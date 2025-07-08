# Custom Graph Agent Design Principles: Preventing Channel Conflicts

## Overview

While sequential workflows are safer and simpler, there are legitimate use cases for `custom_graph` workflows in LangGraph. This document outlines how to properly design custom graph YAML agents that avoid channel conflicts while leveraging parallel execution and complex routing.

## When to Use Custom Graphs

**Use custom graphs when you need:**
- True parallel execution of independent agents
- Complex conditional routing based on state
- Dynamic workflow patterns that can't be expressed linearly
- Multi-agent collaboration with different interaction patterns

**Stick with sequential when you have:**
- Linear processing workflows
- Simple multi-step simulations
- Sequential agent interactions
- Single-path decision flows

## LangGraph Custom Graph Architecture

### State Management Foundation

LangGraph uses a shared state system where:
- **State**: A shared data structure (TypedDict or Pydantic model)
- **Nodes**: Functions that read and update state
- **Edges**: Define execution flow and routing
- **Reducers**: Functions that handle concurrent state updates

### Key Technical Concepts

#### 1. State Channels and Reducers

```yaml
# Problem: Multiple nodes updating same key without reducer
state_key: "value"  # Default override behavior

# Solution: Use distinct keys or understand reducer behavior
node_a_output: "value_a"
node_b_output: "value_b"
```

#### 2. Concurrent Updates

LangGraph executes nodes in "super-steps" where:
- All nodes ready to execute run in parallel
- State updates are collected and applied via reducers
- Next super-step begins with updated state

## Custom Graph Design Patterns

### 1. Fan-out → Fan-in Pattern (SAFE)

```yaml
workflow:
  type: "custom_graph"
  nodes:
    - id: "input_processor"
      prompt: "Process input: {input}"
      output_key: "processed_input"
      
    - id: "agent_a"
      prompt: "Analyze: {state.processed_input}"
      output_key: "analysis_a"
      
    - id: "agent_b"  
      prompt: "Evaluate: {state.processed_input}"
      output_key: "analysis_b"
      
    - id: "synthesizer"
      prompt: |
        Combine insights:
        Analysis A: {state.analysis_a}
        Analysis B: {state.analysis_b}
      output_key: "final_result"
      
  edges:
    - source: "input_processor"
      target: "agent_a"
    - source: "input_processor" 
      target: "agent_b"
    - source: "agent_a"
      target: "synthesizer"
    - source: "agent_b"
      target: "synthesizer"
```

**Why this works:**
- Single input consumer (`input_processor`)
- Parallel nodes use same state key (`processed_input`) but different output keys
- Convergence node explicitly references all parallel outputs
- No concurrent writes to same state keys

### 2. Conditional Routing Pattern (SAFE)

```yaml
workflow:
  type: "custom_graph" 
  nodes:
    - id: "decision_maker"
      prompt: "Analyze and route: {input}"
      output_key: "routing_decision"
      
    - id: "path_a_processor"
      prompt: "Handle path A: {state.routing_decision}"
      output_key: "path_a_result"
      
    - id: "path_b_processor" 
      prompt: "Handle path B: {state.routing_decision}"
      output_key: "path_b_result"
      
    - id: "final_processor"
      prompt: "Complete processing: {state.path_a_result}{state.path_b_result}"
      output_key: "final_result"
      
  edges:
    - source: "decision_maker"
      target: "path_a_processor"
      condition: "'path_a' in {state.routing_decision}.lower()"
    - source: "decision_maker"
      target: "path_b_processor" 
      condition: "'path_b' in {state.routing_decision}.lower()"
    - source: "path_a_processor"
      target: "final_processor"
    - source: "path_b_processor"
      target: "final_processor"
```

### 3. Multi-Agent Collaboration Pattern (SAFE)

```yaml
workflow:
  type: "custom_graph"
  nodes:
    - id: "coordinator"
      prompt: "Coordinate multi-agent task: {input}"
      output_key: "task_breakdown"
      
    - id: "specialist_a"
      prompt: |
        Handle specialist task A:
        Task: {state.task_breakdown}
      output_key: "specialist_a_work"
      
    - id: "specialist_b"
      prompt: |
        Handle specialist task B:
        Task: {state.task_breakdown}
      output_key: "specialist_b_work"
      
    - id: "reviewer"
      prompt: |
        Review all work:
        Specialist A: {state.specialist_a_work}
        Specialist B: {state.specialist_b_work}
      output_key: "review_feedback"
      
    - id: "final_integrator"
      prompt: |
        Integrate final result:
        Original task: {state.task_breakdown}
        Specialist A work: {state.specialist_a_work}
        Specialist B work: {state.specialist_b_work} 
        Review feedback: {state.review_feedback}
      output_key: "integrated_result"
      
  edges:
    - source: "coordinator"
      target: "specialist_a"
    - source: "coordinator"
      target: "specialist_b"
    - source: "specialist_a"
      target: "reviewer"
    - source: "specialist_b"
      target: "reviewer"
    - source: "reviewer"
      target: "final_integrator"
```

## Anti-Patterns That Cause Conflicts

### 1. Multiple Input Consumers (DANGEROUS)

```yaml
# ❌ WRONG: Multiple nodes consuming {input}
nodes:
  - id: "agent_a"
    prompt: "Process: {input}"  # Bad!
  - id: "agent_b" 
    prompt: "Analyze: {input}"  # Bad!
```

### 2. Concurrent Writes to Same State Key (DANGEROUS)

```yaml
# ❌ WRONG: Both nodes writing to 'analysis'
nodes:
  - id: "agent_a"
    output_key: "analysis"  # Conflict!
  - id: "agent_b"
    output_key: "analysis"  # Conflict!
```

### 3. Uncontrolled Fan-out Without Proper Convergence (RISKY)

```yaml
# ❌ RISKY: No clear convergence strategy
edges:
  - source: "start"
    target: "agent_a"
  - source: "start" 
    target: "agent_b"
  - source: "start"
    target: "agent_c"
  # No clear path to final node
```

## Custom Graph Safety Checklist

Before deploying custom graph workflows:

### Input Management
- [ ] Only ONE node consumes `{input}`
- [ ] All other nodes reference `{state.variable_name}`
- [ ] No hardcoded input values in prompts

### State Key Management  
- [ ] Each node has unique `output_key`
- [ ] No concurrent writes to same state key
- [ ] State references are complete (no empty sections)

### Graph Structure
- [ ] Clear convergence points for parallel paths
- [ ] All edges lead to reachable nodes
- [ ] No orphaned nodes or infinite loops
- [ ] Final node has `stop: true`

### Parallel Execution Safety
- [ ] Parallel nodes read from same state keys, write to different keys
- [ ] Convergence nodes explicitly reference all parallel outputs
- [ ] No dependencies between parallel nodes

### Error Prevention
- [ ] Test with minimal 2-3 node versions first
- [ ] Verify all edge sources/targets exist in nodes
- [ ] Ensure deterministic routing in conditional edges

## Advanced Patterns

### Using State Transformation

```yaml
# Transform state for downstream processing
- id: "state_transformer"
  prompt: |
    Transform data for next stage:
    Raw input: {state.raw_data}
    Analysis: {state.analysis_results}
    
    Provide structured data for final processing.
  output_key: "transformed_state"
```

### Conditional Convergence

```yaml
# Different convergence based on conditions
- id: "smart_converger"
  prompt: |
    Intelligently combine results based on content:
    {% if state.path_a_result %}
    Path A Result: {state.path_a_result}
    {% endif %}
    {% if state.path_b_result %}
    Path B Result: {state.path_b_result}
    {% endif %}
    
    Synthesize appropriate response.
  output_key: "conditional_synthesis"
```

## Migration Strategy: Sequential → Custom Graph

When converting sequential workflows to custom graphs:

1. **Start with working sequential version**
2. **Identify true parallelization opportunities**
3. **Design state key strategy**
4. **Convert one parallel section at a time**
5. **Test thoroughly at each step**

## Performance Considerations

Custom graphs are more powerful but:
- **Higher complexity** = more potential failure points
- **Parallel execution** can be faster but uses more resources
- **State management** overhead increases with complexity
- **Debugging** is more challenging than sequential flows

## When to Avoid Custom Graphs

**Avoid custom graphs if:**
- Sequential workflow meets requirements
- Team lacks LangGraph expertise
- Debugging complexity outweighs benefits
- Simple fan-out can be achieved with sequential + state accumulation

## Key Takeaway

**Custom graphs are powerful but require careful design.** The complexity trade-off is only worthwhile when you need true parallel execution, complex routing, or dynamic workflows that can't be expressed sequentially. Most multi-agent simulations work perfectly with sequential workflows where agents build upon each other's outputs.

Start simple, add complexity only when necessary, and always prioritize maintainability over architectural elegance.