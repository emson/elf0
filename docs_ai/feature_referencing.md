# YAML Workflow Referencing Feature Specification

## Overview
This document describes the design and implementation plan for a **YAML file referencing feature** in our workflow engine. By adding a top‐level `reference` key, one workflow file can pull in and execute the contents of another, enabling modular, DRY agent definitions while preserving full backward compatibility.

## Prerequisites
- Familiarity with our existing YAML schema: see `./docs_specs/spec_schema.md`.
- Understanding of the `Spec` loader in `src/elf/core/spec.py`.
- Knowledge of the graph‐compiler in `src/elf/core/compiler.py`.
- Comfort with Python, Pydantic, and YAML processing libraries (e.g. PyYAML or ruamel.yaml).

---

## Feature Description

1. **`reference` field**  
   Add an optional `reference` string at the root of the workflow spec:
   ```yaml
   # top-level of any workflow YAML
   reference: ./other_workflow.yaml
   ```
   When present, the loader will ignore all other keys in this file (or merge them—see merge semantics below) and instead load the spec from the referenced path.

2. **Nested references**  
   A referenced file may itself contain a `reference`, up to an arbitrary depth.

3. **Merge semantics**  
   By default, the referencing file’s other keys are _merged_ into the referenced spec:  
   - Any top-level keys not present in the referenced file are added.  
   - Keys present in both override those in the referenced file.  
   (E.g. override a prompt or model parameter.)

4. **Circular‐reference detection**  
   The loader tracks a `Set[Path]` of in-flight file paths. If a newly resolved path is already in the set, it raises a `CircularReferenceError`.

5. **Path resolution**  
   Supports both relative (to the referencing file’s directory) and absolute paths.

6. **Caching**  
   To avoid redundant disk I/O, the loader caches parsed `Spec` objects by their absolute `Path`.

7. **Backward compatibility**  
   Files without `reference` remain unchanged. All legacy workflows keep running as before.

---

## Changes in `spec_schema.md`

- **Add new field** under the root `Workflow` object:
  ```yaml
  Workflow:
    type: object
    properties:
      reference:
        type: string
        format: filepath
        description: >
          (optional) Path to another workflow YAML file. If set, the loader will
          import and merge that file’s spec here.
  ```
- **Document semantics**:
  - Merge vs overwrite modes.
  - Support for nested and absolute/relative paths.
  - Error cases (missing file, parse error, circular).
- **Examples**:
  ```yaml
  # reference only—full import
  reference: ./common/validation.yaml

  # reference + override
  reference: ../base/agent.yaml
  model:
    temperature: 0.2
  ```
- **Error scenarios** section.

---

## Spec‐loader Changes (`spec.py`)

1. **Pydantic model**  
   ```python
   class Workflow(BaseModel):
       reference: Optional[Path] = None
       # ... existing fields ...
   ```

2. **Recursive loader** in `Spec.from_file(path: Path, visited: Set[Path] = None)`:
   ```python
   def from_file(path, visited=None):
       visited = visited or set()
       path = path.resolve()
       if path in visited:
           raise CircularReferenceError(f"Circular reference: {path}")
       visited.add(path)

       raw = yaml_load(path)
       spec = Workflow.parse_obj(raw)

       if spec.reference:
           ref_path = (path.parent / spec.reference).resolve()
           base_spec = Spec.from_file(ref_path, visited)
           merged = merge_dicts(base_spec.dict(), raw)  # override semantics
           return Spec.parse_obj(merged)
       else:
           return Spec.parse_obj(raw)
   ```
   - **Circular detection** via `visited`.
   - **Caching**: add a module‐level `lru_cache` or dict keyed by `path`.

3. **Merge utility**  
   Write a helper to deep‐merge two dicts, preferring child values.

---

## Compiler Changes (`compiler.py`)

- **No change** to graph‐builders if `Spec` is already fully dereferenced at load time.  
- If you prefer _compile‐time_ merging, add at the start of `compile_spec()`:
  ```python
  if spec.reference:
      spec = load_and_merge(spec)  # as per spec.py logic
  ```
- **Node‐naming**  
  Optionally tag nodes with `source_file` metadata for better observability.
- **Error propagation**  
  Catch `CircularReferenceError` and rethrow as a `CompilationError` with file context.

---

## Error Handling & Validation

- **Missing file** → `FileNotFoundError: “Referenced file not found: …”`
- **YAML parse error** → include both file path and parser message.
- **Circular reference** → `CircularReferenceError` with cycle trace.
- **Invalid merge** → `ValueError: “Cannot merge scalar into mapping at …”`

All errors should include the _absolute_ path and line numbers where possible.

---

## Testing Strategy

1. **Unit tests for `Spec.from_file`**  
   - Single reference import  
   - Nested chain (A → B → C)  
   - Circular reference (A → B → A)  
   - Override semantics (child keys replace parent)  
   - Relative vs absolute paths  
2. **Integration tests**  
   - Compile a real routed‐agent YAML with references and verify the final `StateGraph`.  
3. **Regression tests**  
   - Existing single‐file specs continue to compile unchanged.

Aim for ~12–15 new test cases, using pytest fixtures to create temporary files.

---

## Documentation Updates

- **`docs_specs/spec_schema.md`**: add field, examples, errors.
- **Developer guide** (`compiler.md` or README): add “How to reference workflows” section.
- **Changelog**: document vNext breaking changes (though none to existing APIs).

---

## Priority Ordered Tasks

1. **Extend `spec_schema.md`**  
   - Add `reference` field, merge semantics, examples, error cases.  
2. **Enhance `spec.py` loader**  
   - Add `reference` field to model.  
   - Implement recursive load, merge utility, circular detection, caching.  
3. **Adjust `compiler.py`**  
   - No-op if spec is pre‐merged; else add pre‐compile merge and error wrapping.  
   - Optionally annotate nodes with source metadata.  
4. **Implement merge helper**  
   - Deep‐merge two dicts with override semantics.  
5. **Robust error messages**  
   - File not found, parse errors, circular reference.  
6. **Write unit tests**  
   - Cover all referencing, merging, and error scenarios.  
7. **Add integration & regression tests**  
   - Validate end-to-end compile results for referenced workflows.  
8. **Update documentation**  
   - Schema docs, developer guide, changelog.  
9. **CI pipeline**  
   - Ensure new tests run and fail on missing feature.  
10. **Developer walkthrough**  
   - Sample PR or doc with “Creating modular workflows with references.”

