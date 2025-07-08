# docs/notes/notes_function_calling.md

# Python Function Calling Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to implement Python function calling capabilities in the Elf workflow framework. The existing schema already supports Python functions perfectly—no schema changes are required. The implementation focuses on replacing the current placeholder with a robust, secure function execution system that enables powerful workflow capabilities including user interaction, file processing, and workflow linking.

**Key Insight**: The schema and infrastructure already exist. We just need to implement the execution engine.

## Current State Analysis

### ✅ What Already Works
- **Schema Support**: `functions` section supports `type: python` with `entrypoint: "module.function"`
- **Node Integration**: `tool` nodes can reference functions via `ref` field
- **Routing Infrastructure**: `make_tool_node()` in `compiler.py:522` routes Python vs MCP functions
- **Execution Interface**: `load_tool()` provides the wrapper interface for function execution
- **State Management**: `WorkflowState` provides consistent data flow between nodes

### 🚧 What Needs Implementation
- **Function Loading**: Replace placeholder in `make_tool_node()` with real Python import/execution
- **Parameter Binding**: Map workflow state to function parameters
- **Security Framework**: Safe execution environment with restrictions
- **User Interaction**: Functions that can pause workflow and get user input
- **Error Handling**: Comprehensive error management and recovery

### 📍 Current Placeholder Location
File: `src/elf/core/compiler.py:551-558`
```python
def python_tool_placeholder(state: WorkflowState) -> WorkflowState:
    return {
        **state,
        "output": f"Python tool '{function_spec.name}' (entrypoint: {function_spec.entrypoint}) - Implementation needed",
        "error_context": "Python tool loading not fully implemented"
    }
```

## Technical Design

### Core Architecture

#### 1. Function Discovery & Loading System
```python
class PythonFunctionLoader:
    """Secure loader for Python functions from entrypoints."""
    
    def load_function(self, entrypoint: str) -> callable:
        """Load function from dotted path like 'mymodule.submodule.function_name'"""
        
    def validate_function(self, fn: callable) -> bool:
        """Validate function signature and safety"""
        
    def get_function_signature(self, fn: callable) -> inspect.Signature:
        """Extract parameter information for binding"""
```

**Implementation Approach**:
- Use `importlib.import_module()` for dynamic imports
- Support both relative and absolute imports
- Cache loaded functions for performance
- Validate function signatures on load

#### 2. Parameter Binding System
Following the existing MCP node pattern for consistency:

```yaml
# Workflow YAML example
functions:
  process_pdf:
    type: python
    name: "PDF Processor"
    entrypoint: "mytools.pdf.extract_text"

workflow:
  nodes:
    - id: pdf_extractor
      kind: tool
      ref: process_pdf
      config:
        parameters:
          file_path: "${state.input_file}"
          extract_images: true
          page_range: "${state.json.pages}"
```

**Parameter Binding Features**:
- `${state.field}` - Direct state field access
- `${state.json.field}` - JSON extraction from previous output
- Static values supported
- Type coercion based on function signature
- Default parameter handling

#### 3. Security Framework

**Multi-Layer Security Approach**:

**Layer 1: Import Restrictions**
```python
RESTRICTED_MODULES = {
    'os', 'subprocess', 'sys', 'importlib', 
    'eval', 'exec', '__import__', 'compile',
    'socket', 'urllib', 'requests'  # Network access
}

ALLOWED_MODULES = {
    'pandas', 'numpy', 'openpyxl', 'PyPDF2', 'pdfplumber',
    'json', 'csv', 'datetime', 'pathlib', 'typing',
    'math', 'statistics', 'collections', 're'
}
```

**Layer 2: Execution Environment**
- Execution timeouts (default: 30 seconds)
- Memory limits using `resource` module
- Restricted builtins (no `open`, `eval`, `exec`)
- Read-only filesystem access by default

**Layer 3: Function Validation**
- Signature inspection before execution
- Parameter type validation
- Return value sanitization
- Error containment

#### 4. User Interaction System

**Special Function Pattern for User Input**:
```python
# User-defined function
def get_user_approval(state: WorkflowState) -> WorkflowState:
    """Function that pauses workflow and asks for user input."""
    message = state.get('message', 'Please provide input:')
    
    # This triggers workflow interruption
    user_input = request_user_input(
        prompt=message,
        input_type='text',  # 'text', 'choice', 'file'
        validation=None     # Optional validation function
    )
    
    return {
        **state,
        'user_response': user_input,
        'output': f"User responded: {user_input}"
    }
```

**Implementation Strategy**:
- Use LangGraph's interruption system
- Support different input types (text, choices, file upload)
- Provide input validation
- Handle timeout scenarios

## Implementation Plan

### Phase 1: Core Function Loading (Week 1)
**Priority: High** | **Effort: 3-4 days**

**Tasks**:
1. **Create `PythonFunctionLoader` class** in `src/elf/core/function_loader.py`
   - Implement `load_function()` with importlib
   - Add function caching mechanism
   - Create comprehensive error handling

2. **Replace placeholder in `compiler.py`**
   - Update `make_tool_node()` to use real function loading
   - Integrate with existing `load_tool()` wrapper
   - Maintain backward compatibility

3. **Basic parameter binding**
   - Implement `${state.field}` syntax
   - Support for static parameters
   - Type coercion for basic types

**Success Criteria**:
- Simple Python functions execute successfully
- Parameters bind from workflow state
- Errors are handled gracefully
- Integration tests pass

### Phase 2: Security & Robustness (Week 2)
**Priority: High** | **Effort: 4-5 days**

**Tasks**:
1. **Implement security framework**
   - Module import restrictions
   - Execution timeouts
   - Memory limits
   - Restricted builtins

2. **Enhanced parameter binding**
   - Add `${state.json.field}` JSON extraction
   - Support complex parameter types
   - Default parameter handling
   - Parameter validation

3. **Comprehensive error handling**
   - Import errors
   - Execution errors
   - Timeout handling
   - Security violations

**Success Criteria**:
- Malicious code is prevented from executing
- Resource limits are enforced
- Complex parameter binding works
- Error messages are clear and actionable

### Phase 3: User Interaction (Week 3)
**Priority: Medium** | **Effort: 3-4 days**

**Tasks**:
1. **Design user interaction API**
   - Create `request_user_input()` function
   - Support multiple input types
   - Integrate with LangGraph interruptions

2. **Implement workflow interruption**
   - Pause/resume functionality
   - State persistence during interruption
   - Timeout handling for user responses

3. **CLI integration**
   - User input prompts in CLI
   - File upload handling
   - Interactive choice selection

**Success Criteria**:
- Workflows can pause and ask for user input
- Different input types work correctly
- Workflow resumes with user data
- CLI provides good user experience

### Phase 4: Advanced Features (Week 4)
**Priority: Low** | **Effort: 4-5 days**

**Tasks**:
1. **File processing capabilities**
   - PDF processing functions
   - Excel/CSV handling
   - Image processing basics
   - File validation and safety

2. **Workflow linking functions**
   - Functions that execute other workflows
   - State passing between workflows
   - Workflow composition utilities

3. **Performance optimizations**
   - Function result caching
   - Async execution support
   - Memory usage optimization

**Success Criteria**:
- PDF and Excel processing works reliably
- Workflows can be composed via functions
- Performance is acceptable for production use
- Memory usage is well-controlled

## Security Considerations

### Risk Assessment

**High Risk - Mitigated**:
- **Arbitrary code execution**: Mitigated by import restrictions and whitelisting
- **Resource exhaustion**: Mitigated by timeouts and memory limits
- **File system access**: Mitigated by restricted paths and read-only defaults

**Medium Risk - Monitored**:
- **Network access**: Blocked by default, explicit allowlist if needed
- **Sensitive data exposure**: Functions must handle data securely
- **Dependency vulnerabilities**: Regular security scanning recommended

**Low Risk - Accepted**:
- **Function complexity**: User responsibility to write maintainable code
- **Performance impact**: Balanced against functionality benefits

### Security Best Practices

1. **Principle of Least Privilege**: Functions run with minimal permissions
2. **Defense in Depth**: Multiple security layers prevent single points of failure
3. **Fail Secure**: Security violations result in execution termination
4. **Audit Trail**: Log all function executions and security events
5. **Regular Updates**: Keep security allowlists and restrictions current

## Use Cases & Examples

### Use Case 1: PDF Processing Workflow
```yaml
# pdf_analyzer.yaml
version: "0.1"
description: "Extract and analyze PDF content"
runtime: "langgraph"

llms:
  analyzer:
    type: openai
    model_name: gpt-4.1-mini

functions:
  extract_pdf:
    type: python
    name: "PDF Text Extractor"
    entrypoint: "tools.pdf.extract_text"
    
  analyze_text:
    type: python  
    name: "Text Analyzer"
    entrypoint: "tools.analysis.analyze_content"

workflow:
  type: custom_graph
  nodes:
    - id: extract
      kind: tool
      ref: extract_pdf
      config:
        parameters:
          file_path: "${state.input_file}"
          
    - id: analyze
      kind: agent
      ref: analyzer
      config:
        prompt: "Analyze this text and extract key insights: ${state.output}"
        
    - id: process
      kind: tool
      ref: analyze_text
      config:
        parameters:
          text: "${state.output}"
          analysis_type: "summary"
      stop: true
      
  edges:
    - source: extract
      target: analyze
    - source: analyze  
      target: process
```

### Use Case 2: User Input Workflow
```yaml
# user_input_example.yaml
version: "0.1"
description: "Get user approval before proceeding"
runtime: "langgraph"

functions:
  get_approval:
    type: python
    name: "User Approval"
    entrypoint: "workflows.interactions.get_user_approval"
    
  send_email:
    type: python
    name: "Email Sender" 
    entrypoint: "tools.email.send_message"

workflow:
  type: custom_graph
  nodes:
    - id: ask_approval
      kind: tool
      ref: get_approval
      config:
        parameters:
          message: "Send email to ${state.recipient}?"
          
    - id: send
      kind: tool
      ref: send_email
      config:
        parameters:
          recipient: "${state.recipient}"
          subject: "${state.subject}"
          body: "${state.email_body}"
      stop: true
      
  edges:
    - source: ask_approval
      target: send
      condition: "state.get('user_response') == 'yes'"
```

### Use Case 3: Workflow Linking
```yaml
# master_workflow.yaml
version: "0.1"
description: "Orchestrate multiple sub-workflows"
runtime: "langgraph"

functions:
  run_subworkflow:
    type: python
    name: "Workflow Runner"
    entrypoint: "elf0.runners.execute_workflow"

workflow:
  type: sequential
  nodes:
    - id: process_data
      kind: tool
      ref: run_subworkflow
      config:
        parameters:
          workflow_path: "./data_processing.yaml"
          input_data: "${state.raw_data}"
          
    - id: generate_report
      kind: tool
      ref: run_subworkflow
      config:
        parameters:
          workflow_path: "./report_generator.yaml" 
          processed_data: "${state.output}"
      stop: true
```

## Testing Strategy

### Unit Tests
- **Function Loading**: Test import mechanisms, error handling
- **Parameter Binding**: Test all binding patterns and edge cases
- **Security**: Test restriction enforcement and violation handling
- **User Interaction**: Test interruption and resume functionality

### Integration Tests  
- **End-to-End Workflows**: Test complete workflows with Python functions
- **Error Scenarios**: Test failure modes and recovery
- **Performance**: Test with realistic workloads and data sizes
- **Security**: Test actual attack scenarios

### Test Files Structure
```
tests/core/python_functions/
├── test_function_loader.py      # Function loading and caching
├── test_parameter_binding.py    # State to parameter mapping
├── test_security.py             # Security restrictions
├── test_user_interaction.py     # User input functionality  
├── test_integration.py          # End-to-end workflows
└── fixtures/
    ├── test_functions.py        # Sample functions for testing
    ├── malicious_functions.py   # Security test cases
    └── sample_workflows/        # Test workflow files
```

## Future Considerations

### Near-term Enhancements (3-6 months)
1. **Async Function Support**: Enable async/await patterns for I/O operations
2. **Enhanced User Interaction**: Support file uploads, rich UI components
3. **Function Marketplace**: Curated library of common workflow functions
4. **Performance Monitoring**: Execution metrics and optimization recommendations

### Long-term Vision (6-12 months)
1. **Visual Function Builder**: GUI for creating functions without coding
2. **Distributed Execution**: Run functions on remote workers/containers  
3. **ML Integration**: Built-in functions for common ML operations
4. **Advanced Security**: Formal verification and sandboxing improvements

### Considerations for LLM Implementation

This implementation plan is designed to be **LLM-friendly** with:

**Clear Interfaces**: Each component has well-defined inputs/outputs and responsibilities
**Incremental Development**: Phases can be implemented independently with clear success criteria  
**Comprehensive Examples**: Real-world use cases demonstrate expected functionality
**Explicit Error Handling**: All failure modes are identified and addressed
**Security-First Design**: Security considerations are built into every component
**Testing Guidance**: Complete testing strategy ensures reliable implementation

The existing codebase provides excellent foundations with its vertical slice architecture, comprehensive error handling, and LLM-optimized structure. This function calling implementation maintains those same principles while adding powerful new capabilities that transform Elf from a workflow executor into a complete automation platform.

## Implementation Summary

**Schema Changes**: ✅ None required - existing schema is perfect
**Core Implementation**: 🔄 Replace placeholder in `compiler.py:551-558`  
**Security Model**: 🛡️ Multi-layer restrictions with allowlist approach
**User Experience**: 🎯 Seamless integration with existing CLI and workflow patterns
**Development Effort**: ⏱️ ~4 weeks for full implementation across all phases

This design enables Elf to become a powerful platform for AI-driven automation while maintaining the security, simplicity, and extensibility that make it ideal for LLM-assisted development.