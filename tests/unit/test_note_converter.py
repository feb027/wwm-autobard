"""Tests for NoteConverter class."""

import pytest
from autobard.models import Pitch, NoteName, Accidental
from autobard.core import NoteConverter


class TestNoteConverterBasic:
    """Test basic MIDI to GameNote conversion."""
    
    def test_middle_c_converts_to_mid_do(self, note_converter: NoteConverter):
        """MIDI 60 (C4) should convert to MID-DO."""
        result = note_converter.convert(60)
        assert result.pitch == Pitch.MID
        assert result.name == NoteName.DO
        assert result.accidental == Accidental.NATURAL
    
    def test_c_sharp_converts_to_do_sharp(self, note_converter: NoteConverter):
        """MIDI 61 (C#4) should convert to MID-DO#."""
        result = note_converter.convert(61)
        assert result.pitch == Pitch.MID
        assert result.name == NoteName.DO
        assert result.accidental == Accidental.SHARP
    
    def test_d_converts_to_re(self, note_converter: NoteConverter):
        """MIDI 62 (D4) should convert to MID-RE."""
        result = note_converter.convert(62)
        assert result.pitch == Pitch.MID
        assert result.name == NoteName.RE
        assert result.accidental == Accidental.NATURAL
    
    def test_e_flat_converts_to_mi_flat(self, note_converter: NoteConverter):
        """MIDI 63 (Eb4) should convert to MID-MIb."""
        result = note_converter.convert(63)
        assert result.pitch == Pitch.MID
        assert result.name == NoteName.MI
        assert result.accidental == Accidental.FLAT


class TestNoteConverterOctaves:
    """Test octave detection across pitches."""
    
    def test_low_octave(self, note_converter: NoteConverter):
        """Notes in base octave should be LOW pitch."""
        result = note_converter.convert(48)  # C3
        assert result.pitch == Pitch.LOW
    
    def test_mid_octave(self, note_converter: NoteConverter):
        """Notes in base+1 octave should be MID pitch."""
        result = note_converter.convert(60)  # C4
        assert result.pitch == Pitch.MID
    
    def test_high_octave(self, note_converter: NoteConverter):
        """Notes in base+2 octave should be HIGH pitch."""
        result = note_converter.convert(72)  # C5
        assert result.pitch == Pitch.HIGH


class TestNoteConverterRange:
    """Test note range handling."""
    
    def test_is_in_range_valid(self, note_converter: NoteConverter):
        """Notes within 3-octave range should be valid."""
        assert note_converter.is_in_range(48)   # Low end
        assert note_converter.is_in_range(60)   # Middle
        assert note_converter.is_in_range(83)   # High end
    
    def test_is_in_range_invalid_low(self, note_converter: NoteConverter):
        """Notes below range should be invalid."""
        assert not note_converter.is_in_range(47)
        assert not note_converter.is_in_range(0)
    
    def test_is_in_range_invalid_high(self, note_converter: NoteConverter):
        """Notes above range should be invalid."""
        assert not note_converter.is_in_range(84)
        assert not note_converter.is_in_range(127)
    
    def test_get_range(self, note_converter: NoteConverter):
        """Range should span 3 octaves."""
        min_note, max_note = note_converter.get_range()
        assert max_note - min_note + 1 == 36


class TestNoteConverterClamping:
    """Test note clamping for out-of-range values."""
    
    def test_clamps_low_notes(self, note_converter: NoteConverter):
        """Notes below range should clamp to LOW pitch."""
        result = note_converter.convert(30)  # Way below range
        assert result.pitch == Pitch.LOW
    
    def test_clamps_high_notes(self, note_converter: NoteConverter):
        """Notes above range should clamp to HIGH pitch."""
        result = note_converter.convert(100)  # Way above range
        assert result.pitch == Pitch.HIGH


class TestNoteConverterAllSemitones:
    """Test all 12 semitones map correctly."""
    
    @pytest.mark.parametrize("semitone,expected_name,expected_acc", [
        (0, NoteName.DO, Accidental.NATURAL),     # C
        (1, NoteName.DO, Accidental.SHARP),       # C#
        (2, NoteName.RE, Accidental.NATURAL),     # D
        (3, NoteName.MI, Accidental.FLAT),        # Eb
        (4, NoteName.MI, Accidental.NATURAL),     # E
        (5, NoteName.FA, Accidental.NATURAL),     # F
        (6, NoteName.FA, Accidental.SHARP),       # F#
        (7, NoteName.SOL, Accidental.NATURAL),    # G
        (8, NoteName.SOL, Accidental.SHARP),      # G#
        (9, NoteName.LA, Accidental.NATURAL),     # A
        (10, NoteName.TI, Accidental.FLAT),       # Bb
        (11, NoteName.TI, Accidental.NATURAL),    # B
    ])
    def test_semitone_mapping(self, note_converter: NoteConverter, semitone, expected_name, expected_acc):
        """Each semitone should map to correct note name and accidental."""
        midi_note = 60 + semitone  # Base on middle C
        result = note_converter.convert(midi_note)
        assert result.name == expected_name
        assert result.accidental == expected_acc
