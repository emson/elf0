# Claude Code SDK Integration

## Overview

ELF now includes full integration with Claude Code SDK, enabling self-evolving AI capabilities and advanced code generation, analysis, and modification directly within workflow orchestration.

## Key Features

### 1. Claude Code Node Type
- New `claude_code` node kind for YAML workflows
- Supports multiple task types: `generate_code`, `analyze_code`, `modify_code`, `chat`
- Configurable output formats: `text`, `json`
- Template parameter binding from workflow state
- File context inclusion for code operations

### 2. Self-Improvement Capabilities
- ELF can now modify its own codebase using Claude Code
- Dynamic workflow generation and optimization
- Automatic code quality improvement and refactoring
- Real-time capability expansion

### 3. Advanced Code Operations
- **Code Generation**: Create complete applications from requirements
- **Code Analysis**: Comprehensive code review and improvement suggestions  
- **Code Modification**: Apply improvements and fix issues
- **Chat Interface**: Interactive development conversations

## Configuration

### Basic Claude Code Node
```yaml
- id: code_generator
  kind: claude_code
  config:
    task: "generate_code"
    prompt: "Create a Python function that ${state.requirements}"
    output_format: "text"
    tools: ["filesystem", "bash"]
    temperature: 0.2
```

### Advanced Configuration
```yaml
- id: code_analyzer
  kind: claude_code
  config:
    task: "analyze_code"
    prompt: "Analyze this code: ${state.code_output}"
    files: ["${state.source_files}"]
    output_format: "json"
    session_id: "code_review_session"
    model_name: claude-sonnet-4-20250514
    working_directory: "/path/to/project"
    tools: ["filesystem", "bash"]
```

## Task Types

### 1. `generate_code`
Creates new code based on requirements and specifications.

**Use Cases:**
- Application development from requirements
- Component generation
- Test case creation
- Documentation generation

### 2. `analyze_code`
Analyzes existing code for quality, security, and performance.

**Use Cases:**
- Code reviews
- Security audits
- Performance analysis
- Technical debt assessment

### 3. `modify_code`
Modifies existing code based on analysis or requirements.

**Use Cases:**
- Bug fixes
- Feature enhancements
- Refactoring
- Performance optimizations

### 4. `chat`
General conversational interface for development tasks.

**Use Cases:**
- Interactive development
- Problem-solving discussions
- Architecture planning
- Technical consultations

## State Integration

Claude Code nodes integrate seamlessly with ELF's workflow state:

```yaml
# Template binding from previous node outputs
prompt: "Improve this code: ${state.output}"

# File path binding from state
files: ["${state.generated_files}", "src/existing.py"]

# Multi-level state access
prompt: "Analyze ${state.analysis.recommendations}"
```

## Example Workflows

### 1. Complete Application Development
```yaml
workflow:
  type: sequential
  nodes:
    - id: requirements_analysis
      kind: agent
      # ... analyze requirements
    
    - id: code_generation
      kind: claude_code
      config:
        task: "generate_code"
        prompt: "Build application: ${state.output}"
    
    - id: code_review
      kind: claude_code
      config:
        task: "analyze_code"
        prompt: "Review generated code: ${state.output}"
    
    - id: code_improvement
      kind: claude_code
      config:
        task: "modify_code"
        prompt: "Apply improvements: ${state.output}"
```

### 2. Self-Improvement Workflow
```yaml
workflow:
  type: sequential
  nodes:
    - id: analyze_improvement_request
      kind: agent
      # ... analyze what to improve
    
    - id: implement_improvement
      kind: claude_code
      config:
        task: "modify_code"
        prompt: "Improve ELF: ${state.output}"
        files: ["src/elf/"]
        working_directory: "/path/to/elf"
    
    - id: test_improvement
      kind: claude_code
      config:
        task: "generate_code"
        prompt: "Create tests: ${state.output}"
```

## Benefits

### 1. Self-Evolving Platform
- ELF can improve its own capabilities
- Dynamic feature development
- Continuous optimization
- Adaptive architecture

### 2. Complete Development Lifecycle
- Requirements → Code → Review → Improvement
- Automated quality assurance
- Continuous refactoring
- Production-ready output

### 3. Infinite Extensibility
- Generate new node types on-demand
- Create custom workflow patterns
- Build domain-specific tools
- Extend capabilities dynamically

## Installation

The integration is now complete and ready to use! Install the Claude Code SDK:

```bash
# Install the required dependency
uv pip install claude-code-sdk>=0.0.10

# Or update your project dependencies
dependencies = [
    "claude-code-sdk>=0.0.10",
    # ... other dependencies
]
```

## Usage

You can now use Claude Code nodes in your ELF workflows:

```bash
# Run a workflow with Claude Code integration
uv run elf0 agent specs/examples/claude_code_example.yaml --prompt "Create a Python web scraper"

# Run the self-improvement workflow
uv run elf0 agent specs/examples/claude_code_self_improvement.yaml --prompt "Add caching to ELF's LLM client"
```

## Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: SDK availability and authentication
- **Execution Errors**: Task failures and timeouts
- **Configuration Errors**: Invalid node configurations
- **Graceful Degradation**: Continues workflow with error reporting

## Security Considerations

- Code execution is controlled through Claude Code SDK security
- File access is limited to specified directories
- Generated code is reviewed before execution
- Audit trails for all code modifications

## Future Enhancements

1. **Advanced Simulation Code Generation**: Generate specialized agent behaviors for multi-agent simulations
2. **Real-Time Algorithm Generation**: For trading and analysis applications
3. **Custom MCP Server Generation**: Create specialized tools on-demand
4. **Automated Testing Integration**: Generate and run tests automatically
5. **Documentation Generation**: Auto-generate API docs and guides

## Strategic Impact

This integration transforms ELF from a static workflow orchestrator into the world's first truly self-evolving AI platform, providing:

1. **Unprecedented Flexibility**: Any capability can be developed on-demand
2. **Continuous Improvement**: System enhances itself automatically
3. **Competitive Advantage**: No other platform offers self-modification capabilities
4. **Market Leadership**: Positions ELF as the most advanced AI orchestration platform

The Claude Code integration represents a fundamental leap forward in AI platform capabilities, enabling ELF to adapt, evolve, and improve autonomously while maintaining production reliability and security.
