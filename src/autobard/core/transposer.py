"""Auto-transpose algorithm for fitting songs into the game's range.

This module analyzes MIDI note ranges and calculates the optimal
transpose offset to fit songs within the game's 3-octave range.

This module is pure Python with no external dependencies.
"""

from typing import List

from ..models.note import NoteEvent
from .note_converter import GAME_MIN_MIDI, GAME_MAX_MIDI, GAME_RANGE


class Transposer:
    """Calculates and applies transpose offsets for MIDI notes.
    
    The game supports 3 octaves (36 semitones). Songs that exceed
    this range need to be transposed to fit.
    """
    
    def __init__(self, game_min: int = GAME_MIN_MIDI, game_max: int = GAME_MAX_MIDI):
        """Initialize the transposer.
        
        Args:
            game_min: Minimum playable MIDI note (default: 48 = C3)
            game_max: Maximum playable MIDI note (default: 83 = B5)
        """
        self._game_min = game_min
        self._game_max = game_max
        self._game_range = game_max - game_min + 1
    
    def calculate_offset(self, note_range: tuple[int, int]) -> int:
        """Calculate the optimal transpose offset for a note range.
        
        Args:
            note_range: Tuple of (min_note, max_note) from the MIDI file
            
        Returns:
            Number of semitones to shift (positive = up, negative = down)
            
        The algorithm:
        1. If the song fits within range, center it
        2. If the song is too wide, center it and accept some clipping
        3. Prefer shifting in octaves (12 semitones) when possible
        """
        song_min, song_max = note_range
        song_range = song_max - song_min + 1
        
        # If song already fits perfectly, no transpose needed
        if song_min >= self._game_min and song_max <= self._game_max:
            return 0
        
        # Calculate the center of each range
        song_center = (song_min + song_max) / 2
        game_center = (self._game_min + self._game_max) / 2
        
        # Raw offset to center the song
        raw_offset = game_center - song_center
        
        # Round to nearest octave if the song fits, otherwise round to semitone
        if song_range <= self._game_range:
            # Song fits, prefer octave shifts for more natural sound
            octave_offset = round(raw_offset / 12) * 12
            
            # Verify the octave shift works, adjust if needed
            shifted_min = song_min + octave_offset
            shifted_max = song_max + octave_offset
            
            if shifted_min >= self._game_min and shifted_max <= self._game_max:
                return octave_offset
            
            # Octave shift doesn't fit, try semitone adjustment
            return round(raw_offset)
        else:
            # Song is too wide, center it and accept clipping
            return round(raw_offset)
    
    def apply_transpose(self, events: List[NoteEvent], offset: int) -> List[NoteEvent]:
        """Apply a transpose offset to a list of note events.
        
        Args:
            events: List of NoteEvent objects
            offset: Semitones to shift (positive = up, negative = down)
            
        Returns:
            New list with transposed note values (clamped to 0-127)
        """
        if offset == 0:
            return events
        
        transposed = []
        for event in events:
            new_note = max(0, min(127, event.note + offset))
            transposed.append(NoteEvent(
                note=new_note,
                velocity=event.velocity,
                time_delta=event.time_delta,
                is_note_on=event.is_note_on,
            ))
        return transposed
    
    def get_out_of_range_count(
        self, 
        events: List[NoteEvent], 
        offset: int = 0
    ) -> tuple[int, int]:
        """Count notes that fall outside the playable range.
        
        Args:
            events: List of NoteEvent objects
            offset: Optional transpose offset to apply before checking
            
        Returns:
            Tuple of (notes_below_range, notes_above_range)
        """
        below = 0
        above = 0
        
        for event in events:
            if not event.is_note_on:
                continue
            
            note = event.note + offset
            if note < self._game_min:
                below += 1
            elif note > self._game_max:
                above += 1
        
        return (below, above)
    
    def analyze_range(self, events: List[NoteEvent]) -> dict:
        """Analyze the note range of a song.
        
        Args:
            events: List of NoteEvent objects
            
        Returns:
            Dictionary with analysis results:
            - min_note: Lowest MIDI note
            - max_note: Highest MIDI note
            - range: Total semitone range
            - fits_in_game: Whether the song fits without clipping
            - recommended_offset: Suggested transpose value
        """
        if not events:
            return {
                "min_note": 0,
                "max_note": 0,
                "range": 0,
                "fits_in_game": True,
                "recommended_offset": 0,
            }
        
        note_on_events = [e for e in events if e.is_note_on]
        if not note_on_events:
            return {
                "min_note": 0,
                "max_note": 0,
                "range": 0,
                "fits_in_game": True,
                "recommended_offset": 0,
            }
        
        min_note = min(e.note for e in note_on_events)
        max_note = max(e.note for e in note_on_events)
        note_range = max_note - min_note + 1
        
        offset = self.calculate_offset((min_note, max_note))
        fits = note_range <= self._game_range
        
        return {
            "min_note": min_note,
            "max_note": max_note,
            "range": note_range,
            "fits_in_game": fits,
            "recommended_offset": offset,
        }
    
    def find_best_window(self, events: List[NoteEvent]) -> tuple[int, int]:
        """Find the 36-semitone window that contains the most notes.
        
        This is useful for songs that span more than 3 octaves - we find
        the range that captures the most notes (likely the melody).
        
        Args:
            events: List of NoteEvent objects
            
        Returns:
            Tuple of (window_start, notes_in_window)
        """
        note_on_events = [e for e in events if e.is_note_on]
        if not note_on_events:
            return (self._game_min, 0)
        
        notes = [e.note for e in note_on_events]
        min_note = min(notes)
        max_note = max(notes)
        
        # If already fits, return the actual range
        if max_note - min_note < GAME_RANGE:
            return (min_note, len(notes))
        
        # Slide a 36-semitone window and count notes in each position
        best_start = min_note
        best_count = 0
        
        for start in range(min_note, max_note - GAME_RANGE + 2):
            end = start + GAME_RANGE - 1
            count = sum(1 for n in notes if start <= n <= end)
            if count > best_count:
                best_count = count
                best_start = start
        
        return (best_start, best_count)
    
    def filter_to_window(
        self, 
        events: List[NoteEvent], 
        window_start: int
    ) -> List[NoteEvent]:
        """Filter events to only include notes within a 36-semitone window.
        
        Args:
            events: List of NoteEvent objects
            window_start: Starting MIDI note of the window
            
        Returns:
            Filtered list with only notes in the window, timing preserved
        """
        window_end = window_start + GAME_RANGE - 1
        filtered = []
        accumulated_time = 0.0
        
        for event in events:
            if not event.is_note_on:
                continue
            
            accumulated_time += event.time_delta
            
            if window_start <= event.note <= window_end:
                # Include this note with accumulated time since last included note
                filtered.append(NoteEvent(
                    note=event.note,
                    velocity=event.velocity,
                    time_delta=accumulated_time,
                    is_note_on=True,
                ))
                accumulated_time = 0.0
        
        return filtered
