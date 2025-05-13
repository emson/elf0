# src/awa/core/compiler.py
from typing import Callable, Any, Dict, TypedDict, Protocol
from langgraph.graph import StateGraph, END
from .llm_client import LLMClient
from .spec import Spec, WorkflowNode

class WorkflowState(TypedDict):
    input: str
    output: str | None

class NodeFunction(Protocol):
    """Protocol defining the interface for node functions."""
    def __call__(self, state: WorkflowState) -> WorkflowState: ...

class NodeFactory(Protocol):
    """Protocol defining the interface for node factory functions."""
    def __call__(self, spec: Spec, node: WorkflowNode) -> NodeFunction: ...

def make_llm_node(llm_config: Dict[str, Any]) -> NodeFunction:
    """
    Create a node function that uses an LLM to process input and generate output.
    
    Args:
        llm_config: Dictionary containing LLM configuration parameters
        
    Returns:
        A function that processes state using the LLM
    """
    llm = LLMClient(llm_config)
    
    def node_fn(state: WorkflowState) -> WorkflowState:
        try:
            response = llm.generate(state["input"])
            return {
                "input": state["input"],
                "output": response
            }
        except Exception as e:
            return {
                "input": state["input"],
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
        # TODO: Implement actual tool execution
        return {
            "input": state["input"],
            "output": f"Tool execution result for: {state['input']}"
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
        # TODO: Implement actual judgment logic
        return {
            "input": state["input"],
            "output": f"Judgment for: {state['input']}"
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
        "agent": lambda spec, node: make_llm_node(spec.llms.get(node.ref)),
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

def create_condition_function(expr: str) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition function from a Python expression string.
    
    Args:
        expr: Python expression that evaluates to a boolean
        
    Returns:
        A function that evaluates the expression against the state
        
    Note:
        This uses eval(), which has security implications. In production code,
        consider using a more secure expression parser.
    """
    def condition(state: Dict[str, Any]) -> bool:
        try:
            # Restricted evaluation context
            return bool(eval(expr, {"__builtins__": {}}, state))
        except Exception as e:
            raise ValueError(f"Failed to evaluate condition '{expr}': {str(e)}")
    return condition

def add_nodes_to_graph(graph: StateGraph, spec: Spec) -> None:
    """
    Add all nodes from the specification to the graph.
    
    Args:
        graph: The StateGraph to add nodes to
        spec: The workflow specification
    """
    for node in spec.workflow.nodes:
        factory = NodeFactoryRegistry.get(node.kind)
        node_fn = factory(spec, node)
        graph.add_node(node.id, node_fn)
        
        # If this is a stop node, add an edge to END
        if node.stop:
            graph.add_edge(node.id, END)

def add_edges_to_graph(graph: StateGraph, spec: Spec) -> None:
    """
    Add all edges from the specification to the graph.
    
    Args:
        graph: The StateGraph to add edges to
        spec: The workflow specification
    """
    for edge in spec.workflow.edges:
        if edge.condition:
            # Add conditional edge
            condition_fn = create_condition_function(edge.condition)
            graph.add_conditional_edges(
                edge.source,
                condition_fn,
                {
                    True: edge.target,
                    False: END
                }
            )
        else:
            # Add direct edge
            graph.add_edge(edge.source, edge.target)

def set_entry_point(graph: StateGraph, spec: Spec) -> None:
    """
    Set the entry point for the graph.
    
    Args:
        graph: The StateGraph to set the entry point for
        spec: The workflow specification
    """
    if spec.workflow.nodes:
        graph.set_entry_point(spec.workflow.nodes[0].id)

def compile_to_langgraph(spec: Spec) -> StateGraph:
    """
    Compile a workflow spec into a langgraph StateGraph.
    
    Args:
        spec: The workflow specification containing nodes and edges
        
    Returns:
        A configured StateGraph ready for execution
    """
    # Create a new graph with input/output schemas
    graph = StateGraph(
        input=WorkflowState,
        output=WorkflowState
    )
    
    # Build graph components
    add_nodes_to_graph(graph, spec)
    add_edges_to_graph(graph, spec)
    set_entry_point(graph, spec)
    
    return graph