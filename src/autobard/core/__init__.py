"""Core business logic - pure Python, no external dependencies."""

from .exceptions import (
    AppError,
    MidiParseError,
    KeyMappingError,
    TransposeError,
    PlaybackError,
)
from .key_mapping import KeyMapper
from .note_converter import NoteConverter, SEMITONE_TO_NOTE, GAME_MIN_MIDI, GAME_MAX_MIDI
from .transposer import Transposer

__all__ = [
    # Exceptions
    "AppError",
    "MidiParseError",
    "KeyMappingError",
    "TransposeError",
    "PlaybackError",
    # Classes
    "KeyMapper",
    "NoteConverter",
    "Transposer",
    # Constants
    "SEMITONE_TO_NOTE",
    "GAME_MIN_MIDI",
    "GAME_MAX_MIDI",
]
