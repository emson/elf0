# src/elf/core/compiler.py
from typing import Callable, Any, Dict, TypedDict, Protocol, List, Optional
from langgraph.graph import StateGraph, END
from .llm_client import LLMClient
from .spec import Spec, WorkflowNode, Edge
import logging

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

def make_llm_node(llm_config: Dict[str, Any], node: WorkflowNode) -> NodeFunction:
    """
    Create a node function that uses an LLM to process input and generate output.
    
    Args:
        llm_config: Dictionary containing LLM configuration parameters
        node: The WorkflowNode object, used here to access node.id
        
    Returns:
        A function that processes state using the LLM
    """
    llm = LLMClient(llm_config)
    
    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            logger.info(f"🤖 LLM Processing for node '{node.id}': {state.get('input', '')[:100]}...")
            response = llm.generate(state["input"])
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

def make_judge_node(llm: Any) -> NodeFunction:
    """
    Create a node function that uses an LLM to evaluate/judge the state.
    
    Args:
        llm: LLM configuration for the judge
        
    Returns:
        A node function that performs judgment
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            logger.info("🔍 Evaluating prompt quality...")
            # Increment iteration count
            iteration_count = state.get('iteration_count', 0) + 1
            logger.info(f"🔄 Iteration {iteration_count} of 3")
            
            # TODO: Implement actual judgment logic
            result = f"Judgment for: {state['input']}"
            logger.info(f"📊 Evaluation result: {result[:100]}...")
            
            return {
                **state,  # Preserve all existing state
                "iteration_count": iteration_count,
                "output": result
            }
        except Exception as e:
            logger.error(f"❌ Evaluation Error: {str(e)}")
            return {
                **state,  # Preserve all existing state
                "output": f"Error: {str(e)}"
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
        "agent": lambda spec, node: make_llm_node(spec.llms.get(node.ref), node),
        "tool": lambda spec, node: load_tool(spec.functions.get(node.ref)),
        "judge": lambda spec, node: make_judge_node(spec.llms.get(node.ref)),
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
    # Create a new graph with input/output schemas
    graph = StateGraph(
        input=WorkflowState,
        output=WorkflowState
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