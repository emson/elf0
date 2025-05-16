import pytest
from pathlib import Path
from elf.core.spec import Spec, LLM, WorkflowNode, Edge, Workflow

# Test data
VALID_LLM_CONFIG = {
    "type": "openai",
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
    """Test creating a valid spec."""
    spec = Spec(
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
    assert spec.version == "0.1"
    assert "llm1" in spec.llms
    assert spec.workflow.type == "sequential"

def test_workflow_edge_validation():
    """Test that workflow edges must reference valid nodes."""
    with pytest.raises(ValueError, match="Edge source 'invalid' not found in nodes"):
        Spec(
            version="0.1",
            llms={"llm1": LLM(**VALID_LLM_CONFIG)},
            workflow=Workflow(
                type="sequential",
                nodes=[
                    WorkflowNode(id="start", kind="agent", ref="llm1"),
                    WorkflowNode(id="end", kind="agent", ref="llm1", stop=True)
                ],
                edges=[
                    Edge(source="invalid", target="end")
                ]
            )
        )

def test_node_reference_validation():
    """Test that node references must exist in the spec."""
    with pytest.raises(ValueError, match="Node 'start' references unknown LLM 'invalid'"):
        Spec(
            version="0.1",
            llms={"llm1": LLM(**VALID_LLM_CONFIG)},
            workflow=Workflow(
                type="sequential",
                nodes=[
                    WorkflowNode(id="start", kind="agent", ref="invalid"),
                    WorkflowNode(id="end", kind="agent", ref="llm1", stop=True)
                ],
                edges=[
                    Edge(source="start", target="end")
                ]
            )
        )

def test_spec_from_file(tmp_path):
    """Test loading a spec from a YAML file."""
    spec_yaml = """
version: "0.1"
llms:
  llm1:
    type: openai
    model_name: gpt-4.1-mini
    temperature: 0.5
workflow:
  type: sequential
  nodes:
    - id: start
      kind: agent
      ref: llm1
    - id: end
      kind: agent
      ref: llm1
      stop: true
  edges:
    - source: start
      target: end
"""
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(spec_yaml)
    
    spec = Spec.from_file(str(spec_file))
    assert spec.version == "0.1"
    assert "llm1" in spec.llms
    assert spec.workflow.type == "sequential"
    assert len(spec.workflow.nodes) == 2
    assert spec.workflow.nodes[0].id == "start"
    assert spec.workflow.nodes[1].id == "end"
    assert spec.workflow.nodes[0].ref == "llm1"
    assert spec.workflow.nodes[1].ref == "llm1"
    assert spec.workflow.edges[0].source == "start"
    assert spec.workflow.edges[0].target == "end" 