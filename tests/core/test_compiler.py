import pytest
from elf.core.compiler import (
    compile_to_langgraph,
    WorkflowState,
    NodeFactoryRegistry,
    create_condition_function
)
from elf.core.spec import Spec, LLM, WorkflowNode, Edge, Workflow
from elf.core.config import load_env_file

@pytest.fixture(autouse=True)
def load_env():
    """Load environment variables before each test."""
    load_env_file()

# Test data
VALID_LLM_CONFIG = {
    "type": "openai",
    "model_name": "gpt-4.1-mini",
    "temperature": 0.5,
    "params": {}
}

def create_minimal_spec() -> Spec:
    """Helper function to create a minimal valid spec for testing."""
    return Spec(
        version="0.1",
        llms={"llm1": LLM(**VALID_LLM_CONFIG)},
        workflow=Workflow(
            type="sequential",
            nodes=[
                WorkflowNode(id="start", kind="agent", ref="llm1"),
                WorkflowNode(id="end", kind="agent", ref="llm1", stop=True)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
    )

def test_compile_minimal_workflow():
    """Test compiling a minimal valid workflow."""
    spec = create_minimal_spec()
    graph = compile_to_langgraph(spec)
    
    # Verify graph was created successfully
    assert graph is not None
    # Only verify that the graph was created, not its internal structure

def test_compile_workflow_with_conditional_edges():
    """Test compiling a workflow with conditional edges."""
    spec = Spec(
        version="0.1",
        llms={"llm1": LLM(**VALID_LLM_CONFIG)},
        workflow=Workflow(
            type="sequential",
            nodes=[
                WorkflowNode(id="start", kind="agent", ref="llm1"),
                WorkflowNode(id="branch1", kind="agent", ref="llm1"),
                WorkflowNode(id="branch2", kind="agent", ref="llm1"),
                WorkflowNode(id="end", kind="agent", ref="llm1", stop=True)
            ],
            edges=[
                Edge(source="start", target="branch1", condition="state.get('iteration_count', 0) < 2"),
                Edge(source="start", target="branch2", condition="state.get('iteration_count', 0) >= 2"),
                Edge(source="branch1", target="end"),
                Edge(source="branch2", target="end")
            ]
        )
    )
    
    # Verify that compilation succeeds for a complex workflow
    graph = compile_to_langgraph(spec)
    assert graph is not None

def test_condition_function_evaluation():
    """Test condition function creation and evaluation."""
    # Test basic condition evaluation
    condition_fn = create_condition_function("state.get('iteration_count', 0) < 2")
    
    # Test with iteration count below threshold
    state = {"iteration_count": 1}
    assert condition_fn(state) is True
    
    # Test with iteration count at threshold
    state = {"iteration_count": 2}
    assert condition_fn(state) is False
    
    # Test with missing key (should use default value)
    state = {}
    assert condition_fn(state) is True  # Should use default value 0
    
    # Test with more complex condition
    complex_condition = "state.get('iteration_count', 0) < 2 and state.get('evaluation_score', 0) > 3"
    complex_fn = create_condition_function(complex_condition)
    
    # Test complex condition with both values
    state = {"iteration_count": 1, "evaluation_score": 4}
    assert complex_fn(state) is True
    
    # Test complex condition with one value missing
    state = {"evaluation_score": 4}
    assert complex_fn(state) is True  # Should use default for iteration_count

def test_node_factory_registry():
    """Test node factory registration and retrieval."""
    # Test getting registered factory
    factory = NodeFactoryRegistry.get("agent")
    assert factory is not None
    
    # Test getting unknown factory
    with pytest.raises(ValueError, match="Unknown node kind"):
        NodeFactoryRegistry.get("unknown_kind")
    
    # Test registering new factory
    def test_factory(spec, node):
        def node_fn(state):
            return state
        return node_fn
    
    NodeFactoryRegistry.register("test_kind", test_factory)
    assert NodeFactoryRegistry.get("test_kind") is not None

def test_workflow_state_management():
    """Test workflow state handling during execution."""
    spec = create_minimal_spec()
    graph = compile_to_langgraph(spec)
    
    # Verify that the graph was created successfully
    assert graph is not None
    # We'll test actual execution in integration tests 