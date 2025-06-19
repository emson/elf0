# src/elf/core/function_loader.py
from collections.abc import Callable
import importlib
import inspect
import logging
from typing import Any

logger = logging.getLogger(__name__)

class SimpleFunctionLoader:
    """MVP function loader with basic import capabilities."""

    def __init__(self):
        self._function_cache: dict[str, Callable] = {}

    def load_function(self, entrypoint: str) -> Callable:
        """Load function from dotted path like 'mymodule.submodule.function_name'.

        Args:
            entrypoint: Dotted path to function (e.g., "tools.pdf.extract_text")

        Returns:
            Callable function

        Raises:
            ImportError: If module or function cannot be imported
            AttributeError: If function doesn't exist in module
        """
        if entrypoint in self._function_cache:
            return self._function_cache[entrypoint]

        try:
            # Split module path and function name
            if "." not in entrypoint:
                msg = f"Invalid entrypoint format: {entrypoint}. Expected 'module.function'"
                raise ValueError(msg)

            module_path, function_name = entrypoint.rsplit(".", 1)

            # Import the module
            logger.info(f"[blue]Importing {module_path}[/blue]")
            module = importlib.import_module(module_path)

            # Get the function
            if not hasattr(module, function_name):
                msg = f"Function '{function_name}' not found in module '{module_path}'"
                raise AttributeError(msg)

            func = getattr(module, function_name)

            if not callable(func):
                msg = f"'{entrypoint}' is not callable"
                raise TypeError(msg)

            # Validate function signature
            self._validate_function_signature(func, entrypoint)

            # Cache and return
            self._function_cache[entrypoint] = func
            logger.info(f"[green]✓ Loaded function: {entrypoint}[/green]")
            return func

        except Exception as e:
            logger.exception(f"[red]✗ Failed to load function {entrypoint}: {e!s}[/red]")
            msg = f"Could not load function '{entrypoint}': {e!s}"
            raise ImportError(msg) from e

    def _validate_function_signature(self, func: Callable, entrypoint: str) -> None:
        """Validate that function has compatible signature."""
        sig = inspect.signature(func)

        # Check if function accepts state parameter
        if "state" not in sig.parameters:
            logger.warning(f"[yellow]⚠ Function {entrypoint} missing 'state' parameter[/yellow]")

    def bind_parameters(self, func: Callable, state: dict[str, Any], parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Bind workflow state and config parameters to function signature.

        Args:
            func: The function to call
            state: Current workflow state
            parameters: Parameter configuration from YAML

        Returns:
            Dictionary of bound parameters ready for function call
        """
        if parameters is None:
            parameters = {}

        sig = inspect.signature(func)
        bound_params = {}

        # Always pass state if function accepts it
        if "state" in sig.parameters:
            bound_params["state"] = state

        # Process parameter bindings
        for param_name, param_value in parameters.items():
            if param_name in sig.parameters:
                # Handle ${state.field} substitution
                if isinstance(param_value, str) and param_value.startswith("${state."):
                    field_name = param_value[8:-1]  # Remove ${state. and }
                    bound_params[param_name] = state.get(field_name)
                else:
                    # Static value
                    bound_params[param_name] = param_value
            else:
                logger.warning(f"[yellow]⚠ Parameter {param_name} not found in function signature[/yellow]")

        return bound_params

# Global instance
function_loader = SimpleFunctionLoader()
