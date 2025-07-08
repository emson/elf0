# Workflow Structure (`workflow`)

The `workflow` section is the heart of your agent specification, defining the sequence or graph of operations. It's where you lay out the nodes (steps) and edges (transitions) that constitute your agent's behavior.

```yaml
workflow:
  type: <string>        # REQUIRED: sequential | react | evaluator_optimizer | custom_graph
  nodes: <list>         # REQUIRED: List of WorkflowNode objects
  edges: <list>         # REQUIRED: List of Edge objects
  max_iterations: <int> # Optional: For workflows with loops, max times to repeat
```

**CRITICAL**: The `workflow.type` field is **mandatory**. It determines how the runtime engine processes the nodes and edges. Refer to `docs/flow_rules.md` for guidance on choosing the correct type based on your edge patterns (e.g., sequential vs. fan-out/fan-in for custom_graph).

---

## Nodes (`workflow.nodes`)

Nodes are the building blocks of your workflow, representing individual tasks or processing steps. Each node in the `nodes` list is an object with the following common fields:

-   `id` (string, **Required**): A unique identifier for this node within the workflow. This ID is used in `edges` to connect nodes.
-   `kind` (string, **Required**): Defines the type and behavior of the node. See detailed descriptions for each kind below.
-   `ref` (string, Optional/Required): Typically references a named configuration from top-level sections like `llms` or `functions`.
    -   **Required** for `agent`, `tool`, and `judge` nodes.
    -   **Not used** for `mcp` nodes (MCP configuration is entirely within `config`).
    -   Optional for `branch` nodes (as branching logic might be self-contained or simple).
-   `config` (object, Optional/Required): A flexible object for node-specific settings.
    -   **Required** for `mcp` nodes.
    -   Commonly used in `agent` and `judge` nodes for `prompt` and `output_key`.
    -   Used in `tool` nodes if the tool itself requires specific parameters not covered by its `Function` definition.
-   `stop` (bool, Optional, default: `false`): If `true`, the workflow (or the current path in a `custom_graph`) will terminate after this node executes. See Rule 5 in `docs/flow_rules.md`.

### Node Kinds

#### 1. `agent`

-   **Purpose**: For all LLM-based processing. This includes tasks like analyzing input, generating text, making decisions based on prompts, simulating personas, or any operation that involves sending a prompt to an LLM.
-   **`ref`**: **Required**. Must point to a valid LLM name defined in the top-level `llms` section.
-   **`config`**:
    -   `prompt` (string, **Required**): The prompt template to be sent to the LLM. Can include placeholders like `{workflow_initial_input}` (for the very first agent node in a workflow - see Rule 1 in `docs/flow_rules.md`) or `{state.variable_name}` to inject data from previous nodes (see Rule 3 in `docs/flow_rules.md`).
    -   `output_key` (string, **Required if output is used by other nodes**): The key under which this agent's output (the LLM's response) will be stored in the workflow state, accessible by subsequent nodes via `{state.your_output_key}`. See Rule 2 in `docs/flow_rules.md`.

    ```yaml
    - id: analyze_request
      kind: agent
      ref: analysis_llm # Defined in top-level llms section
      config:
        prompt: "Analyze the following user request: {workflow_initial_input}"
        output_key: analysis_result
    ```

#### 2. `tool`

-   **Purpose**: To execute pre-defined external functions, typically Python code. These are for deterministic operations or interactions with external systems not covered by MCP.
-   **`ref`**: **Required**. Must point to a valid function name defined in the top-level `functions` section (where `type` is `python`).
-   **`config`**:
    -   `output_key` (string, **Required if output is used by other nodes**): The key for storing the tool's return value in the workflow state.
    -   `parameters` (object, Optional): If the Python function expects specific arguments, they can sometimes be mapped here from the workflow state. (This depends on the tool runner implementation).

    ```yaml
    # Assumes in top-level functions:
    # functions:
    #   my_data_processor:
    #     type: python
    #     name: "Data Processor Tool"
    #     entrypoint: "my_module.my_data_processing_function"

    # In workflow.nodes:
    - id: process_data_step
      kind: tool
      ref: my_data_processor
      config:
        output_key: processed_data_output
        # Example: parameters might be passed if tool runner supports it
        # parameters:
        #   input_value: "{state.some_previous_data}"
    ```
    *Note: Parameter passing to `tool` nodes is highly dependent on the specific runtime implementation for Python function execution.*

#### 3. `judge`

-   **Purpose**: For LLM-based evaluation or scoring. A `judge` node typically takes the output of another node and uses an LLM to assess its quality, correctness, or adherence to certain criteria, often outputting a structured response (e.g., JSON with a score).
-   **`ref`**: **Required**. Must point to a valid LLM name defined in the `llms` section, usually one configured for evaluation tasks (e.g., specific prompt, temperature for consistency).
-   **`config`**:
    -   `prompt` (string, **Required**): The prompt template for the evaluation. It will typically include a placeholder (e.g., `{state.output_to_evaluate}`) to receive the data that needs judging.
    -   `output_key` (string, **Required if output is used by other nodes**): The key for the judge's assessment (the LLM's response to the evaluation prompt). This might be a JSON string containing a score, reasoning, etc.
    -   The prompt should guide the LLM to produce a parseable output, often JSON, e.g., `{"score": 0.8, "reasoning": "..."}`.

    ```yaml
    - id: evaluate_summary_quality
      kind: judge
      ref: evaluator_llm # Defined in top-level llms section
      config:
        prompt: |
          Evaluate the quality of this summary: {state.generated_summary}
          Return a JSON object with keys "score" (0.0-1.0) and "feedback" (string).
        output_key: evaluation_feedback
    ```

#### 4. `branch`

-   **Purpose**: To introduce conditional logic and routing into the workflow, enabling different paths based on the current state. This is essential for `custom_graph` workflows that aren't strictly sequential.
-   **`ref`**: Optional. Not typically used, as branching logic is usually defined by `edges` originating from this node, which have `condition` fields.
-   **`config`**: Optional. Might be used if the branching node itself needs to perform some minor state transformation or preparation before conditions on outgoing edges are evaluated. Usually, the state used by conditions is prepared by nodes *preceding* the branch node.
-   **Behavior**: A `branch` node itself usually doesn't perform a major state-altering operation. Its primary role is to be a point from which multiple conditional `edges` can diverge. The conditions on these outgoing edges determine the next node to execute.

    ```yaml
    # Node itself is simple:
    - id: main_decision_point
      kind: branch

    # Logic is primarily in the edges *originating from* this branch node (see Edges section).
    # Example edges for this branch node:
    # - source: main_decision_point
    #   target: high_priority_path
    #   condition: "state.get('priority_level') == 'high'"
    # - source: main_decision_point
    #   target: default_path
    #   condition: "state.get('priority_level') != 'high'"
    ```

#### 5. `mcp` (Model Context Protocol)

-   **Purpose**: For direct integration with external tools and services via the Model Context Protocol. This is the recommended way to call external, potentially long-running or stateful, tools like calculators, database query engines, file system tools, etc. See Rule 8 in `docs/flow_rules.md` for when to choose `mcp` over `agent`.
-   **`ref`**: **Not used**. All MCP configuration is within the `config` block.
-   **`config`** (**Required**, and has specific sub-fields):
    -   `server` (object, **Required**): Defines how to start and manage the MCP server.
        -   `command` (list of strings, **Required**): The command and arguments to execute to start the MCP server (e.g., `["python", "mcp_servers/my_calculator_server.py"]`).
        -   `cwd` (string, Optional): The working directory from which to run the server command.
    -   `tool` (string, **Required**): The name of the specific tool/function to call on the MCP server (e.g., `"add"`, `"query_database"`).
    -   `parameters` (object, Optional): A key-value map of parameters to pass to the MCP tool. Supports dynamic value injection from the workflow state using `${state.variable_name}` or `${state.json.field_name}` for extracting from JSON strings. (See `docs_specs/spec_schema.md` for details on MCP parameter binding).
    -   `output_key` (string, **Required if output is used by other nodes**): The key for storing the result from the MCP tool call in the workflow state.

    ```yaml
    - id: execute_external_calculator
      kind: mcp
      config:
        server:
          command: ["python", "mcp_services/calculator.py"]
          # cwd: "/opt/mcp/services" # Optional working directory
        tool: "multiply" # Name of the tool on the MCP server
        parameters:
          value1: "${state.first_operand}"
          value2: "${state.second_operand}"
        output_key: multiplication_result
    ```
    *Refer to the "MCP Nodes" section in `docs_specs/spec_schema.md` for more detailed examples and parameter binding syntax like `${state.json.field}`.*

---

## Edges (`workflow.edges`)

Edges define the transitions and control flow between nodes in your workflow. Each edge in the `edges` list is an object:

-   `source` (string, **Required**): The `id` of the node from which this edge originates.
-   `target` (string, **Required**): The `id` of the node to which this edge leads.
-   `condition` (string, Optional): A Python-like expression string that is evaluated against the current workflow state. If the condition evaluates to `true`, this edge is traversed. If omitted, the edge is considered unconditional.
    -   **Syntax**: Expressions can access workflow state variables using `state.get('variable_name', default_value)` or direct dictionary access like `state['variable_name']` if the key is guaranteed to exist. Examples:
        -   `"state.get('user_intent') == 'purchase'"`
        -   `"state.get('confidence_score', 0) > 0.75"`
        -   `"state.get('requires_approval')"` (evaluates to true if `requires_approval` exists in state and is truthy, e.g., `True`, non-empty string/list).
    -   If multiple conditional edges originate from the same `source` node, the runtime will typically evaluate them in the order they are listed or based on specific router logic. It takes the first one whose condition is met. Ensure conditions are logically structured (e.g., mutually exclusive if order-independent behavior is intended, or provide a fallback unconditional edge if no conditions might match).
    -   For `workflow.type: sequential`, edges are typically unconditional and simply link nodes in order. The `edges` list can sometimes be automatically inferred by the runtime if nodes are listed sequentially and no complex routing is needed, though explicitly defining them is always clearer and safer.
    -   For `workflow.type: custom_graph`, conditions are crucial for implementing branching, merging, and looping logic.

```yaml
edges:
  # Example of an unconditional edge in a sequential or custom_graph flow
  - source: data_ingestion_node
    target: data_processing_node

  # Example of conditional edges for a branch
  - source: decision_making_node # This would be a 'branch' kind node typically
    target: approval_path_node
    condition: "state.get('is_approved') == True"
  - source: decision_making_node
    target: rejection_path_node
    condition: "state.get('is_approved') == False"

  # Example of a fallback edge (could be unconditional or a final catch-all condition)
  - source: complex_routing_node
    target: error_handling_node 
    # condition: "state.get('status') == 'error'" # Or simply no condition if it's the last edge
```

This detailed structure, in conjunction with `docs_specs/spec_schema.md` and `docs/flow_rules.md`, should provide a solid foundation for LLMs to understand how to construct valid and meaningful workflow YAML files. 