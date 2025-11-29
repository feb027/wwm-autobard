"""Tests for the key mapping lookup tables."""

import pytest
from autobard.models import (
    Pitch, 
    NoteName, 
    NATURAL_KEYS, 
    SHARP_KEYS, 
    FLAT_KEYS,
    SHARPS_SUPPORTED,
    FLATS_SUPPORTED,
)


class TestNaturalKeys:
    """Test NATURAL_KEYS mapping table."""
    
    def test_has_all_pitches(self):
        """All three pitch levels should be present."""
        assert Pitch.HIGH in NATURAL_KEYS
        assert Pitch.MID in NATURAL_KEYS
        assert Pitch.LOW in NATURAL_KEYS
    
    def test_has_all_notes_per_pitch(self):
        """Each pitch should have all 7 notes."""
        for pitch in Pitch:
            assert len(NATURAL_KEYS[pitch]) == 7
            for note_name in NoteName:
                assert note_name in NATURAL_KEYS[pitch]
    
    def test_total_natural_keys(self):
        """Should have 21 natural keys (3 pitches x 7 notes)."""
        total = sum(len(notes) for notes in NATURAL_KEYS.values())
        assert total == 21
    
    def test_high_pitch_keys(self):
        """HIGH pitch should map to Q-U row."""
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.DO] == "q"
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.RE] == "w"
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.MI] == "e"
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.FA] == "r"
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.SOL] == "t"
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.LA] == "y"
        assert NATURAL_KEYS[Pitch.HIGH][NoteName.TI] == "u"
    
    def test_mid_pitch_keys(self):
        """MID pitch should map to A-J row."""
        assert NATURAL_KEYS[Pitch.MID][NoteName.DO] == "a"
        assert NATURAL_KEYS[Pitch.MID][NoteName.RE] == "s"
        assert NATURAL_KEYS[Pitch.MID][NoteName.MI] == "d"
        assert NATURAL_KEYS[Pitch.MID][NoteName.FA] == "f"
        assert NATURAL_KEYS[Pitch.MID][NoteName.SOL] == "g"
        assert NATURAL_KEYS[Pitch.MID][NoteName.LA] == "h"
        assert NATURAL_KEYS[Pitch.MID][NoteName.TI] == "j"
    
    def test_low_pitch_keys(self):
        """LOW pitch should map to Z-M row."""
        assert NATURAL_KEYS[Pitch.LOW][NoteName.DO] == "z"
        assert NATURAL_KEYS[Pitch.LOW][NoteName.RE] == "x"
        assert NATURAL_KEYS[Pitch.LOW][NoteName.MI] == "c"
        assert NATURAL_KEYS[Pitch.LOW][NoteName.FA] == "v"
        assert NATURAL_KEYS[Pitch.LOW][NoteName.SOL] == "b"
        assert NATURAL_KEYS[Pitch.LOW][NoteName.LA] == "n"
        assert NATURAL_KEYS[Pitch.LOW][NoteName.TI] == "m"


class TestSharpKeys:
    """Test SHARP_KEYS mapping table."""
    
    def test_only_supported_sharps(self):
        """Only Do, Fa, Sol should have sharp variants."""
        assert SHARPS_SUPPORTED == frozenset({NoteName.DO, NoteName.FA, NoteName.SOL})
    
    def test_total_sharp_keys(self):
        """Should have 9 sharp keys (3 pitches x 3 notes)."""
        total = sum(len(notes) for notes in SHARP_KEYS.values())
        assert total == 9
    
    def test_sharp_keys_per_pitch(self):
        """Each pitch should have exactly 3 sharp notes."""
        for pitch in Pitch:
            assert len(SHARP_KEYS[pitch]) == 3


class TestFlatKeys:
    """Test FLAT_KEYS mapping table."""
    
    def test_only_supported_flats(self):
        """Only Mi, Ti should have flat variants."""
        assert FLATS_SUPPORTED == frozenset({NoteName.MI, NoteName.TI})
    
    def test_total_flat_keys(self):
        """Should have 6 flat keys (3 pitches x 2 notes)."""
        total = sum(len(notes) for notes in FLAT_KEYS.values())
        assert total == 6
    
    def test_flat_keys_per_pitch(self):
        """Each pitch should have exactly 2 flat notes."""
        for pitch in Pitch:
            assert len(FLAT_KEYS[pitch]) == 2


class TestTotalGameKeys:
    """Test total key coverage."""
    
    def test_total_36_keys(self):
        """Game should support 36 total keys (21 + 9 + 6)."""
        natural = sum(len(n) for n in NATURAL_KEYS.values())
        sharps = sum(len(n) for n in SHARP_KEYS.values())
        flats = sum(len(n) for n in FLAT_KEYS.values())
        assert natural + sharps + flats == 36
