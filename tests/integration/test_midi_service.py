"""Integration tests for MidiService."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

from autobard.services import MidiService
from autobard.core.exceptions import MidiParseError


class TestMidiServiceInit:
    """Test MidiService initialization."""
    
    def test_initial_state(self):
        """Service should start with no file loaded."""
        service = MidiService()
        assert service.is_loaded is False
        assert service.current_file is None
        assert service.get_song_info() is None


class TestMidiServiceLoading:
    """Test MIDI file loading with mocked mido."""
    
    def test_load_valid_file(self):
        """Should load and parse a valid MIDI file."""
        # Setup mock
        mock_mido = MagicMock()
        mock_msg1 = Mock()
        mock_msg1.type = 'note_on'
        mock_msg1.note = 60
        mock_msg1.velocity = 100
        mock_msg1.time = 0.0
        
        mock_msg2 = Mock()
        mock_msg2.type = 'note_on'
        mock_msg2.note = 62
        mock_msg2.velocity = 100
        mock_msg2.time = 0.5
        
        mock_midi_file = MagicMock()
        mock_midi_file.__iter__ = Mock(return_value=iter([mock_msg1, mock_msg2]))
        mock_mido.MidiFile.return_value = mock_midi_file
        
        with patch.dict(sys.modules, {'mido': mock_mido}):
            service = MidiService()
            events = service.load_file(Path("test.mid"))
            
            assert len(events) == 2
            assert events[0].note == 60
            assert events[1].note == 62
            assert service.is_loaded is True
    
    def test_load_file_updates_song_info(self):
        """Loading should populate song info."""
        mock_mido = MagicMock()
        mock_msg = Mock()
        mock_msg.type = 'note_on'
        mock_msg.note = 60
        mock_msg.velocity = 100
        mock_msg.time = 1.0
        
        mock_midi_file = MagicMock()
        mock_midi_file.__iter__ = Mock(return_value=iter([mock_msg]))
        mock_mido.MidiFile.return_value = mock_midi_file
        
        with patch.dict(sys.modules, {'mido': mock_mido}):
            service = MidiService()
            service.load_file(Path("song.mid"))
            
            info = service.get_song_info()
            assert info is not None
            assert info.filename == "song.mid"
            assert info.note_count == 1
    
    def test_load_only_returns_note_on(self):
        """Should only return note_on events (note_off is ignored for playback)."""
        mock_mido = MagicMock()
        mock_note_on = Mock()
        mock_note_on.type = 'note_on'
        mock_note_on.note = 60
        mock_note_on.velocity = 100
        mock_note_on.time = 0.0
        
        mock_note_off = Mock()
        mock_note_off.type = 'note_off'
        mock_note_off.note = 60
        mock_note_off.velocity = 0
        mock_note_off.time = 0.5
        
        mock_midi_file = MagicMock()
        mock_midi_file.__iter__ = Mock(return_value=iter([mock_note_on, mock_note_off]))
        mock_mido.MidiFile.return_value = mock_midi_file
        
        with patch.dict(sys.modules, {'mido': mock_mido}):
            service = MidiService()
            events = service.load_file(Path("test.mid"))
            
            # Only note_on events are returned (note_off ignored)
            assert len(events) == 1
            assert events[0].is_note_on is True


class TestMidiServiceNoteRange:
    """Test note range calculation."""
    
    def test_get_note_range(self):
        """Should return min and max notes."""
        mock_mido = MagicMock()
        messages = []
        for note in [60, 65, 72, 55]:
            msg = Mock()
            msg.type = 'note_on'
            msg.note = note
            msg.velocity = 100
            msg.time = 0.1
            messages.append(msg)
        
        mock_midi_file = MagicMock()
        mock_midi_file.__iter__ = Mock(return_value=iter(messages))
        mock_mido.MidiFile.return_value = mock_midi_file
        
        with patch.dict(sys.modules, {'mido': mock_mido}):
            service = MidiService()
            service.load_file(Path("test.mid"))
            
            min_note, max_note = service.get_note_range()
            assert min_note == 55
            assert max_note == 72
    
    def test_get_note_range_no_file(self):
        """Should return default range when no file loaded."""
        service = MidiService()
        min_note, max_note = service.get_note_range()
        assert min_note == 60  # Default middle C
        assert max_note == 60


class TestMidiServiceErrors:
    """Test error handling."""
    
    def test_raises_on_invalid_file(self):
        """Should raise MidiParseError on invalid file."""
        mock_mido = MagicMock()
        mock_mido.MidiFile.side_effect = Exception("Invalid file")
        
        with patch.dict(sys.modules, {'mido': mock_mido}):
            service = MidiService()
            with pytest.raises(MidiParseError):
                service.load_file(Path("invalid.mid"))
