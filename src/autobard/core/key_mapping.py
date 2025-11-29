"""Key mapping logic for converting game notes to keyboard presses.

This module is pure Python with no external dependencies.
"""

from ..models.enums import Pitch, NoteName, Accidental
from ..models.mapping_table import (
    NATURAL_KEYS,
    SHARP_KEYS,
    FLAT_KEYS,
    SHARPS_SUPPORTED,
    FLATS_SUPPORTED,
)
from ..models.note import KeyPress, GameNote


class KeyMapper:
    """Maps game notes to keyboard presses.
    
    Handles natural notes, sharps (Shift modifier), flats (Ctrl modifier),
    and fallback logic for unsupported accidentals.
    """
    
    def get_key_press(self, game_note: GameNote) -> KeyPress:
        """Convert a GameNote to a KeyPress.
        
        Args:
            game_note: The game note to convert
            
        Returns:
            KeyPress with the appropriate key and modifiers
        """
        if game_note.accidental == Accidental.SHARP:
            return self._get_sharp_key(game_note.pitch, game_note.name)
        elif game_note.accidental == Accidental.FLAT:
            return self._get_flat_key(game_note.pitch, game_note.name)
        return self._get_natural_key(game_note.pitch, game_note.name)
    
    def _get_natural_key(self, pitch: Pitch, name: NoteName) -> KeyPress:
        """Get key press for a natural note."""
        key = NATURAL_KEYS[pitch][name]
        return KeyPress(key=key)
    
    def _get_sharp_key(self, pitch: Pitch, name: NoteName) -> KeyPress:
        """Get key press for a sharp note.
        
        Falls back to natural if sharp not supported for this note.
        Only Do#, Fa#, Sol# are supported in the game.
        """
        if name not in SHARPS_SUPPORTED:
            # Fallback: unsupported sharp plays as natural
            return self._get_natural_key(pitch, name)
        key = SHARP_KEYS[pitch][name]
        return KeyPress(key=key, modifiers=("shift",))
    
    def _get_flat_key(self, pitch: Pitch, name: NoteName) -> KeyPress:
        """Get key press for a flat note.
        
        Falls back to natural if flat not supported for this note.
        Only Mib, Tib are supported in the game.
        """
        if name not in FLATS_SUPPORTED:
            # Fallback: unsupported flat plays as natural
            return self._get_natural_key(pitch, name)
        key = FLAT_KEYS[pitch][name]
        return KeyPress(key=key, modifiers=("ctrl",))
    
    def is_accidental_supported(self, name: NoteName, accidental: Accidental) -> bool:
        """Check if an accidental is supported for a given note name.
        
        Args:
            name: The note name (DO through TI)
            accidental: The accidental type
            
        Returns:
            True if the accidental is natively supported, False if it will fallback
        """
        if accidental == Accidental.NATURAL:
            return True
        elif accidental == Accidental.SHARP:
            return name in SHARPS_SUPPORTED
        elif accidental == Accidental.FLAT:
            return name in FLATS_SUPPORTED
        return False
