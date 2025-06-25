# src/elf0/core/compiler.py
import asyncio
from collections.abc import Callable
import json
import logging
from typing import Any, Protocol, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from .config import create_llm_config
from .exceptions import UserExitRequested, WorkflowValidationError
from .function_loader import function_loader
from .llm_client import LLMClient
from .spec import Edge, Spec, WorkflowNode

# Configure logging (This section will be removed)
# Default max iterations if not specified in the spec's workflow
DEFAULT_MAX_ITERATIONS = 7


class SafeNamespace:
    """A namespace that returns empty string for missing attributes instead of raising AttributeError."""

    def __init__(self, data: dict[str, Any]):
        self._data = {k: v for k, v in data.items() if isinstance(k, str)}

    def __getattr__(self, name: str) -> Any:
        # First check regular state fields
        if name in self._data:
            return self._data[name]
        # Then check dynamic_state for output_key fields
        dynamic_state = self._data.get("dynamic_state", {})
        if dynamic_state and isinstance(dynamic_state, dict) and name in dynamic_state:
            return dynamic_state[name]
        return ""

    def __contains__(self, key: str) -> bool:
        if key in self._data:
            return True
        dynamic_state = self._data.get("dynamic_state", {})
        return dynamic_state and isinstance(dynamic_state, dict) and key in dynamic_state

    def __getitem__(self, key: str) -> Any:
        return self.__getattr__(key)

    def get(self, key: str, default: Any = "") -> Any:
        return self.__getattr__(key) if self.__contains__(key) else default

# Get a logger specific to elf.core.compiler. The CLI's --quiet flag will target 'elf.core'.
logger = logging.getLogger(__name__) # This will be 'elf.core.compiler'

class WorkflowState(TypedDict):
    """Represents the shared state of the workflow, passed between and modified by nodes."""
    input: str
    output: str | None
    iteration_count: int | None
    evaluation_score: float | None
    # Optional workflow metadata fields for enhanced tracking
    workflow_id: str | None
    current_node: str | None
    error_context: str | None
    # User interaction fields
    user_exit_requested: bool | None  # Flag when user requests to exit
    # Structured output validation fields
    structured_output: dict[str, Any] | None
    validation_status: str | None  # 'valid', 'invalid', 'error', or None
    validation_error: str | None
    # Format processing fields
    structured_data: dict[str, Any] | None
    raw_json: str | None
    format_status: str | None  # 'converted', 'error', or None
    format_error: str | None
    # Claude Code integration fields
    claude_code_result: dict[str, Any] | None
    # Dynamic fields for output_key support - stores custom node outputs
    dynamic_state: dict[str, Any] | None

class NodeFunction(Protocol):
    """Protocol defining the interface for node functions."""
    def __call__(self, state: WorkflowState) -> WorkflowState: ...

class NodeFactory(Protocol):
    """Protocol defining the interface for node factory functions."""
    def __call__(self, spec: Spec, node: WorkflowNode) -> NodeFunction: ...

def _create_llm_client(spec: Spec, node: WorkflowNode) -> LLMClient:
    """Creates and configures an `LLMClient` instance based on LLM specifications.

    This helper function retrieves LLM configuration from `spec.llms` using `node.ref`.
    It ensures the referenced LLM spec exists and contains a 'type' attribute.
    It then uses `create_llm_config` to resolve API keys and other LLM parameters,
    populating the Pydantic model instance for the LLM before creating the `LLMClient`.

    Args:
        spec: The full workflow specification, containing LLM definitions in `spec.llms`.
        node: The `WorkflowNode` that references the LLM to be configured.

    Returns:
        A fully configured `LLMClient` instance.

    Raises:
        ValueError: If the LLM reference in `node.ref` is not found in `spec.llms`,
                    or if the LLM configuration is missing the required 'type' attribute.
    """
    if node.ref not in spec.llms:
        msg = f"LLM reference '{node.ref}' in node '{node.id}' not found in spec.llms"
        raise ValueError(msg)

    llm_pydantic_model_instance = spec.llms[node.ref]

    # Safely get the type attribute
    llm_instance_type = getattr(llm_pydantic_model_instance, "type", None)
    if not llm_instance_type:
        msg = (
            f"LLM configuration for reference '{node.ref}' (used in node '{node.id}') "
            f"is missing the required 'type' attribute. "
            f"Ensure the LLM spec includes 'type'. LLM details: {llm_pydantic_model_instance.model_dump(exclude_none=True)}"
        )
        raise ValueError(
            msg
        )

    # Use create_llm_config to get a config object that includes the resolved API key
    populated_config_obj = create_llm_config(
        config=llm_pydantic_model_instance.model_dump(),
        llm_type=llm_instance_type
    )

    # Update the original Pydantic model instance with the resolved API key
    llm_pydantic_model_instance.api_key = populated_config_obj.api_key

    # Return configured LLMClient
    return LLMClient(llm_pydantic_model_instance)

def make_llm_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """Creates a node function that uses an LLM to process input and generate output.

    The returned node function takes a `WorkflowState`, uses an LLM (configured via `spec`
    and `node.ref`) to process `state['input']` (after formatting it with `node.config.prompt`
    if available), and returns an updated `WorkflowState` with the LLM's response
    in `state['output']`. It also handles iteration counting and error handling.

    Args:
        spec: The full workflow specification.
        node: The WorkflowNode object, used here to access node.id, node.ref for LLM configuration,
              and node.config.prompt for the prompt template.

    Returns:
        A node function that processes state using the LLM.
    """
    llm_client = _create_llm_client(spec, node)

    prompt_template_str: str | None = None
    # node.config is now a field in WorkflowNode, defaulting to an empty dict if not in YAML.
    potential_prompt = node.config.get("prompt")
    if isinstance(potential_prompt, str):
        prompt_template_str = potential_prompt
    elif potential_prompt is not None: # 'prompt' key exists in config but its value is not a string
        logger.warning(f"[yellow]⚠ [Node: {node.id}] Invalid prompt type - ignored[/yellow]")

    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            current_iter_display = (state.get("iteration_count") or 0) + 1
            max_iter_display = getattr(spec.workflow, "max_iterations", None) or DEFAULT_MAX_ITERATIONS
            iteration_str = f"Iteration {current_iter_display}/{max_iter_display}"

            user_provided_input = state.get("input", "")

            final_prompt_to_llm: str
            if prompt_template_str:
                # Support multiple state fields in template
                template_kwargs = {
                    "input": user_provided_input,
                    "output": state.get("output", ""),
                    "iteration_count": state.get("iteration_count", 0),
                    "evaluation_score": state.get("evaluation_score", 0.0),
                    # Allow attribute-style access such as {state.output} with safe fallback
                    "state": SafeNamespace(state),
                }

                try:
                    final_prompt_to_llm = prompt_template_str.format(**template_kwargs)
                except KeyError as e:
                    logger.warning(f"[yellow]⚠ [Node: {node.id}] Template variable {e} not found in state, using partial formatting[/yellow]")
                    # Fall back to just input formatting for compatibility
                    if "{input}" in prompt_template_str:
                        final_prompt_to_llm = prompt_template_str.format(input=user_provided_input)
                    else:
                        final_prompt_to_llm = prompt_template_str
                        if user_provided_input:
                            final_prompt_to_llm += "\n\nUser Input: " + user_provided_input
            elif user_provided_input:
                final_prompt_to_llm = user_provided_input
            else:
                error_msg = f"Node {node.id} (type: {node.kind}) has no prompt template in config and no 'input' in state. Cannot proceed."
                logger.error(f"[red]✗ [Node: {node.id}] {error_msg}[/red]")
                return WorkflowState({
                    **state,
                    "output": f"ConfigurationError: {error_msg}",
                    "current_node": node.id,
                    "error_context": error_msg
                })

            logger.info(f"[blue][Node: {node.id}] LLM call ({iteration_str}) {llm_client.spec.type}:{llm_client.spec.model_name}[/blue]")
            response = llm_client.generate(final_prompt_to_llm)
            logger.info(f"[dim][Node: {node.id}] Response: {response[:50]}...[/dim]")

            # Check if this node has a structured output format
            output_format = node.config.get("format")
            if output_format:
                logger.info(f"[blue][Node: {node.id}] Processing {output_format} format[/blue]")
                try:
                    if output_format == "json":
                        # Handle JSON structured output for Spec generation
                        spec_instance = Spec.from_structured_json(response)
                        yaml_output = spec_instance.to_yaml_string()

                        logger.info(f"[green]✓ [Node: {node.id}] JSON validation passed[/green]")
                        return WorkflowState({
                            **state,
                            "output": yaml_output,  # Clean YAML output
                            "structured_data": spec_instance.model_dump(exclude_none=True),
                            "raw_json": response,
                            "format_status": "converted",
                            "current_node": node.id,
                            "error_context": None
                        })
                    if output_format == "yaml":
                        # Handle YAML format (existing logic)
                        structured_output = Spec.create_structured_output(response)

                        if structured_output["validation"]["is_valid"]:
                            logger.info(f"[green]✓ [Node: {node.id}] YAML validation passed[/green]")
                            return WorkflowState({
                                **state,
                                "output": structured_output["yaml_content"],
                                "structured_output": structured_output,
                                "validation_status": "valid",
                                "current_node": node.id,
                                "error_context": None
                            })
                        error_msg = structured_output["validation"]["error"]
                        logger.error(f"[red]✗ [Node: {node.id}] YAML validation failed: {error_msg}[/red]")
                        return WorkflowState({
                            **state,
                            "output": response,
                            "structured_output": structured_output,
                            "validation_status": "invalid",
                            "validation_error": error_msg,
                            "current_node": node.id,
                            "error_context": f"YAML validation failed: {error_msg}"
                        })
                    logger.warning(f"[yellow]⚠ [Node: {node.id}] Unknown format: {output_format}[/yellow]")

                except Exception as e:
                    logger.exception(f"[red]✗ [Node: {node.id}] Structured output error: {e!s}[/red]")
                    return WorkflowState({
                        **state,
                        "output": response,
                        "format_status": "error",
                        "format_error": str(e),
                        "current_node": node.id,
                        "error_context": f"Structured output error: {e!s}"
                    })

            if node.id == "breakdown_worker":
                current_iteration_for_node = state.get("iteration_count") or 0
                return WorkflowState({
                    **state,
                    "output": response,
                    "iteration_count": current_iteration_for_node + 1,
                    "current_node": node.id,
                    "error_context": None
                })

            # Handle output_key for custom state field assignment
            result_state = {
                **state,  # Preserve all existing state
                "output": response,
                "current_node": node.id,
                "error_context": None
            }
            
            # If node has output_key, store response in dynamic_state
            output_key = node.config.get("output_key")
            if output_key and isinstance(output_key, str):
                if "dynamic_state" not in result_state or result_state["dynamic_state"] is None:
                    result_state["dynamic_state"] = {}
                result_state["dynamic_state"][output_key] = response
            
            return WorkflowState(result_state)
        except Exception as e:
            logger.exception(f"[red]✗ [Node: {node.id}] LLM error: {e!s}[/red]")
            # Preserve original state from before this node's execution on error
            return {
                **state,
                "output": f"Error: {e!s}",
                "current_node": node.id,
                "error_context": f"LLM error in node {node.id}: {type(e).__name__}"
            }
    return node_fn

def load_tool(fn: Any) -> NodeFunction:
    """Creates a node function that wraps and executes a given tool/function.

    The wrapped tool is expected to operate on or use the `WorkflowState`.
    The returned node function takes the current `WorkflowState`, calls the tool,
    and integrates its result back into the `WorkflowState`.
    - If the tool returns a string, it becomes `state['output']`.
    - If the tool returns a dictionary, it's merged into the state.
    - Other return types are converted to string and set as `state['output']`.
    Error handling is included.

    Args:
        fn: The tool function to be executed by the node. Can be any callable.

    Returns:
        A node function compatible with StateGraph that executes the tool.
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            if fn is None:
                logger.warning("[yellow]⚠ Tool function is None - returning input as output[/yellow]")
                return {
                    **state,
                    "output": state.get("input", "")
                }

            logger.info(f"[blue]Executing tool: {getattr(fn, '__name__', 'unknown')}[/blue]")

            # Execute the tool function with the current state
            if callable(fn):
                result = fn(state)

                # If the tool returns a string, use it as output
                if isinstance(result, str):
                    return {
                        **state,
                        "output": result
                    }
                # If the tool returns a dict, merge it with state
                if isinstance(result, dict):
                    return {
                        **state,
                        **result
                    }
                # Otherwise convert to string
                return {
                    **state,
                    "output": str(result)
                }
            logger.warning("[yellow]⚠ Tool function is not callable[/yellow]")
            return {
                **state,
                "output": f"Tool function {fn} is not callable"
            }

        except Exception as e:
            logger.exception(f"[red]✗ Tool execution error: {e!s}[/red]")
            return {
                **state,
                "output": f"Tool error: {e!s}"
            }
    return node_fn

def make_mcp_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """Creates a node function that executes an MCP tool using the new MCP node architecture.

    The node function connects to an MCP server, executes the specified tool,
    and integrates the result back into the `WorkflowState`.

    Args:
        spec: The full workflow specification (not used in MVP but included for consistency)
        node: The WorkflowNode containing MCP configuration

    Returns:
        A node function compatible with StateGraph that executes the MCP tool
    """
    from .mcp_client import MCPConnectionError, MCPToolError
    from .nodes.mcp_node import MCPNode

    # Create MCP node instance
    mcp_node = MCPNode(node.config)

    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            logger.info(f"[blue][Node: {node.id}] Executing MCP tool: {mcp_node.tool_name}[/blue]")

            # Convert state to regular dict for MCP node
            state_dict = dict(state)

            # Execute MCP tool
            try:
                # Handle async execution
                try:
                    loop = asyncio.get_running_loop()
                    # If we're already in an event loop, we need to handle this differently
                    result_state = asyncio.run_coroutine_threadsafe(
                        mcp_node.execute(state_dict),
                        loop
                    ).result(timeout=30.0)
                except RuntimeError:
                    # No event loop running, create one
                    result_state = asyncio.run(mcp_node.execute(state_dict))

                logger.info(f"[green]✓ [Node: {node.id}] MCP tool completed[/green]")

                # Use the output field from the result state if available, otherwise fallback to mcp_result
                output = result_state.get("output", result_state.get("mcp_result", ""))

                return WorkflowState({
                    **state,
                    "output": output,
                    "current_node": node.id,
                    "error_context": None
                })

            except MCPConnectionError as e:
                logger.exception(f"[red]✗ [Node: {node.id}] MCP connection error: {e!s}[/red]")
                return WorkflowState({
                    **state,
                    "output": f"MCP Connection Error: {e!s}",
                    "current_node": node.id,
                    "error_context": f"MCP connection error: {e!s}"
                })
            except MCPToolError as e:
                logger.exception(f"[red]✗ [Node: {node.id}] MCP tool error: {e!s}[/red]")
                return WorkflowState({
                    **state,
                    "output": f"MCP Tool Error: {e!s}",
                    "current_node": node.id,
                    "error_context": f"MCP tool error: {e!s}"
                })
            except TimeoutError:
                logger.exception(f"[red]✗ [Node: {node.id}] MCP tool timed out[/red]")
                return WorkflowState({
                    **state,
                    "output": "MCP Tool Error: Tool execution timed out",
                    "current_node": node.id,
                    "error_context": "MCP tool timeout"
                })

        except Exception as e:
            logger.exception(f"[red]✗ [Node: {node.id}] Unexpected MCP error: {e!s}[/red]")
            return WorkflowState({
                **state,
                "output": f"Unexpected error: {e!s}",
                "current_node": node.id,
                "error_context": f"Unexpected MCP error: {type(e).__name__}"
            })

    return node_fn

def make_claude_code_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """Creates a node function that executes Claude Code SDK tasks.

    The node function uses the Claude Code SDK to perform various code-related tasks
    such as code generation, analysis, modification, and general chat interactions.

    Args:
        spec: The full workflow specification (not used in current implementation but included for consistency)
        node: The WorkflowNode containing Claude Code configuration

    Returns:
        A node function compatible with StateGraph that executes Claude Code tasks
    """
    from .nodes.claude_code_node import (
        ClaudeCodeConnectionError,
        ClaudeCodeExecutionError,
        ClaudeCodeNode,
    )

    # Create Claude Code node instance
    try:
        claude_code_node = ClaudeCodeNode(node.config)
    except Exception as e:
        # Capture error details immediately to avoid closure scope issues
        error_message = str(e)
        node_id = node.id

        # If there's an error creating the node, return a function that reports the error
        def error_node_fn(state: WorkflowState) -> WorkflowState:
            error_msg = f"Claude Code node configuration error: {error_message}"
            logger.exception(f"[red]✗ [Node: {node_id}] {error_msg}[/red]")
            return WorkflowState({
                **state,
                "output": error_msg,
                "current_node": node_id,
                "error_context": error_msg
            })
        return error_node_fn

    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            logger.info(f"[blue][Node: {node.id}] Executing Claude Code task: {claude_code_node.task}[/blue]")

            # Convert state to regular dict for Claude Code node
            state_dict = dict(state)

            # Execute Claude Code task
            try:
                # Handle async execution with proper event loop management
                import concurrent.futures

                def run_claude_code():
                    """Run Claude Code in a new event loop in a separate thread."""
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(claude_code_node.execute(state_dict))
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)

                # Always run in a separate thread to avoid event loop conflicts
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_claude_code)
                    result_state = future.result(timeout=120.0)  # Longer timeout for code operations

                logger.info(f"[green]✓ [Node: {node.id}] Claude Code task completed[/green]")

                # Use the output field from the result state
                output = result_state.get("output", "")

                return WorkflowState({
                    **state,
                    "output": output,
                    "claude_code_result": result_state.get("claude_code_result"),
                    "current_node": node.id,
                    "error_context": None
                })

            except ClaudeCodeConnectionError as e:
                logger.exception(f"[red]✗ [Node: {node.id}] Claude Code connection error: {e!s}[/red]")
                return WorkflowState({
                    **state,
                    "output": f"Claude Code Connection Error: {e!s}",
                    "current_node": node.id,
                    "error_context": f"Claude Code connection error: {e!s}"
                })
            except ClaudeCodeExecutionError as e:
                logger.exception(f"[red]✗ [Node: {node.id}] Claude Code execution error: {e!s}[/red]")
                return WorkflowState({
                    **state,
                    "output": f"Claude Code Execution Error: {e!s}",
                    "current_node": node.id,
                    "error_context": f"Claude Code execution error: {e!s}"
                })
            except TimeoutError:
                logger.exception(f"[red]✗ [Node: {node.id}] Claude Code task timed out[/red]")
                return WorkflowState({
                    **state,
                    "output": "Claude Code Error: Task execution timed out",
                    "current_node": node.id,
                    "error_context": "Claude Code task timeout"
                })

        except Exception as e:
            logger.exception(f"[red]✗ [Node: {node.id}] Unexpected Claude Code error: {e!s}[/red]")
            return WorkflowState({
                **state,
                "output": f"Unexpected Claude Code error: {e!s}",
                "current_node": node.id,
                "error_context": f"Unexpected Claude Code error: {type(e).__name__}"
            })

    return node_fn

def make_judge_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """Creates a node function that uses a designated LLM to evaluate/judge the workflow state.

    The judge LLM typically processes `state['output']` (or `state['input']` as a fallback)
    from the previous node. It's expected to return a JSON structure containing an
    'evaluation_score'. This score is parsed and stored in `state['evaluation_score']`.
    The raw LLM response is stored in `state['output']`. Iteration count is also incremented.
    Includes logic for robust JSON parsing and error handling.

    Args:
        spec: The full workflow specification, used to configure the judge LLM.
        node: The WorkflowNode defining the judge, including its LLM reference.

    Returns:
        A node function that performs the judgment and updates the `WorkflowState`.
    """
    judge_llm_client = _create_llm_client(spec, node)

    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            # Determine input for the judge
            input_to_judge = state.get("output")
            if input_to_judge is None:
                logger.warning(f"[yellow]⚠ [Node: {node.id}] No output from previous node - using input as fallback[/yellow]")
                input_to_judge = state.get("input", "")

            # Iteration display
            # iteration_count in state is completed iterations. Current is +1.
            # The judge node itself will increment iteration_count for the *next* state.
            # So for *this* run, current_iter_display is based on the incoming state.
            current_iter_display = (state.get("iteration_count") or 0) + 1
            max_iter_display = getattr(spec.workflow, "max_iterations", None) or DEFAULT_MAX_ITERATIONS
            iteration_str = f"Iteration {current_iter_display}/{max_iter_display}"

            logger.info(f"[blue][Node: {node.id}] Judge evaluation ({iteration_str}) {judge_llm_client.spec.type}:{judge_llm_client.spec.model_name}[/blue]")

            judgment_prompt = str(input_to_judge)
            raw_llm_output = judge_llm_client.generate(judgment_prompt)
            logger.info(f"[dim][Node: {node.id}] Judge output: {raw_llm_output[:50]}...[/dim]") # Show a bit more for JSON

            parsed_score_value: float | None = None

            try:
                # Clean the string: remove markdown fences and trim whitespace
                cleaned_json_str = raw_llm_output.strip()
                if cleaned_json_str.startswith("```json"):
                    cleaned_json_str = cleaned_json_str[len("```json"):]
                elif cleaned_json_str.startswith("```"):
                     cleaned_json_str = cleaned_json_str[len("```"):]

                if cleaned_json_str.endswith("```"):
                    cleaned_json_str = cleaned_json_str[:-len("```")]
                cleaned_json_str = cleaned_json_str.strip()

                if not cleaned_json_str:
                    logger.warning(f"[yellow]⚠ [Node: {node.id}] Empty JSON string after cleaning[/yellow]")
                    msg = "Cleaned JSON string is empty."
                    raise ValueError(msg)

                data = json.loads(cleaned_json_str)
                if isinstance(data, dict) and "evaluation_score" in data:
                    score_from_json = data["evaluation_score"]
                    if isinstance(score_from_json, int | float):
                        parsed_score_value = float(score_from_json)
                    else:
                        logger.warning(f"[yellow]⚠ [Node: {node.id}] Invalid evaluation_score type: {type(score_from_json).__name__}[/yellow]")
                else:
                    logger.warning(f"[yellow]⚠ [Node: {node.id}] Missing evaluation_score in JSON[/yellow]")
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.exception(f"[red]✗ [Node: {node.id}] Failed to parse evaluation_score: {type(e).__name__}[/red]")

            # This is the iteration_count for the *output* state of this node.
            iteration_count_for_next_state = (state.get("iteration_count") or 0) + 1

            final_score_for_state: float
            if parsed_score_value is not None:
                final_score_for_state = parsed_score_value
            else:
                final_score_for_state = 0.0
                logger.warning(f"[yellow]⚠ [Node: {node.id}] Defaulting evaluation_score to 0.0[/yellow]")

            return {
                **state,
                "output": raw_llm_output,
                "iteration_count": iteration_count_for_next_state, # Update iteration count for the next node
                "evaluation_score": final_score_for_state
            }
        except Exception as e:
            logger.exception(f"[red]✗ [Node: {node.id}] Unhandled exception: {type(e).__name__}[/red]")
            return {
                **state,
                "output": f"Error in Judge Node '{node.id}': {type(e).__name__} - {e!s}",
                "iteration_count": (state.get("iteration_count") or 0) + 1,
                "evaluation_score": state.get("evaluation_score") if isinstance(state.get("evaluation_score"), float) else 0.0
            }
    return node_fn

def make_branch_node(node: Any) -> NodeFunction:
    """Creates a node function for implementing branching logic within the workflow.

    Branch nodes are pass-through nodes that preserve the previous node's output
    while allowing conditional routing based on their configuration. The actual
    routing logic is handled by the graph edges, not the node function itself.

    Args:
        node: The node configuration object. Specific attributes relevant to branching
              (e.g., conditions, target nodes) would be defined here in a full implementation.

    Returns:
        A node function that passes through the previous node's output unchanged.
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        # Branch nodes are pass-through - preserve previous output for routing
        return {
            **state,
            "current_node": getattr(node, 'id', 'branch_node'),
            "error_context": None
        }
    return node_fn

def make_tool_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """Creates a tool node function that routes to either Python or MCP tool loaders.

    This function examines the referenced function's type and calls the appropriate
    loader (load_tool for Python functions, load_mcp_tool for MCP functions).

    Args:
        spec: The full workflow specification containing function definitions
        node: The WorkflowNode referencing the tool function

    Returns:
        A node function that executes the appropriate tool type

    Raises:
        ValueError: If the function reference is not found or has an unsupported type
    """
    function_spec = spec.functions.get(node.ref)

    if function_spec is None:
        msg = f"Function reference '{node.ref}' not found in spec.functions"
        raise ValueError(msg)

    if function_spec.type == "python":
        logger.info(f"[blue]Loading Python tool: {function_spec.name}[/blue]")

        try:
            # Load the actual function
            func = function_loader.load_function(function_spec.entrypoint)

            # Create wrapper that handles parameter binding
            def python_function_wrapper(state: WorkflowState) -> WorkflowState:
                try:
                    # Get parameters from node config
                    parameters = node.config.get("parameters", {}) if node.config else {}

                    # Bind parameters from state and config
                    bound_params = function_loader.bind_parameters(func, state, parameters)

                    # Execute function
                    logger.info(f"[blue]Executing {function_spec.entrypoint}[/blue]")
                    result = func(**bound_params)

                    # Handle return value
                    if isinstance(result, dict):
                        # Function returned state update
                        return {**state, **result}
                    if isinstance(result, str):
                        # Function returned string output
                        return {**state, "output": result}
                    # Convert other types to string
                    return {**state, "output": str(result)}

                except UserExitRequested:
                    # Let UserExitRequested propagate up to terminate the workflow
                    raise
                except Exception as e:
                    logger.exception(f"[red]✗ Python function error: {e!s}[/red]")
                    return {
                        **state,
                        "output": f"Function error: {e!s}",
                        "error_context": f"Python function '{function_spec.entrypoint}' failed: {e!s}"
                    }

            return load_tool(python_function_wrapper)

        except Exception as load_error:
            error_msg = str(load_error)
            logger.exception(f"[red]✗ Failed to load Python function: {error_msg}[/red]")

            def error_function(state: WorkflowState) -> WorkflowState:
                return {
                    **state,
                    "output": f"Failed to load function '{function_spec.entrypoint}': {error_msg}",
                    "error_context": f"Function loading error: {error_msg}"
                }

            return error_function

    elif function_spec.type == "mcp":
        # For MCP functions, create a placeholder that explains the new architecture
        logger.info(f"[blue]MCP function {function_spec.name} - use MCP nodes instead[/blue]")

        def mcp_function_placeholder(state: WorkflowState) -> WorkflowState:
            return {
                **state,
                "output": f"MCP function '{function_spec.name}' - Use MCP nodes instead of function references for MCP tools",
                "error_context": "MCP functionality is now handled by MCP nodes directly"
            }

        return mcp_function_placeholder

    else:
        msg = f"Unsupported function type '{function_spec.type}' for function '{function_spec.name}'"
        raise ValueError(msg)

class NodeFactoryRegistry:
    """Registry for node factory functions."""

    _factories: dict[str, NodeFactory] = {
        "agent": make_llm_node,
        "tool": make_tool_node,
        "judge": lambda spec, node: make_judge_node(spec, node),
        "branch": lambda spec, node: make_branch_node(node),
        "mcp": make_mcp_node,
        "claude_code": make_claude_code_node,
    }

    @classmethod
    def get(cls, kind: str) -> NodeFactory:
        """Retrieves a registered node factory function for a given node kind.

        Node factories are callables that, given a `Spec` and a `WorkflowNode`,
        return a `NodeFunction` (the actual callable to be executed in the graph).
        This method allows dynamic creation of nodes based on their 'kind' string.

        Args:
            kind: The type/kind of node (e.g., "agent", "tool", "judge") for which
                  to retrieve the factory.

        Returns:
            The registered `NodeFactory` capable of creating nodes of the specified kind.

        Raises:
            ValueError: If no factory is registered for the given `kind`.
        """
        try:
            return cls._factories[kind]
        except KeyError:
            msg = f"Unknown node kind: {kind}"
            raise ValueError(msg) from None

    @classmethod
    def register(cls, kind: str, factory: NodeFactory) -> None:
        """Registers a new node factory function for a specific node kind.

        This allows extending the compiler with custom node types. The `factory`
        provided should be a callable conforming to the `NodeFactory` protocol,
        meaning it accepts a `Spec` and `WorkflowNode` and returns a `NodeFunction`.

        Args:
            kind: The string identifier for the new node kind (e.g., "custom_agent").
            factory: The `NodeFactory` function to be associated with this kind.
        """
        cls._factories[kind] = factory

def create_condition_function(expr: str) -> Callable[[dict[str, Any]], Any]:
    """Creates a callable function from a condition expression string for graph routing.

    This function parses a domain-specific expression string (e.g.,
    "state.get('evaluation_score', 0) >= 0.75") and converts it into a Python
    function. This generated function takes a `WorkflowState` (as a dictionary)
    and evaluates the expression against it, returning a boolean or a target node name.

    Supported expressions include:
    - Comparisons: `state.get('key', default_value) op value` (e.g., `state.get('score', 0) > 5`)
      where `op` can be `>=`, `<=`, `>`, `<`, `==`, `!=`.
    - Logical combinations: `condition1 and condition2`, `condition1 or condition2`.
    - Direct boolean access: `state.get('key')` (evaluates to `bool(state.get('key'))`).
    - Simple boolean literals: `'true'`, `'false'`.
    - String literals (interpreted as target node names if no other pattern matches).

    This provides a safe way to define routing logic in a declarative manner
    without using `eval()` directly on arbitrary Python code.

    Args:
        expr: The condition expression string to parse.

    Returns:
        A callable function that takes a state dictionary and returns the evaluation
        result (typically boolean for conditions, or a string for direct routing).

    Raises:
        ValueError: If the expression string contains unsupported operations or fails to parse.
    """
    import operator
    import re

    # Define allowed operators
    ops = {
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def _parse_value(val_str: str) -> int | float | str:
        """Parse a string value to int, float, or string."""
        val_str = val_str.strip()
        if val_str.isdigit() or (val_str.startswith("-") and val_str[1:].isdigit()):
            return int(val_str)
        try:
            return float(val_str)
        except ValueError:
            return val_str.strip('"\'')

    def _evaluate_single_condition(condition_str: str, state: dict[str, Any]) -> bool | str:
        """Evaluate a single condition like 'state.get('key', default) op value'."""
        # Updated pattern to correctly capture key, optional default, operator, and value.
        # Handles: state.get('key', default_val) op value_val
        #      OR: state.get('key') op value_val
        pattern = r"state\.get\s*\(\s*['\"](.*?)['\"]\s*(?:,\s*(.*?))?\s*\)\s*([><=!]+)\s*(.*)"
        match = re.match(pattern, condition_str.strip())

        if not match:
            # Handle simple boolean expressions
            if condition_str.lower() in ("true", "false"):
                return condition_str.lower() == "true"

            # Handle direct state key access if the expression is *just* state.get('key') or state['key']
            # (intended to evaluate its truthiness)
            key_access_pattern = r"state\.(?:get\s*\(\s*['\"](.*?)['\"]\s*(?:,\s*.*?)?\s*\)|\[['\"](.*?)['\"]\])"
            key_access_match = re.fullmatch(key_access_pattern, condition_str.strip())
            if key_access_match:
                key = key_access_match.group(1) or key_access_match.group(2)
                # Default to None if key not found, then evaluate truthiness
                return bool(state.get(key))

            # Treat as string literal (for target node names if no other pattern matched)
            # This allows conditions to be direct node names for unconditional routing via conditional_edges
            return condition_str.strip('"\'')

        key, default_val_str, op_str, value_expr_str = match.groups()

        # Parse default value from expression. If not provided in expr, use None for state.get().
        default_for_state_get = _parse_value(default_val_str) if default_val_str is not None else None

        # Parse the value to compare against
        comp_value = _parse_value(value_expr_str)

        # Get state value using the key and the parsed or implicit default
        state_value_raw = state.get(key, default_for_state_get)

        # Prepare state_value for comparison: if it's a string and comp_value is also a string, strip it.
        state_value_for_comparison = state_value_raw
        if isinstance(state_value_raw, str) and isinstance(comp_value, str):
            state_value_for_comparison = state_value_raw.strip()

        # Perform comparison using the appropriate operator
        if op_str in ops:
            return ops[op_str](state_value_for_comparison, comp_value)
        msg = f"Unsupported operator: {op_str}"
        raise ValueError(msg)

    def condition(state: dict[str, Any]) -> bool | str:
        try:
            # Handle complex expressions with 'and' and 'or'
            if " and " in expr or " or " in expr:
                # Split by 'and' and 'or' operators
                # For simplicity, we'll handle left-to-right evaluation

                # Split by 'and' first (higher precedence)
                and_parts = expr.split(" and ")
                and_results = []

                for and_part in and_parts:
                    # Handle 'or' within each 'and' part
                    if " or " in and_part:
                        or_parts = and_part.split(" or ")
                        or_result = any(_evaluate_single_condition(part.strip(), state) for part in or_parts)
                        and_results.append(or_result)
                    else:
                        and_results.append(_evaluate_single_condition(and_part.strip(), state))

                return all(and_results)

            # Handle single condition
            return _evaluate_single_condition(expr, state)

        except Exception as e:
            msg = f"Failed to evaluate condition '{expr}': {e!s}"
            raise ValueError(msg)

    return condition


def add_nodes_to_graph(graph: StateGraph, spec: Spec) -> None:
    """Adds all nodes defined in `spec.workflow.nodes` to the `StateGraph`.

    For each node in the specification, this function:
    1. Retrieves the appropriate node factory using `NodeFactoryRegistry.get(node.kind)`.
    2. Calls the factory to create the actual node callable (an instance of `NodeFunction`).
    3. Adds the callable to the `graph` with `graph.add_node(node.id, node_fn)`.
    Additionally, if a node is marked with `node.stop is True`, an edge is automatically
    added from this node to the `END` state of the graph.

    Args:
        graph: The `StateGraph` instance to which nodes will be added.
        spec: The workflow specification containing the list of nodes.
    """
    if spec.workflow is None:
        msg = "Workflow must be present for compilation"
        raise WorkflowValidationError(msg)
    logger.info("[blue]Building workflow nodes[/blue]")
    for node in spec.workflow.nodes:
        logger.info(f"[dim]  Adding node: {node.id} ({node.kind})[/dim]")
        factory = NodeFactoryRegistry.get(node.kind)
        node_fn = factory(spec, node)
        graph.add_node(node.id, node_fn)

        # If this is a stop node, add an edge to END
        if node.stop:
            logger.info(f"[dim]  End condition: {node.id}[/dim]")
            graph.add_edge(node.id, END)

def add_edges_to_graph(graph: StateGraph, spec: Spec) -> None:
    """Configures all edges in the `StateGraph` based on `spec.workflow.edges`.

    For sequential workflows, automatically creates edges between consecutive nodes.
    For other workflow types, processes edges from the specification:
    1. Groups edges by their `source` node.
    2. For each source node:
        a. If there are conditional edges (edges with a `condition` string):
            - A router function is dynamically created. This router uses `create_condition_function`
              to parse each condition string into an evaluatable function that operates on `WorkflowState`.
            - `graph.add_conditional_edges` is called with the source node, the router,
              and a mapping of expected router return values (target node names) to target nodes.
            - Handles default targets if specified, or routes to `END` if no condition matches
              and no default is set.
        b. If there are only unconditional edges:
            - Each edge is added directly using `graph.add_edge(edge.source, edge.target)`.
            - Supports fan-out to multiple targets if multiple unconditional edges exist from a source.
    Logs detailed information about the edge configurations being applied.

    Args:
        graph: The `StateGraph` instance to which edges will be added.
        spec: The workflow specification containing the list of edges.
    """
    if spec.workflow is None:
        msg = "Workflow must be present for compilation"
        raise WorkflowValidationError(msg)
    logger.info("[blue]Building workflow edges[/blue]")

    # Handle sequential workflows by automatically creating edges between consecutive nodes
    if spec.workflow.type == "sequential":
        logger.info("[dim]Sequential workflow - auto-linking nodes[/dim]")
        nodes = spec.workflow.nodes
        for i in range(len(nodes) - 1):
            current_node = nodes[i]
            next_node = nodes[i + 1]
            logger.info(f"[dim]  {current_node.id} → {next_node.id}[/dim]")
            graph.add_edge(current_node.id, next_node.id)

        # Also process any additional edges from the edges list (for sequential workflows with custom overrides)
        if spec.workflow.edges:
            logger.info("[dim]Processing custom edges[/dim]")

    edges_by_source: dict[str, list[Edge]] = {}
    for edge in spec.workflow.edges:
        edges_by_source.setdefault(edge.source, []).append(edge)

    for source, edges_from_source in edges_by_source.items():
        logger.info(f"[dim]Processing edges from {source}[/dim]")

        conditional_edges = [e for e in edges_from_source if e.condition]
        unconditional_edges = [e for e in edges_from_source if not e.condition]

        if conditional_edges:
            # If there are any conditional edges, all decisions from this node
            # must go through a single conditional router.
            logger.info(f"[dim]  Conditional routing for {source}[/dim]")

            default_target: str | None = None
            if len(unconditional_edges) > 1:
                logger.warning(f"[yellow]⚠ Multiple unconditional edges from {source} - using first as default[/yellow]")
                default_target = unconditional_edges[0].target
            elif unconditional_edges:
                default_target = unconditional_edges[0].target
                logger.info(f"[dim]  Default target: {default_target}[/dim]")


            # Create a router function that evaluates conditions and falls back to default_target or END
            def create_router_for_source(
                source_node_id: str,
                cond_edges: list[Edge],
                def_target: str | None
            ) -> Callable[[dict[str, Any]], str]:

                condition_target_pairs = [
                    (create_condition_function(e.condition or "true"), e.target)
                    for e in cond_edges
                ]

                def router(state: dict[str, Any]) -> str:
                    logger.info(f"[dim]  Router evaluating: {str(state.get('output', ''))[:30]}...[/dim]") # Log the state output
                    for condition_fn, target_node_name in condition_target_pairs:
                        try:
                            if condition_fn(state): # condition_fn should return boolean
                                logger.info(f"[dim]  Routing {source_node_id} → {target_node_name}[/dim]")
                                return target_node_name # Router returns the key for the ends_map
                        except Exception as e:
                            logger.exception(f"[red]✗ Routing error for {source_node_id}: {e!s}[/red]")
                            # In a production system, you might want to raise or handle this more specifically

                    if def_target:
                        logger.info(f"[dim]  Default routing {source_node_id} → {def_target}[/dim]")
                        return def_target

                    logger.warning(f"[yellow]⚠ No route found for {source_node_id} - routing to END[/yellow]")
                    return END # LangGraph's END sentinel if no path is chosen

                return router

            router_fn = create_router_for_source(source, conditional_edges, default_target)

            # The conditional_edge_mapping keys are what the router returns.
            # The values are the actual node IDs (or special targets like END).
            # Our router is designed to return actual target node names or END.
            edge_mapping: dict[Any, Any] = {e.target: e.target for e in conditional_edges}
            if default_target:
                edge_mapping[default_target] = default_target # Add default target to map
            edge_mapping[END] = END # Ensure END is always a valid target if router returns it

            graph.add_conditional_edges(
                source,
                router_fn,
                edge_mapping
            )

        elif unconditional_edges: # No conditional edges from this source, only unconditional ones.
            if len(unconditional_edges) > 1:
                 logger.info(f"[dim]  Fan-out from {source}: {[e.target for e in unconditional_edges]}[/dim]")
            for edge in unconditional_edges:
                logger.info(f"[dim]  {source} → {edge.target}[/dim]")
                graph.add_edge(edge.source, edge.target)  # ✅ FIXED: Actually add the edge
        else:
            # This case means the node is a leaf node in terms of defined edges.
            # If it's not a 'stop: true' node, the graph might halt here if no global end is reached.
            logger.info(f"[dim]  No outgoing edges from {source}[/dim]")

            # Check if this node should have edges but doesn't
            node = next((n for n in spec.workflow.nodes if n.id == source), None)
            if node and not node.stop:
                logger.warning(f"[yellow]⚠ Node {source} has no edges and stop=False - may terminate unexpectedly[/yellow]")


def compile_to_langgraph(spec: Spec) -> StateGraph:
    """Compiles a `Spec` object into a runnable `langgraph.StateGraph`.

    This orchestration function performs the following steps:
    1. Validates that the spec has a workflow (should be resolved by this point).
    2. Defines a `WorkflowStateSchema` (a Pydantic model) that dictates the structure
       of the state object passed between nodes in the graph. This schema matches
       the `WorkflowState` TypedDict.
    3. Initializes a `StateGraph` instance with this `WorkflowStateSchema`.
    4. Calls `add_nodes_to_graph(graph, spec)` to populate the graph with all defined nodes
       from the specification, creating node callables via `NodeFactoryRegistry`.
    5. Calls `add_edges_to_graph(graph, spec)` to establish the control flow (transitions)
       between these nodes, including conditional logic based on `WorkflowState`.
    6. Sets the entry point of the graph using `graph.set_entry_point()`, typically to the
       ID of the first node defined in `spec.workflow.nodes`.

    Args:
        spec: The workflow specification object containing all definitions for nodes,
              edges, LLMs, and functions. Must be fully resolved (no pending references).

    Returns:
        A fully configured `langgraph.StateGraph` instance, ready for execution
        with an initial input state.

    Raises:
        ValueError: If the spec doesn't have a workflow (references should be resolved by now).
    """
    logger.info("[blue]Compiling workflow[/blue]")

    # Ensure the spec has a workflow (references should be resolved by this point)
    if not spec.workflow:
        msg = "Cannot compile spec: workflow is missing. This may indicate an unresolved reference."
        raise ValueError(msg)

    # Type narrowing for mypy
    workflow = spec.workflow

    # Define the state schema using Pydantic
    class WorkflowStateSchema(BaseModel):
        """Schema for workflow state."""
        input: str
        output: str | None = None
        iteration_count: int | None = Field(default=0)
        evaluation_score: float | None = None
        # Enhanced workflow metadata for better tracking
        workflow_id: str | None = None
        current_node: str | None = None
        error_context: str | None = None
        # User interaction fields
        user_exit_requested: bool | None = None  # Flag when user requests to exit
        # Structured output validation fields
        structured_output: dict[str, Any] | None = None
        validation_status: str | None = None  # 'valid', 'invalid', 'error', or None
        validation_error: str | None = None
        # Format processing fields
        structured_data: dict[str, Any] | None = None
        raw_json: str | None = None
        format_status: str | None = None  # 'converted', 'error', or None
        format_error: str | None = None
        # Dynamic fields for output_key support
        dynamic_state: dict[str, Any] | None = None

    # Create a new graph with explicit state schema
    graph = StateGraph(
        state_schema=WorkflowStateSchema
    )

    # Build graph components
    add_nodes_to_graph(graph, spec)
    add_edges_to_graph(graph, spec)

    # Set the entry point
    if workflow.nodes:
        logger.info(f"[dim]Entry point: {workflow.nodes[0].id}[/dim]")
        graph.set_entry_point(workflow.nodes[0].id)

    logger.info("[green]✓ Workflow compilation complete[/green]")
    return graph
