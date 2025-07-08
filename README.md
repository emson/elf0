# 🧝 Elf0 - Build AI Agent Workflows in YAML

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Elf0 is a command line tool I created to help rapidly build and test AI agent workflows. Often you might get a requirement to build an agent to do something and need to experiment with how it works.

For example, you may have an insurance PDF document and want to extract quote information. Sure, you could write a quick prompt and plug it into ChatGPT, but usually the problem is more nuanced and complex, requiring a sophisticated workflow (an agent) to solve it properly.

**Elf0 lets you easily create surprisingly useful agents.**

Start by creating a YAML file that defines your agent workflow, add in the prompts and model settings, and run it as real code. Since your agent specification (_spec_) is defined in YAML, you can easily feed the whole thing into ChatGPT or Claude and get it to improve it.

Defining agents like this is powerful because you can version not only the prompts but the entire logic of the workflow, the model parameters, and the reasoning chains. YAML becomes a great agent abstraction that can be quickly tailored to your specific needs and use cases.

## 🚀 What Can You Build?

### Simple Agents
```bash
# Basic assistant (uses gpt-4.1-mini - cheap but not great at reasoning)
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "How many r's are in strawberry?"

# Better reasoning agent (same model, much better system prompt - gets strawberry right!)
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "How many r's are in strawberry?"

# Prompt optimization - enter a potential prompt and it iterates to improve it
uv run elf0 agent specs/utils/optimizer_prompt_v1.yaml --prompt "Help me write better prompts for code review"
```

### File Analysis with @references
```bash
# Automatically include file contents in your prompts
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Review this code @src/elf0/cli.py and suggest improvements"

# Analyze entire directories  
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Analyze all code in @src/ for improvements"
```

### YouTube Analysis (with MCP servers)
You will first need to install and run the included MCP server (please see [mcp/youtube-transcript/README.md](mcp/youtube-transcript/README.md)).

```bash
# Download and summarize YouTube transcripts
uv run elf0 agent specs/content/youtube_analyzer.yaml --prompt "Analyse this youtube video https://www.youtube.com/watch?v=9tOmppsiO2w"
```

### Interactive Workflows
```bash
# Ask for your name and create a poem about it (calls Python functions)
uv run elf0 agent specs/examples/interactive_assistant.yaml --prompt "Ask me my name and then make a poem about it."
```

### Simulations
```bash
# Create complex multi-agent simulations
uv run elf0 -v agent specs/utils/simulation_scenario_v1.yaml --prompt "Create a salary negotiation simulation. There are 2 people, Ben a plucky young agent engineer and Clive the CEO of a hot up-and-coming software conslutancy based in London. Create a persona for Ben and Clive, and design this YAML spec around how they will interact under different scenarios. We will give the new YAML file you output the scenarios." --output simulate_salary.yaml

# Then run scenarios with your new simulation
uv run elf0 agent simulate_salary.yaml --prompt "Ben is negotiating a new job with Clive, Ben has to commute from Edinburgh 4 days a month. Work through the negotiation step by step."
```

**Pulling all this together, you have a very powerful and useful "agent toolkit" to explore ideas and get stuff done.**

## ⚡ Quick Start (5 minutes)

> ⚠️ **Be careful!** Elf0 can execute code and access your files. Only run workflows you trust.

### 1. Install Python 3.13+ and uv
- **Python 3.13+**: [Download here](https://python.org/downloads/)
- **uv package manager**: Fast Python package manager - [Install guide](https://docs.astral.sh/uv/getting-started/installation/)

### 2. Install Elf0
```bash
git clone https://github.com/emson/elf0.git
cd elf0
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

### 3. Get an API key
Choose one:
- **OpenAI**: [Get key](https://platform.openai.com/api-keys) → `export OPENAI_API_KEY="your-key"`
- **Anthropic**: [Get key](https://console.anthropic.com/) → `export ANTHROPIC_API_KEY="your-key"`  
- **Ollama**: [Install locally](https://ollama.ai/) → `ollama pull llama2` (no key needed)

### 4. Try it out!
```bash
# Test basic chat
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Write a haiku about programming"

# Test file analysis
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "What does this code do? @src/elf0/cli.py"

# Test the strawberry reasoning challenge
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "How many r's are in strawberry?"
```

**🎉 It works!** You should see AI-generated responses. The reasoning agent actually gets the strawberry question right! 

## 🔒 Security Note

**Elf0 can execute code, read files, and make network requests.** It's experimental software - be careful what you run.

**What workflows can do:**
- Read any file you can access
- Execute Python functions and MCP servers  
- Send your data to LLM providers
- Write/modify files

**Stay safe:**
- Only run workflows you trust
- Review YAML files before running (`cat workflow.yaml`)
- Use test API keys, not production ones
- Back up important work first
- Start with simple examples in `specs/basic/`

**Red flags - never run workflows that:**
- Come from unknown sources
- Use `os.system()` or `subprocess`
- Access sensitive directories (`~/.ssh`, `/etc`)
- Request elevated permissions

The `@file.txt` syntax sends file contents to LLM providers, so be mindful of sensitive data.

## 🧠 How Elf0 Works

### YAML as Agent Abstraction

Here's what a simple agent looks like:

```yaml
# specs/basic/chat_simple_v1.yaml
version: "0.1"
description: "Simple AI assistant"
runtime: "langgraph"

llms:
  assistant:
    type: openai
    model_name: gpt-4.1-mini
    temperature: 0.7

workflow:
  type: sequential
  nodes:
    - id: chat_step
      kind: agent
      ref: assistant
      config:
        prompt: |
          You are a helpful AI assistant. 
          User request: {input}
      stop: true
```

**What this does:**
1. Defines an LLM (OpenAI's cheap but fast model)
2. Creates a workflow with one step
3. Sets up the prompt with user input
4. Runs when you execute: `uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Hello"`

### The Magic of `@file.md` and `@my/dir` References

Instead of copy-pasting file contents, just use `@filename`:

```bash
# This automatically reads README.md and includes it in the prompt
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Summarize @README.md"

# Works with any file type
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "Find bugs in @app.py"

# Even entire directories
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Analyze the code quality in @src/"
```

This is incredibly useful for code review, documentation, and analysis tasks.

## 🛠️ Cool Things You Can Do

### Workflow Self-Improvement

Don't like a workflow? Get AI to improve it:

```bash
# AI analyzes and improves any workflow
uv run elf0 improve yaml specs/basic/chat_simple_v1.yaml

# Or use the dedicated optimizer
uv run elf0 agent specs/utils/optimizer_yaml_v1.yaml --prompt "Improve this workflow @specs/basic/chat_simple_v1.yaml"

# You can even feed the result back into ChatGPT for more improvements
```

### Interactive Mode

Have conversations with any workflow (in verbose mode `-v`):

```bash
uv run elf0 -v prompt specs/basic/chat_simple_v1.yaml
💬 Prompt: Help me debug this code @app.py
💬 Prompt: Now write unit tests for it
💬 Prompt: /exit
```

### Multi-Agent Workflows

Create sophisticated multi-step processes:

```yaml
# Example: Code review workflow
workflow:
  type: sequential
  nodes:
    - id: analyze_code
      kind: agent
      ref: fast_model
      config:
        prompt: "Analyze this code for issues: {input}"
    
    - id: detailed_review
      kind: agent  
      ref: smart_model
      config:
        prompt: |
          Based on this analysis: {state.output}
          Provide detailed code review with suggestions.
```

### Advanced Examples

```bash
# Create new workflows using AI
uv run elf0 agent specs/utils/agent_creator.yaml --prompt "Create a workflow for API testing"

# Process YouTube videos (requires MCP server setup)
uv run elf0 agent specs/content/youtube_analyzer.yaml --prompt "Analyze this video https://youtube.com/watch?v=example"

# Generate simulations
uv run elf0 agent specs/utils/simulation_scenario_v1.yaml --prompt "Create a customer service training simulation" --output customer_sim.yaml
```

## 📋 Command Reference

### Basic Commands

```bash
# Run a workflow
uv run elf0 agent <workflow.yaml> --prompt "Your prompt here"

# Interactive mode
uv run elf0 prompt <workflow.yaml>

# Improve a workflow with AI
uv run elf0 improve yaml <workflow.yaml>

# List available workflows
uv run elf0 list-specs

# Verbose mode (see what's happening)
uv run elf0 --verbose agent <workflow.yaml> --prompt "Debug mode"
```

### Useful Options

```bash
# Save output to file
--output filename.txt

# Include additional files as context
--context file1.txt --context file2.csv

# Use @file.ext syntax anywhere in prompts
--prompt "Analyze @data.csv and @config.yaml"

# Interactive mode commands
💬 Prompt: /send          # Send current message
💬 Prompt: /exit          # Exit session
💬 Prompt: @file.txt help # Include file in message
```

### Examples

```bash
# Code review
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "Review @app.py for security issues"

# Content generation
uv run elf0 agent specs/content/linkedin_post.yaml --prompt "Write about AI trends" --output post.md

# Interactive debugging
uv run elf0 prompt specs/basic/chat_simple_v1.yaml
💬 Prompt: Help me debug @buggy_code.py
💬 Prompt: Now write tests for the fixed version
```

## 🧠 Understanding Workflows

Think of workflows like cooking recipes - a series of steps that transform your input into the desired output.

**Basic structure:**
1. **Input**: Your prompt or question
2. **LLM models**: Define which AI models to use (OpenAI, Anthropic, Ollama)
3. **Workflow nodes**: The processing steps (agents, tools, functions)
4. **Output**: The final result

**Node types:**
- **agent**: AI model that processes text
- **tool**: Python function for custom logic  
- **mcp**: External tool via Model Context Protocol

**Flow types:**
- **sequential**: Steps run one after another (most common)
- **custom_graph**: Complex routing with conditionals and parallel processing

```yaml
# Minimal workflow example
version: "0.1"
runtime: "langgraph"

llms:
  my_ai:
    type: openai
    model_name: gpt-4.1-mini

workflow:
  type: sequential
  nodes:
    - id: process
      kind: agent
      ref: my_ai
      config:
        prompt: "Help with: {input}"
      stop: true
```

## 💡 Quick Examples by Use Case
You can list the YAML workflows in the `specs` directory (and filter the subdirectories) with:
```bash
# list all specs (ignoring archive)
uv run elf0 list-specs

# List a specific directory
uv run elf0 list-specs content
```

### Content Creation
```bash
# Blog posts and articles
uv run elf0 agent specs/content/content_basic_v1.yaml --prompt "Write about AI trends in 2024"

# Social media
uv run elf0 agent specs/content/linkedin_post.yaml --prompt "Post about remote work benefits"
uv run elf0 agent specs/content/twitter_post.yaml --prompt "Tweet about machine learning"

# Documentation
uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Document this API @api.py"
```

### Code Analysis
```bash
# Code review with the reasoning agent (much better than basic chat)
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "Review @app.py for bugs and improvements"

# Security check
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "Find security issues in @auth.py"

# Compare files
uv run elf0 agent specs/basic/reasoning_structured_v1.yaml --prompt "Compare @old_version.py and @new_version.py"
```

### Claude Code Integration
Elf0 includes powerful integration with the Claude Code SDK, providing AI-assisted development through Claude's advanced code understanding and generation capabilities:

```bash
# Deep code analysis with Claude Code
uv run elf0 agent specs/code/claude_code_review.yaml --prompt "Analyse the following file and tell me how to improve it @src/elf0/cli.py"

# Generate code with Claude Code
uv run elf0 agent specs/examples/claude_code_example.yaml --prompt "Create a FastAPI application with user authentication"

# Get architectural guidance
uv run elf0 agent specs/code/claude_code_review.yaml --prompt "Review @src/ and suggest architectural improvements"
```

**Why use Claude Code?** Claude Code provides AI-assisted development through a Python SDK, enabling streamlined interaction with Claude for code-related tasks. It offers tool-based workflows like file reading/writing, automated development tasks, and comprehensive error handling - perfect for integrating AI assistance directly into your development process.

### Workflow Management
```bash
# Create new workflows with AI
uv run elf0 agent specs/utils/agent_creator.yaml --prompt "Create a workflow for API testing"

# Improve existing ones
uv run elf0 improve yaml specs/basic/chat_simple_v1.yaml --prompt "Make it better for code review"

# Generate simulations
uv run elf0 agent specs/utils/simulation_scenario_v1.yaml --prompt "Create a customer support simulation" --output support_sim.yaml
```

## 🚀 Advanced Features

### Python Functions
Add custom logic to workflows:

```python
# Create custom functions
def my_processor(state, operation="uppercase"):
    text = state.get("output", "")
    if operation == "uppercase":
        result = text.upper()
    return {"output": f"Processed: {result}"}
```

### MCP Servers
Connect to external tools. For example, the YouTube transcript server:

```bash
# First install and start the MCP server (see mcp/youtube-transcript/README.md)
uv pip install youtube-transcript-api

# Then use it in workflows
uv run elf0 agent specs/content/youtube_analyzer.yaml --prompt "Analyze this video https://youtube.com/watch?v=example"
```

### Multiple AI Models
Use different models for different tasks:

```yaml
llms:
  fast_model:      # Quick and cheap
    type: openai
    model_name: gpt-4.1-mini
    
  smart_model:     # Powerful reasoning
    type: anthropic
    model_name: claude-sonnet-4
    
  local_model:     # Private and free
    type: ollama
    model_name: llama3

workflow:
  nodes:
    - id: draft
      ref: fast_model    # Quick first pass
    - id: refine  
      ref: smart_model   # Detailed improvement
```

### Want More?
```bash
# See all available workflows
uv run elf0 list-specs

# Explore examples and utilities
ls specs/examples/
ls specs/utils/

# Create your own workflow
uv run elf0 agent specs/utils/agent_creator.yaml --prompt "Create a workflow for my specific use case"
```

## 🛠️ Troubleshooting

### Common Issues

**"Command not found: elf"**
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate
uv pip install -e .
```

**"API key not found"**
```bash
# Check your environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set them if missing
export OPENAI_API_KEY="your-key-here"
```

**"Module not found" errors**
```bash
# Reinstall in development mode
uv pip install -e .
```

**Workflow not working as expected**
```bash
# Use verbose mode to see what's happening
uv run elf0 --verbose agent workflow.yaml --prompt "debug"

# Review the YAML file
cat workflow.yaml
```

## 🤝 Contributing & Support

**Want to help?**
- Report bugs or suggest features: [GitHub Issues](https://github.com/emson/elf0/issues)
- Share your workflows: Submit a PR with your useful specs
- Improve docs: Found something unclear? Please fix it!

**Development setup:**
```bash
git clone https://github.com/emson/elf0.git
cd elf0
uv venv && source .venv/bin/activate
uv pip install -e .
pytest  # Run tests
```

## 📄 License

Apache License 2.0 - Use freely, even commercially. See [LICENSE](LICENSE) file.

**Disclaimer**: This is experimental software. Use with caution, especially in production environments. You're responsible for reviewing workflows before running them.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- Uses [uv](https://github.com/astral-sh/uv) by Astral for fast Python package management  
- Supports [MCP](https://modelcontextprotocol.io/) for tool integration
- Inspired by agentic workflow patterns

---

**Ready to build your first AI workflow?** Start with the [Quick Start](#-quick-start-5-minutes) section! 🚀

I hope you love using Elf0 as much as I enjoyed building it.
