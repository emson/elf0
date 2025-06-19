# docs_ai/features/feature_functions-01.md

# Python Function Calling - MVP Implementation Guide

## Feature Overview

**Objective**: Implement minimum viable Python function calling in Elf workflows to enable user interaction and file processing capabilities.

**Target Use Cases**:
- Functions that pause workflow and get user input
- PDF and Excel file processing
- Simple data transformation functions

**Implementation Strategy**: Replace the placeholder in `compiler.py:551-558` with a simple but extensible function loading system that can grow into the full security model later.

## Current State & Context

### Existing Infrastructure ✅
- **Schema Support**: `functions` section with `type: python` and `entrypoint: "module.function"`
- **Node Integration**: `tool` nodes reference functions via `ref` field
- **Execution Wrapper**: `load_tool()` function provides state management interface
- **Routing Logic**: `make_tool_node()` routes Python vs MCP functions

### Target Location 📍
**File**: `src/elf/core/compiler.py:551-558`

**Current Placeholder**:
```python
def python_tool_placeholder(state: WorkflowState) -> WorkflowState:
    return {
        **state,
        "output": f"Python tool '{function_spec.name}' (entrypoint: {function_spec.entrypoint}) - Implementation needed",
        "error_context": "Python tool loading not fully implemented"
    }
```

### WorkflowState Structure 📋
From `compiler.py:19-37`:
```python
class WorkflowState(TypedDict):
    input: str
    output: str | None
    iteration_count: Optional[int]
    evaluation_score: Optional[float]
    workflow_id: Optional[str]
    current_node: Optional[str]
    error_context: Optional[str]
    structured_output: Optional[Dict[str, Any]]
    # ... additional fields for validation, formatting
```

## MVP Architecture Design

### 1. Simple Function Loader
**Location**: `src/elf/core/function_loader.py` (new file)

```python
# src/elf/core/function_loader.py
import importlib
import inspect
from typing import Dict, Any, Callable
from .compiler import WorkflowState

class SimpleFunctionLoader:
    """MVP function loader with basic import capabilities."""
    
    def __init__(self):
        self._function_cache: Dict[str, Callable] = {}
    
    def load_function(self, entrypoint: str) -> Callable:
        """Load function from dotted path like 'mymodule.submodule.function_name'"""
        # Implementation details in steps below
    
    def bind_parameters(self, func: Callable, state: WorkflowState, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Bind workflow state and config parameters to function signature"""
        # Implementation details in steps below
```

### 2. Parameter Binding System
Support `${state.field}` syntax for accessing workflow state:

```yaml
# Example workflow node
- id: process_file
  kind: tool
  ref: pdf_extractor
  config:
    parameters:
      file_path: "${state.input_file}"
      extract_images: true
      page_numbers: "${state.page_range}"
```

### 3. User Interaction Pattern
Special function signature for user input:

```python
def get_user_input(state: WorkflowState) -> WorkflowState:
    """Function that requests user input via CLI."""
    message = state.get('prompt', 'Please provide input:')
    
    # Simple CLI input for MVP
    user_response = input(f"\n{message}\n> ")
    
    return {
        **state,
        'user_input': user_response,
        'output': f"User provided: {user_response}"
    }
```

## Implementation Steps

### Step 1: Create Function Loader Module
**File**: `src/elf/core/function_loader.py`

**Implementation**:
```python
# src/elf/core/function_loader.py
import importlib
import inspect
import logging
import re
from typing import Dict, Any, Callable, Optional
from .compiler import WorkflowState

logger = logging.getLogger(__name__)

class SimpleFunctionLoader:
    """MVP function loader with basic import capabilities."""
    
    def __init__(self):
        self._function_cache: Dict[str, Callable] = {}
    
    def load_function(self, entrypoint: str) -> Callable:
        """
        Load function from dotted path like 'mymodule.submodule.function_name'
        
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
            if '.' not in entrypoint:
                raise ValueError(f"Invalid entrypoint format: {entrypoint}. Expected 'module.function'")
            
            module_path, function_name = entrypoint.rsplit('.', 1)
            
            # Import the module
            logger.info(f"🐍 Importing module: {module_path}")
            module = importlib.import_module(module_path)
            
            # Get the function
            if not hasattr(module, function_name):
                raise AttributeError(f"Function '{function_name}' not found in module '{module_path}'")
            
            func = getattr(module, function_name)
            
            if not callable(func):
                raise TypeError(f"'{entrypoint}' is not callable")
            
            # Validate function signature
            self._validate_function_signature(func, entrypoint)
            
            # Cache and return
            self._function_cache[entrypoint] = func
            logger.info(f"✅ Successfully loaded function: {entrypoint}")
            return func
            
        except Exception as e:
            logger.error(f"❌ Failed to load function '{entrypoint}': {str(e)}")
            raise ImportError(f"Could not load function '{entrypoint}': {str(e)}") from e
    
    def _validate_function_signature(self, func: Callable, entrypoint: str) -> None:
        """Validate that function has compatible signature."""
        sig = inspect.signature(func)
        
        # Check if function accepts state parameter
        if 'state' not in sig.parameters:
            logger.warning(f"⚠️ Function '{entrypoint}' doesn't have 'state' parameter. "
                         f"It may not work correctly with workflow state.")
    
    def bind_parameters(self, func: Callable, state: WorkflowState, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Bind workflow state and config parameters to function signature.
        
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
        if 'state' in sig.parameters:
            bound_params['state'] = state
        
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
                logger.warning(f"⚠️ Parameter '{param_name}' not found in function signature")
        
        return bound_params

# Global instance
function_loader = SimpleFunctionLoader()
```

### Step 2: Update Compiler Integration
**File**: `src/elf/core/compiler.py`

**Changes Required**:

1. **Add import at top of file**:
```python
from .function_loader import function_loader
```

2. **Replace placeholder in `make_tool_node()` function (lines 544-558)**:
```python
if function_spec.type == "python":
    logger.info(f"🐍 Loading Python tool: {function_spec.name}")
    
    try:
        # Load the actual function
        func = function_loader.load_function(function_spec.entrypoint)
        
        # Create wrapper that handles parameter binding
        def python_function_wrapper(state: WorkflowState) -> WorkflowState:
            try:
                # Get parameters from node config
                parameters = node.config.get('parameters', {}) if node.config else {}
                
                # Bind parameters from state and config
                bound_params = function_loader.bind_parameters(func, state, parameters)
                
                # Execute function
                logger.info(f"🔧 Executing Python function: {function_spec.entrypoint}")
                result = func(**bound_params)
                
                # Handle return value
                if isinstance(result, dict):
                    # Function returned state update
                    return {**state, **result}
                elif isinstance(result, str):
                    # Function returned string output
                    return {**state, "output": result}
                else:
                    # Convert other types to string
                    return {**state, "output": str(result)}
                    
            except Exception as e:
                logger.error(f"❌ Python function error: {str(e)}")
                return {
                    **state,
                    "output": f"Function error: {str(e)}",
                    "error_context": f"Python function '{function_spec.entrypoint}' failed: {str(e)}"
                }
        
        return load_tool(python_function_wrapper)
        
    except Exception as e:
        logger.error(f"❌ Failed to load Python function: {str(e)}")
        
        def error_function(state: WorkflowState) -> WorkflowState:
            return {
                **state,
                "output": f"Failed to load function '{function_spec.entrypoint}': {str(e)}",
                "error_context": f"Function loading error: {str(e)}"
            }
        
        return error_function
```

### Step 3: Create Sample Functions for Testing
**File**: `src/elf/examples/sample_functions.py` (new file)

```python
# src/elf/examples/sample_functions.py
"""Sample functions for testing Python function calling."""

from ..core.compiler import WorkflowState
from typing import Dict, Any

def simple_greeting(state: WorkflowState, name: str = "World") -> WorkflowState:
    """Simple function that greets someone."""
    greeting = f"Hello, {name}!"
    return {
        **state,
        "output": greeting,
        "greeting_generated": True
    }

def get_user_input(state: WorkflowState, prompt: str = "Please provide input:") -> WorkflowState:
    """Function that requests user input via CLI."""
    print(f"\n📝 {prompt}")
    user_response = input("> ")
    
    return {
        **state,
        'user_input': user_response,
        'output': f"User provided: {user_response}"
    }

def process_pdf_mock(state: WorkflowState, file_path: str) -> WorkflowState:
    """Mock PDF processing function for testing."""
    # For MVP, just simulate PDF processing
    return {
        **state,
        "output": f"Processed PDF: {file_path}",
        "pdf_text": f"Mock extracted text from {file_path}",
        "page_count": 5
    }

def process_excel_mock(state: WorkflowState, file_path: str, sheet_name: str = "Sheet1") -> WorkflowState:
    """Mock Excel processing function for testing."""
    # For MVP, just simulate Excel processing
    return {
        **state,
        "output": f"Processed Excel: {file_path}, Sheet: {sheet_name}",
        "excel_data": {"rows": 100, "columns": 5},
        "sheet_processed": sheet_name
    }

def calculate_sum(state: WorkflowState, a: float, b: float) -> str:
    """Simple calculation function that returns a string."""
    result = a + b
    return f"The sum of {a} and {b} is {result}"

def transform_text(state: WorkflowState, operation: str = "upper") -> WorkflowState:
    """Transform text from previous output."""
    text = state.get("output", "")
    
    if operation == "upper":
        transformed = text.upper()
    elif operation == "lower":
        transformed = text.lower()
    elif operation == "reverse":
        transformed = text[::-1]
    else:
        transformed = text
    
    return {
        **state,
        "output": transformed,
        "transformation_applied": operation
    }
```

### Step 4: Create Test Workflows
**File**: `specs/examples/python_function_test.yaml` (new file)

```yaml
version: "0.1"
description: "Test Python function calling"
runtime: "langgraph"

llms:
  test_llm:
    type: openai
    model_name: gpt-4o-mini
    temperature: 0.0

functions:
  greet_user:
    type: python
    name: "Greeting Function"
    entrypoint: "elf.examples.sample_functions.simple_greeting"
    
  get_input:
    type: python
    name: "User Input"
    entrypoint: "elf.examples.sample_functions.get_user_input"
    
  process_pdf:
    type: python
    name: "PDF Processor"
    entrypoint: "elf.examples.sample_functions.process_pdf_mock"

workflow:
  type: sequential
  nodes:
    - id: greet
      kind: tool
      ref: greet_user
      config:
        parameters:
          name: "${state.input}"
          
    - id: ask_user
      kind: tool
      ref: get_input
      config:
        parameters:
          prompt: "What file would you like to process?"
          
    - id: process
      kind: tool
      ref: process_pdf
      config:
        parameters:
          file_path: "${state.user_input}"
      stop: true
```

### Step 5: Create Integration Tests
**File**: `tests/core/test_python_functions.py` (new file)

```python
# tests/core/test_python_functions.py
import pytest
from elf.core.function_loader import SimpleFunctionLoader, function_loader
from elf.core.compiler import WorkflowState

class TestSimpleFunctionLoader:
    
    def test_load_valid_function(self):
        """Test loading a valid function."""
        # Test with a built-in function first
        func = function_loader.load_function("json.dumps")
        assert callable(func)
    
    def test_load_invalid_module(self):
        """Test loading from non-existent module."""
        with pytest.raises(ImportError):
            function_loader.load_function("nonexistent.module.function")
    
    def test_load_invalid_function(self):
        """Test loading non-existent function from valid module."""
        with pytest.raises(ImportError):
            function_loader.load_function("json.nonexistent_function")
    
    def test_function_caching(self):
        """Test that functions are cached properly."""
        func1 = function_loader.load_function("json.dumps")
        func2 = function_loader.load_function("json.dumps")
        assert func1 is func2  # Should be same cached instance
    
    def test_parameter_binding_static(self):
        """Test static parameter binding."""
        def dummy_func(state, name, value=42):
            pass
        
        state = WorkflowState(input="test", output=None)
        parameters = {"name": "test_name", "value": 100}
        
        bound = function_loader.bind_parameters(dummy_func, state, parameters)
        
        assert bound["state"] == state
        assert bound["name"] == "test_name"
        assert bound["value"] == 100
    
    def test_parameter_binding_state_substitution(self):
        """Test ${state.field} parameter substitution."""
        def dummy_func(state, file_path):
            pass
        
        state = WorkflowState(input="test.pdf", output=None)
        parameters = {"file_path": "${state.input}"}
        
        bound = function_loader.bind_parameters(dummy_func, state, parameters)
        
        assert bound["file_path"] == "test.pdf"

class TestPythonFunctionIntegration:
    """Integration tests for Python function execution in workflows."""
    
    def test_sample_greeting_function(self):
        """Test the sample greeting function."""
        from elf.examples.sample_functions import simple_greeting
        
        state = WorkflowState(input="Alice", output=None)
        result = simple_greeting(state, name="Alice")
        
        assert result["output"] == "Hello, Alice!"
        assert result["greeting_generated"] is True
    
    def test_calculation_function(self):
        """Test function that returns string directly."""
        from elf.examples.sample_functions import calculate_sum
        
        state = WorkflowState(input="", output=None)
        result = calculate_sum(state, 5.0, 3.0)
        
        assert result == "The sum of 5.0 and 3.0 is 8.0"
```

## Validation & Testing Plan

### Pre-Implementation Checks ✅

Before starting implementation, verify:

1. **Current placeholder location**:
   ```bash
   grep -n "python_tool_placeholder" src/elf/core/compiler.py
   ```

2. **WorkflowState structure**:
   ```bash
   grep -A 20 "class WorkflowState" src/elf/core/compiler.py
   ```

3. **Existing imports and dependencies**:
   ```bash
   grep -n "import" src/elf/core/compiler.py | head -10
   ```

### Implementation Validation Steps ✅

After each step:

1. **Function loader validation**:
   ```bash
   python -c "from elf.core.function_loader import function_loader; print('✅ Loader imported')"
   ```

2. **Sample function loading**:
   ```bash
   python -c "
   from elf.core.function_loader import function_loader
   func = function_loader.load_function('json.dumps')
   print('✅ Function loaded:', func.__name__)
   "
   ```

3. **Integration test**:
   ```bash
   cd /Users/benemson/Dropbox/devel/projects/ai/elf
   python -m pytest tests/core/test_python_functions.py -v
   ```

4. **End-to-end workflow test**:
   ```bash
   uv run elf agent specs/examples/python_function_test.yaml --prompt "TestUser"
   ```

### Success Criteria 🎯

**MVP Complete When**:
- ✅ Function loader can import and cache Python functions
- ✅ Parameter binding works for both static values and `${state.field}` syntax
- ✅ Sample functions execute and return proper WorkflowState
- ✅ User input function pauses and gets CLI input
- ✅ Mock file processing functions work
- ✅ Integration tests pass
- ✅ End-to-end workflow executes successfully

### Error Handling Verification 🛡️

Test error scenarios:
1. **Invalid entrypoint**: Non-existent module/function
2. **Import errors**: Missing dependencies
3. **Runtime errors**: Function execution failures
4. **Parameter mismatches**: Wrong parameter names/types

## Post-MVP Extension Points 🚀

This MVP sets up extension points for future features:

1. **Security Layer**: Add import restrictions and sandboxing
2. **Advanced Parameter Binding**: Support `${state.json.field}` extraction
3. **Async Support**: Enable async/await function patterns
4. **Workflow Interruption**: Replace simple CLI input with LangGraph interrupts
5. **Real File Processing**: Add actual PDF/Excel libraries

## Implementation Notes for LLM 🤖

**File Creation Order**:
1. `src/elf/core/function_loader.py` - Core functionality
2. Update `src/elf/core/compiler.py` - Integration  
3. `src/elf/examples/sample_functions.py` - Test functions
4. `specs/examples/python_function_test.yaml` - Test workflow
5. `tests/core/test_python_functions.py` - Tests

**Key Implementation Points**:
- Maintain existing code style and error handling patterns
- Use existing logger instance and logging format
- Follow the existing `load_tool()` wrapper pattern
- Keep error messages consistent with existing format
- Preserve all existing functionality and backward compatibility

**Testing Strategy**:
- Unit test each component independently
- Integration test with existing workflow system
- Validate error handling and edge cases
- Test with real workflow execution

This MVP provides a solid foundation that can evolve into the full-featured Python function calling system while delivering immediate value for user interaction and file processing use cases.