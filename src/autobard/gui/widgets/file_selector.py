"""File selector widget for MIDI and Sky sheet files."""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Callable, Optional


class FileSelector(tk.Frame):
    """Widget for selecting and displaying music files (MIDI or Sky sheets)."""
    
    def __init__(
        self, 
        parent: tk.Widget,
        on_file_selected: Optional[Callable[[Path], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.configure(bg="#2b2b2b")
        
        self._on_file_selected = on_file_selected
        self._current_file: Optional[Path] = None
        
        # File name display
        self._file_label = tk.Label(
            self,
            text="No file loaded",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#2b2b2b",
            anchor=tk.W
        )
        self._file_label.pack(fill=tk.X, pady=(0, 4))
        
        # Browse button
        self._browse_btn = tk.Button(
            self,
            text="Browse...",
            font=("Segoe UI", 9),
            command=self._browse_file,
            bg="#404040",
            fg="#ffffff",
            activebackground="#505050",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self._browse_btn.pack(fill=tk.X)
    
    def _browse_file(self) -> None:
        """Open file dialog to select a music file."""
        file_path = filedialog.askopenfilename(
            title="Select Music File",
            filetypes=[
                ("All supported", "*.mid *.midi *.json *.skysheet *.txt"),
                ("MIDI files", "*.mid *.midi"),
                ("Sky sheets", "*.json *.skysheet *.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.set_file(Path(file_path))
    
    def set_file(self, path: Path) -> None:
        """Set the selected file and update display."""
        self._current_file = path
        
        # Truncate long filenames
        name = path.name
        if len(name) > 30:
            name = name[:27] + "..."
        
        self._file_label.config(text=name, fg="#ffffff")
        
        if self._on_file_selected:
            self._on_file_selected(path)
    
    def clear(self) -> None:
        """Clear the selected file."""
        self._current_file = None
        self._file_label.config(text="No file loaded", fg="#888888")
    
    @property
    def current_file(self) -> Optional[Path]:
        """Get the currently selected file."""
        return self._current_file
