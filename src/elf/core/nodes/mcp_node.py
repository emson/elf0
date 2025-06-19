# src/elf/core/nodes/mcp_node.py
import logging
from typing import Any

from elf.core.mcp_client import MCPConnectionError, SimpleMCPClient

logger = logging.getLogger(__name__)

class MCPNode:
    """MVP MCP node - basic tool execution."""

    def __init__(self, config: dict[str, Any]):
        self.server_command = config["server"]["command"]
        self.server_cwd = config["server"].get("cwd")
        self.tool_name = config["tool"]
        self.parameters = config.get("parameters", {})
        self.client = None

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute MCP tool and update state."""
        # Connect to server
        self.client = SimpleMCPClient(self.server_command, cwd=self.server_cwd)
        connected = await self.client.connect()

        if not connected:
            msg = "Failed to connect to MCP server"
            raise MCPConnectionError(msg)

        try:
            # Bind parameters from state
            bound_params = self._bind_parameters(state)

            # Execute tool
            result = await self.client.call_tool(self.tool_name, bound_params)

            # Extract text content from MCP result format
            if "content" in result and isinstance(result["content"], list):
                # Find first text content
                for content_item in result["content"]:
                    if content_item.get("type") == "text":
                        state["output"] = content_item["text"]
                        break
                else:
                    state["output"] = str(result)
            else:
                state["output"] = str(result)

            # Also store raw MCP result
            state["mcp_result"] = result
            return state

        finally:
            await self.client.disconnect()

    def _bind_parameters(self, state: dict[str, Any]) -> dict[str, Any]:
        """Enhanced parameter binding from state with JSON parsing support."""
        import json
        bound = {}
        for key, value in self.parameters.items():
            if isinstance(value, str) and value.startswith("${"):
                # Template substitution
                var_name = value[2:-1].replace("state.", "")

                # Special handling for JSON extraction from previous output
                if var_name.startswith("json."):
                    # Extract from JSON in output field
                    json_key = var_name[5:]  # Remove "json." prefix
                    try:
                        output = state.get("output", "{}")
                        # Clean the output to extract just JSON
                        if isinstance(output, str):
                            # Try to find JSON in the output
                            start = output.find("{")
                            end = output.rfind("}") + 1
                            if start != -1 and end != 0:
                                json_str = output[start:end]
                                parsed = json.loads(json_str)
                                bound[key] = parsed.get(json_key, value)
                            else:
                                bound[key] = value
                        else:
                            bound[key] = value
                    except (json.JSONDecodeError, AttributeError):
                        bound[key] = value
                else:
                    bound[key] = state.get(var_name, value)
            else:
                bound[key] = value
        return bound
