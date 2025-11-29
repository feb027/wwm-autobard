"""Keyboard input simulation service - uses keyboard library for game compatibility."""

import logging
import time
from typing import Set

from ..models.note import KeyPress

logger = logging.getLogger(__name__)


class KeyboardService:
    """Service for simulating keyboard input.
    
    Uses the 'keyboard' library which sends scan codes that work with games.
    This is more compatible than pynput for DirectInput games.
    """
    
    def __init__(self):
        self._held_modifiers: Set[str] = set()
        self._initialized = False
        self._keyboard = None
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of keyboard library."""
        if self._initialized:
            return
        
        try:
            import keyboard
            self._keyboard = keyboard
            self._initialized = True
            logger.debug("Keyboard service initialized (using keyboard library)")
        except ImportError as e:
            logger.error("keyboard library not installed")
            raise RuntimeError("keyboard library required for keyboard simulation") from e
    
    def press(self, key_press: KeyPress, delay_ms: int = 0) -> None:
        """Execute a key press with optional modifiers.
        
        Args:
            key_press: KeyPress object with key and modifiers
            delay_ms: Optional delay in milliseconds after the press
        """
        self._ensure_initialized()
        
        try:
            # Press modifiers first
            for mod in key_press.modifiers:
                self._press_modifier(mod)
            
            # Small delay to ensure modifier is registered
            if key_press.modifiers:
                time.sleep(0.01)
            
            # Press and release the main key using scan codes
            self._keyboard.press(key_press.key)
            time.sleep(0.02)  # Hold key briefly
            self._keyboard.release(key_press.key)
            
            # Release modifiers
            for mod in key_press.modifiers:
                self._release_modifier(mod)
            
            # Optional delay
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
                
            logger.debug(f"Pressed: {key_press}")
            
        except Exception as e:
            logger.error(f"Failed to press {key_press}: {e}")
            self.release_all()
            raise
    
    def press_key(self, key: str) -> None:
        """Press and release a single key without modifiers."""
        self._ensure_initialized()
        self._keyboard.press(key)
        time.sleep(0.02)
        self._keyboard.release(key)
    
    def press_multiple(self, key_presses: list[KeyPress], delay_ms: int = 0, strum_ms: int = 0) -> None:
        """Press multiple keys for chords with optional strum effect.
        
        Args:
            key_presses: List of KeyPress objects to press together
            delay_ms: Optional delay after all keys are pressed
            strum_ms: Delay between each key press (strum effect, 0 = simultaneous)
        """
        self._ensure_initialized()
        
        if not key_presses:
            return
        
        try:
            # Collect all modifiers needed
            all_modifiers = set()
            for kp in key_presses:
                all_modifiers.update(kp.modifiers)
            
            # Press all modifiers first
            for mod in all_modifiers:
                self._press_modifier(mod)
            
            if all_modifiers:
                time.sleep(0.01)
            
            # Press keys with optional strum delay
            keys_pressed = []
            strum_delay = strum_ms / 1000.0
            for i, kp in enumerate(key_presses):
                self._keyboard.press(kp.key)
                keys_pressed.append(kp.key)
                # Add strum delay between notes (not after last one)
                if strum_ms > 0 and i < len(key_presses) - 1:
                    time.sleep(strum_delay)
            
            time.sleep(0.02)  # Hold briefly
            
            # Release all keys
            for key in keys_pressed:
                self._keyboard.release(key)
            
            # Release all modifiers
            for mod in all_modifiers:
                self._release_modifier(mod)
            
            # Optional delay
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            logger.debug(f"Pressed chord: {[str(kp) for kp in key_presses]}")
            
        except Exception as e:
            logger.error(f"Failed to press chord: {e}")
            self.release_all()
            raise
    
    def _press_modifier(self, modifier: str) -> None:
        """Press and hold a modifier key."""
        self._ensure_initialized()
        mod_key = self._get_modifier_key(modifier)
        if mod_key:
            self._keyboard.press(mod_key)
            self._held_modifiers.add(modifier)
    
    def _release_modifier(self, modifier: str) -> None:
        """Release a modifier key."""
        self._ensure_initialized()
        mod_key = self._get_modifier_key(modifier)
        if mod_key:
            self._keyboard.release(mod_key)
            self._held_modifiers.discard(modifier)
    
    def _get_modifier_key(self, modifier: str) -> str:
        """Convert modifier string to keyboard library key name."""
        modifier_map = {
            "shift": "shift",
            "ctrl": "ctrl", 
            "alt": "alt",
        }
        return modifier_map.get(modifier.lower(), modifier)
    
    def release_all(self) -> None:
        """Emergency release of all held keys.
        
        Call this on panic/stop to ensure no keys remain stuck.
        """
        if not self._initialized or self._keyboard is None:
            return
        
        logger.info("Releasing all held keys")
        
        # Release all tracked modifiers
        for mod in list(self._held_modifiers):
            try:
                self._release_modifier(mod)
            except Exception as e:
                logger.warning(f"Failed to release {mod}: {e}")
        
        self._held_modifiers.clear()
        
        # Also try to release common modifier keys directly
        for key in ["shift", "ctrl", "alt"]:
            try:
                self._keyboard.release(key)
            except Exception:
                pass
        
        # Release all letter keys that might be stuck
        for key in "qwertyuasdfghjzxcvbnm":
            try:
                self._keyboard.release(key)
            except Exception:
                pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if the keyboard service is ready."""
        return self._initialized
