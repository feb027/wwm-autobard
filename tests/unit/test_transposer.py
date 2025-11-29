"""Tests for Transposer class."""

import pytest
from autobard.models import NoteEvent
from autobard.core import Transposer


class TestTransposerOffset:
    """Test transpose offset calculation."""
    
    def test_no_transpose_when_in_range(self, transposer: Transposer):
        """Songs already in range should have 0 offset."""
        offset = transposer.calculate_offset((48, 83))  # Exact game range
        assert offset == 0
    
    def test_transpose_up_when_too_low(self, transposer: Transposer):
        """Songs below range should transpose up."""
        offset = transposer.calculate_offset((36, 71))  # One octave too low
        assert offset > 0
    
    def test_transpose_down_when_too_high(self, transposer: Transposer):
        """Songs above range should transpose down."""
        offset = transposer.calculate_offset((60, 95))  # One octave too high
        assert offset < 0
    
    def test_prefers_octave_shifts(self, transposer: Transposer):
        """When possible, shift by full octaves (12 semitones)."""
        offset = transposer.calculate_offset((36, 71))  # Needs +12 shift
        assert offset % 12 == 0 or abs(offset) < 12


class TestTransposerApply:
    """Test applying transpose to events."""
    
    def test_apply_zero_offset_unchanged(self, transposer: Transposer, sample_note_events):
        """Zero offset should return identical events."""
        result = transposer.apply_transpose(sample_note_events, 0)
        assert len(result) == len(sample_note_events)
        for orig, new in zip(sample_note_events, result):
            assert orig.note == new.note
    
    def test_apply_positive_offset(self, transposer: Transposer):
        """Positive offset should raise note values."""
        events = [NoteEvent(note=60, velocity=100, time_delta=0.0)]
        result = transposer.apply_transpose(events, 12)
        assert result[0].note == 72
    
    def test_apply_negative_offset(self, transposer: Transposer):
        """Negative offset should lower note values."""
        events = [NoteEvent(note=72, velocity=100, time_delta=0.0)]
        result = transposer.apply_transpose(events, -12)
        assert result[0].note == 60
    
    def test_clamps_to_valid_midi_range(self, transposer: Transposer):
        """Transposed notes should clamp to 0-127."""
        events = [NoteEvent(note=10, velocity=100, time_delta=0.0)]
        result = transposer.apply_transpose(events, -20)
        assert result[0].note == 0
        
        events = [NoteEvent(note=120, velocity=100, time_delta=0.0)]
        result = transposer.apply_transpose(events, 20)
        assert result[0].note == 127
    
    def test_preserves_other_fields(self, transposer: Transposer):
        """Transpose should preserve velocity, time_delta, is_note_on."""
        events = [NoteEvent(note=60, velocity=80, time_delta=0.5, is_note_on=True)]
        result = transposer.apply_transpose(events, 5)
        assert result[0].velocity == 80
        assert result[0].time_delta == 0.5
        assert result[0].is_note_on is True


class TestTransposerOutOfRange:
    """Test out-of-range note counting."""
    
    def test_count_notes_below_range(self, transposer: Transposer):
        """Should count notes below playable range."""
        events = [
            NoteEvent(note=40, velocity=100, time_delta=0.0),  # Below
            NoteEvent(note=60, velocity=100, time_delta=0.0),  # In range
        ]
        below, above = transposer.get_out_of_range_count(events)
        assert below == 1
        assert above == 0
    
    def test_count_notes_above_range(self, transposer: Transposer):
        """Should count notes above playable range."""
        events = [
            NoteEvent(note=60, velocity=100, time_delta=0.0),  # In range
            NoteEvent(note=90, velocity=100, time_delta=0.0),  # Above
        ]
        below, above = transposer.get_out_of_range_count(events)
        assert below == 0
        assert above == 1
    
    def test_count_with_offset(self, transposer: Transposer):
        """Should apply offset before counting."""
        events = [NoteEvent(note=40, velocity=100, time_delta=0.0)]
        below, above = transposer.get_out_of_range_count(events, offset=12)
        assert below == 0  # 40 + 12 = 52, now in range


class TestTransposerAnalyze:
    """Test song range analysis."""
    
    def test_analyze_empty_events(self, transposer: Transposer):
        """Empty events should return safe defaults."""
        result = transposer.analyze_range([])
        assert result["fits_in_game"] is True
        assert result["recommended_offset"] == 0
    
    def test_analyze_finds_range(self, transposer: Transposer, sample_note_events):
        """Should find min/max notes in events."""
        result = transposer.analyze_range(sample_note_events)
        assert result["min_note"] == 60
        assert result["max_note"] == 67
    
    def test_analyze_fits_in_game(self, transposer: Transposer, sample_note_events):
        """Small range should fit in game."""
        result = transposer.analyze_range(sample_note_events)
        assert result["fits_in_game"] is True
    
    def test_analyze_wide_range_does_not_fit(self, transposer: Transposer):
        """Range > 36 semitones should not fit."""
        events = [
            NoteEvent(note=30, velocity=100, time_delta=0.0),
            NoteEvent(note=100, velocity=100, time_delta=0.0),
        ]
        result = transposer.analyze_range(events)
        assert result["fits_in_game"] is False
