# tests/core/test_mcp_integration.py
import pytest

from elf0.core.compiler import make_tool_node
from elf0.core.spec import Function, Spec


class TestMCPFunctionValidation:
    """Test MCP function validation in the spec model."""

    def test_valid_mcp_entrypoint(self):
        """Test that valid MCP entrypoints pass validation."""
        function = Function(
            type="mcp",
            name="test_tool",
            entrypoint="mcp://localhost:3000/multiply"
        )
        assert function.entrypoint == "mcp://localhost:3000/multiply"

    def test_mcp_entrypoint_with_port(self):
        """Test MCP entrypoint with custom port."""
        function = Function(
            type="mcp",
            name="test_tool",
            entrypoint="mcp://server.example.com:8080/calculate"
        )
        assert function.entrypoint == "mcp://server.example.com:8080/calculate"

    def test_invalid_mcp_entrypoint_no_scheme(self):
        """Test that MCP entrypoint without mcp:// scheme fails validation."""
        with pytest.raises(ValueError, match="MCP entrypoint must start with 'mcp://'"):
            Function(
                type="mcp",
                name="test_tool",
                entrypoint="localhost:3000/tool"
            )

    def test_invalid_mcp_entrypoint_no_server(self):
        """Test that MCP entrypoint without server address fails validation."""
        with pytest.raises(ValueError, match="MCP entrypoint must include server address"):
            Function(
                type="mcp",
                name="test_tool",
                entrypoint="mcp:///tool"
            )

    def test_invalid_mcp_entrypoint_no_tool(self):
        """Test that MCP entrypoint without tool name fails validation."""
        with pytest.raises(ValueError, match="MCP entrypoint must include tool name"):
            Function(
                type="mcp",
                name="test_tool",
                entrypoint="mcp://localhost:3000"
            )

    def test_python_entrypoint_still_works(self):
        """Test that Python function validation still works."""
        function = Function(
            type="python",
            name="test_func",
            entrypoint="module.submodule.function"
        )
        assert function.entrypoint == "module.submodule.function"

    def test_invalid_python_entrypoint(self):
        """Test that invalid Python entrypoints still fail validation."""
        with pytest.raises(ValueError, match="Python entrypoint must be in format 'module.function'"):
            Function(
                type="python",
                name="test_func",
                entrypoint="just_function"
            )


class TestMCPArchitectureCompatibility:
    """Test compatibility between old MCP function specs and new MCP node architecture."""

    def test_mcp_functions_still_validate(self):
        """Test that MCP functions still validate in specs for backward compatibility."""
        # Note: MCP functionality is now handled by MCP nodes directly
        # rather than through the Function system. This test verifies
        # that MCP functions are still properly validated in the spec.
        function_spec = Function(
            type="mcp",
            name="test_tool",
            entrypoint="mcp://localhost:3000/echo"
        )

        # Function validation should still work
        assert function_spec.type == "mcp"
        assert function_spec.entrypoint == "mcp://localhost:3000/echo"


class TestMCPToolNodeFactory:
    """Test the make_tool_node function with MCP support."""

    def test_make_tool_node_mcp_function(self):
        """Test make_tool_node with MCP function returns placeholder explaining new architecture."""
        from elf0.core.spec import Workflow, WorkflowNode

        # Create a spec with an MCP function
        spec = Spec(
            llms={},
            functions={
                "mcp_tool": Function(
                    type="mcp",
                    name="test_tool",
                    entrypoint="mcp://localhost:3000/echo"
                )
            },
            workflow=Workflow(
                type="sequential",
                nodes=[
                    WorkflowNode(id="tool_node", kind="tool", ref="mcp_tool")
                ],
                edges=[]
            )
        )

        node = WorkflowNode(id="tool_node", kind="tool", ref="mcp_tool")

        node_fn = make_tool_node(spec, node)
        assert callable(node_fn)

        # Test that it returns the expected placeholder message
        result = node_fn({"input": "test"})
        assert "Use MCP nodes instead" in result["output"]
        assert "MCP functionality is now handled by MCP nodes directly" in result["error_context"]

    def test_make_tool_node_python_function(self):
        """Test make_tool_node with Python function."""
        from elf0.core.spec import Workflow, WorkflowNode

        # Create a spec with a Python function
        spec = Spec(
            llms={},
            functions={
                "python_tool": Function(
                    type="python",
                    name="test_func",
                    entrypoint="module.function"
                )
            },
            workflow=Workflow(
                type="sequential",
                nodes=[
                    WorkflowNode(id="tool_node", kind="tool", ref="python_tool")
                ],
                edges=[]
            )
        )

        node = WorkflowNode(id="tool_node", kind="tool", ref="python_tool")

        node_fn = make_tool_node(spec, node)
        assert callable(node_fn)

    def test_make_tool_node_missing_function(self):
        """Test make_tool_node with missing function reference."""
        from elf0.core.spec import Workflow, WorkflowNode

        # Create a spec with a dummy workflow that passes validation
        spec = Spec(
            llms={"dummy_llm": {
                "type": "openai",
                "model_name": "gpt-4o-mini"
            }},
            functions={},
            workflow=Workflow(
                type="sequential",
                nodes=[
                    WorkflowNode(id="dummy_node", kind="agent", ref="dummy_llm")
                ],
                edges=[]
            )
        )

        # Now try to call make_tool_node with a missing function reference
        node = WorkflowNode(id="tool_node", kind="tool", ref="missing_tool")

        with pytest.raises(ValueError, match="Function reference 'missing_tool' not found"):
            make_tool_node(spec, node)

    def test_make_tool_node_unsupported_type(self):
        """Test make_tool_node with unsupported function type."""
        from elf0.core.spec import Workflow, WorkflowNode

        # Create a valid spec first
        spec = Spec(
            llms={"dummy_llm": {
                "type": "openai",
                "model_name": "gpt-4o-mini"
            }},
            functions={"valid_tool": Function(
                type="mcp",
                name="test_tool",
                entrypoint="mcp://localhost:3000/echo"
            )},
            workflow=Workflow(
                type="sequential",
                nodes=[
                    WorkflowNode(id="dummy_node", kind="agent", ref="dummy_llm")
                ],
                edges=[]
            )
        )

        # Now modify the function's type directly to simulate an unsupported type
        spec.functions["valid_tool"].type = "unsupported_type"

        node = WorkflowNode(id="tool_node", kind="tool", ref="valid_tool")

        with pytest.raises(ValueError, match="Unsupported function type 'unsupported_type'"):
            make_tool_node(spec, node)
