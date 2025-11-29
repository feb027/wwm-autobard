"""Data classes for notes and key presses."""

from dataclasses import dataclass
from typing import Optional

from .enums import Pitch, NoteName, Accidental


@dataclass(frozen=True)
class KeyPress:
    """Immutable representation of a keyboard action.
    
    Attributes:
        key: The keyboard key to press (e.g., 'a', 'q', 'z')
        modifiers: Tuple of modifier keys to hold (e.g., ('shift',), ('ctrl',))
    """
    key: str
    modifiers: tuple[str, ...] = ()
    
    def __str__(self) -> str:
        if self.modifiers:
            return f"{'+'.join(self.modifiers)}+{self.key}"
        return self.key


@dataclass(frozen=True)
class GameNote:
    """Represents a note in the game's notation system.
    
    Attributes:
        pitch: HIGH, MID, or LOW octave
        name: Note name (DO through TI)
        accidental: NATURAL, SHARP, or FLAT
    """
    pitch: Pitch
    name: NoteName
    accidental: Accidental = Accidental.NATURAL
    
    def __str__(self) -> str:
        acc_str = ""
        if self.accidental == Accidental.SHARP:
            acc_str = "#"
        elif self.accidental == Accidental.FLAT:
            acc_str = "b"
        return f"{self.pitch.name}-{self.name.name}{acc_str}"


@dataclass
class NoteEvent:
    """Represents a MIDI note event with timing information.
    
    Attributes:
        note: MIDI note number (0-127)
        velocity: Note velocity/volume (0-127)
        time_delta: Time since previous event in seconds
        is_note_on: True for note-on, False for note-off
    """
    note: int
    velocity: int
    time_delta: float
    is_note_on: bool = True
    
    def __post_init__(self) -> None:
        if not 0 <= self.note <= 127:
            raise ValueError(f"MIDI note must be 0-127, got {self.note}")
        if not 0 <= self.velocity <= 127:
            raise ValueError(f"Velocity must be 0-127, got {self.velocity}")
        if self.time_delta < 0:
            raise ValueError(f"Time delta cannot be negative, got {self.time_delta}")


@dataclass
class SongInfo:
    """Metadata about a loaded MIDI file.
    
    Attributes:
        filename: Name of the MIDI file
        duration: Total duration in seconds
        note_count: Number of note events
        min_note: Lowest MIDI note number
        max_note: Highest MIDI note number
        transpose_offset: Calculated transpose offset to fit game range
    """
    filename: str
    duration: float
    note_count: int
    min_note: int
    max_note: int
    transpose_offset: int = 0
