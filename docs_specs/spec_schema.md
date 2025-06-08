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
    - **Note on `params`**: This field is for additional, provider-specific keyword arguments that take simple values (string, float, or integer). For complex, nested parameters (e.g., OpenAI's `response_format` which expects an object like `{"type": "json_object"}`), do not place them directly in `params`. Such parameters might need to be handled as top-level fields within the LLM definition if supported by the schema, or handled by the underlying LLM client integration. The `params` field is intended for flat key-value pairs.
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
      kind: <string>        #     (Required) agent | tool | judge | branch | mcp
      ref: <string>         #     (Optional for mcp nodes, Required for others) key into llms/functions/workflows
      config: <object>      #     (Optional for most nodes, Required for mcp nodes) node configuration
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

**Note on `params`**: This field is for additional, provider-specific keyword arguments that take simple values (string, float, or integer). For complex, nested parameters (e.g., OpenAI's `response_format` which expects an object like `{"type": "json_object"}`), do not place them directly in `params`. Such parameters might need to be handled as top-level fields within the LLM definition if supported by the schema, or handled by the underlying LLM client integration. The `params` field is intended for flat key-value pairs.

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
  - `name`: string (human-readable name)
  - `entrypoint`: dotted path (for Python) or MCP URI (for MCP)

**Python Functions:**
```yaml
functions:
  my_python_tool:
    type: python
    name: "Data Processor"
    entrypoint: "mymodule.submodule.process_data"
```

**MCP Functions (Legacy Pattern - Deprecated):**
```yaml
functions:
  my_mcp_tool:
    type: mcp
    name: "Calculator Tool"
    entrypoint: "mcp://localhost:3000/calculate"
```

**Note:** The MCP functions pattern above is deprecated. Use MCP nodes directly in workflows instead (see MCP Nodes section below).

**MCP URI Format:** `mcp://server:port/tool_name`
- **server**: MCP server hostname or IP
- **port**: MCP server port (optional, defaults vary by server)
- **tool_name**: Name of the tool to call on the MCP server

#### MCP Nodes

MCP nodes provide direct integration with Model Context Protocol servers, allowing workflows to execute tools from MCP servers without needing to define them in the `functions` section. This is the recommended approach for MCP integration.

**MCP Node Configuration:**
```yaml
workflow:
  nodes:
    - id: calculator
      kind: mcp
      config:
        server:
          command: ["python", "mcp/calculator/server.py"]
          cwd: "/path/to/project"  # Optional working directory
        tool: "add"
        parameters:
          a: "${state.json.a}"
          b: "${state.json.b}"
          operation: "${state.json.operation}"
```

**MCP Node Fields:**
- `server.command` (array, required): Command to start the MCP server
- `server.cwd` (string, optional): Working directory for the server process
- `tool` (string, required): Name of the tool to call on the MCP server
- `parameters` (object, optional): Parameters to pass to the tool (supports state variable substitution)

**Parameter Binding:**
MCP nodes support enhanced parameter binding from workflow state using the `${state.variable}` syntax:
```yaml
parameters:
  # Basic state variable binding
  input_data: "${state.user_input}"
  
  # JSON extraction from previous step output
  number_a: "${state.json.a}"
  number_b: "${state.json.b}"
  operation: "${state.json.operation}"
  
  # Static values
  format: "json"
  max_results: 10
```

**JSON Parameter Extraction:**
The `${state.json.field}` syntax allows extraction of specific fields from JSON data in the previous step's output:
- The system looks for JSON content in `state.output`
- Parses the JSON and extracts the specified field
- Falls back to the original template string if parsing fails

#### `workflow`
- **Type**: **Workflow** object  
- **Required**  
- Describes your directed (or cyclic) graph.  
- **CRUCIAL NOTE**: The `type` field (e.g., "sequential", "custom_graph", "react", "evaluator_optimizer") within this `workflow` block is **ABSOLUTELY MANDATORY**. Its absence is a common validation error. This field dictates how the nodes and edges are processed by the runtime. Please ensure it is always specified.
- **Workflow Fields**:
  - `type`: "sequential" | "react" | "evaluator_optimizer" | "custom_graph"  # This field is **REQUIRED**
  - `nodes`: array of **WorkflowNode**  
  - `edges`: array of **Edge**

**WorkflowNode**
- `id` (string): unique name  
- `kind` (string): "agent" / "tool" / "judge" / "branch" / "mcp"  
- `ref` (string): reference key into `llms`, `functions`, or sub-workflows (optional for MCP nodes, required for others)
- `config` (object): configuration object (required for MCP nodes, optional for others)
  - `format` (string, optional): Structured output format - "json" or "yaml"
    - When `format: json` is specified, the node expects JSON output that will be validated against the Spec schema and converted to clean YAML
    - When `format: yaml` is specified, the node validates YAML output against the Spec schema  
    - If no format is specified, output is processed as plain text
- `stop` (bool): marks finish nodes

**MCP Node Validation:**
- MCP nodes (`kind: "mcp"`) do not require the `ref` field
- MCP nodes must have a `config` object with required fields:
  - `server`: Server configuration with `command` array
  - `tool`: Tool name to execute
  - `parameters`: Tool parameters (optional)

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

### MCP Integration Example

```yaml
version: "0.1"
description: "Agent with MCP calculator integration"
runtime: "langgraph"

llms:
  analyzer_llm:
    type: openai
    model_name: gpt-4o-mini
    temperature: 0.3

workflow:
  type: custom_graph
  nodes:
    - id: input_analyzer
      kind: agent
      ref: analyzer_llm
      config:
        prompt: |
          Extract mathematical operation from: {input}
          Return JSON: {"a": number, "b": number, "operation": "add|subtract|multiply|divide"}
    - id: calculator
      kind: mcp
      config:
        server:
          command: ["python", "mcp/calculator/server.py"]
        tool: "calculate"
        parameters:
          a: "${state.json.a}"
          b: "${state.json.b}"
          operation: "${state.json.operation}"
    - id: result_formatter
      kind: agent
      ref: analyzer_llm
      config:
        prompt: "Format the calculation result: {output}"
      stop: true
  edges:
    - source: input_analyzer
      target: calculator
    - source: calculator
      target: result_formatter
```

---

### Notes & Extensions

- **Adding new `type`s**: Extend your Pydantic `Spec` model and update the node-factory registry.  
- **Branching/Loops**: Use `type: custom_graph` and define your own `nodes` & `edges`.  
- **Human-in-the-loop**: Insert a `branch` node with `condition: "await_user"` and wire in LangGraph's `interrupt()` handler.  
- **Structured outputs**: Use the `format` field in node config to specify "json" or "yaml" structured output validation.

### Structured Output Examples

#### JSON Format for Spec Generation
```yaml
workflow:
  nodes:
    - id: generate_spec
      kind: agent
      ref: spec_generator_llm
      config:
        format: json  # Expects JSON output, validates against Spec schema
        prompt: |
          Generate a workflow specification as structured JSON.
          Do not include markdown fences or commentary.
          
          Required structure:
          - version (string): "1.0"
          - description (string): Workflow description
          - runtime (string): "langgraph"
          - llms (object): LLM definitions
          - workflow (object): Workflow definition with nodes and edges
```

#### YAML Format Validation
```yaml
workflow:
  nodes:
    - id: validate_spec
      kind: agent  
      ref: validator_llm
      config:
        format: yaml  # Validates YAML output against Spec schema
        prompt: |
          Review and output the corrected YAML specification.
          Ensure all required fields are present and valid.
```

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
