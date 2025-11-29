"""Main overlay window for WWM Auto-Bard."""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import TYPE_CHECKING

from ..models import PlaybackState
from ..config import APP_NAME
from .widgets.status_indicator import StatusIndicator
from .widgets.speed_slider import SpeedSlider
from .widgets.file_selector import FileSelector
from .widgets.track_selector import TrackSelector

if TYPE_CHECKING:
    from ..app import AutoBardApp


class MainWindow:
    """Main application window - compact overlay design.
    
    Displays as a small, semi-transparent window that floats
    above other applications (including games).
    """
    
    def __init__(self, root: tk.Tk, app: "AutoBardApp"):
        """Initialize the main window.
        
        Args:
            root: The Tk root window
            app: The application controller
        """
        self._root = root
        self._app = app
        
        self._setup_window()
        self._create_widgets()
        self._bind_events()
        
        # Register as observer
        app.on_state_change(self._on_state_change)
        app.on_progress(self._on_progress)
    
    def _setup_window(self) -> None:
        """Configure the window appearance."""
        self._root.title(APP_NAME)
        self._root.geometry("280x260")
        self._root.resizable(False, False)
        self._root.configure(bg="#2b2b2b")
        
        # Always on top
        if self._app.config.window_always_on_top:
            self._root.attributes("-topmost", True)
        
        # Semi-transparent (Windows)
        try:
            self._root.attributes("-alpha", self._app.config.window_opacity)
        except tk.TclError:
            pass  # Alpha not supported on this platform
        
        # Remove window decorations for cleaner look (optional)
        # self._root.overrideredirect(True)
    
    def _create_widgets(self) -> None:
        """Create and layout all widgets."""
        # Main container with padding
        main_frame = tk.Frame(self._root, bg="#2b2b2b", padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            main_frame,
            text=APP_NAME,
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#2b2b2b"
        )
        title.pack(anchor=tk.W, pady=(0, 8))
        
        # Status indicator
        self._status = StatusIndicator(main_frame)
        self._status.pack(fill=tk.X, pady=(0, 12))
        
        # File selector
        self._file_selector = FileSelector(
            main_frame,
            on_file_selected=self._on_file_selected
        )
        self._file_selector.pack(fill=tk.X, pady=(0, 8))
        
        # Track selector
        self._track_selector = TrackSelector(
            main_frame,
            on_track_change=self._on_track_change
        )
        self._track_selector.pack(fill=tk.X, pady=(0, 12))
        
        # Speed slider
        self._speed_slider = SpeedSlider(
            main_frame,
            on_change=self._on_speed_change
        )
        self._speed_slider.pack(fill=tk.X, pady=(0, 12))
        
        # Delay slider
        self._delay_frame = tk.Frame(main_frame, bg="#2b2b2b")
        self._delay_frame.pack(fill=tk.X, pady=(0, 8))
        
        delay_label = tk.Label(
            self._delay_frame,
            text="Input Delay",
            font=("Segoe UI", 9),
            fg="#aaaaaa",
            bg="#2b2b2b"
        )
        delay_label.pack(anchor=tk.W)
        
        delay_inner = tk.Frame(self._delay_frame, bg="#2b2b2b")
        delay_inner.pack(fill=tk.X, pady=(2, 0))
        
        self._delay_value = tk.IntVar(value=self._app.config.input_delay_ms)
        self._delay_slider = ttk.Scale(
            delay_inner,
            from_=0,
            to=200,
            orient=tk.HORIZONTAL,
            variable=self._delay_value,
            command=self._on_delay_change
        )
        self._delay_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self._delay_label = tk.Label(
            delay_inner,
            text=f"{self._app.config.input_delay_ms}ms",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg="#2b2b2b",
            width=5
        )
        self._delay_label.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Hotkey hints
        hints = tk.Label(
            main_frame,
            text=f"F10: Start/Pause | F12: Stop",
            font=("Segoe UI", 8),
            fg="#666666",
            bg="#2b2b2b"
        )
        hints.pack(anchor=tk.W, pady=(4, 0))
    
    def _bind_events(self) -> None:
        """Bind keyboard shortcuts."""
        self._root.bind("<F10>", lambda e: self._toggle_playback())
        self._root.bind("<F12>", lambda e: self._app.stop())
        self._root.bind("<Escape>", lambda e: self._app.stop())
    
    def _toggle_playback(self) -> None:
        """Toggle between play and pause."""
        if self._app.state == PlaybackState.PLAYING:
            self._app.pause()
        else:
            self._app.start()
    
    def _on_file_selected(self, path: Path) -> None:
        """Handle file selection."""
        success = self._app.load_midi(path)
        if success:
            # Update track selector with track info
            track_info = self._app.get_track_info()
            self._track_selector.set_tracks(track_info)
        else:
            self._file_selector.clear()
    
    def _on_track_change(self, track: int) -> None:
        """Handle track selection change."""
        self._app.reload_track(track)
    
    def _on_speed_change(self, speed: float) -> None:
        """Handle speed slider change."""
        self._app.set_playback_speed(speed)
    
    def _on_delay_change(self, value: str) -> None:
        """Handle delay slider change."""
        delay = int(float(value))
        self._app.set_input_delay(delay)
        self._delay_label.config(text=f"{delay}ms")
    
    def _on_state_change(self, state: PlaybackState) -> None:
        """Handle playback state changes (Observer callback)."""
        self._status.set_state(state)
    
    def _on_progress(self, current: int, total: int) -> None:
        """Handle progress updates (Observer callback)."""
        # Could update a progress bar here
        pass
    
    def run(self) -> None:
        """Start the main event loop."""
        self._root.mainloop()
