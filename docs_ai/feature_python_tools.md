# Python Tool Loading Feature

## Overview

Python tool loading enables ELF workflows to dynamically load and execute Python functions as tools within workflow nodes. This provides a powerful way to extend workflow capabilities with custom business logic, data processing, and integrations without modifying the core ELF framework.

## Current State

The current Python tool implementation in `src/elf/core/compiler.py` has placeholder functionality:
- `load_python_functions()` method exists but is not implemented
- No mechanism to discover, load, or execute Python functions
- No validation or sandboxing for Python code execution
- No parameter binding or result handling for Python tools

## Feature Requirements

### Core Python Tool Support

1. **Function Discovery and Loading**
   - Dynamically load Python modules and extract callable functions
   - Support both file-based and module-based function imports
   - Automatic function signature introspection and validation
   - Support for both sync and async functions

2. **Function Execution Framework**
   - Safe execution environment with proper error handling
   - Parameter binding from workflow state to function arguments
   - Result capture and transformation back to workflow state
   - Support for complex parameter types (dict, list, custom objects)

3. **Security and Sandboxing**
   - Restricted execution environment to prevent malicious code
   - Import restrictions and module whitelisting
   - Resource limits (CPU, memory, execution time)
   - File system access controls

### Configuration and Management

1. **Function Configuration**
   - YAML-based function definitions in workflow specs
   - Function parameter mapping and validation
   - Return value handling and transformation
   - Error handling and retry configuration

2. **Module Management**
   - Python path management for custom modules
   - Dependency resolution and validation
   - Module reloading for development workflows
   - Version compatibility checking

### Workflow Integration

1. **Python Node Type**
   - New `python` node type for workflow specifications
   - Function selection and parameter binding
   - Result handling and state management
   - Integration with workflow control flow

2. **Type System Integration**
   - Automatic type conversion between workflow state and Python types
   - Pydantic model integration for complex data structures
   - Type validation and error reporting
   - Schema generation from function signatures

## Implementation Details

### 1. Python Function Loader

```python
# src/elf/core/python_loader.py
from typing import Dict, Any, Callable, Optional
import importlib
import inspect
from pathlib import Path

class PythonFunctionLoader:
    """Load and manage Python functions for workflow execution"""
    
    def __init__(self, allowed_modules: Optional[List[str]] = None):
        self.allowed_modules = allowed_modules or []
        self.loaded_functions: Dict[str, Callable] = {}
        self.function_schemas: Dict[str, Dict[str, Any]] = {}
    
    def load_function(self, module_path: str, function_name: str) -> Callable:
        """Load a specific function from a module"""
        # Implementation needed
    
    def load_from_file(self, file_path: Path, function_name: str) -> Callable:
        """Load function from a Python file"""
        # Implementation needed
    
    def get_function_schema(self, function: Callable) -> Dict[str, Any]:
        """Extract function signature and generate schema"""
        # Implementation needed
    
    def validate_function(self, function: Callable) -> bool:
        """Validate function is safe for execution"""
        # Implementation needed
```

### 2. Python Execution Environment

```python
# src/elf/core/python_executor.py
import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
import time

class PythonExecutor:
    """Safe execution environment for Python functions"""
    
    def __init__(self, max_execution_time: int = 30, max_memory_mb: int = 512):
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def execute_function(
        self, 
        function: Callable, 
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute function with resource limits and error handling"""
        # Implementation needed
    
    def _execute_with_timeout(self, function: Callable, parameters: Dict[str, Any]) -> Any:
        """Execute function with timeout protection"""
        # Implementation needed
    
    def _validate_parameters(self, function: Callable, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert parameters to match function signature"""
        # Implementation needed
```

### 3. Function Configuration Schema

```yaml
# Python function configuration in workflow YAML
functions:
  python_functions:
    - name: "data_processor"
      module: "my_tools.data_processing"
      function: "process_data"
      parameters:
        input_data: "${state.raw_data}"
        config: 
          format: "json"
          validate: true
      timeout: 30
      memory_limit_mb: 256
    
    - name: "file_analyzer"
      file: "./tools/file_analyzer.py"
      function: "analyze_file"
      parameters:
        file_path: "${state.file_path}"
        deep_scan: false
      allowed_imports:
        - "pandas"
        - "numpy"
        - "requests"
```

### 4. Python Node Implementation

```python
# src/elf/core/nodes/python_node.py
from typing import Dict, Any
from elf.core.nodes.base import BaseNode
from elf.core.python_loader import PythonFunctionLoader
from elf.core.python_executor import PythonExecutor

class PythonNode(BaseNode):
    """Python function execution node"""
    
    def __init__(self, config: PythonNodeConfig):
        self.function_name = config.function_name
        self.parameters = config.parameters
        self.loader = PythonFunctionLoader()
        self.executor = PythonExecutor(
            max_execution_time=config.timeout or 30,
            max_memory_mb=config.memory_limit_mb or 512
        )
        self._function = None
    
    async def initialize(self) -> None:
        """Load the Python function during node initialization"""
        # Implementation needed
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute Python function and update workflow state"""
        # Implementation needed
    
    def _bind_parameters(self, state: WorkflowState) -> Dict[str, Any]:
        """Bind workflow state to function parameters"""
        # Implementation needed
```

### 5. Security and Sandboxing

```python
# src/elf/core/python_security.py
import ast
import importlib
from typing import Set, List

class PythonSecurityValidator:
    """Validate Python code for safe execution"""
    
    FORBIDDEN_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 
        'input', 'raw_input', 'file', 'reload'
    }
    
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'importlib', 'runpy',
        'pickle', 'marshal', 'shelve', 'dill'
    }
    
    def validate_code(self, code: str) -> bool:
        """Validate Python code for security issues"""
        # Implementation needed
    
    def validate_imports(self, allowed_modules: List[str]) -> bool:
        """Validate that only allowed modules are imported"""
        # Implementation needed
    
    def create_restricted_globals(self, allowed_modules: List[str]) -> Dict[str, Any]:
        """Create restricted global namespace"""
        # Implementation needed
```

## Testing Requirements

### Unit Tests

1. **Python Loader Tests** (`tests/core/test_python_loader.py`)
   - Test function loading from modules and files
   - Test function signature introspection and schema generation
   - Test module import validation and security checks
   - Test error handling for invalid functions and modules
   - Test function caching and reloading

2. **Python Executor Tests** (`tests/core/test_python_executor.py`)
   - Test function execution with various parameter types
   - Test timeout and resource limit enforcement
   - Test async and sync function execution
   - Test parameter binding and validation
   - Test error handling and exception propagation

3. **Python Node Tests** (`tests/core/test_python_node.py`)
   - Test Python node configuration validation
   - Test node execution with mock functions
   - Test state management and result handling
   - Test parameter interpolation from workflow state
   - Test error propagation and recovery

4. **Security Tests** (`tests/core/test_python_security.py`)
   - Test forbidden function and module detection
   - Test restricted execution environment
   - Test resource limit enforcement
   - Test malicious code prevention
   - Test import restriction validation

### Integration Tests

1. **Real Function Tests** (`tests/integration/test_python_functions.py`)
   - Test with actual Python functions in test modules
   - Test complex parameter binding and result handling
   - Test function execution within complete workflows
   - Test error scenarios and recovery
   - Create test Python modules with various function types

2. **Workflow Integration Tests** (`tests/integration/test_python_workflows.py`)
   - Test complete workflows using Python functions
   - Test Python function results flowing to subsequent nodes
   - Test conditional logic based on Python function results
   - Test error handling in workflow context

### CLI Tests

1. **Python Function CLI Tests** (`tests/cli/test_python_cli.py`)
   - Test workflow execution with Python nodes
   - Test Python function discovery and validation
   - Test error reporting for Python function issues
   - Test configuration validation

## Implementation Tasks

### Phase 1: Core Function Loading (High Priority)

1. **Implement Python Function Loader**
   - Create `PythonFunctionLoader` class with module and file loading
   - Add function signature introspection and schema generation
   - Implement function validation and caching
   - Add error handling for import and loading failures

2. **Implement Python Executor**
   - Create `PythonExecutor` class with safe execution environment
   - Add timeout and resource limit enforcement
   - Implement parameter binding and validation
   - Add async execution support

3. **Create Python Node Type**
   - Implement `PythonNode` class for workflow execution
   - Add Python node configuration schema
   - Implement function execution and result handling
   - Add parameter interpolation from workflow state

### Phase 2: Security and Advanced Features (Medium Priority)

1. **Implement Security Framework**
   - Create `PythonSecurityValidator` for code validation
   - Add restricted execution environment
   - Implement import restrictions and module whitelisting
   - Add resource monitoring and limits

2. **Enhanced Type System**
   - Implement automatic type conversion between workflow and Python types
   - Add Pydantic model integration
   - Create comprehensive type validation
   - Add schema generation from function signatures

3. **Advanced Parameter Binding**
   - Support complex parameter mapping from workflow state
   - Add template-based parameter binding
   - Implement nested object parameter handling
   - Add parameter validation and transformation

### Phase 3: Performance and Reliability (Lower Priority)

1. **Performance Optimization**
   - Implement function compilation and caching
   - Add execution pooling for concurrent functions
   - Optimize parameter binding and type conversion
   - Add performance monitoring and metrics

2. **Advanced Error Handling**
   - Implement retry logic for transient failures
   - Add detailed error reporting and debugging
   - Create function execution tracing
   - Add error recovery strategies

3. **Development Tools**
   - Create function testing and validation tools
   - Add function performance profiling
   - Implement hot reloading for development
   - Add function documentation generation

## Testing Strategy

1. **Isolated Function Testing**
   - Test function loading and execution in isolation
   - Use mock functions and test modules
   - Test all error conditions and edge cases
   - Focus on security and resource limits

2. **Integration Testing with Real Functions**
   - Create comprehensive test function library
   - Test common usage patterns and workflows
   - Validate end-to-end functionality
   - Test performance and resource usage

3. **Security Testing**
   - Test malicious code detection and prevention
   - Validate resource limit enforcement
   - Test import restriction effectiveness
   - Perform security audit of execution environment

## Documentation Updates

1. **Update project_tasks.md**
   - Add Python tool loading tasks to Phase 2 or create new phase
   - Mark current placeholder implementation status
   - Add testing and security requirements

2. **Create User Documentation**
   - Add Python function configuration examples to README
   - Create Python tool workflow examples
   - Document security guidelines and best practices
   - Add troubleshooting guide for Python function issues

3. **Developer Documentation**
   - Document Python function development guidelines
   - Create function testing best practices
   - Document security restrictions and limitations
   - Add examples for common function patterns

## Success Criteria

1. **Functional Requirements**
   - Load and execute Python functions from modules and files
   - Support complex parameter binding and type conversion
   - Provide secure execution environment with resource limits
   - Handle errors gracefully with detailed reporting

2. **Non-Functional Requirements**
   - Function execution overhead < 50ms for simple functions
   - Support for 100+ concurrent function executions
   - Memory usage isolation and limits
   - 99.9% reliability for valid function execution

3. **Security Requirements**
   - Prevent execution of malicious code
   - Enforce resource limits (CPU, memory, time)
   - Restrict file system and network access
   - Validate all imports and function calls

## Dependencies

1. **Core Dependencies**
   - Python AST parsing for security validation
   - Concurrent execution framework
   - Resource monitoring libraries
   - Type introspection utilities

2. **Development Dependencies**
   - Test function libraries
   - Security testing tools
   - Performance profiling tools
   - Documentation generation tools

This Python tool loading feature will enable ELF workflows to leverage the full power of the Python ecosystem while maintaining security and performance standards, making it possible to create sophisticated data processing and integration workflows.