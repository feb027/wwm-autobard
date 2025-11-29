"""Application configuration management."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Configuration settings for WWM Auto-Bard."""
    # Playback settings
    input_delay_ms: int = 50
    min_note_delay_ms: int = 80
    playback_speed: float = 1.0
    auto_optimize: bool = True
    loop_mode: bool = False
    countdown_seconds: int = 3
    
    # Natural sound improvements
    humanize_ms: int = 12
    chord_strum_ms: int = 6
    velocity_timing: bool = True
    dynamic_tempo: bool = True
    
    # Performance options
    high_performance: bool = True
    
    # Hotkeys
    hotkey_start: str = "f10"
    hotkey_stop: str = "f12"
    
    # Window settings
    window_opacity: float = 0.9
    window_always_on_top: bool = True
    window_x: int = -1  # -1 = center
    window_y: int = -1
    window_width: int = 380
    window_height: int = 600
    
    # Song library
    recent_files: list = None
    library_path: str = ""
    
    def __post_init__(self):
        if self.recent_files is None:
            self.recent_files = []
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AppConfig":
        """Load configuration from a JSON file.
        
        Args:
            path: Path to config file. Uses default if None.
            
        Returns:
            AppConfig instance (defaults if file not found)
        """
        if path is None:
            path = cls.get_default_path()
        
        if path.exists():
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded config from {path}")
                return cls(**data)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        return cls()
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to a JSON file.
        
        Args:
            path: Path to save to. Uses default if None.
        """
        if path is None:
            path = self.get_default_path()
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Saved config to {path}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "input_delay_ms": self.input_delay_ms,
            "min_note_delay_ms": self.min_note_delay_ms,
            "playback_speed": self.playback_speed,
            "auto_optimize": self.auto_optimize,
            "loop_mode": self.loop_mode,
            "countdown_seconds": self.countdown_seconds,
            "humanize_ms": self.humanize_ms,
            "chord_strum_ms": self.chord_strum_ms,
            "velocity_timing": self.velocity_timing,
            "dynamic_tempo": self.dynamic_tempo,
            "high_performance": self.high_performance,
            "hotkey_start": self.hotkey_start,
            "hotkey_stop": self.hotkey_stop,
            "window_opacity": self.window_opacity,
            "window_always_on_top": self.window_always_on_top,
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "recent_files": self.recent_files,
            "library_path": self.library_path,
        }
    
    def add_recent_file(self, path: str, max_recent: int = 10) -> None:
        """Add a file to recent files list."""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:max_recent]
    
    @staticmethod
    def get_default_path() -> Path:
        """Get the default config file path."""
        # Use local directory for portability
        return Path("config.json")
