import typer
from pathlib import Path
from typing import List, Optional, Any
import json
from elf.core.runner import run_workflow
import rich
import sys
from rich.console import Console as RichConsole
from rich.markdown import Markdown
import os
import logging
from prompt_toolkit import prompt as prompt_toolkit_prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.special import TextLexer # Using a simple lexer for plain text input
from prompt_toolkit.output.defaults import create_output as pt_create_output

# Configure global Rich console for stderr
rich.console = RichConsole(stderr=True)
# Dedicated Rich console for stdout (workflow results)
stdout_workflow_console = RichConsole(file=sys.stdout)

# Application state for --verbose flag
class AppState:
    verbose_mode: bool = False # Default is not verbose

app_state = AppState()

app = typer.Typer(
    name="elf",
    help="AI Workflow Architect - Execute and optimize LLM-powered agent workflows",
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
        help="Enable verbose logging output. Shows INFO level logs from ELF and HTTP libraries."
    )
):
    """
    ELF: AI Workflow Architect.

    Execute and optimize LLM-powered agent workflows.
    By default, only critical errors are sent to stderr. Use --verbose for more detailed logs.

    Examples for output/log redirection:
    
      elf agent workflow.yaml --prompt "Summarize" > result.txt                    # Output to file, minimal logs (errors only) to stderr
      
      elf agent workflow.yaml --prompt "Summarize" 2> elf.log                      # Minimal logs to file, output to stdout
      
      elf --verbose agent workflow.yaml --prompt "Summarize" 2> elf_verbose.log  # Verbose logs to file, output to stdout
      
      elf agent workflow.yaml --prompt "Summarize" | grep "keyword"                # Pipe output, minimal logs to stderr
      
      elf --verbose agent workflow.yaml --prompt "Summarize" | grep "keyword"      # Pipe output, verbose logs to stderr (if not redirected)
      
      elf agent workflow.yaml --prompt "Summarize" > result.txt 2> errors.log      # Output to result.txt, minimal logs to errors.log
    """
    app_state.verbose_mode = verbose
    if app_state.verbose_mode:
        # Enable INFO logging for elf.core and HTTP libraries
        core_logger = logging.getLogger('elf.core') 
        if not core_logger.hasHandlers(): 
            core_logger.addHandler(logging.NullHandler())
        core_logger.setLevel(logging.INFO) 

        for lib_name in ["httpx", "httpcore"]:
            lib_logger = logging.getLogger(lib_name)
            if not lib_logger.hasHandlers(): 
                lib_logger.addHandler(logging.NullHandler())
            lib_logger.setLevel(logging.INFO) 
    else:
        # Default: Minimal logging (errors for elf.core, warnings for HTTP)
        core_logger = logging.getLogger('elf.core')
        if not core_logger.hasHandlers():
             core_logger.addHandler(logging.NullHandler())
        core_logger.setLevel(logging.ERROR) # Only show errors from ELF core

        for lib_name in ["httpx", "httpcore"]:
            lib_logger = logging.getLogger(lib_name)
            if not lib_logger.hasHandlers():
                lib_logger.addHandler(logging.NullHandler())
            lib_logger.setLevel(logging.WARNING) # Show warnings from HTTP libs, suppress INFO

def _conditional_secho(message: str, **kwargs):
    """Helper to print to stderr.
    Errors (fg=RED) are always printed.
    Other messages (warnings, success) are printed only if in verbose mode.
    """
    is_error = kwargs.get("fg") == typer.colors.RED
    if app_state.verbose_mode or is_error:
        typer.secho(message, **kwargs)

def parse_at_references(prompt: str) -> tuple[str, List[Path]]:
    """
    Parse @ file references from a prompt string.
    
    Args:
        prompt: The input prompt that may contain @filename references
        
    Returns:
        Tuple of (cleaned_prompt, list_of_referenced_files)
    """
    import re
    
    # Find all @filename.ext patterns
    at_pattern = r'@([^\s@]+(?:\.[^\s@]+)*)'
    matches = re.findall(at_pattern, prompt)
    
    referenced_files = []
    for match in matches:
        path = Path(match)
        if _is_valid_file(path):
            referenced_files.append(path)
        else:
            _conditional_secho(f"Warning: Referenced file '@{match}' not found. Skipping.", fg=typer.colors.YELLOW)
    
    # Remove @ references from the prompt
    cleaned_prompt = re.sub(r'@[^\s@]+(?:\.[^\s@]+)*', '', prompt)
    # Clean up extra whitespace
    cleaned_prompt = ' '.join(cleaned_prompt.split())
    
    return cleaned_prompt, referenced_files

def parse_context_files(context_files: Optional[List[Path]]) -> str:
    """
    Parse and read content from context files.
    
    Args:
        context_files: List of paths to context files
        
    Returns:
        Combined content from all valid context files
    """
    if not context_files:
        return ""
        
    actual_files_to_read: List[Path] = []

    for file_or_list in context_files:
        file_str = str(file_or_list)
        if ',' in file_str:
            actual_files_to_read.extend(_parse_comma_separated_files(file_str))
        else:
            path = Path(file_str)
            if _is_valid_file(path):
                actual_files_to_read.append(path)
            else:
                _conditional_secho(f"Warning: Context file '{path}' not found or is not a file. Skipping.", fg=typer.colors.YELLOW)

    return _read_files_content(actual_files_to_read)

def _parse_comma_separated_files(file_str: str) -> List[Path]:
    """Parse comma-separated file paths."""
    valid_files = []
    for f_name in file_str.split(','):
        path = Path(f_name.strip())
        if _is_valid_file(path):
            valid_files.append(path)
        else:
            _conditional_secho(f"Warning: Context file '{f_name.strip()}' not found or is not a file. Skipping.", fg=typer.colors.YELLOW)
    return valid_files

def _is_valid_file(path: Path) -> bool:
    """Check if a path exists and is a file."""
    return path.exists() and path.is_file()

def _read_files_content(files: List[Path]) -> str:
    """Read content from a list of files."""
    content_parts = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                content_parts.append(f"Content of {file_path.name}:\n{f.read()}\n---")
        except Exception as e:
            _conditional_secho(f"Warning: Could not read context file '{file_path}': {e}. Skipping.", fg=typer.colors.YELLOW)
    return "\n".join(content_parts)

def prepare_workflow_input(prompt: str, context_content: str) -> str:
    """Combine context content with user prompt."""
    if not context_content:
        return prompt
    return f"{context_content}\nUser prompt:\n{prompt}"

def format_workflow_result(result: Any) -> tuple[str, bool]:
    """
    Format workflow result for output.
    
    Returns:
        Tuple of (formatted_content, is_json)
    """
    if isinstance(result, dict) and 'output' in result and isinstance(result['output'], str):
        return result['output'], False
    elif isinstance(result, str):
        return result, False
    else:
        try:
            return json.dumps(result, indent=4), True
        except TypeError as e:
            # This is an error, so it should always be shown on stderr
            typer.secho(f"Error: Could not serialize result to JSON: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

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
        with open(output_path, 'w') as f:
            f.write(content)
        _conditional_secho(f"Workflow result saved to '{output_path}'", fg=typer.colors.GREEN)
        
        if is_json and output_path.suffix.lower() != '.json':
            _conditional_secho(f"Note: JSON content was saved to a file with extension '{output_path.suffix}'.", fg=typer.colors.YELLOW)
    except IOError as e:
        typer.secho(f"Error writing to output file '{output_path}': {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def display_workflow_result(result: Any) -> None:
    """Display workflow result in the console to stdout."""
    if isinstance(result, dict):
        output_content = result.get('output')
        if isinstance(output_content, str):
            stdout_workflow_console.print(Markdown(output_content))
        else:
            # These warnings should go to stderr, only if verbose
            if 'output' in result:
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
    """
    Read content from a prompt file.
    
    Args:
        prompt_file: Path to the prompt file
        
    Returns:
        Content of the prompt file, or empty string if file is empty
        
    Raises:
        typer.Exit: If the file cannot be read or has an invalid extension
    """
    if prompt_file.suffix.lower() not in ['.md', '.xml']:
        typer.secho("Error: --prompt_file must be a markdown (.md) or XML (.xml) file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    try:
        content = prompt_file.read_text(encoding='utf-8')
        return content if content is not None else ""
    except Exception as e:
        typer.secho(f"Error: Could not read prompt file '{prompt_file}': {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def agent_command(
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec'),
    prompt: Optional[str] = typer.Option(None, help='User prompt to process'),
    prompt_file: Optional[Path] = typer.Option(
        None,
        "--prompt_file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Markdown (.md) or XML (.xml) file containing the prompt",
        show_default=False,
    ),
    session_id: str = typer.Option('session', help='Session identifier for stateful runs'),
    context_files: Optional[List[Path]] = typer.Option(None, "--context", help="Context file(s) to include. Use multiple times or comma-separated.", show_default=False),
    output_path: Optional[Path] = typer.Option(None, "--output", help="Save result to file instead of displaying", show_default=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
):
    """
    Execute an agent workflow defined in YAML.
    
    File References:
        Use @filename.ext within prompts to automatically include file contents as context.
    
    Examples:
        elf agent workflow.yaml --prompt "What is the weather in London?"
        elf agent workflow.yaml --prompt_file prompt.md
        elf agent workflow.yaml --prompt "Explain this code @main.py and @utils.py"
        elf agent workflow.yaml --prompt "Analyze this" --context file1.txt --output result.md
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
    result = run_workflow(spec_path, processed_prompt, session_id)
    
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
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec to improve'),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Save improved YAML to file (default: <original>_improved.yaml)", show_default=False),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Custom improvement guidance (supports @file references)", show_default=False),
    session_id: str = typer.Option('improve_session', help='Session identifier for improvement run')
):
    """
    Improve a YAML workflow specification using the built-in optimizer.
    
    File References:
        Use @filename.ext within --prompt to automatically include file contents as context.
    
    Examples:
        elf improve yaml workflow.yaml
        elf improve yaml workflow.yaml --output improved_workflow.yaml
        elf improve yaml workflow.yaml --prompt "Focus on making prompts more specific"
        elf improve yaml workflow.yaml --prompt "Follow patterns from @examples/best_workflow.yaml"
    """
    # Use the built-in agent-optimizer.yaml spec
    optimizer_spec_path = Path(__file__).parent.parent.parent / "specs" / "agent-optimizer.yaml"
    
    if not optimizer_spec_path.exists():
        typer.secho(f"Error: Agent optimizer spec not found at {optimizer_spec_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Read the original spec content
    try:
        with open(spec_path, 'r') as f:
            original_content = f.read()
    except Exception as e:
        typer.secho(f"Error reading input spec: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
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
    result = run_workflow(optimizer_spec_path, optimization_prompt, session_id)
    
    # Extract the improved YAML from the result
    if isinstance(result, dict) and 'output' in result:
        improved_yaml = result['output']
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
        with open(output_path, 'w') as f:
            f.write(improved_yaml)
        _conditional_secho(f"Improved YAML saved to: {output_path}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error saving improved YAML: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def get_multiline_input() -> str:
    """
    Get multi-line input from user with support for pasting, arrow key navigation, and history.
    
    Returns empty string if user wants to exit.
    Uses Enter on an empty line or '/submit' to submit prompt.
    """
    lines = []
    # Messages like "Enter your prompt" should only appear in verbose mode
    if app_state.verbose_mode:
        rich.console.print("[dim]💬 Enter your prompt:[/dim]") # Use the global stderr console
    
    history = InMemoryHistory()
    pt_stderr_output = pt_create_output(sys.stderr) # Ensure prompt_toolkit uses stderr
    
    try:
        while True:
            try:
                # Using a simple TextLexer, you can replace with more specific lexers if needed
                # For example, if you expect markdown, you could use MarkdownLexer
                line = prompt_toolkit_prompt(
                    "   ", 
                    history=history, 
                    lexer=PygmentsLexer(TextLexer), 
                    multiline=False,
                    output=pt_stderr_output # Pass stderr output to prompt_toolkit
                ) 
            except EOFError: # Handles Ctrl+D
                return "" 
            
            # Check for submission commands
            if line.strip() == '/submit':
                break
            elif line.strip().lower() in ['/exit', '/quit', '/bye']:
                return "" # User wants to exit
            elif not line.strip() and lines: # Enter on an empty line (after at least one line of input)
                # Check if the previous line was also effectively empty to allow for blank lines within the prompt
                if not lines[-1].strip(): 
                    lines.append(line) # Add the current empty line
                    break # Submit on double empty line
                else:
                    lines.append(line) # Allow single empty lines within the prompt
            elif not line.strip() and not lines: # First line is empty, treat as submission
                break
            else:
                lines.append(line)
    
    except KeyboardInterrupt: # Handles Ctrl+C
        # This message should only appear in verbose mode
        if app_state.verbose_mode:
            rich.console.print("\n[yellow]Input cancelled.[/yellow]") # Use the global stderr console
        return ""
    
    # Join lines and clean up
    result = '\n'.join(lines).strip()
    return result

def prompt_yaml_command(
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec to prompt'),
    session_id: str = typer.Option('interactive_session', help='Session identifier for this conversation')
):
    """
    Start an interactive prompt session with a YAML workflow specification.
    
    File References:
        Use @filename.ext within prompts to automatically include file contents as context.
    
    Examples:
        elf prompt workflow.yaml
        Then type your prompt and press Enter twice to submit
        Or type "/submit" on a new line to submit
    """
    # All these introductory messages go to stderr and only if verbose
    if app_state.verbose_mode:
        rich.console.print(f"[bold blue]Starting interactive session with {spec_path.name}[/bold blue]")
        rich.console.print("[dim]Commands: '/exit', '/quit', '/bye' to quit | Enter twice or '/submit' to send[/dim]")
        rich.console.print()
    
    try:
        while True:
            # Get multi-line user input
            prompt = get_multiline_input()
            
            # Check if user wants to exit
            if not prompt or prompt.lower() in ['exit', 'quit', 'bye']:
                break
            
            if app_state.verbose_mode:
                rich.console.print("[dim]Running workflow...[/dim]")
            
            try:
                # Parse @ references from the prompt
                cleaned_prompt, at_referenced_files = parse_at_references(prompt)
                
                # Process any @ referenced files as context
                context_content = parse_context_files(at_referenced_files if at_referenced_files else None)
                final_prompt = prepare_workflow_input(cleaned_prompt, context_content)
                
                # Run the workflow with processed prompt
                result = run_workflow(spec_path, final_prompt, session_id)
                
                # Display result (goes to stdout via display_workflow_result)
                if app_state.verbose_mode:
                     # "Response:" header goes to stderr, only if verbose
                    rich.console.print("\n[bold green]Response:[/bold green]")
                display_workflow_result(result)
                if app_state.verbose_mode:
                    rich.console.print()  # Add spacing before next prompt to stderr
                
            except Exception as e:
                # Error messages always go to stderr (rich.console is stderr by default)
                rich.console.print(f"[bold red]Error:[/bold red] {e}")
                if app_state.verbose_mode:
                    rich.console.print()  # Add spacing before next prompt
                
    except KeyboardInterrupt:
        if app_state.verbose_mode: # Message to stderr, only if verbose
            rich.console.print("\n[yellow]Session ended.[/yellow]")
    except EOFError:
        if app_state.verbose_mode: # Message to stderr, only if verbose
            rich.console.print("\n[yellow]Session ended.[/yellow]")

# Add subcommands to improve app
improve_app.command("yaml", help="Improve a YAML workflow specification using AI optimization")(improve_yaml_command)

# Register commands
app.command("agent", help="Execute an agent workflow defined in YAML")(agent_command)
app.add_typer(improve_app)
app.command("prompt", help="Start interactive conversation with a workflow agent (supports multi-line input)")(prompt_yaml_command)

if __name__ == '__main__':
    app()