# Elf0 YAML Specification Principles: Complete LLM Guide

## Overview

This document provides comprehensive principles for creating robust, maintainable, and error-free Elf0 YAML specification files. It synthesizes lessons learned from common failures and provides patterns that work reliably across different use cases.

**Target Audience**: LLMs generating YAML specs, developers creating workflows, and anyone debugging specification issues.

## Core Foundation Principles

### 1. **Mandatory Fields First**
Always start with the absolutely required fields in exactly this order:

```yaml
version: "0.1"                    # REQUIRED: Always use quotes
description: "Brief description"   # OPTIONAL but recommended
runtime: "langgraph"              # REQUIRED: langgraph | agentiq
```

**Critical Rule**: The `workflow.type` field is **ABSOLUTELY MANDATORY** and commonly forgotten. This field determines how the runtime processes the workflow.

### 2. **Progressive Validation Strategy**
Build specs incrementally to catch errors early:

1. **Minimal Valid Spec**: Start with single agent node
2. **Add Components**: One LLM, function, or node at a time
3. **Test Frequently**: Validate after each addition
4. **Complex Patterns Last**: Only add parallelism/custom graphs after basics work

## LLM and Resource Management

### 3. **LLM Definition Principles**

```yaml
# ✅ CORRECT: Complete LLM definition
llms:
  main_agent:                     # Use descriptive names
    type: openai                  # openai | anthropic | ollama
    model_name: gpt-4o-mini       # Verify model availability
    temperature: 0.3              # 0.0-1.0 range
    params:                       # Flat key-value pairs only
      max_tokens: 1000
      
# ❌ WRONG: Common mistakes
llms:
  agent1:                         # Non-descriptive name
    type: openai
    model: gpt-4                  # Wrong field name (should be model_name)
    params:
      response_format:            # Complex nested objects not supported
        type: "json_object"
```

**Model Availability**: Always use commonly available models:
- **OpenAI**: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`
- **Ollama**: `llama2`, `mistral`, `codellama`

### 4. **Function Integration Patterns**

#### State-First Design (Preferred)
```yaml
# ✅ PREFERRED: Let functions access state directly
functions:
  user_input:
    type: python
    name: "User Input Collector"
    entrypoint: "elf0.functions.utils.get_user_input"

workflow:
  nodes:
    - id: collect_input
      kind: tool
      ref: user_input
      # No config/parameters needed - function reads state
```

#### Parameter-Based Design (When Necessary)
```yaml
# ✅ ACCEPTABLE: Explicit parameters for configuration
- id: process_data
  kind: tool
  ref: data_processor
  config:
    parameters:
      operation: "transform"      # Static configuration
      format: "json"             # Not workflow state data
```

**Anti-Pattern**: Avoid complex state variable passing through parameters:
```yaml
# ❌ WRONG: Complex state parameter passing
config:
  parameters:
    prompt: "${state.question}"   # Fragile template substitution
    data: "{state.user_input}"    # Inconsistent syntax
```

## Workflow Design Patterns

### 5. **Sequential Workflow Pattern (Default Choice)**

**Use for**: 90% of workflows including multi-agent interactions, data processing pipelines, and user interactions.

```yaml
workflow:
  type: sequential              # MANDATORY field
  nodes:
    - id: input_processor
      kind: agent
      ref: main_llm
      config:
        prompt: |
          Process user input: "{input}"
          Generate structured output for next step.
    
    - id: task_executor
      kind: agent  
      ref: main_llm
      config:
        prompt: |
          Execute task based on: {state.output}
          Provide detailed results.
    
    - id: final_formatter
      kind: agent
      ref: main_llm
      config:
        prompt: |
          Format final response: {state.output}
          Make it user-friendly and complete.
      stop: true
      
  edges:                        # Optional for sequential - auto-generated
    - source: input_processor
      target: task_executor
    - source: task_executor  
      target: final_formatter
```

### 6. **Input Isolation Principle (Critical)**

**Rule**: Only ONE node should ever consume the raw `{input}` variable.

```yaml
# ✅ CORRECT: Single input consumer
nodes:
  - id: entry_point
    prompt: "Analyze input: {input}"
    output_key: processed_input
    
  - id: next_step
    prompt: "Continue with: {state.processed_input}"

# ❌ WRONG: Multiple input consumers (causes channel conflicts)
nodes:
  - id: agent_a
    prompt: "Process: {input}"
  - id: agent_b  
    prompt: "Also process: {input}"  # VIOLATION!
```

### 7. **State Variable Management**

#### State Flow Rules
1. **Previous Node Output**: Access via `{state.output}`
2. **Specific Keys**: Use `output_key` for custom state variables
3. **State Accumulation**: Each node adds to state, doesn't replace it

```yaml
# ✅ CORRECT: Proper state management
- id: data_analyzer
  kind: agent
  ref: analyzer_llm
  config:
    prompt: "Analyze: {input}"
  output_key: analysis_result

- id: decision_maker
  kind: agent
  ref: decision_llm  
  config:
    prompt: |
      Based on analysis: {state.analysis_result}
      Make a decision about next steps.
  output_key: decision

- id: action_executor
  kind: agent
  ref: executor_llm
  config:
    prompt: |
      Execute this decision: {state.decision}
      Original analysis: {state.analysis_result}
      Provide execution results.
  stop: true
```

### 8. **Custom Graph Patterns (Advanced)**

**Use only when you need**: True parallelism, complex routing, or dynamic workflows.

#### Safe Fan-out → Fan-in Pattern
```yaml
workflow:
  type: custom_graph
  nodes:
    - id: input_distributor
      kind: agent
      ref: coordinator_llm
      config:
        prompt: "Distribute task: {input}"
      output_key: distributed_task
      
    - id: specialist_a
      kind: agent
      ref: specialist_llm
      config:
        prompt: "Handle aspect A: {state.distributed_task}"
      output_key: result_a
      
    - id: specialist_b
      kind: agent  
      ref: specialist_llm
      config:
        prompt: "Handle aspect B: {state.distributed_task}"
      output_key: result_b
      
    - id: result_synthesizer
      kind: agent
      ref: synthesizer_llm
      config:
        prompt: |
          Combine results:
          Specialist A: {state.result_a}
          Specialist B: {state.result_b}
          Original task: {state.distributed_task}
      stop: true
      
  edges:
    - source: input_distributor
      target: specialist_a
    - source: input_distributor
      target: specialist_b
    - source: specialist_a
      target: result_synthesizer
    - source: specialist_b
      target: result_synthesizer
```

## Advanced Integration Patterns

### 9. **MCP Integration (Modern Pattern)**

```yaml
# ✅ MODERN: Direct MCP nodes (preferred)
workflow:
  nodes:
    - id: calculator
      kind: mcp
      config:
        server:
          command: ["python", "mcp/calculator/server.py"]
          cwd: "/path/to/project"
        tool: "calculate"
        parameters:
          a: "${state.json.number_a}"
          b: "${state.json.number_b}"
          operation: "${state.json.operation}"

# ❌ LEGACY: MCP functions (deprecated)
functions:
  calc_tool:
    type: mcp
    entrypoint: "mcp://localhost:3000/calculate"
```

### 10. **Interactive User Input Patterns**

```yaml
# ✅ GENERIC INTERACTIVE PATTERN
workflow:
  type: sequential
  nodes:
    - id: generate_question
      kind: agent
      ref: assistant
      config:
        prompt: |
          Based on: "{input}"
          What additional information do you need?
          Generate ONE specific question.
          Output only the question text.
    
    - id: collect_user_response
      kind: tool
      ref: get_user_input
      # No parameters - function uses state.output for question
    
    - id: generate_final_response
      kind: agent
      ref: assistant
      config:
        prompt: |
          Original request: "{input}"
          Question asked: {state.output}
          User response: {state.user_input}
          Provide comprehensive final answer.
      stop: true
```

## Error Prevention and Edge Cases

### 11. **Validation Checklist**

Before creating any YAML spec, verify:

#### Required Fields
- [ ] `version` is present and quoted
- [ ] `runtime` is specified
- [ ] `workflow.type` is specified (most common error)
- [ ] At least one LLM is defined in `llms` section
- [ ] All node `ref` fields point to existing LLMs/functions
- [ ] At least one node has `stop: true`

#### State Management
- [ ] Only one node consumes `{input}`
- [ ] All `output_key` values are unique
- [ ] State references use consistent syntax: `{state.variable_name}`
- [ ] No empty prompt template sections

#### Graph Structure
- [ ] All edge `source` and `target` refer to existing node IDs
- [ ] No unreachable nodes (orphans)
- [ ] No infinite loops in edge definitions
- [ ] Custom graphs have proper convergence points

### 12. **Common Error Patterns and Fixes**

#### Channel Conflict Errors
```yaml
# ERROR: INVALID_CONCURRENT_GRAPH_UPDATE
# CAUSE: Multiple nodes receiving input simultaneously

# ❌ PROBLEMATIC PATTERN
edges:
  - source: start_node
    target: agent_a
  - source: start_node    # Fan-out without proper state management
    target: agent_b
  
# ✅ SOLUTION: Sequential with state passing
edges:
  - source: start_node
    target: coordinator
  - source: coordinator
    target: agent_a
  - source: agent_a
    target: agent_b
```

#### Reference Errors
```yaml
# ERROR: Node references unknown LLM/function
# ❌ WRONG: Undefined reference
nodes:
  - id: my_agent
    kind: agent
    ref: undefined_llm    # Not in llms section

# ✅ CORRECT: Valid reference
llms:
  main_llm:
    type: openai
    model_name: gpt-4o-mini
    
nodes:
  - id: my_agent
    kind: agent
    ref: main_llm
```

#### Template Variable Errors
```yaml
# ❌ WRONG: Malformed template variables
prompt: |
  Process input: {input}
  Previous result: {state.previous_result
  Context: {state.}

# ✅ CORRECT: Proper template syntax
prompt: |
  Process input: {input}
  Previous result: {state.previous_result}
  Context: {state.context_data}
```

### 13. **Performance and Resource Principles**

#### Model Selection Strategy
```yaml
# Fast + Cheap for simple tasks
model_name: gpt-4o-mini
temperature: 0.1

# Powerful for complex reasoning
model_name: gpt-4o  
temperature: 0.3

# Local for privacy/offline
type: ollama
model_name: llama2
```

#### Workflow Optimization
```yaml
# ✅ EFFICIENT: Minimal necessary steps
nodes:
  - id: process
  - id: validate  
  - id: output

# ❌ INEFFICIENT: Unnecessary complexity  
nodes:
  - id: pre_process
  - id: process
  - id: post_process
  - id: validate
  - id: re_validate
  - id: format
  - id: post_format
  - id: output
```

## Security and Safety Principles

### 14. **Input Sanitization**
```yaml
# ✅ SAFE: Validate and sanitize input
- id: input_validator
  kind: agent
  ref: validator_llm
  config:
    prompt: |
      Validate and sanitize this input: "{input}"
      Ensure it contains no harmful content.
      Output cleaned version or reject if unsafe.
```

### 15. **Function Security**
```yaml
# ✅ SAFE: Use only trusted function entrypoints
functions:
  safe_processor:
    type: python
    entrypoint: "elf0.functions.verified.safe_processor"

# ❌ RISKY: Arbitrary or untrusted code
functions:
  risky_tool:
    entrypoint: "random_package.untrusted_function"
```

## Testing and Debugging Strategies

### 16. **Progressive Testing Pattern**

```yaml
# Step 1: Minimal working spec
version: "0.1"
runtime: "langgraph"
llms:
  test_llm:
    type: openai
    model_name: gpt-4o-mini
workflow:
  type: sequential
  nodes:
    - id: simple_test
      kind: agent
      ref: test_llm
      stop: true

# Step 2: Add one component at a time
# Step 3: Test after each addition
# Step 4: Add complexity only when basics work
```

### 17. **Debug Information Strategy**

```yaml
# Add debug nodes during development
- id: debug_state
  kind: agent
  ref: debug_llm
  config:
    prompt: |
      Debug state inspection:
      Current state keys: {state.keys()}
      Input: {input}
      Previous output: {state.output}
      Generate summary of current workflow state.
  output_key: debug_info
```

## Specialized Use Case Patterns

### 18. **Multi-Agent Simulation**
```yaml
# ✅ EFFECTIVE: Sequential simulation creating agent interaction illusion
workflow:
  type: sequential
  nodes:
    - id: scenario_setup
      prompt: "Setup scenario: {input}"
      
    - id: agent_alice
      prompt: |
        You are Alice in this scenario: {state.output}
        React and respond naturally.
        
    - id: agent_bob  
      prompt: |
        You are Bob. Alice just said: {state.output}
        In scenario: {state.scenario_setup}
        Respond to Alice naturally.
        
    - id: agent_alice_response
      prompt: |
        You are Alice. Bob responded: {state.output}
        Continue the conversation naturally.
        
    - id: simulation_summary
      prompt: |
        Summarize this agent interaction:
        Scenario: {state.scenario_setup}
        Full conversation context from previous exchanges.
      stop: true
```

### 19. **Data Processing Pipeline**
```yaml
workflow:
  type: sequential
  nodes:
    - id: data_ingestion
      kind: agent
      ref: processor_llm
      config:
        prompt: "Ingest and structure: {input}"
      output_key: structured_data
      
    - id: data_validation
      kind: tool
      ref: validator_function
      
    - id: data_transformation
      kind: agent
      ref: transformer_llm
      config:
        prompt: |
          Transform validated data: {state.output}
          Original structure: {state.structured_data}
      output_key: transformed_data
      
    - id: output_formatting
      kind: agent
      ref: formatter_llm
      config:
        prompt: "Format final output: {state.transformed_data}"
      stop: true
```

### 20. **Conditional Workflow**
```yaml
workflow:
  type: custom_graph
  nodes:
    - id: decision_point
      kind: agent
      ref: decision_llm
      config:
        prompt: |
          Analyze: {input}
          Route to: "technical" or "creative" or "general"
          Output only the routing decision.
      output_key: routing_decision
      
    - id: technical_handler
      kind: agent
      ref: technical_llm
      config:
        prompt: "Handle technical query: {state.routing_decision}"
      output_key: technical_result
      
    - id: creative_handler
      kind: agent
      ref: creative_llm
      config:
        prompt: "Handle creative query: {state.routing_decision}"
      output_key: creative_result
      
    - id: general_handler
      kind: agent
      ref: general_llm
      config:
        prompt: "Handle general query: {state.routing_decision}"
      output_key: general_result
      
  edges:
    - source: decision_point
      target: technical_handler
      condition: "'technical' in state.routing_decision.lower()"
    - source: decision_point
      target: creative_handler  
      condition: "'creative' in state.routing_decision.lower()"
    - source: decision_point
      target: general_handler
      condition: "'general' in state.routing_decision.lower()"
```

## Anti-Patterns and What to Avoid

### 21. **Critical Anti-Patterns**

```yaml
# ❌ NEVER DO: Multiple input consumers
nodes:
  - id: agent_a
    prompt: "{input}"
  - id: agent_b
    prompt: "{input}"

# ❌ NEVER DO: Conflicting output keys
nodes:
  - id: agent_a
    output_key: "result"
  - id: agent_b
    output_key: "result"

# ❌ NEVER DO: Empty or incomplete references
nodes:
  - id: broken_node
    prompt: |
      Context: {state.}
      Data: 
      Process: {state.nonexistent}

# ❌ NEVER DO: Complex parameter passing
config:
  parameters:
    complex_data: "${state.nested.deep.value}"
    template_string: "Process {state.var} with {state.other}"

# ❌ NEVER DO: Missing required fields
workflow:
  # Missing type field!
  nodes:
    - id: node1
      kind: agent
      # Missing ref field!
```

## Quick Reference Checklist

### Pre-Creation Checklist
- [ ] Understand the use case (sequential vs parallel needs)
- [ ] Choose appropriate LLM models for the task
- [ ] Design state flow before writing YAML
- [ ] Plan testing strategy

### During Creation Checklist  
- [ ] Start with minimal working spec
- [ ] Add required fields first
- [ ] Use descriptive IDs and names
- [ ] Follow input isolation principle
- [ ] Design unique output keys
- [ ] Test incrementally

### Post-Creation Validation
- [ ] All required fields present
- [ ] No orphaned or unreachable nodes
- [ ] State references are complete
- [ ] Edge sources/targets exist
- [ ] No anti-patterns present
- [ ] Test with real inputs

## Summary: Golden Rules for LLMs

When generating YAML specifications:

1. **Start Simple**: Begin with sequential workflow pattern
2. **Required Fields First**: `version`, `runtime`, `workflow.type` are mandatory
3. **One Input Consumer**: Only first node uses `{input}`
4. **State Flow**: Use `{state.output}` for previous node results
5. **Unique Keys**: Every `output_key` must be unique
6. **Valid References**: All `ref` fields must point to defined LLMs/functions
7. **Complete Templates**: No empty `{state.}` or malformed variables
8. **Test Incrementally**: Build and test in small steps
9. **Avoid Complexity**: Use custom graphs only when truly needed
10. **Follow Patterns**: Use proven patterns from this document

**Remember**: A working simple specification is infinitely better than a broken complex one. Start minimal, test frequently, and add complexity only when the basics work perfectly.