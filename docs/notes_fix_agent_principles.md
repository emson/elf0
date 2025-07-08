# Agent Workflow Design Principles: Learning from LangGraph Channel Conflicts

## Problem Analysis: The `simulate_salary.yaml` Issue

### What Went Wrong

The `simulate_salary.yaml` workflow failed with `INVALID_CONCURRENT_GRAPH_UPDATE` errors due to several design anti-patterns:

1. **Fan-out Anti-pattern**: The `scenario_processor` node fanned out to 4 nodes simultaneously (`ben_agent`, `patrick_agent`, `lily_agent`, `context_injector`), causing multiple concurrent writes to the input channel.

2. **Input Channel Violations**: LangGraph received multiple identical input values simultaneously, violating the "one value per step" rule for input channels.

3. **Complex Dependency Web**: The `outcome_synthesizer` node received inputs from 6 different sources, creating a complex dependency graph that was difficult to manage.

4. **Incomplete State References**: Several nodes had malformed prompts with empty `Scenario:` sections instead of proper `{state.scenario_input}` references.

5. **Runtime Mismatch**: Used `custom_graph` workflow type with patterns that don't align with LangGraph's execution model.

### Root Technical Issue

LangGraph expects either:
- Sequential execution with clear single-path flow
- Custom graphs with proper state management using annotated types and reducers
- Explicit handling of concurrent updates through reducer functions

The workflow violated these constraints by creating implicit concurrent state access without proper coordination.

## Prevention Principles

### 1. Input Isolation Principle

**Rule**: Only ONE node should consume the raw `{input}` variable.

```yaml
# ✅ CORRECT: Single input consumer
- id: "entry_node"
  prompt: "Process input: {input}"
  output_key: "processed_input"

- id: "next_node"  
  prompt: "Continue with: {state.processed_input}"
```

```yaml
# ❌ WRONG: Multiple input consumers
- id: "node_a"
  prompt: "Process: {input}"
- id: "node_b"
  prompt: "Also process: {input}"  # Violates single input rule
```

### 2. Linear Flow Preference

**Rule**: Prefer sequential workflows over complex custom graphs unless parallelism is absolutely necessary.

```yaml
# ✅ CORRECT: Linear sequential flow
workflow:
  type: "sequential"
  nodes:
    - id: "step1"
    - id: "step2" 
    - id: "step3"
  edges:
    - source: "step1"
      target: "step2"
    - source: "step2"
      target: "step3"
```

```yaml
# ❌ RISKY: Complex fan-out pattern
workflow:
  type: "custom_graph"
  edges:
    - source: "step1"
      target: "step2a"
    - source: "step1"
      target: "step2b"  # Fan-out creates complexity
    - source: "step1"
      target: "step2c"
```

### 3. State Reference Completeness

**Rule**: Every node that needs scenario/context data should explicitly reference state variables.

```yaml
# ✅ CORRECT: Complete state reference
prompt: |
  You are Agent X analyzing this scenario.
  
  Scenario:
  {state.scenario_input}
  
  Provide your analysis...
```

```yaml
# ❌ WRONG: Missing state reference
prompt: |
  You are Agent X analyzing this scenario.
  
  Scenario:
  
  Provide your analysis...  # Empty scenario reference
```

### 4. Explicit Dependency Management

**Rule**: Make data dependencies explicit in graph structure rather than relying on implicit state sharing.

```yaml
# ✅ CORRECT: Clear dependency chain
edges:
  - source: "data_collector"
    target: "analyzer"
  - source: "analyzer" 
    target: "synthesizer"  # Clear who feeds whom
```

```yaml
# ❌ UNCLEAR: Implicit dependencies
edges:
  - source: "step1"
    target: "final_step"  # Missing intermediate dependencies
  - source: "step2"
    target: "final_step"
  - source: "step3"
    target: "final_step"  # Complex convergence without clear data flow
```

### 5. Runtime Constraint Awareness

**Rule**: Understand and design within the constraints of your target runtime.

**LangGraph Constraints:**
- Input channels can only receive one value per step
- Concurrent updates require explicit reducer functions
- Fan-out patterns need careful state management
- Custom graphs require more sophisticated error handling

**Design Accordingly:**
- Use sequential workflows for linear processes
- Use custom graphs only when true parallelism is needed
- Test complex patterns incrementally

### 6. Incremental Testing Principle

**Rule**: Build and test workflows incrementally rather than creating complex structures all at once.

**Progressive Development:**
1. Start with 2-3 nodes in sequential flow
2. Test basic input → processing → output flow
3. Add one node at a time
4. Test after each addition
5. Only add complexity (fan-out, convergence) after basics work

### 7. State Key Uniqueness

**Rule**: Ensure each node outputs to a unique state key to avoid conflicts.

```yaml
# ✅ CORRECT: Unique output keys
nodes:
  - id: "agent_a"
    output_key: "agent_a_response"
  - id: "agent_b"  
    output_key: "agent_b_response"
```

```yaml
# ❌ WRONG: Conflicting output keys
nodes:
  - id: "agent_a"
    output_key: "response"
  - id: "agent_b"
    output_key: "response"  # Potential conflict
```

### 8. Error Message Analysis

**Rule**: When LangGraph errors occur, analyse the technical details rather than just fixing symptoms.

**For `INVALID_CONCURRENT_GRAPH_UPDATE`:**
- Check for fan-out patterns
- Verify input isolation
- Look for concurrent state writes
- Consider switching to sequential workflow
- Add explicit reducers if concurrent updates are needed

## Implementation Checklist

Before deploying a complex workflow:

- [ ] Only one node consumes `{input}`
- [ ] All other nodes use `{state.variable_name}` references
- [ ] No empty or incomplete prompt templates
- [ ] Clear linear data flow (prefer sequential over custom_graph)
- [ ] Unique output keys for all nodes
- [ ] Incremental testing completed
- [ ] Runtime constraints understood and respected
- [ ] Error handling considered for complex patterns

## Recovery Strategies

When facing channel conflicts:

1. **Simplify First**: Convert custom_graph to sequential workflow
2. **Eliminate Fan-out**: Create linear execution chains
3. **Fix State References**: Ensure all nodes properly reference state
4. **Test Minimally**: Start with 2-3 nodes and build up
5. **Consider Alternatives**: Sometimes the workflow design needs fundamental changes

## Key Takeaway

**Complex multi-agent simulations can be achieved with simple linear workflows.** The illusion of parallelism in AI agent interactions can often be maintained through sequential execution where each agent builds upon the previous agent's output, creating rich interactive dynamics without LangGraph's concurrency complications.