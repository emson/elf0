import typer
from pathlib import Path
from typing import List, Optional
import json # Added for JSON serialization
from awa.core.runner import run_workflow
from rich.console import Console
from rich.markdown import Markdown
import os

app = typer.Typer(
    name="awa",
    help="AI Workflow Architect - Execute and optimize LLM-powered agent workflows",
    add_completion=False
)

def run_workflow_command(
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec'),
    prompt: str = typer.Option(..., help='User prompt to process'),
    session_id: str = typer.Option('session', help='Session identifier for stateful runs'),
    context_files: Optional[List[Path]] = typer.Option(None, "--context", help="Path to context file(s). Can be specified multiple times or as a comma-separated list. File contents will be added to the prompt.", show_default=False),
    output_path: Optional[Path] = typer.Option(None, "--output", help="Path to save the final workflow result. If provided, console output of the result is suppressed.", show_default=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
):
    """
    Execute an agent workflow defined in YAML.
    
    Example:
        awa workflow.yaml --prompt "What is the weather in London?"
        awa workflow.yaml --prompt "Summarize these files" --context file1.txt --context dir/file2.py
        awa workflow.yaml --prompt "Explain this code" --context file1.py,file2.py
        awa workflow.yaml --prompt "Explain this code" --context file1.py --output result.md
        awa workflow.yaml --prompt "Summarize data" --output summary.json
    """
    processed_prompt = prompt
    if context_files:
        all_files_content = []
        actual_files_to_read: List[Path] = []

        for file_or_list in context_files:
            # Typer might pass a single Path object even for comma-separated if not invoked multiple times
            # So we convert to string and check for commas
            file_str = str(file_or_list)
            if ',' in file_str:
                for f_name in file_str.split(','):
                    path = Path(f_name.strip())
                    if path.exists() and path.is_file():
                        actual_files_to_read.append(path)
                    else:
                        typer.secho(f"Warning: Context file '{f_name.strip()}' not found or is not a file. Skipping.", fg=typer.colors.YELLOW)
            else:
                path = Path(file_str) # Ensure it's a Path object
                if path.exists() and path.is_file():
                    actual_files_to_read.append(path)
                else:
                    typer.secho(f"Warning: Context file '{path}' not found or is not a file. Skipping.", fg=typer.colors.YELLOW)

        for file_path in actual_files_to_read:
            try:
                with open(file_path, 'r') as f:
                    all_files_content.append(f"Content of {file_path.name}:\\n{f.read()}\\n---")
            except Exception as e:
                typer.secho(f"Warning: Could not read context file '{file_path}': {e}. Skipping.", fg=typer.colors.YELLOW)
        
        if all_files_content:
            processed_prompt = "\\n".join(all_files_content) + "\\nUser prompt:\\n" + prompt

    result = run_workflow(spec_path, processed_prompt, session_id)

    if output_path:
        content_to_save = ""
        save_as_json = False

        if isinstance(result, dict) and 'output' in result and isinstance(result['output'], str):
            content_to_save = result['output']
        elif isinstance(result, str):
            content_to_save = result
        else:
            # Serialize entire result as JSON if it's not a string or dict with 'output':str
            # This includes cases where result is a dict but 'output' is missing or not a string.
            try:
                content_to_save = json.dumps(result, indent=4)
                save_as_json = True # Flag to indicate content is JSON
            except TypeError as e:
                typer.secho(f"Error: Could not serialize result to JSON for output file: {e}", fg=typer.colors.RED)
                typer.secho(f"Result type: {type(result)}, Result: {result}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        # Handle empty content
        if content_to_save is None or content_to_save == "":
            typer.secho(f"Warning: Workflow result is empty. Writing an empty file to '{output_path}'.", fg=typer.colors.YELLOW)
            content_to_save = "" # Ensure it's an empty string for writing

        # Note: output_path.parent.mkdir(parents=True, exist_ok=True) could be used if auto-creating parent dirs was desired.
        # However, the requirements state to check if parent directory exists and is writable if the file does not exist.
        # Typer's `writable=True` on `Path` handles some checks. For non-existent files, we check parent explicitly.
        try:
            if not output_path.exists():
                if not output_path.parent.exists():
                    typer.secho(f"Error: Parent directory '{output_path.parent}' does not exist.", fg=typer.colors.RED)
                    raise typer.Exit(code=1)
                if not os.access(output_path.parent, os.W_OK):
                    typer.secho(f"Error: Parent directory '{output_path.parent}' is not writable.", fg=typer.colors.RED)
                    raise typer.Exit(code=1)
            elif not os.access(output_path, os.W_OK):
                 typer.secho(f"Error: Output file '{output_path}' is not writable.", fg=typer.colors.RED)
                 raise typer.Exit(code=1)               

            with open(output_path, 'w') as f:
                f.write(content_to_save)
            typer.secho(f"Workflow result saved to '{output_path}'", fg=typer.colors.GREEN)
            # Documenting mismatched extension and content format as per requirements
            if save_as_json and output_path.suffix.lower() not in ['.json']:
                typer.secho(f"Note: JSON content was saved to a file with extension '{output_path.suffix}'.", fg=typer.colors.YELLOW)
            elif not save_as_json and output_path.suffix.lower() == '.json' and isinstance(result, dict) and not (isinstance(result.get('output'), str)):
                # This case is subtle: result was complex, not string, not dict with output:str, but not saved as JSON (e.g. due to serialization error prior)
                # However, the primary json.dumps path should handle most complex dicts.
                # This is more for if content_to_save ended up being a string representation of a dict that wasn't explicitly JSON.
                pass # Difficult to definitively warn here without more context on what content_to_save is

        except IOError as e:
            typer.secho(f"Error writing to output file '{output_path}': {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        except Exception as e: # Catch any other unexpected errors during file operations
            typer.secho(f"An unexpected error occurred while saving to '{output_path}': {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    else:
        # Existing behavior: print the result to the console
        if isinstance(result, dict):
            output_content = result.get('output')
            if isinstance(output_content, str):
                console = Console()
                console.print(Markdown(output_content))
            else:
                # Fallback: if 'output' key is missing or its content is not a string
                if 'output' in result: # 'output' key exists but content is not a string
                     typer.secho(f"Warning: Content of 'output' key is not a string (type: {type(output_content)}). Displaying raw result.", fg=typer.colors.YELLOW)
                else: # 'output' key is missing
                     typer.secho("Warning: Key 'output' not found in workflow result. Displaying raw result.", fg=typer.colors.YELLOW)
                typer.echo(str(result)) # Print the whole dict for inspection
        elif isinstance(result, str):
            # If the result from run_workflow is already a string (e.g., an error message or simple text output)
            typer.echo(result)
        else:
            # Fallback for other unexpected result types
            typer.secho(f"Warning: Unexpected result type from workflow ({type(result)}). Displaying raw result.", fg=typer.colors.YELLOW)
            typer.echo(str(result))

app.command()(run_workflow_command)

if __name__ == '__main__':
    app()