# src/elf/core/spec.py
from collections.abc import Callable
import json
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
)

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
import yaml

from elf.utils.yaml_loader import load_yaml_file


class CircularReferenceError(Exception):
    """Raised when a circular reference is detected in workflow imports."""


class WorkflowReferenceError(Exception):
    """Raised when there's an error processing workflow references."""


def _clean_markdown_fences(content: str, expected_language: str | None = None) -> str:
    """Removes markdown code fences from content.

    Args:
        content: The content that may be wrapped in markdown code fences
        expected_language: Optional language identifier (e.g., 'yaml', 'json')

    Returns:
        Clean content with markdown fences removed
    """
    cleaned = content.strip()

    # Handle language-specific fences first (e.g., ```yaml, ```json)
    if expected_language:
        fence_start = f"```{expected_language}"
        if cleaned.startswith(fence_start):
            # Remove the language-specific fence start and any following whitespace
            cleaned = cleaned[len(fence_start):].lstrip("\n\r ")
        elif cleaned.startswith("```"):
            # Generic fence handling
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            else:
                # No newline found, just remove the ```
                cleaned = cleaned[3:]
    elif cleaned.startswith("```"):
        # No expected language, handle generic fences
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        else:
            # No newline found, just remove the ```
            cleaned = cleaned[3:]

    # Remove trailing fences
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].rstrip("\n\r ")

    return cleaned.strip()


def _deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override values taking precedence.

    Args:
        base: The base dictionary to merge into
        override: The dictionary whose values override the base

    Returns:
        A new dictionary with merged values

    Raises:
        ValueError: If attempting to merge incompatible types
    """
    result = base.copy()

    for key, value in override.items():
        if key in result:
            base_value = result[key]
            if isinstance(base_value, dict) and isinstance(value, dict):
                result[key] = _deep_merge_dicts(base_value, value)
            elif isinstance(base_value, list) and isinstance(value, list):
                result[key] = value  # Override semantics: replace entire list
            elif type(base_value) is type(value) or base_value is None or value is None:
                result[key] = value  # Override with new value
            else:
                msg = (
                    f"Cannot merge incompatible types at key '{key}': "
                    f"{type(base_value).__name__} and {type(value).__name__}"
                )
                raise ValueError(
                    msg
                )
        else:
            result[key] = value

    return result

class LLM(BaseModel):
    """Configuration for a specific Large Language Model (LLM) instance.

    Defines the type, model name, operational parameters (like temperature),
    and API key for an LLM. This model is referenced by nodes in the workflow
    that require LLM capabilities (e.g., 'agent' or 'judge' nodes).
    """

    type: Literal["openai", "anthropic", "ollama"]
    model_name: str
    temperature: float = 0.7
    params: dict[str, str | float | int] = Field(default_factory=dict)
    api_key: str | None = None

    @field_validator("temperature")
    @classmethod
    def check_temperature(cls, v: float) -> float:
        """Validate that temperature is within valid range."""
        if v < 0 or v > 1:
            msg = "Temperature must be between 0 and 1"
            raise ValueError(msg)
        return v

class Retriever(BaseModel):
    """Configuration for a vector retriever system.

    Specifies the type of retriever (e.g., Qdrant, Redis) and the target
    collection or database to retrieve from. Used for fetching relevant
    context or data for the workflow.
    """

    type: Literal["qdrant", "redis", "weaviate"]
    collection: str

class Memory(BaseModel):
    """Configuration for a memory store.

    Defines the type of memory backend (e.g., in-memory, Qdrant, Postgres)
    and a namespace for isolating data. Used by workflow components that
    need to persist or recall state or conversation history.
    """

    type: Literal["inmemory", "qdrant", "postgres"]
    namespace: str

class Function(BaseModel):
    """Configuration for an external function or tool callable by the workflow.

    Specifies the type of function (e.g., Python module, MCP endpoint), its
    globally unique name (for referencing within the workflow), and the entrypoint
    (e.g., 'module.submodule.function_name' for Python, or a URI for MCP).
    These functions are typically wrapped by 'tool' nodes in the workflow.
    """

    type: Literal["python", "mcp"]
    name: str
    entrypoint: str  # dotted path or MCP URI

    @field_validator("entrypoint")
    @classmethod
    def validate_entrypoint(cls, v: str, info: ValidationInfo) -> str:
        """Check that entrypoint has proper format."""
        # Get the function type from the validation context
        func_type = info.data.get("type")

        if func_type == "python":
            if v.count(".") < 1:
                msg = "Python entrypoint must be in format 'module.function'"
                raise ValueError(msg)
        elif func_type == "mcp":
            if not v.startswith("mcp://"):
                msg = "MCP entrypoint must start with 'mcp://' (e.g., 'mcp://localhost:3000/tool_name')"
                raise ValueError(msg)
            # Additional MCP URI validation
            from urllib.parse import urlparse
            try:
                parsed = urlparse(v)
                if not parsed.netloc:
                    msg = "MCP entrypoint must include server address"
                    raise ValueError(msg)
                if not parsed.path.lstrip("/"):
                    msg = "MCP entrypoint must include tool name in path"
                    raise ValueError(msg)
            except Exception as e:
                msg = f"Invalid MCP entrypoint format: {e!s}"
                raise ValueError(msg)

        return v

class WorkflowNode(BaseModel):
    """Definition of a single node within a workflow graph.

    Each node has a unique `id`, a `kind` (e.g., 'agent', 'tool', 'judge', 'branch')
    that determines its behavior, and a `ref` that points to a specific LLM,
    function, or sub-workflow configuration defined elsewhere in the `Spec`.
    The `stop` flag indicates if the workflow should terminate after this node executes.
    """

    id: str
    kind: Literal["agent", "tool", "judge", "branch", "mcp", "claude_code"]
    ref: str | None = None     # key into llms/functions/sub-workflows (not used for MCP nodes)
    config: dict[str, Any] = Field(default_factory=dict)
    stop: bool = False

class Edge(BaseModel):
    """Definition of a directed edge connecting two nodes in a workflow graph.

    Specifies the `source` node ID and `target` node ID. An optional `condition`
    can be provided as a Python expression string (evaluated against the workflow state)
    to determine if this edge should be traversed. Edges define the control flow.
    """

    source: str
    target: str
    condition: str | None = None  # python expression on state

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str | None) -> str | None:
        """Validate that condition is a valid Python expression."""
        # This is a simple check - in production code you might
        # want more robust validation
        if v is not None and not v.strip():
            msg = "Condition cannot be empty string"
            raise ValueError(msg)
        return v

class Workflow(BaseModel):
    """Definition of the overall workflow structure, including nodes and edges.

    Contains the `type` of workflow pattern (e.g., 'sequential', 'react'), a list
    of `WorkflowNode` definitions, and a list of `Edge` definitions that connect them.
    `max_iterations` can optionally limit the number of cycles in looped workflows.
    This model orchestrates how nodes and edges form the executable graph.
    """

    type: Literal["sequential", "react", "evaluator_optimizer", "custom_graph"]
    nodes: list[WorkflowNode]
    edges: list[Edge]
    max_iterations: int | None = Field(default=None, description="Maximum number of iterations for the workflow loop.")

    @model_validator(mode="after")
    def validate_workflow_structure(self) -> "Workflow":
        """Validate that the workflow has valid structure."""
        # Check that we have at least one node
        if not self.nodes:
            msg = "Workflow must have at least one node"
            raise ValueError(msg)

        # Check that each edge refers to valid nodes
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids:
                msg = f"Edge source '{edge.source}' not found in nodes"
                raise ValueError(msg)
            if edge.target not in node_ids:
                msg = f"Edge target '{edge.target}' not found in nodes"
                raise ValueError(msg)

        return self

class Spec(BaseModel):
    """The main specification model for defining an entire AI workflow.

    This top-level model aggregates all configurations required for a workflow:
    - `version`: Specification version.
    - `description`: Optional textual description of the workflow.
    - `reference`: Optional path to another workflow YAML file to import and merge.
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

    version: str = "0.1"
    description: str | None = None
    reference: str | list[str] | None = None
    runtime: Literal["langgraph", "agentiq"] = "langgraph"
    llms: dict[str, LLM] = Field(default_factory=dict)
    retrievers: dict[str, Retriever] = Field(default_factory=dict)
    memory: dict[str, Memory] = Field(default_factory=dict)
    functions: dict[str, Function] = Field(default_factory=dict)
    workflow: Workflow | None = None
    eval: dict[str, str | list[str]] | None = None

    # Registry of workflow patterns
    _workflow_patterns: ClassVar[dict[str, Callable[..., "Spec"]]] = {}

    @model_validator(mode="after")
    def validate_references(self) -> "Spec":
        """Validate that all references in the workflow exist."""
        # If this spec has a reference field, workflow validation will happen after merging
        if self.reference:
            return self

        # For non-reference specs, workflow is required
        if not self.workflow:
            msg = "Workflow is required when not using a reference"
            raise ValueError(msg)

        # Check that all referenced LLMs exist
        for node in self.workflow.nodes:
            if node.kind in {"agent", "judge"}:
                if not node.ref:
                    msg = f"Node '{node.id}' of kind '{node.kind}' must have a ref field"
                    raise ValueError(msg)
                if node.ref not in self.llms:
                    msg = f"Node '{node.id}' references unknown LLM '{node.ref}'"
                    raise ValueError(msg)
            elif node.kind == "tool":
                if not node.ref:
                    msg = f"Node '{node.id}' of kind 'tool' must have a ref field"
                    raise ValueError(msg)
                if node.ref not in self.functions:
                    msg = f"Node '{node.id}' references unknown function '{node.ref}'"
                    raise ValueError(msg)
            elif node.kind == "mcp":
                # MCP nodes don't use ref field, they use config directly
                if not node.config:
                    msg = f"MCP node '{node.id}' must have configuration"
                    raise ValueError(msg)
                if "server" not in node.config:
                    msg = f"MCP node '{node.id}' must have 'server' configuration"
                    raise ValueError(msg)
                if "tool" not in node.config:
                    msg = f"MCP node '{node.id}' must have 'tool' configuration"
                    raise ValueError(msg)
            elif node.kind == "claude_code":
                # Claude Code nodes use config directly, similar to MCP nodes
                if not node.config:
                    msg = f"Claude Code node '{node.id}' must have configuration"
                    raise ValueError(msg)
                # Basic validation - we'll validate specific fields in the node implementation

        return self

    @classmethod
    def validate_yaml_string(cls, yaml_content: str) -> tuple[bool, Optional["Spec"], str | None]:
        """Validates a YAML string against the Spec schema.

        Args:
            yaml_content: The YAML content as a string (may be wrapped in markdown fences)

        Returns:
            A tuple of (is_valid, spec_object, error_message)
        """
        try:
            # Clean markdown fences from YAML content
            cleaned_yaml = _clean_markdown_fences(yaml_content, "yaml")

            if not cleaned_yaml:
                return False, None, "YAML content is empty after cleaning"

            # Parse YAML content
            data = yaml.safe_load(cleaned_yaml)
            if data is None:
                return False, None, "YAML content is empty or null"

            # Validate against Spec schema
            spec = cls.model_validate(data)
            return True, spec, None

        except yaml.YAMLError as e:
            return False, None, f"YAML parsing error: {e!s}"
        except Exception as e:
            return False, None, f"Validation error: {e!s}"

    @classmethod
    def create_structured_output(cls, yaml_content: str) -> dict[str, Any]:
        """Creates a structured output dictionary that includes validation status and parsed spec.

        Args:
            yaml_content: The YAML content as a string (may be wrapped in markdown fences)

        Returns:
            A dictionary with validation status, spec data, and error information
        """
        # Clean markdown fences for consistent output
        cleaned_yaml = _clean_markdown_fences(yaml_content, "yaml")

        is_valid, spec, error = cls.validate_yaml_string(yaml_content)

        result = {
            "validation": {
                "is_valid": is_valid,
                "error": error
            },
            "yaml_content": cleaned_yaml,
            "raw_content": yaml_content.strip(),
            "spec_data": None
        }

        if spec:
            result["spec_data"] = spec.model_dump(exclude_none=True)

        return result

    def to_yaml_string(self) -> str:
        """Converts the Spec instance to a YAML string.

        Returns:
            YAML representation of the spec
        """
        return yaml.dump(
            self.model_dump(exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )

    @classmethod
    def from_structured_json(cls, json_content: str) -> "Spec":
        """Creates a Spec instance from structured JSON output.

        Args:
            json_content: JSON string containing spec data

        Returns:
            A validated Spec instance

        Raises:
            ValueError: If JSON is invalid or doesn't match Spec schema
        """
        try:
            # Clean markdown fences if present
            cleaned_json = _clean_markdown_fences(json_content, "json")

            # Parse JSON
            data = json.loads(cleaned_json)

            # Validate and return Spec
            return cls.model_validate(data)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON: {e!s}"
            raise ValueError(msg)
        except Exception as e:
            msg = f"Spec validation error: {e!s}"
            raise ValueError(msg)

    @classmethod
    def get_json_schema_for_structured_output(cls) -> dict[str, Any]:
        """Returns the JSON schema for this Spec model, formatted for LLM structured output.

        Returns:
            JSON schema dictionary suitable for OpenAI structured output
        """
        return cls.model_json_schema()

    @classmethod
    def from_file(cls, spec_path: str, visited: set[Path] | None = None) -> "Spec":
        """Loads, parses, and validates a workflow specification from a YAML file.

        Supports recursive loading with reference resolution and circular detection.

        This method takes a file path to a YAML specification, reads its content,
        and then uses Pydantic's `model_validate` to parse the data into a `Spec`
        object. If the spec contains a `reference` field, it will recursively load
        and merge the referenced specification.

        Args:
            spec_path: The string path to the YAML specification file.
            visited: Set of already visited paths for circular reference detection.

        Returns:
            A validated `Spec` instance representing the workflow.

        Raises:
            FileNotFoundError: If the YAML file specified by `spec_path` does not exist.
            CircularReferenceError: If a circular reference is detected.
            WorkflowReferenceError: If there's an error processing references.
            pydantic.ValidationError: If the content of the YAML file does not conform
                                    to the `Spec` schema or fails any custom validation rules.
        """
        if visited is None:
            visited = set()

        # Resolve to absolute path for consistent comparison
        path = Path(spec_path).resolve()

        # Check for circular references
        if path in visited:
            cycle_path = " -> ".join(str(p) for p in visited) + f" -> {path}"
            msg = f"Circular reference detected in workflow chain: {cycle_path}"
            raise CircularReferenceError(msg)

        # Check if file exists
        if not path.exists():
            msg = f"Referenced file not found: {spec_path}"
            raise FileNotFoundError(msg)

        # Add current path to visited set
        visited.add(path)

        try:
            # Load YAML data
            data = load_yaml_file(str(path))

            # Check if this spec has a reference
            if data.get("reference"):
                references_input = data["reference"]
                current_data_for_merging = {k: v for k, v in data.items() if k != "reference"}

                accumulated_base_data: dict[str, Any] = {}

                if isinstance(references_input, str):
                    # Single reference string
                    reference_paths = [references_input]
                elif isinstance(references_input, list):
                    # List of reference strings
                    reference_paths = references_input
                else:
                    msg = f"Invalid format for 'reference' in {spec_path}. Must be a string or a list of strings."
                    raise WorkflowReferenceError(
                        msg
                    )

                for _i, ref_path_str in enumerate(reference_paths):
                    if not isinstance(ref_path_str, str):
                        msg = f"Invalid reference path in {spec_path}. All items in reference list must be strings. Found: {type(ref_path_str)}"
                        raise WorkflowReferenceError(
                            msg
                        )

                    # Resolve reference path (relative to current file's directory)
                    resolved_ref_path = Path(ref_path_str)
                    if not resolved_ref_path.is_absolute():
                        resolved_ref_path = path.parent / resolved_ref_path

                    try:
                        # Recursively load the referenced spec
                        # For the first reference, it becomes the base.
                        # For subsequent references, they merge into the accumulated base.
                        referenced_spec = cls.from_file(str(resolved_ref_path), visited.copy())
                        new_data_to_merge = referenced_spec.model_dump(exclude_none=True)

                        if not accumulated_base_data: # First reference
                            accumulated_base_data = new_data_to_merge
                        else: # Subsequent references merge into the current accumulated base
                            accumulated_base_data = _deep_merge_dicts(accumulated_base_data, new_data_to_merge)

                    except Exception as e:
                        if isinstance(e, CircularReferenceError | FileNotFoundError | WorkflowReferenceError):
                            raise
                        msg = f"Error processing reference '{resolved_ref_path}' from file '{spec_path}': {e!s}"
                        raise WorkflowReferenceError(msg) from e

                # Merge the current spec's data on top of all accumulated base data
                final_merged_data = _deep_merge_dicts(accumulated_base_data, current_data_for_merging)

                # Validate and return the merged spec
                return cls.model_validate(final_merged_data)
            # No reference, validate directly
            return cls.model_validate(data)

        finally:
            # Remove current path from visited set
            visited.discard(path)

    @classmethod
    def register_workflow_pattern(cls, name: str, workflow_factory: Callable[..., "Spec"]) -> None:
        """Registers a factory function for creating `Spec` instances from predefined patterns.

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
    def create_from_pattern(cls, pattern: str, **kwargs: object) -> "Spec":
        """Creates a `Spec` instance using a previously registered workflow pattern factory.

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
            msg = f"Unknown workflow pattern: {pattern}"
            raise ValueError(msg)

        factory = cls._workflow_patterns[pattern]
        return factory(**kwargs)

def load_spec(spec_path: str) -> Spec:
    """Loads, parses, and validates a workflow specification from a YAML file.

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
def create_sequential_workflow(nodes: list[dict[str, Any]]) -> Workflow:
    """Constructs a `Workflow` object representing a simple sequential flow.

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
    edges = [
        Edge(
            source=workflow_nodes[i].id,
            target=workflow_nodes[i + 1].id
        )
        for i in range(len(workflow_nodes) - 1)
    ]

    # Mark last node as a stop node
    if workflow_nodes:
        workflow_nodes[-1].stop = True

    return Workflow(
        type="sequential",
        nodes=workflow_nodes,
        edges=edges
    )

def create_react_workflow(agent_node: dict[str, Any], tools: list[dict[str, Any]]) -> Workflow:
    """Creates a `Workflow` object structured for a ReAct (Reasoning and Acting) pattern.

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
    edges: list[Edge] = []

    return Workflow(
        type="react",
        nodes=workflow_nodes,
        edges=edges
    )

# Factory function to create a new Spec from a sequential workflow
def create_sequential_spec(
    name: str,
    description: str,
    llm_config: dict[str, Any],
    nodes: list[dict[str, Any]]
) -> Spec:
    """Factory function to create a complete `Spec` for a sequential workflow.

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
