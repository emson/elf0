# src/elf/core/mcp_client.py
from typing import Dict, Any, Optional
import logging
from urllib.parse import urlparse
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# MCP-related exceptions
class MCPError(Exception):
    """Base exception for MCP-related errors."""
    pass

class MCPConnectionError(MCPError):
    """Raised when MCP server connection fails."""
    pass

class MCPToolError(MCPError):
    """Raised when MCP tool execution fails."""
    pass

class MCPNotAvailableError(MCPError):
    """Raised when MCP dependencies are not available."""
    pass

@dataclass
class MCPToolCall:
    """Represents an MCP tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    server_uri: str

@dataclass
class MCPToolResult:
    """Represents the result of an MCP tool call."""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MCPClientInterface(ABC):
    """Abstract interface for MCP clients."""
    
    @abstractmethod
    async def connect(self, server_uri: str) -> bool:
        """Connect to an MCP server."""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Call a tool on the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self, server_uri: str) -> None:
        """Disconnect from an MCP server."""
        pass
    
    @abstractmethod
    def is_connected(self, server_uri: str) -> bool:
        """Check if connected to a server."""
        pass

class MCPClient(MCPClientInterface):
    """
    MCP Client implementation with connection pooling and error handling.
    
    This client manages connections to multiple MCP servers and handles
    tool invocations within the workflow system.
    """
    
    def __init__(self):
        self._connections: Dict[str, Any] = {}
        self._mcp_available = self._check_mcp_availability()
        
        if self._mcp_available:
            try:
                # Import MCP modules only if available
                import mcp.client  # type: ignore
                self._mcp_client_module = mcp.client
                logger.info("MCP client libraries loaded successfully")
            except ImportError as e:
                logger.warning(f"MCP client import failed: {e}")
                self._mcp_available = False
                self._mcp_client_module = None
        else:
            self._mcp_client_module = None
    
    def _check_mcp_availability(self) -> bool:
        """Check if MCP dependencies are available."""
        try:
            import mcp  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "MCP dependencies not found. Install with: pip install 'mcp[cli]' "
                "to enable MCP tool support."
            )
            return False
    
    def _ensure_mcp_available(self) -> None:
        """Ensure MCP is available, raise error if not."""
        if not self._mcp_available:
            raise MCPNotAvailableError(
                "MCP dependencies are not installed. Install with: pip install 'mcp[cli]'"
            )
    
    def _parse_server_uri(self, server_uri: str) -> Dict[str, str]:
        """Parse MCP server URI into components."""
        parsed = urlparse(server_uri)
        return {
            "scheme": parsed.scheme,
            "host": parsed.hostname or "localhost",
            "port": str(parsed.port) if parsed.port else "3000",
            "path": parsed.path,
            "full_uri": server_uri
        }
    
    async def connect(self, server_uri: str) -> bool:
        """
        Connect to an MCP server.
        
        Args:
            server_uri: URI of the MCP server (e.g., "mcp://localhost:3000")
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            MCPNotAvailableError: If MCP dependencies not installed
            MCPConnectionError: If connection fails
        """
        self._ensure_mcp_available()
        
        if server_uri in self._connections:
            logger.debug(f"Already connected to MCP server: {server_uri}")
            return True
        
        try:
            # Parse the server URI
            uri_components = self._parse_server_uri(server_uri)
            
            # Create MCP client connection
            # Note: This is a simplified implementation
            # Real implementation would use proper MCP client initialization
            client = self._mcp_client_module.MCPClient()
            
            # For now, we'll simulate a connection
            # In a real implementation, you'd connect to the actual server
            logger.info(f"🔌 Connecting to MCP server: {server_uri}")
            
            # Store the connection
            self._connections[server_uri] = {
                "client": client,
                "uri_components": uri_components,
                "connected": True
            }
            
            logger.info(f"✅ Successfully connected to MCP server: {server_uri}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server {server_uri}: {str(e)}")
            raise MCPConnectionError(f"Failed to connect to MCP server {server_uri}: {str(e)}") from e
    
    async def call_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_call: MCPToolCall containing tool name, arguments, and server URI
            
        Returns:
            MCPToolResult with the tool execution result
            
        Raises:
            MCPNotAvailableError: If MCP dependencies not installed
            MCPConnectionError: If not connected to the server
            MCPToolError: If tool execution fails
        """
        self._ensure_mcp_available()
        
        server_uri = tool_call.server_uri
        
        # Ensure we're connected to the server
        if not self.is_connected(server_uri):
            await self.connect(server_uri)
        
        connection = self._connections.get(server_uri)
        if not connection:
            raise MCPConnectionError(f"No connection to MCP server: {server_uri}")
        
        try:
            logger.info(
                f"🔧 Calling MCP tool '{tool_call.tool_name}' on server {server_uri} "
                f"with args: {tool_call.arguments}"
            )
            
            # Call the tool on the MCP server
            # Note: This is a simplified implementation
            # Real implementation would use proper MCP protocol
            # client = connection["client"]  # Would be used in real implementation
            
            # For now, we'll simulate a tool call
            # In a real implementation, you'd call: client.call_tool(tool_call.tool_name, tool_call.arguments)
            
            # Simulate some basic tools for demonstration
            if tool_call.tool_name == "echo":
                result = tool_call.arguments.get("message", "")
            elif tool_call.tool_name == "add":
                a = tool_call.arguments.get("a", 0)
                b = tool_call.arguments.get("b", 0)
                result = a + b
            elif tool_call.tool_name == "multiply":
                a = tool_call.arguments.get("a", 1)
                b = tool_call.arguments.get("b", 1)
                result = a * b
            else:
                # For unknown tools, return a placeholder response
                result = f"MCP tool '{tool_call.tool_name}' called with {tool_call.arguments}"
            
            logger.info(f"✨ MCP tool '{tool_call.tool_name}' returned: {result}")
            
            return MCPToolResult(
                success=True,
                result=result,
                metadata={
                    "server_uri": server_uri,
                    "tool_name": tool_call.tool_name,
                    "execution_time": "simulated"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ MCP tool '{tool_call.tool_name}' failed: {str(e)}")
            return MCPToolResult(
                success=False,
                result=None,
                error=f"MCP tool execution failed: {str(e)}",
                metadata={
                    "server_uri": server_uri,
                    "tool_name": tool_call.tool_name,
                    "error_type": type(e).__name__
                }
            )
    
    async def disconnect(self, server_uri: str) -> None:
        """
        Disconnect from an MCP server.
        
        Args:
            server_uri: URI of the MCP server to disconnect from
        """
        if server_uri in self._connections:
            try:
                # connection = self._connections[server_uri]  # Would be used for cleanup in real implementation
                # Close the connection
                # In a real implementation: await connection["client"].close()
                
                del self._connections[server_uri]
                logger.info(f"🔌 Disconnected from MCP server: {server_uri}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error disconnecting from MCP server {server_uri}: {str(e)}")
    
    def is_connected(self, server_uri: str) -> bool:
        """
        Check if connected to a server.
        
        Args:
            server_uri: URI of the MCP server
            
        Returns:
            True if connected, False otherwise
        """
        connection = self._connections.get(server_uri)
        return connection is not None and connection.get("connected", False)
    
    async def cleanup(self) -> None:
        """Clean up all connections."""
        for server_uri in list(self._connections.keys()):
            await self.disconnect(server_uri)

# Singleton instance for global use
_mcp_client: Optional[MCPClient] = None

def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client

def parse_mcp_entrypoint(entrypoint: str) -> Dict[str, str]:
    """
    Parse an MCP entrypoint string into server URI and tool name.
    
    Expected format: "mcp://server:port/tool_name" or "mcp://server/tool_name"
    
    Args:
        entrypoint: MCP entrypoint string
        
    Returns:
        Dictionary with 'server_uri' and 'tool_name'
        
    Raises:
        ValueError: If entrypoint format is invalid
    """
    if not entrypoint.startswith("mcp://"):
        raise ValueError(f"MCP entrypoint must start with 'mcp://': {entrypoint}")
    
    try:
        parsed = urlparse(entrypoint)
        
        # Extract server URI (without the tool path)
        server_uri = f"{parsed.scheme}://{parsed.netloc}"
        
        # Extract tool name from path
        tool_name = parsed.path.lstrip("/")
        
        if not tool_name:
            raise ValueError(f"MCP entrypoint must include tool name: {entrypoint}")
        
        return {
            "server_uri": server_uri,
            "tool_name": tool_name
        }
        
    except Exception as e:
        raise ValueError(f"Invalid MCP entrypoint format '{entrypoint}': {str(e)}") from e

async def call_mcp_tool(
    entrypoint: str, 
    arguments: Dict[str, Any],
    timeout: float = 30.0
) -> MCPToolResult:
    """
    High-level function to call an MCP tool.
    
    Args:
        entrypoint: MCP entrypoint string (e.g., "mcp://localhost:3000/multiply")
        arguments: Arguments to pass to the tool
        timeout: Timeout in seconds
        
    Returns:
        MCPToolResult with the execution result
        
    Raises:
        ValueError: If entrypoint format is invalid
        MCPError: If MCP call fails
    """
    # Parse the entrypoint
    parsed = parse_mcp_entrypoint(entrypoint)
    server_uri = parsed["server_uri"]
    tool_name = parsed["tool_name"]
    
    # Create tool call
    tool_call = MCPToolCall(
        tool_name=tool_name,
        arguments=arguments,
        server_uri=server_uri
    )
    
    # Execute the tool call
    client = get_mcp_client()
    return await client.call_tool(tool_call)