"""MIDI note number to GameNote conversion.

This module converts standard MIDI note numbers (0-127) to the game's
3-octave Jianpu notation system.

MIDI note mapping:
- Middle C (C4) = MIDI 60
- The game supports 3 octaves (LOW, MID, HIGH)
- Each octave has 12 semitones

This module is pure Python with no external dependencies.
"""

from ..models.enums import Pitch, NoteName, Accidental
from ..models.note import GameNote


# MIDI note to scale degree mapping within an octave (0-11 semitones)
# C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
SEMITONE_TO_NOTE: dict[int, tuple[NoteName, Accidental]] = {
    0: (NoteName.DO, Accidental.NATURAL),    # C
    1: (NoteName.DO, Accidental.SHARP),      # C# / Db
    2: (NoteName.RE, Accidental.NATURAL),    # D
    3: (NoteName.MI, Accidental.FLAT),       # D# / Eb (use Eb = Mib)
    4: (NoteName.MI, Accidental.NATURAL),    # E
    5: (NoteName.FA, Accidental.NATURAL),    # F
    6: (NoteName.FA, Accidental.SHARP),      # F# / Gb
    7: (NoteName.SOL, Accidental.NATURAL),   # G
    8: (NoteName.SOL, Accidental.SHARP),     # G# / Ab
    9: (NoteName.LA, Accidental.NATURAL),    # A
    10: (NoteName.TI, Accidental.FLAT),      # A# / Bb (use Bb = Tib)
    11: (NoteName.TI, Accidental.NATURAL),   # B
}

# Game's playable range (3 octaves)
# We define the "base" octave as MID, centered around middle C
GAME_OCTAVE_LOW = 4    # C4-B4 maps to LOW by default (after transpose)
GAME_OCTAVE_MID = 5    # C5-B5 maps to MID
GAME_OCTAVE_HIGH = 6   # C6-B6 maps to HIGH

# MIDI note range for the game (3 octaves = 36 notes)
GAME_MIN_MIDI = 48     # C3 (LOW Do at default)
GAME_MAX_MIDI = 83     # B5 (HIGH Ti at default)
GAME_RANGE = GAME_MAX_MIDI - GAME_MIN_MIDI + 1  # 36 notes


class NoteConverter:
    """Converts MIDI note numbers to GameNote objects.
    
    Handles octave detection and maps semitones to the game's
    Jianpu notation with appropriate accidentals.
    """
    
    def __init__(self, base_octave: int = 4):
        """Initialize the converter.
        
        Args:
            base_octave: The MIDI octave number that maps to LOW pitch.
                        Default is 4 (C4 = MIDI 48 = LOW Do)
        """
        self._base_octave = base_octave
    
    @property
    def min_midi_note(self) -> int:
        """Minimum playable MIDI note."""
        return self._base_octave * 12  # C of base octave
    
    @property
    def max_midi_note(self) -> int:
        """Maximum playable MIDI note."""
        return (self._base_octave + 3) * 12 - 1  # B of base+2 octave
    
    def convert(self, midi_note: int) -> GameNote:
        """Convert a MIDI note number to a GameNote.
        
        Args:
            midi_note: MIDI note number (0-127)
            
        Returns:
            GameNote with pitch, name, and accidental
            
        Note:
            Notes outside the 3-octave range will be clamped to the
            nearest valid octave. Use Transposer first to shift the
            entire song into range.
        """
        # Clamp to valid range
        clamped_note = max(self.min_midi_note, min(midi_note, self.max_midi_note))
        
        # Calculate octave and semitone within octave
        octave = clamped_note // 12
        semitone = clamped_note % 12
        
        # Determine pitch based on octave relative to base
        octave_offset = octave - self._base_octave
        if octave_offset <= 0:
            pitch = Pitch.LOW
        elif octave_offset == 1:
            pitch = Pitch.MID
        else:
            pitch = Pitch.HIGH
        
        # Get note name and accidental from semitone
        name, accidental = SEMITONE_TO_NOTE[semitone]
        
        return GameNote(pitch=pitch, name=name, accidental=accidental)
    
    def is_in_range(self, midi_note: int) -> bool:
        """Check if a MIDI note is within the playable range.
        
        Args:
            midi_note: MIDI note number to check
            
        Returns:
            True if the note is within the 3-octave game range
        """
        return self.min_midi_note <= midi_note <= self.max_midi_note
    
    def get_range(self) -> tuple[int, int]:
        """Get the playable MIDI note range.
        
        Returns:
            Tuple of (min_note, max_note)
        """
        return (self.min_midi_note, self.max_midi_note)
