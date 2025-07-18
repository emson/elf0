# tests/core/test_python_functions_new.py
"""High-level tests for Python function calling functionality."""

from unittest.mock import patch

import pytest

from elf0.core.compiler import WorkflowState, compile_to_langgraph
from elf0.core.function_loader import function_loader
from elf0.core.spec import Spec


class TestPythonFunctionLoading:
    """Test high-level function loading behavior."""

    def test_loads_valid_function(self):
        """Test that valid functions can be loaded successfully."""
        # Arrange: Use a standard library function that should always exist
        entrypoint = "json.dumps"

        # Act: Load the function
        func = function_loader.load_function(entrypoint)

        # Assert: Function is callable
        assert callable(func)

    def test_caches_loaded_functions(self):
        """Test that functions are cached for performance."""
        # Arrange
        entrypoint = "json.loads"

        # Act: Load same function twice
        func1 = function_loader.load_function(entrypoint)
        func2 = function_loader.load_function(entrypoint)

        # Assert: Same instance returned (cached)
        assert func1 is func2

    def test_handles_invalid_entrypoint(self):
        """Test that invalid entrypoints raise appropriate errors."""
        # Arrange
        invalid_entrypoint = "nonexistent.module.function"

        # Act & Assert: Should raise ImportError
        with pytest.raises(ImportError):
            function_loader.load_function(invalid_entrypoint)


class TestParameterBinding:
    """Test parameter binding from workflow state."""

    def test_binds_static_parameters(self):
        """Test binding of static parameter values."""
        # Arrange
        def dummy_func(state, name, value=42) -> None:
            pass

        state = WorkflowState(input="test", output=None)
        parameters = {"name": "test_name", "value": 100}

        # Act
        bound = function_loader.bind_parameters(dummy_func, state, parameters)

        # Assert
        assert bound["state"] == state
        assert bound["name"] == "test_name"
        assert bound["value"] == 100

    def test_binds_state_substitution(self):
        """Test ${state.field} parameter substitution."""
        # Arrange
        def dummy_func(state, file_path) -> None:
            pass

        state = WorkflowState(input="test.pdf", output=None)
        parameters = {"file_path": "${state.input}"}

        # Act
        bound = function_loader.bind_parameters(dummy_func, state, parameters)

        # Assert
        assert bound["file_path"] == "test.pdf"


class TestUtilityFunctions:
    """Test utility functions behavior."""

    @patch("elf0.core.input_collector.collect_terminal_input")
    def test_user_input_function(self, mock_collect_terminal_input):
        """Test user input function interface."""
        # Arrange
        from elf0.functions.utils import get_user_input
        state = WorkflowState(input="test", output=None)
        mock_collect_terminal_input.return_value = "test response"

        # Act
        result = get_user_input(state, prompt="Test prompt")

        # Assert
        assert result["output"] == "User provided: test response"
        mock_collect_terminal_input.assert_called_once_with("Test prompt", multiline=True)

    def test_text_processor_word_count(self):
        """Test text processor word counting."""
        # Arrange
        from elf0.functions.utils import text_processor
        state = WorkflowState(input="", output="hello world test")

        # Act
        result = text_processor(state, operation="count_words")

        # Assert
        assert result["word_count"] == 3
        assert result["output"] == "Word count: 3"

    def test_text_processor_uppercase(self):
        """Test text processor uppercase transformation."""
        # Arrange
        from elf0.functions.utils import text_processor
        state = WorkflowState(input="", output="hello world")

        # Act
        result = text_processor(state, operation="uppercase")

        # Assert
        assert result["output"] == "HELLO WORLD"
        assert result["transformation"] == "uppercase"


class TestWorkflowIntegration:
    """Test Python functions in complete workflows."""

    def test_workflow_compilation_with_python_functions(self):
        """Test that workflows with Python functions compile successfully."""
        # Arrange: Create a minimal spec with Python function
        spec_data = {
            "version": "0.1",
            "description": "Test workflow",
            "runtime": "langgraph",
            "llms": {
                "test_llm": {
                    "type": "openai",
                    "model_name": "gpt-4o-mini",
                    "temperature": 0.0
                }
            },
            "functions": {
                "test_func": {
                    "type": "python",
                    "name": "Text Processor",
                    "entrypoint": "elf0.functions.utils.text_processor"
                }
            },
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_node",
                        "kind": "tool",
                        "ref": "test_func",
                        "config": {
                            "parameters": {
                                "operation": "count_words"
                            }
                        },
                        "stop": True
                    }
                ],
                "edges": []
            }
        }

        # Act: Compile the workflow
        spec = Spec(**spec_data)
        graph = compile_to_langgraph(spec)

        # Assert: Graph compiles successfully
        assert graph is not None
        # StateGraph compiles but needs to be compiled to be runnable
        compiled_graph = graph.compile()
        assert hasattr(compiled_graph, "invoke")  # Should be a runnable graph


class TestErrorHandling:
    """Test error handling in Python function execution."""

    def test_handles_missing_function_gracefully(self):
        """Test workflow handles missing functions without crashing."""
        # Arrange: Create spec with non-existent function
        spec_data = {
            "version": "0.1",
            "description": "Test error handling",
            "runtime": "langgraph",
            "llms": {
                "test_llm": {
                    "type": "openai",
                    "model_name": "gpt-4o-mini",
                    "temperature": 0.0
                }
            },
            "functions": {
                "missing_func": {
                    "type": "python",
                    "name": "Missing Function",
                    "entrypoint": "nonexistent.module.missing_function"
                }
            },
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_node",
                        "kind": "tool",
                        "ref": "missing_func",
                        "stop": True
                    }
                ],
                "edges": []
            }
        }

        # Act: Compile workflow - should not raise exception
        spec = Spec(**spec_data)
        graph = compile_to_langgraph(spec)

        # Assert: Graph compiles even with missing function
        # (Error handling happens at runtime, not compile time)
        assert graph is not None

    def test_invalid_entrypoint_format(self):
        """Test that invalid entrypoint formats are handled."""
        # Arrange
        invalid_entrypoint = "invalid_format"

        # Act & Assert
        with pytest.raises(ImportError):
            function_loader.load_function(invalid_entrypoint)
