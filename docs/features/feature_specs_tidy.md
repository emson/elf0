# Feature: Specs Directory Reorganisation

## Overview

This feature implements a comprehensive reorganisation of the elf0 workflow specifications directory. The plan transforms 38 inconsistently named workflows into a logical directory system with 15-18 active workflows whilst preserving all existing work in an archive. Key improvements include zero-loss migration, logical structure with four focused directories, consistent naming convention, simplified CLI filtering, and a quality framework for standardisation.

## Current State Context

The existing system has 38 workflow files split between the main `/specs/` directory (18 files) and `/specs/examples/` subdirectory (16 files). Problems include inconsistent naming conventions, poor organisation, missing business value, quality inconsistencies, and user experience issues. The current CLI only scans the root directory without filtering capabilities.

---

## Section 1: Directory Structure Creation

**Summary:** Establish the new four-directory structure (`basic/`, `content/`, `code/`, `examples/`, `archive/`) with proper organisation for workflow progression and discovery.

### Tasks

- [x] Create `specs/basic/` directory for entry-level workflows (3-4 files)
- [x] Create `specs/content/` directory for content creation & analysis workflows (4-5 files)  
- [x] Create `specs/code/` directory for code generation & analysis workflows (3-4 files)
- [x] Create `specs/examples/` directory for advanced patterns & integrations (4-5 files)
- [x] Create `specs/archive/` directory to preserve all existing workflows unchanged
- [x] Verify directory structure matches the planned layout with appropriate README files for each category

---

## Section 2: Workflow Migration and Archiving

**Summary:** Move all 38 existing workflows to the archive directory unchanged, then create curated active workflows in the new structure using the `{subcategory}_{context}_{version}.yaml` naming convention.

### Archive Migration Tasks

- [x] Copy all 18 files from main `/specs/` directory to `specs/archive/` unchanged
- [x] Copy all 16 files from `/specs/examples/` directory to `specs/archive/` unchanged  
- [x] Verify all 38 workflows are preserved exactly as-is in archive
- [x] Test that archived workflows remain functional and accessible

### Active Workflow Creation Tasks

#### Basic Category
- [x] Migrate `basic_chat.yaml` → `basic/chat_simple_v1.yaml` with updated metadata
- [x] Migrate `basic_reasoning-01.yaml` → `basic/reasoning_structured_v1.yaml` with updated metadata
- [ ] Create new `basic/content_basic_v1.yaml` as simplified content creation workflow

#### Content Category  
- [x] Create new `content/content_basic_v1.yaml` as general content creation workflow
- [ ] Migrate `agent-twitter-01_improved.yaml` → `content/social_twitter_v2.yaml` with updated metadata
- [ ] Migrate `agent-linkedin-01.yaml` → `content/social_linkedin_v1.yaml` with updated metadata
- [ ] Migrate `youtube_analyzer.yaml` → `content/analysis_youtube_v1.yaml` with updated metadata
- [ ] Migrate `agent-tech_doc_creator.yaml` → `content/documentation_technical_v1.yaml` with updated metadata

#### Code Category
- [ ] Migrate `examples/ollama_coder.yaml` → `code/generator_python_v1.yaml` with updated metadata
- [ ] Create new `code/analyzer_review_v1.yaml` for code analysis and review functionality
- [ ] Migrate `examples/claude_code_example.yaml` → `code/integration_claude_code_v1.yaml` with updated metadata

#### Examples Category
- [ ] Migrate `prompt_optimizer.yaml` → `examples/automation_prompt_optimizer_v1.yaml` with updated metadata
- [ ] Migrate `examples/orchestration_workers.yaml` → `examples/orchestration_workers_v1.yaml` with updated metadata  
- [ ] Migrate `examples/mcp_workflow.yaml` → `examples/integration_mcp_calculator_v1.yaml` with updated metadata
- [ ] Create new `examples/workflow_chaining_v1.yaml` for workflow composition patterns
- [ ] Create new `examples/evaluation_judge_v1.yaml` for evaluation workflow patterns

---

## Section 3: CLI Enhancement Implementation

**Summary:** Modify the CLI to support recursive directory scanning and simple filtering with `elf0 list-specs [directory]` syntax, updating both the command interface and underlying file discovery logic.

### CLI Command Updates

- [x] Modify `src/elf0/cli.py` line 545 `list_specs_command()` function signature
- [x] Add optional positional `directory` argument using `typer.Argument()`
- [x] Update help text to reflect new filtering capabilities
- [x] Implement directory validation with helpful error messages for invalid directories
- [x] Ensure consistent output formatting across all directory filters

### File Discovery Updates

- [x] Modify `src/elf0/utils/file_utils.py` `list_spec_files()` function at line 139
- [x] Add `directory_filter: str | None = None` parameter to function signature
- [x] Implement recursive scanning logic when `directory_filter` is None
- [x] Implement single directory scanning when `directory_filter` is specified
- [x] Add directory existence validation and error handling
- [x] Maintain consistent sorting and output formatting
- [x] Update function docstring with new parameter and behavior documentation

### CLI Usage Examples Verification

- [x] Test `elf0 list-specs` shows all specs across all directories
- [x] Test `elf0 list-specs basic` shows only basic/ directory contents
- [x] Test `elf0 list-specs content` shows only content/ directory contents (empty for now)
- [x] Test `elf0 list-specs code` shows only code/ directory contents (empty for now)
- [x] Test `elf0 list-specs examples` shows only examples/ directory contents (empty for now)
- [x] Test `elf0 list-specs archive` shows only archived workflows
- [x] Test error handling for invalid directory names

---

## Section 4: Schema Compliance and Optional Metadata

**Summary:** Ensure all workflows comply with the existing Pydantic schema and optionally add discovery metadata through the eval section for enhanced organisation without breaking existing validation.

### Schema Compliance Tasks

- [x] Ensure `version: "v1"` field is present in all active workflows (existing schema requirement)
- [x] Add clear, concise `description` field to all active workflows (existing optional field)
- [x] Verify `runtime: "langgraph"` field is present in all workflows (existing schema requirement)
- [x] Validate all workflows against existing Pydantic `Spec` model without adding new required fields

### Optional Discovery Metadata (via eval section)

- [x] Add optional discovery metadata in `eval` section for workflows that benefit from it:
  ```yaml
  eval:
    tags: ["content", "social-media", "automation"]
    use_cases: ["Marketing campaigns", "Content planning"]
    prerequisites: ["Basic understanding of social media"]
    estimated_runtime: "30-60 seconds"
  ```
- [ ] Keep all discovery metadata optional to maintain backwards compatibility
- [ ] Use directory structure for primary categorisation instead of metadata fields

### Schema Validation

- [ ] Verify all migrated workflows validate against existing Pydantic `Spec` model
- [ ] Test that no existing workflows are broken by migrations
- [ ] Ensure CLI and file discovery work with existing schema structure

---

## Section 5: Testing and Validation

**Summary:** Ensure all existing pytest tests continue to pass whilst adding new test coverage for directory filtering, recursive scanning, and metadata validation functionality.

### Existing Test Compatibility

- [ ] Run full pytest test suite to verify no regressions
- [ ] Fix any broken tests due to file location changes
- [ ] Update test file paths to reference new directory structure
- [ ] Verify workflow functionality remains intact after migration

### New Test Cases

- [ ] Add test for CLI `list-specs` command with no directory argument (shows all specs)
- [ ] Add test for CLI `list-specs` command with valid directory argument (shows filtered specs)
- [ ] Add test for CLI `list-specs` command with invalid directory argument (returns helpful error)
- [ ] Add test for `list_spec_files()` function with recursive directory scanning

### Validation Testing

- [ ] Test all migrated workflows execute successfully in new locations
- [ ] Validate metadata consistency across all active workflows
- [ ] Test CLI functionality with various directory filter combinations
- [ ] Verify error messages are helpful and user-friendly

---

## Section 6: Documentation Updates

**Summary:** Create comprehensive documentation for the new structure including a single well-structured specs README, updated CLI help, and migration guides for users.

### Comprehensive Documentation

- [ ] Create `specs/README.md` with clear, structured documentation including:
  - Overview of the workflow directory structure and organization
  - Directory-by-directory explanation (basic/, content/, code/, examples/, archive/)
  - Progression path from entry-level to advanced workflows
  - Usage instructions with CLI examples (`elf0 list-specs`, `elf0 agent`)
  - Naming convention explanation with examples
  - How to find the right workflow for specific use cases
  - Archive access instructions for legacy workflows

### CLI Documentation Updates

- [ ] Update CLI help text for `list-specs` command with new filtering options
- [ ] Add usage examples to command help documentation
- [ ] Update any references to old workflow paths in help text
- [ ] Ensure error messages provide clear guidance for users

### User Migration Guide

- [ ] Create migration guide explaining new directory structure
- [ ] Document how to find equivalent workflows in new structure
- [ ] Provide examples of using new CLI filtering capabilities
- [ ] Explain archive access for legacy workflow usage

---

## Success Criteria

### Immediate Validation
- [ ] All 38 existing workflows preserved unchanged in archive directory
- [ ] 15-18 curated active workflows properly organized in new directory structure
- [ ] CLI filtering works correctly for all directories (basic, content, code, examples, archive)
- [ ] All pytest tests pass without regressions
- [ ] All active workflows validate against existing Pydantic `Spec` model

### Quality Verification  
- [ ] Naming convention `{subcategory}_{context}_{version}.yaml` applied consistently
- [ ] Directory structure provides clear categorisation without requiring metadata fields
- [ ] Documentation provides clear guidance for workflow discovery and usage
- [ ] Optional discovery metadata used judiciously through eval section only

### Functional Testing
- [ ] `elf0 list-specs` shows all workflows across directories
- [ ] Directory-specific filtering works for each category
- [ ] All migrated workflows execute successfully
- [ ] Error handling provides helpful user feedback
- [ ] Archive workflows remain accessible and functional
- [ ] No schema validation errors for any workflow

---

## Implementation Notes

- Preserve all existing workflow functionality during migration
- Test each migrated workflow individually before proceeding
- Maintain backwards compatibility where possible
- Focus on minimal, incremental changes to reduce risk
- Validate CLI changes thoroughly before committing
- Document any deviations from the original plan with clear rationale