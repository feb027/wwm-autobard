"""Sky: Children of the Light sheet music parser."""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models.note import NoteEvent, SongInfo
from ..models.enums import Pitch, NoteName
from ..core.exceptions import MidiParseError

logger = logging.getLogger(__name__)

# Sky uses a 15-key pentatonic layout per octave
# Row 1: C4 D4 E4 F4 G4 (keys 0-4)
# Row 2: A4 B4 C5 D5 E5 (keys 5-9)
# Row 3: F5 G5 A5 B5 C6 (keys 10-14)
# This maps to MIDI notes (C4 = 60)
SKY_KEY_TO_MIDI = {
    # Octave 1 (1Key0 - 1Key14)
    0: 60,   # C4
    1: 62,   # D4
    2: 64,   # E4
    3: 65,   # F4
    4: 67,   # G4
    5: 69,   # A4
    6: 71,   # B4
    7: 72,   # C5
    8: 74,   # D5
    9: 76,   # E5
    10: 77,  # F5
    11: 79,  # G5
    12: 81,  # A5
    13: 83,  # B5
    14: 84,  # C6
}

# Extended octave 2 (2Key0 - 2Key14) - same pattern, one octave higher
SKY_KEY_TO_MIDI_OCT2 = {k: v + 12 for k, v in SKY_KEY_TO_MIDI.items()}


class SkySheetService:
    """Service for loading Sky: Children of the Light sheet music.
    
    Supports .json and .skysheet.json formats from sky-music.herokuapp.com
    and related tools.
    """
    
    def __init__(self):
        self._current_file: Optional[Path] = None
        self._events: List[NoteEvent] = []
        self._song_info: Optional[SongInfo] = None
        self._raw_data: Optional[Dict[str, Any]] = None
    
    def load_file(self, path: Path) -> List[NoteEvent]:
        """Load and parse a Sky sheet JSON file.
        
        Args:
            path: Path to the .json or .skysheet.json file
            
        Returns:
            List of NoteEvent objects
        """
        if not path.exists():
            raise MidiParseError(f"File not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise MidiParseError(f"Invalid JSON: {e}") from e
        
        self._current_file = path
        self._events = []
        
        # Handle different formats
        if isinstance(data, list):
            # Check if it's a list of note objects directly (like [{time, key}, ...])
            if len(data) > 0 and isinstance(data[0], dict) and 'key' in data[0]:
                # Direct array of notes
                song_notes = data
                data = {'name': path.stem, 'bpm': 120}
            elif len(data) > 0:
                # Array wrapper around song object
                data = data[0]
                song_notes = data.get('songNotes', []) or data.get('notes', [])
            else:
                song_notes = []
        else:
            song_notes = data.get('songNotes', []) or data.get('notes', [])
        
        self._raw_data = data
        
        name = data.get('name', path.stem)
        bpm = data.get('bpm', 120)
        
        logger.info(f"Loading Sky sheet: {name} ({len(song_notes)} notes, {bpm} BPM)")
        
        # Parse notes
        self._events = self._parse_notes(song_notes)
        
        # Build song info
        if self._events:
            notes = [e.note for e in self._events if e.is_note_on]
            duration = self._events[-1].time_delta if self._events else 0
            # Calculate actual duration from time values
            total_time = sum(e.time_delta for e in self._events) / 1000.0
            
            self._song_info = SongInfo(
                filename=path.name,
                duration=total_time,
                note_count=len(self._events),
                min_note=min(notes) if notes else 0,
                max_note=max(notes) if notes else 0,
            )
        
        logger.info(f"Loaded {path.name}: {len(self._events)} events")
        return self._events
    
    def _parse_notes(self, song_notes: List) -> List[NoteEvent]:
        """Parse songNotes array into NoteEvents."""
        events = []
        last_time = 0
        
        for note in song_notes:
            # Handle different formats
            if isinstance(note, dict):
                time_ms = note.get('time', 0)
                key = note.get('key', '')
            elif isinstance(note, list) and len(note) >= 2:
                # [key_index, time_ms] format
                key = f"1Key{note[0]}"
                time_ms = note[1]
            else:
                continue
            
            # Parse key string like "1Key0" or "2Key5"
            midi_note = self._key_to_midi(key)
            if midi_note is None:
                continue
            
            # Calculate time delta from previous note
            time_delta = max(0, time_ms - last_time)
            last_time = time_ms
            
            events.append(NoteEvent(
                note=midi_note,
                velocity=100,
                time_delta=time_delta / 1000.0,  # Convert ms to seconds
                is_note_on=True,
            ))
        
        return events
    
    def _key_to_midi(self, key: str) -> Optional[int]:
        """Convert Sky key string to MIDI note number."""
        if not key or 'Key' not in key:
            return None
        
        try:
            # Parse "1Key0" or "2Key5" format
            octave = int(key[0])
            key_num = int(key.split('Key')[1])
            
            if octave == 1:
                return SKY_KEY_TO_MIDI.get(key_num)
            elif octave == 2:
                return SKY_KEY_TO_MIDI_OCT2.get(key_num)
            else:
                # Octave 3+: extrapolate
                base = SKY_KEY_TO_MIDI.get(key_num, 60)
                return base + (octave - 1) * 12
        except (ValueError, IndexError):
            return None
    
    def get_song_info(self) -> Optional[SongInfo]:
        """Get metadata about the loaded song."""
        return self._song_info
    
    def get_note_range(self) -> tuple[int, int]:
        """Get the min and max MIDI notes in the loaded song."""
        if not self._events:
            return (60, 60)
        
        notes = [e.note for e in self._events if e.is_note_on]
        if not notes:
            return (60, 60)
        
        return (min(notes), max(notes))
    
    @property
    def is_loaded(self) -> bool:
        """Check if a file is loaded."""
        return len(self._events) > 0
    
    @staticmethod
    def is_sky_sheet(path: Path) -> bool:
        """Check if a file appears to be a Sky sheet."""
        suffix = path.suffix.lower()
        name = path.name.lower()
        
        # Direct extension match
        if suffix in ('.skysheet', '.txt'):
            return True
        
        if suffix == '.json':
            # Check for skysheet naming
            if 'skysheet' in name or 'sky' in name:
                return True
            # Try to peek at content
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                    return 'songNotes' in content or ('"key"' in content and 'Key' in content)
            except:
                pass
        
        return False
