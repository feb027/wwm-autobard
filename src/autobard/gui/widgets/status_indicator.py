"""Status indicator widget for playback state."""

import tkinter as tk
from typing import Dict

from ...models import PlaybackState


class StatusIndicator(tk.Frame):
    """Visual indicator showing the current playback state."""
    
    STATE_COLORS: Dict[PlaybackState, str] = {
        PlaybackState.READY: "#4CAF50",     # Green
        PlaybackState.PLAYING: "#2196F3",   # Blue
        PlaybackState.PAUSED: "#FF9800",    # Orange
        PlaybackState.STOPPED: "#F44336",   # Red
    }
    
    STATE_TEXT: Dict[PlaybackState, str] = {
        PlaybackState.READY: "Ready",
        PlaybackState.PLAYING: "Playing",
        PlaybackState.PAUSED: "Paused",
        PlaybackState.STOPPED: "Stopped",
    }
    
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#2b2b2b")
        
        self._state = PlaybackState.READY
        
        # Status dot
        self._dot_canvas = tk.Canvas(
            self, 
            width=16, 
            height=16, 
            bg="#2b2b2b", 
            highlightthickness=0
        )
        self._dot_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self._dot = self._dot_canvas.create_oval(2, 2, 14, 14, fill="#4CAF50")
        
        # Status text
        self._label = tk.Label(
            self,
            text="Ready",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#2b2b2b"
        )
        self._label.pack(side=tk.LEFT)
    
    def set_state(self, state: PlaybackState) -> None:
        """Update the displayed state."""
        self._state = state
        color = self.STATE_COLORS.get(state, "#808080")
        text = self.STATE_TEXT.get(state, "Unknown")
        
        self._dot_canvas.itemconfig(self._dot, fill=color)
        self._label.config(text=text)
    
    @property
    def state(self) -> PlaybackState:
        """Get the current state."""
        return self._state
