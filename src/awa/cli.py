import typer
from pathlib import Path
from typing import List, Optional
from awa.core.runner import run_workflow
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer(
    name="awa",
    help="AI Workflow Architect - Execute and optimize LLM-powered agent workflows",
    add_completion=False
)

def run_workflow_command(
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec'),
    prompt: str = typer.Option(..., help='User prompt to process'),
    session_id: str = typer.Option('session', help='Session identifier for stateful runs'),
    context_files: Optional[List[Path]] = typer.Option(None, "--context", help="Path to context file(s). Can be specified multiple times or as a comma-separated list. File contents will be added to the prompt.", show_default=False)
):
    """
    Execute an agent workflow defined in YAML.
    
    Example:
        awa workflow.yaml --prompt "What is the weather in London?"
        awa workflow.yaml --prompt "Summarize these files" --context file1.txt --context dir/file2.py
        awa workflow.yaml --prompt "Explain this code" --context file1.py,file2.py
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
    # typer.echo(result) # This line is replaced by the logic below.
    
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