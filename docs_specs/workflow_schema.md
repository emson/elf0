# workflow.schema.yaml
This document defines the schema for a workflow in YAML format.
It describes the schema structure, gives descriptions of each field, and provides examples.

## 1. Top-Level Schema (JSON-Schema excerpt)

```yaml
type: object
required:
  - version
  - description
  - agents
  - steps
  - output
properties:
  version:
    type: string
    description: SemVer or simple version (e.g. "0.1.0")
  description:
    type: string
    description: Human-readable summary of the workflow’s goal
  defaults:
    type: object
    description: Global defaults for LLM client, model & parameters
    properties:
      llm_client:
        $ref: "#/definitions/LLMClient"
  tools:
    type: array
    description: “Pure” function or MCP tool registrations
    items:
      $ref: "#/definitions/ToolDef"
  agents:
    type: array
    description: LLM “personas” with prompts and optional tool list
    items:
      $ref: "#/definitions/AgentDef"
  steps:
    type: array
    description: Ordered execution units (agent, tool, or sub-workflow)
    items:
      $ref: "#/definitions/StepDef"
  output:
    $ref: "#/definitions/OutputDef"

definitions:
  LLMClient:
    type: object
    required: [type, model]
    properties:
      type:   { type: string, enum: ["openai","anthropic","local_vllm", /*…*/] }
      model:  { type: string }
      params: { type: object, additionalProperties: true }
  ToolDef:
    type: object
    required: [id]
    properties:
      id:          { type: string }
      description: { type: string }
  AgentDef:
    type: object
    required: [id, system_prompt, user_prompt]
    properties:
      id:             { type: string }
      llm_client:     { $ref: "#/definitions/LLMClient" }
      system_prompt:  { type: string }
      user_prompt:    { type: string }
      tools:
        type: array
        items: { type: string }
      output_parser:  { type: string }
  StepDef:
    type: object
    required: [id]
    properties:
      id:         { type: string }
      agent_id:   { type: string }
      tool_id:    { type: string }
      workflow:   { type: string }
      input:
        type: object
        required: [source]
        properties:
          source: { type: string }
          key:    { type: string }
      mode:       { type: string, enum: ["serial","map","parallel"] }
      branch:
        type: object
        properties:
          source: { type: string }
          cases:
            type: object
            additionalProperties: { type: string }
      condition:  { type: string }
      params:
        type: object
        additionalProperties: true
      tool_params:
        type: object
        additionalProperties: true
      on_error:   { type: string, enum: ["retry","skip","fail"] }
      max_retries:{ type: integer }
  OutputDef:
    type: object
    required: [step]
    properties:
      step:
        type: string
        description: “Which step’s result is the final workflow output”
      save_to:
        type: object
        properties:
          path: { type: string }
```

---

## 2. Field-by-Field Explanation

| Section    | Field              | Purpose & Notes                                                                                                                                           |
|------------|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Meta**   | `version`          | Version your workflow defs. Helps migrations if schema changes.                                                                                          |
|            | `description`      | Human summary—LLMs use this as context to choose styles, safety rules, etc.                                                                              |
| **Defaults**| `defaults.llm_client` | Global client/model/params, inherited by all agents unless overridden.                                                                                |
| **Tools**  | `tools[]`          | Register pure-function steps (text splitters, retrievers, MCP calls). Tools differ from agents: they are **deterministic** code, not LLM prompts.         |
| **Agents** | `agents[]`         | Each describes an LLM persona: ⟨client, prompts, optional tools⟩.                                                                                         |
|            | `llm_client`       | Overrides `defaults.llm_client` if present. Useful for mixing OpenAI & Anthropic in one flow.                                                             |
|            | `system_prompt`    | Cold-start instruction (Anthropic “System”).                                                                                                              |
|            | `user_prompt`      | Dynamic template (Anthropic “User”), uses Jinja variables like `{{ input }}` or `{{ steps.foo.output }}`.                                                 |
|            | `tools[]`          | Function-calling schemas this agent may invoke. Engine wires in JSON-Schema so LLM can call them.                                                        |
| **Steps**  | `id`               | Unique name for DAG nodes.                                                                                                                                |
|            | **Exactly one** of:<br>• `agent_id`<br>• `tool_id`<br>• `workflow` | Defines the *type* of work. Agents → LLM; Tools → code; Workflow → nested YAML.                                                   |
|            | `input.source`     | `"USER_INPUT"` or a previous step `id`. Tells engine where to take the input payload from.                                                               |
|            | `input.key`        | If the source is a dict, pick a sub-field (e.g. select `"text"` from `{text,metadata}`).                                                                   |
|            | `mode`             | Controls fan-out:<br>• `serial` (default) → one call<br>• `map` → call once per item in a **list** input<br>• `parallel` → call all items concurrently       |
|            | `branch`           | **Routing**: pattern = Anthropic “routing agent.” Matches classifier output to next step by literal key.                                                 |
|            | `condition`        | **Evaluator-optimizer**: run step only if Jinja expression is true (e.g. `{{ steps.eval.score < 7 }}`).                                                     |
|            | `params`           | Override LLM params (temperature, max_tokens) on a per-step basis—e.g. higher temperature for creative refine passes.                                      |
|            | `tool_params`      | Pass args into your pure-code tool step (e.g. `{"split_on":"\n\n"}`).                                                                                       |
|            | `on_error` / `max_retries` | Simple fault-tolerance (e.g. `retry` on transient API errors).                                                                                 |
| **Output** | `output.step`      | Which step produces the final JSON result.                                                                                                                |
|            | `output.save_to`   | Filesystem path template. Engine writes atomically.                                                                                                       |

---

## 3. Mapping to Anthropic Patterns

| Pattern                  | YAML Feature                                 | Example element                           |
|--------------------------|-----------------------------------------------|-------------------------------------------|
| **Prompt-Chaining**      | serial steps                                  | no `mode`, no `branch`                    |
| **Routing**              | `branch` block                                | see `workflows/routing.yaml` above        |
| **Parallelisation**      | `mode: map` or `mode: parallel`               | see `workflows/orchestrator_example.yaml` |
| **Orchestrator–Worker**  | fan-out (`mode: map`) + aggregator step       | planner → `mode: map` → aggregator        |
| **Evaluator–Optimizer**  | `condition` + per-step `params` override      | only run refine if score low              |
| **Self-Reflection**      | multi-step mirror of draft → reflect → revise | similar to evaluator but no external data |

---

## 4. Example: Mixed Orchestrator + Tool + Sub-Workflow

```yaml
# workflows/mixed_example.yaml
version: 0.1.0
description: >
  Split input into paragraphs, summarise each, run sentiment,
  then compile executive summary.

defaults:
  llm_client:
    type: openai
    model: gpt-4o
    params:
      temperature: 0.2

tools:
  - id: splitter
    description: "Split text into paragraphs"

agents:
  - id: summariser
    system_prompt: |
      You are a summariser. Condense the paragraph into one sentence.
    user_prompt: |
      Paragraph:
      {{ input.text }}

steps:
  - id: split_para
    tool_id: splitter
    input:
      source: USER_INPUT
    tool_params:
      delimiter: "\n\n"

  - id: sum_each
    agent_id: summariser
    mode: map
    input:
      source: split_para
      key: text

  - id: sentiment_check
    workflow: workflows/sentiment_analysis.yaml
    input:
      source: sum_each
      key: outputs

  - id: compile_report
    agent_id: summariser
    input:
      source: sentiment_check
      key: outputs

output:
  step: compile_report
  save_to:
    path: "results/{{ name }}.json"
```

---

### Notes & Pitfalls

- **`mode: map` vs `mode: parallel`**  
  - `map` preserves index/item context and returns a **list** of outputs.  
  - `parallel` simply fires N calls and returns an unordered list; use when order doesn’t matter.  

- **`branch` vs `condition`**  
  - Use `branch` to select _which_ step to run next.  
  - Use `condition` to _skip_ a step based on runtime data.  

- **Sub-workflow I/O**  
  - Sub-workflow must accept its own `input` structure; engine inlines it at compile time.  

- **Tool vs Agent**  
  - Tools are deterministic code (e.g. parsing, splitting, DB lookups).  
  - Agents are LLM calls—more expensive, unpredictable, and require prompts.  
