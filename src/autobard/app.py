"""Main application orchestrator for WWM Auto-Bard."""

import logging
import time
import threading
import random
from pathlib import Path
from typing import Optional, Callable, List

from .config.settings import AppConfig
from .models import PlaybackState, NoteEvent, SongInfo
from .core import KeyMapper, NoteConverter, Transposer
from .core.compiled_song import CompiledSong
from .core.precision_timer import PrecisionTimer, precision_sleep
from .services import MidiService, KeyboardService, HotkeyService
from .services.sky_sheet_service import SkySheetService

logger = logging.getLogger(__name__)


class AutoBardApp:
    """Main application controller - orchestrates all components.
    
    Coordinates MIDI loading, playback, keyboard simulation, and hotkeys.
    Uses Observer pattern to notify GUI of state changes.
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the application.
        
        Args:
            config: Application configuration. Uses defaults if None.
        """
        self._config = config or AppConfig()
        
        # Initialize services (dependency injection)
        self._midi_service = MidiService()
        self._sky_service = SkySheetService()
        self._keyboard_service = KeyboardService()
        self._hotkey_service = HotkeyService()
        self._precision_timer = PrecisionTimer()
        self._current_file_type = "midi"  # "midi" or "sky"
        self._compiled_song: Optional[CompiledSong] = None  # Pre-compiled for playback
        
        # Initialize core logic
        self._key_mapper = KeyMapper()
        self._note_converter = NoteConverter()
        self._transposer = Transposer()
        
        # State
        self._state = PlaybackState.READY
        self._events: List[NoteEvent] = []
        self._transpose_offset = 0
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        
        # Playback position tracking
        self._current_position: int = 0  # Current note index
        self._start_position: int = 0  # Where to start/resume from
        self._ab_loop_start: Optional[int] = None  # A-B loop start position
        self._ab_loop_end: Optional[int] = None  # A-B loop end position
        
        # Queue/Playlist
        self._playlist: List[Path] = []
        self._playlist_index: int = 0
        
        # Observers for state changes
        self._state_callbacks: List[Callable[[PlaybackState], None]] = []
        self._progress_callbacks: List[Callable[[int, int], None]] = []
        self._time_callbacks: List[Callable[[float, float], None]] = []  # current_time, total_time
        self._countdown_callbacks: List[Callable[[int], None]] = []  # countdown seconds
        
        # Setup hotkeys
        self._setup_hotkeys()
    
    def _setup_hotkeys(self) -> None:
        """Register global hotkeys."""
        self._hotkey_service.register_hotkey(
            self._config.hotkey_start, 
            self._on_hotkey_start_pause
        )
        self._hotkey_service.register_hotkey(
            self._config.hotkey_stop, 
            self.stop
        )
    
    def _on_hotkey_start_pause(self) -> None:
        """Handle start/pause hotkey."""
        if self._state == PlaybackState.PLAYING:
            self.pause()
        elif self._state in (PlaybackState.READY, PlaybackState.PAUSED):
            self.start()
    
    def start_hotkey_listener(self) -> None:
        """Start listening for global hotkeys."""
        self._hotkey_service.start_listening()
        logger.info(f"Hotkeys active: {self._config.hotkey_start}=Start/Pause, {self._config.hotkey_stop}=Stop")
    
    def stop_hotkey_listener(self) -> None:
        """Stop the global hotkey listener."""
        self._hotkey_service.stop_listening()
    
    def load_midi(self, path: Path) -> bool:
        """Load a music file for playback (MIDI or Sky sheet).
        
        Args:
            path: Path to the .mid or .json file
            
        Returns:
            True if loaded successfully
        """
        try:
            # Detect file type
            suffix = path.suffix.lower()
            is_sky = suffix in ('.json', '.skysheet', '.txt') or SkySheetService.is_sky_sheet(path)
            
            if is_sky:
                self._events = self._sky_service.load_file(path)
                song_info = self._sky_service.get_song_info()
                self._current_file_type = "sky"
                logger.info(f"Loaded Sky sheet: {path.name}")
            else:
                self._events = self._midi_service.load_file(path)
                song_info = self._midi_service.get_song_info()
                self._current_file_type = "midi"
            
            # Filter to note-on events only for playback
            self._events = [e for e in self._events if e.is_note_on]
            
            original_count = len(self._events)
            
            # Auto-optimize if enabled and song is too wide
            if self._config.auto_optimize and self._events:
                notes = [e.note for e in self._events]
                span = max(notes) - min(notes)
                if span > 36:
                    # Find best window and filter
                    window_start, window_count = self._transposer.find_best_window(self._events)
                    self._events = self._transposer.filter_to_window(self._events, window_start)
                    logger.info(f"  Auto-optimized: kept {len(self._events)}/{original_count} notes in best range")
            
            # Calculate transpose offset based on filtered events
            if self._events:
                min_note = min(e.note for e in self._events)
                max_note = max(e.note for e in self._events)
                self._transpose_offset = self._transposer.calculate_offset((min_note, max_note))
            else:
                self._transpose_offset = 0
            
            # Pre-compile song for optimized playback
            self._compiled_song = CompiledSong.compile(
                self._events,
                self._transpose_offset,
                self._note_converter,
                self._key_mapper
            )
            
            # Log song info for debugging
            if song_info:
                logger.info(f"Loaded: {song_info.filename}")
                logger.info(f"  Original: {original_count} notes, Range: MIDI {song_info.min_note}-{song_info.max_note} (span: {song_info.max_note - song_info.min_note})")
                if self._events:
                    new_min = min(e.note for e in self._events)
                    new_max = max(e.note for e in self._events)
                    logger.info(f"  Playing: {len(self._events)} notes, Range: MIDI {new_min}-{new_max} (span: {new_max - new_min})")
                logger.info(f"  Transpose: {self._transpose_offset:+d} semitones")
                logger.info(f"  Pre-compiled: {self._compiled_song.total_notes} playable notes")
            
            self._set_state(PlaybackState.READY)
            return True
            
        except Exception as e:
            logger.error(f"Failed to load file: {e}")
            return False
    
    def start(self) -> None:
        """Start or resume playback."""
        if not self._events and not self._compiled_song:
            logger.warning("No file loaded")
            return
        
        if self._state == PlaybackState.PLAYING:
            return
        
        if self._state == PlaybackState.PAUSED:
            # Resume from paused position
            self._pause_flag.clear()
            self._set_state(PlaybackState.PLAYING)
            return
        
        # Stop any existing playback thread first
        if self._playback_thread and self._playback_thread.is_alive():
            self._stop_flag.set()
            self._playback_thread.join(timeout=0.5)
        
        # Start new playback
        self._stop_flag.clear()
        self._pause_flag.clear()
        
        # Use optimized or standard playback
        target = self._play_with_countdown
        
        self._playback_thread = threading.Thread(
            target=target,
            daemon=True
        )
        self._playback_thread.start()
        
        # Set high priority for playback thread (Windows)
        try:
            import ctypes
            handle = ctypes.windll.kernel32.OpenThread(0x0020, False, self._playback_thread.ident)
            if handle:
                ctypes.windll.kernel32.SetThreadPriority(handle, 2)  # ABOVE_NORMAL
                ctypes.windll.kernel32.CloseHandle(handle)
                logger.debug("Set playback thread to high priority")
        except Exception:
            pass
    
    def _play_with_countdown(self) -> None:
        """Wrapper that handles countdown before playback."""
        # Countdown
        if self._config.countdown_seconds > 0 and self._start_position == 0:
            self._set_state(PlaybackState.PLAYING)
            for i in range(self._config.countdown_seconds, 0, -1):
                if self._stop_flag.is_set():
                    return
                self._notify_countdown(i)
                time.sleep(1.0)
            self._notify_countdown(0)
        
        self._set_state(PlaybackState.PLAYING)
        logger.info("Playback started" + (" (high-perf mode)" if self._config.high_performance else ""))
        
        # Run playback (potentially looping)
        while not self._stop_flag.is_set():
            if self._config.high_performance:
                self._play_optimized()
            else:
                self._play_events()
            
            # Check for loop mode
            if self._config.loop_mode and not self._stop_flag.is_set():
                self._start_position = 0
                logger.info("Looping playback...")
                continue
            
            # Check for playlist
            if self._playlist and self._playlist_index < len(self._playlist) - 1:
                self._playlist_index += 1
                self.load_midi(self._playlist[self._playlist_index])
                continue
            
            break
    
    def pause(self) -> None:
        """Pause playback (remembers position)."""
        if self._state != PlaybackState.PLAYING:
            return
        
        self._pause_flag.set()
        self._start_position = self._current_position  # Remember position
        self._set_state(PlaybackState.PAUSED)
        logger.info(f"Playback paused at position {self._current_position}")
    
    def stop(self) -> None:
        """Stop playback and release all keys (panic button)."""
        self._stop_flag.set()
        self._pause_flag.clear()
        
        # Release all held keys immediately
        self._keyboard_service.release_all()
        
        # Wait for playback thread to finish
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        
        # Reset position
        self._current_position = 0
        self._start_position = 0
        
        self._set_state(PlaybackState.STOPPED)
        logger.info("Playback stopped")
    
    def seek(self, position: int) -> None:
        """Seek to a specific note position."""
        if not self._compiled_song:
            return
        
        max_pos = self._compiled_song.total_notes - 1
        self._start_position = max(0, min(position, max_pos))
        self._current_position = self._start_position
        logger.info(f"Seeked to position {self._start_position}")
        
        # Update progress display
        self._notify_progress(self._start_position, self._compiled_song.total_notes)
    
    def seek_percent(self, percent: float) -> None:
        """Seek to a percentage position (0.0 to 1.0)."""
        if not self._compiled_song:
            return
        position = int(self._compiled_song.total_notes * max(0, min(1, percent)))
        self.seek(position)
    
    def set_ab_loop(self, start: Optional[int] = None, end: Optional[int] = None) -> None:
        """Set A-B loop points. Pass None to clear."""
        self._ab_loop_start = start
        self._ab_loop_end = end
        if start is not None and end is not None:
            logger.info(f"A-B loop set: {start} to {end}")
        else:
            logger.info("A-B loop cleared")
    
    def set_loop_a(self) -> None:
        """Set loop point A to current position."""
        self._ab_loop_start = self._current_position
        logger.info(f"Loop A set at {self._ab_loop_start}")
    
    def set_loop_b(self) -> None:
        """Set loop point B to current position."""
        self._ab_loop_end = self._current_position
        logger.info(f"Loop B set at {self._ab_loop_end}")
    
    def clear_ab_loop(self) -> None:
        """Clear A-B loop points."""
        self._ab_loop_start = None
        self._ab_loop_end = None
        logger.info("A-B loop cleared")
    
    def toggle_loop(self) -> bool:
        """Toggle loop mode on/off."""
        self._config.loop_mode = not self._config.loop_mode
        logger.info(f"Loop mode: {'ON' if self._config.loop_mode else 'OFF'}")
        return self._config.loop_mode
    
    # Playlist functions
    def set_playlist(self, files: List[Path]) -> None:
        """Set a playlist of files to play."""
        self._playlist = files
        self._playlist_index = 0
        if files:
            self.load_midi(files[0])
            logger.info(f"Playlist set: {len(files)} songs")
    
    def add_to_playlist(self, file: Path) -> None:
        """Add a file to the playlist."""
        self._playlist.append(file)
        logger.info(f"Added to playlist: {file.name}")
    
    def clear_playlist(self) -> None:
        """Clear the playlist."""
        self._playlist = []
        self._playlist_index = 0
    
    def next_song(self) -> bool:
        """Skip to next song in playlist."""
        if self._playlist and self._playlist_index < len(self._playlist) - 1:
            self.stop()
            self._playlist_index += 1
            return self.load_midi(self._playlist[self._playlist_index])
        return False
    
    def prev_song(self) -> bool:
        """Go to previous song in playlist."""
        if self._playlist and self._playlist_index > 0:
            self.stop()
            self._playlist_index -= 1
            return self.load_midi(self._playlist[self._playlist_index])
        return False
    
    def _play_events(self) -> None:
        """Main playback loop - runs in separate thread.
        
        Includes natural sound improvements:
        - Humanization (random timing variations)
        - Chord strum effect
        - Velocity-based timing
        - Dynamic tempo for dense sections
        - High-precision timing
        """
        # Copy events to avoid race conditions when user loads new file
        events = list(self._events)
        total_events = len(events)
        if total_events == 0:
            return
            
        min_delay = self._config.min_note_delay_ms / 1000.0
        chord_threshold = 0.05  # 50ms - notes within this are treated as chord
        
        # Pre-calculate note density for dynamic tempo (notes per second in 2s windows)
        density_map = self._calculate_density_map(events) if self._config.dynamic_tempo else {}
        
        # Use high-precision timer
        next_time = time.perf_counter()
        
        i = 0
        while i < total_events:
            if self._stop_flag.is_set():
                break
            
            # Handle pause
            while self._pause_flag.is_set() and not self._stop_flag.is_set():
                time.sleep(0.05)
                next_time = time.perf_counter()  # Reset timer after pause
            
            if self._stop_flag.is_set():
                break
            
            event = events[i]
            
            # Calculate delay with improvements
            base_delay = event.time_delta / self._config.playback_speed
            
            # Dynamic tempo: slow down for dense sections
            if self._config.dynamic_tempo and i in density_map:
                density = density_map[i]
                if density > 8:  # More than 8 notes/sec = dense
                    base_delay *= 1.0 + (density - 8) * 0.03  # Slow down up to 30%
            
            # Velocity-based timing: softer notes get slightly longer gaps
            if self._config.velocity_timing and event.velocity < 80:
                velocity_factor = 1.0 + (80 - event.velocity) / 200  # Up to 40% longer
                base_delay *= velocity_factor
            
            # Humanization: add random micro-timing
            if self._config.humanize_ms > 0:
                humanize = random.uniform(-self._config.humanize_ms, self._config.humanize_ms) / 1000.0
                base_delay += humanize
            
            # Ensure minimum delay
            actual_delay = max(base_delay, min_delay) if i > 0 else 0
            
            # High-precision wait
            if actual_delay > 0:
                next_time += actual_delay
                sleep_time = next_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            if self._stop_flag.is_set():
                break
            
            # Collect chord notes
            chord_events = [event]
            j = i + 1
            while j < total_events and events[j].time_delta <= chord_threshold:
                chord_events.append(events[j])
                j += 1
            
            # Play note(s)
            try:
                if len(chord_events) == 1:
                    transposed_note = event.note + self._transpose_offset
                    game_note = self._note_converter.convert(transposed_note)
                    key_press = self._key_mapper.get_key_press(game_note)
                    
                    self._keyboard_service.press(
                        key_press, 
                        delay_ms=self._config.input_delay_ms
                    )
                else:
                    # Chord with strum effect
                    key_presses = []
                    for ce in chord_events:
                        transposed_note = ce.note + self._transpose_offset
                        game_note = self._note_converter.convert(transposed_note)
                        key_press = self._key_mapper.get_key_press(game_note)
                        key_presses.append(key_press)
                    
                    self._keyboard_service.press_multiple(
                        key_presses,
                        delay_ms=self._config.input_delay_ms,
                        strum_ms=self._config.chord_strum_ms
                    )
                
                self._notify_progress(j, total_events)
                
            except Exception as e:
                logger.error(f"Error playing note {event.note}: {e}")
            
            i = j
        
        if not self._stop_flag.is_set():
            self._set_state(PlaybackState.READY)
            logger.info("Playback finished")
    
    def _play_optimized(self) -> None:
        """High-performance playback using pre-compiled data and precision timing."""
        if not self._compiled_song or self._compiled_song.total_notes == 0:
            return
        
        song = self._compiled_song
        min_delay = self._config.min_note_delay_ms / 1000.0
        
        # Calculate total duration for time display
        total_duration = song.duration / self._config.playback_speed
        
        # Start precision timer
        self._precision_timer.start()
        
        # Start from saved position (for resume/seek)
        i = self._start_position
        current_time = 0.0
        
        while i < song.total_notes:
            if self._stop_flag.is_set():
                break
            
            # Handle pause
            while self._pause_flag.is_set() and not self._stop_flag.is_set():
                time.sleep(0.05)
                self._precision_timer.reset()
            
            if self._stop_flag.is_set():
                break
            
            # Track current position
            self._current_position = i
            
            # Check A-B loop
            if (self._ab_loop_end is not None and 
                self._ab_loop_start is not None and 
                i >= self._ab_loop_end):
                i = self._ab_loop_start
                self._precision_timer.reset()
                continue
            
            note = song.notes[i]
            
            # Calculate delay with all improvements
            base_delay = note.time_delta / self._config.playback_speed
            current_time += base_delay
            
            # Dynamic tempo
            if self._config.dynamic_tempo and i < len(song.density_map):
                density = song.density_map[i]
                if density > 8:
                    base_delay *= 1.0 + (density - 8) * 0.03
            
            # Velocity timing
            if self._config.velocity_timing and note.velocity < 80:
                base_delay *= 1.0 + (80 - note.velocity) / 200
            
            # Humanization
            if self._config.humanize_ms > 0:
                base_delay += random.uniform(-self._config.humanize_ms, self._config.humanize_ms) / 1000.0
            
            # Apply minimum delay
            actual_delay = max(base_delay, min_delay) if i > self._start_position else 0
            
            # Precision wait
            if actual_delay > 0:
                self._precision_timer.wait(actual_delay)
            
            if self._stop_flag.is_set():
                break
            
            # Play using keyboard service (better game compatibility than SendInput)
            try:
                if note.chord_size > 1:
                    # Chord
                    key_presses = song.get_chord_key_presses(i)
                    self._keyboard_service.press_multiple(
                        key_presses,
                        delay_ms=self._config.input_delay_ms,
                        strum_ms=self._config.chord_strum_ms
                    )
                    i += note.chord_size
                else:
                    # Single note
                    key_press = song.get_key_press(i)
                    self._keyboard_service.press(key_press, delay_ms=self._config.input_delay_ms)
                    i += 1
                
                self._notify_progress(i, song.total_notes)
                self._notify_time(current_time, total_duration)
                
            except Exception as e:
                logger.error(f"Playback error: {e}")
                i += 1
        
        # Cleanup
        self._precision_timer.stop()
        self._start_position = 0  # Reset for next play
        
        if not self._stop_flag.is_set():
            self._set_state(PlaybackState.READY)
            logger.info("Playback finished")
    
    def _calculate_density_map(self, events: List[NoteEvent]) -> dict:
        """Calculate note density at each position for dynamic tempo.
        
        Returns dict mapping event index to notes-per-second in surrounding 2s window.
        """
        density = {}
        window = 2.0  # 2 second window
        
        # Build cumulative time array
        times = []
        cumulative = 0.0
        for e in events:
            cumulative += e.time_delta
            times.append(cumulative)
        
        for i, t in enumerate(times):
            # Count notes within window centered on this note
            start_t = t - window / 2
            end_t = t + window / 2
            count = sum(1 for tt in times if start_t <= tt <= end_t)
            notes_per_sec = count / window
            density[i] = notes_per_sec
        
        return density
    
    def _set_state(self, state: PlaybackState) -> None:
        """Update state and notify observers."""
        self._state = state
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")
    
    def _notify_progress(self, current: int, total: int) -> None:
        """Notify progress observers."""
        for callback in self._progress_callbacks:
            try:
                callback(current, total)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def _notify_time(self, current: float, total: float) -> None:
        """Notify time observers."""
        for callback in self._time_callbacks:
            try:
                callback(current, total)
            except Exception as e:
                logger.error(f"Time callback error: {e}")
    
    def _notify_countdown(self, seconds: int) -> None:
        """Notify countdown observers."""
        for callback in self._countdown_callbacks:
            try:
                callback(seconds)
            except Exception as e:
                logger.error(f"Countdown callback error: {e}")
    
    def on_state_change(self, callback: Callable[[PlaybackState], None]) -> None:
        """Register callback for state changes (Observer pattern)."""
        self._state_callbacks.append(callback)
    
    def on_progress(self, callback: Callable[[int, int], None]) -> None:
        """Register callback for playback progress updates."""
        self._progress_callbacks.append(callback)
    
    def on_time_update(self, callback: Callable[[float, float], None]) -> None:
        """Register callback for time updates (current_seconds, total_seconds)."""
        self._time_callbacks.append(callback)
    
    def on_countdown(self, callback: Callable[[int], None]) -> None:
        """Register callback for countdown updates."""
        self._countdown_callbacks.append(callback)
    
    @property
    def state(self) -> PlaybackState:
        """Get current playback state."""
        return self._state
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        return self._config
    
    @property
    def song_info(self) -> Optional[SongInfo]:
        """Get info about the loaded song."""
        return self._midi_service.get_song_info()
    
    @property
    def is_file_loaded(self) -> bool:
        """Check if a MIDI file is loaded."""
        return self._midi_service.is_loaded
    
    @property
    def current_position(self) -> int:
        """Get current playback position (note index)."""
        return self._current_position
    
    @property
    def total_notes(self) -> int:
        """Get total number of notes in song."""
        return self._compiled_song.total_notes if self._compiled_song else 0
    
    @property
    def song_duration(self) -> float:
        """Get song duration in seconds."""
        return self._compiled_song.duration if self._compiled_song else 0.0
    
    @property
    def playlist(self) -> List[Path]:
        """Get current playlist."""
        return self._playlist
    
    @property
    def playlist_index(self) -> int:
        """Get current playlist index."""
        return self._playlist_index
    
    @property
    def ab_loop_active(self) -> bool:
        """Check if A-B loop is active."""
        return self._ab_loop_start is not None and self._ab_loop_end is not None
    
    def get_track_info(self) -> list:
        """Get info about tracks in the loaded file (MIDI only)."""
        if self._current_file_type == "sky":
            return []  # Sky sheets don't have tracks
        return self._midi_service.get_track_info()
    
    def reload_track(self, track: Optional[int]) -> bool:
        """Reload the current file with a specific track.
        
        Args:
            track: Track number to load, or None for all tracks merged
            
        Returns:
            True if successful
        """
        try:
            if track is None:
                self._events = self._midi_service.load_file(self._midi_service._current_file)
            else:
                self._events = self._midi_service.reload_track(track)
            
            # Filter to note-on events only
            self._events = [e for e in self._events if e.is_note_on]
            original_count = len(self._events)
            
            # Get note range for optimization
            song_info = self._midi_service.get_song_info()
            
            # Auto-optimize if enabled and song is too wide
            if self._config.auto_optimize and song_info:
                span = song_info.max_note - song_info.min_note
                if span > 36:
                    window_start, _ = self._transposer.find_best_window(self._events)
                    self._events = self._transposer.filter_to_window(self._events, window_start)
                    logger.info(f"  Auto-optimized: kept {len(self._events)}/{original_count} notes")
            
            # Recalculate transpose based on filtered events
            if self._events:
                min_note = min(e.note for e in self._events)
                max_note = max(e.note for e in self._events)
                self._transpose_offset = self._transposer.calculate_offset((min_note, max_note))
            else:
                self._transpose_offset = 0
            
            # Log updated info
            if song_info:
                logger.info(f"Reloaded track {track if track is not None else 'all'}: {original_count} original notes")
                if self._events:
                    new_min = min(e.note for e in self._events)
                    new_max = max(e.note for e in self._events)
                    logger.info(f"  Playing: {len(self._events)} notes, Range: MIDI {new_min}-{new_max}")
                logger.info(f"  Transpose: {self._transpose_offset:+d} semitones")
            
            self._set_state(PlaybackState.READY)
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload track: {e}")
            return False
    
    def set_playback_speed(self, speed: float) -> None:
        """Set playback speed (0.5 to 2.0)."""
        self._config.playback_speed = max(0.5, min(2.0, speed))
    
    def set_input_delay(self, delay_ms: int) -> None:
        """Set input delay in milliseconds."""
        self._config.input_delay_ms = max(0, min(500, delay_ms))
    
    def shutdown(self) -> None:
        """Clean shutdown of the application."""
        self.stop()
        self.stop_hotkey_listener()
        logger.info("Application shutdown complete")
