from pathlib import Path
from typing import Any, Dict
from elf.core.spec import load_spec
from elf.core.compiler import compile_to_langgraph

def run_workflow(spec_path: Path, prompt: str, session_id: str) -> Dict[str, Any]:
    """
    Run a workflow defined in a YAML spec file.
    
    Args:
        spec_path: Path to the YAML spec file
        prompt: User prompt to process
        session_id: Unique identifier for this workflow run
        
    Returns:
        The final state of the workflow execution
    """
    # Load and validate the spec
    spec = load_spec(str(spec_path))
    
    # Compile to appropriate runtime
    if spec.runtime == 'langgraph':
        graph = compile_to_langgraph(spec)
        # For LangGraph 0.4.3, we need to compile the graph first
        compiled = graph.compile()
        # Then we can invoke it
        result = compiled.invoke(
            {'input': prompt},
            config={'configurable': {'thread_id': session_id}}
        )
        return result
    else:
        raise ValueError(f"Unsupported runtime: {spec.runtime}")