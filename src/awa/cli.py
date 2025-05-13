import typer
from pathlib import Path
from awa.core.runner import run_workflow

app = typer.Typer(
    name="awa",
    help="AI Workflow Architect - Execute and optimize LLM-powered agent workflows",
    add_completion=False
)

def run_workflow_command(
    spec_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help='Path to YAML spec'),
    prompt: str = typer.Option(..., help='User prompt to process'),
    session_id: str = typer.Option('session', help='Session identifier for stateful runs')
):
    """
    Execute an agent workflow defined in YAML.
    
    Example:
        awa workflow.yaml --prompt "What is the weather in London?"
    """
    result = run_workflow(spec_path, prompt, session_id)
    typer.echo(result)

app.command()(run_workflow_command)

if __name__ == '__main__':
    app()