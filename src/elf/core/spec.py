# src/elf/core/spec.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, List, Dict, Union, Optional, ClassVar, Any, Callable
from pathlib import Path
from ..utils.yaml_loader import load_yaml_file

class LLM(BaseModel):
    """Configuration for a specific Large Language Model (LLM) instance.
    
    Defines the type, model name, operational parameters (like temperature),
    and API key for an LLM. This model is referenced by nodes in the workflow
    that require LLM capabilities (e.g., 'agent' or 'judge' nodes).
    """
    
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
    """Configuration for a vector retriever system.
    
    Specifies the type of retriever (e.g., Qdrant, Redis) and the target
    collection or database to retrieve from. Used for fetching relevant
    context or data for the workflow.
    """
    
    type: Literal['qdrant', 'redis', 'weaviate']
    collection: str

class Memory(BaseModel):
    """Configuration for a memory store.
    
    Defines the type of memory backend (e.g., in-memory, Qdrant, Postgres)
    and a namespace for isolating data. Used by workflow components that
    need to persist or recall state or conversation history.
    """
    
    type: Literal['inmemory', 'qdrant', 'postgres']
    namespace: str

class Function(BaseModel):
    """Configuration for an external function or tool callable by the workflow.
    
    Specifies the type of function (e.g., Python module, MCP endpoint), its
    globally unique name (for referencing within the workflow), and the entrypoint
    (e.g., 'module.submodule.function_name' for Python, or a URI for MCP).
    These functions are typically wrapped by 'tool' nodes in the workflow.
    """
    
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
    """Definition of a single node within a workflow graph.
    
    Each node has a unique `id`, a `kind` (e.g., 'agent', 'tool', 'judge', 'branch')
    that determines its behavior, and a `ref` that points to a specific LLM,
    function, or sub-workflow configuration defined elsewhere in the `Spec`.
    The `stop` flag indicates if the workflow should terminate after this node executes.
    """
    
    id: str
    kind: Literal['agent', 'tool', 'judge', 'branch']
    ref: str      # key into llms/functions/sub-workflows
    stop: bool = False

class Edge(BaseModel):
    """Definition of a directed edge connecting two nodes in a workflow graph.
    
    Specifies the `source` node ID and `target` node ID. An optional `condition`
    can be provided as a Python expression string (evaluated against the workflow state)
    to determine if this edge should be traversed. Edges define the control flow.
    """
    
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
    """Definition of the overall workflow structure, including nodes and edges.
    
    Contains the `type` of workflow pattern (e.g., 'sequential', 'react'), a list
    of `WorkflowNode` definitions, and a list of `Edge` definitions that connect them.
    `max_iterations` can optionally limit the number of cycles in looped workflows.
    This model orchestrates how nodes and edges form the executable graph.
    """
    
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
    """The main specification model for defining an entire AI workflow.
    
    This top-level model aggregates all configurations required for a workflow:
    - `version`: Specification version.
    - `description`: Optional textual description of the workflow.
    - `runtime`: Target execution runtime (e.g., 'langgraph').
    - `llms`: A dictionary of named `LLM` configurations.
    - `retrievers`: A dictionary of named `Retriever` configurations.
    - `memory`: A dictionary of named `Memory` configurations.
    - `functions`: A dictionary of named `Function` (tool) configurations.
    - `workflow`: A `Workflow` model instance defining the graph structure (nodes and edges).
    - `eval`: Optional evaluation configuration.
    
    It includes validation logic to ensure references within the workflow (e.g., from a
    node to an LLM or function) are valid. It also provides class methods for loading
    from a file (`from_file`) and for creating specs from predefined patterns.
    """
    
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
        Loads, parses, and validates a workflow specification from a YAML file.

        This method takes a file path to a YAML specification, reads its content,
        and then uses Pydantic's `model_validate` to parse the data into a `Spec`
        object. This process includes all validations defined within the `Spec` model
        and its nested models (e.g., `LLM`, `WorkflowNode`, `Edge`).
        
        Args:
            spec_path: The string path to the YAML specification file.
            
        Returns:
            A validated `Spec` instance representing the workflow.
            
        Raises:
            FileNotFoundError: If the YAML file specified by `spec_path` does not exist.
            pydantic.ValidationError: If the content of the YAML file does not conform
                                    to the `Spec` schema or fails any custom validation rules.
        """
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
            
        data = load_yaml_file(spec_path)
        return cls.model_validate(data)
    
    @classmethod
    def register_workflow_pattern(cls, name: str, workflow_factory: Callable[..., 'Spec']) -> None:
        """
        Registers a factory function for creating `Spec` instances from predefined patterns.

        Workflow patterns provide a way to encapsulate common workflow structures.
        The `workflow_factory` is a callable that accepts pattern-specific arguments
        and returns a fully configured `Spec` object.
        Registered patterns can be instantiated using `Spec.create_from_pattern()`.
        
        Args:
            name: The unique string name to identify this workflow pattern.
            workflow_factory: A callable (function or class method) that, when called,
                              returns a `Spec` instance configured according to the pattern.
        """
        cls._workflow_patterns[name] = workflow_factory
    
    @classmethod
    def create_from_pattern(cls, pattern: str, **kwargs: Any) -> 'Spec':
        """
        Creates a `Spec` instance using a previously registered workflow pattern factory.

        This method looks up a pattern by its `name` in the internal registry
        and calls the associated factory function, passing any `**kwargs` to it.
        This allows for quick instantiation of complex workflows based on templates.
        
        Args:
            pattern: The string name of the workflow pattern to use (must be registered
                     via `Spec.register_workflow_pattern()`).
            **kwargs: Arbitrary keyword arguments that will be passed directly to the
                      pattern's factory function.
            
        Returns:
            A `Spec` instance configured by the specified pattern factory.
            
        Raises:
            ValueError: If the provided `pattern` name is not found in the registry. 
        """
        if pattern not in cls._workflow_patterns:
            raise ValueError(f"Unknown workflow pattern: {pattern}")
            
        factory = cls._workflow_patterns[pattern]
        return factory(**kwargs)

def load_spec(spec_path: str) -> Spec:
    """
    Loads, parses, and validates a workflow specification from a YAML file.

    This is a convenience function that directly calls `Spec.from_file(spec_path)`.
    It provides a simple, top-level function for loading specifications.
    
    Args:
        spec_path: The string path to the YAML specification file.
        
    Returns:
        A validated `Spec` instance.
        
    Raises:
        FileNotFoundError: If the YAML file does not exist.
        pydantic.ValidationError: If the YAML content is invalid against the `Spec` schema.
    """
    return Spec.from_file(spec_path)

# Convenience factory methods for common workflow patterns
def create_sequential_workflow(nodes: List[Dict[str, Any]]) -> Workflow:
    """
    Constructs a `Workflow` object representing a simple sequential flow.

    Nodes are connected in the order they appear in the `nodes` list.
    The last node in the sequence is automatically marked as a `stop` node.
    
    Args:
        nodes: A list of dictionaries, where each dictionary is a configuration
               for a `WorkflowNode` (will be validated by `WorkflowNode.model_validate`).
               Each dictionary must contain at least an `id` and `kind`.
        
    Returns:
        A `Workflow` instance configured with the given nodes connected sequentially.
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
    Creates a `Workflow` object structured for a ReAct (Reasoning and Acting) pattern.

    Note: The current implementation is a placeholder. A full ReAct pattern
    would typically involve an agent node that can choose among several tool nodes,
    potentially looping back to itself after a tool executes. This factory would
    set up the necessary nodes and conditional edges for such a loop.
    
    Args:
        agent_node: Configuration dictionary for the central agent `WorkflowNode`.
        tools: A list of configuration dictionaries for the tool `WorkflowNode`s
               available to the agent.
        
    Returns:
        A `Workflow` instance. (Currently basic, needs full ReAct logic).
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
    Factory function to create a complete `Spec` for a sequential workflow.

    This helper function simplifies the creation of a `Spec` where the workflow
    consists of a linear sequence of nodes. It takes high-level configuration
    for the workflow's name, description, a single LLM configuration, and the
    list of nodes that will form the sequence.
    
    Args:
        name: A name for the workflow, also used as the key for the LLM in `spec.llms`.
        description: A textual description for the `Spec`.
        llm_config: A dictionary configuring a single `LLM` instance for this workflow.
        nodes: A list of dictionaries, each configuring a `WorkflowNode` for the
               sequential workflow (passed to `create_sequential_workflow`).
        
    Returns:
        A fully populated `Spec` instance with the specified sequential workflow. 
    """
    llm = LLM.model_validate(llm_config)
    workflow = create_sequential_workflow(nodes)
    
    return Spec(
        description=description,
        llms={name: llm},
        workflow=workflow
    )