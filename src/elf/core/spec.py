# src/elf/core/spec.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, List, Dict, Union, Optional, ClassVar, Any, Callable
from pathlib import Path
from ..utils.yaml_loader import load_yaml_file

class LLM(BaseModel):
    """Configuration for a language model."""
    
    type: Literal['openai', 'anthropic', 'ollama']
    model_name: str
    temperature: float = 0.7
    params: Dict[str, Union[str, float, int]] = Field(default_factory=dict)
    api_key: Optional[str] = None
    
    @field_validator('temperature')
    def check_temperature(cls, v: float) -> float:
        """Validate that temperature is within valid range."""
        if v < 0 or v > 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

class Retriever(BaseModel):
    """Configuration for a vector retriever."""
    
    type: Literal['qdrant', 'redis', 'weaviate']
    collection: str

class Memory(BaseModel):
    """Configuration for a memory store."""
    
    type: Literal['inmemory', 'qdrant', 'postgres']
    namespace: str

class Function(BaseModel):
    """Configuration for a function or tool."""
    
    type: Literal['python', 'mcp']
    name: str
    entrypoint: str  # dotted path or MCP URI
    
    @field_validator('entrypoint')
    def validate_entrypoint(cls, v: str) -> str:
        """Check that entrypoint has proper format."""
        if v.count('.') < 1 and cls.type == 'python':
            raise ValueError("Python entrypoint must be in format 'module.function'")
        return v

class WorkflowNode(BaseModel):
    """Definition of a workflow node."""
    
    id: str
    kind: Literal['agent', 'tool', 'judge', 'branch']
    ref: str      # key into llms/functions/sub-workflows
    stop: bool = False

class Edge(BaseModel):
    """Definition of an edge between workflow nodes."""
    
    source: str
    target: str
    condition: Optional[str] = None  # python expression on state
    
    @field_validator('condition')
    def validate_condition(cls, v: Optional[str]) -> Optional[str]:
        """Validate that condition is a valid Python expression."""
        # This is a simple check - in production code you might 
        # want more robust validation
        if v is not None and not v.strip():
            raise ValueError("Condition cannot be empty string")
        return v

class Workflow(BaseModel):
    """Definition of a workflow graph."""
    
    type: Literal['sequential', 'react', 'evaluator_optimizer', 'custom_graph']
    nodes: List[WorkflowNode]
    edges: List[Edge]
    max_iterations: Optional[int] = Field(default=None, description="Maximum number of iterations for the workflow loop.")
    
    @model_validator(mode='after')
    def validate_workflow_structure(self) -> 'Workflow':
        """Validate that the workflow has valid structure."""
        # Check that we have at least one node
        if not self.nodes:
            raise ValueError("Workflow must have at least one node")
            
        # Check that each edge refers to valid nodes
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                raise ValueError(f"Edge target '{edge.target}' not found in nodes")
                
        return self

class Spec(BaseModel):
    """Main workflow specification."""
    
    version: str = '0.1'
    description: Optional[str] = None
    runtime: Literal['langgraph', 'agentiq'] = 'langgraph'
    llms: Dict[str, LLM]
    retrievers: Dict[str, Retriever] = Field(default_factory=dict)
    memory: Dict[str, Memory] = Field(default_factory=dict)
    functions: Dict[str, Function] = Field(default_factory=dict)
    workflow: Workflow
    eval: Optional[Dict[str, Union[str, List[str]]]] = None
    
    # Registry of workflow patterns
    _workflow_patterns: ClassVar[Dict[str, Callable[..., 'Spec']]] = {}
    
    @model_validator(mode='after')
    def validate_references(self) -> 'Spec':
        """Validate that all references in the workflow exist."""
        # Check that all referenced LLMs exist
        for node in self.workflow.nodes:
            if node.kind == 'agent' or node.kind == 'judge':
                if node.ref not in self.llms:
                    raise ValueError(f"Node '{node.id}' references unknown LLM '{node.ref}'")
            elif node.kind == 'tool':
                if node.ref not in self.functions:
                    raise ValueError(f"Node '{node.id}' references unknown function '{node.ref}'")
                    
        return self
    
    @classmethod
    def from_file(cls, spec_path: str) -> 'Spec':
        """
        Load and validate a workflow specification from a YAML file.
        
        Args:
            spec_path: Path to the YAML specification file
            
        Returns:
            A validated Spec object
            
        Raises:
            FileNotFoundError: If the spec file doesn't exist
            ValidationError: If the spec doesn't match the schema
        """
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
            
        data = load_yaml_file(spec_path)
        return cls.model_validate(data)
    
    @classmethod
    def register_workflow_pattern(cls, name: str, workflow_factory: Callable[..., 'Spec']) -> None:
        """
        Register a workflow pattern factory.
        
        Args:
            name: The name of the pattern
            workflow_factory: A function that creates a workflow pattern
        """
        cls._workflow_patterns[name] = workflow_factory
    
    @classmethod
    def create_from_pattern(cls, pattern: str, **kwargs: Any) -> 'Spec':
        """
        Create a specification from a registered pattern.
        
        Args:
            pattern: The name of the pattern to use
            **kwargs: Parameters to pass to the pattern factory
            
        Returns:
            A Spec instance configured for the pattern
            
        Raises:
            ValueError: If the pattern is not registered
        """
        if pattern not in cls._workflow_patterns:
            raise ValueError(f"Unknown workflow pattern: {pattern}")
            
        factory = cls._workflow_patterns[pattern]
        return factory(**kwargs)

def load_spec(spec_path: str) -> Spec:
    """
    Load and validate a workflow specification from a YAML file.
    
    Args:
        spec_path: Path to the YAML specification file
        
    Returns:
        A validated Spec object
        
    Raises:
        FileNotFoundError: If the spec file doesn't exist
        ValidationError: If the spec doesn't match the schema
    """
    return Spec.from_file(spec_path)

# Convenience factory methods for common workflow patterns
def create_sequential_workflow(nodes: List[Dict[str, Any]]) -> Workflow:
    """
    Create a sequential workflow where each node connects to the next.
    
    Args:
        nodes: List of node configurations
        
    Returns:
        A configured Workflow
    """
    workflow_nodes = [WorkflowNode.model_validate(node) for node in nodes]
    
    # Create edges connecting each node to the next
    edges = []
    for i in range(len(workflow_nodes) - 1):
        edges.append(Edge(
            source=workflow_nodes[i].id,
            target=workflow_nodes[i + 1].id
        ))
    
    # Mark last node as a stop node
    if workflow_nodes:
        workflow_nodes[-1].stop = True
    
    return Workflow(
        type='sequential',
        nodes=workflow_nodes,
        edges=edges
    )

def create_react_workflow(agent_node: Dict[str, Any], tools: List[Dict[str, Any]]) -> Workflow:
    """
    Create a ReAct pattern workflow.
    
    Args:
        agent_node: Configuration for the agent node
        tools: List of tool configurations
        
    Returns:
        A configured Workflow
    """
    # TODO: Implement actual ReAct pattern
    workflow_nodes = [WorkflowNode.model_validate(agent_node)]
    workflow_nodes.extend(WorkflowNode.model_validate(tool) for tool in tools)
    
    # Create basic connections
    edges: List[Edge] = []
    
    return Workflow(
        type='react',
        nodes=workflow_nodes,
        edges=edges
    )

# Factory function to create a new Spec from a sequential workflow
def create_sequential_spec(
    name: str, 
    description: str,
    llm_config: Dict[str, Any],
    nodes: List[Dict[str, Any]]
) -> Spec:
    """
    Create a new specification with a sequential workflow.
    
    Args:
        name: The name of the workflow
        description: A description of the workflow
        llm_config: Configuration for the LLM
        nodes: List of node configurations
        
    Returns:
        A complete Spec instance
    """
    llm = LLM.model_validate(llm_config)
    workflow = create_sequential_workflow(nodes)
    
    return Spec(
        description=description,
        llms={name: llm},
        workflow=workflow
    )