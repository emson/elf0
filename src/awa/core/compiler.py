from typing import Callable, Any, Dict, TypedDict
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from .llm_client import LLMClient

class WorkflowState(TypedDict):
    input: str
    output: str | None

def make_llm_node(llm_config: Dict[str, Any]) -> Callable:
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

def load_tool(fn: Any) -> Callable:
    """
    Create a node function that executes a tool/function.
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        # TODO: Implement actual tool execution
        return {
            "input": state["input"],
            "output": f"Tool execution result for: {state['input']}"
        }
    return node_fn

def make_judge_node(llm: Any) -> Callable:
    """
    Create a node function that uses an LLM to evaluate/judge the state.
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        # TODO: Implement actual judgment logic
        return {
            "input": state["input"],
            "output": f"Judgment for: {state['input']}"
        }
    return node_fn

def make_branch_node(node: Any) -> Callable:
    """
    Create a node function that implements branching logic.
    """
    def node_fn(state: WorkflowState) -> WorkflowState:
        # TODO: Implement actual branching logic
        return {
            "input": state["input"],
            "output": f"Branch result for: {state['input']}"
        }
    return node_fn

# Registry mapping from node.kind to factory function
_NODE_FACTORIES: Dict[str, Callable[[Any, Any], Callable]] = {
    "agent": lambda spec, node: make_llm_node(spec.llms.get(node.ref)),
    "tool": lambda spec, node: load_tool(spec.functions.get(node.ref)),
    "judge": lambda spec, node: make_judge_node(spec.llms.get(node.ref)),
    "branch": lambda spec, node: make_branch_node(node),
}

def get_node_factory(kind: str) -> Callable:
    """
    Return a factory that builds a StateGraph node callable for the given kind.
    """
    try:
        return _NODE_FACTORIES[kind]
    except KeyError:
        raise ValueError(f"Unknown node kind: {kind}")

def get_edge_condition(expr: str) -> Callable[[Dict[str, Any]], bool]:
    """
    Given a Python expression string, return a function that evaluates
    it against the current state dict and returns a boolean.
    """
    def condition(state: Dict[str, Any]) -> bool:
        return bool(eval(expr, {}, state))
    return condition

def compile_to_langgraph(spec: Any) -> StateGraph:
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
    
    # Add nodes
    for node in spec.workflow.nodes:
        factory = get_node_factory(node.kind)
        node_fn = factory(spec, node)
        graph.add_node(node.id, node_fn)
        
        # If this is a stop node, add an edge to END
        if node.stop:
            graph.add_edge(node.id, END)
    
    # Add edges between nodes
    for edge in spec.workflow.edges:
        if edge.condition:
            # Add conditional edge
            condition_fn = get_edge_condition(edge.condition)
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
    
    # Set the entry point to the first node
    if spec.workflow.nodes:
        graph.set_entry_point(spec.workflow.nodes[0].id)
    
    return graph