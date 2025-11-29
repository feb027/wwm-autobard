"""MIDI file parsing service - wraps mido library."""

import logging
from pathlib import Path
from typing import List, Optional, Dict

from ..models.note import NoteEvent, SongInfo
from ..core.exceptions import MidiParseError

logger = logging.getLogger(__name__)


class MidiService:
    """Service for loading and parsing MIDI files.
    
    Wraps the mido library to provide a clean interface for MIDI operations.
    """
    
    def __init__(self):
        self._current_file: Optional[Path] = None
        self._events: List[NoteEvent] = []
        self._song_info: Optional[SongInfo] = None
        self._midi_file = None
        self._track_info: List[Dict] = []
    
    def load_file(self, path: Path, track: Optional[int] = None) -> List[NoteEvent]:
        """Load and parse a MIDI file.
        
        Args:
            path: Path to the .mid file
            track: Optional track number to load (None = all tracks merged)
            
        Returns:
            List of NoteEvent objects representing note-on events
            
        Raises:
            MidiParseError: If the file cannot be loaded or parsed
        """
        try:
            import mido
        except ImportError as e:
            raise MidiParseError("mido library not installed") from e
        
        try:
            midi = mido.MidiFile(str(path))
        except Exception as e:
            raise MidiParseError(f"Failed to load MIDI file: {path}") from e
        
        self._current_file = path
        self._midi_file = midi
        self._events = []
        
        # Analyze tracks
        self._track_info = self._analyze_tracks(midi)
        
        # Log track info
        logger.info(f"MIDI has {len(midi.tracks)} tracks:")
        for info in self._track_info:
            logger.info(f"  Track {info['index']}: {info['name']} - {info['note_count']} notes")
        
        # Determine which track(s) to use
        if track is not None and 0 <= track < len(midi.tracks):
            # Load specific track
            self._events = self._load_single_track(midi.tracks[track], midi.ticks_per_beat)
            logger.info(f"Loaded track {track} only")
        else:
            # Load all tracks merged (original behavior)
            self._events = self._load_all_tracks(midi)
        
        # Calculate duration
        total_duration = sum(e.time_delta for e in self._events)
        
        # Build song info
        self._song_info = self._build_song_info(path.name, total_duration)
        
        logger.info(f"Loaded {path.name}: {len(self._events)} events, {total_duration:.1f}s")
        return self._events
    
    def _analyze_tracks(self, midi) -> List[Dict]:
        """Analyze tracks in a MIDI file."""
        track_info = []
        
        for i, track in enumerate(midi.tracks):
            name = f"Track {i}"
            note_count = 0
            
            for msg in track:
                if msg.type == 'track_name':
                    name = msg.name
                elif msg.type == 'note_on' and msg.velocity > 0:
                    note_count += 1
            
            track_info.append({
                'index': i,
                'name': name,
                'note_count': note_count,
            })
        
        return track_info
    
    def _load_single_track(self, track, ticks_per_beat: int) -> List[NoteEvent]:
        """Load events from a single track."""
        import mido
        
        events = []
        absolute_time = 0.0
        last_note_on_time = 0.0
        tempo = 500000  # Default tempo (120 BPM)
        
        for msg in track:
            # Convert ticks to seconds
            if msg.time > 0:
                absolute_time += mido.tick2second(msg.time, ticks_per_beat, tempo)
            
            if msg.type == 'set_tempo':
                tempo = msg.tempo
            elif msg.type == 'note_on' and msg.velocity > 0:
                time_since_last_note = absolute_time - last_note_on_time
                events.append(NoteEvent(
                    note=msg.note,
                    velocity=msg.velocity,
                    time_delta=time_since_last_note,
                    is_note_on=True,
                ))
                last_note_on_time = absolute_time
        
        return events
    
    def _load_all_tracks(self, midi) -> List[NoteEvent]:
        """Load all tracks merged together."""
        events = []
        absolute_time = 0.0
        last_note_on_time = 0.0
        
        for msg in midi:  # Iterating over MidiFile merges all tracks
            absolute_time += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                time_since_last_note = absolute_time - last_note_on_time
                events.append(NoteEvent(
                    note=msg.note,
                    velocity=msg.velocity,
                    time_delta=time_since_last_note,
                    is_note_on=True,
                ))
                last_note_on_time = absolute_time
        
        return events
    
    def get_track_info(self) -> List[Dict]:
        """Get info about tracks in the loaded MIDI file."""
        return self._track_info
    
    def reload_track(self, track: int) -> List[NoteEvent]:
        """Reload the current file with a specific track."""
        if self._current_file is None:
            raise MidiParseError("No file loaded")
        return self.load_file(self._current_file, track=track)
    
    def _build_song_info(self, filename: str, duration: float) -> SongInfo:
        """Build song metadata from loaded events."""
        note_on_events = [e for e in self._events if e.is_note_on]
        
        if not note_on_events:
            return SongInfo(
                filename=filename,
                duration=duration,
                note_count=0,
                min_note=0,
                max_note=0,
            )
        
        notes = [e.note for e in note_on_events]
        return SongInfo(
            filename=filename,
            duration=duration,
            note_count=len(note_on_events),
            min_note=min(notes),
            max_note=max(notes),
        )
    
    def get_note_events(self) -> List[NoteEvent]:
        """Get only note-on events (for playback)."""
        return [e for e in self._events if e.is_note_on]
    
    def get_note_range(self) -> tuple[int, int]:
        """Get the range of notes in the current file.
        
        Returns:
            Tuple of (min_note, max_note) MIDI numbers
        """
        if self._song_info is None:
            return (60, 60)  # Default to middle C
        return (self._song_info.min_note, self._song_info.max_note)
    
    def get_duration(self) -> float:
        """Get the total duration of the current file in seconds."""
        if self._song_info is None:
            return 0.0
        return self._song_info.duration
    
    def get_song_info(self) -> Optional[SongInfo]:
        """Get metadata about the currently loaded song."""
        return self._song_info
    
    @property
    def is_loaded(self) -> bool:
        """Check if a file is currently loaded."""
        return self._current_file is not None and len(self._events) > 0
    
    @property
    def current_file(self) -> Optional[Path]:
        """Get the path of the currently loaded file."""
        return self._current_file
