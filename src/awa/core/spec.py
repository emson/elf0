from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Union, Optional
import yaml
from pathlib import Path

class LLM(BaseModel):
    _type: Literal['openai', 'anthropic', 'ollama']
    model_name: str
    temperature: float = 0.0
    params: Dict[str, Union[str, float, int]] = Field(default_factory=dict)

class Retriever(BaseModel):
    _type: Literal['qdrant', 'redis', 'weaviate']
    collection: str

class Memory(BaseModel):
    _type: Literal['inmemory', 'qdrant', 'postgres']
    namespace: str

class Function(BaseModel):
    _type: Literal['python', 'mcp']
    name: str
    entrypoint: str  # dotted path or MCP URI

class WorkflowNode(BaseModel):
    id: str
    kind: Literal['agent', 'tool', 'judge', 'branch']
    ref: str      # key into llms/functions/sub-workflows
    stop: bool = False

class Edge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None  # python expression on state

class Workflow(BaseModel):
    _type: Literal['sequential', 'react', 'evaluator_optimizer', 'custom_graph']
    nodes: List[WorkflowNode]
    edges: List[Edge]

class Spec(BaseModel):
    version: str = '0.1'
    description: Optional[str] = None
    runtime: Literal['langgraph', 'agentiq'] = 'langgraph'
    llms: Dict[str, LLM]
    retrievers: Dict[str, Retriever] = Field(default_factory=dict)
    memory: Dict[str, Memory] = Field(default_factory=dict)
    functions: Dict[str, Function] = Field(default_factory=dict)
    workflow: Workflow
    eval: Optional[Dict[str, Union[str, List[str]]]] = None

def load_spec(spec_path: str) -> Spec:
    """
    Load and validate a workflow specification from a YAML file.
    
    Args:
        spec_path: Path to the YAML specification file
        
    Returns:
        A validated Spec object
        
    Raises:
        FileNotFoundError: If the spec file doesn't exist
        yaml.YAMLError: If the YAML is invalid
        ValidationError: If the spec doesn't match the schema
    """
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
        
    with path.open() as f:
        data = yaml.safe_load(f)
        
    return Spec.model_validate(data)
    