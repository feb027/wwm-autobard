"""Enumerations for the autobard application."""

from enum import Enum, auto


class Pitch(Enum):
    """Pitch levels for the game's 3-octave range."""
    HIGH = auto()
    MID = auto()
    LOW = auto()


class NoteName(Enum):
    """Note names in Jianpu notation (1-7)."""
    DO = 1
    RE = 2
    MI = 3
    FA = 4
    SOL = 5
    LA = 6
    TI = 7


class Accidental(Enum):
    """Note accidentals (sharps and flats)."""
    NATURAL = auto()
    SHARP = auto()
    FLAT = auto()


class PlaybackState(Enum):
    """States for the playback controller."""
    READY = auto()
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()
