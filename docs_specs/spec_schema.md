i## Spec YAML Schema Reference

```yaml
# Top-level object
version: <string>            # (Required) Spec version, e.g. "0.1"
description: <string>        # (Optional) Free-text description of this workflow
reference: <string> or <list of strings>
runtime:                     # (Required) Which engine to use
  langgraph | agentiq
llms:                        # (Required) Named LLM clients
  <llm_name>:                #   key used in workflow.nodes[].ref
    type:                    #   (Required) one of: openai, anthropic, ollama
    model_name: <string>     #   (Required) provider model identifier
    temperature: <float>     #   (Optional, default 0.0) sampling temperature
    params:                  #   (Optional) provider-specific keyword args
      <param>: <value>
retrievers:                  # (Optional) Named Retriever configs
  <retriever_name>:
    type:                    #   one of: qdrant, redis, weaviate
    collection: <string>     #   name of vector collection
memory:                      # (Optional) Named Memory stores
  <memory_name>:
    type:                    #   one of: inmemory, qdrant, postgres
    namespace: <string>      #   namespace / table / prefix
functions:                   # (Optional) Named Tool / Function definitions
  <function_name>:
    type:                    #   one of: python, mcp
    name: <string>           #   human-readable name
    entrypoint: <string>     #   dotted path or MCP URI
workflow:                    # (Required) Defines the directed graph
  type:                     #   (Required) one of: sequential, react, evaluator_optimizer, custom_graph
  nodes:                    #   (Required) list of graph nodes
    - id: <string>          #     (Required) unique node identifier
      kind: <string>        #     (Required) agent | tool | judge | branch
      ref: <string>         #     (Required) key into llms/functions/workflows
      stop: <bool>          #     (Optional, default false) mark finish points
  edges:                    #   (Required; can be empty) list of transitions
    - source: <string>      #     (Required) node.id
      target: <string>      #     (Required) node.id
      condition: <string>   #     (Optional) Python expression, uses state keys
eval:                        # (Optional) evaluation harness
  metrics:                  #   list of metric names to collect
    - quality
    - latency
  dataset_path: <string>    #   path to prompts/gold file (jsonl, csv…)
```

---

### Field-by-Field Description

#### `version`
- **Type**: string  
- **Required**  
- Indicates your spec's version; bump when schema or semantics change.

#### `description`
- **Type**: string  
- **Optional**  
- A human-friendly summary of the workflow's purpose.

#### `reference`
- **Type**: string (filepath) or list of strings (filepaths)
- **Optional**  
- Path (or list of paths) to other workflow YAML file(s) to import and merge. 
- When present, the loader will import the referenced file(s) and merge their specifications. 
- If a list of paths is provided, they are merged sequentially: the first file in the list forms the base, and each subsequent file is merged on top of the accumulated result. 
- Finally, any additional keys defined in the current file take precedence over all referenced files (override semantics). 
- Supports both relative paths (relative to the current file's directory) and absolute paths. 
- Nested references are supported, but circular references will raise an error.

#### `runtime`
- **Type**: literal  
- **Values**: `langgraph` or `agentiq`  
- Specifies which execution engine will run this spec.

#### `llms`
- **Type**: map of **LLM** objects  
- **Required**  
- Defines each LLM client you'll call.  
- **LLM Object**:
  - `type`: "openai" | "anthropic" | "ollama"  
  - `model_name`: string  
  - `temperature`: float (default 0.0)  
  - `params`: map of provider-specific kwargs

```yaml
llms:
  chat_llm:
    type: openai
    model_name: gpt-4o-mini
    temperature: 0.2
    params:
      max_tokens: 512
```

#### `retrievers`
- **Type**: map of **Retriever** objects  
- **Optional** (defaults to `{}`)  
- For RAG use-cases: point at your vector stores.  
- **Retriever Object**:
  - `type`: "qdrant" | "redis" | "weaviate"  
  - `collection`: string

#### `memory`
- **Type**: map of **Memory** objects  
- **Optional**  
- Defines persistent context stores.  
- **Memory Object**:
  - `type`: "inmemory" | "qdrant" | "postgres"  
  - `namespace`: string

#### `functions`
- **Type**: map of **Function** objects  
- **Optional**  
- For local-python or MCP tool integrations.  
- **Function Object**:
  - `type`: "python" | "mcp"  
  - `name`: string  
  - `entrypoint`: dotted path or URI

#### `workflow`
- **Type**: **Workflow** object  
- **Required**  
- Describes your directed (or cyclic) graph.  
- **Workflow Fields**:
  - `type`: "sequential" | "react" | "evaluator_optimizer" | "custom_graph"  
  - `nodes`: array of **WorkflowNode**  
  - `edges`: array of **Edge**

**WorkflowNode**
- `id` (string): unique name  
- `kind` (string): "agent" / "tool" / "judge" / "branch"  
- `ref` (string): reference key into `llms`, `functions`, or sub-workflows  
- `stop` (bool): marks finish nodes

**Edge**
- `source` (string): node.id  
- `target` (string): node.id  
- `condition` (string): Python expression evaluated against state

#### `eval`
- **Type**: map  
- **Optional**  
- Hooks for benchmarking & self-improvement.  
- Typical keys:
  - `metrics`: list of metric names  
  - `dataset_path`: path to a JSONL or CSV of test prompts/gold outputs

---

### Full Minimal Example

```yaml
version: "0.1"
description: "Single-turn chat"
runtime: "langgraph"

llms:
  chat_llm:
    type: openai
    model_name: gpt-4o-mini
    temperature: 0.0
    params: {}

retrievers: {}
memory: {}
functions: {}

workflow:
  type: sequential
  nodes:
    - id: chat
      kind: agent
      ref: chat_llm
      stop: true
  edges: []

eval:
  metrics:
    - quality
  dataset_path: "data/test_prompts.jsonl"
```

---

### Notes & Extensions

- **Adding new `type`s**: Extend your Pydantic `Spec` model and update the node-factory registry.  
- **Branching/Loops**: Use `type: custom_graph` and define your own `nodes` & `edges`.  
- **Human-in-the-loop**: Insert a `branch` node with `condition: "await_user"` and wire in LangGraph's `interrupt()` handler.  
- **Structured outputs**: Embed a "judge" node that validates with a JSON Schema.

### Reference Examples

#### Simple reference (import everything)
```yaml
# basic_agent.yaml
reference: ./common/reasoning_agent.yaml
```

#### Reference with overrides
```yaml
# custom_agent.yaml
reference: ../base/agent.yaml
llms:
  chat_llm:
    temperature: 0.2  # Override temperature from base file
workflow:
  type: custom_graph  # Override workflow type
```

#### Nested references
```yaml
# File A references File B, which references File C
# agent_a.yaml
reference: ./agent_b.yaml
description: "Agent A with custom description"

# agent_b.yaml  
reference: ./agent_c.yaml
llms:
  chat_llm:
    temperature: 0.5

# agent_c.yaml (base definition)
version: "0.1"
llms:
  chat_llm:
    type: openai
    model_name: gpt-4o-mini
# ... rest of spec
```

#### Multiple References Example

```yaml
# main_workflow.yaml
reference:
  - ./common/base_llms.yaml      # Defines common LLM configurations
  - ./common/base_workflow.yaml  # Defines a base workflow structure

description: "Main workflow that combines LLMs and a base structure, then customizes."

llms:
  specific_llm: # Added in this file
    type: openai
    model_name: gpt-4-turbo
  chat_llm: # Overrides chat_llm from base_llms.yaml if it exists
    temperature: 0.3 

workflow:
  nodes:
    # Add new nodes or override nodes from base_workflow.yaml
    - id: custom_step
      kind: agent
      ref: specific_llm
      config:
        prompt: "This is a custom step added in main_workflow.yaml"
```

### Error Handling

When loading and processing spec files, several types of errors can occur:

#### File Not Found Error
- **Type**: `FileNotFoundError`
- **Cause**: A `reference` path in the YAML points to a file that does not exist.
- **Example Message**: `FileNotFoundError: Referenced file not found: ./missing_workflow.yaml`

#### Circular Reference Error
- **Type**: `CircularReferenceError` (Custom exception from `elf.core.spec`)
- **Cause**: A chain of `reference` declarations creates a loop (e.g., File A references File B, and File B references File A).
- **Example Message**: `CircularReferenceError: Circular reference detected in workflow chain: /path/to/agent_a.yaml -> /path/to/agent_b.yaml -> /path/to/agent_a.yaml`

#### Workflow Reference Error
- **Type**: `WorkflowReferenceError` (Custom exception from `elf.core.spec`)
- **Cause**: A general error occurred while trying to process a `reference`. This can include:
    - The `reference` value is not a string or a list of strings.
    - An item within a list of references is not a string.
    - An underlying error (like a `pydantic.ValidationError` or `YAMLError`) occurred while loading or merging a referenced file. The original error will typically be nested.
- **Example Message (wrapping a Pydantic error)**: `WorkflowReferenceError: Error processing reference '/path/to/referenced_spec.yaml': 1 validation error for Spec\n  Value error, Node 'some_node' references unknown LLM 'unknown_llm' [type=value_error, ...]`
- **Example Message (invalid reference format)**: `WorkflowReferenceError: Invalid format for 'reference' in main.yaml. Must be a string or a list of strings.`

#### YAML Parse Error
- **Type**: `yaml.YAMLError` (from the PyYAML library)
- **Cause**: The YAML syntax in the main spec file or any referenced spec file is invalid.
- **Example Message**: `YAMLError: Failed to parse referenced file ./invalid_syntax.yaml: Line 5: mapping values are not allowed here`

#### Pydantic Validation Error
- **Type**: `pydantic.ValidationError`
- **Cause**: The structure or values in the YAML file (after successful parsing and merging) do not conform to the `Spec` model's schema (e.g., required fields missing, incorrect data types, invalid enum values, or custom validation failures like a node referencing an LLM not defined in the `llms` section).
- **Example Message**: `pydantic.ValidationError: 1 validation error for Spec\nworkflow -> nodes -> 0 -> kind\n  Input should be 'agent', 'tool', 'judge' or 'branch' [type=literal_error, ...]`
  (This can also be wrapped by `WorkflowReferenceError` if it occurs during the processing of a referenced file).

#### Value Error (During Merging)
- **Type**: `ValueError` (from `_deep_merge_dicts` in `elf.core.spec`)
- **Cause**: An attempt was made to merge incompatible data types during the deep merge process (e.g., trying to merge a string into a dictionary at the same key).
- **Example Message**: `ValueError: Cannot merge incompatible types at key 'llms': dict and str`

This section, along with your Python `Spec` definitions and the rest of the schema documentation, should provide a comprehensive guide for authoring valid YAML specs.
