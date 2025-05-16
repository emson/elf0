# Project Tasks

## Phase 1: MVP Functionality

### CLI Functionality
- [x] Add a `elf` command to the CLI, and it defaults to `help`
- [x] Add a `elf --help` command to the CLI
- [x] Add a `elf ./specs/<spec_name>.yaml` command to the CLI
- [x] Enhance `run_workflow_command` in `cli.py` with `--prompt_file <prompt.md>`:
  - [x] **Parameter Definition:**
    - [x] Add optional `--prompt_file` (type `Path`) for loading prompt from file
    - [x] Support markdown (.md) and XML (.xml) file extensions
    - [x] Validate file existence and extension
    - [x] Make `--prompt` optional when `--prompt_file` is provided
  - [x] **Behavior and Integration:**
    - [x] Read and validate prompt file content
    - [x] Combine prompt file content with `--prompt` when both provided
    - [x] Handle empty files and error cases gracefully
    - [x] Maintain backward compatibility with existing `--prompt` usage
  - [x] **Edge Cases and Robustness:**
    - [x] Handle file reading errors with clear messages
    - [x] Validate file extensions case-insensitively
    - [x] Ensure proper handling of empty files
    - [x] Handle encoding issues gracefully
  - [x] **Code Structure and Style:**
    - [x] Add helper function for prompt file reading
    - [x] Maintain consistent error handling patterns
    - [x] Add clear docstrings and comments
  - [x] **Example Usage in Help and Docstring:**
    - [x] Update command's docstring with `--prompt_file` examples:
      ```
      elf workflow.yaml --prompt_file prompt.md
      elf workflow.yaml --prompt_file prompt.md --prompt "Additional instructions"
      ```
  - [x] **Test Implementation:**
    - [x] Add test module for prompt file functionality:
      - [x] Test reading valid prompt files
      - [x] Test combining prompt file with prompt string
      - [x] Test handling of invalid file extensions
      - [x] Test handling of nonexistent files
      - [x] Test handling of empty files
      - [x] Test proper error messages
      - [x] Use Typer's CliRunner for proper CLI testing
      - [x] Follow CLI testing best practices

### Spec Functionality
- [x] Define a spec schema in JSON-Schema, in `docs_specs/spec_schema.md`
- [x] Create a simple example spec in YAML, in `specs/basic_chat.yaml`. It has one step and one agent and just returns the result from an input prompt.
- [x] Create `spec`, `compiler` and `runner` as well as the `yaml_loader`.
- [x] Implmement basic LLM call using LangGraph
  - [x] Create an `llm_client` file that implements the OpenAI API and returns a client that the `compiler.py` `make_llm_node` function can use


### Save File Functionality
- [x] Enhance `run_workflow_command` in `cli.py` with `--output <output.md>`:
  - [x] **Parameter Definition:**
    - [x] Add optional `--output` (type `Path`) for saving the final result.
    - [x] Handle various output file extensions (.md, .json, etc.).
    - [x] Validate writability:
      - [x] If file exists, check if writable.
      - [x] If file doesn't exist, check if parent directory exists and is writable.
  - [x] **Behavior and Integration:**
    - [x] Determine content to save from `run_workflow` result:
      - [x] If `result` is `dict` with 'output' key (string value), save that string.
      - [x] If `result` is `string`, save that string.
      - [x] Otherwise, serialize entire `result` as pretty-printed JSON.
    - [x] If `--output` is provided:
      - [x] Save content to the specified file.
      - [x] Print confirmation message with output file path on success.
      - [x] Print clear error message (e.g., `typer.secho`) on failure (permission, invalid path); do not crash.
    - [x] If `--output` is not provided:
      - [x] Preserve existing behavior (print to console, render Markdown, etc.).
  - [x] **Edge Cases and Robustness:**
    - [x] Handle mismatched extension and content format (e.g., JSON in .md); document in comments.
    - [x] Ensure saving to file suppresses console output of content (except confirmation message).
    - [x] If output content is empty or `None`, write an empty file and warn user.
    - [x] Handle file writing exceptions gracefully with user-friendly error messages.
  - [x] **Code Structure and Style:**
    - [x] Keep `--output` option consistent with Typer's style and existing options.
    - [x] Add clear docstrings/comments for the new option and behavior.
    - [x] Maintain readability and modularity; consider a helper function for file-saving.
  - [x] **Example Usage in Help and Docstring:**
    - [x] Update command's docstring with `--output` examples:
      ```
      elf workflow.yaml --prompt "Explain this code" --context file1.py --output result.md
      elf workflow.yaml --prompt "Summarize data" --output summary.json
      ```
    - [x] Clarify in help text: output file contains workflow result, console output replaced by confirmation when `--output` is used.

### Implement the Other Patterns
- [x] Add a new Spec file `specs/prompt_chaining.yaml` that implements the prompt chain pattern
- [ ] Add a new Spec file `specs/prompt_routing.yaml` that implements the prompt routing pattern

### Test Implementation
- [x] Create test module for core Spec functionality:
  - [x] Set up test data constants for valid configurations
  - [x] Implement test_create_valid_spec to verify basic Spec creation
  - [x] Implement test_workflow_edge_validation to verify edge validation
  - [x] Implement test_node_reference_validation to verify LLM/function references
  - [x] Implement test_spec_from_file to verify YAML loading
  - [x] Add proper docstrings and test descriptions
  - [x] Use pytest fixtures for file handling
  - [x] Follow best practices for test structure and assertions

- [x] Create test module for core Compiler functionality:
  - [x] Set up helper functions for creating test specs
  - [x] Implement test_compile_minimal_workflow to verify basic graph creation
  - [x] Implement test_compile_workflow_with_conditional_edges to verify branching
  - [x] Implement test_condition_function_evaluation to verify condition handling
  - [x] Implement test_node_factory_registry to verify node creation
  - [x] Implement test_workflow_state_management to verify state handling
  - [x] Add proper docstrings and test descriptions
  - [x] Follow best practices for test structure and assertions


