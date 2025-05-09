# Location: src/awa/cli.py

import typer
from pathlib import Path
from typing import Optional
import sys

app = typer.Typer(
    name="awa",
    help="🤖 AWA - AI Workflow Architect",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

@app.command()
def run(
    workflow_file: Path = typer.Argument(
        ...,  # Required argument
        help="Path to the workflow YAML file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed execution information"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate workflow execution without running"
    ),
):
    """
    Execute a workflow from a YAML configuration file

    Args:
        workflow_file: Path to the workflow YAML file
        verbose: Show detailed execution information
        dry_run: Simulate workflow execution without running
    """
    if dry_run:
        typer.secho("[DRY RUN]", fg=typer.colors.YELLOW, bold=True)
        typer.echo(f"Would run workflow from: {workflow_file}")
    else:
        typer.secho("TODO: Implement workflow execution", fg=typer.colors.CYAN)
        typer.echo(f"Workflow file: {workflow_file}")
        if verbose:
            typer.echo("\n[Verbose mode enabled]")
            typer.echo(f"Absolute path: {workflow_file.absolute()}")
            typer.echo(f"File size: {workflow_file.stat().st_size} bytes")

def main():
    """Main entry point for the AWA CLI"""
    if len(sys.argv) == 1:
        typer.echo("AWA - Advanced Workflow Automation")
        typer.echo("\nUsage:")
        typer.echo("  awa run <workflow_file>")
        typer.echo("  awa --help")
        typer.echo("\nOptions:")
        typer.echo("  --verbose, -v    Show detailed execution information")
        typer.echo("  --dry-run        Simulate workflow execution without running")
        typer.echo("  --help           Show this message and exit")
        return
    
    app()

if __name__ == "__main__":
    main()
