from pathlib import Path
from typing import Any

from elf.core.compiler import compile_to_langgraph
from elf.core.spec import load_spec

from .exceptions import UserExitRequested


def run_workflow(spec_path: Path, prompt: str, session_id: str) -> dict[str, Any]:
    """Run a workflow defined in a YAML spec file.

    Args:
        spec_path: Path to the YAML spec file
        prompt: User prompt to process
        session_id: Unique identifier for this workflow run

    Returns:
        The final state of the workflow execution

    Raises:
        UserExitRequested: When user requests to exit via /exit, /quit, or /bye
    """
    try:
        # Load and validate the spec
        spec = load_spec(str(spec_path))

        # Compile to appropriate runtime
        if spec.runtime == "langgraph":
            graph = compile_to_langgraph(spec)
            # For LangGraph 0.4.3, we need to compile the graph first
            compiled = graph.compile()
            # Then we can invoke it
            result = compiled.invoke(
                {"input": prompt},
                config={"configurable": {"thread_id": session_id}}
            )

            # Check if user requested to exit during workflow execution
            if result.get("user_exit_requested"):
                msg = "User requested to exit during workflow execution"
                raise UserExitRequested(msg)

            return result
        msg = f"Unsupported runtime: {spec.runtime}"
        raise ValueError(msg)

    except UserExitRequested:
        # Re-raise to let the CLI handle the exit gracefully
        raise
