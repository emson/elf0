# Location: src/awa/cli.py

import typer
import asyncio
from pathlib import Path
from typing import Optional
import sys
import logging
import json

from awa.core.workflow_executor import WorkflowExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("awa.cli")

app = typer.Typer(
    name="awa",
    help="🤖 AWA - AI Workflow Architect",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

async def execute_workflow(
    workflow_file: Path,
    input_message: str,
    verbose: bool
) -> dict:
    """Execute a workflow with the provided input.

    Args:
        workflow_file: Path to the workflow YAML file
        input_message: Input message for the workflow
        verbose: Whether to show verbose output

    Returns:
        The workflow execution result
    """
    # Initialize the workflow executor
    executor = WorkflowExecutor(workflow_file)

    # Prepare the input data
    input_data = {"message": input_message}

    # Execute the workflow
    if verbose:
        logger.info(f"Executing workflow with input: {input_data}")

    result = await executor.execute(input_data)
    return result

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
    prompt: str = typer.Option(
        None, "--prompt", "-p", help="Input prompt for the workflow"
    ),
    prompt_file: Optional[Path] = typer.Option(
        None, "--prompt-file", "-f", help="File containing the input prompt",
        exists=False, file_okay=True, dir_okay=False
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed execution information"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate workflow execution without running"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="File to save the output to"
    ),
):
    """
    Execute a workflow from a YAML configuration file

    Args:
        workflow_file: Path to the workflow YAML file
        prompt: Input prompt for the workflow
        prompt_file: File containing the input prompt
        verbose: Show detailed execution information
        dry_run: Simulate workflow execution without running
        output_file: File to save the output to
    """
    # Set log level based on verbose flag
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    # Get input prompt
    input_message = ""
    if prompt and prompt_file:
        typer.secho("Error: Please provide either --prompt or --prompt-file, not both",
                    fg=typer.colors.RED)
        raise typer.Exit(1)
    elif prompt:
        input_message = prompt
    elif prompt_file:
        try:
            if not prompt_file.exists():
                typer.secho(f"Error: Prompt file not found: {prompt_file}",
                            fg=typer.colors.RED)
                raise typer.Exit(1)
            input_message = prompt_file.read_text().strip()
        except Exception as e:
            typer.secho(f"Error reading prompt file: {str(e)}", fg=typer.colors.RED)
            raise typer.Exit(1)
    else:
        # If no prompt is provided, ask for it interactively
        typer.echo("Enter your prompt (press Ctrl+D when finished):")
        input_lines = []
        try:
            while True:
                line = input()
                input_lines.append(line)
        except EOFError:
            input_message = "\n".join(input_lines)

    if dry_run:
        typer.secho("[DRY RUN]", fg=typer.colors.YELLOW, bold=True)
        typer.echo(f"Would run workflow from: {workflow_file}")
        typer.echo(f"With input: {input_message[:100]}{'...' if len(input_message) > 100 else ''}")
    else:
        typer.secho(f"Running workflow: {workflow_file.name}", fg=typer.colors.CYAN)

        if verbose:
            typer.echo("\n[Verbose mode enabled]")
            typer.echo(f"Absolute path: {workflow_file.absolute()}")
            typer.echo(f"File size: {workflow_file.stat().st_size} bytes")
            typer.echo(f"Input message: {input_message[:200]}{'...' if len(input_message) > 200 else ''}")

        try:
            # Run the workflow
            result = asyncio.run(execute_workflow(workflow_file, input_message, verbose))

            # Display the result
            if isinstance(result, dict) and "content" in result:
                output = result["content"]
                typer.echo("\n--- Workflow Result ---")
                typer.echo(output)
            else:
                typer.echo("\n--- Workflow Result ---")
                typer.echo(result)

            # Save the output if requested
            if output_file:
                try:
                    with open(output_file, 'w') as f:
                        if isinstance(result, dict):
                            json.dump(result, f, indent=2)
                        else:
                            f.write(str(result))
                    typer.secho(f"Output saved to: {output_file}", fg=typer.colors.GREEN)
                except Exception as e:
                    typer.secho(f"Error saving output: {str(e)}", fg=typer.colors.RED)

        except Exception as e:
            typer.secho(f"Error executing workflow: {str(e)}", fg=typer.colors.RED)
            logger.exception("Workflow execution failed")
            raise typer.Exit(1)

def main():
    """Main entry point for the AWA CLI"""
    if len(sys.argv) == 1:
        typer.echo("AWA - AI Workflow Architect")
        typer.echo("\nUsage:")
        typer.echo("  awa run <workflow_file> [options]")
        typer.echo("  awa --help")
        typer.echo("\nOptions:")
        typer.echo("  --prompt, -p TEXT         Input prompt for the workflow")
        typer.echo("  --prompt-file, -f PATH    File containing the input prompt")
        typer.echo("  --verbose, -v             Show detailed execution information")
        typer.echo("  --dry-run                 Simulate workflow execution without running")
        typer.echo("  --output, -o PATH         File to save the output to")
        typer.echo("  --help                    Show this message and exit")
        return

    app()

if __name__ == "__main__":
    main()
