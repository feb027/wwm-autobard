"""Tests for KeyMapper class."""

import pytest
from autobard.models import Pitch, NoteName, Accidental, GameNote, KeyPress
from autobard.core import KeyMapper


class TestKeyMapperNatural:
    """Test natural note mapping."""
    
    def test_mid_do_natural(self, key_mapper: KeyMapper):
        """MID-DO should map to 'a' with no modifiers."""
        note = GameNote(Pitch.MID, NoteName.DO, Accidental.NATURAL)
        result = key_mapper.get_key_press(note)
        assert result.key == "a"
        assert result.modifiers == ()
    
    def test_high_sol_natural(self, key_mapper: KeyMapper):
        """HIGH-SOL should map to 't' with no modifiers."""
        note = GameNote(Pitch.HIGH, NoteName.SOL, Accidental.NATURAL)
        result = key_mapper.get_key_press(note)
        assert result.key == "t"
        assert result.modifiers == ()
    
    def test_low_ti_natural(self, key_mapper: KeyMapper):
        """LOW-TI should map to 'm' with no modifiers."""
        note = GameNote(Pitch.LOW, NoteName.TI, Accidental.NATURAL)
        result = key_mapper.get_key_press(note)
        assert result.key == "m"
        assert result.modifiers == ()


class TestKeyMapperSharp:
    """Test sharp note mapping."""
    
    def test_high_do_sharp(self, key_mapper: KeyMapper):
        """HIGH-DO# should map to 'q' with shift."""
        note = GameNote(Pitch.HIGH, NoteName.DO, Accidental.SHARP)
        result = key_mapper.get_key_press(note)
        assert result.key == "q"
        assert result.modifiers == ("shift",)
    
    def test_mid_fa_sharp(self, key_mapper: KeyMapper):
        """MID-FA# should map to 'f' with shift."""
        note = GameNote(Pitch.MID, NoteName.FA, Accidental.SHARP)
        result = key_mapper.get_key_press(note)
        assert result.key == "f"
        assert result.modifiers == ("shift",)
    
    def test_low_sol_sharp(self, key_mapper: KeyMapper):
        """LOW-SOL# should map to 'b' with shift."""
        note = GameNote(Pitch.LOW, NoteName.SOL, Accidental.SHARP)
        result = key_mapper.get_key_press(note)
        assert result.key == "b"
        assert result.modifiers == ("shift",)


class TestKeyMapperFlat:
    """Test flat note mapping."""
    
    def test_high_mi_flat(self, key_mapper: KeyMapper):
        """HIGH-MIb should map to 'e' with ctrl."""
        note = GameNote(Pitch.HIGH, NoteName.MI, Accidental.FLAT)
        result = key_mapper.get_key_press(note)
        assert result.key == "e"
        assert result.modifiers == ("ctrl",)
    
    def test_mid_ti_flat(self, key_mapper: KeyMapper):
        """MID-TIb should map to 'j' with ctrl."""
        note = GameNote(Pitch.MID, NoteName.TI, Accidental.FLAT)
        result = key_mapper.get_key_press(note)
        assert result.key == "j"
        assert result.modifiers == ("ctrl",)
    
    def test_low_mi_flat(self, key_mapper: KeyMapper):
        """LOW-MIb should map to 'c' with ctrl."""
        note = GameNote(Pitch.LOW, NoteName.MI, Accidental.FLAT)
        result = key_mapper.get_key_press(note)
        assert result.key == "c"
        assert result.modifiers == ("ctrl",)


class TestKeyMapperFallback:
    """Test fallback behavior for unsupported accidentals."""
    
    def test_unsupported_sharp_falls_back(self, key_mapper: KeyMapper):
        """RE# (unsupported) should fall back to natural RE."""
        note = GameNote(Pitch.MID, NoteName.RE, Accidental.SHARP)
        result = key_mapper.get_key_press(note)
        assert result.key == "s"  # Natural RE
        assert result.modifiers == ()
    
    def test_unsupported_flat_falls_back(self, key_mapper: KeyMapper):
        """DOb (unsupported) should fall back to natural DO."""
        note = GameNote(Pitch.HIGH, NoteName.DO, Accidental.FLAT)
        result = key_mapper.get_key_press(note)
        assert result.key == "q"  # Natural DO
        assert result.modifiers == ()
    
    def test_la_sharp_falls_back(self, key_mapper: KeyMapper):
        """LA# (unsupported) should fall back to natural LA."""
        note = GameNote(Pitch.LOW, NoteName.LA, Accidental.SHARP)
        result = key_mapper.get_key_press(note)
        assert result.key == "n"  # Natural LA
        assert result.modifiers == ()


class TestKeyMapperAccidentalSupport:
    """Test accidental support checking."""
    
    def test_natural_always_supported(self, key_mapper: KeyMapper):
        """Natural accidental should always be supported."""
        for name in NoteName:
            assert key_mapper.is_accidental_supported(name, Accidental.NATURAL)
    
    def test_supported_sharps(self, key_mapper: KeyMapper):
        """Only DO, FA, SOL sharps should be supported."""
        assert key_mapper.is_accidental_supported(NoteName.DO, Accidental.SHARP)
        assert key_mapper.is_accidental_supported(NoteName.FA, Accidental.SHARP)
        assert key_mapper.is_accidental_supported(NoteName.SOL, Accidental.SHARP)
        assert not key_mapper.is_accidental_supported(NoteName.RE, Accidental.SHARP)
        assert not key_mapper.is_accidental_supported(NoteName.LA, Accidental.SHARP)
    
    def test_supported_flats(self, key_mapper: KeyMapper):
        """Only MI, TI flats should be supported."""
        assert key_mapper.is_accidental_supported(NoteName.MI, Accidental.FLAT)
        assert key_mapper.is_accidental_supported(NoteName.TI, Accidental.FLAT)
        assert not key_mapper.is_accidental_supported(NoteName.DO, Accidental.FLAT)
        assert not key_mapper.is_accidental_supported(NoteName.FA, Accidental.FLAT)
