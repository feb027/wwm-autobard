"""High-performance keyboard input using direct Win32 SendInput API."""

import ctypes
import time
import logging
from typing import Set, List
from ctypes import wintypes

from ..models.note import KeyPress

logger = logging.getLogger(__name__)

# Win32 constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Virtual key codes
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt

# Scan codes for common keys
SCAN_CODES = {
    'q': 0x10, 'w': 0x11, 'e': 0x12, 'r': 0x13, 't': 0x14,
    'y': 0x15, 'u': 0x16, 'i': 0x17, 'o': 0x18, 'p': 0x19,
    'a': 0x1E, 's': 0x1F, 'd': 0x20, 'f': 0x21, 'g': 0x22,
    'h': 0x23, 'j': 0x24, 'k': 0x25, 'l': 0x26,
    'z': 0x2C, 'x': 0x2D, 'c': 0x2E, 'v': 0x2F, 'b': 0x30,
    'n': 0x31, 'm': 0x32,
    '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05, '5': 0x06,
    '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A, '0': 0x0B,
    'shift': 0x2A, 'ctrl': 0x1D, 'alt': 0x38,
    'space': 0x39, 'enter': 0x1C, 'esc': 0x01,
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]


class HighPerfInputService:
    """High-performance keyboard input using direct Win32 SendInput.
    
    ~1ms latency vs ~5ms with keyboard library.
    Uses scan codes for game compatibility.
    """
    
    def __init__(self):
        self._held_modifiers: Set[str] = set()
        self._send_input = ctypes.windll.user32.SendInput
        self._send_input.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self._send_input.restype = wintypes.UINT
        logger.debug("High-performance input service initialized")
    
    def _make_input(self, scan_code: int, key_up: bool = False) -> INPUT:
        """Create an INPUT structure for SendInput."""
        flags = KEYEVENTF_SCANCODE
        if key_up:
            flags |= KEYEVENTF_KEYUP
        
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = 0
        inp.ki.wScan = scan_code
        inp.ki.dwFlags = flags
        inp.ki.time = 0
        inp.ki.dwExtraInfo = None
        return inp
    
    def _get_scan_code(self, key: str) -> int:
        """Get scan code for a key."""
        return SCAN_CODES.get(key.lower(), 0)
    
    def press(self, key_press: KeyPress, delay_ms: int = 0) -> None:
        """Execute a key press with optional modifiers."""
        inputs = []
        
        # Press modifiers
        for mod in key_press.modifiers:
            scan = self._get_scan_code(mod)
            if scan:
                inputs.append(self._make_input(scan, key_up=False))
        
        # Press main key
        main_scan = self._get_scan_code(key_press.key)
        if main_scan:
            inputs.append(self._make_input(main_scan, key_up=False))
        
        # Release main key
        if main_scan:
            inputs.append(self._make_input(main_scan, key_up=True))
        
        # Release modifiers (reverse order)
        for mod in reversed(key_press.modifiers):
            scan = self._get_scan_code(mod)
            if scan:
                inputs.append(self._make_input(scan, key_up=True))
        
        # Send all inputs at once
        if inputs:
            arr = (INPUT * len(inputs))(*inputs)
            self._send_input(len(inputs), arr, ctypes.sizeof(INPUT))
        
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
    
    def press_multiple(self, key_presses: List[KeyPress], delay_ms: int = 0, strum_ms: int = 0) -> None:
        """Press multiple keys for chords with optional strum effect."""
        if not key_presses:
            return
        
        # Collect all modifiers
        all_modifiers = set()
        for kp in key_presses:
            all_modifiers.update(kp.modifiers)
        
        inputs = []
        
        # Press all modifiers first
        for mod in all_modifiers:
            scan = self._get_scan_code(mod)
            if scan:
                inputs.append(self._make_input(scan, key_up=False))
        
        if inputs:
            arr = (INPUT * len(inputs))(*inputs)
            self._send_input(len(inputs), arr, ctypes.sizeof(INPUT))
            inputs = []
        
        # Press keys with optional strum
        strum_delay = strum_ms / 1000.0
        for i, kp in enumerate(key_presses):
            scan = self._get_scan_code(kp.key)
            if scan:
                inp = self._make_input(scan, key_up=False)
                self._send_input(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            
            if strum_ms > 0 and i < len(key_presses) - 1:
                time.sleep(strum_delay)
        
        time.sleep(0.015)  # Brief hold
        
        # Release all keys
        for kp in key_presses:
            scan = self._get_scan_code(kp.key)
            if scan:
                inp = self._make_input(scan, key_up=True)
                self._send_input(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        
        # Release modifiers
        for mod in all_modifiers:
            scan = self._get_scan_code(mod)
            if scan:
                inp = self._make_input(scan, key_up=True)
                self._send_input(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
    
    def release_all(self) -> None:
        """Release all potentially held keys."""
        logger.info("Releasing all held keys")
        for key in list(SCAN_CODES.keys()):
            scan = SCAN_CODES[key]
            inp = self._make_input(scan, key_up=True)
            self._send_input(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
