# src/elf/core/mcp_client.py
from typing import Dict, Any, Optional, List
import logging
import asyncio
from urllib.parse import urlparse
from dataclasses import dataclass
import json

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

class MCPClient:
    """
    Modern MCP Client implementation using the latest MCP Python SDK.
    
    This client manages connections to MCP servers and handles tool invocations
    within the workflow system using the proper MCP protocol.
    """
    
    def __init__(self):
        self._sessions: Dict[str, Any] = {}
        self._mcp_available = self._check_mcp_availability()
        self._client_session = None
        self._stdio_client = None
        
        if self._mcp_available:
            try:
                # Import the correct MCP modules
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client
                self._ClientSession = ClientSession
                self._StdioServerParameters = StdioServerParameters
                self._stdio_client = stdio_client
                logger.info("✅ MCP client libraries loaded successfully")
            except ImportError as e:
                logger.warning(f"❌ MCP client import failed: {e}")
                self._mcp_available = False
        else:
            self._ClientSession = None
            self._StdioServerParameters = None
    
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
    
    async def connect(self, server_uri: str) -> bool:
        """
        Connect to an MCP server using the proper MCP protocol.
        
        Args:
            server_uri: URI of the MCP server (e.g., "mcp://localhost:3000")
            
        Returns:
            True if connection successful, False otherwise
        """
        self._ensure_mcp_available()
        
        if server_uri in self._sessions:
            logger.debug(f"Already connected to MCP server: {server_uri}")
            return True
        
        # For development/testing, we immediately fall back to mock implementation
        # In production, you would check for actual MCP server configurations here
        
        # Check if there's a real MCP server configuration for this URI
        real_server_config = self._get_server_config(server_uri)
        
        if real_server_config:
            try:
                # Parse server URI 
                parsed = urlparse(server_uri)
                host = parsed.hostname or "localhost"
                port = parsed.port or 3000
                
                logger.info(f"🔌 Connecting to real MCP server: {host}:{port}")
                
                # Create server parameters for stdio connection
                server_params = self._StdioServerParameters(
                    command=real_server_config["command"],
                    args=real_server_config["args"],
                    env=real_server_config.get("env")
                )
                
                # Create client session with timeout
                async def _connect_with_timeout():
                    async with self._stdio_client(server_params) as (read, write):
                        session = self._ClientSession(read, write)
                        
                        # Initialize the session
                        await session.initialize()
                        
                        # Store session
                        self._sessions[server_uri] = {
                            "session": session,
                            "read": read,
                            "write": write,
                            "connected": True
                        }
                        
                        logger.info(f"✅ Successfully connected to MCP server: {server_uri}")
                        return True
                
                # Apply timeout to connection attempt
                await asyncio.wait_for(_connect_with_timeout(), timeout=5.0)
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to real MCP server {server_uri}: {str(e)}")
                # Fall through to mock implementation
        
        # Use mock implementation for development/testing
        logger.info(f"🔄 Using mock MCP implementation for: {server_uri}")
        self._sessions[server_uri] = {
            "session": None,  # Mock session
            "connected": True,
            "mock": True
        }
        logger.info(f"✅ Mock MCP connection established: {server_uri}")
        return True
    
    def _get_server_config(self, server_uri: str) -> Optional[Dict[str, Any]]:
        """
        Get real MCP server configuration for a given URI.
        
        In production, this would look up actual MCP server configurations
        from environment variables, config files, or a service registry.
        
        Returns None for development/testing (uses mock implementation).
        """
        # Example of what real server configs might look like:
        # 
        # real_configs = {
        #     "mcp://localhost:8000": {
        #         "command": "node",
        #         "args": ["/opt/mcp-servers/calculator/server.js"],
        #         "env": {"PORT": "8000"}
        #     },
        #     "mcp://math-server:3000": {
        #         "command": "python",
        #         "args": ["/opt/mcp-servers/math/server.py"],
        #         "env": {"MCP_PORT": "3000"}
        #     }
        # }
        # return real_configs.get(server_uri)
        
        # For now, return None to always use mock implementation
        return None
    
    async def call_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """
        Call a tool on the MCP server using proper MCP protocol.
        
        Args:
            tool_call: MCPToolCall containing tool name, arguments, and server URI
            
        Returns:
            MCPToolResult with the tool execution result
        """
        self._ensure_mcp_available()
        
        server_uri = tool_call.server_uri
        
        # Ensure we're connected
        if server_uri not in self._sessions:
            await self.connect(server_uri)
        
        session_info = self._sessions.get(server_uri)
        if not session_info:
            raise MCPConnectionError(f"No connection to MCP server: {server_uri}")
        
        try:
            logger.info(
                f"🔧 Calling MCP tool '{tool_call.tool_name}' on server {server_uri} "
                f"with args: {tool_call.arguments}"
            )
            
            # Check if this is a mock session (for development)
            if session_info.get("mock"):
                return await self._mock_tool_call(tool_call)
            
            # Use real MCP session to call tool
            session = session_info["session"]
            
            if session:
                # Call the tool using proper MCP protocol
                from mcp.types import CallToolRequest
                
                request = CallToolRequest(
                    method="tools/call",
                    params={
                        "name": tool_call.tool_name,
                        "arguments": tool_call.arguments
                    }
                )
                
                response = await session.call_tool(request)
                
                if response.isError:
                    return MCPToolResult(
                        success=False,
                        result=None,
                        error=f"MCP tool error: {response.error}",
                        metadata={"server_uri": server_uri, "tool_name": tool_call.tool_name}
                    )
                
                return MCPToolResult(
                    success=True,
                    result=response.result,
                    metadata={
                        "server_uri": server_uri,
                        "tool_name": tool_call.tool_name,
                        "response_id": getattr(response, 'id', None)
                    }
                )
            else:
                return await self._mock_tool_call(tool_call)
                
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
    
    async def _mock_tool_call(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Mock tool call for development/testing."""
        # Extract input from arguments
        user_input = tool_call.arguments.get("input", "")
        context = tool_call.arguments.get("context", {})
        
        # Simulate different tools based on name
        if tool_call.tool_name == "calculate":
            # Try to evaluate simple math expressions
            try:
                import re
                
                # Extract numbers and operators from natural language
                # Look for patterns like "15 + 27", "calculate 2*3", "what is 10-5"
                math_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
                matches = re.findall(math_pattern, user_input)
                
                if matches:
                    # Use the first mathematical expression found
                    num1, op, num2 = matches[0]
                    expr = f"{num1} {op} {num2}"
                    
                    # Safe evaluation
                    try:
                        result = eval(expr)
                        return MCPToolResult(
                            success=True,
                            result=f"The result of {expr} is {result}",
                            metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
                        )
                    except Exception as eval_error:
                        return MCPToolResult(
                            success=False,
                            result=None,
                            error=f"Calculation error: {str(eval_error)}",
                            metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
                        )
                else:
                    # Try to find any sequence of numbers and operators
                    simple_expr_pattern = r'[\d+\-*/().\s]+'
                    if re.search(r'\d', user_input):  # Contains at least one number
                        # Extract just the mathematical part
                        cleaned = re.sub(r'[^\d+\-*/().\s]', '', user_input)
                        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                        
                        if cleaned and any(op in cleaned for op in ['+', '-', '*', '/']):
                            try:
                                result = eval(cleaned)
                                return MCPToolResult(
                                    success=True,
                                    result=f"The result of {cleaned} is {result}",
                                    metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
                                )
                            except:
                                pass
                    
                    return MCPToolResult(
                        success=True,
                        result=f"Calculator received: '{user_input}' but could not find a mathematical expression to evaluate. Please provide an expression like '15 + 27'.",
                        metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
                    )
                    
            except Exception as e:
                return MCPToolResult(
                    success=False,
                    result=None,
                    error=f"Calculation error: {str(e)}",
                    metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
                )
        
        elif tool_call.tool_name == "process_data":
            # Mock data processing
            data_summary = f"Processed data: {user_input[:100]}..." if len(user_input) > 100 else f"Processed data: {user_input}"
            return MCPToolResult(
                success=True,
                result=data_summary,
                metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
            )
        
        elif tool_call.tool_name == "analyze_text":
            # Mock text analysis
            word_count = len(user_input.split())
            char_count = len(user_input)
            analysis = f"Text analysis: {word_count} words, {char_count} characters. Content appears to be about general text processing."
            return MCPToolResult(
                success=True,
                result=analysis,
                metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
            )
        
        else:
            # Generic mock response for unknown tools
            return MCPToolResult(
                success=True,
                result=f"Mock MCP tool '{tool_call.tool_name}' processed: {user_input}",
                metadata={"server_uri": tool_call.server_uri, "tool_name": tool_call.tool_name, "mock": True}
            )
    
    async def disconnect(self, server_uri: str) -> None:
        """Disconnect from an MCP server."""
        if server_uri in self._sessions:
            try:
                session_info = self._sessions[server_uri]
                if not session_info.get("mock") and session_info.get("session"):
                    # Close real MCP session
                    await session_info["session"].close()
                
                del self._sessions[server_uri]
                logger.info(f"🔌 Disconnected from MCP server: {server_uri}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error disconnecting from MCP server {server_uri}: {str(e)}")
    
    def is_connected(self, server_uri: str) -> bool:
        """Check if connected to a server."""
        session_info = self._sessions.get(server_uri)
        return session_info is not None and session_info.get("connected", False)
    
    async def cleanup(self) -> None:
        """Clean up all connections."""
        for server_uri in list(self._sessions.keys()):
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