# src/elf/core/nodes/mcp_node.py
import logging
from typing import Any

from elf0.core.mcp_client import MCPConnectionError, SimpleMCPClient

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
                    # Extract from JSON in output field or dynamic_state
                    json_key = var_name[5:]  # Remove "json." prefix
                    try:
                        # First try to find JSON in dynamic_state (new system)
                        dynamic_state = state.get("dynamic_state", {})
                        json_found = False
                        
                        if dynamic_state and isinstance(dynamic_state, dict):
                            for dyn_key, dyn_value in dynamic_state.items():
                                if isinstance(dyn_value, str):
                                    try:
                                        # Try to parse as JSON
                                        cleaned_value = dyn_value.strip()
                                        if cleaned_value.startswith('```json'):
                                            cleaned_value = cleaned_value[7:]
                                        if cleaned_value.startswith('```'):
                                            cleaned_value = cleaned_value[3:]
                                        if cleaned_value.endswith('```'):
                                            cleaned_value = cleaned_value[:-3]
                                        cleaned_value = cleaned_value.strip()
                                        
                                        # Handle malformed responses
                                        if cleaned_value.startswith('"') and cleaned_value.endswith('"') and cleaned_value.count('"') == 2:
                                            # Likely malformed: "youtube_url" instead of {"youtube_url": "value"}
                                            continue
                                        
                                        parsed = json.loads(cleaned_value)
                                        if isinstance(parsed, dict) and json_key in parsed:
                                            bound[key] = parsed[json_key]
                                            json_found = True
                                            break
                                    except (json.JSONDecodeError, ValueError):
                                        continue
                        
                        # Fallback to old output-based parsing if not found in dynamic_state
                        if not json_found:
                            output = state.get("output", "{}")
                            if isinstance(output, str):
                                # Try to find JSON in the output
                                start = output.find("{")
                                end = output.rfind("}") + 1
                                if start != -1 and end != 0:
                                    try:
                                        json_str = output[start:end]
                                        parsed = json.loads(json_str)
                                        bound[key] = parsed.get(json_key, value)
                                        json_found = True
                                    except (json.JSONDecodeError, ValueError):
                                        pass
                            
                            # Final fallback - if still no JSON found, use placeholder or skip
                            if not json_found:
                                logger.warning(f"[yellow]⚠ MCP parameter {key}: Could not extract {json_key} from JSON, using placeholder[/yellow]")
                                bound[key] = f"MISSING_{json_key.upper()}"
                                
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.warning(f"[yellow]⚠ MCP parameter {key}: JSON extraction failed ({e}), using placeholder[/yellow]")
                        bound[key] = f"MISSING_{json_key.upper()}"
                else:
                    bound[key] = state.get(var_name, value)
            else:
                bound[key] = value
        return bound
