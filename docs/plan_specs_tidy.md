# Specs Directory Reorganisation Plan

## Executive Summary

This plan outlines a comprehensive reorganisation of the elf0 workflow specifications directory that preserves all existing work whilst creating a curated, well-organized structure. The approach transforms 38 inconsistently named workflows into a logical directory system with 15-18 active workflows and full preservation of all existing work in an archive.

**Key changes:**
- **Zero-loss migration:** All 38 existing workflows preserved in `archive/` directory
- **Logical structure:** Four focused directories (`basic/`, `content/`, `code/`, `examples/`)
- **Consistent naming:** Restored `{subcategory}_{context}_{version}.yaml` pattern
- **Simplified CLI:** Minimal `elf0 list-specs [directory]` filtering approach
- **Quality framework:** Standardization approach for prompt engineering and metadata
- **Future-ready:** Lean, flexible architecture supporting continuous improvement

## Current State Analysis

### File Locations

**Main `/specs/` directory (18 files):**
- `src/elf0/specs/basic_chat.yaml`
- `src/elf0/specs/basic_reasoning-01.yaml`
- `src/elf0/specs/basic_reasoning-02.yaml`
- `src/elf0/specs/agent-twitter-01.yaml`
- `src/elf0/specs/agent-twitter-01_improved.yaml`
- `src/elf0/specs/agent-linkedin-01.yaml`
- `src/elf0/specs/youtube_analyzer.yaml`
- `src/elf0/specs/prompt_optimizer.yaml`
- `src/elf0/specs/agent-tech_doc_creator.yaml`
- `src/elf0/specs/agent-creator-01.yaml`
- `src/elf0/specs/agent-creator-02.yaml`
- `src/elf0/specs/agent-simulation.yaml`
- `src/elf0/specs/agent-optimizer.yaml`

**Examples subdirectory `/specs/examples/` (16 files):**
- `src/elf0/specs/examples/claude_code_example.yaml`
- `src/elf0/specs/examples/claude_code_self_improvement.yaml`
- `src/elf0/specs/examples/claude_sonnet_example.yaml`
- `src/elf0/specs/examples/interactive_assistant.yaml`
- `src/elf0/specs/examples/mcp_workflow.yaml`
- `src/elf0/specs/examples/ollama_chat.yaml`
- `src/elf0/specs/examples/ollama_coder.yaml`
- `src/elf0/specs/examples/ollama_optimizer.yaml`
- `src/elf0/specs/examples/orchestration_workers.yaml`
- `src/elf0/specs/examples/prompt_chaining.yaml`
- `src/elf0/specs/examples/prompt_routing.yaml`
- `src/elf0/specs/examples/prompt_routing_with_reference.yaml`
- `src/elf0/specs/examples/python_calculator.yaml`
- `src/elf0/specs/examples/python_function_test.yaml`
- `src/elf0/specs/examples/python_text_processor.yaml`
- `src/elf0/specs/examples/simple_mcp.yaml`

### Technical Architecture Analysis

**Workflow Types Supported:**
- `sequential` - Linear execution flow
- `react` - Reasoning and acting pattern
- `evaluator_optimizer` - Iterative improvement cycles
- `custom_graph` - Complex conditional workflows

**Node Types Available:**
- `agent` - LLM-powered reasoning nodes
- `tool` - External function calls
- `judge` - Evaluation and scoring nodes
- `branch` - Conditional routing nodes
- `mcp` - Model Context Protocol integrations
- `claude_code` - Code generation nodes

**LLM Integrations:**
- OpenAI (GPT-4, GPT-4.1-mini, O3)
- Anthropic (Claude Sonnet 4, Claude Haiku)
- Ollama (Local models)

**Current Workflow Complexity Distribution:**
- Level 1 (Basic): 6 workflows
- Level 2 (Structured): 8 workflows
- Level 3 (Advanced): 12 workflows
- Level 4 (Complex): 8 workflows
- Level 5 (Expert): 4 workflows

## Problems Identified

### 1. Inconsistent Naming Conventions
- Mixed prefixes: `basic_`, `agent-`, no prefix
- Inconsistent versioning: `-01`, `-02`, `_improved`
- No clear category indication in filenames

### 2. Poor Organisation Structure
- Flat directory structure makes discovery difficult
- `/examples/` subdirectory contains production-ready workflows
- No clear progression path for users

### 3. Missing Business Value
- Lack of practical business automation workflows
- Limited entrepreneurial use cases
- No clear ROI demonstration

### 4. Quality Inconsistencies
- Inconsistent metadata standards
- Variable prompt quality
- Missing documentation within workflows

### 5. User Experience Issues
- No clear entry points for new users
- Difficult to find appropriate workflows for specific needs
- No guidance on workflow progression

## Proposed Solution

### 1. Enhanced Directory Structure

Organized by use case with clear progression paths:

```
specs/
├── basic/                  # Entry-level workflows (3-4 files)
│   ├── chat_simple_v1.yaml
│   ├── reasoning_structured_v1.yaml
│   └── content_basic_v1.yaml
├── content/                # Content creation & analysis (4-5 files)
│   ├── social_twitter_v2.yaml
│   ├── social_linkedin_v1.yaml
│   ├── analysis_youtube_v1.yaml
│   └── documentation_technical_v1.yaml
├── code/                   # Code generation & analysis (3-4 files)
│   ├── generator_python_v1.yaml
│   ├── analyzer_review_v1.yaml
│   └── integration_claude_code_v1.yaml
├── examples/               # Advanced patterns & integrations (4-5 files)
│   ├── automation_prompt_optimizer_v1.yaml
│   ├── orchestration_workers_v1.yaml
│   ├── integration_mcp_calculator_v1.yaml
│   └── workflow_chaining_v1.yaml
└── archive/                # All existing workflows preserved
    ├── agent-twitter-01.yaml
    ├── basic_reasoning-02.yaml
    ├── agent-creator-01.yaml
    └── [... all 38 current files]
```

**Total: ~15-18 active files + 38 archived files**

### 2. Naming Convention

**Structure:** `{subcategory}_{context}_{version}.yaml`

**Examples:**
- `social_twitter_v2.yaml` - Twitter/thread generator
- `integration_mcp_calculator_v1.yaml` - MCP calculator integration
- `generator_python_v1.yaml` - Python code generation workflow
- `automation_prompt_optimizer_v1.yaml` - Prompt optimization workflow

**Rationale:** Consistent naming enables:
- **Clear categorization** - Subcategory prefix indicates workflow type
- **Version management** - Explicit versioning supports iterative improvement
- **Predictable discovery** - Pattern-based naming aids CLI filtering
- **Future-proofing** - Structure accommodates expansion

### 3. Essential Metadata Standards

Every workflow must include:

```yaml
version: "0.1"
description: "Clear, concise description of purpose and use case"
runtime: "langgraph"
# Optional metadata for enhanced discovery:
tags: ["content", "automation", "analysis"]  # For filtering
complexity: "basic|intermediate|advanced"    # For user progression
```

**Rationale:** Minimal required metadata reduces maintenance overhead whilst supporting essential discovery features.

### 4. Minimal CLI Design

**Current `list-specs` command:**
- Scans only root `./specs` directory
- No filtering capabilities

**Enhanced design philosophy:**
- **Default to all** - Show all specs across directories by default
- **Simple filtering** - Optional directory name as argument
- **Minimal complexity** - Single parameter, intuitive usage

**Proposed CLI signature:**
```bash
elf0 list-specs [directory]
```

**Usage examples:**
```bash
elf0 list-specs              # Show all specs (default)
elf0 list-specs basic        # Show only basic/ directory
elf0 list-specs content      # Show only content/ directory  
elf0 list-specs code         # Show only code/ directory
elf0 list-specs archive      # Show archived workflows
```

**Implementation approach:**
- Single optional positional argument
- Directory validation with helpful error messages
- Consistent output formatting across all directories

## Priority-Based Implementation Plan

### Priority 1: Core Structure (Immediate)

**Goals:** Establish basic organisation without breaking existing functionality

**Tasks:**
1. **Audit and consolidate** - Identify the 12-15 most valuable workflows from current 38
2. **Create directory structure** - Establish `basic/`, `content/`, `examples/` folders
3. **Initial migration** - Move and rename selected workflows
4. **Update CLI** - Modify `list-specs` to support subdirectories

**Outcome:** Functional organised structure with reduced file count

### Priority 2: CLI Enhancement (Next)

**Goals:** Improve workflow discovery and filtering

**Tasks:**
1. **Enhance list-specs command** - Add category filtering (`--category basic|content|examples|all`)
2. **Update file discovery** - Modify `list_spec_files()` for recursive scanning
3. **Test integration** - Ensure pytest tests continue to pass
4. **Documentation updates** - Update CLI help and examples

**Outcome:** Enhanced discovery through CLI filtering

### Priority 3: Quality Standardisation (Then)

**Goals:** Consistent metadata and prompt quality

**Tasks:**
1. **Standardise metadata** - Apply essential metadata to all workflows
2. **Improve prompts** - Enhance prompt engineering for consistency
3. **Add quality checks** - Implement validation for required fields
4. **Documentation** - Create README for each category

**Outcome:** Professional, consistent workflow library

### Priority 4: Gradual Expansion (Later)

**Goals:** Add new workflows based on user needs

**Tasks:**
1. **Monitor usage patterns** - Identify gaps in workflow coverage
2. **Create missing workflows** - Develop high-value business automations
3. **Community guidelines** - Enable external contributions
4. **Advanced features** - Add versioning, tagging, search functionality

**Outcome:** Comprehensive workflow ecosystem

## File Migration Strategy

### Preserve All Workflows - Zero Loss Approach

**Archive Directory:**
All 38 existing workflows moved to `archive/` directory unchanged:
- Preserves all existing work and investment
- Enables reference and potential future promotion
- Maintains backwards compatibility for any external references
- No workflow is lost or deleted

### Curated Active Workflows (15-18 total)

**Basic Category (3 files):**
- `basic_chat.yaml` → `basic/chat_simple_v1.yaml`
- `basic_reasoning-01.yaml` → `basic/reasoning_structured_v1.yaml`
- NEW: `basic/content_basic_v1.yaml` (simplified content creation)

**Content Category (4 files):**
- `agent-twitter-01_improved.yaml` → `content/social_twitter_v2.yaml`
- `agent-linkedin-01.yaml` → `content/social_linkedin_v1.yaml`
- `youtube_analyzer.yaml` → `content/analysis_youtube_v1.yaml`
- `agent-tech_doc_creator.yaml` → `content/documentation_technical_v1.yaml`

**Code Category (3 files):**
- `examples/ollama_coder.yaml` → `code/generator_python_v1.yaml`
- NEW: `code/analyzer_review_v1.yaml` (code analysis and review)
- `examples/claude_code_example.yaml` → `code/integration_claude_code_v1.yaml`

**Examples Category (5 files):**
- `prompt_optimizer.yaml` → `examples/automation_prompt_optimizer_v1.yaml`
- `examples/orchestration_workers.yaml` → `examples/orchestration_workers_v1.yaml`
- `examples/mcp_workflow.yaml` → `examples/integration_mcp_calculator_v1.yaml`
- NEW: `examples/workflow_chaining_v1.yaml` (workflow composition patterns)
- NEW: `examples/evaluation_judge_v1.yaml` (evaluation workflow patterns)

**Migration Philosophy:**
- **Curate, don't delete** - Select best examples for active use
- **Preserve everything** - Archive maintains all existing work
- **Enhance selectively** - Improve chosen workflows with standardized metadata
- **Enable discovery** - Clear organization aids workflow discovery

## CLI Technical Requirements

### Required Changes to `src/elf0/cli.py`

**Current `list-specs` command (line 545):**
```python
@app.command("list-specs", help="List all YAML workflow spec files in the ./specs directory.")
def list_specs_command() -> None:
```

**Enhanced `list-specs` command:**
```python
@app.command("list-specs", help="List YAML workflow spec files, optionally filtered by directory.")
def list_specs_command(
    directory: str = typer.Argument(
        None, 
        help="Optional directory filter (basic, content, code, examples, archive). Shows all if not specified."
    )
) -> None:
```

### Required Changes to `src/elf0/utils/file_utils.py`

**Current `list_spec_files()` function (line 139):**
- Only scans root directory
- Ignores subdirectories

**Enhanced function signature:**
```python
def list_spec_files(specs_dir: Path, directory_filter: str | None = None) -> list[Path]:
    """Lists YAML spec files with optional directory filtering.
    
    Args:
        specs_dir: The Path to the specs directory
        directory_filter: None for all directories, or specific subdirectory name
        
    Returns:
        List of Path objects for matching spec files
    """
```

**Implementation approach:**
- If `directory_filter` is None: recursively scan all subdirectories
- If `directory_filter` specified: scan only that subdirectory
- Validate directory exists and provide helpful error messages
- Maintain consistent sorting and output formatting

### Test Considerations

**Existing pytest tests:** Ensure all current tests continue to pass
**New test cases needed:**
- Directory filtering functionality  
- Recursive directory scanning
- Invalid directory handling
- Empty directory handling

## Standardization and Enhancement Strategy

### Prompt Quality Framework

**Current challenges:**
- Inconsistent prompt engineering quality
- Variable output formats
- Missing error handling
- Unclear instructions

**Standardization approach:**
```yaml
# Template for consistent prompt structure
prompt: |
  ROLE: [Clear role definition]
  
  CONTEXT:
  [Relevant context and background]
  
  TASK:
  [Specific, actionable instructions]
  
  CONSTRAINTS:
  - [Clear limitations and boundaries]
  - [Output format requirements]
  
  EXAMPLES:
  [Input/output examples when helpful]
  
  OUTPUT FORMAT:
  [Explicit format specification]
```

### Metadata Standardization

**Required fields for all workflows:**
```yaml
version: "v1"           # Semantic versioning
description: "..."      # One-line purpose description
runtime: "langgraph"    # Target runtime
complexity: "basic"     # basic|intermediate|advanced
category: "content"     # Directory category
subcategory: "social"   # Workflow type
```

**Optional enhancement fields:**
```yaml
tags: ["twitter", "social-media", "content-creation"]
use_cases: ["Marketing campaigns", "Content planning"]
prerequisites: ["Twitter API access"]
estimated_runtime: "30-60 seconds"
example_inputs:
  - "Write a thread about AI safety"
  - "Create tweets for product launch"
```

### Enhancement Methodology

**1. Iterative Improvement Process:**
- Version workflows when making significant changes
- Test with multiple example inputs before promoting
- Document improvement rationale in commit messages
- Maintain backwards compatibility within major versions

**2. Quality Gates:**
- **Syntax validation** - YAML schema compliance
- **Prompt clarity** - Clear, unambiguous instructions
- **Error handling** - Graceful failure modes
- **Output consistency** - Predictable result formats

**3. Best Practice Patterns:**
- **Temperature tuning** - Appropriate creativity levels per use case
- **Model selection** - Optimal LLM choice for task requirements
- **Token management** - Efficient prompt design for cost control
- **Retry logic** - Built-in resilience for API failures

### Future Enhancement Pipeline

**Phase 1: Foundation (Current)**
- Establish directory structure and naming convention
- Migrate core workflows with basic metadata
- Implement CLI filtering functionality

**Phase 2: Quality (Next)**
- Apply prompt standardization template
- Add comprehensive metadata to all workflows
- Implement validation tooling

**Phase 3: Intelligence (Later)**
- Usage analytics to identify improvement opportunities
- Automated prompt optimization suggestions
- Community contribution review process
- Performance benchmarking framework

### Lean Implementation Principles

**Minimal viable changes:**
- Single responsibility - Each workflow does one thing well
- Composability - Workflows can be chained together
- Configurability - Parameters exposed for customization
- Observability - Clear logging and error reporting

**Flexible architecture:**
- Plugin-based enhancement system
- Configuration-driven behavior
- Minimal coupling between components
- Future-proof metadata schema

## Implementation Benefits

### Immediate Benefits
- **Zero workflow loss** - All existing work preserved in archive
- **Clear organization** - Logical directory structure with versioning
- **Improved discovery** - Simple CLI filtering by directory
- **Reduced maintenance** - Focus on curated, high-quality workflows

### Long-term Benefits
- **Quality consistency** - Standardized prompt engineering patterns
- **Version management** - Clear upgrade and iteration paths
- **Community scaling** - Structure supports external contributions
- **Performance optimization** - Framework for continuous improvement

## Conclusion

This enhanced reorganisation plan balances immediate organizational benefits with long-term quality and maintainability goals. By preserving all existing workflows whilst curating a focused active set, we maintain backwards compatibility whilst improving user experience. The standardization framework ensures consistent quality improvements over time, following lean principles that minimize complexity whilst maximizing flexibility.