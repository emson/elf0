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

### Spec Listing Feature
- [x] Implement `elf list-specs` command to display workflow specifications.
- [x] Scan `./specs` directory for `.yaml`/`.yml` files (ignores subdirectories).
- [x] Extract descriptions from `description` field in YAML or first comment line.
- [x] Display results using Rich for professional formatting (filename, description, separators).
- [x] Handle missing or empty `./specs` directory with user-friendly messages.
- [x] Implement helper functions in `elf.utils.file_utils` (`list_spec_files`, `extract_spec_description`).

### CLI Improvements
- [x] Refactor verbose `run-workflow-command` to concise `agent` command
- [x] Update all tests to use new command structure
- [x] Update CLI help text for clarity and accuracy
- [x] Ensure backward compatibility through proper command registration

### Documentation Updates
- [x] Update README.md with new CLI commands and usage examples
- [x] Update project_overview.md with feature descriptions
- [x] Document file reference system usage patterns
- [x] Add interactive mode documentation and examples
- [x] Update all documentation to reflect `agent` command rename

## Phase 3: Core Platform Features

### CLI Enhancements (Output & Logging)
- [x] Implement clean separation of workflow output (stdout) and logs (stderr)
- [x] Add `--quiet` mode to suppress non-critical logs
- [x] Ensure Rich consoles and Python logging direct to appropriate streams
- [x] Update CLI help and documentation with redirection examples

### MCP Integration (MVP Complete)
- [x] Replace placeholder MCP client with real MCP protocol implementation
- [x] Implement MCP server connection management (stdio transport only for MVP)
- [x] Add MCP tool discovery, caching, and execution
- [x] Create MCP node type for workflow integration
- [x] Add MCP server configuration in workflow YAML
- [x] Add comprehensive MCP integration tests
- [x] Create MCP workflow examples and documentation
- [ ] Extend MCP support for SSE and WebSocket transports
- [ ] Implement MCP security and authentication
- [ ] Add MCP server lifecycle management and error recovery

### Python Tool Loading
- [ ] Implement Python function loader with module and file support
- [ ] Create secure Python execution environment with resource limits
- [ ] Add Python node type for workflow integration
- [ ] Implement function signature introspection and schema generation
- [ ] Add parameter binding and type conversion
- [ ] Create security framework for safe Python execution
- [ ] Add comprehensive Python tool tests
- [ ] Create Python tool development documentation

### Structured Output Framework
- [x] Implement `format` field for node configuration with "json" and "yaml" support
- [x] Add JSON structured output processing with Spec schema validation
- [x] Create automatic JSON-to-YAML conversion for clean output generation
- [x] Add markdown fence cleaning for robust LLM output handling
- [x] Integrate structured output processing into compiler workflow
- [x] Add comprehensive test coverage for structured output functionality
- [x] Update documentation with `format` field usage and examples
- [x] Replace non-standard `validate_yaml_output` with industry-standard `format` approach

### ReAct Pattern Implementation
- [ ] Implement ReAct controller with reasoning/action/observation loop
- [ ] Create action framework for tool integration
- [ ] Add ReAct node type for workflow execution
- [ ] Implement reasoning templates and prompt management
- [ ] Add action parsing and execution coordination
- [ ] Create termination logic and success criteria evaluation
- [ ] Add comprehensive ReAct pattern tests
- [ ] Create ReAct workflow examples and documentation


