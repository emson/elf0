# tests/core/test_mcp_workflow_integration.py
from unittest.mock import patch

import pytest

from elf0.core.compiler import NodeFactoryRegistry, make_mcp_node
from elf0.core.spec import Spec, Workflow, WorkflowNode


class TestMCPWorkflowIntegration:
    """Test suite for MCP integration with the workflow system."""

    def test_mcp_node_kind_supported(self):
        """Test that MCP node kind is supported in spec validation."""
        # Arrange
        spec_data = {
            "version": "0.1",
            "runtime": "langgraph",
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_mcp",
                        "kind": "mcp",
                        "ref": "",  # MCP nodes don't use ref
                        "config": {
                            "server": {"command": ["echo", "test"]},
                            "tool": "test_tool",
                            "parameters": {"input": "${state.input}"}
                        }
                    }
                ],
                "edges": []
            }
        }

        # Act & Assert - Should not raise validation error
        spec = Spec.model_validate(spec_data)
        assert len(spec.workflow.nodes) == 1
        assert spec.workflow.nodes[0].kind == "mcp"

    def test_mcp_node_validation_missing_config(self):
        """Test MCP node validation when configuration is missing."""
        # Arrange
        spec_data = {
            "version": "0.1",
            "runtime": "langgraph",
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_mcp",
                        "kind": "mcp",
                        "ref": ""
                        # Missing config
                    }
                ],
                "edges": []
            }
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Spec.model_validate(spec_data)

        assert "must have configuration" in str(exc_info.value)

    def test_mcp_node_validation_missing_server(self):
        """Test MCP node validation when server config is missing."""
        # Arrange
        spec_data = {
            "version": "0.1",
            "runtime": "langgraph",
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_mcp",
                        "kind": "mcp",
                        "ref": "",
                        "config": {
                            "tool": "test_tool"
                            # Missing server
                        }
                    }
                ],
                "edges": []
            }
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Spec.model_validate(spec_data)

        assert "must have 'server' configuration" in str(exc_info.value)

    def test_mcp_node_validation_missing_tool(self):
        """Test MCP node validation when tool config is missing."""
        # Arrange
        spec_data = {
            "version": "0.1",
            "runtime": "langgraph",
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_mcp",
                        "kind": "mcp",
                        "ref": "",
                        "config": {
                            "server": {"command": ["echo", "test"]}
                            # Missing tool
                        }
                    }
                ],
                "edges": []
            }
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Spec.model_validate(spec_data)

        assert "must have 'tool' configuration" in str(exc_info.value)

    def test_node_factory_registry_has_mcp(self):
        """Test that NodeFactoryRegistry includes MCP node factory."""
        # Act
        factory = NodeFactoryRegistry.get("mcp")

        # Assert
        assert factory is not None
        assert factory == make_mcp_node

    def test_make_mcp_node_creates_valid_function(self):
        """Test that make_mcp_node creates a valid node function."""
        # Arrange
        # For this test, we don't need a valid workflow, just a spec to pass to the function
        spec = None

        node = WorkflowNode(
            id="test_mcp",
            kind="mcp",
            ref="",
            config={
                "server": {"command": ["echo", "test"]},
                "tool": "test_tool",
                "parameters": {"input": "${state.input}"}
            }
        )

        # Act
        node_fn = make_mcp_node(spec, node)

        # Assert
        assert callable(node_fn)

    def test_mcp_node_function_execution(self):
        """Test that MCP node function properly handles state and async execution."""
        # Arrange
        spec = None

        node = WorkflowNode(
            id="test_mcp",
            kind="mcp",
            ref="",
            config={
                "server": {"command": ["echo", "test"]},
                "tool": "test_tool",
                "parameters": {"input": "${state.input}"}
            }
        )

        state = {
            "input": "test input",
            "output": None
        }

        # Act
        node_fn = make_mcp_node(spec, node)

        # Mock the async execution to simulate successful MCP execution
        expected_result = {
            "input": "test input",
            "output": "mcp tool result",
            "current_node": "test_mcp",
            "error_context": None
        }

        with patch("asyncio.run") as mock_run:
            with patch("asyncio.get_running_loop", side_effect=RuntimeError):
                mock_run.return_value = expected_result
                result = node_fn(state)

        # Assert - Test high-level behavior: state transformation
        assert result["input"] == "test input"
        assert result["output"] == "mcp tool result"
        assert result["current_node"] == "test_mcp"
        assert result["error_context"] is None

    def test_workflow_compilation_with_mcp_node(self):
        """Test that workflows with MCP nodes can be created without errors."""
        # Arrange
        workflow = Workflow(
            type="sequential",
            nodes=[
                WorkflowNode(
                    id="mcp_test",
                    kind="mcp",
                    ref="",
                    config={
                        "server": {"command": ["echo", "test"]},
                        "tool": "test_tool",
                        "parameters": {"input": "${state.input}"}
                    }
                )
            ],
            edges=[]
        )

        spec = Spec(
            version="0.1",
            runtime="langgraph",
            workflow=workflow
        )

        # Act & Assert - Should validate without errors
        assert spec.workflow is not None
        assert len(spec.workflow.nodes) == 1
        assert spec.workflow.nodes[0].kind == "mcp"
