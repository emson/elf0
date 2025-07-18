from collections.abc import Generator
import contextlib
import json
import logging
import os
from pathlib import Path
import sys
from typing import Annotated, Any

from prompt_toolkit import PromptSession  # Added for specifying output
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output.defaults import create_output as pt_create_output
from pygments.lexers.special import (
    TextLexer,  # Using a simple lexer for plain text input
)
import rich
from rich.console import Console as RichConsole
from rich.live import Live
from rich.logging import RichHandler  # Added
from rich.markdown import Markdown
from rich.spinner import Spinner
import typer

from elf0.core.exceptions import UserExitRequested
from elf0.core.input_state import is_collecting_input
from elf0.core.runner import run_workflow
from elf0.utils.file_utils import (  # Added import
    extract_spec_description,
    list_spec_files,
    parse_at_references,
    parse_context_files,
)

# Configure global Rich console for stderr
# This is used by the RichHandler's default console if not specified,
# or can be passed explicitly.
rich.console = RichConsole(stderr=True)
# Dedicated Rich console for stdout (workflow results)
stdout_workflow_console = RichConsole(file=sys.stdout)

# --- BEGIN Centralized basicConfig (Module Level) ---
# Setup root logger with RichHandler. Specific log levels are tuned by main_callback.
logging.basicConfig(
    level=logging.WARNING,  # Default root level. Loggers like 'elf0.core' will be adjusted.
    format="%(message)s",   # RichHandler handles its own formatting.
    datefmt="[%X]",         # RichHandler might use its own or this as a hint.
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False,
            log_time_format="[%X]",
            console=rich.console # Use the globally configured stderr RichConsole
        )
    ]
)
# --- END Centralized basicConfig ---

# Application state for --verbose flag
class AppState:
    verbose_mode: bool = False # Default is not verbose

app_state = AppState()

app = typer.Typer(
    name="elf0",
    help="Elf0 - sElf Improving Agentic YAML Workflows",
    add_completion=False,
    rich_markup_mode="rich"
)

improve_app = typer.Typer(
    name="improve",
    help="Improve and optimize YAML workflow specifications"
)

@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging output. Shows INFO level logs from Elf0 and HTTP libraries."
    )
) -> None:
    """Elf0: sElf Improving Agentic YAML Workflows, zero complex coding required.

    Execute and optimize LLM-powered agentic YAML workflows.
    By default, only critical errors are sent to stderr. Use --verbose for more detailed logs.

    Examples for output/log redirection:

      elf0 agent workflow.yaml --prompt "Summarize" > result.txt                    # Output to file, minimal logs (errors only) to stderr

      elf0 agent workflow.yaml --prompt "Summarize" 2> elf0.log                      # Minimal logs to file, output to stdout

      elf0 --verbose agent workflow.yaml --prompt "Summarize" 2> elf0_verbose.log  # Verbose logs to file, output to stdout

      elf0 agent workflow.yaml --prompt "Summarize" | grep "keyword"                # Pipe output, minimal logs to stderr

      elf0 --verbose agent workflow.yaml --prompt "Summarize" | grep "keyword"      # Pipe output, verbose logs to stderr (if not redirected)

      elf0 agent workflow.yaml --prompt "Summarize" > result.txt 2> errors.log      # Output to result.txt, minimal logs to errors.log
    """
    app_state.verbose_mode = verbose
    if app_state.verbose_mode:
        # Enable INFO logging for elf.core and HTTP libraries
        logging.getLogger("elf0.core").setLevel(logging.INFO)
        # Removed NullHandler logic for elf.core

        for lib_name in ["httpx", "httpcore"]:
            lib_logger = logging.getLogger(lib_name)
            # Removed NullHandler logic for http libs
            lib_logger.setLevel(logging.INFO)
    else:
        # Default: Minimal logging (errors for elf.core, warnings for HTTP)
        logging.getLogger("elf0.core").setLevel(logging.ERROR)
        # Removed NullHandler logic for elf.core

        for lib_name in ["httpx", "httpcore"]:
            lib_logger = logging.getLogger(lib_name)
            # Removed NullHandler logic for http libs
            lib_logger.setLevel(logging.WARNING)

def _conditional_secho(message: str, **kwargs: Any) -> None:
    """Helper to print to stderr.

    Errors (fg=RED) are always printed.
    Other messages (warnings, success) are printed only if in verbose mode.
    """
    is_error = kwargs.get("fg") == typer.colors.RED
    if app_state.verbose_mode or is_error:
        typer.secho(message, **kwargs)


@contextlib.contextmanager
def progress_spinner(message: str) -> Generator[None]:
    """Context manager that shows a spinner with message in non-verbose mode."""
    if app_state.verbose_mode:
        # In verbose mode, just yield without showing spinner
        yield
    else:
        # In non-verbose mode, show spinner with clean terminal handoff
        import threading
        import time
        
        # Create spinner
        spinner = Spinner("dots", text=f"[dim]{message}[/dim]")
        live = Live(spinner, console=rich.console, refresh_per_second=10)
        
        # Control variables
        stop_monitoring = threading.Event()
        
        def monitor_and_manage():
            """Monitor input state and manage spinner pause/resume."""
            spinner_running = False
            
            while not stop_monitoring.wait(0.1):
                input_active = is_collecting_input()
                
                if input_active and spinner_running:
                    # Pause spinner for input collection
                    try:
                        live.stop()
                        spinner_running = False
                    except Exception:
                        pass
                elif not input_active and not spinner_running:
                    # Resume spinner after input collection
                    try:
                        live.start()
                        spinner_running = True
                    except Exception:
                        pass
        
        # Start spinner
        live.start()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_and_manage, daemon=True)
        monitor_thread.start()
        
        try:
            yield
        finally:
            # Clean shutdown
            stop_monitoring.set()
            monitor_thread.join(timeout=0.5)
            try:
                live.stop()
            except Exception:
                pass

def prepare_workflow_input(prompt: str, context_content: str) -> str:
    """Combine context content with user prompt."""
    if not context_content:
        return prompt
    return f"{context_content}\nUser prompt:\n{prompt}"

def format_workflow_result(result: object) -> tuple[str, bool]:
    """Format workflow result for output.

    Returns:
        Tuple of (formatted_content, is_json)
    """
    if isinstance(result, dict) and "output" in result and isinstance(result["output"], str):
        return result["output"], False
    if isinstance(result, str):
        return result, False
    try:
        return json.dumps(result, indent=4), True
    except TypeError as e:
        # This is an error, so it should always be shown on stderr
        typer.secho(f"Error: Could not serialize result to JSON: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

def _display_spec_file(spec_file_path: Path, show_full_path: bool = False) -> None:
    """Display a single spec file with its description."""
    description = extract_spec_description(spec_file_path)

    if show_full_path:
        full_path = str(spec_file_path.relative_to(Path()))
        rich.console.print(f"[bold bright_green]{full_path}[/bold bright_green]")
    else:
        rich.console.print(f"[bold bright_green]{spec_file_path.name}[/bold bright_green]")

    if description == "No description available.":
        rich.console.print(f"  [dim italic]{description}[/dim italic]")
    elif "Error:" in description:
        rich.console.print(f"  [red]{description}[/red]")
    else:
        rich.console.print(f"  {description}")

def _display_grouped_specs(grouped_files: dict, directory_order: list[str]) -> None:
    """Display specs grouped by directory."""
    first_group = True
    for dir_name in directory_order:
        if dir_name in grouped_files:
            files_in_dir = grouped_files[dir_name]

            # Add spacing between groups (except before first group)
            if not first_group:
                rich.console.print()
                rich.console.print()

            # Directory header
            rich.console.print(f"[bold blue]── {dir_name.title()} ──[/bold blue]")
            rich.console.print()

            # Files in this directory
            for i, spec_file_path in enumerate(files_in_dir):
                # Add subtle separator between files in same directory
                if i > 0:
                    rich.console.print()

                _display_spec_file(spec_file_path, show_full_path=True)

            first_group = False

    # Final spacing
    rich.console.print()

def _display_single_directory_specs(spec_files: list[Path]) -> None:
    """Display specs for a single directory."""
    for i, spec_file_path in enumerate(spec_files):
        # Add spacing between entries except the first one
        if i > 0:
            rich.console.print()

        _display_spec_file(spec_file_path, show_full_path=True)

        # Add a blank line after the last item for spacing before the next shell prompt
        if i == len(spec_files) - 1:
            rich.console.print()

def validate_output_path(output_path: Path) -> None:
    """Validate output path and permissions."""
    if not output_path.parent.exists():
        typer.secho(f"Error: Parent directory '{output_path.parent}' does not exist.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not os.access(output_path.parent, os.W_OK):
        typer.secho(f"Error: Parent directory '{output_path.parent}' is not writable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if output_path.exists() and not os.access(output_path, os.W_OK):
        typer.secho(f"Error: Output file '{output_path}' is not writable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def save_workflow_result(output_path: Path, content: str, is_json: bool) -> None:
    """Save workflow result to file."""
    try:
        with output_path.open("w") as f:
            f.write(content)
        _conditional_secho(f"Workflow result saved to '{output_path}'", fg=typer.colors.GREEN)

        if is_json and output_path.suffix.lower() != ".json":
            _conditional_secho(f"Note: JSON content was saved to a file with extension '{output_path.suffix}'.", fg=typer.colors.YELLOW)
    except OSError as e:
        typer.secho(f"Error writing to output file '{output_path}': {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

def display_workflow_result(result: object) -> None:
    """Display workflow result in the console to stdout."""
    if isinstance(result, dict):
        output_content = result.get("output")
        if isinstance(output_content, str):
            stdout_workflow_console.print(Markdown(output_content))
        else:
            # These warnings should go to stderr, only if verbose
            if "output" in result:
                _conditional_secho(f"Warning: Content of 'output' key is not a string (type: {type(output_content)}). Displaying raw result to stdout.", fg=typer.colors.YELLOW)
            else:
                _conditional_secho("Warning: Key 'output' not found in workflow result. Displaying raw result to stdout.", fg=typer.colors.YELLOW)
            # The raw result still goes to stdout
            stdout_workflow_console.print(str(result))
    elif isinstance(result, str):
        stdout_workflow_console.print(result) # Ensure this uses the stdout console
    else:
        # This warning goes to stderr, only if verbose
        _conditional_secho(f"Warning: Unexpected result type from workflow ({type(result)}). Displaying raw result to stdout.", fg=typer.colors.YELLOW)
        # The raw result still goes to stdout
        stdout_workflow_console.print(str(result))

def read_prompt_file(prompt_file: Path) -> str:
    """Read content from a prompt file.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Content of the prompt file, or empty string if file is empty

    Raises:
        typer.Exit: If the file cannot be read or has an invalid extension
    """
    if prompt_file.suffix.lower() not in [".md", ".xml"]:
        typer.secho("Error: --prompt_file must be a markdown (.md) or XML (.xml) file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        content = prompt_file.read_text(encoding="utf-8")
        return content if content is not None else ""
    except OSError as e:
        typer.secho(f"Error: Could not read prompt file '{prompt_file}': {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

def agent_command(
    spec_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, help="Path to YAML spec")],
    prompt: str | None = typer.Option(None, help="User prompt to process"),
    prompt_file: Path | None = typer.Option(
        None,
        "--prompt_file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Markdown (.md) or XML (.xml) file containing the prompt",
        show_default=False,
    ),
    session_id: str = typer.Option("session", help="Session identifier for stateful runs"),
    context_files: list[Path] | None = typer.Option(None, "--context", help="Context file(s) to include. Use multiple times or comma-separated.", show_default=False),
    output_path: Path | None = typer.Option(None, "--output", help="Save result to file instead of displaying", show_default=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
) -> None:
    """Execute an agent workflow defined in YAML.

    File References:
        Use @filename.ext within prompts to automatically include file contents as context.

    Examples:
        elf0 agent workflow.yaml --prompt "What is the weather in London?"
        elf0 agent workflow.yaml --prompt_file prompt.md
        elf0 agent workflow.yaml --prompt "Explain this code @main.py and @utils.py"
        elf0 agent workflow.yaml --prompt "Analyze this" --context file1.txt --output result.md
    """
    # Validate that at least one prompt source is provided
    if not prompt and not prompt_file:
        typer.secho("Error: You must provide either --prompt or --prompt_file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Read prompt_file content if provided
    prompt_file_content = ""
    if prompt_file:
        prompt_file_content = read_prompt_file(prompt_file)

    # Combine prompt_file content and prompt string
    if prompt_file_content and prompt:
        combined_prompt = f"{prompt_file_content}\n{prompt}"
    elif prompt_file_content:
        combined_prompt = prompt_file_content
    else:
        combined_prompt = prompt or ""  # Ensure we never pass None to run_workflow

    # Parse @ references from the prompt and extract context files
    cleaned_prompt, at_referenced_files = parse_at_references(combined_prompt)

    # Combine explicit context files with @ referenced files
    all_context_files = (context_files or []) + at_referenced_files

    # Process context files and prepare input
    context_content = parse_context_files(all_context_files if all_context_files else None)
    processed_prompt = prepare_workflow_input(cleaned_prompt, context_content)

    # Run workflow
    try:
        with progress_spinner("Running workflow..."):
            result = run_workflow(spec_path, processed_prompt, session_id)
    except UserExitRequested:
        # User requested to exit, end gracefully
        rich.console.print("\n[yellow]Workflow terminated by user.[/yellow]")
        raise typer.Exit(code=0) from None

    # Handle output
    if output_path:
        content, is_json = format_workflow_result(result)
        if not content:
            _conditional_secho(f"Warning: Workflow result is empty. Writing an empty file to '{output_path}'.", fg=typer.colors.YELLOW)
            content = ""

        validate_output_path(output_path)
        save_workflow_result(output_path, content, is_json)
    else:
        display_workflow_result(result)

def improve_yaml_command(
    spec_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, help="Path to YAML spec to improve")],
    output_path: Path | None = typer.Option(None, "--output", "-o", help="Save improved YAML to file (default: <original>_improved.yaml)", show_default=False),
    prompt: str | None = typer.Option(None, "--prompt", help="Custom improvement guidance (supports @file references)", show_default=False),
    session_id: str = typer.Option("improve_session", help="Session identifier for improvement run")
) -> None:
    """Improve a YAML workflow specification using the built-in optimizer.

    File References:
        Use @filename.ext within --prompt to automatically include file contents as context.

    Examples:
        elf0 improve yaml workflow.yaml
        elf0 improve yaml workflow.yaml --output improved_workflow.yaml
        elf0 improve yaml workflow.yaml --prompt "Focus on making prompts more specific"
        elf0 improve yaml workflow.yaml --prompt "Follow patterns from @examples/best_workflow.yaml"
    """
    # Use the built-in agent-optimizer.yaml spec
    optimizer_spec_path = Path(__file__).parent.parent.parent / "specs" / "utils" /  "optimizer_yaml_v1.yaml"

    if not optimizer_spec_path.exists():
        typer.secho(f"Error: Agent optimizer spec not found at {optimizer_spec_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Read the original spec content
    try:
        with spec_path.open() as f:
            original_content = f.read()
    except OSError as e:
        typer.secho(f"Error reading input spec: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

    # Prepare the prompt for the optimizer
    base_prompt = f"""Please improve this YAML workflow specification:

```yaml
{original_content}
```

Focus on:
1. Schema compliance and best practices
2. Clear, effective prompts and descriptions
3. Proper workflow structure and error handling
4. Optimal LLM parameters for the use case
5. Documentation and maintainability"""

    # Add custom improvement guidance if provided
    if prompt:
        # Parse @ references from the custom prompt
        cleaned_custom_prompt, at_referenced_files = parse_at_references(prompt)

        # Process any @ referenced files as context
        context_content = parse_context_files(at_referenced_files if at_referenced_files else None)

        # Combine context with the custom prompt
        if context_content:
            custom_guidance = f"{context_content}\n\nCustom improvement guidance:\n{cleaned_custom_prompt}"
        else:
            custom_guidance = cleaned_custom_prompt

        optimization_prompt = f"""{base_prompt}

Additional improvement guidance:
{custom_guidance}

Output only the improved YAML specification."""
    else:
        optimization_prompt = f"""{base_prompt}

Output only the improved YAML specification."""

    # This is an informational message
    if app_state.verbose_mode:
        typer.secho("Improving YAML specification...", fg=typer.colors.BLUE)

    # Run the optimizer workflow
    try:
        with progress_spinner("Optimizing YAML specification..."):
            result = run_workflow(optimizer_spec_path, optimization_prompt, session_id)
    except UserExitRequested:
        # User requested to exit during optimization
        rich.console.print("\n[yellow]Optimization terminated by user.[/yellow]")
        raise typer.Exit(code=0) from None

    # Extract the improved YAML from the result
    if isinstance(result, dict) and "output" in result:
        improved_yaml = result["output"]
    elif isinstance(result, str):
        improved_yaml = result
    else:
        typer.secho("Error: Unexpected result format from optimizer", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Determine output path
    if not output_path:
        output_path = spec_path.parent / f"{spec_path.stem}_improved{spec_path.suffix}"

    # Save the improved YAML
    try:
        with output_path.open("w") as f:
            f.write(improved_yaml)
        _conditional_secho(f"Improved YAML saved to: {output_path}", fg=typer.colors.GREEN)
    except OSError as e:
        typer.secho(f"Error saving improved YAML: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

def get_multiline_input() -> str:
    """Get multi-line input from user with support for pasting, arrow key navigation, and history.

    Returns empty string if user wants to exit.
    Uses Enter on an empty line or '/send' to send prompt.
    """
    lines = []
    # Messages like "Enter your prompt" are essential UI for interactive mode, always show.
    rich.console.print("[dim]💬 Enter your prompt:[/dim]") # Use the global stderr console

    history = InMemoryHistory()
    pt_stderr_output = pt_create_output(sys.stderr) # Ensure prompt_toolkit uses stderr
    # Create a PromptSession with the desired output, history, and lexer
    session = PromptSession(
        history=history,
        lexer=PygmentsLexer(TextLexer),
        output=pt_stderr_output
    )

    try:
        while True:
            try:
                # Use the prompt method from the session instance
                line = session.prompt(
                    "   ",
                    multiline=False # multiline can be specified per-prompt call
                )
            except EOFError: # Handles Ctrl+D
                return ""

            # Check for submission commands
            if line.strip() == "/send":
                break
            if line.strip().lower() in ["/exit", "/quit", "/bye"]:
                return "" # User wants to exit
            if not line.strip() and lines: # Enter on an empty line (after at least one line of input)
                # Check if the previous line was also effectively empty to allow for blank lines within the prompt
                if not lines[-1].strip():
                    lines.append(line) # Add the current empty line
                    break # send on double empty line
                lines.append(line) # Allow single empty lines within the prompt
            elif not line.strip() and not lines: # First line is empty, treat as submission
                break
            else:
                lines.append(line)

    except KeyboardInterrupt: # Handles Ctrl+C
        # This message is essential feedback for interactive mode, always show.
        rich.console.print("\n[yellow]Input cancelled.[/yellow]") # Use the global stderr console
        return ""

    # Join lines and clean up
    return "\n".join(lines).strip()

def prompt_yaml_command(
    spec_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, help="Path to YAML spec to prompt")],
    session_id: str = typer.Option("interactive_session", help="Session identifier for this conversation")
) -> None:
    """Start an interactive prompt session with a YAML workflow specification.

    File References:
        Use @filename.ext within prompts to automatically include file contents as context.

    Examples:
        elf0 prompt workflow.yaml
        Then type your prompt and press Enter twice to send
        Or type "/send" on a new line to send
    """
    # All these introductory messages are essential UI for interactive mode, always show.
    rich.console.print(f"[bold blue]Starting interactive session with {spec_path.name}[/bold blue]")
    rich.console.print("[dim]Commands: '/exit', '/quit', '/bye' to quit | Enter twice or '/send' to send[/dim]")
    rich.console.print()

    try:
        while True:
            # Get multi-line user input
            prompt = get_multiline_input()

            # Check if user wants to exit
            if not prompt or prompt.lower() in ["exit", "quit", "bye"]:
                break

            # "Running workflow..." is essential feedback in interactive mode.
            rich.console.print("[dim]Running workflow...[/dim]")

            try:
                # Parse @ references from the prompt
                cleaned_prompt, at_referenced_files = parse_at_references(prompt)

                # Process any @ referenced files as context
                context_content = parse_context_files(at_referenced_files if at_referenced_files else None)
                final_prompt = prepare_workflow_input(cleaned_prompt, context_content)

                # Run the workflow with processed prompt
                try:
                    with progress_spinner("Processing..."):
                        result = run_workflow(spec_path, final_prompt, session_id)
                except UserExitRequested:
                    # User requested to exit during workflow, break the interactive loop
                    rich.console.print("\n[yellow]Workflow terminated by user.[/yellow]")
                    break

                # Display result (goes to stdout via display_workflow_result)
                # "Response:" header is essential UI in interactive mode.
                rich.console.print("\n[bold green]Response:[/bold green]")
                display_workflow_result(result)
                # Spacing for next prompt is also part of interactive UI flow.
                rich.console.print()  # Add spacing before next prompt to stderr

            except Exception as e:
                # Error messages always go to stderr (rich.console is stderr by default)
                rich.console.print(f"[bold red]Error:[/bold red] {e}")
                # Spacing after error in interactive mode.
                rich.console.print()  # Add spacing before next prompt

    except KeyboardInterrupt:
        # Session ended message is essential UI feedback.
        rich.console.print("\n[yellow]Session ended.[/yellow]")
    except EOFError:
        # Session ended message is essential UI feedback.
        rich.console.print("\n[yellow]Session ended.[/yellow]")

@app.command("list-specs", help="List YAML workflow spec files, optionally filtered by directory.")
def list_specs_command(
    directory: str = typer.Argument(
        None,
        help="Optional directory filter (basic, content, code, examples, utils, archive). Shows all except archive if not specified."
    )
) -> None:
    """Scans the ./specs directory for YAML workflow specification files (.yaml or .yml)
    and displays them with their descriptions.

    Descriptions are extracted from a 'description' field in the YAML or the first comment line.
    """
    specs_dir = Path("./specs")

    if not specs_dir.exists() or not specs_dir.is_dir():
        rich.console.print(f"[yellow]Warning:[/] Specs directory '{specs_dir}' not found.")
        return

    spec_files = list_spec_files(specs_dir, directory)

    if not spec_files:
        rich.console.print(f"No spec files (.yaml or .yml) found in '{specs_dir}'.")
        return

    if directory is None:
        # Group by directory when showing all specs
        from collections import defaultdict

        # Group files by directory
        grouped_files = defaultdict(list)
        for spec_file_path in spec_files:
            dir_name = spec_file_path.parent.name
            grouped_files[dir_name].append(spec_file_path)

        # Define directory order (archive last, excluded from 'all')
        directory_order = ["specs", "basic", "content", "code", "examples", "utils"]

        _display_grouped_specs(grouped_files, directory_order)
    else:
        _display_single_directory_specs(spec_files)

# Add subcommands to improve app
improve_app.command("yaml", help="Improve a YAML workflow specification using AI optimization")(improve_yaml_command)

# Register commands
app.command("agent", help="Execute an agent workflow defined in YAML")(agent_command)
app.add_typer(improve_app)
app.command("prompt", help="Start interactive conversation with a workflow agent (supports multi-line input)")(prompt_yaml_command)

if __name__ == "__main__":
    app()
