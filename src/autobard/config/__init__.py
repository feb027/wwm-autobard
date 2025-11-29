"""Configuration management."""

from .settings import AppConfig
from .constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_INPUT_DELAY_MS,
    DEFAULT_PLAYBACK_SPEED,
    DEFAULT_HOTKEY_START,
    DEFAULT_HOTKEY_STOP,
)

__all__ = [
    "AppConfig",
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_INPUT_DELAY_MS",
    "DEFAULT_PLAYBACK_SPEED",
    "DEFAULT_HOTKEY_START",
    "DEFAULT_HOTKEY_STOP",
]
