"""Global hotkey listener service - uses keyboard library for game compatibility."""

import logging
from typing import Callable, Dict, Optional, List

logger = logging.getLogger(__name__)


class HotkeyService:
    """Service for listening to global hotkeys.
    
    Uses the 'keyboard' library which hooks at a lower level than pynput,
    making it work even when games are in focus.
    """
    
    def __init__(self):
        self._hotkeys: Dict[str, Callable[[], None]] = {}
        self._registered_hooks: List = []
        self._running = False
        self._keyboard = None
    
    def register_hotkey(self, key: str, callback: Callable[[], None]) -> None:
        """Register a callback for a hotkey.
        
        Args:
            key: Key name (e.g., 'f10', 'f12', 'escape')
            callback: Function to call when the key is pressed
        """
        self._hotkeys[key.lower()] = callback
        logger.debug(f"Registered hotkey: {key}")
    
    def unregister_hotkey(self, key: str) -> None:
        """Remove a registered hotkey."""
        key_lower = key.lower()
        if key_lower in self._hotkeys:
            del self._hotkeys[key_lower]
            logger.debug(f"Unregistered hotkey: {key}")
    
    def start_listening(self) -> None:
        """Start the global hotkey listener."""
        if self._running:
            logger.warning("Hotkey listener already running")
            return
        
        try:
            import keyboard
            self._keyboard = keyboard
        except ImportError as e:
            logger.error("keyboard library not installed")
            raise RuntimeError("keyboard library required for hotkey listening") from e
        
        # Register hotkeys with the keyboard library
        for key, callback in self._hotkeys.items():
            try:
                # Use suppress=True to prevent the key from being passed to the game
                # when we handle it (optional - remove if you want game to also see it)
                hook = self._keyboard.on_press_key(key, lambda e, cb=callback: cb(), suppress=False)
                self._registered_hooks.append(hook)
                logger.debug(f"Hooked hotkey: {key}")
            except Exception as e:
                logger.error(f"Failed to hook {key}: {e}")
        
        self._running = True
        logger.info(f"Hotkey listener started with {len(self._registered_hooks)} hotkeys")
    
    def stop_listening(self) -> None:
        """Stop the global hotkey listener."""
        if not self._running:
            return
        
        if self._keyboard:
            # Unhook all registered hotkeys
            for hook in self._registered_hooks:
                try:
                    self._keyboard.unhook(hook)
                except Exception as e:
                    logger.warning(f"Failed to unhook: {e}")
            self._registered_hooks.clear()
        
        self._running = False
        logger.info("Hotkey listener stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if the listener is active."""
        return self._running
    
    @property
    def registered_hotkeys(self) -> list[str]:
        """Get list of registered hotkey names."""
        return list(self._hotkeys.keys())
