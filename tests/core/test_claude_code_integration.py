# tests/core/test_claude_code_integration.py
from unittest.mock import Mock

import pytest

from elf.core.compiler import NodeFactoryRegistry, make_claude_code_node
from elf.core.nodes.claude_code_node import ClaudeCodeError, ClaudeCodeNode
from elf.core.spec import Spec, WorkflowNode


class TestClaudeCodeNodeBasics:
    """Test basic Claude Code node functionality."""

    def test_claude_code_node_requires_prompt(self):
        """Test that Claude Code node requires a prompt configuration."""
        # Arrange
        config = {"task": "generate_code"}  # Missing prompt

        # Act & Assert
        with pytest.raises(ClaudeCodeError, match="requires a 'prompt'"):
            ClaudeCodeNode(config)

    def test_claude_code_node_accepts_valid_config(self):
        """Test that Claude Code node accepts valid configuration."""
        # Arrange
        config = {
            "task": "generate_code",
            "prompt": "Create a Python function"
        }

        # Act
        node = ClaudeCodeNode(config)

        # Assert
        assert node.task == "generate_code"
        assert node.prompt == "Create a Python function"


class TestClaudeCodeFactory:
    """Test Claude Code node factory registration and creation."""

    def test_claude_code_factory_is_registered(self):
        """Test that claude_code factory is registered in NodeFactoryRegistry."""
        # Act
        factory = NodeFactoryRegistry.get("claude_code")

        # Assert
        assert factory == make_claude_code_node

    def test_make_claude_code_node_returns_callable(self):
        """Test that make_claude_code_node returns a callable function."""
        # Arrange
        spec = Mock()
        node = WorkflowNode(
            id="test_node",
            kind="claude_code",
            config={
                "task": "chat",
                "prompt": "Hello Claude Code!"
            }
        )

        # Act
        node_fn = make_claude_code_node(spec, node)

        # Assert
        assert callable(node_fn)

    def test_make_claude_code_node_handles_invalid_config(self):
        """Test that make_claude_code_node handles invalid configuration gracefully."""
        # Arrange
        spec = Mock()
        node = WorkflowNode(
            id="bad_node",
            kind="claude_code",
            config={"task": "chat"}  # Missing prompt
        )

        # Act
        node_fn = make_claude_code_node(spec, node)

        # Assert
        assert callable(node_fn)

        # Verify error handling by executing the function
        state = {"input": "test"}
        result = node_fn(state)
        assert "configuration error" in result["output"]


class TestClaudeCodeWorkflowIntegration:
    """Test Claude Code integration with workflow specs."""

    def test_workflow_validates_with_claude_code_node(self):
        """Test that workflow specs validate correctly with claude_code nodes."""
        # Arrange
        spec_data = {
            "version": "0.1",
            "runtime": "langgraph",
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "code_generator",
                        "kind": "claude_code",
                        "config": {
                            "task": "generate_code",
                            "prompt": "Create a Python function"
                        }
                    }
                ],
                "edges": []
            }
        }

        # Act
        spec = Spec.model_validate(spec_data)

        # Assert
        assert spec.workflow is not None
        assert len(spec.workflow.nodes) == 1
        assert spec.workflow.nodes[0].kind == "claude_code"

    def test_workflow_requires_claude_code_config(self):
        """Test that workflow validation requires config for claude_code nodes."""
        # Arrange
        spec_data = {
            "version": "0.1",
            "runtime": "langgraph",
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "code_generator",
                        "kind": "claude_code"
                        # Missing config
                    }
                ],
                "edges": []
            }
        }

        # Act & Assert
        with pytest.raises(ValueError, match="must have configuration"):
            Spec.model_validate(spec_data)


class TestClaudeCodeExampleWorkflows:
    """Test that example workflows are valid."""

    def test_claude_code_example_workflow_is_valid(self):
        """Test that the Claude Code example workflow validates."""
        # Act
        spec = Spec.from_file("specs/examples/claude_code_example.yaml")

        # Assert
        assert spec.workflow is not None
        assert len(spec.workflow.nodes) > 0

        # Verify it contains claude_code nodes
        claude_code_nodes = [n for n in spec.workflow.nodes if n.kind == "claude_code"]
        assert len(claude_code_nodes) > 0

    def test_claude_code_self_improvement_workflow_is_valid(self):
        """Test that the Claude Code self-improvement workflow validates."""
        # Act
        spec = Spec.from_file("specs/examples/claude_code_self_improvement.yaml")

        # Assert
        assert spec.workflow is not None
        assert len(spec.workflow.nodes) > 0

        # Verify it contains claude_code nodes
        claude_code_nodes = [n for n in spec.workflow.nodes if n.kind == "claude_code"]
        assert len(claude_code_nodes) > 0
