"""Track selector widget for choosing MIDI tracks."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TrackSelector(ttk.Frame):
    """Dropdown widget for selecting MIDI track to play."""
    
    def __init__(self, parent, on_track_change: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        self._on_track_change = on_track_change
        self._tracks: List[Dict] = []
        
        # Label
        self._label = ttk.Label(self, text="Track:")
        self._label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Dropdown
        self._var = tk.StringVar(value="All tracks")
        self._combo = ttk.Combobox(
            self, 
            textvariable=self._var,
            state="readonly",
            width=25
        )
        self._combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._combo.bind("<<ComboboxSelected>>", self._on_select)
        
        # Set initial state
        self._combo['values'] = ["All tracks (merged)"]
        self._combo.current(0)
    
    def set_tracks(self, tracks: List[Dict]) -> None:
        """Update the track list.
        
        Args:
            tracks: List of track info dicts with 'index', 'name', 'note_count' keys
        """
        self._tracks = tracks
        
        # Build display strings
        values = ["All tracks (merged)"]
        for t in tracks:
            if t['note_count'] > 0:
                values.append(f"{t['index']}: {t['name']} ({t['note_count']} notes)")
        
        self._combo['values'] = values
        self._combo.current(0)
        logger.debug(f"Track selector updated with {len(tracks)} tracks")
    
    def _on_select(self, event) -> None:
        """Handle track selection change."""
        selection = self._combo.current()
        
        if selection == 0:
            # All tracks merged
            track_num = None
            logger.info("Selected: All tracks merged")
        else:
            # Specific track - find which one
            # We need to map back to the actual track index since we skip empty tracks
            non_empty = [t for t in self._tracks if t['note_count'] > 0]
            if selection - 1 < len(non_empty):
                track_num = non_empty[selection - 1]['index']
                logger.info(f"Selected: Track {track_num}")
            else:
                track_num = None
        
        if self._on_track_change:
            self._on_track_change(track_num)
    
    def get_selected_track(self) -> Optional[int]:
        """Get the currently selected track number, or None for all tracks."""
        selection = self._combo.current()
        if selection == 0:
            return None
        non_empty = [t for t in self._tracks if t['note_count'] > 0]
        if selection - 1 < len(non_empty):
            return non_empty[selection - 1]['index']
        return None
