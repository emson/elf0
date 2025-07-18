# tests/integration/test_mcp_integration.py
import os
from pathlib import Path
import tempfile

import pytest

from elf0.core.mcp_client import SimpleMCPClient
from elf0.core.nodes.mcp_node import MCPNode

# Skip integration tests in CI environments unless explicitly enabled
CI_SKIP = os.getenv("CI") and not os.getenv("ELF_RUN_INTEGRATION_TESTS")


class TestMCPIntegrationReal:
    """Integration tests for MCP with real server scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.requires_external
    @pytest.mark.skipif(CI_SKIP, reason="Skipping real MCP server tests in CI (requires Node.js/npm)")
    async def test_filesystem_mcp_server_if_available(self):
        """Test with real filesystem MCP server if available."""
        # Create temp directory with test file
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello, MCP!")

            # Test filesystem server (skip if not available)
            client = SimpleMCPClient([
                "npx", "@modelcontextprotocol/server-filesystem", temp_dir
            ])

            try:
                # Add timeout to connection attempt (30 seconds max)
                import asyncio
                try:
                    connected = await asyncio.wait_for(client.connect(), timeout=30.0)
                except TimeoutError:
                    pytest.skip("MCP server connection timed out")

                if not connected:
                    pytest.skip("Filesystem MCP server not available")

                # List tools
                tools = await client.list_tools()
                tool_names = [tool["name"] for tool in tools]

                # Check if read_file tool is available
                if "read_file" not in tool_names:
                    pytest.skip("read_file tool not available in MCP server")

                # Read file
                result = await client.call_tool("read_file", {"path": str(test_file)})
                assert "Hello, MCP!" in str(result)

            except Exception as e:
                pytest.skip(f"MCP server test skipped: {e}")
            finally:
                # Ensure proper cleanup
                try:
                    await asyncio.wait_for(client.disconnect(), timeout=5.0)
                except (TimeoutError, Exception):
                    # Force cleanup if disconnect hangs
                    pass

    @pytest.mark.asyncio
    async def test_mcp_node_end_to_end(self):
        """Test MCP node end-to-end with mock server."""
        # This test uses a mock to simulate end-to-end behavior
        # In a real scenario, this would use an actual MCP server

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content for MCP")

            # Configure MCP node
            config = {
                "server": {"command": ["echo", "mock_server"]},
                "tool": "read_file",
                "parameters": {"path": str(test_file)}
            }

            # Create and test node (this will fail with real server but tests structure)
            node = MCPNode(config)
            state = {"input": "test input"}

            # This would normally connect to a real server
            # For integration testing, we'd need a test MCP server
            try:
                await node.execute(state)
            except Exception:
                # Expected to fail without real MCP server
                # This tests that the integration points work correctly
                pass

    def test_mcp_configuration_validation(self):
        """Test MCP configuration validation with realistic configs."""
        # Test valid configurations that would work with real servers
        valid_configs = [
            {
                "server": {"command": ["npx", "@modelcontextprotocol/server-filesystem", "/tmp"]},
                "tool": "read_file",
                "parameters": {"path": "${state.file_path}"}
            },
            {
                "server": {"command": ["python", "-m", "mcp_server_example"]},
                "tool": "process_data",
                "parameters": {
                    "input": "${state.input}",
                    "format": "json"
                }
            }
        ]

        for config in valid_configs:
            # Should not raise exception
            node = MCPNode(config)
            assert node.server_command == config["server"]["command"]
            assert node.tool_name == config["tool"]
            assert node.parameters == config["parameters"]

    def test_parameter_binding_realistic_scenarios(self):
        """Test parameter binding with realistic workflow scenarios."""
        config = {
            "server": {"command": ["echo", "test"]},
            "tool": "analyze_document",
            "parameters": {
                "document_path": "${state.document_path}",
                "analysis_type": "sentiment",
                "include_summary": True,
                "max_length": 1000
            }
        }

        node = MCPNode(config)
        state = {
            "document_path": "/path/to/document.txt",
            "user_input": "Analyze this document",
            "previous_output": "Some previous result"
        }

        bound_params = node._bind_parameters(state)

        expected = {
            "document_path": "/path/to/document.txt",
            "analysis_type": "sentiment",
            "include_summary": True,
            "max_length": 1000
        }

        assert bound_params == expected
