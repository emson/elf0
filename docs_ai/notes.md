# General Project Notes and Todos

- Save files to a tmp dir on each iteration


- [ ] Enhance `run_workflow_command` in `cli.py` with `--output <output.md>`:
  - [ ] **Parameter Definition:**
    - [ ] Add optional `--output` (type `Path`) for saving the final result.
    - [ ] Handle various output file extensions (.md, .json, etc.).
    - [ ] Validate writability:
      - [ ] If file exists, check if writable.
      - [ ] If file doesn't exist, check if parent directory exists and is writable.
  - [ ] **Behavior and Integration:**
    - [ ] Determine content to save from `run_workflow` result:
      - [ ] If `result` is `dict` with 'output' key (string value), save that string.
      - [ ] If `result` is `string`, save that string.
      - [ ] Otherwise, serialize entire `result` as pretty-printed JSON.
    - [ ] If `--output` is provided:
      - [ ] Save content to the specified file.
      - [ ] Print confirmation message with output file path on success.
      - [ ] Print clear error message (e.g., `typer.secho`) on failure (permission, invalid path); do not crash.
    - [ ] If `--output` is not provided:
      - [ ] Preserve existing behavior (print to console, render Markdown, etc.).
  - [ ] **Edge Cases and Robustness:**
    - [ ] Handle mismatched extension and content format (e.g., JSON in .md); document in comments.
    - [ ] Ensure saving to file suppresses console output of content (except confirmation message).
    - [ ] If output content is empty or `None`, write an empty file and warn user.
    - [ ] Handle file writing exceptions gracefully with user-friendly error messages.
  - [ ] **Code Structure and Style:**
    - [ ] Keep `--output` option consistent with Typer's style and existing options.
    - [ ] Add clear docstrings/comments for the new option and behavior.
    - [ ] Maintain readability and modularity; consider a helper function for file-saving.
  - [ ] **Example Usage in Help and Docstring:**
    - [ ] Update command's docstring with `--output` examples:
      ```
      awa workflow.yaml --prompt "Explain this code" --context file1.py --output result.md
      awa workflow.yaml --prompt "Summarize data" --output summary.json
      ```
    - [ ] Clarify in help text: output file contains workflow result, console output replaced by confirmation when `--output` is used.
