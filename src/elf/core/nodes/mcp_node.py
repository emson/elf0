# src/elf/core/nodes/mcp_node.py
import logging
from typing import Dict, Any
from ..mcp_client import SimpleMCPClient, MCPConnectionError

logger = logging.getLogger(__name__)

class MCPNode:
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
            raise MCPConnectionError("Failed to connect to MCP server")
        
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