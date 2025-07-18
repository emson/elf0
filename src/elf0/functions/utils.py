# src/elf/functions/utils.py
"""Utility functions for Elf workflows."""

import sys
import time

from rich.console import Console

from elf0.core.compiler import WorkflowState

# Exit command constants
EXIT_COMMANDS = {"/exit", "/quit", "/bye"}

def _is_exit_command(response: str) -> bool:
    """Check if response is an exit command."""
    return response.strip().lower() in EXIT_COMMANDS

def _show_exit_feedback() -> None:
    """Show exit processing feedback with appropriate indicators."""
    console = Console(stderr=True)

    if sys.stderr.isatty():
        # Rich terminal - use spinner for exit processing
        with console.status("[dim]🚪 Processing exit request...[/dim]", spinner="dots"):
            time.sleep(0.4)
        console.print("[dim red]✗[/dim red] [dim]Exiting workflow...[/dim]")
    else:
        # Non-terminal - simple text indicators
        console.print("[dim]🚪 Processing exit request...[/dim]")
        console.print("[dim]✗ Exiting workflow...[/dim]")

def _show_processing_feedback() -> None:
    """Show normal input processing feedback."""
    console = Console(stderr=True)

    if sys.stderr.isatty():
        # Rich terminal - use professional spinner with checkmark
        with console.status("[dim]🤔 Processing your input...[/dim]", spinner="dots"):
            time.sleep(0.6)
        console.print("[dim green]✓[/dim green] [dim]Input received, continuing workflow...[/dim]")
    else:
        # Non-terminal - simple text indicator
        console.print("[dim]🤔 Processing your input...[/dim]")
        console.print("[dim]✓ Input received, continuing workflow...[/dim]")

def _create_exit_state(state: WorkflowState, user_response: str) -> WorkflowState:
    """Create workflow state for exit request."""
    return {
        **state,
        "user_input": user_response,
        "output": f"User requested to exit: {user_response}",
        "user_exit_requested": True
    }

# Legacy functions removed - now using unified input_collector module

def get_user_input(state: WorkflowState, prompt: str = "Please provide input:") -> WorkflowState:
    """Function that requests user input via CLI with multi-line support.

    Features:
    - Multi-line input support (when in terminal)
    - Double-enter or '/send' to submit
    - Exit commands ('/exit', '/quit', '/bye')
    - History and navigation support (when in terminal)
    - Professional processing indicators

    Args:
        state: Current workflow state
        prompt: Question or prompt to display to user

    Returns:
        Updated workflow state with user response
    """
    from elf0.core.input_collector import get_workflow_input
    return get_workflow_input(state, prompt)

def text_processor(state: WorkflowState, operation: str = "count_words") -> WorkflowState:
    """Process text from workflow state.

    Args:
        state: Current workflow state
        operation: Processing operation to perform

    Returns:
        Updated workflow state with processed results
    """
    # Use output if available, otherwise fall back to input
    text = state.get("output") or state.get("input", "")

    if operation == "count_words":
        word_count = len(text.split()) if text else 0
        return {
            **state,
            "output": f"Word count: {word_count}",
            "word_count": word_count,
            "processed_text": text
        }
    if operation == "uppercase":
        transformed = text.upper()
        return {
            **state,
            "output": transformed,
            "transformation": "uppercase"
        }
    if operation == "length":
        char_count = len(text)
        return {
            **state,
            "output": f"Character count: {char_count}",
            "character_count": char_count,
            "processed_text": text
        }
    return {
        **state,
        "output": f"Unknown operation: {operation}",
        "error_context": f"Unsupported operation: {operation}"
    }
