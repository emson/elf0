# Elf: AI Workflow Architect

**Elf is a Python framework for defining, executing, and intelligently improving LLM-powered agent workflows.**

It enables developers to build complex sequences of AI agent interactions declaratively and **provides tools to leverage AI itself for optimizing these workflows**.
Our core philosophy is to _"start small, make it work, then make it better, but build on solid foundations."_

## Vision

AI and LLMs are changing fast, therefore we must find ways in which to utilise them to help build better AI systems.
This is a tool that allows users to quickly define agentic workflows, specify the attributes of each agent and their prompts, the tools they can access and finally how to output their results.
What is more as this workflow is declarative, it can be fed back into the the system and be used to improve the workflow itself.
Key aims:
1.  **Simplify Complexity:** Provide a clear, declarative way (via YAML) to define multi-agent workflows, making them easy to understand, share, and manage.
2.  **Promote Flexibility:** Enable flexible selection of LLM clients (e.g., OpenAI, Anthropic), models, parameters, and tools at both the workflow and individual agent level.
3.  **Facilitate Extensibility:** Allow for the easy integration of custom tools, functions, and future capabilities like Model Context Protocol (MCP) and Retrieval Augmented Generation (RAG).
4.  **Enable AI-Driven Optimization:** Introduce an "AI Workflow Architect" (Elf) agent capable of analyzing existing workflows and suggesting improvements, effectively using AI to enhance AI systems.

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Usage

### Basic Workflow Execution
```bash
# Execute a workflow with a simple prompt
uv run elf specs/basic_chat.yaml --prompt "What is the weather in London?"

# Use a prompt file
uv run elf specs/basic_chat.yaml --prompt_file my_prompt.md

# Include context files
uv run elf specs/basic_chat.yaml --prompt "Summarize these files" --context file1.txt --context file2.py

# Use @ file references for automatic context inclusion
uv run elf specs/basic_chat.yaml --prompt "Explain this code @main.py and compare it to @test.py"

# Save output to file
uv run elf specs/basic_chat.yaml --prompt "Generate a report" --output report.md
```

### Self-Improvement Features
```bash
# Improve any YAML workflow specification
uv run elf improve yaml specs/my_workflow.yaml

# Save improved version to specific file
uv run elf improve yaml specs/my_workflow.yaml --output specs/my_workflow_v2.yaml

# Custom improvement guidance
uv run elf improve yaml specs/my_workflow.yaml --prompt "Focus on making prompts more specific"

# Reference-based improvement with @ file syntax
uv run elf improve yaml specs/my_workflow.yaml --prompt "Follow patterns from @examples/best_workflow.yaml"
```

### Interactive Mode
```bash
# Start an interactive session with any workflow agent
uv run elf prompt specs/basic_chat.yaml

# Then type prompts interactively, including @ file references:
💬 Prompt: Analyze @config.yaml and suggest improvements
💬 Prompt: Review @README.md and @src/main.py for consistency
💬 Prompt: exit
```

### File Reference System
Elf supports automatic file inclusion using `@filename.ext` syntax in any prompt:

- **In command-line prompts**: `--prompt "Explain @main.py"`
- **In interactive mode**: `💬 Prompt: Review @config.yaml`
- **Combined with context files**: Works alongside `--context` flag
- **Multiple files**: `"Compare @file1.py to @file2.py and @file3.py"`

Files are automatically read and included as context, making it easy to reference project files without manual copy-paste.

## Guiding Principles

### Directory Structure Principles
Every sub-directory is a vertical slice of functionality, not a horizontal layer.
You can delete or replace any slice without rippling changes across the codebase – ideal for rapid, AI-assisted refactors.  Vertical Slices are recommended for AI-heavy repos because they minimise context size and cross-file hops for coding agents.

### System Principles
*   **Declarative First:** Workflows are defined as data (YAML), making them portable and machine-readable/writable.
*   **Component-Based Architecture:** Built from small, reusable, and well-defined Python components.
*   **Clear Abstractions:** Decouple core logic from specific LLM implementations or tool details.
*   **Human-in-the-Loop by Design:** While aiming for automation, human oversight and intervention are integral, especially for quality and safety.
*   **Iterative Improvement:** The system itself is designed to be improved incrementally, and to facilitate the iterative improvement of the workflows it manages.

## Key Functionality

### 1. Declarative Workflow Definition
   - Workflows are defined in simple YAML files.
   - Each workflow consists of a sequence of "steps" and "agents" or "tools" within those steps.
   - Each agent has its own configuration:
     - System prompt
     - LLM client (e.g., OpenAI, Anthropic, ..., etc.)
     - Model (e.g., `gpt-4.1-mini`)
     - Model parameters (e.g., `temperature`)
     - (Future) Tools it can access

### 2. Workflow Execution
- A command-line interface (CLI) allows users to run defined workflows.
- The system dynamically assembles the workflow logic based on the YAML definition.
- It manages the passage of data (LLM responses) between agents in the sequence.
- Handles interactions with different LLM clients and their specific parameters.

### 3. AI-Powered Workflow Optimization (Elf Agent)
- A specialized "AI Workflow Architect" (Elf) agent can analyze an existing workflow definition.
- The Elf can suggest improvements to an agent's system prompt within a workflow, based on a user-defined goal.
- Available via `elf improve yaml` command with optional custom guidance via `--prompt`.
- Future: Elf will be able to suggest more complex changes like adding/removing steps, changing models, or incorporating new tools.
- This functionality enables a meta-loop where AI helps refine its own operational procedures.

### 4. Interactive Agent Sessions
- Interactive prompt sessions allow real-time conversation with any workflow agent.
- Maintains session state across multiple prompts for contextual conversations.
- Supports the same file reference system (`@filename.ext`) as batch processing.
- Clean exit options and error handling for robust user experience.
