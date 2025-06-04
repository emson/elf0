<overview>
This is a CLI tool for running YAML agent workflows (specs).
The tool can also be run to improve the YAML agent workflows and even it's own workflow.

Key Features:
- Execute YAML-defined agent workflows with multiple LLM providers (OpenAI, Anthropic, Ollama)
- MCP (Model Context Protocol) integration for external tool access
- Self-improvement capabilities for optimizing YAML specifications
- Interactive prompt sessions with workflow agents
- File reference system using @filename.ext syntax for automatic context inclusion
- Support for complex Anthropic's "Building Effective Agents" agent design patterns (e.g. sequential, react, evaluator-optimizer, custom graphs)
- Workflow referencing and composition for modular design
</overview>

<requirements>
- Python 3.13
- `uv` by Astral for dependency management
- LLM API client (e.g. OpenAI, Anthropic)
- Use `pydantic` for data validation
</requirements>

<implementation>
- Write clear and concise code
- Code must be minimal and flexible, and concisely implements the solution
- Use composite functions made up of concise subfunctions
- Add short clear and concise code documentation
- Write code documentation to help LLMs to easily understand the code
- Always use absolute paths in imports, do not use relative import paths
</implementation>

<dependencies>
- `pydantic` version >= 2.0.0
- `pyyaml`
- `typer`
- `rich` (for enhanced CLI output and formatting)
</dependencies>

<cli_commands>
## Core Commands

### Workflow Execution
- `elf agent <spec_path> --prompt "Your prompt here"` - Execute a workflow with a prompt
- `elf agent <spec_path> --prompt_file prompt.md` - Execute using prompt from file
- `elf agent <spec_path> --prompt "Your prompt" --context file1.txt file2.py` - Include context files
- `elf agent <spec_path> --prompt "Analyze @config.yaml and @main.py"` - Use @file references for automatic context
- Supports workflows with MCP nodes for external tool integration (filesystem, databases, APIs)

### Self-Improvement
- `elf improve yaml <spec_path>` - Improve a YAML workflow specification
- `elf improve yaml <spec_path> --output improved.yaml` - Save improved spec to specific file
- `elf improve yaml <spec_path> --prompt "custom guidance"` - Custom improvement guidance
- Supports @file references in custom prompts

### Interactive Mode
- `elf prompt <spec_path>` - Start interactive session with a workflow agent
- Supports @file references during interactive prompts
- Type 'exit', 'quit', or 'bye' to end session

## File Reference System
Use @filename.ext within any prompt to automatically include file contents as context:
- Example: "Explain this code @main.py and compare it to @test.py"
- Works in both command-line prompts and interactive mode
- Combines with existing --context flag functionality

## MCP Integration
The framework supports MCP (Model Context Protocol) nodes for external tool integration:
- **MCP Nodes**: Direct integration with MCP servers in workflow YAML (kind: mcp)
- **Automatic Server Management**: MCP servers are started and stopped automatically
- **Parameter Binding**: Dynamic parameter binding from workflow state using ${state.variable} syntax
- **Stdio Transport**: Currently supports stdio transport (MVP), with plans for SSE/WebSocket
- **Tool Discovery**: Automatic discovery and execution of tools from MCP servers
- **Examples Available**: See specs/examples/simple_mcp.yaml and related test files
</cli_commands>
