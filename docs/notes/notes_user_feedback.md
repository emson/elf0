 # Creating a User Input Node in a YAML Spec Agent Workflow

 **Prompt:**
 ```
 Create a prompt that will allow a YAML spec agent @docs/project_overview.md @docs_specs/spec_schema.md to prompt the user for input, we need a node that allows the LLM can ask the user a question and wait for the answer, and then incorporate this in the context of the overall process.
```

 ## Overview
 This document provides a detailed guide on how to define a workflow node within a YAML spec that enables an LLM-based agent to **prompt the user for input**, wait for the user's
 response, and then incorporate that input into the workflow's context for subsequent processing. This capability is essential for interactive workflows requiring human-in-the-lo
 input.

 ## Prerequisites
 - Familiarity with the YAML spec schema for agent workflows as defined in the `spec_schema.md`.
 - Python 3.13 environment with dependencies installed (`pydantic` ≥ 2.0.0, `pyyaml`, `typer`, `rich`).
 - Understanding of the CLI tool `elf` for running YAML agent workflows.
 - Basic knowledge of LLM prompt design and state management within workflows.

 ## Scope
 - Defining a **user input node** that pauses execution to receive input.
 - Integrating the user input into the workflow state.
 - Ensuring smooth transition and context propagation in the workflow graph.
 - Using standard node kinds and configurations supported by the YAML spec schema.
 - Providing a minimal working example and explanation.

 ---

 ## Defining a User Input Node in the Workflow

 ### Conceptual Approach
 - Use a **`branch` node** or a dedicated **`agent` node** configured to prompt the user.
 - The node's prompt explicitly asks a question.
 - The workflow engine pauses and waits for user input.
 - The input is captured and stored in the workflow's state (e.g., `state.user_input`).
 - Subsequent nodes can reference this state variable for further processing.

 ### Recommended Node Kind and Configuration

 | Field       | Value / Description                                                                                  |
 |-------------|----------------------------------------------------------------------------------------------------|
 | `id`        | Unique identifier for the node, e.g., `user_prompt`.                                               |
 | `kind`      | Use `"agent"` to leverage LLM prompting capabilities.                                              |
 | `ref`       | Reference to an LLM client defined in the `llms` section, e.g., `chat_llm`.                         |
 | `config`    | Contains the prompt text asking the user a question.                                               |
 | `stop`      | `false` (default) to continue workflow after input is received.                                    |

 ### Example Node Definition

 ```yaml
 workflow:
   type: sequential
   nodes:
     - id: user_prompt
       kind: agent
       ref: chat_llm
       config:
         prompt: |
           Please answer the following question:
           What is your preferred programming language?
       stop: false
     - id: process_input
       kind: agent
       ref: chat_llm
       config:
         prompt: |
           You received the user's input: {state.user_prompt}
           Please provide a summary or next steps based on this input.
       stop: true
   edges:
     - source: user_prompt
       target: process_input
```

---

## Step-by-Step Procedure to Implement User Input Node

 1 Define the LLM Client
   Ensure your llms section includes a valid LLM client, for example:

```yaml
    llms:
      chat_llm:
        type: openai
        model_name: gpt-4o-mini
        temperature: 0.0
        params: {}
```

 2 Add the User Prompt Node
   Create an agent node with a prompt that explicitly asks the user a question.
 3 Enable Input Capture
   The CLI tool or runtime must support interactive input capture for this node. When the node executes, it will display the prompt and wait for user input.
 4 Store User Input in State
   The user's response is automatically stored in the workflow state under the node's id key (e.g., state.user_prompt).
 5 Reference User Input in Subsequent Nodes
   Use {state.user_prompt} or ${state.user_prompt} syntax in prompts or parameters of downstream nodes to incorporate the user's answer.
 6 Define Workflow Edges
   Connect the user prompt node to subsequent nodes to continue processing.
 7 Run the Workflow
   Execute the workflow using the CLI command:
```bash
    elf agent path/to/spec.yaml
```

   The tool will prompt the user at the user_prompt node and wait for input.

---

## Validation Criteria


  Criterion                          Success Indicator
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Node prompts user with question    Prompt text appears clearly in CLI or interactive session.
  Workflow pauses for user input     Execution halts until user provides input.
  User input is captured in state    Input is accessible as state.user_prompt in subsequent nodes.
  Subsequent nodes receive context   Downstream prompts correctly reference and utilize the user input.
  Workflow completes without error   No validation or runtime errors occur during execution.


---

## Additional Notes

 • Interactive Mode: Use elf prompt <spec_path> for an interactive session that naturally supports user input nodes.
 • Input Validation: For advanced use, add validation logic in downstream nodes or via custom Python tools.
 • Branching Based on Input: Use branch nodes with conditions on state.user_prompt to direct workflow paths dynamically.
 • File Reference Syntax: Not applicable for direct user input but can be combined with context files if needed.
 • MCP Nodes: Not required for simple user input prompts.

---

## Complete Minimal YAML Spec Example with User Input Node

```yaml
 version: "0.1"
 description: "Workflow demonstrating user input prompt node"
 runtime: "langgraph"

 llms:
   chat_llm:
     type: openai
     model_name: gpt-4o-mini
     temperature: 0.0
     params: {}

 workflow:
   type: sequential
   nodes:
     - id: user_prompt
       kind: agent
       ref: chat_llm
       config:
         prompt: |
           Please answer the following question:
           What is your preferred programming language?
       stop: false

     - id: process_input
       kind: agent
       ref: chat_llm
       config:
         prompt: |
           You received the user's input: {state.user_prompt}
           Please provide a summary or next steps based on this input.
       stop: true

   edges:
     - source: user_prompt
       target: process_input

```

---

## Troubleshooting


  Issue                                Possible Cause                                           Solution
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Workflow does not pause for input    Runtime or CLI does not support interactive input        Use elf prompt <spec_path> for interactive mode; verify CLI version supports
                                                                                                input nodes
  User input not accessible in state   Incorrect state variable reference or node id mismatch   Confirm node id matches state key used in downstream prompts
  Validation errors on spec file       Missing required fields or invalid node configuration    Validate YAML against schema; ensure workflow.type and required fields are
                                                                                                present
  Unexpected workflow termination      Node marked with stop: true prematurely                  Set stop: false on user input node to continue workflow after input


───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

## References

 • Project Overview: CLI Tool for YAML Agent Workflows
 • Spec YAML Schema Reference
 • MCP Integration and Workflow Composition
 • CLI Commands and Interactive Mode
 • Pydantic Validation and Error Handling




