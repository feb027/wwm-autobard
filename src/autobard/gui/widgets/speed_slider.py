"""Speed/tempo slider widget."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class SpeedSlider(tk.Frame):
    """Slider for adjusting playback speed."""
    
    def __init__(
        self, 
        parent: tk.Widget, 
        on_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.configure(bg="#2b2b2b")
        
        self._on_change = on_change
        
        # Label
        self._title = tk.Label(
            self,
            text="Speed",
            font=("Segoe UI", 9),
            fg="#aaaaaa",
            bg="#2b2b2b"
        )
        self._title.pack(anchor=tk.W)
        
        # Slider frame
        slider_frame = tk.Frame(self, bg="#2b2b2b")
        slider_frame.pack(fill=tk.X, pady=(2, 0))
        
        # Value variable
        self._value = tk.DoubleVar(value=1.0)
        
        # Slider
        style = ttk.Style()
        style.configure("Custom.Horizontal.TScale", background="#2b2b2b")
        
        self._slider = ttk.Scale(
            slider_frame,
            from_=0.5,
            to=1.5,
            orient=tk.HORIZONTAL,
            variable=self._value,
            command=self._on_slider_change,
            style="Custom.Horizontal.TScale"
        )
        self._slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Value display
        self._value_label = tk.Label(
            slider_frame,
            text="100%",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg="#2b2b2b",
            width=5
        )
        self._value_label.pack(side=tk.RIGHT, padx=(8, 0))
    
    def _on_slider_change(self, value: str) -> None:
        """Handle slider value changes."""
        speed = float(value)
        percentage = int(speed * 100)
        self._value_label.config(text=f"{percentage}%")
        
        if self._on_change:
            self._on_change(speed)
    
    def get_value(self) -> float:
        """Get the current speed value."""
        return self._value.get()
    
    def set_value(self, speed: float) -> None:
        """Set the speed value."""
        self._value.set(speed)
        percentage = int(speed * 100)
        self._value_label.config(text=f"{percentage}%")
