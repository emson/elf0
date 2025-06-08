# MCP Integration Feature

## Overview

Model Context Protocol (MCP) integration enables ELF workflows to connect to and utilize external MCP servers for accessing tools, resources, and data sources. This transforms ELF from a standalone workflow runner into a connected ecosystem participant.

## Current State

The current MCP implementation in `src/elf/core/mcp_client.py` is a placeholder with mock functionality:
- `MCPClient` class exists but methods are not implemented
- `connect()`, `disconnect()`, `list_tools()`, `call_tool()` methods return empty results
- No real MCP server communication or protocol handling

## MVP Implementation Strategy

### Core MVP Principles

1. **Stdio-only transport** - Skip WebSocket/SSE complexity initially
2. **Single server connection per node** - Avoid multi-server complexity
3. **Tools-only** - Skip resources for now (files, URLs, databases)
4. **Basic error handling** - No retry/circuit breaker patterns
5. **Minimal configuration** - Simple YAML schema without advanced features
6. **Direct process spawning** - No connection pooling or management

### MVP Scope

#### What's Included (MVP)
- ✅ Stdio transport for MCP servers
- ✅ Basic tool discovery and execution  
- ✅ Simple parameter binding from workflow state
- ✅ Basic error handling with exceptions
- ✅ Single server connection per node
- ✅ Minimal YAML configuration schema

#### What's Deferred (Post-MVP)
- ❌ WebSocket/SSE transports
- ❌ Resource access (files, URLs, etc.)
- ❌ Multiple simultaneous server connections
- ❌ Authentication and security
- ❌ Connection pooling and caching
- ❌ Retry logic and circuit breakers
- ❌ Advanced parameter binding and validation
- ❌ Comprehensive error recovery

## MVP Implementation Details

### 1. Simple MCP Client (MVP)

```python
# src/elf/core/mcp_client.py - MVP version
import asyncio
import json
import subprocess
from typing import Dict, Any, List, Optional

class SimpleMCPClient:
    """MVP MCP client - stdio transport only"""
    
    def __init__(self, command: List[str], cwd: Optional[str] = None):
        self.command = command
        self.cwd = cwd
        self.process = None
        self.tools = {}
        self.request_id = 0
    
    async def connect(self) -> bool:
        """Start MCP server process and initialize"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            
            # Send initialize request
            await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                }
            })
            
            # Get tools list
            tools_response = await self._send_request("tools/list", {})
            self.tools = {tool["name"]: tool for tool in tools_response.get("tools", [])}
            
            return True
        except Exception:
            return False
    
    async def disconnect(self) -> None:
        """Close MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with parameters"""
        return await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": parameters
        })
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return list(self.tools.values())
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request and get response"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode().strip())
        
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")
        
        return response.get("result", {})
```

### 2. MCP Node Implementation (MVP)

```python
# src/elf/core/nodes/mcp_node.py - MVP version
from typing import Dict, Any
from elf.core.nodes.base import BaseNode
from elf.core.mcp_client import SimpleMCPClient

class MCPNode(BaseNode):
    """MVP MCP node - basic tool execution"""
    
    def __init__(self, config: Dict[str, Any]):
        self.server_command = config["server"]["command"]
        self.tool_name = config["tool"]
        self.parameters = config.get("parameters", {})
        self.client = None
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool and update state"""
        # Connect to server
        self.client = SimpleMCPClient(self.server_command)
        connected = await self.client.connect()
        
        if not connected:
            raise Exception(f"Failed to connect to MCP server")
        
        try:
            # Bind parameters from state
            bound_params = self._bind_parameters(state)
            
            # Execute tool
            result = await self.client.call_tool(self.tool_name, bound_params)
            
            # Update state with result
            state["mcp_result"] = result
            return state
            
        finally:
            await self.client.disconnect()
    
    def _bind_parameters(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Simple parameter binding from state"""
        bound = {}
        for key, value in self.parameters.items():
            if isinstance(value, str) and value.startswith("${"):
                # Simple template substitution
                var_name = value[2:-1].replace("state.", "")
                bound[key] = state.get(var_name, value)
            else:
                bound[key] = value
        return bound
```

### 3. MVP Configuration Schema

```yaml
# MVP workflow YAML with MCP
nodes:
  - id: "file_reader"
    type: "mcp"
    config:
      server:
        command: ["npx", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
      tool: "read_file"
      parameters:
        path: "${state.file_path}"

  - id: "web_search"
    type: "mcp"
    config:
      server:
        command: ["python", "-m", "mcp_server_web"]
      tool: "search"
      parameters:
        query: "${state.search_query}"
        max_results: 5

edges:
  - from: "start"
    to: "file_reader"
    condition: "always"
  - from: "file_reader"
    to: "web_search"
    condition: "always"
```

### 4. Error Handling (MVP)

```python
# src/elf/core/mcp_errors.py
class MCPError(Exception):
    """Base MCP error class"""
    pass

class MCPConnectionError(MCPError):
    """MCP server connection errors"""
    pass

class MCPToolError(MCPError):
    """MCP tool execution errors"""
    pass
```

## Testing Requirements (MVP)

### Unit Tests

1. **Simple MCP Client Tests** (`tests/core/test_mcp_client.py`)
   - Test connection establishment with mock subprocess
   - Test tool discovery and caching
   - Test tool execution with various parameter types
   - Test error handling for connection failures
   - Mock MCP server responses for reliable testing

```python
# tests/core/test_mcp_client.py
import pytest
from unittest.mock import AsyncMock, patch
from elf.core.mcp_client import SimpleMCPClient

@pytest.mark.asyncio
async def test_mcp_client_connect():
    """Test basic MCP client connection"""
    with patch('asyncio.create_subprocess_exec') as mock_subprocess:
        # Mock successful connection
        mock_process = AsyncMock()
        mock_subprocess.return_value = mock_process
        
        client = SimpleMCPClient(["echo", "test"])
        result = await client.connect()
        
        assert result is True
        assert client.process is not None

@pytest.mark.asyncio
async def test_mcp_tool_execution():
    """Test MCP tool execution"""
    client = SimpleMCPClient(["echo", "test"])
    
    with patch.object(client, '_send_request', return_value={"output": "success"}):
        result = await client.call_tool("test_tool", {"input": "test"})
        assert result["output"] == "success"
```

2. **MCP Node Tests** (`tests/core/test_mcp_node.py`)
   - Test MCP node configuration validation
   - Test node execution with mock MCP client
   - Test state management and result handling
   - Test parameter interpolation from workflow state

```python
# tests/core/test_mcp_node.py
import pytest
from unittest.mock import patch, AsyncMock
from elf.core.nodes.mcp_node import MCPNode

@pytest.mark.asyncio
async def test_mcp_node_execution():
    """Test MCP node execution with mock client"""
    config = {
        "server": {"command": ["echo", "test"]},
        "tool": "test_tool",
        "parameters": {"input": "${state.input}"}
    }
    
    node = MCPNode(config)
    state = {"input": "test_value"}
    
    with patch('elf.core.mcp_client.SimpleMCPClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.connect.return_value = True
        mock_client.call_tool.return_value = {"output": "success"}
        mock_client_class.return_value = mock_client
        
        result_state = await node.execute(state)
        
        assert "mcp_result" in result_state
        assert result_state["mcp_result"]["output"] == "success"
        assert mock_client.call_tool.called
```

### Integration Tests

1. **Real MCP Server Tests** (`tests/integration/test_mcp_integration.py`)
   - Test with actual filesystem MCP server
   - Test end-to-end workflow execution with MCP nodes
   - Test error scenarios with server failures

```python
# tests/integration/test_mcp_integration.py
import pytest
import tempfile
import os
from pathlib import Path
from elf.core.mcp_client import SimpleMCPClient

@pytest.mark.asyncio
async def test_filesystem_mcp_server():
    """Test with real filesystem MCP server"""
    # Create temp directory with test file
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, MCP!")
        
        # Test filesystem server
        client = SimpleMCPClient([
            "npx", "@modelcontextprotocol/server-filesystem", temp_dir
        ])
        
        connected = await client.connect()
        if not connected:
            pytest.skip("Filesystem MCP server not available")
        
        try:
            # List tools
            tools = await client.list_tools()
            assert any(tool["name"] == "read_file" for tool in tools)
            
            # Read file
            result = await client.call_tool("read_file", {"path": str(test_file)})
            assert "Hello, MCP!" in result["content"]
            
        finally:
            await client.disconnect()
```

## Implementation Timeline

### Week 1: Core Client Implementation
1. Replace `src/elf/core/mcp_client.py` with `SimpleMCPClient`
2. Add basic error handling classes
3. Create unit tests for client functionality

### Week 2: Node Implementation and Integration
1. Create `MCPNode` class in `src/elf/core/nodes/mcp_node.py`
2. Update workflow compiler to support MCP node type
3. Add configuration validation for MCP nodes

### Week 3: Testing and Integration
1. Add comprehensive unit tests
2. Create integration tests with filesystem MCP server
3. Test end-to-end workflow execution

### Week 4: Documentation and Examples
1. Update README with MCP examples
2. Create sample workflows using MCP
3. Add troubleshooting documentation

## Success Criteria (MVP)

1. **Functional Requirements**
   - ✅ Connect to real MCP server (filesystem server)
   - ✅ Execute one tool successfully (read_file)
   - ✅ Pass tool result to next workflow node
   - ✅ Handle connection failure gracefully
   - ✅ One working end-to-end example

2. **Non-Functional Requirements**
   - Connection establishment < 5 seconds
   - Tool execution overhead < 1 second
   - Basic error reporting and debugging
   - Test coverage > 80%

3. **Integration Requirements**
   - Works with existing workflow patterns
   - Backward compatibility with current specifications
   - Clear error messages for debugging

## Extension Strategy (Post-MVP)

The MVP design enables easy extension:

### Phase 2: Enhanced Features
- Replace `SimpleMCPClient` with full `MCPClient` supporting WebSocket/SSE
- Add `MCPClientManager` for connection pooling
- Extend configuration schema for authentication
- Add resource access support

### Phase 3: Production Features
- Add retry logic and circuit breakers
- Implement connection caching and performance optimization
- Add monitoring and observability
- Support multiple transport types

### Example Extension Path

```python
# Future full implementation
class MCPClient:
    """Full MCP client with all transports"""
    
    def __init__(self, config: MCPServerConfig):
        self.transport = self._create_transport(config.transport)
        self.auth = self._create_auth(config.auth)
        # ... additional features
    
    def _create_transport(self, transport_config):
        if transport_config.type == "stdio":
            return StdioTransport(transport_config)
        elif transport_config.type == "websocket":
            return WebSocketTransport(transport_config)
        # ... other transports
```

## Dependencies

### MVP Dependencies
- Python asyncio (built-in)
- JSON-RPC protocol handling (manual implementation)
- Subprocess management (built-in)

### Future Dependencies
- WebSocket client library (websockets)
- Authentication libraries (for OAuth, JWT, etc.)
- Connection pooling libraries
- Monitoring and metrics libraries

This MVP approach delivers working MCP integration in 2-3 weeks while maintaining a clear path for future enhancements and production features.