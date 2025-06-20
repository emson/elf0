# src/elf/core/mcp_client.py
import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class MCPError(Exception):
    """Base MCP error class."""

class MCPConnectionError(MCPError):
    """MCP server connection errors."""

class MCPToolError(MCPError):
    """MCP tool execution errors."""

class SimpleMCPClient:
    """MVP MCP client - stdio transport only."""

    def __init__(self, command: list[str], cwd: str | None = None):
        self.command = command
        self.cwd = cwd
        self.process = None
        self.tools = {}
        self.request_id = 0

    async def connect(self) -> bool:
        """Start MCP server process and initialize."""
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

            logger.info(f"Connected to MCP server with {len(self.tools)} tools")
            return True
        except Exception as e:
            logger.exception(f"Failed to connect to MCP server: {e}")
            return False

    async def disconnect(self) -> None:
        """Close MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None

    async def call_tool(self, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Execute tool with parameters."""
        return await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": parameters
        })

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools."""
        return list(self.tools.values())

    async def _send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send JSON-RPC request and get response."""
        if not self.process:
            msg = "Not connected to MCP server"
            raise MCPConnectionError(msg)

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
        if not response_line:
            msg = "No response from MCP server"
            raise MCPConnectionError(msg)

        response = json.loads(response_line.decode().strip())

        if "error" in response:
            msg = f"MCP Error: {response['error']}"
            raise MCPToolError(msg)

        return response.get("result", {})
