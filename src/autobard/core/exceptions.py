"""Custom exceptions for the autobard application."""


class AppError(Exception):
    """Base exception for all application errors."""
    pass


class MidiParseError(AppError):
    """Failed to parse or load a MIDI file."""
    pass


class KeyMappingError(AppError):
    """A note cannot be mapped to a valid game key."""
    pass


class TransposeError(AppError):
    """Failed to transpose notes into playable range."""
    pass


class PlaybackError(AppError):
    """Error during playback execution."""
    pass
