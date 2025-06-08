# src/elf/functions/utils.py
"""Utility functions for Elf workflows."""

from ..core.compiler import WorkflowState
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.special import TextLexer
from prompt_toolkit.output.defaults import create_output
from rich.console import Console
import time

def get_user_input(state: WorkflowState, prompt: str = "Please provide input:") -> WorkflowState:
    """
    Function that requests user input via CLI with multi-line support.
    
    Uses enhanced input mechanism when in terminal, falls back to simple input otherwise:
    - Multi-line input support (when in terminal)
    - Double-enter or '/send' to submit
    - Exit commands ('/exit', '/quit', '/bye')
    - History and navigation support (when in terminal)
    
    Args:
        state: Current workflow state
        prompt: Question or prompt to display to user
        
    Returns:
        Updated workflow state with user response
    """
    print(f"\n📝 {prompt}")
    
    # Check if we're in a terminal environment that supports prompt_toolkit
    try:
        if not sys.stdin.isatty():
            # Not in a terminal, use simple input
            print("Enter your response (press Enter to submit):")
            user_response = input("> ")
            
            # Check for exit commands in simple input mode too
            if user_response.strip().lower() in ['/exit', '/quit', '/bye']:
                console = Console(stderr=True)
                
                # Show immediate exit processing feedback
                if sys.stderr.isatty():
                    # Rich terminal - use spinner for exit processing
                    with console.status("[dim]🚪 Processing exit request...[/dim]", spinner="dots"):
                        time.sleep(0.4)  # Brief pause to show the indicator
                    console.print("[dim red]✗[/dim red] [dim]Exiting workflow...[/dim]")
                else:
                    # Non-terminal - simple text indicators
                    console.print("[dim]🚪 Processing exit request...[/dim]")
                    console.print("[dim]✗ Exiting workflow...[/dim]")
                
                return {
                    **state,
                    'user_input': user_response,
                    'output': f"User requested to exit: {user_response}",
                    'user_exit_requested': True  # Flag for workflow termination
                }
        else:
            # In a terminal, use enhanced multi-line input
            print("Enter your response: ('/exit'| Enter twice or '/send' to send)\n")
            
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
                    user_response = ""
                    break
                
                # Check for submission commands
                if line.strip() == '/send':
                    break
                elif line.strip().lower() in ['/exit', '/quit', '/bye']:
                    console = Console(stderr=True)
                    
                    # Show immediate exit processing feedback
                    if sys.stderr.isatty():
                        # Rich terminal - use spinner for exit processing
                        with console.status("[dim]🚪 Processing exit request...[/dim]", spinner="dots"):
                            time.sleep(0.4)  # Brief pause to show the indicator
                        console.print("[dim red]✗[/dim red] [dim]Exiting workflow...[/dim]")
                    else:
                        # Non-terminal - simple text indicators
                        console.print("[dim]🚪 Processing exit request...[/dim]")
                        console.print("[dim]✗ Exiting workflow...[/dim]")
                    
                    return {
                        **state,
                        'user_input': line.strip(),
                        'output': f"User requested to exit: {line.strip()}",
                        'user_exit_requested': True  # Flag for workflow termination
                    }
                elif not line.strip() and lines:  # Enter on empty line after input
                    if not lines[-1].strip():  # Double empty line
                        lines.append(line)
                        break
                    else:
                        lines.append(line)  # Allow single empty lines
                elif not line.strip() and not lines:  # First line empty
                    break
                else:
                    lines.append(line)
            
            if 'user_response' not in locals():
                user_response = '\n'.join(lines).strip()
                
    except (KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            print("\nInput cancelled.")
        else:
            # Fallback to simple input on any prompt_toolkit error
            print("Enter your response (press Enter to submit):")
            try:
                user_response = input("> ")
                
                # Check for exit commands in fallback mode too
                if user_response.strip().lower() in ['/exit', '/quit', '/bye']:
                    console = Console(stderr=True)
                    
                    # Show immediate exit processing feedback
                    if sys.stderr.isatty():
                        # Rich terminal - use spinner for exit processing
                        with console.status("[dim]🚪 Processing exit request...[/dim]", spinner="dots"):
                            time.sleep(0.4)  # Brief pause to show the indicator
                        console.print("[dim red]✗[/dim red] [dim]Exiting workflow...[/dim]")
                    else:
                        # Non-terminal - simple text indicators
                        console.print("[dim]🚪 Processing exit request...[/dim]")
                        console.print("[dim]✗ Exiting workflow...[/dim]")
                    
                    return {
                        **state,
                        'user_input': user_response,
                        'output': f"User requested to exit: {user_response}",
                        'user_exit_requested': True  # Flag for workflow termination
                    }
            except (EOFError, KeyboardInterrupt):
                user_response = ""
    
    # Show processing indicator after user submits input
    if user_response:
        console = Console(stderr=True)
        
        # Different indicators based on terminal capability
        if sys.stderr.isatty():
            # Rich terminal - use professional spinner with checkmark
            with console.status("[dim]🤔 Processing your input...[/dim]", spinner="dots"):
                time.sleep(0.6)  # Brief pause to show the indicator
            console.print("[dim green]✓[/dim green] [dim]Input received, continuing workflow...[/dim]")
        else:
            # Non-terminal - simple text indicator
            console.print("[dim]🤔 Processing your input...[/dim]")
            console.print("[dim]✓ Input received, continuing workflow...[/dim]")
    
    return {
        **state,
        'user_input': user_response,
        'output': f"User provided: {user_response}"
    }

def text_processor(state: WorkflowState, operation: str = "count_words") -> WorkflowState:
    """
    Process text from workflow state.
    
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
    elif operation == "uppercase":
        transformed = text.upper()
        return {
            **state,
            "output": transformed,
            "transformation": "uppercase"
        }
    elif operation == "length":
        char_count = len(text)
        return {
            **state,
            "output": f"Character count: {char_count}",
            "character_count": char_count,
            "processed_text": text
        }
    else:
        return {
            **state,
            "output": f"Unknown operation: {operation}",
            "error_context": f"Unsupported operation: {operation}"
        }