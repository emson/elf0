# Project Tasks

## Phase 1: MVP Functionality

### LLM Integration
- [x] Implement multi-provider support:
  - [x] OpenAI provider integration
  - [x] Anthropic provider integration
  - [x] Ollama provider integration
- [x] Add support for Claude 3 Sonnet model
- [x] Implement proper error handling for LLM interactions

### Workflow Patterns
- [x] Implement basic sequential workflow pattern
- [x] Implement prompt chaining pattern
- [x] Implement prompt routing pattern
- [x] Support conditional branching in workflows

### Workflow Referencing
- [x] Support modular workflow composition through references
- [x] Implement reference merging with override precedence
- [x] Support both single and multiple file references
- [x] Handle circular reference detection
- [x] Implement proper path resolution for references

### Testing
- [x] Test LLM provider integrations
- [x] Test workflow pattern implementations
- [x] Test reference loading and merging
- [x] Test error handling and edge cases

## Phase 2: Enhanced CLI Features

### Self-Improvement Capabilities
- [x] Implement `elf improve yaml` command for workflow optimization
- [x] Integration with existing agent-optimizer.yaml specification
- [x] Automatic generation of improved YAML specs with better prompts and structure
- [x] Support for custom output paths for improved specifications
- [x] Add `--prompt` option for custom improvement guidance
- [x] Support @file references in custom improvement prompts

### Interactive Mode
- [x] Implement `elf prompt` command for interactive agent sessions
- [x] Real-time conversation interface with workflow agents
- [x] Session state management across multiple prompts
- [x] Clean exit handling (Ctrl+C, 'exit', 'quit', 'bye')
- [x] Error handling and recovery in interactive mode

### File Reference System
- [x] Implement @filename.ext syntax for automatic file inclusion
- [x] Integration with existing --context flag functionality
- [x] Support for multiple file references in single prompt
- [x] Automatic file content parsing and context preparation
- [x] Works in both command-line and interactive modes
- [x] Proper error handling for non-existent referenced files

### Documentation Updates
- [x] Update README.md with new CLI commands and usage examples
- [x] Update project_overview.md with feature descriptions
- [x] Document file reference system usage patterns
- [x] Add interactive mode documentation and examples


