"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path

from autobard.models import Pitch, NoteName, Accidental, GameNote, NoteEvent
from autobard.core import KeyMapper, NoteConverter, Transposer
from autobard.config import AppConfig


@pytest.fixture
def key_mapper() -> KeyMapper:
    """Provide a KeyMapper instance."""
    return KeyMapper()


@pytest.fixture
def note_converter() -> NoteConverter:
    """Provide a NoteConverter instance."""
    return NoteConverter()


@pytest.fixture
def transposer() -> Transposer:
    """Provide a Transposer instance."""
    return Transposer()


@pytest.fixture
def app_config() -> AppConfig:
    """Provide default AppConfig."""
    return AppConfig()


@pytest.fixture
def sample_note_events() -> list[NoteEvent]:
    """Provide sample note events for testing."""
    return [
        NoteEvent(note=60, velocity=100, time_delta=0.0, is_note_on=True),
        NoteEvent(note=62, velocity=100, time_delta=0.5, is_note_on=True),
        NoteEvent(note=64, velocity=100, time_delta=0.5, is_note_on=True),
        NoteEvent(note=65, velocity=100, time_delta=0.5, is_note_on=True),
        NoteEvent(note=67, velocity=100, time_delta=0.5, is_note_on=True),
    ]


@pytest.fixture
def game_note_mid_do() -> GameNote:
    """Provide a MID-DO natural note."""
    return GameNote(pitch=Pitch.MID, name=NoteName.DO, accidental=Accidental.NATURAL)


@pytest.fixture
def game_note_high_fa_sharp() -> GameNote:
    """Provide a HIGH-FA sharp note."""
    return GameNote(pitch=Pitch.HIGH, name=NoteName.FA, accidental=Accidental.SHARP)


@pytest.fixture
def game_note_low_mi_flat() -> GameNote:
    """Provide a LOW-MI flat note."""
    return GameNote(pitch=Pitch.LOW, name=NoteName.MI, accidental=Accidental.FLAT)
