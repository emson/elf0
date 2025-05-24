```markdown
# Task List: Adding Model Context Protocol (MCP) Server Tool Usage in Workflow Agents

## Overview
Enable workflows defined by YAML specs to invoke MCP server tools seamlessly within the existing AI agent framework. This feature allows `tool` nodes in the workflow to call MCP server endpoints as external tools, integrating MCP capabilities into the LangGraph-based execution environment.

---

## Priority-Ordered Task List

- [ ] **1. Extend `Function` Spec Model to Support MCP Tool Invocation**
  - Add or confirm support for `Function.type == "mcp"` with `entrypoint` as MCP URI.
  - Ensure `spec.functions` can register MCP tools by URI.
  - Validate MCP function references during spec validation (`spec.py`).

- [ ] **2. Implement MCP Client Integration in Compiler**
  - Add MCP client initialization and connection logic in `compiler.py`.
  - Modify `load_tool(fn)` or create a specialized loader to detect MCP functions.
  - For MCP tools, implement invocation via MCP client calls instead of local Python calls.
  - Handle serialization/deserialization of inputs/outputs between `WorkflowState` and MCP calls.

- [ ] **3. Update Node Factory Registry to Support MCP Tools**
  - In `NodeFactoryRegistry`, ensure `"tool"` kind nodes referencing MCP functions use the MCP-aware loader.
  - Possibly add a dedicated factory for MCP tools if needed.

- [ ] **4. Enhance Error Handling and Logging for MCP Calls**
  - Add detailed logging for MCP tool invocation attempts and responses.
  - Handle network errors, timeouts, and protocol errors gracefully.
  - Propagate meaningful error messages into `WorkflowState.output` and `error_context`.

- [ ] **5. Update Workflow Spec Examples and Documentation**
  - Provide example YAML spec snippets showing `tool` nodes calling MCP tools via `ref` to MCP functions.
  - Document expected MCP URI format in `Function.entrypoint`.
  - Reference MCP integration guide (`mcp_guide.md`) for users.

- [ ] **6. Add Unit and Integration Tests**
  - Mock MCP server responses to test MCP tool invocation in workflows.
  - Validate correct state updates and error handling.
  - Test fallback behavior when MCP server is unreachable.

- [ ] **7. Optional: Support Dynamic Discovery of MCP Servers**
  - Implement MCP client discovery logic to dynamically find MCP servers at runtime.
  - Allow workflow spec or runtime config to specify MCP server endpoints or discovery parameters.

---

## Summary
This task list guides the incremental integration of MCP server tool usage into the existing AI workflow system. The key is to extend the `Function` spec and node execution logic to support MCP calls transparently, enabling YAML-defined agents to leverage MCP tools as first-class workflow nodes.

By following these prioritized steps, an LLM or developer can implement the feature with clear understanding of required code changes, validation, error handling, and documentation updates.
```