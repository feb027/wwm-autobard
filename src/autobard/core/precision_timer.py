"""High-precision timing utilities for Windows."""

import ctypes
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Windows multimedia timer API
try:
    winmm = ctypes.windll.winmm
    _timeBeginPeriod = winmm.timeBeginPeriod
    _timeEndPeriod = winmm.timeEndPeriod
    _HAS_WINMM = True
except (OSError, AttributeError):
    _HAS_WINMM = False
    logger.warning("Windows multimedia timer not available")


@contextmanager
def high_precision_mode():
    """Context manager for high-precision timer mode on Windows.
    
    Sets Windows timer resolution to 1ms (default is ~15ms).
    Use sparingly as it increases power consumption.
    """
    if _HAS_WINMM:
        _timeBeginPeriod(1)
        logger.debug("Enabled high-precision timer (1ms)")
    try:
        yield
    finally:
        if _HAS_WINMM:
            _timeEndPeriod(1)
            logger.debug("Disabled high-precision timer")


def enable_high_precision():
    """Enable high-precision timer mode."""
    if _HAS_WINMM:
        _timeBeginPeriod(1)
        logger.debug("Enabled high-precision timer (1ms)")
        return True
    return False


def disable_high_precision():
    """Disable high-precision timer mode."""
    if _HAS_WINMM:
        _timeEndPeriod(1)
        logger.debug("Disabled high-precision timer")


def precision_sleep(seconds: float) -> None:
    """High-precision sleep combining sleep and spin-wait.
    
    For durations > 2ms, uses sleep for most of it then spin-waits.
    For durations <= 2ms, uses pure spin-wait.
    """
    if seconds <= 0:
        return
    
    target = time.perf_counter() + seconds
    
    # Sleep for most of the duration (leave 1.5ms for spin)
    if seconds > 0.002:
        time.sleep(seconds - 0.0015)
    
    # Spin-wait for remaining time (most precise)
    while time.perf_counter() < target:
        pass


class PrecisionTimer:
    """High-precision timer for scheduling events."""
    
    def __init__(self):
        self._start_time = time.perf_counter()
        self._next_time = self._start_time
        self._precision_enabled = False
    
    def start(self) -> None:
        """Start/reset the timer and enable high-precision mode."""
        self._start_time = time.perf_counter()
        self._next_time = self._start_time
        if not self._precision_enabled:
            self._precision_enabled = enable_high_precision()
    
    def stop(self) -> None:
        """Stop and disable high-precision mode."""
        if self._precision_enabled:
            disable_high_precision()
            self._precision_enabled = False
    
    def wait(self, duration: float) -> None:
        """Wait for duration seconds from last wait point."""
        self._next_time += duration
        remaining = self._next_time - time.perf_counter()
        
        if remaining > 0:
            precision_sleep(remaining)
    
    def wait_until(self, target_time: float) -> None:
        """Wait until absolute time (relative to start)."""
        self._next_time = self._start_time + target_time
        remaining = self._next_time - time.perf_counter()
        
        if remaining > 0:
            precision_sleep(remaining)
    
    def reset(self) -> None:
        """Reset timing reference point."""
        self._next_time = time.perf_counter()
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time since start."""
        return time.perf_counter() - self._start_time
