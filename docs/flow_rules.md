## Agent Workflow YAML: Data Flow & State Management Rules

This document outlines critical rules for defining how data flows between nodes and how state is managed within agent workflow YAML specifications. Adhering to these rules is essential for creating robust and error-free workflows, especially those involving custom graphs with parallel execution or sequential chains.

**Core Principle:** Be explicit about data. The runtime needs to know exactly where data comes from and where it goes.

> **Placeholder Convention**  
> Throughout this document we illustrate the first‑node placeholder for the initial user input with `{workflow_initial_input}`.  
> **Do NOT copy `{workflow_initial_input}` into production YAML.** Replace it with the engine’s reserved token—curly braces around the word *input* — when you implement your first node.  
> Using a surrogate token here prevents the documentation itself from being mistaken as executable YAML when it is provided to an LLM alongside live specs.

### Rule 1: Initial Workflow Input

*   **1.1.** The very first node in your workflow (the entry point) that needs to process the initial user prompt or input provided to the entire workflow **MUST** use the specific placeholder for initial workflow input (i.e., curly braces around the word 'input') in its `config.prompt` field to receive this data.
    *   **Note on Examples:** In the YAML examples below (and throughout this document), `"{workflow_initial_input}"` is used to represent where the overall workflow input is consumed. When implementing your *actual first node*, you **MUST** use the literal placeholder for initial input (curly braces around 'input').
    *   **Example (Illustrative - see note above):**
        ```yaml
        nodes:
          - id: initial_processing_node
            kind: agent
            ref: some_llm
            config:
              prompt: "Analyze this user request: {workflow_initial_input}" # In actual YAML, replace {workflow_initial_input} with the placeholder for initial input (curly braces around the word input)
              output_key: processed_request
        ```
    *   **Why:** The workflow runtime automatically makes the initial overall input available via the literal reserved input placeholder. Using any other placeholder (e.g., `{user_prompt}`, `{initial_data}`) for this purpose in the actual first node will lead to warnings and unpredictable input handling. The use of `"{workflow_initial_input}"` in these rules is to prevent parsing issues when this document itself is processed as context by an LLM that might be sensitive to the literal placeholder string appearing in example code when it also needs to process `{state.variable}` placeholders.

### Rule 2: Defining Node Outputs (State Variables)

*   **2.1.** Every node that produces a result intended for use by subsequent nodes **MUST** define an `output_key` in its `config` section.
    *   **Example (Correct):**
        ```yaml
        nodes:
          - id: data_generator_node
            kind: agent
            ref: an_llm
            config:
              prompt: "Generate data based on {state.previous_step_output}."
              output_key: my_generated_data # This stores the node's output in state.my_generated_data
        ```
*   **2.2.** The value of `output_key` should be a descriptive, unique string (e.g., `customer_summary`, `analysis_result`, `ceo_decision`). This string becomes the key under which the node's output is stored in the workflow's shared state.
    *   **Why:** Without an `output_key`, the node's result is transient or implicitly handled, making it difficult for other nodes to reliably access it, especially in complex graphs. Explicitly naming outputs prevents ambiguity and errors like those seen with parallel branches trying to access unnamed or poorly scoped data.

### Rule 3: Referencing Node Outputs (Consuming State Variables)

*   **3.1.** When a node's prompt needs to consume the output of a *previous* node, it **MUST** reference that output using the format `{state.your_output_key_name}` within its `config.prompt`. It can also reference the initial workflow input using the reserved input placeholder if needed (assuming the first node didn't consume/overwrite it, or if it was explicitly passed through).
    *   **Example (Correct):**
        ```yaml
        nodes:
          - id: first_step
            kind: agent
            ref: llm_1
            config:
              prompt: "Initial processing of: {workflow_initial_input}" # In actual YAML, replace {workflow_initial_input} with the placeholder for initial input (curly braces around the word input)   
              output_key: first_step_output                             
          - id: second_step                                             
            kind: agent                                                 
            ref: llm_2                                                  
            config:                                                     
              prompt: "Now process the result from the first step: {state.first_step_output}"
              output_key: second_step_output
        ```
    *   **Why:** The `{state.your_output_key_name}` syntax tells the runtime to fetch the value associated with `your_output_key_name` from the shared workflow state and inject it into the prompt. This is the only reliable way to pass data between nodes.
*   **3.2.** Ensure the `your_output_key_name` exactly matches an `output_key` defined in an earlier node that has already executed in the workflow path leading to the current node.
    *   **Why:** Referencing a non-existent state key will lead to errors or missing data in the prompt.

### Rule 4: Handling Parallel Execution (Fan-Out)

*   **4.1.** When one node's output (`Node A`) is intended to be the input for multiple subsequent nodes (`Node B`, `Node C`, `Node D`) that can run in parallel:
    *   `Node A` **MUST** use `output_key` to store its result (e.g., `output_key: common_data_for_parallel_nodes`).
    *   Each parallel node (`Node B`, `Node C`, `Node D`) **MUST** reference this specific output in their prompts using the `{state.common_data_for_parallel_nodes}` syntax.
    *   **Example (Correct):**
        ```yaml
        # ... (llms definition) ...
        workflow:
          type: custom_graph
          nodes:
            - id: data_preparation_node # Node A
              kind: agent
              ref: main_llm
              config:
                prompt: "Prepare data from: {workflow_initial_input}" # In actual YAML, replace {workflow_initial_input} with the placeholder for initial input (curly braces around the word input)
                output_key: prepared_data
            - id: process_data_type_x # Node B
              kind: agent
              ref: main_llm
              config:
                prompt: "Process prepared data for type X: {state.prepared_data}"
                output_key: result_x
            - id: process_data_type_y # Node C
              kind: agent
              ref: main_llm
              config:
                prompt: "Process prepared data for type Y: {state.prepared_data}"
                output_key: result_y
            # ... potentially a merge node here ...
          edges:
            - source: data_preparation_node
              target: process_data_type_x
            - source: data_preparation_node
              target: process_data_type_y
            # ... other edges ...
        ```
    *   **Why:** This ensures that each parallel branch receives the same, correctly scoped input derived from the preceding node. Trying to implicitly pass data or relying on a generic reserved input placeholder for parallel branches will cause errors like "Can receive only one value per step" because the runtime cannot determine how to distribute or manage the state for concurrent operations without these explicit instructions.

### Rule 5: Terminating Nodes (Stop Points)

*   **5.1.** Clearly mark nodes that represent the end of a workflow or a significant branch by setting `stop: true` in the node definition.
    *   **Example (Correct):
        ```yaml
        nodes:
          - id: final_summary_node
            kind: agent
            ref: an_llm
            stop: true
            config:
              prompt: "Summarize all findings: {state.aggregated_results}"
              output_key: final_report
        ```
    *   **Why:** While not directly related to data flow errors of the type just debugged, it's good practice for workflow clarity and helps the runtime understand execution completion points, which can be relevant for resource management and state finalization in more complex scenarios.

### Rule 6: Avoiding Compiler Input Append Behavior

*   **6.1.** For nodes that consume ONLY state variables (not the initial workflow input), ensure their prompts do NOT trigger the compiler's automatic input appending behavior.
    *   **Context:** The ELF compiler has specific behavior: if a node's prompt doesn't contain the reserved input placeholder, it will automatically append the raw user input to the prompt. This can cause issues in parallel execution scenarios.
    *   **Example (Correct - node using only state variables):**
        ```yaml
        nodes:
          - id: process_analysis
            kind: agent
            ref: main_llm
            config:
              prompt: |
                Based on the analysis: {state.analysis_result}
                Generate a summary focusing on key findings.
              output_key: summary
        ```
    *   **Example (Incorrect - will trigger unwanted input appending):**
        ```yaml
        nodes:
          - id: process_analysis
            kind: agent
            ref: main_llm
            config:
              prompt: |
                Based on the analysis: {state.analysis_result}
                # Missing any reference to the reserved input placeholder, compiler will append raw input
              output_key: summary
        ```
    *   **Why:** When multiple nodes run in parallel and all receive the appended raw input due to this compiler behavior, it can cause "Can receive only one value per step" errors in the state management system. Nodes should be explicit about whether they need the initial input or only state variables.

### Rule 7: Workflow Type Must Match Edge Pattern

*   **7.1.** The `workflow.type` field MUST accurately reflect the actual edge pattern in your workflow.
    *   **Sequential Type Requirements:** If `workflow.type: sequential`, the edges must form a strict chain where each node has at most one outgoing edge to the next node (A→B→C→D).
    *   **Custom Graph Type Requirements:** If your workflow has ANY of the following patterns, you MUST use `workflow.type: custom_graph`:
        - Fan-out: One node connecting to multiple nodes (e.g., A→B,C,D)
        - Fan-in: Multiple nodes connecting to one node (e.g., B,C,D→E)
        - Any form of parallel execution
        - Complex routing or conditional branching
        - Non-linear flow patterns
    *   **Example (Incorrect - type mismatch):**
        ```yaml
        workflow:
          type: sequential  # WRONG! This has fan-out pattern
          nodes:
            - id: input_processor
              # ... node config ...
            - id: parallel_task_1
              # ... node config ...
            - id: parallel_task_2
              # ... node config ...
          edges:
            - source: input_processor
              target: parallel_task_1
            - source: input_processor
              target: parallel_task_2  # Fan-out pattern requires custom_graph!
        ```
    *   **Example (Correct - matching type and pattern):**
        ```yaml
        workflow:
          type: custom_graph  # Correct for fan-out pattern
          nodes:
            - id: input_processor
              # ... node config ...
            - id: parallel_task_1
              # ... node config ...
            - id: parallel_task_2
              # ... node config ...
            - id: aggregator
              # ... node config ...
          edges:
            - source: input_processor
              target: parallel_task_1
            - source: input_processor
              target: parallel_task_2
            - source: parallel_task_1
              target: aggregator
            - source: parallel_task_2
              target: aggregator
        ```
    *   **Why:** Mismatched workflow types and edge patterns cause runtime errors. The execution engine uses the workflow type to determine how to process nodes. A "sequential" type expects linear execution, while parallel patterns require "custom_graph" to handle concurrent state updates properly.

### Rule 8: Choosing the Correct Node Type

*   **8.1.** **Agent Nodes (`kind: agent`)** should be used for ALL LLM-based processing, including:
    - Processing the initial workflow input
    - Text generation, analysis, or reasoning
    - Persona simulation or role-playing
    - Any task that requires sending a prompt to an LLM
    
*   **8.2.** **MCP Nodes (`kind: mcp`)** should ONLY be used for external tool integration:
    - Calling calculators, databases, or file systems
    - Integrating with external APIs via MCP servers  
    - Any task that requires executing external tools, not LLM processing
    - MCP nodes require both `server` and `tool` configurations in their `config`
    
*   **8.3.** **Common Mistake to Avoid:** Do NOT use MCP nodes for input processing or text generation. If you need to process user input or generate responses, use `agent` nodes.
    
    *   **Example (Incorrect - using MCP for input processing):**
        ```yaml
        nodes:
          - id: input_processor
            kind: mcp  # WRONG! This should be 'agent'
            config:
              output_key: processed_input
        ```
        
    *   **Example (Correct - using agent for input processing):**
        ```yaml
        nodes:
          - id: input_processor
            kind: agent  # Correct for LLM-based processing
            ref: main_llm
            config:
              prompt: "Process this input: {workflow_initial_input}" # In actual YAML, replace {workflow_initial_input} with the placeholder for initial input (curly braces around the word input)   
              output_key: processed_input
        ```
        
*   **Why:** Mixing up node types leads to validation errors and workflow failures. Each node type has specific requirements and purposes. Using the wrong type will cause the workflow compiler to fail with configuration errors.

By strictly following these rules, LLMs (and human developers) can construct YAML agent workflows that are more robust, predictable, and less prone to data flow and state management errors, particularly when dealing with the Langchain backend.