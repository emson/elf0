# tests/core/test_mcp_client.py
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from elf.core.mcp_client import SimpleMCPClient, MCPConnectionError, MCPToolError


class TestSimpleMCPClient:
    """Test suite for SimpleMCPClient MVP implementation"""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful MCP server connection"""
        # Arrange
        mock_process = AsyncMock()
        mock_process.stdin.write = MagicMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock()
        
        # Mock successful initialization and tools list responses
        mock_responses = [
            json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}).encode() + b"\n",
            json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "test_tool"}]}}).encode() + b"\n"
        ]
        mock_process.stdout.readline.side_effect = mock_responses
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            client = SimpleMCPClient(["echo", "test"])
            
            # Act
            result = await client.connect()
            
            # Assert
            assert result is True
            assert client.process is not None
            assert "test_tool" in client.tools
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test MCP server connection failure"""
        # Arrange
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Connection failed")):
            client = SimpleMCPClient(["echo", "test"])
            
            # Act
            result = await client.connect()
            
            # Assert
            assert result is False
            assert client.process is None
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool execution"""
        # Arrange
        client = SimpleMCPClient(["echo", "test"])
        mock_process = AsyncMock()
        mock_process.stdin.write = MagicMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock()
        
        # Mock tool call response
        tool_response = {"jsonrpc": "2.0", "id": 1, "result": {"output": "success"}}
        mock_process.stdout.readline.return_value = json.dumps(tool_response).encode() + b"\n"
        
        client.process = mock_process
        
        # Act
        result = await client.call_tool("test_tool", {"input": "test"})
        
        # Assert
        assert result == {"output": "success"}
    
    @pytest.mark.asyncio
    async def test_call_tool_error_response(self):
        """Test tool execution with error response from server"""
        # Arrange
        client = SimpleMCPClient(["echo", "test"])
        mock_process = AsyncMock()
        mock_process.stdin.write = MagicMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock()
        
        # Mock error response
        error_response = {"jsonrpc": "2.0", "id": 1, "error": {"code": -1, "message": "Tool failed"}}
        mock_process.stdout.readline.return_value = json.dumps(error_response).encode() + b"\n"
        
        client.process = mock_process
        
        # Act & Assert
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("test_tool", {"input": "test"})
        
        assert "Tool failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        """Test tool execution when not connected"""
        # Arrange
        client = SimpleMCPClient(["echo", "test"])
        # client.process is None (not connected)
        
        # Act & Assert
        with pytest.raises(MCPConnectionError) as exc_info:
            await client.call_tool("test_tool", {"input": "test"})
        
        assert "Not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self):
        """Test proper cleanup on disconnect"""
        # Arrange
        client = SimpleMCPClient(["echo", "test"])
        mock_process = AsyncMock()
        client.process = mock_process
        
        # Act
        await client.disconnect()
        
        # Assert
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_awaited_once()
        assert client.process is None
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools"""
        # Arrange
        client = SimpleMCPClient(["echo", "test"])
        client.tools = {
            "tool1": {"name": "tool1", "description": "Test tool 1"},
            "tool2": {"name": "tool2", "description": "Test tool 2"}
        }
        
        # Act
        tools = await client.list_tools()
        
        # Assert
        assert len(tools) == 2
        assert any(tool["name"] == "tool1" for tool in tools)
        assert any(tool["name"] == "tool2" for tool in tools)
    
    @pytest.mark.asyncio
    async def test_send_request_no_response(self):
        """Test handling of no response from server"""
        # Arrange
        client = SimpleMCPClient(["echo", "test"])
        mock_process = AsyncMock()
        mock_process.stdin.write = MagicMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")  # Empty response
        
        client.process = mock_process
        
        # Act & Assert
        with pytest.raises(MCPConnectionError) as exc_info:
            await client._send_request("test", {})
        
        assert "No response" in str(exc_info.value)
    
    def test_client_initialization(self):
        """Test client initialization with parameters"""
        # Arrange & Act
        client = SimpleMCPClient(["node", "server.js"], cwd="/test/path")
        
        # Assert
        assert client.command == ["node", "server.js"]
        assert client.cwd == "/test/path"
        assert client.process is None
        assert client.tools == {}
        assert client.request_id == 0