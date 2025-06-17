# Claude Code Integration Notes

## Overview

Claude Code SDK integration enables ELF workflows to generate, analyse, and modify code using Anthropic's Claude AI. This integration adds a new `claude_code` node type that can perform four main tasks: code generation, code analysis, code modification, and interactive coding assistance.

## Quick Start

### Prerequisites
```bash
# Required: Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"
```

### Basic Usage
```bash
# Generate code
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Create a Python function to validate email addresses"

# Analyse existing code
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Review this code for bugs @my_script.py"
```

## Node Configuration

### Basic Configuration
```yaml
nodes:
  - id: code_generator
    kind: claude_code
    config:
      task: "generate_code"              # Required: task type
      prompt: "Create a Python class"    # Required: task description
      output_format: "text"              # Optional: "text" or "json"
      tools: ["filesystem"]              # Optional: available tools
      temperature: 0.2                   # Optional: 0.0-1.0
      max_tokens: 4096                   # Optional: response length
```

### Task Types

1. **generate_code** - Create new code from requirements
2. **analyse_code** - Review and analyse existing code
3. **modify_code** - Edit existing code with specific changes
4. **chat** - General programming assistance

### File References
Use ELF's `@filename` syntax to include file contents:
```yaml
prompt: "Optimize the performance of @src/utils.py"
files: ["@src/main.py", "@tests/test_main.py"]
```

## Use Cases

### 1. Code Generation
Generate complete applications or components from specifications.

**Example: API Generation**
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Create a FastAPI REST API with user authentication and CRUD operations"
```

**Workflow Pattern:**
```yaml
nodes:
  - id: generate_models
    kind: claude_code
    config:
      task: "generate_code"
      prompt: "Create Pydantic models for: {input}"
  
  - id: generate_endpoints
    kind: claude_code
    config:
      task: "generate_code"
      prompt: "Create FastAPI endpoints using these models: {output}"
```

### 2. Code Analysis and Review
Analyse code for bugs, security issues, performance problems, and maintainability.

**Example: Security Review**
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Analyse @auth.py for security vulnerabilities"
```

**Multi-aspect Analysis:**
```yaml
workflow:
  type: custom_graph
  nodes:
    - id: security_check
      kind: claude_code
      config:
        task: "analyse_code"
        prompt: "Check for security vulnerabilities in: {input}"
    
    - id: performance_check
      kind: claude_code
      config:
        task: "analyse_code"
        prompt: "Identify performance bottlenecks in: {input}"
    
    - id: maintainability_check
      kind: claude_code
      config:
        task: "analyse_code"
        prompt: "Review code maintainability in: {input}"
```

### 3. Code Modification and Refactoring
Automatically improve existing code based on analysis or requirements.

**Example: Add Error Handling**
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Add comprehensive error handling to @api.py"
```

**Refactoring Workflow:**
```yaml
nodes:
  - id: analyse_structure
    kind: claude_code
    config:
      task: "analyse_code"
      prompt: "Analyse code structure and identify refactoring opportunities"
  
  - id: apply_refactoring
    kind: claude_code
    config:
      task: "modify_code"
      prompt: "Apply recommended refactoring: {output}"
      tools: ["filesystem"]
```

### 4. Documentation Generation
Generate and maintain code documentation automatically.

**Example: API Documentation**
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Generate OpenAPI documentation for @src/api/"
```

**Living Documentation:**
```yaml
nodes:
  - id: extract_api_info
    kind: claude_code
    config:
      task: "analyse_code"
      prompt: "Extract API endpoints and schemas from codebase"
  
  - id: generate_docs
    kind: claude_code
    config:
      task: "generate_code"
      prompt: "Create comprehensive API documentation: {output}"
      tools: ["filesystem"]
```

### 5. Language Translation
Convert code between programming languages while preserving functionality.

**Example: Python to TypeScript**
```yaml
nodes:
  - id: analyse_python_code
    kind: claude_code
    config:
      task: "analyse_code"
      prompt: "Analyse Python code structure and patterns"
      files: ["@src/main.py"]
  
  - id: generate_typescript
    kind: claude_code
    config:
      task: "generate_code"
      prompt: "Convert to TypeScript maintaining same functionality: {output}"
```

### 6. Self-Improvement Workflows
Enable ELF to analyse and improve its own codebase.

**Example: Platform Enhancement**
```bash
uv run elf agent specs/examples/claude_code_self_improvement.yaml \
  --prompt "Add better error handling to MCP node implementation"
```

**Self-Improvement Pattern:**
```yaml
nodes:
  - id: analyse_platform_code
    kind: claude_code
    config:
      task: "analyse_code"
      prompt: "Analyse ELF platform for improvement opportunities: {input}"
      files: ["src/elf/"]
  
  - id: implement_improvements
    kind: claude_code
    config:
      task: "modify_code"
      prompt: "Implement identified improvements: {output}"
      tools: ["filesystem"]
  
  - id: validate_changes
    kind: claude_code
    config:
      task: "chat"
      prompt: "Run tests and validate improvements"
      tools: ["bash", "filesystem"]
```

## Advanced Patterns

### State-Driven Workflows
Pass structured data between nodes for complex multi-step processing.

```yaml
nodes:
  - id: extract_api_spec
    kind: claude_code
    config:
      task: "analyse_code"
      output_format: "json"
      prompt: "Extract API specification as JSON"
  
  - id: generate_client
    kind: claude_code
    config:
      task: "generate_code"
      prompt: "Generate client library for API spec: {output}"
```

### Parallel Processing
Run multiple analysis tasks simultaneously.

```yaml
workflow:
  type: custom_graph
  edges:
    - source: "input"
      target: ["security_check", "performance_check", "style_check"]
    - source: ["security_check", "performance_check", "style_check"]
      target: "consolidate_results"
```

### Iterative Improvement
Create feedback loops for continuous code enhancement.

```yaml
nodes:
  - id: generate_initial_code
    kind: claude_code
    config:
      task: "generate_code"
  
  - id: analyse_generated_code
    kind: claude_code
    config:
      task: "analyse_code"
      prompt: "Review generated code for improvements: {output}"
  
  - id: refine_code
    kind: claude_code
    config:
      task: "modify_code"
      prompt: "Apply suggested improvements: {output}"
```

## Technical Implementation

### Architecture
- **Node Type**: `claude_code` registered in ELF's node factory system
- **Async Handling**: Runs in isolated threads to prevent event loop conflicts
- **Error Recovery**: Graceful fallback with mock responses when SDK unavailable
- **State Integration**: Full integration with ELF's workflow state system

### Configuration Options
```yaml
config:
  task: "generate_code"                    # Required
  prompt: "Task description"               # Required
  files: ["@file1.py", "@file2.py"]       # Optional context files
  output_format: "text"                   # "text" or "json"
  tools: ["filesystem", "bash"]           # Available tools
  temperature: 0.2                        # Creativity level (0.0-1.0)
  max_tokens: 4096                        # Response length limit
  working_directory: "/path/to/project"   # Execution context
```

### Tool Options
- **filesystem**: Read and write files
- **bash**: Execute shell commands
- **No tools**: Analysis only (default for analyse_code)

## Current Limitations

### SDK Compatibility
- Claude Code SDK v0.0.10 has known parsing issues
- ELF provides mock responses when SDK fails
- Real SDK functionality available when compatibility issues resolved

### Resource Considerations
- API usage costs apply for Anthropic API calls
- Large codebases may consume significant tokens
- Recommended to use appropriate context size limits

### Authentication
- Requires valid Anthropic API key
- Set via environment variable: `ANTHROPIC_API_KEY`

## Best Practices

### Prompt Design
- Be specific about requirements and constraints
- Include context through file references
- Use appropriate task types for different operations

### Workflow Structure
- Start with analysis before modification
- Include validation steps after code changes
- Use structured output for complex data passing

### Error Handling
- Include fallback nodes for critical paths
- Validate outputs before proceeding to next steps
- Use appropriate timeouts for long-running operations

### Performance Optimization
- Limit file context to necessary files only
- Use lower temperature for precision tasks
- Batch related operations when possible

## Examples

### Simple Code Generation
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Create a Python class for managing user sessions"
```

### Code Review with Context
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Review @auth.py considering security best practices from @security_guidelines.md"
```

### Multi-step Improvement
```bash
uv run elf agent specs/examples/claude_code_example.yaml \
  --prompt "Analyse @legacy_code.py, identify issues, and generate improved version"
```

### Platform Self-Improvement
```bash
uv run elf agent specs/examples/claude_code_self_improvement.yaml \
  --prompt "Add input validation to ELF's workflow compiler"
```

## Testing

All Claude Code functionality includes comprehensive test coverage:
- Node creation and configuration validation
- Mock response handling
- Workflow integration testing
- Error handling verification

Run tests with:
```bash
uv run pytest tests/core/test_claude_code_integration.py
```
