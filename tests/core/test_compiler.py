import pytest
from elf.core.compiler import (
    compile_to_langgraph,
    WorkflowState,
    NodeFactoryRegistry,
    create_condition_function,
    make_judge_node
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

# --- New tests for make_judge_node ---

@pytest.fixture
def minimal_spec_with_judge_llm() -> Spec:
    """Creates a minimal spec with an LLM configured for a judge node."""
    return Spec(
        version="0.1",
        llms={"judge_llm": LLM(**VALID_LLM_CONFIG)}, # Use the same valid config
        workflow=Workflow( # Dummy workflow, not directly used by make_judge_node test
            type="sequential",
            nodes=[WorkflowNode(id="judge1", kind="judge", ref="judge_llm")],
            edges=[]
        )
    )

def test_make_judge_node_evaluation_parsing(minimal_spec_with_judge_llm, mocker):
    """Test the JSON parsing and state updates in make_judge_node."""
    spec = minimal_spec_with_judge_llm
    judge_node_spec = spec.workflow.nodes[0] # The judge node

    # Test scenarios: (input_state_output, llm_mock_output, expected_score, expected_iteration_count, expected_node_output)
    scenarios = [
        # 1. Successful parsing
        ({"input": "initial_input", "output": "content_to_judge1"}, 
         '{"evaluation_score": 4.5, "feedback": "good"}', 
         4.5, 1, '{"evaluation_score": 4.5, "feedback": "good"}'),
        # 2. JSON with markdown fences
        ({"input": "initial_input", "output": "content_to_judge2", "iteration_count": 1}, 
         '```json\n{"evaluation_score": 3.0, "comment": "okay"}\n```', 
         3.0, 2, '```json\n{"evaluation_score": 3.0, "comment": "okay"}\n```'),
        # 3. Invalid JSON
        ({"input": "initial_input", "output": "content_to_judge3", "evaluation_score": 2.0}, 
         'not json', 
         0.0, 1, 'not json'), # Defaults to 0.0 if parsing fails, original state score not kept unless explicitly handled
        # 4. Valid JSON but missing 'evaluation_score' key
        ({"input": "initial_input", "output": "content_to_judge4", "iteration_count": 3}, 
         '{"feedback": "missing score"}', 
         0.0, 4, '{"feedback": "missing score"}'), # Defaults to 0.0
        # 5. Valid JSON but 'evaluation_score' is not a number
        ({"input": "initial_input", "output": "content_to_judge5"}, 
         '{"evaluation_score": "not_a_number"}', 
         0.0, 1, '{"evaluation_score": "not_a_number"}'), # Defaults to 0.0
        # 6. Empty string from LLM
        ({"input": "initial_input", "output": "content_to_judge6"}, 
         '', 
         0.0, 1, ''), # Defaults to 0.0
        # 7. LLM returns JSON with integer score
        ({"input": "initial_input", "output": "content_to_judge7"}, 
         '{"evaluation_score": 5}', 
         5.0, 1, '{"evaluation_score": 5}'),
        # 8. Input to judge is None (e.g. previous node failed), should use state['input']
        ({"input": "fallback_input", "output": None, "iteration_count": 0},
         '{"evaluation_score": 2.5}',
         2.5, 1, '{"evaluation_score": 2.5}'),
        # 9. Only ``` at start and end
        ({"input": "initial_input", "output": "content_to_judge9", "iteration_count": 1}, 
         '```\n{"evaluation_score": 1.0}\n```', 
         1.0, 2, '```\n{"evaluation_score": 1.0}\n```'),
    ]

    # Mock create_llm_config to avoid actual credential/config loading
    mocker.patch('elf.core.compiler.create_llm_config', 
                 return_value=LLM(**VALID_LLM_CONFIG)) # Changed LLMSpecModel to LLM

    for initial_state_parts, llm_response, expected_score, expected_iter_count, expected_raw_output in scenarios:
        
        # Set up the full initial state, ensuring all keys from WorkflowState are present
        initial_state: WorkflowState = {
            "input": initial_state_parts.get("input", "default_input"),
            "output": initial_state_parts.get("output"), # Can be None
            "iteration_count": initial_state_parts.get("iteration_count", 0),
            "evaluation_score": initial_state_parts.get("evaluation_score") # Can be None
        }

        # Mock LLMClient and its generate method
        mock_llm_client_instance = mocker.MagicMock()
        # Configure the generate method (which is also a MagicMock by default) to return the specific llm_response
        mock_llm_client_instance.generate.return_value = llm_response 
        # Make the LLMClient constructor return our mock instance
        mock_llm_client_constructor = mocker.patch('elf.core.compiler.LLMClient', return_value=mock_llm_client_instance)
        
        # Create the judge node function
        # We need to import make_judge_node if it's not already available globally in the test file
        judge_fn = make_judge_node(spec, judge_node_spec)
        
        # Execute the node function
        result_state = judge_fn(initial_state.copy()) # Pass a copy to avoid modifying the original in the loop

        # Assertions
        assert result_state["evaluation_score"] == expected_score, f"Scenario with LLM output '{llm_response}' failed evaluation_score."
        assert result_state["iteration_count"] == expected_iter_count, f"Scenario with LLM output '{llm_response}' failed iteration_count."
        assert result_state["output"] == expected_raw_output, f"Scenario with LLM output '{llm_response}' failed node output."
        
        # Verify LLMClient was called with the correct input
        # The judge node's prompt is just the input string it's supposed to judge.
        expected_judge_input = initial_state["output"] if initial_state["output"] is not None else initial_state["input"]
        mock_llm_client_instance.generate.assert_called_once_with(str(expected_judge_input))
        
        # Verify LLMClient was instantiated correctly
        # The Pydantic model instance passed to LLMClient is spec.llms[judge_node_spec.ref]
        # The create_llm_config mock handles the API key part
        # So, LLMClient should be called with the LLM model from the spec
        mock_llm_client_constructor.assert_called_with(spec.llms[judge_node_spec.ref]) 