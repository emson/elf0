import typer
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import json
from elf.core.runner import run_workflow
from rich.console import Console
from rich.markdown import Markdown
import os

app = typer.Typer(
    name="elf",
    help="AI Workflow Architect - Execute and optimize LLM-powered agent workflows",
    add_completion=False
)

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
        
    all_files_content = []
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
                typer.secho(f"Warning: Context file '{path}' not found or is not a file. Skipping.", fg=typer.colors.YELLOW)

    return _read_files_content(actual_files_to_read)

def _parse_comma_separated_files(file_str: str) -> List[Path]:
    """Parse comma-separated file paths."""
    valid_files = []
    for f_name in file_str.split(','):
        path = Path(f_name.strip())
        if _is_valid_file(path):
            valid_files.append(path)
        else:
            typer.secho(f"Warning: Context file '{f_name.strip()}' not found or is not a file. Skipping.", fg=typer.colors.YELLOW)
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
            typer.secho(f"Warning: Could not read context file '{file_path}': {e}. Skipping.", fg=typer.colors.YELLOW)
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
        typer.secho(f"Workflow result saved to '{output_path}'", fg=typer.colors.GREEN)
        
        if is_json and output_path.suffix.lower() != '.json':
            typer.secho(f"Note: JSON content was saved to a file with extension '{output_path.suffix}'.", fg=typer.colors.YELLOW)
    except IOError as e:
        typer.secho(f"Error writing to output file '{output_path}': {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def display_workflow_result(result: Any) -> None:
    """Display workflow result in the console."""
    if isinstance(result, dict):
        output_content = result.get('output')
        if isinstance(output_content, str):
            console = Console()
            console.print(Markdown(output_content))
        else:
            if 'output' in result:
                typer.secho(f"Warning: Content of 'output' key is not a string (type: {type(output_content)}). Displaying raw result.", fg=typer.colors.YELLOW)
            else:
                typer.secho("Warning: Key 'output' not found in workflow result. Displaying raw result.", fg=typer.colors.YELLOW)
            typer.echo(str(result))
    elif isinstance(result, str):
        typer.echo(result)
    else:
        typer.secho(f"Warning: Unexpected result type from workflow ({type(result)}). Displaying raw result.", fg=typer.colors.YELLOW)
        typer.echo(str(result))

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

def run_workflow_command(
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec'),
    prompt: Optional[str] = typer.Option(None, help='User prompt to process'),
    prompt_file: Optional[Path] = typer.Option(
        None,
        "--prompt_file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to a markdown (.md) or XML (.xml) file containing the prompt.",
        show_default=False,
    ),
    session_id: str = typer.Option('session', help='Session identifier for stateful runs'),
    context_files: Optional[List[Path]] = typer.Option(None, "--context", help="Path to context file(s). Can be specified multiple times or as a comma-separated list. File contents will be added to the prompt.", show_default=False),
    output_path: Optional[Path] = typer.Option(None, "--output", help="Path to save the final workflow result. If provided, console output of the result is suppressed.", show_default=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
):
    """
    Execute an agent workflow defined in YAML.
    
    Example:
        elf workflow.yaml --prompt "What is the weather in London?"
        elf workflow.yaml --prompt_file prompt.md
        elf workflow.yaml --prompt_file prompt.md --prompt "Additional instructions"
        elf workflow.yaml --prompt "Summarize these files" --context file1.txt --context dir/file2.py
        elf workflow.yaml --prompt "Explain this code" --context file1.py,file2.py
        elf workflow.yaml --prompt "Explain this code" --context file1.py --output result.md
        elf workflow.yaml --prompt "Summarize data" --output summary.json
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

    # Process context files and prepare input
    context_content = parse_context_files(context_files)
    processed_prompt = prepare_workflow_input(combined_prompt, context_content)
    
    # Run workflow
    result = run_workflow(spec_path, processed_prompt, session_id)
    
    # Handle output
    if output_path:
        content, is_json = format_workflow_result(result)
        if not content:
            typer.secho(f"Warning: Workflow result is empty. Writing an empty file to '{output_path}'.", fg=typer.colors.YELLOW)
            content = ""
        
        validate_output_path(output_path)
        save_workflow_result(output_path, content, is_json)
    else:
        display_workflow_result(result)

app.command()(run_workflow_command)

if __name__ == '__main__':
    app()