<overview>
This is a CLI tool for running workflows defined in YAML files.
The tool can also be run to improve the workflows and even it's own workflow.

Key Features:
- Execute YAML-defined agent workflows with multiple LLM providers
- Self-improvement capabilities for optimizing YAML specifications
- Interactive prompt sessions with workflow agents
- File reference system using @filename.ext syntax for automatic context inclusion
- Support for complex workflow patterns (sequential, react, evaluator-optimizer)
</overview>

<requirements>
- Python 3.13
- `uv` by Astral for dependency management
- LLM API client (e.g. OpenAI, Anthropic)
- Use `pydantic` for data validation
</requirements>

<dependencies>
- `pydantic` version >= 2.0.0
- `pyyaml`
- `typer`
- `rich` (for enhanced CLI output and formatting)
</dependencies>

<cli_commands>
## Core Commands

### Workflow Execution
- `elf <spec_path> --prompt "Your prompt here"` - Execute a workflow with a prompt
- `elf <spec_path> --prompt_file prompt.md` - Execute using prompt from file
- `elf <spec_path> --prompt "Your prompt" --context file1.txt file2.py` - Include context files
- `elf <spec_path> --prompt "Analyze @config.yaml and @main.py"` - Use @file references for automatic context

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
</cli_commands>
