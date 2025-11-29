"""Pre-compiled song data for optimized playback."""

import array
from dataclasses import dataclass
from typing import List, Tuple, Optional

from ..models.note import KeyPress, NoteEvent


@dataclass(frozen=True, slots=True)
class CompiledNote:
    """Pre-compiled note with all calculations done."""
    key: str
    modifiers: Tuple[str, ...]
    time_delta: float
    velocity: int
    is_chord_start: bool
    chord_size: int


class CompiledSong:
    """Pre-compiled song with all key mappings resolved.
    
    Eliminates per-note calculations during playback for lower latency.
    Uses arrays for better cache performance.
    """
    
    __slots__ = ('notes', 'total_notes', 'duration', 'density_map', 
                 '_time_deltas', '_velocities', '_chord_sizes')
    
    def __init__(self):
        self.notes: List[CompiledNote] = []
        self.total_notes: int = 0
        self.duration: float = 0.0
        self.density_map: array.array = array.array('f')
        
        # Parallel arrays for cache-friendly access
        self._time_deltas: array.array = array.array('f')
        self._velocities: array.array = array.array('B')  # unsigned char
        self._chord_sizes: array.array = array.array('B')
    
    @classmethod
    def compile(
        cls,
        events: List[NoteEvent],
        transpose_offset: int,
        note_converter,
        key_mapper,
        chord_threshold: float = 0.05
    ) -> 'CompiledSong':
        """Compile a list of events into optimized playback data.
        
        Args:
            events: Raw note events
            transpose_offset: Semitones to transpose
            note_converter: NoteConverter instance
            key_mapper: KeyMapper instance
            chord_threshold: Max time between notes to group as chord
        """
        song = cls()
        
        if not events:
            return song
        
        # Pre-process: group chords and compile all notes
        i = 0
        total_time = 0.0
        
        while i < len(events):
            event = events[i]
            total_time += event.time_delta
            
            # Find chord group
            chord_events = [event]
            j = i + 1
            while j < len(events) and events[j].time_delta <= chord_threshold:
                chord_events.append(events[j])
                j += 1
            
            # Compile each note in chord
            for idx, ce in enumerate(chord_events):
                try:
                    transposed = ce.note + transpose_offset
                    game_note = note_converter.convert(transposed)
                    key_press = key_mapper.get_key_press(game_note)
                    
                    # Only first note of chord has time_delta
                    note_time = ce.time_delta if idx == 0 else 0.0
                    
                    compiled = CompiledNote(
                        key=key_press.key,
                        modifiers=tuple(key_press.modifiers),
                        time_delta=note_time,
                        velocity=ce.velocity,
                        is_chord_start=(idx == 0 and len(chord_events) > 1),
                        chord_size=len(chord_events) if idx == 0 else 0
                    )
                    song.notes.append(compiled)
                    
                    # Parallel arrays
                    song._time_deltas.append(note_time)
                    song._velocities.append(min(127, ce.velocity))
                    song._chord_sizes.append(len(chord_events) if idx == 0 else 0)
                    
                except Exception:
                    pass  # Skip notes that can't be mapped
            
            i = j
        
        song.total_notes = len(song.notes)
        song.duration = total_time
        
        # Pre-calculate density map
        song._calculate_density()
        
        return song
    
    def _calculate_density(self, window: float = 2.0) -> None:
        """Pre-calculate note density at each position."""
        if not self.notes:
            return
        
        # Build cumulative times
        times = []
        cumulative = 0.0
        for note in self.notes:
            cumulative += note.time_delta
            times.append(cumulative)
        
        # Calculate density at each position
        half_window = window / 2
        for t in times:
            start_t = t - half_window
            end_t = t + half_window
            count = sum(1 for tt in times if start_t <= tt <= end_t)
            density = count / window
            self.density_map.append(density)
    
    def get_key_press(self, index: int) -> KeyPress:
        """Get KeyPress for note at index."""
        note = self.notes[index]
        return KeyPress(key=note.key, modifiers=list(note.modifiers))
    
    def get_chord_key_presses(self, index: int) -> List[KeyPress]:
        """Get all KeyPress objects for a chord starting at index."""
        if index >= len(self.notes):
            return []
        
        chord_size = self.notes[index].chord_size
        if chord_size <= 1:
            return [self.get_key_press(index)]
        
        return [
            self.get_key_press(index + i)
            for i in range(chord_size)
            if index + i < len(self.notes)
        ]
