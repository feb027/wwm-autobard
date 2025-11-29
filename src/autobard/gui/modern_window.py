"""Modern UI using CustomTkinter for WWM Auto-Bard."""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import TYPE_CHECKING, Optional
import logging

from ..models import PlaybackState
from ..config import APP_NAME, APP_VERSION

if TYPE_CHECKING:
    from ..app import AutoBardApp

logger = logging.getLogger(__name__)

# Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModernWindow:
    """Modern UI window using CustomTkinter."""
    
    def __init__(self, root: ctk.CTk, app: "AutoBardApp"):
        self._root = root
        self._app = app
        self._current_file: Optional[Path] = None
        
        self._setup_window()
        self._create_ui()
        self._bind_keys()
        
        # Observers
        app.on_state_change(self._on_state_change)
        app.on_progress(self._on_progress)
        app.on_time_update(self._on_time_update)
        app.on_countdown(self._on_countdown)
    
    def _setup_window(self) -> None:
        self._root.title(APP_NAME)
        
        # Set window icon
        self._set_icon()
        
        cfg = self._app.config
        w, h = cfg.window_width, cfg.window_height
        
        if cfg.window_x >= 0:
            self._root.geometry(f"{w}x{h}+{cfg.window_x}+{cfg.window_y}")
        else:
            x = (self._root.winfo_screenwidth() - w) // 2
            y = (self._root.winfo_screenheight() - h) // 2
            self._root.geometry(f"{w}x{h}+{x}+{y}")
        
        self._root.minsize(400, 600)
        
        if cfg.window_always_on_top:
            self._root.attributes('-topmost', True)
        
        self._root.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _set_icon(self) -> None:
        """Set the window and taskbar icon."""
        import sys
        from pathlib import Path
        
        # Find icon path (works for both dev and exe)
        if getattr(sys, 'frozen', False):
            # Running as exe
            base = Path(sys._MEIPASS)
        else:
            # Running as script
            base = Path(__file__).parent.parent.parent.parent
        
        icon_path = base / 'resources' / 'icon.ico'
        
        if icon_path.exists():
            try:
                self._root.iconbitmap(str(icon_path))
            except Exception as e:
                logger.warning(f"Could not set icon: {e}")
    
    def _create_ui(self) -> None:
        # Main container with tabs
        self._tabview = ctk.CTkTabview(self._root, corner_radius=10)
        self._tabview.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Create tabs
        self._tabview.add("Player")
        self._tabview.add("Library")
        self._tabview.add("Settings")
        
        self._create_player_tab()
        self._create_library_tab()
        self._create_settings_tab()
    
    def _create_player_tab(self) -> None:
        tab = self._tabview.tab("Player")
        
        # === NOW PLAYING CARD ===
        card = ctk.CTkFrame(tab, corner_radius=15)
        card.pack(fill='x', pady=(0, 15))
        
        # Status row
        status_frame = ctk.CTkFrame(card, fg_color="transparent")
        status_frame.pack(fill='x', padx=20, pady=(15, 5))
        
        self._status_label = ctk.CTkLabel(status_frame, text="● Ready",
                                         font=ctk.CTkFont(size=13, weight="bold"),
                                         text_color="#888888")
        self._status_label.pack(side='left')
        
        self._loop_label = ctk.CTkLabel(status_frame, text="",
                                       font=ctk.CTkFont(size=12),
                                       text_color="#f0ad4e")
        self._loop_label.pack(side='right')
        
        # Song title
        self._song_title = ctk.CTkLabel(card, text="No song loaded",
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       wraplength=350)
        self._song_title.pack(padx=20, pady=(5, 0))
        
        # Song info
        self._song_info = ctk.CTkLabel(card, text="Open a MIDI or Sky sheet file",
                                      font=ctk.CTkFont(size=12),
                                      text_color="#888888")
        self._song_info.pack(padx=20, pady=(0, 15))
        
        # Countdown overlay
        self._countdown_label = ctk.CTkLabel(card, text="",
                                            font=ctk.CTkFont(size=64, weight="bold"),
                                            text_color="#3b8ed0")
        
        # === PROGRESS BAR ===
        progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self._time_current = ctk.CTkLabel(progress_frame, text="0:00",
                                         font=ctk.CTkFont(size=11),
                                         text_color="#888888", width=45)
        self._time_current.pack(side='left')
        
        self._progress_bar = ctk.CTkProgressBar(progress_frame, height=8,
                                               corner_radius=4)
        self._progress_bar.pack(side='left', fill='x', expand=True, padx=10)
        self._progress_bar.set(0)
        self._progress_bar.bind('<Button-1>', self._on_progress_click)
        
        self._time_total = ctk.CTkLabel(progress_frame, text="0:00",
                                       font=ctk.CTkFont(size=11),
                                       text_color="#888888", width=45)
        self._time_total.pack(side='right')
        
        # === MAIN CONTROLS ===
        # Big play button centered
        self._play_btn = ctk.CTkButton(tab, text="▶", width=90, height=90,
                                      font=ctk.CTkFont(size=36),
                                      corner_radius=45,
                                      command=self._toggle_play)
        self._play_btn.pack(pady=(15, 10))
        
        # Secondary controls row below
        controls = ctk.CTkFrame(tab, fg_color="transparent")
        controls.pack()
        
        self._restart_btn = ctk.CTkButton(controls, text="⏮ Restart", width=90, height=36,
                                         font=ctk.CTkFont(size=12),
                                         fg_color="#2b2b2b", hover_color="#3b3b3b",
                                         command=self._restart)
        self._restart_btn.grid(row=0, column=0, padx=4)
        
        self._stop_btn = ctk.CTkButton(controls, text="⏹ Stop", width=90, height=36,
                                      font=ctk.CTkFont(size=12),
                                      fg_color="#2b2b2b", hover_color="#3b3b3b",
                                      command=self._app.stop)
        self._stop_btn.grid(row=0, column=1, padx=4)
        
        self._loop_btn = ctk.CTkButton(controls, text="🔁 Loop", width=90, height=36,
                                      font=ctk.CTkFont(size=12),
                                      fg_color="#2b2b2b", hover_color="#3b3b3b",
                                      command=self._toggle_loop)
        self._loop_btn.grid(row=0, column=2, padx=4)
        
        # === SPEED SLIDER ===
        speed_frame = ctk.CTkFrame(tab, fg_color="transparent")
        speed_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(speed_frame, text="Speed", font=ctk.CTkFont(size=12),
                    text_color="#888888").pack(side='left')
        
        self._speed_label = ctk.CTkLabel(speed_frame, text="100%",
                                        font=ctk.CTkFont(size=12, weight="bold"),
                                        width=50)
        self._speed_label.pack(side='right')
        
        self._speed_slider = ctk.CTkSlider(speed_frame, from_=25, to=200,
                                          number_of_steps=35,
                                          command=self._on_speed_change)
        self._speed_slider.set(100)
        self._speed_slider.pack(side='left', fill='x', expand=True, padx=15)
        
        # === TRACK SELECTOR ===
        self._track_frame = ctk.CTkFrame(tab, fg_color="transparent")
        
        ctk.CTkLabel(self._track_frame, text="Track:",
                    font=ctk.CTkFont(size=12)).pack(side='left')
        
        self._track_var = ctk.StringVar(value="All tracks")
        self._track_menu = ctk.CTkOptionMenu(self._track_frame,
                                            variable=self._track_var,
                                            values=["All tracks"],
                                            command=self._on_track_change,
                                            width=250)
        self._track_menu.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        # === OPEN FILE BUTTON ===
        self._open_btn = ctk.CTkButton(tab, text="📁  Open File", height=45,
                                      font=ctk.CTkFont(size=14),
                                      command=self._open_file)
        self._open_btn.pack(fill='x', pady=(15, 0))
        
        # === SHORTCUTS HINT ===
        ctk.CTkLabel(tab, text="F10: Play/Pause  •  F12: Stop  •  Home: Restart",
                    font=ctk.CTkFont(size=11), text_color="#666666"
                    ).pack(side='bottom', pady=(10, 0))
    
    def _create_library_tab(self) -> None:
        tab = self._tabview.tab("Library")
        
        # Header
        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(header, text="Recent Files",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side='left')
        
        ctk.CTkButton(header, text="Clear", width=60, height=28,
                     fg_color="transparent", hover_color="#3b3b3b",
                     text_color="#888888", command=self._clear_recent
                     ).pack(side='right')
        
        # File list with scrolling
        self._file_scroll = ctk.CTkScrollableFrame(tab, corner_radius=10)
        self._file_scroll.pack(fill='both', expand=True)
        
        self._file_buttons: list[ctk.CTkButton] = []
        self._update_library()
        
        # Add files button
        ctk.CTkButton(tab, text="+ Add Files", height=40,
                     fg_color="#2b2b2b", hover_color="#3b3b3b",
                     command=self._add_files).pack(fill='x', pady=(10, 0))
    
    def _create_settings_tab(self) -> None:
        tab = self._tabview.tab("Settings")
        
        # Scrollable settings
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill='both', expand=True)
        
        # === PLAYBACK SETTINGS ===
        self._create_section(scroll, "Playback")
        
        # Countdown
        countdown_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        countdown_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(countdown_frame, text="Countdown (seconds)",
                    font=ctk.CTkFont(size=13)).pack(side='left')
        
        self._countdown_var = ctk.StringVar(value=str(self._app.config.countdown_seconds))
        countdown_menu = ctk.CTkOptionMenu(countdown_frame, variable=self._countdown_var,
                                          values=["0", "1", "2", "3", "4", "5"],
                                          width=80, command=self._save_countdown)
        countdown_menu.pack(side='right')
        
        # Min note delay
        delay_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        delay_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(delay_frame, text="Min note delay (ms)",
                    font=ctk.CTkFont(size=13)).pack(side='left')
        
        self._delay_var = ctk.StringVar(value=str(self._app.config.min_note_delay_ms))
        delay_entry = ctk.CTkEntry(delay_frame, textvariable=self._delay_var,
                                  width=80, justify='center')
        delay_entry.pack(side='right')
        delay_entry.bind('<FocusOut>', self._save_delay)
        
        # Humanize
        humanize_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        humanize_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(humanize_frame, text="Humanize timing (ms)",
                    font=ctk.CTkFont(size=13)).pack(side='left')
        
        self._humanize_var = ctk.StringVar(value=str(self._app.config.humanize_ms))
        humanize_entry = ctk.CTkEntry(humanize_frame, textvariable=self._humanize_var,
                                     width=80, justify='center')
        humanize_entry.pack(side='right')
        humanize_entry.bind('<FocusOut>', self._save_humanize)
        
        # Chord strum
        strum_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        strum_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(strum_frame, text="Chord strum (ms)",
                    font=ctk.CTkFont(size=13)).pack(side='left')
        
        self._strum_var = ctk.StringVar(value=str(self._app.config.chord_strum_ms))
        strum_entry = ctk.CTkEntry(strum_frame, textvariable=self._strum_var,
                                  width=80, justify='center')
        strum_entry.pack(side='right')
        strum_entry.bind('<FocusOut>', self._save_strum)
        
        # === WINDOW SETTINGS ===
        self._create_section(scroll, "Window")
        
        # Always on top
        top_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        top_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(top_frame, text="Always on top",
                    font=ctk.CTkFont(size=13)).pack(side='left')
        
        self._topmost_var = ctk.BooleanVar(value=self._app.config.window_always_on_top)
        topmost_switch = ctk.CTkSwitch(top_frame, text="",
                                      variable=self._topmost_var,
                                      command=self._save_topmost)
        topmost_switch.pack(side='right')
        
        # === HOTKEYS ===
        self._create_section(scroll, "Hotkeys")
        
        hotkey_info = ctk.CTkLabel(scroll, 
                                  text="F10 - Play/Pause (works in game)\n"
                                       "F12 - Stop playback\n"
                                       "Space - Play/Pause (app focused)\n"
                                       "Home - Restart song\n"
                                       "Escape - Stop",
                                  font=ctk.CTkFont(size=12),
                                  text_color="#888888",
                                  justify='left')
        hotkey_info.pack(anchor='w', pady=5)
        
        # === ABOUT ===
        self._create_section(scroll, "About")
        
        ctk.CTkLabel(scroll, text=f"{APP_NAME} v{APP_VERSION}",
                    font=ctk.CTkFont(size=13, weight="bold")).pack(anchor='w')
        ctk.CTkLabel(scroll, text="MIDI & Sky sheet to keyboard macro player\nfor Where Winds Meet",
                    font=ctk.CTkFont(size=12), text_color="#888888",
                    justify='left').pack(anchor='w', pady=(2, 0))
    
    def _create_section(self, parent, title: str) -> None:
        """Create a section header."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=(20, 10))
        
        ctk.CTkLabel(frame, text=title,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#3b8ed0").pack(side='left')
        
        # Separator line
        sep = ctk.CTkFrame(frame, height=1, fg_color="#3b3b3b")
        sep.pack(side='left', fill='x', expand=True, padx=(15, 0))
    
    def _bind_keys(self) -> None:
        self._root.bind('<F10>', lambda e: self._toggle_play())
        self._root.bind('<F12>', lambda e: self._app.stop())
        self._root.bind('<Escape>', lambda e: self._app.stop())
        self._root.bind('<space>', lambda e: self._toggle_play())
        self._root.bind('<Home>', lambda e: self._restart())
    
    # === PLAYER ACTIONS ===
    
    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open Music File",
            filetypes=[
                ("All supported", "*.mid *.midi *.json *.skysheet *.txt"),
                ("MIDI", "*.mid *.midi"),
                ("Sky sheets", "*.json *.skysheet *.txt"),
            ]
        )
        if path:
            self._load_file(Path(path))
    
    def _load_file(self, path: Path) -> None:
        if self._app.load_midi(path):
            self._current_file = path
            self._app.config.add_recent_file(str(path))
            self._app.config.save()
            
            # Update UI
            name = path.stem
            if len(name) > 35:
                name = name[:32] + "..."
            self._song_title.configure(text=name)
            
            notes = self._app.total_notes
            duration = self._app.song_duration
            self._song_info.configure(text=f"{notes} notes  •  {self._fmt_time(duration)}")
            self._time_total.configure(text=self._fmt_time(duration))
            self._time_current.configure(text="0:00")
            self._progress_bar.set(0)
            
            self._status_label.configure(text="● Ready", text_color="#888888")
            
            # Track selector
            tracks = self._app.get_track_info()
            if tracks and len(tracks) > 1:
                values = ["All tracks"]
                for t in tracks:
                    if t['note_count'] > 0:
                        values.append(f"Track {t['index']}: {t['name']} ({t['note_count']} notes)")
                self._track_menu.configure(values=values)
                self._track_var.set("All tracks")
                self._track_frame.pack(fill='x', pady=10, before=self._open_btn)
            else:
                self._track_frame.pack_forget()
            
            self._update_library()
    
    def _toggle_play(self) -> None:
        if self._app.state == PlaybackState.PLAYING:
            self._app.pause()
        else:
            self._app.start()
    
    def _restart(self) -> None:
        self._app.stop()
        self._app.seek(0)
        self._progress_bar.set(0)
        self._time_current.configure(text="0:00")
    
    def _toggle_loop(self) -> None:
        enabled = self._app.toggle_loop()
        if enabled:
            self._loop_btn.configure(fg_color="#3b8ed0")
            self._loop_label.configure(text="🔁 Loop ON")
        else:
            self._loop_btn.configure(fg_color="#2b2b2b")
            self._loop_label.configure(text="")
    
    def _on_speed_change(self, value: float) -> None:
        speed = value / 100
        self._app.set_playback_speed(speed)
        self._speed_label.configure(text=f"{int(value)}%")
    
    def _on_progress_click(self, event) -> None:
        width = self._progress_bar.winfo_width()
        if width > 0:
            percent = event.x / width
            self._app.seek_percent(percent)
            self._progress_bar.set(percent)
    
    def _on_track_change(self, choice: str) -> None:
        if choice == "All tracks":
            self._app.reload_track(None)
        else:
            # Extract track index
            try:
                idx = int(choice.split(":")[0].replace("Track ", ""))
                self._app.reload_track(idx)
            except:
                pass
        
        self._song_info.configure(
            text=f"{self._app.total_notes} notes  •  {self._fmt_time(self._app.song_duration)}"
        )
    
    # === LIBRARY ACTIONS ===
    
    def _update_library(self) -> None:
        # Clear existing buttons
        for btn in self._file_buttons:
            btn.destroy()
        self._file_buttons.clear()
        
        # Add file buttons
        for i, filepath in enumerate(self._app.config.recent_files[:15]):
            path = Path(filepath)
            name = path.stem
            if len(name) > 40:
                name = name[:37] + "..."
            
            btn = ctk.CTkButton(self._file_scroll, text=f"🎵  {name}",
                               anchor='w', height=40,
                               fg_color="transparent", hover_color="#2b2b2b",
                               font=ctk.CTkFont(size=13),
                               command=lambda p=path: self._on_file_click(p))
            btn.pack(fill='x', pady=2)
            self._file_buttons.append(btn)
        
        if not self._file_buttons:
            label = ctk.CTkLabel(self._file_scroll, text="No recent files",
                                text_color="#666666")
            label.pack(pady=20)
    
    def _on_file_click(self, path: Path) -> None:
        if path.exists():
            self._load_file(path)
            self._tabview.set("Player")
        else:
            messagebox.showwarning("File Not Found", f"File no longer exists:\n{path.name}")
    
    def _clear_recent(self) -> None:
        self._app.config.recent_files = []
        self._app.config.save()
        self._update_library()
    
    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Add Files to Library",
            filetypes=[
                ("All supported", "*.mid *.midi *.json *.skysheet *.txt"),
                ("MIDI", "*.mid *.midi"),
                ("Sky sheets", "*.json *.skysheet *.txt"),
            ]
        )
        for path in paths:
            self._app.config.add_recent_file(path)
        self._app.config.save()
        self._update_library()
    
    # === SETTINGS ACTIONS ===
    
    def _save_countdown(self, value: str) -> None:
        self._app.config.countdown_seconds = int(value)
        self._app.config.save()
    
    def _save_delay(self, event=None) -> None:
        try:
            self._app.config.min_note_delay_ms = int(self._delay_var.get())
            self._app.config.save()
        except ValueError:
            pass
    
    def _save_humanize(self, event=None) -> None:
        try:
            self._app.config.humanize_ms = int(self._humanize_var.get())
            self._app.config.save()
        except ValueError:
            pass
    
    def _save_strum(self, event=None) -> None:
        try:
            self._app.config.chord_strum_ms = int(self._strum_var.get())
            self._app.config.save()
        except ValueError:
            pass
    
    def _save_topmost(self) -> None:
        value = self._topmost_var.get()
        self._app.config.window_always_on_top = value
        self._app.config.save()
        self._root.attributes('-topmost', value)
    
    # === OBSERVERS ===
    
    def _on_state_change(self, state: PlaybackState) -> None:
        states = {
            PlaybackState.READY: ("● Ready", "#888888", "▶"),
            PlaybackState.PLAYING: ("● Playing", "#4ecca3", "⏸"),
            PlaybackState.PAUSED: ("● Paused", "#f0ad4e", "▶"),
            PlaybackState.STOPPED: ("● Stopped", "#888888", "▶"),
        }
        
        text, color, btn = states.get(state, ("● Ready", "#888888", "▶"))
        self._status_label.configure(text=text, text_color=color)
        self._play_btn.configure(text=btn)
        
        if state == PlaybackState.STOPPED:
            self._progress_bar.set(0)
            self._time_current.configure(text="0:00")
    
    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress_bar.set(current / total)
    
    def _on_time_update(self, current: float, total: float) -> None:
        self._time_current.configure(text=self._fmt_time(current))
    
    def _on_countdown(self, seconds: int) -> None:
        if seconds > 0:
            self._countdown_label.configure(text=str(seconds))
            self._countdown_label.pack(pady=10)
        else:
            self._countdown_label.pack_forget()
    
    def _fmt_time(self, seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"
    
    def _on_close(self) -> None:
        self._app.config.window_x = self._root.winfo_x()
        self._app.config.window_y = self._root.winfo_y()
        self._app.config.window_width = self._root.winfo_width()
        self._app.config.window_height = self._root.winfo_height()
        self._app.config.save()
        self._app.shutdown()
        self._root.destroy()
    
    def run(self) -> None:
        self._root.mainloop()
