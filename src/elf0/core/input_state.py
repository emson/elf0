# src/elf0/core/input_state.py
"""Thread-safe input collection state management for CLI coordination."""

import threading

# Global state for input collection coordination
_input_lock = threading.Lock()
_collecting_input = False


def set_collecting_input() -> None:
    """Signal that user input collection has started."""
    global _collecting_input
    with _input_lock:
        _collecting_input = True


def clear_collecting_input() -> None:
    """Signal that user input collection has completed."""
    global _collecting_input
    with _input_lock:
        _collecting_input = False


def is_collecting_input() -> bool:
    """Check if user input collection is currently active."""
    with _input_lock:
        return _collecting_input