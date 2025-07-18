# src/elf0/core/input_collector.py
"""Unified input collection system with terminal handoff integration."""

import io
import sys
import time
from typing import TYPE_CHECKING, Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output.defaults import create_output
from pygments.lexers.special import TextLexer  # type: ignore
from rich.console import Console

from elf0.core.input_state import clear_collecting_input, set_collecting_input

if TYPE_CHECKING:
    from elf0.core.compiler import WorkflowState

# Exit command constants
EXIT_COMMANDS = {"/exit", "/quit", "/bye"}


class InputCollectionError(Exception):
    """Exception raised when input collection fails after all retry attempts."""


def _is_exit_command(response: str) -> bool:
    """Check if response is an exit command."""
    return response.strip().lower() in EXIT_COMMANDS


def _collect_enhanced_input() -> str:
    """Collect input using enhanced multi-line prompt_toolkit."""
    console = Console(stderr=True)
    console.print("[dim]Commands: '/exit', '/quit', '/bye' to quit | Enter twice or '/send' to send[/dim]")
    console.print()

    # Handle flush() safely for testing environments
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except (OSError, io.UnsupportedOperation):
        # In testing environments, stdout/stderr might be redirected
        pass

    lines: list[str] = []
    history = InMemoryHistory()

    pt_stderr_output = create_output(sys.stderr)
    session: Any = PromptSession(
        history=history,
        lexer=PygmentsLexer(TextLexer),
        output=pt_stderr_output
    )

    while True:
        try:
            line = str(session.prompt("> ", multiline=False))
        except EOFError:
            return ""
        except KeyboardInterrupt:
            msg = "User interrupted input"
            raise KeyboardInterrupt(msg)

        if line.strip() == "/send":
            break
        if _is_exit_command(line):
            return line.strip()
        if not line.strip() and lines:
            if not lines[-1].strip():
                lines.append(line)
                break
            lines.append(line)
        elif not line.strip() and not lines:
            break
        else:
            lines.append(line)

    return "\n".join(lines).strip()


def _collect_simple_input() -> str:
    """Collect input using simple input() method."""
    console = Console(stderr=True)
    console.print("[dim]Enter your response (press Enter to submit):[/dim]")

    # Handle flush() safely for testing environments
    try:
        sys.stdin.flush()
        sys.stdout.flush()
        sys.stderr.flush()
    except (OSError, io.UnsupportedOperation):
        # In testing environments, stdin/stdout/stderr might be redirected
        pass

    try:
        return input("> ")
    except EOFError:
        return ""


def collect_terminal_input(prompt: str, multiline: bool = True) -> str:
    """Collect terminal input with unified handoff functionality.

    Args:
        prompt: The prompt message to display to the user
        multiline: Whether to enable multi-line input (default: True)

    Returns:
        User input string

    Raises:
        InputCollectionError: If input collection fails after all retries
    """
    console = Console(stderr=True)

    # Signal input collection start
    set_collecting_input()

    try:
        # Wait for spinner handoff
        time.sleep(0.2)

        # Display prompt
        console.print("\n[bold blue]Assistant:[/bold blue]")
        console.print(prompt)
        console.print()

        # Collect input with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if sys.stdin.isatty() and multiline:
                    user_response = _collect_enhanced_input()
                else:
                    user_response = _collect_simple_input()

                # Show processing feedback for non-exit commands
                if user_response and not _is_exit_command(user_response):
                    if sys.stderr.isatty():
                        with console.status("[dim]🤔 Processing your input...[/dim]", spinner="dots"):
                            time.sleep(0.6)
                        console.print("[dim green]✓[/dim green] [dim]Input received, continuing workflow...[/dim]")
                    else:
                        console.print("[dim]🤔 Processing your input...[/dim]")
                        console.print("[dim]✓ Input received, continuing workflow...[/dim]")

                return user_response

            except KeyboardInterrupt:
                if attempt < max_retries - 1:
                    console.print(f"\n[yellow]Interrupted. Retrying... ({attempt + 1}/{max_retries})[/yellow]")
                    time.sleep(0.2)
                    continue
                console.print("\n[yellow]Input cancelled after multiple attempts.[/yellow]")
                return ""

            except Exception:
                # Fallback to simple input
                console.print("\n[yellow]Input method failed, trying simple input...[/yellow]")
                try:
                    return _collect_simple_input()
                except (EOFError, KeyboardInterrupt):
                    console.print("\n[yellow]Input cancelled.[/yellow]")
                    return ""

        msg = "Input collection failed after all retries"
        raise InputCollectionError(msg)

    finally:
        # Always clear input collection state
        clear_collecting_input()


def get_cli_input() -> str:
    """Get input for CLI prompt command.

    Returns:
        User input string
    """
    return collect_terminal_input("💬 Enter your prompt:", multiline=True)


def get_workflow_input(state: "WorkflowState", prompt: str = "Please provide input:") -> "WorkflowState":
    """Get input for workflow with proper state handling.

    Args:
        state: Current workflow state
        prompt: Prompt message to display

    Returns:
        Updated workflow state
    """
    # Extract prompt from state if default prompt provided
    if prompt == "Please provide input:":
        if "question" in state:
            question = state.get("question", prompt)
            prompt = str(question) if question is not None else prompt
        elif "output" in state:
            output = state.get("output", prompt)
            prompt = str(output) if output is not None else prompt

    user_response = collect_terminal_input(prompt, multiline=True)

    # Handle exit commands
    if _is_exit_command(user_response):
        if sys.stderr.isatty():
            console = Console(stderr=True)
            with console.status("[dim]🚪 Processing exit request...[/dim]", spinner="dots"):
                time.sleep(0.4)
            console.print("[dim red]✗[/dim red] [dim]Exiting workflow...[/dim]")
        else:
            console = Console(stderr=True)
            console.print("[dim]🚪 Processing exit request...[/dim]")
            console.print("[dim]✗ Exiting workflow...[/dim]")

        return {
            **state,
            "output": f"User requested to exit: {user_response}",
            "user_exit_requested": True
        }

    # Return normal state
    return {
        **state,
        "output": f"User provided: {user_response}"
    }
