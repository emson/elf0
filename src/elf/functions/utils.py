# src/elf/functions/utils.py
"""Utility functions for Elf workflows."""

import sys
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output.defaults import create_output
from pygments.lexers.special import TextLexer
from rich.console import Console

from elf.core.compiler import WorkflowState

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

def _collect_simple_input() -> str:
    """Collect input using simple input() method."""
    console = Console(stderr=True)
    console.print("[dim]Enter your response (press Enter to submit):[/dim]")
    return input("> ")

def _collect_enhanced_input() -> str:
    """Collect input using enhanced multi-line prompt_toolkit."""
    console = Console(stderr=True)
    console.print("[dim]Commands: '/exit', '/quit', '/bye' to quit | Enter twice or '/send' to send[/dim]")
    console.print()

    lines = []
    history = InMemoryHistory()
    pt_stderr_output = create_output(sys.stderr)

    session = PromptSession(
        history=history,
        lexer=PygmentsLexer(TextLexer),
        output=pt_stderr_output
    )

    while True:
        try:
            line = session.prompt("   ", multiline=False)
        except EOFError:  # Handles Ctrl+D
            return ""

        # Check for submission commands
        if line.strip() == "/send":
            break
        if _is_exit_command(line):
            return line.strip()
        if not line.strip() and lines:  # Enter on empty line after input
            if not lines[-1].strip():  # Double empty line
                lines.append(line)
                break
            lines.append(line)  # Allow single empty lines
        elif not line.strip() and not lines:  # First line empty
            break
        else:
            lines.append(line)

    return "\n".join(lines).strip()

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
    console = Console(stderr=True)

    # Display the LLM's question with professional styling
    console.print("\n[bold blue]Assistant:[/bold blue]")
    console.print(prompt)
    console.print()  # Add spacing

    # Collect user input based on terminal capability
    try:
        if sys.stdin.isatty():
            user_response = _collect_enhanced_input()
        else:
            user_response = _collect_simple_input()
    except (KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            console.print("\n[yellow]Input cancelled.[/yellow]")
            return {**state, "user_input": "", "output": "User cancelled input"}
        # Fallback to simple input on any prompt_toolkit error
        try:
            user_response = _collect_simple_input()
        except (EOFError, KeyboardInterrupt):
            return {**state, "user_input": "", "output": "Input cancelled"}

    # Handle exit commands
    if _is_exit_command(user_response):
        _show_exit_feedback()
        return _create_exit_state(state, user_response)

    # Show normal processing feedback for non-empty responses
    if user_response:
        _show_processing_feedback()

    # Return normal state
    return {
        **state,
        "user_input": user_response,
        "output": f"User provided: {user_response}"
    }

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
