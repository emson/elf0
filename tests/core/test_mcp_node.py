# tests/core/test_mcp_node.py
from unittest.mock import AsyncMock, patch

import pytest

from elf.core.mcp_client import MCPConnectionError, MCPToolError
from elf.core.nodes.mcp_node import MCPNode


class TestMCPNode:
    """Test suite for MCPNode implementation."""

    def test_node_initialization(self):
        """Test MCP node initialization with configuration."""
        # Arrange
        config = {
            "server": {"command": ["node", "server.js"]},
            "tool": "test_tool",
            "parameters": {"input": "${state.input}", "format": "json"}
        }

        # Act
        node = MCPNode(config)

        # Assert
        assert node.server_command == ["node", "server.js"]
        assert node.tool_name == "test_tool"
        assert node.parameters == {"input": "${state.input}", "format": "json"}
        assert node.client is None

    def test_parameter_binding_simple(self):
        """Test simple parameter binding from state."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {"input": "${state.user_input}", "static": "value"}
        }
        node = MCPNode(config)
        state = {"user_input": "hello world", "other": "data"}

        # Act
        bound_params = node._bind_parameters(state)

        # Assert
        assert bound_params == {"input": "hello world", "static": "value"}

    def test_parameter_binding_with_fallback(self):
        """Test parameter binding with missing state values."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {"input": "${state.missing_key}", "static": "value"}
        }
        node = MCPNode(config)
        state = {"user_input": "hello world"}

        # Act
        bound_params = node._bind_parameters(state)

        # Assert
        assert bound_params == {"input": "${state.missing_key}", "static": "value"}

    def test_parameter_binding_no_template(self):
        """Test parameter binding without template variables."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {"input": "direct_value", "number": 42}
        }
        node = MCPNode(config)
        state = {"user_input": "hello world"}

        # Act
        bound_params = node._bind_parameters(state)

        # Assert
        assert bound_params == {"input": "direct_value", "number": 42}

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful MCP node execution."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {"input": "${state.input}"}
        }
        node = MCPNode(config)
        state = {"input": "test data"}

        with patch("elf.core.nodes.mcp_node.SimpleMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.call_tool.return_value = {"output": "tool result"}
            mock_client.disconnect = AsyncMock()
            mock_client_class.return_value = mock_client

            # Act
            result_state = await node.execute(state)

            # Assert
            assert "mcp_result" in result_state
            assert result_state["mcp_result"] == {"output": "tool result"}
            assert result_state["input"] == "test data"  # Original state preserved
            mock_client.connect.assert_called_once()
            mock_client.call_tool.assert_called_once_with("test_tool", {"input": "test data"})
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_connection_failure(self):
        """Test MCP node execution with connection failure."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {}
        }
        node = MCPNode(config)
        state = {"input": "test data"}

        with patch("elf.core.nodes.mcp_node.SimpleMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.return_value = False  # Connection failed
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(MCPConnectionError) as exc_info:
                await node.execute(state)

            assert "Failed to connect" in str(exc_info.value)
            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_error(self):
        """Test MCP node execution with tool execution error."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "failing_tool",
            "parameters": {}
        }
        node = MCPNode(config)
        state = {"input": "test data"}

        with patch("elf.core.nodes.mcp_node.SimpleMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.call_tool.side_effect = MCPToolError("Tool execution failed")
            mock_client.disconnect = AsyncMock()
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(MCPToolError) as exc_info:
                await node.execute(state)

            assert "Tool execution failed" in str(exc_info.value)
            mock_client.disconnect.assert_called_once()  # Ensure cleanup

    @pytest.mark.asyncio
    async def test_execute_ensures_cleanup(self):
        """Test that disconnect is always called even on exceptions."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {}
        }
        node = MCPNode(config)
        state = {"input": "test data"}

        with patch("elf.core.nodes.mcp_node.SimpleMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.call_tool.side_effect = Exception("Unexpected error")
            mock_client.disconnect = AsyncMock()
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await node.execute(state)

            assert "Unexpected error" in str(exc_info.value)
            mock_client.disconnect.assert_called_once()  # Cleanup happened

    def test_parameter_binding_edge_cases(self):
        """Test parameter binding with edge cases."""
        # Arrange
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "test_tool",
            "parameters": {
                "empty_template": "${state.}",  # Malformed template
                "non_string": 123,
                "empty_string": "",
                "partial_template": "prefix_${state.value}_suffix"
            }
        }
        node = MCPNode(config)
        state = {"value": "middle"}

        # Act
        bound_params = node._bind_parameters(state)

        # Assert
        assert bound_params["empty_template"] == "${state.}"  # Unchanged
        assert bound_params["non_string"] == 123  # Unchanged
        assert bound_params["empty_string"] == ""  # Unchanged
        # Note: Current implementation doesn't handle partial templates
        assert bound_params["partial_template"] == "prefix_${state.value}_suffix"
