i## Spec YAML Schema Reference

```yaml
# Top-level object
version: <string>            # (Required) Spec version, e.g. "0.1"
description: <string>        # (Optional) Free-text description of this workflow
runtime:                     # (Required) Which engine to use
  langgraph | agentiq
llms:                        # (Required) Named LLM clients
  <llm_name>:                #   key used in workflow.nodes[].ref
    _type:                   #   (Required) one of: openai, anthropic, ollama
    model_name: <string>     #   (Required) provider model identifier
    temperature: <float>     #   (Optional, default 0.0) sampling temperature
    params:                  #   (Optional) provider-specific keyword args
      <param>: <value>
retrievers:                  # (Optional) Named Retriever configs
  <retriever_name>:
    _type:                   #   one of: qdrant, redis, weaviate
    collection: <string>     #   name of vector collection
memory:                      # (Optional) Named Memory stores
  <memory_name>:
    _type:                   #   one of: inmemory, qdrant, postgres
    namespace: <string>      #   namespace / table / prefix
functions:                   # (Optional) Named Tool / Function definitions
  <function_name>:
    _type:                   #   one of: python, mcp
    name: <string>           #   human-readable name
    entrypoint: <string>     #   dotted path or MCP URI
workflow:                    # (Required) Defines the directed graph
  _type:                    #   (Required) one of: sequential, react, evaluator_optimizer, custom_graph
  nodes:                    #   (Required) list of graph nodes
    - id: <string>          #     (Required) unique node identifier
      kind: <string>        #     (Required) agent | tool | judge | branch
      ref: <string>         #     (Required) key into llms/functions/workflows
      stop: <bool>          #     (Optional, default false) mark finish points
  edges:                    #   (Required; can be empty) list of transitions
    - source: <string>      #     (Required) node.id
      target: <string>      #     (Required) node.id
      condition: <string>   #     (Optional) Python expression, uses state keys
eval:                        # (Optional) evaluation harness
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
- Indicates your spec’s version; bump when schema or semantics change.

#### `description`
- **Type**: string  
- **Optional**  
- A human-friendly summary of the workflow’s purpose.

#### `runtime`
- **Type**: literal  
- **Values**: `langgraph` or `agentiq`  
- Specifies which execution engine will run this spec.

#### `llms`
- **Type**: map of **LLM** objects  
- **Required**  
- Defines each LLM client you’ll call.  
- **LLM Object**:
  - `_type`: “openai” | “anthropic” | “ollama”  
  - `model_name`: string  
  - `temperature`: float (default 0.0)  
  - `params`: map of provider-specific kwargs

```yaml
llms:
  chat_llm:
    _type: openai
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
  - `_type`: “qdrant” | “redis” | “weaviate”  
  - `collection`: string

#### `memory`
- **Type**: map of **Memory** objects  
- **Optional**  
- Defines persistent context stores.  
- **Memory Object**:
  - `_type`: “inmemory” | “qdrant” | “postgres”  
  - `namespace`: string

#### `functions`
- **Type**: map of **Function** objects  
- **Optional**  
- For local-python or MCP tool integrations.  
- **Function Object**:
  - `_type`: “python” | “mcp”  
  - `name`: string  
  - `entrypoint`: dotted path or URI

#### `workflow`
- **Type**: **Workflow** object  
- **Required**  
- Describes your directed (or cyclic) graph.  
- **Workflow Fields**:
  - `_type`: “sequential” | “react” | “evaluator_optimizer” | “custom_graph”  
  - `nodes`: array of **WorkflowNode**  
  - `edges`: array of **Edge**

**WorkflowNode**
- `id` (string): unique name  
- `kind` (string): “agent” / “tool” / “judge” / “branch”  
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
    _type: openai
    model_name: gpt-4o-mini
    temperature: 0.0
    params: {}

retrievers: {}
memory: {}
functions: {}

workflow:
  _type: sequential
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

- **Adding new `_type`s**: Extend your Pydantic `Spec` model and update the node-factory registry.  
- **Branching/Loops**: Use `_type: custom_graph` and define your own `nodes` & `edges`.  
- **Human-in-the-loop**: Insert a `branch` node with `condition: "await_user"` and wire in LangGraph’s `interrupt()` handler.  
- **Structured outputs**: Embed a “judge” node that validates with a JSON Schema.

This reference, together with your Python `Spec` definitions, ensures anyone can author valid YAML specs and understand every field.  