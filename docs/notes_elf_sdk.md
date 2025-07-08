# Elf0 SDK Design Notes

## Current State Analysis

Elf0 is currently a CLI-first application with a well-structured core that can be transformed into a programmable Python SDK. The existing architecture provides:

- **Core workflow engine** (`src/elf0/core/`) - LangGraph compilation, LLM clients, spec loading
- **CLI interface** (`src/elf0/cli.py`) - Command-line wrapper around core functionality
- **YAML workflow specifications** (`specs/`) - Declarative workflow definitions
- **Rich integrations** - OpenAI, Anthropic, Ollama, MCP, Claude Code SDK

## SDK Conversion Goals

Transform Elf0 into a **dual-purpose package**:
1. **Python SDK** for embedding AI workflows in applications
2. **CLI tool** (existing functionality preserved)

### Design Principles
- **Minimal core changes** - Leverage existing robust architecture
- **Backward compatibility** - All CLI commands continue working
- **Progressive enhancement** - Gradual adoption path from CLI to SDK
- **Clean separation** - SDK layer wraps core, CLI becomes SDK consumer

## Proposed Architecture

### New SDK Module Structure
```
src/elf0/
├── __init__.py           # Main SDK exports and version
├── sdk/                  # New SDK interface layer
│   ├── __init__.py       # SDK exports
│   ├── workflow.py       # Primary Workflow class
│   ├── client.py         # Session management and high-level API
│   ├── builder.py        # Programmatic workflow construction
│   ├── config.py         # SDK configuration management
│   └── integrations/     # Framework-specific helpers
│       ├── __init__.py
│       ├── fastapi.py    # FastAPI middleware
│       ├── django.py     # Django integration
│       └── jupyter.py    # Jupyter notebook helpers
├── core/                 # Existing engine (minimal changes)
│   ├── compiler.py       # Workflow → LangGraph compiler
│   ├── spec.py           # YAML spec models
│   ├── runner.py         # Low-level execution
│   ├── config.py         # Enhanced with SDK support
│   └── ...
├── cli.py               # Refactored to use SDK internally
└── utils/               # Existing utilities
```

## SDK Public API Design

### 1. Primary Workflow Class

```python
from elf0 import ElfWorkflow

# Load from YAML
workflow = ElfWorkflow.from_yaml("path/to/workflow.yaml")
result = workflow.run("Your prompt here", session_id="my_session")

# Load from dict/spec
spec_dict = {"name": "my_workflow", "llms": {...}, "workflow": {...}}
workflow = ElfWorkflow.from_dict(spec_dict)

# Access workflow metadata
print(workflow.name)
print(workflow.description)
print(workflow.tags)
```

### 2. Client-Based API (Session Management)

```python
from elf0 import ElfClient

# Create client with configuration
client = ElfClient(
    openai_api_key="sk-...",
    anthropic_api_key="sk-ant-...",
    default_session_id="app_session"
)

# Run workflows
result = client.run_workflow(
    "specs/basic/chat_simple_v1.yaml", 
    "Hello, world!",
    session_id="user_123"
)

# Manage sessions
client.clear_session("user_123")
client.list_sessions()
```

### 3. Programmatic Workflow Builder

```python
from elf0 import WorkflowBuilder

# Fluent API for creating workflows
workflow = WorkflowBuilder() \
    .name("dynamic_chat") \
    .description("Programmatically created workflow") \
    .add_llm("gpt4", type="openai", model="gpt-4", temperature=0.7) \
    .add_agent_node(
        id="chat", 
        llm="gpt4",
        prompt="You are a helpful assistant. User: {input}"
    ) \
    .set_stop_node("chat") \
    .build()

result = workflow.run("What's the weather like?")
```

### 4. Configuration Management

```python
import elf0

# Global configuration
elf0.configure(
    openai_api_key="sk-...",
    anthropic_api_key="sk-ant-...",
    default_temperature=0.8,
    default_session_id="global"
)

# Per-workflow configuration
workflow.configure(temperature=0.5, max_tokens=1000)

# Environment-based configuration (existing .env support)
elf0.configure_from_env()
```

## Implementation Plan

### Phase 1: Core SDK Foundation

#### 1.1 Create SDK Interface Layer
- **`src/elf0/sdk/workflow.py`** - Main Workflow class wrapping core functionality
- **`src/elf0/sdk/client.py`** - Client with session management and configuration
- **`src/elf0/__init__.py`** - Export main SDK classes and version

```python
# src/elf0/__init__.py
__version__ = "0.1.0"

from .sdk.workflow import ElfWorkflow
from .sdk.client import ElfClient
from .sdk.builder import WorkflowBuilder
from .sdk.config import configure, configure_from_env

__all__ = [
    "ElfWorkflow", 
    "ElfClient", 
    "WorkflowBuilder",
    "configure",
    "configure_from_env"
]
```

#### 1.2 Enhance Core Engine
- **Modify `core/config.py`** - Add programmatic configuration support
- **Update `core/runner.py`** - Support SDK calls with better error handling
- **Add result formatting** - Consistent output format for SDK consumers

#### 1.3 Package Configuration
- **Update `pyproject.toml`** - Add library classifiers, maintain CLI entry point
- **Version management** - Use `__version__` in `__init__.py`

### Phase 2: Advanced SDK Features

#### 2.1 Programmatic Workflow Builder
```python
# src/elf0/sdk/builder.py
class WorkflowBuilder:
    def __init__(self):
        self._spec = {
            "name": "",
            "llms": {},
            "workflow": {"type": "sequential", "nodes": [], "edges": []}
        }
    
    def name(self, name: str) -> "WorkflowBuilder":
        self._spec["name"] = name
        return self
    
    def add_llm(self, id: str, type: str, model: str, **kwargs) -> "WorkflowBuilder":
        self._spec["llms"][id] = {"type": type, "model_name": model, **kwargs}
        return self
    
    def add_agent_node(self, id: str, llm: str, prompt: str, **kwargs) -> "WorkflowBuilder":
        node = {
            "id": id,
            "kind": "agent", 
            "ref": llm,
            "config": {"prompt": prompt},
            **kwargs
        }
        self._spec["workflow"]["nodes"].append(node)
        return self
    
    def build(self) -> "ElfWorkflow":
        return ElfWorkflow.from_dict(self._spec)
```

#### 2.2 Enhanced Session Management
- **Persistent sessions** - Store session state across runs
- **Context management** - Automatic cleanup and resource management
- **Async support** - `async def run_async()` methods

### Phase 3: CLI as SDK Consumer

#### 3.1 Refactor CLI to Use SDK
```python
# Modified src/elf0/cli.py
from elf0 import ElfClient

def agent_command(spec_path: Path, prompt: str, session_id: str, ...):
    """Execute an agent workflow - now using SDK internally."""
    client = ElfClient()
    
    try:
        result = client.run_workflow(spec_path, prompt, session_id)
        display_workflow_result(result)
    except Exception as e:
        # Enhanced error handling
        handle_sdk_error(e)
```

## Usage Examples

### 1. Web Application Integration

```python
from flask import Flask, request, jsonify
from elf0 import ElfClient

app = Flask(__name__)
elf_client = ElfClient()

@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    data = request.json
    prompt = data['prompt']
    session_id = data.get('session_id', f"web_{request.remote_addr}")
    
    try:
        result = elf_client.run_workflow(
            "specs/basic/chat_simple_v1.yaml",
            prompt,
            session_id=session_id
        )
        return jsonify({
            'success': True,
            'response': result['output'],
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ai/sessions/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    elf_client.clear_session(session_id)
    return jsonify({'success': True})
```

### 2. Jupyter Notebook Integration

```python
# In a Jupyter cell
from elf0 import ElfWorkflow
import IPython.display as display

workflow = ElfWorkflow.from_yaml("specs/content/content_basic_v1.yaml")

# Interactive widget for workflow execution
def run_content_generator(prompt):
    result = workflow.run(prompt, session_id="notebook")
    display.Markdown(result['output'])

# Use with ipywidgets
import ipywidgets as widgets
prompt_widget = widgets.Text(placeholder="Enter your content prompt...")
output_widget = widgets.Output()

def on_submit(change):
    with output_widget:
        output_widget.clear_output()
        run_content_generator(prompt_widget.value)

prompt_widget.observe(on_submit, names='value')
display.VBox([prompt_widget, output_widget])
```

### 3. Batch Processing

```python
from elf0 import ElfWorkflow
import asyncio
from concurrent.futures import ThreadPoolExecutor

workflow = ElfWorkflow.from_yaml("specs/content/linkedin_post.yaml")

def process_single(prompt):
    return workflow.run(prompt, session_id=f"batch_{id(prompt)}")

async def process_batch(prompts, max_workers=5):
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, process_single, prompt)
            for prompt in prompts
        ]
        results = await asyncio.gather(*tasks)
    
    return results

# Usage
prompts = [
    "Write about AI in healthcare",
    "Write about renewable energy", 
    "Write about remote work trends"
]

results = asyncio.run(process_batch(prompts))
for i, result in enumerate(results):
    print(f"Result {i+1}: {result['output'][:100]}...")
```

### 4. Dynamic Workflow Creation

```python
from elf0 import WorkflowBuilder

def create_analysis_workflow(model_type="openai", complexity="basic"):
    builder = WorkflowBuilder() \
        .name(f"{complexity}_analysis") \
        .description(f"Dynamic {complexity} analysis workflow")
    
    # Add appropriate LLM based on complexity
    if complexity == "basic":
        builder.add_llm("analyzer", type=model_type, model="gpt-4o-mini", temperature=0.3)
    else:
        builder.add_llm("analyzer", type=model_type, model="gpt-4", temperature=0.5)
    
    # Build analysis chain
    builder.add_agent_node(
        id="analyze",
        llm="analyzer", 
        prompt=f"Perform {complexity} analysis of: {{input}}"
    ).set_stop_node("analyze")
    
    return builder.build()

# Create different workflows for different use cases
basic_analyzer = create_analysis_workflow("openai", "basic")
advanced_analyzer = create_analysis_workflow("anthropic", "advanced")

# Use them
basic_result = basic_analyzer.run("Analyze this simple dataset")
advanced_result = advanced_analyzer.run("Perform deep analysis of market trends")
```

## Migration Strategy

### Backward Compatibility
- **All CLI commands work unchanged** - `uv run elf0 agent workflow.yaml --prompt "..."`
- **YAML workflow format preserved** - Existing specs continue working
- **Environment variables supported** - `.env` files and `export` commands

### Gradual Adoption Path
1. **Install**: Same package (`pip install elf0` or `uv pip install elf0`)
2. **Use CLI**: Continue using CLI as before
3. **Import SDK**: Start with `from elf0 import ElfWorkflow`
4. **Migrate incrementally**: Replace CLI subprocess calls with SDK calls

### Breaking Changes (None in Phase 1)
- No breaking changes to existing functionality
- CLI remains primary interface initially
- SDK additive, not replacement

## Testing Strategy

### Unit Tests
- SDK classes and methods
- Configuration management
- Workflow builder validation
- Error handling and edge cases

### Integration Tests
- SDK + LLM providers (OpenAI, Anthropic, Ollama)
- SDK + MCP servers
- SDK + Claude Code integration
- Session management across multiple workflows

### Compatibility Tests
- CLI commands still work after SDK implementation
- YAML workflow specs continue functioning
- Environment variable configuration preserved

### Example Tests
```python
# tests/sdk/test_workflow.py
import pytest
from elf0 import ElfWorkflow

def test_workflow_from_yaml():
    workflow = ElfWorkflow.from_yaml("tests/fixtures/simple_chat.yaml")
    assert workflow.name == "simple_chat"
    
def test_workflow_run():
    workflow = ElfWorkflow.from_yaml("tests/fixtures/simple_chat.yaml")
    result = workflow.run("Hello", session_id="test")
    assert "output" in result
    assert isinstance(result["output"], str)
```

## Package Configuration Updates

### pyproject.toml Changes
```toml
[project]
name = "elf0"
description = "AI workflow engine and SDK for building agent-powered applications"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",  # SDK
    "Topic :: System :: Systems Administration",                     # CLI
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

# Maintain CLI entry point
[project.scripts]
elf0 = "elf0.cli:app"

# Optional dependencies for integrations
[project.optional-dependencies]
web = ["fastapi>=0.104.0", "uvicorn>=0.24.0"]
django = ["django>=4.2.0"]
jupyter = ["ipywidgets>=8.0.0", "jupyter>=1.0.0"]
all = ["elf0[web,django,jupyter]"]
```

## Documentation Structure

### SDK Documentation
- **API Reference** - Auto-generated from docstrings
- **Quickstart Guide** - Basic SDK usage
- **Integration Examples** - Flask, Django, FastAPI, Jupyter
- **Migration Guide** - CLI to SDK transition

### Enhanced CLI Documentation
- **Existing CLI docs** - Preserved and enhanced
- **SDK Integration** - How to use SDK alongside CLI
- **Best Practices** - When to use CLI vs SDK

## Benefits of This Approach

### For Developers
- **Embed AI workflows** in existing applications
- **Programmatic control** over workflow execution
- **Session management** for user interactions
- **Dynamic workflow creation** based on runtime conditions

### For Organizations
- **Integration flexibility** - Works with existing tech stacks
- **Gradual adoption** - No need to rewrite existing CLI usage
- **Scalable architecture** - SDK supports high-throughput applications
- **Consistent interface** - Same underlying engine for CLI and SDK

### For the Elf0 Project
- **Broader adoption** - Appeals to both CLI users and Python developers
- **Ecosystem growth** - Enables third-party integrations and extensions
- **Maintainability** - Single codebase for both CLI and SDK
- **Future-proof** - Foundation for advanced features (web UI, cloud deployment)

This design transforms Elf0 from a CLI tool into a comprehensive AI workflow platform while preserving everything that makes it powerful today.