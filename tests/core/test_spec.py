import pytest
from pathlib import Path
from elf.core.spec import Spec, LLM, WorkflowNode, Edge, Workflow

# Test data
VALID_LLM_CONFIG = {
    "_type": "openai",
    "model_name": "gpt-4.1-mini",
    "temperature": 0.5,
    "params": {}
}

VALID_NODE = {
    "id": "node1",
    "kind": "agent",
    "ref": "llm1"
}

VALID_EDGE = {
    "source": "node1",
    "target": "node2"
}

def test_create_valid_spec():
    """Test creating a Spec instance with valid data."""
    # Create a minimal valid workflow
    workflow = Workflow(
        _type="sequential",
        nodes=[WorkflowNode(**VALID_NODE)],
        edges=[]
    )
    
    # Create the spec
    spec = Spec(
        version="0.1",
        description="Test spec",
        llms={"llm1": LLM(**VALID_LLM_CONFIG)},
        workflow=workflow
    )
    
    # Verify the spec was created correctly
    assert spec.version == "0.1"
    assert spec.description == "Test spec"
    assert "llm1" in spec.llms
    assert spec.llms["llm1"].model_name == "gpt-4.1-mini"
    assert len(spec.workflow.nodes) == 1
    assert spec.workflow.nodes[0].id == "node1"

def test_workflow_edge_validation():
    """Test that workflow edges must reference valid nodes."""
    # First create a valid workflow with two nodes
    workflow = Workflow(
        _type="sequential",
        nodes=[
            WorkflowNode(**VALID_NODE),
            WorkflowNode(id="node2", kind="agent", ref="llm1")
        ],
        edges=[Edge(source="node1", target="node2")]
    )
    
    # Create a valid spec first
    spec = Spec(
        version="0.1",
        llms={"llm1": LLM(**VALID_LLM_CONFIG)},
        workflow=workflow
    )
    
    # Now modify the workflow to have an invalid edge
    spec.workflow.edges.append(Edge(source="node1", target="nonexistent"))
    
    # Attempting to validate the spec should raise a validation error
    with pytest.raises(ValueError, match="Edge target 'nonexistent' not found in nodes"):
        spec.model_validate(spec.model_dump())

def test_node_reference_validation():
    """Test that nodes must reference existing LLMs or functions."""
    # Create a workflow with a node referencing a non-existent LLM
    workflow = Workflow(
        _type="sequential",
        nodes=[WorkflowNode(id="node1", kind="agent", ref="nonexistent_llm")],
        edges=[]
    )
    
    # Attempting to create a spec with this workflow should raise a validation error
    with pytest.raises(ValueError, match="Node 'node1' references unknown LLM 'nonexistent_llm'"):
        Spec(
            version="0.1",
            llms={"llm1": LLM(**VALID_LLM_CONFIG)},
            workflow=workflow
        )

def test_spec_from_file(tmp_path):
    """Test loading a spec from a YAML file."""
    # Create a minimal valid YAML spec
    yaml_content = """
    version: "0.1"
    description: "Test spec from file"
    llms:
      llm1:
        _type: openai
        model_name: gpt-4.1-mini
        temperature: 0.5
    workflow:
      _type: sequential
      nodes:
        - id: node1
          kind: agent
          ref: llm1
      edges: []
    """
    
    # Write the YAML to a temporary file
    spec_file = tmp_path / "test_spec.yaml"
    spec_file.write_text(yaml_content)
    
    # Load the spec from the file
    spec = Spec.from_file(str(spec_file))
    
    # Verify the spec was loaded correctly
    assert spec.version == "0.1"
    assert spec.description == "Test spec from file"
    assert "llm1" in spec.llms
    assert spec.llms["llm1"].model_name == "gpt-4.1-mini"
    assert len(spec.workflow.nodes) == 1
    assert spec.workflow.nodes[0].id == "node1"
    assert spec.workflow.nodes[0].ref == "llm1" 