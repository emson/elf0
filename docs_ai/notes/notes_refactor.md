# ELF Codebase Refactoring Plan for LLM Optimization

This document outlines the proposed refactoring steps to optimize the ELF codebase for better LLM processing, improved maintainability, and adherence to best practices.

## I. Refactor `src/elf/cli.py`

**Summary Overview:** The `cli.py` module currently handles command-line argument parsing, file I/O for prompts and context files, output formatting, and logging setup. The goal is to make `cli.py` leaner by extracting general-purpose file utilities into a new, dedicated module. This will improve separation of concerns and code reusability.

**Tasks:**

- [ ] **Create `src/elf/utils/file_utils.py`:**
    - **Context:** To centralize file-related utility functions currently in `cli.py`.
    - **Why:** Improves modularity and makes `cli.py` more focused on CLI logic. Allows these utilities to be reused elsewhere.
    - **Action:** Create a new file named `file_utils.py` in the `src/elf/utils/` directory.

- [ ] **Move `_is_valid_file` to `file_utils.py`:**
    - **Context:** This function (`_is_valid_file(path: Path) -> bool`) in `cli.py` checks if a path exists and is a file.
    - **Why:** It's a generic file system check, suitable for a utility module.
    - **Action:** Define `is_valid_file` (consider removing leading underscore for public utility) in `src/elf/utils/file_utils.py` and remove it from `cli.py`. Update call sites in `cli.py`.

- [ ] **Move `_read_files_content` to `file_utils.py`:**
    - **Context:** This function (`_read_files_content(files: List[Path]) -> str`) in `cli.py` reads and concatenates content from a list of files.
    - **Why:** It's a general file reading utility.
    - **Action:** Define `read_files_content` (consider removing leading underscore) in `src/elf/utils/file_utils.py` and remove it from `cli.py`. Update call sites.

- [ ] **Move `_parse_comma_separated_files` to `file_utils.py`:**
    - **Context:** This function (`_parse_comma_separated_files(file_str: str) -> List[Path]`) in `cli.py` parses a comma-separated string of file paths.
    - **Why:** It's a string and path parsing utility related to file inputs.
    - **Action:** Define `parse_comma_separated_files` (consider removing leading underscore) in `src/elf/utils/file_utils.py` and remove it from `cli.py`. Update call sites. It will use `is_valid_file` from the same module.

- [ ] **Move `parse_context_files` to `file_utils.py`:**
    - **Context:** This function (`parse_context_files(context_files: Optional[List[Path]]) -> str`) in `cli.py` uses the helper functions above to process context file arguments.
    - **Why:** It directly orchestrates the file utility functions being moved.
    - **Action:** Define `parse_context_files` in `src/elf/utils/file_utils.py` and remove it from `cli.py`. Update `cli.py` to import and use it from `elf.utils.file_utils`. This function will use helpers like `parse_comma_separated_files` and `read_files_content` from within its own module.

- [ ] **Move `parse_at_references` to `file_utils.py`:**
    - **Context:** This function (`parse_at_references(prompt: str) -> tuple[str, List[Path]]`) in `cli.py` extracts `@file` references from a prompt string and validates them.
    - **Why:** It involves file path extraction and validation, fitting the scope of `file_utils.py`.
    - **Action:** Define `parse_at_references` in `src/elf/utils/file_utils.py` and remove it from `cli.py`. Update `cli.py` to import and use it. This function will use `is_valid_file` from the same module.

- [ ] **Update imports in `cli.py`:**
    - **Context:** After moving file utility functions.
    - **Why:** To ensure `cli.py` correctly accesses the moved functions from `elf.utils.file_utils`.
    - **Action:** Add `from elf.utils import file_utils` (or similar, depending on how functions are exposed, e.g., `from elf.utils.file_utils import parse_context_files, parse_at_references`) and update all call sites of the moved functions.

- [ ] **Review `improve_yaml_command` in `cli.py` for YAML saving:**
    - **Context:** The `improve_yaml_command` saves an (improved) YAML specification.
    - **Why:** To ensure consistency by using the existing `elf.utils.yaml_loader.save_yaml_file` utility if the improved data is in a compatible dictionary format.
    - **Action:** Inspect `improve_yaml_command`. If it manually writes YAML and the data is available as a dictionary, refactor to use `save_yaml_file` from `elf.utils.yaml_loader`.

- [ ] **Review `read_prompt_file` in `cli.py`:**
    - **Context:** This function reads a prompt from a file.
    - **Why:** To determine if it's simple enough to be inlined or replaced by a generic text file reading utility (potentially added to `file_utils.py`).
    - **Action:** Examine `read_prompt_file`. If it performs complex parsing specific to prompts beyond simple text reading or `@file` references, keep it. Otherwise, simplify or replace with a generic utility like `Path(prompt_file).read_text()`.

## II. Refinements in `src/elf/utils/`

**Summary Overview:** The `utils` directory contains `yaml_loader.py`. The focus here is on improving clarity around function naming, specifically for `load_spec`, to avoid confusion with a similarly named function in `core/spec.py`.

**Tasks:**

- [ ] **Clarify `load_spec` function name in `elf.utils.yaml_loader.py`:**
    - **Context:** `elf.utils.yaml_loader.py` has a `load_spec` function that loads a single YAML file and validates it using `Spec.model_validate()`. `elf.core.spec.py` has `Spec.from_file()` (also exposed via `elf.core.spec.load_spec`) which handles loading full specifications including references and merging.
    - **Why:** The identical name `load_spec` for functions with different scopes (single file validation vs. full spec lifecycle) can be confusing.
    - **Action:** Rename `load_spec` in `elf.utils.yaml_loader.py` to something more descriptive like `load_and_validate_single_yaml_as_spec` or `parse_yaml_to_spec_model`. Update its docstring to clearly differentiate its purpose from `elf.core.spec.load_spec` (or `Spec.from_file`). Update the call site in `elf.core.runner.run_workflow` (which currently uses `from elf.core.spec import load_spec`) to ensure it's calling the correct one, likely the one from `elf.core.spec`. The `yaml_loader.load_spec` is actually used internally in `core.spec.Spec.from_file` via an indirection through `yaml_loader.load_yaml_file` and then `Spec.model_validate(data)` is called inside `from_file` after loading. The key is to ensure the `load_spec` in `yaml_loader.py` (if kept or renamed) is clearly for the *single file parsing and Pydantic model validation step*, not the full spec loading with reference handling. *Self-correction: After re-checking, `runner.py` uses `from elf.core.spec import load_spec`. The `load_spec` in `yaml_loader.py` seems to be primarily for backward compatibility or internal use. The main goal is to ensure its name and docstring are very clear about its limited role if it's still needed.*
    - **Revised Action:** Review the usage of `load_spec` in `yaml_loader.py`. If it is primarily for backward compatibility and potentially can be phased out or its role is very specific (e.g., a direct YAML-to-Pydantic parse without reference handling), rename it for clarity (e.g., `_internal_load_yaml_for_spec_model`) and update its docstring. Ensure the main `load_spec` in `core.spec.py` (which calls `Spec.from_file`) is the one used for general spec loading.

## III. Considerations for `src/elf/core/`

**Summary Overview:** The `core` modules (`spec.py`, `compiler.py`, `runner.py`) are generally well-structured. The main consideration is to ensure merge logic for specifications is intentional and logging is consistent.

**Tasks:**

- [ ] **Verify merge logic in `spec.py` (`_deep_merge_dicts`) vs. `yaml_loader.py` (`merge_yaml_data`):**
    - **Context:** `spec.py` has `_deep_merge_dicts` (list replacement semantics) used when `Spec.from_file` processes referenced specs. `yaml_loader.py` has `merge_yaml_data` (list concatenation semantics).
    - **Why:** To confirm that this difference in merge strategies (especially for lists) is intentional and correctly applied in the context of spec referencing and general YAML merging.
    - **Action:** Review the usage of `_deep_merge_dicts` within `Spec.from_file` to ensure it aligns with the desired behavior for merging included/referenced specifications. Confirm that `merge_yaml_data` in `yaml_loader.py` is used where its specific list concatenation behavior is intended. No change if the distinct behaviors are by design and correctly used.

- [ ] **Confirm logging setup consistency:**
    - **Context:** `cli.py` configures global logging levels. `compiler.py` sets up its own `RichHandler`.
    - **Why:** To ensure that logging behaves predictably and the CLI's verbosity settings correctly influence all relevant parts of the `elf.core` loggers.
    - **Action:** Verify that the logger named `elf.core.compiler` (or any other logger within `elf.core`) correctly inherits and respects the logging level set for the parent `elf.core` logger by `cli.py`. The current setup appears largely correct, this is a verification step.

## IV. General Code Health

**Summary Overview:** The codebase demonstrates good practices with type hinting and docstrings. These should be maintained.

**Tasks:**

- [ ] **Maintain and enhance type hinting:**
    - **Context:** The codebase uses Pydantic and `TypedDict` effectively.
    - **Why:** Strong typing improves code robustness, readability, and maintainability, and is very helpful for LLM understanding.
    - **Action:** Continue to ensure all new and modified function signatures, class attributes, and important variables are fully type-hinted.

- [ ] **Maintain high-quality docstrings:**
    - **Context:** Existing code generally has good docstrings.
    - **Why:** Clear docstrings are crucial for human and LLM comprehension, explaining purpose, arguments, returns, and side effects.
    - **Action:** Ensure all new and modified modules, classes, methods, and functions have comprehensive docstrings that follow a consistent style (e.g., Google style, NumPy style). 