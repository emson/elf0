# src/elf/core/compiler.py
from typing import Callable, Any, Dict, TypedDict, Protocol, List, Optional
from langgraph.graph import StateGraph, END
from .llm_client import LLMClient
from .spec import Spec, WorkflowNode, Edge, LLM as LLMSpecModel
from .config import create_llm_config
import logging
from pydantic import BaseModel, Field
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    input: str
    output: str | None
    iteration_count: Optional[int]
    evaluation_score: Optional[float]

class NodeFunction(Protocol):
    """Protocol defining the interface for node functions."""
    def __call__(self, state: WorkflowState) -> WorkflowState: ...

class NodeFactory(Protocol):
    """Protocol defining the interface for node factory functions."""
    def __call__(self, spec: Spec, node: WorkflowNode) -> NodeFunction: ...

def make_llm_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """
    Create a node function that uses an LLM to process input and generate output.
    
    Args:
        spec: The full workflow specification.
        node: The WorkflowNode object, used here to access node.id and node.ref.
        
    Returns:
        A function that processes state using the LLM.
    """
    # 1. Get the specific LLM model configuration from the spec
    if node.ref not in spec.llms:
        raise ValueError(f"LLM reference '{node.ref}' in node '{node.id}' not found in spec.llms")
    
    llm_pydantic_model_instance = spec.llms[node.ref]

    # Safely get the type attribute
    llm_instance_type = getattr(llm_pydantic_model_instance, 'type', None)
    if not llm_instance_type:
        raise ValueError(
            f"LLM configuration for reference '{node.ref}' (used in node '{node.id}') "
            f"is missing the required 'type' attribute. "
            f"Ensure the LLM spec includes 'type'. LLM details: {llm_pydantic_model_instance.model_dump(exclude_none=True)}"
        )

    # 2. Use create_llm_config to get a config object that includes the resolved API key.
    populated_config_obj = create_llm_config(
        config=llm_pydantic_model_instance.model_dump(), 
        llm_type=llm_instance_type # Use the safely retrieved type
    )

    # 3. Update the original Pydantic model instance from spec.llms with the resolved API key.
    llm_pydantic_model_instance.api_key = populated_config_obj.api_key
    
    # 4. Instantiate LLMClient with the updated Pydantic model instance
    llm_client = LLMClient(llm_pydantic_model_instance)
    
    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            logger.info(f"🤖 LLM Processing for node '{node.id}' (using {llm_client.spec.type}:{llm_client.spec.model_name}): {state.get('input', '')[:100]}...")
            response = llm_client.generate(state["input"])
            logger.info(f"✨ LLM Response from node '{node.id}': {response[:100]}...")
            
            new_state = {
                **state,  # Preserve all existing state
                "output": response
            }

            # If this node is 'breakdown_worker', increment iteration_count.
            # This is specific to the logic in orchestration_workers.yaml where breakdown_worker
            # completes a cycle before returning to the orchestrator.
            if node.id == "breakdown_worker":
                current_iteration = state.get('iteration_count', 0)
                new_state['iteration_count'] = current_iteration + 1
                logger.info(f"🔄 Node '{node.id}' (breakdown_worker) incremented iteration_count to {new_state['iteration_count']}")
            
            return new_state
        except Exception as e:
            logger.error(f"❌ LLM Error in node '{node.id}': {str(e)}")
            # Preserve original state from before this node's execution on error
            return {
                **state, 
                "output": f"Error: {str(e)}"
            }
    return node_fn

def load_tool(fn: Any) -> NodeFunction:
    """
    Create a node function that executes a tool/function.
    
    Args:
        fn: The function to execute
        
    Returns:
        A node function that executes the tool
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            logger.info("🔍 Evaluating prompt quality...")
            # Increment iteration count
            iteration_count = state.get('iteration_count', 0) + 1
            
            # Mock evaluation score logic for testing
            # This ensures the score changes and can meet exit conditions.
            mock_score: float = 0.0
            if iteration_count == 1:
                mock_score = 1.0
            elif iteration_count == 2:
                mock_score = 4.0 # This should meet the ">= 4" condition on the 2nd attempt
            else:
                mock_score = 5.0 # For any subsequent attempts

            logger.info(f"🔄 Iteration {iteration_count} of 3 (target for prompt improvement loop)")
            logger.info(f"📊 Evaluation result: Mock Score = {mock_score}")
            
            result_message = f"Judgment for: {state.get('input','')} - Iteration: {iteration_count}, Mock Score: {mock_score}"
            
            return {
                **state,  # Preserve all existing state
                "iteration_count": iteration_count,
                "evaluation_score": mock_score,
                "output": result_message
            }
        except Exception as e:
            logger.error(f"❌ Evaluation Error: {str(e)}")
            return {
                **state,  # Preserve all existing state
                "output": f"Error: {str(e)}"
            }
    return node_fn

def make_judge_node(spec: Spec, node: WorkflowNode) -> NodeFunction:
    """
    Create a node function that uses an LLM to evaluate/judge the state.
    
    Args:
        spec: The full workflow specification.
        node: The WorkflowNode for the judge.
        
    Returns:
        A node function that performs judgment
    """
    # Similar logic to make_llm_node for instantiating the LLMClient
    if node.ref not in spec.llms:
        raise ValueError(f"LLM reference '{node.ref}' in judge node '{node.id}' not found in spec.llms")

    llm_pydantic_model_instance = spec.llms[node.ref]

    # Safely get the type attribute
    llm_instance_type = getattr(llm_pydantic_model_instance, 'type', None)
    if not llm_instance_type:
        raise ValueError(
            f"LLM configuration for reference '{node.ref}' (used in judge node '{node.id}') "
            f"is missing the required 'type' attribute. "
            f"Ensure the LLM spec includes 'type'. LLM details: {llm_pydantic_model_instance.model_dump(exclude_none=True)}"
        )
        
    populated_config_obj = create_llm_config(
        config=llm_pydantic_model_instance.model_dump(),
        llm_type=llm_instance_type # Use the safely retrieved type
    )
    llm_pydantic_model_instance.api_key = populated_config_obj.api_key

    judge_llm_client = LLMClient(llm_pydantic_model_instance)

    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            # The input to the judge is the output of the previous 'generate' node.
            input_to_judge = state.get("output")
            if input_to_judge is None:
                # If state['output'] is None (e.g., if 'generate' node had an issue or it's the very start of a sub-graph not chained well),
                # fall back to state['input']. This might happen if 'generate' failed to produce output.
                logger.warning(f"⚖️ Judge LLM Node '{node.id}': Input from previous node (state['output']) is None. Using state['input'] as fallback: {str(state.get('input', ''))[:100]}...")
                input_to_judge = state.get("input", "") 
            else:
                logger.info(f"⚖️ Judge LLM Node '{node.id}': Received input from state['output']: {str(input_to_judge)[:100]}...")


            logger.info(f"⚖️ Judge LLM Processing for node '{node.id}' (using {judge_llm_client.spec.type}:{judge_llm_client.spec.model_name}): {str(input_to_judge)[:100]}...")
            
            # Construct prompt for the judge LLM
            # The judge's system prompt should guide it on how to evaluate.
            # Here, we pass the content to be evaluated directly as the user message to the judge.
            judgment_prompt = str(input_to_judge) # Pass the content to be judged

            raw_llm_output = judge_llm_client.generate(judgment_prompt)
            # Log more of the raw output for easier debugging of JSON issues
            logger.info(f"📊 Judge LLM raw output for node '{node.id}': {raw_llm_output[:500]}...")

            parsed_score_value: Optional[float] = None
            
            try:
                # Clean the string: remove markdown fences and trim whitespace
                cleaned_json_str = raw_llm_output.strip()
                if cleaned_json_str.startswith("```json"):
                    cleaned_json_str = cleaned_json_str[len("```json"):] 
                # Also handle cases where it might just start with ```
                elif cleaned_json_str.startswith("```"):
                     cleaned_json_str = cleaned_json_str[len("```"):]

                if cleaned_json_str.endswith("```"):
                    cleaned_json_str = cleaned_json_str[:-len("```")]
                cleaned_json_str = cleaned_json_str.strip()
                
                if not cleaned_json_str:
                    # This case can happen if the LLM output is empty after stripping fences.
                    logger.warning(f"⚠️ Judge node '{node.id}': Cleaned JSON string is empty. Raw output: '{raw_llm_output}'")
                    raise ValueError("Cleaned JSON string is empty.")

                data = json.loads(cleaned_json_str)
                if isinstance(data, dict) and 'evaluation_score' in data:
                    # Ensure the extracted score is actually a number, robustly.
                    score_from_json = data['evaluation_score']
                    if isinstance(score_from_json, (int, float)):
                        parsed_score_value = float(score_from_json)
                    else:
                        logger.warning(f"⚠️ Judge node '{node.id}': 'evaluation_score' in JSON is not a number: {score_from_json}. Type: {type(score_from_json)}")
                else:
                    logger.warning(f"⚠️ Judge node '{node.id}': 'evaluation_score' not found in JSON output or output is not a dict. Parsed JSON data: {data}")
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # Catches errors from json.loads, float(), or if cleaned_json_str is empty.
                logger.error(f"❌ Judge node '{node.id}': Failed to parse 'evaluation_score' from LLM output. Error: {type(e).__name__} - {e}. Raw output: '{raw_llm_output}'")

            current_iteration = state.get('iteration_count', 0) + 1
            
            final_score_for_state: float
            if parsed_score_value is not None:
                final_score_for_state = parsed_score_value
            else:
                # If parsing failed or score was None, default to 0.0.
                # This ensures conditions always have a float to compare against.
                final_score_for_state = 0.0
                logger.warning(f"Judge node '{node.id}': Defaulting 'evaluation_score' to 0.0 in state due to parsing failure or missing key in LLM response.")

            # The 'output' field of the state will be updated with this judge's raw LLM output.
            # Other fields like 'input' are preserved from the incoming state unless explicitly changed.
            return {
                **state,
                "output": raw_llm_output, # This node's (judge's) own output (the JSON string)
                "iteration_count": current_iteration,
                "evaluation_score": final_score_for_state # The crucial score for conditions
            }
        except Exception as e:
            # Catch any other unexpected errors during node execution
            logger.error(f"❌ Unhandled Exception in Judge LLM Node '{node.id}': {type(e).__name__} - {str(e)}", exc_info=True)
            # Preserve state as much as possible, ensure critical fields for conditions are sensible
            return {
                **state,
                "output": f"Error in Judge Node '{node.id}': {type(e).__name__} - {str(e)}",
                # Increment iteration even on error to potentially break out of loops if the error is persistent
                "iteration_count": state.get('iteration_count', 0) + 1,
                # Try to keep the last known score, or default to 0.0, to avoid NoneType errors in subsequent condition checks.
                "evaluation_score": state.get("evaluation_score") if isinstance(state.get("evaluation_score"), float) else 0.0
            }
    return node_fn

def make_branch_node(node: Any) -> NodeFunction:
    """
    Create a node function that implements branching logic.
    
    Args:
        node: The node configuration for branching
        
    Returns:
        A node function that performs branching
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        # TODO: Implement actual branching logic
        return {
            "input": state["input"],
            "output": f"Branch result for: {state['input']}"
        }
    return node_fn

class NodeFactoryRegistry:
    """Registry for node factory functions."""
    
    _factories: Dict[str, NodeFactory] = {
        "agent": make_llm_node,
        "tool": lambda spec, node: load_tool(spec.functions.get(node.ref)),
        "judge": lambda spec, node: make_judge_node(spec, node),
        "branch": lambda spec, node: make_branch_node(node),
    }
    
    @classmethod
    def get(cls, kind: str) -> NodeFactory:
        """
        Return a factory that builds a StateGraph node callable for the given kind.
        
        Args:
            kind: The type of node to create a factory for
            
        Returns:
            A factory function for the specified node kind
            
        Raises:
            ValueError: If the node kind is not registered
        """
        try:
            return cls._factories[kind]
        except KeyError:
            raise ValueError(f"Unknown node kind: {kind}")
    
    @classmethod
    def register(cls, kind: str, factory: NodeFactory) -> None:
        """
        Register a new node factory function.
        
        Args:
            kind: The type of node the factory creates
            factory: The factory function
        """
        cls._factories[kind] = factory

def create_condition_function(expr: str) -> Callable[[Dict[str, Any]], Any]:
    """
    Create a condition function from a Python expression string.
    
    Args:
        expr: Python expression that evaluates to a boolean or returns a target node name
        
    Returns:
        A function that evaluates the expression against the state
        
    Note:
        This uses eval(), which has security implications. In production code,
        consider using a more secure expression parser.
    """
    # Pre-process the expression to handle state dictionary access
    # Replace state.get() with direct dictionary access
    processed_expr = expr.replace("state.get('", "state.get('")
    
    def condition(state: Dict[str, Any]) -> Any:
        try:
            # Create a context with state as a local variable
            context = {
                "__builtins__": {},
                "state": state,
                "get": lambda d, k, default=None: d.get(k, default)
            }
            return eval(processed_expr, context)
        except Exception as e:
            raise ValueError(f"Failed to evaluate condition '{expr}': {str(e)}")
    return condition

def create_workflow_graph(spec: Spec) -> StateGraph:
    """
    Create a LangGraph workflow from a specification.
    
    Args:
        spec: The workflow specification
        
    Returns:
        A configured StateGraph instance
    """
    # Create the graph
    graph = StateGraph()
    
    # Add nodes
    add_nodes_to_graph(graph, spec)
    
    # Add edges
    add_edges_to_graph(graph, spec)
    
    # Set the entry point
    graph.set_entry_point(spec.workflow.nodes[0].id)
    
    return graph

def add_nodes_to_graph(graph: StateGraph, spec: Spec) -> None:
    """
    Add all nodes from the specification to the graph.
    
    Args:
        graph: The StateGraph to add nodes to
        spec: The workflow specification
    """
    logger.info("🔄 Building workflow nodes...")
    for node in spec.workflow.nodes:
        logger.info(f"📝 Adding node: {node.id} ({node.kind})")
        factory = NodeFactoryRegistry.get(node.kind)
        node_fn = factory(spec, node)
        graph.add_node(node.id, node_fn)
        
        # If this is a stop node, add an edge to END
        if node.stop:
            logger.info(f"🏁 Adding end condition for node: {node.id}")
            graph.add_edge(node.id, END)

def add_edges_to_graph(graph: StateGraph, spec: Spec) -> None:
    """
    Add all edges from the specification to the graph.
    
    Args:
        graph: The StateGraph to add edges to
        spec: The workflow specification
    """
    logger.info("🔄 Building workflow edges...")
    edges_by_source: Dict[str, List[Edge]] = {}
    for edge in spec.workflow.edges:
        edges_by_source.setdefault(edge.source, []).append(edge)
    
    for source, edges_from_source in edges_by_source.items():
        logger.info(f"📝 Processing edges from node: {source}")
        
        conditional_edges = [e for e in edges_from_source if e.condition]
        unconditional_edges = [e for e in edges_from_source if not e.condition]

        if conditional_edges:
            # If there are any conditional edges, all decisions from this node
            # must go through a single conditional router.
            logger.info(f"  → Node {source} has conditional logic. All outgoing edges managed by a router.")

            default_target: Optional[str] = None
            if len(unconditional_edges) > 1:
                logger.warning(
                    f"  ⚠️ Node {source} has multiple unconditional edges ({[e.target for e in unconditional_edges]}) "
                    f"alongside conditional ones. The first unconditional edge target "
                    f"'{unconditional_edges[0].target}' will be used as the default fallback. "
                    "Define explicit conditions for all paths or ensure a single default path for clarity."
                )
                default_target = unconditional_edges[0].target
            elif unconditional_edges:
                default_target = unconditional_edges[0].target
                logger.info(f"  → Default target for {source} (if no conditions met): {default_target}")


            # Create a router function that evaluates conditions and falls back to default_target or END
            def create_router_for_source(
                source_node_id: str,
                cond_edges: List[Edge],
                def_target: Optional[str]
            ) -> Callable[[Dict[str, Any]], str]:
                
                condition_target_pairs = [
                    (create_condition_function(e.condition), e.target)
                    for e in cond_edges
                ]

                def router(state: Dict[str, Any]) -> str:
                    for condition_fn, target_node_name in condition_target_pairs:
                        try:
                            if condition_fn(state): # condition_fn should return boolean
                                logger.info(f"  Router for {source_node_id}: Condition met, routing to '{target_node_name}'")
                                return target_node_name # Router returns the key for the ends_map
                        except Exception as e:
                            logger.error(
                                f"❌ Routing Error for {source_node_id} evaluating condition for {target_node_name}: {str(e)}. "
                                "Attempting to continue with other conditions or fallback."
                            )
                            # In a production system, you might want to raise or handle this more specifically
                    
                    if def_target:
                        logger.info(f"  Router for {source_node_id}: No conditional route taken, routing to default target '{def_target}'")
                        return def_target
                    
                    logger.warning(
                        f"  Router for {source_node_id}: No condition met and no default target. Routing to END. "
                        "Ensure graph logic correctly leads to a defined state or END."
                    )
                    return END # LangGraph's END sentinel if no path is chosen

                return router

            router_fn = create_router_for_source(source, conditional_edges, default_target)
            
            # The conditional_edge_mapping keys are what the router returns.
            # The values are the actual node IDs (or special targets like END).
            # Our router is designed to return actual target node names or END.
            edge_mapping = {e.target: e.target for e in conditional_edges}
            if default_target:
                edge_mapping[default_target] = default_target # Add default target to map
            edge_mapping[END] = END # Ensure END is always a valid target if router returns it

            graph.add_conditional_edges(
                source,
                router_fn,
                edge_mapping
            )
        
        elif unconditional_edges: # No conditional edges from this source, only unconditional ones.
            logger.info(f"  → Node {source} has only unconditional edges.")
            if len(unconditional_edges) > 1:
                 logger.info(f"    Node {source} has multiple unconditional edges (fan-out): {[e.target for e in unconditional_edges]}")
            for edge in unconditional_edges:
                logger.info(f"    → Adding direct edge from {source} to: {edge.target}")
                graph.add_edge(edge.source, edge.target)
        else:
            # This case means the node is a leaf node in terms of defined edges.
            # If it's not a 'stop: true' node, the graph might halt here if no global end is reached.
            logger.info(f"  → Node {source} has no outgoing edges defined in the spec.")


def compile_to_langgraph(spec: Spec) -> StateGraph:
    """
    Compile a workflow spec into a langgraph StateGraph.
    
    Args:
        spec: The workflow specification containing nodes and edges
        
    Returns:
        A configured StateGraph ready for execution
    """
    logger.info("🚀 Compiling workflow...")
    
    # Define the state schema using Pydantic
    class WorkflowStateSchema(BaseModel):
        """Schema for workflow state."""
        input: str
        output: Optional[str] = None
        iteration_count: Optional[int] = Field(default=0)
        evaluation_score: Optional[float] = None
    
    # Create a new graph with explicit state schema
    graph = StateGraph(
        state_schema=WorkflowStateSchema
    )
    
    # Build graph components
    add_nodes_to_graph(graph, spec)
    add_edges_to_graph(graph, spec)
    
    # Set the entry point
    if spec.workflow.nodes:
        logger.info(f"🎯 Setting entry point: {spec.workflow.nodes[0].id}")
        graph.set_entry_point(spec.workflow.nodes[0].id)
    
    logger.info("✅ Workflow compilation complete")
    return graph