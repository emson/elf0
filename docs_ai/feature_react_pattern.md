# ReAct Pattern Feature

## Overview

The ReAct (Reasoning and Acting) pattern enables AI agents to interleave reasoning steps with action execution in an iterative loop. This pattern allows agents to think through problems step-by-step, take actions to gather information or modify the environment, observe results, and continue reasoning based on new information until reaching a solution.

## Current State

The ReAct pattern is currently marked as TODO in the codebase:
- No implementation of the ReAct reasoning loop
- No action/observation framework
- No integration with tool calling or function execution
- No support for iterative reasoning workflows

## Feature Requirements

### Core ReAct Pattern Support

1. **Reasoning Loop Framework**
   - Iterative thought/action/observation cycles
   - Structured reasoning prompts and templates
   - Action planning and execution coordination
   - Termination conditions and success criteria

2. **Action Framework**
   - Integration with available tools (Python functions, MCP tools, built-in actions)
   - Action parameter extraction from reasoning text
   - Action execution and result capture
   - Error handling and retry logic for failed actions

3. **Observation Processing**
   - Action result interpretation and formatting
   - Observation integration into reasoning context
   - Result filtering and summarization
   - Error and exception handling

### Reasoning and Planning

1. **Structured Thinking**
   - Step-by-step reasoning templates
   - Goal decomposition and sub-task identification
   - Progress tracking and state management
   - Decision-making frameworks

2. **Action Selection**
   - Available action discovery and recommendation
   - Action parameter inference from context
   - Action prioritization and selection logic
   - Constraint handling and validation

### Workflow Integration

1. **ReAct Node Type**
   - New `react` node type for workflow specifications
   - Goal definition and success criteria configuration
   - Tool and action availability configuration
   - Reasoning prompt customization

2. **State Management**
   - Reasoning history tracking
   - Action/observation log maintenance
   - Intermediate result storage
   - Context window management

## Implementation Details

### 1. ReAct Controller

```python
# src/elf/core/react_controller.py
from typing import List, Dict, Any, Optional, Union
import re
from dataclasses import dataclass

@dataclass
class ReActStep:
    """Single step in ReAct reasoning loop"""
    step_type: str  # 'thought', 'action', 'observation'
    content: str
    metadata: Dict[str, Any]
    timestamp: float

@dataclass
class ReActAction:
    """Parsed action from reasoning text"""
    action_name: str
    parameters: Dict[str, Any]
    raw_text: str

class ReActController:
    """Manages ReAct reasoning and action execution loop"""
    
    def __init__(self, 
                 llm_client,
                 available_actions: List[str],
                 max_iterations: int = 10,
                 max_context_length: int = 8000):
        self.llm_client = llm_client
        self.available_actions = available_actions
        self.max_iterations = max_iterations
        self.max_context_length = max_context_length
        self.reasoning_history: List[ReActStep] = []
    
    async def run_react_loop(self, 
                           goal: str, 
                           initial_context: str = "") -> Dict[str, Any]:
        """Execute complete ReAct reasoning loop"""
        # Implementation needed
    
    def parse_reasoning_response(self, response: str) -> List[ReActStep]:
        """Parse LLM response into thought/action steps"""
        # Implementation needed
    
    def extract_action(self, action_text: str) -> Optional[ReActAction]:
        """Extract structured action from reasoning text"""
        # Implementation needed
    
    async def execute_action(self, action: ReActAction) -> str:
        """Execute action and return observation"""
        # Implementation needed
    
    def build_reasoning_prompt(self, 
                              goal: str, 
                              context: str, 
                              history: List[ReActStep]) -> str:
        """Build prompt for next reasoning step"""
        # Implementation needed
    
    def should_terminate(self, history: List[ReActStep]) -> bool:
        """Determine if reasoning loop should terminate"""
        # Implementation needed
```

### 2. Action Executor Framework

```python
# src/elf/core/react_actions.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ReActAction(ABC):
    """Base class for ReAct actions"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Action name for reasoning text parsing"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Action description for LLM context"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Action parameter schema"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute action and return observation"""
        pass

class PythonFunctionAction(ReActAction):
    """Execute Python function as ReAct action"""
    
    def __init__(self, function_name: str, function: Callable):
        self.function_name = function_name
        self.function = function
        self._schema = self._extract_schema()
    
    @property
    def name(self) -> str:
        return self.function_name
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        # Implementation needed
        pass

class MCPToolAction(ReActAction):
    """Execute MCP tool as ReAct action"""
    
    def __init__(self, tool_name: str, mcp_client):
        self.tool_name = tool_name
        self.mcp_client = mcp_client
        self._tool_info = None
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        # Implementation needed
        pass

class ReActActionRegistry:
    """Registry for available ReAct actions"""
    
    def __init__(self):
        self.actions: Dict[str, ReActAction] = {}
    
    def register_action(self, action: ReActAction):
        """Register new action"""
        self.actions[action.name] = action
    
    def get_action(self, name: str) -> Optional[ReActAction]:
        """Get action by name"""
        return self.actions.get(name)
    
    def list_actions(self) -> List[str]:
        """List all available action names"""
        return list(self.actions.keys())
    
    def get_actions_description(self) -> str:
        """Get formatted description of all actions for LLM context"""
        # Implementation needed
        pass
```

### 3. ReAct Node Implementation

```python
# src/elf/core/nodes/react_node.py
from typing import Dict, Any, Optional
from elf.core.nodes.base import BaseNode
from elf.core.react_controller import ReActController
from elf.core.react_actions import ReActActionRegistry

class ReActNode(BaseNode):
    """ReAct reasoning and action execution node"""
    
    def __init__(self, config: ReActNodeConfig):
        self.goal = config.goal
        self.initial_context = config.context or ""
        self.max_iterations = config.max_iterations or 10
        self.actions = config.actions or []
        self.success_criteria = config.success_criteria
        self.action_registry = ReActActionRegistry()
        self.controller = None
    
    async def initialize(self) -> None:
        """Initialize ReAct controller and register actions"""
        # Implementation needed
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute ReAct reasoning loop"""
        # Implementation needed
    
    def _interpolate_goal(self, state: WorkflowState) -> str:
        """Interpolate goal template with workflow state"""
        # Implementation needed
    
    def _check_success_criteria(self, 
                               result: Dict[str, Any], 
                               state: WorkflowState) -> bool:
        """Check if success criteria are met"""
        # Implementation needed
```

### 4. ReAct Configuration Schema

```yaml
# ReAct node configuration in workflow YAML
nodes:
  - id: "react_researcher"
    type: "react"
    config:
      goal: "Research the topic '${state.research_topic}' and provide a comprehensive summary"
      context: "You are a research assistant. Use available tools to gather information."
      max_iterations: 15
      success_criteria:
        - "Final answer contains at least 3 key points"
        - "Sources are cited for claims"
        - "Summary is between 200-500 words"
      actions:
        - type: "web_search"
          name: "search"
          description: "Search the web for information"
        - type: "python_function"
          module: "research_tools"
          function: "extract_key_points"
        - type: "mcp_tool"
          server: "knowledge_base"
          tool: "query_database"
      reasoning_template: |
        Goal: {goal}
        
        Available actions:
        {actions_description}
        
        Current situation:
        {context}
        
        Reasoning history:
        {history}
        
        Think step by step about what to do next. Use this format:
        Thought: [your reasoning]
        Action: action_name(parameter1="value1", parameter2="value2")
        
        Or if you're ready to finish:
        Thought: [your final reasoning]
        Final Answer: [your complete answer]
```

### 5. Reasoning Templates

```python
# src/elf/core/react_templates.py

DEFAULT_REACT_TEMPLATE = """
You are solving this problem: {goal}

{context}

Available actions:
{actions_description}

Previous steps:
{history}

Think step by step about what to do next. You can:
1. Reason about the current situation
2. Take an action to gather more information or make progress
3. Provide a final answer when you have enough information

Use this exact format:
Thought: [Your reasoning about what to do next]
Action: action_name(param1="value1", param2="value2")

OR if you're ready to finish:
Thought: [Your final reasoning]
Final Answer: [Your complete answer]

Begin:
"""

SIMPLE_REACT_TEMPLATE = """
Goal: {goal}
{context}

Actions: {actions_description}

{history}

Next step (Thought: ... then Action: ... OR Final Answer: ...):
"""

STRUCTURED_REACT_TEMPLATE = """
## Problem
{goal}

## Context
{context}

## Available Tools
{actions_description}

## Progress So Far
{history}

## Next Step
Analyze the situation and either:
1. Take an action: Action: tool_name(param="value")
2. Provide final answer: Final Answer: [complete response]

Thought: 
"""
```

## Testing Requirements

### Unit Tests

1. **ReAct Controller Tests** (`tests/core/test_react_controller.py`)
   - Test reasoning loop execution with mock LLM responses
   - Test action parsing from reasoning text
   - Test termination condition evaluation
   - Test context window management
   - Test error handling for malformed responses

2. **Action Framework Tests** (`tests/core/test_react_actions.py`)
   - Test action registration and discovery
   - Test action execution with various parameter types
   - Test action error handling and retry logic
   - Test action description generation
   - Test parameter validation and binding

3. **ReAct Node Tests** (`tests/core/test_react_node.py`)
   - Test ReAct node configuration validation
   - Test goal interpolation from workflow state
   - Test success criteria evaluation
   - Test reasoning loop integration
   - Test state management and result handling

### Integration Tests

1. **End-to-End ReAct Tests** (`tests/integration/test_react_integration.py`)
   - Test complete ReAct workflows with real LLM
   - Test action execution with Python functions and MCP tools
   - Test multi-step reasoning and problem solving
   - Test various goal types and complexity levels
   - Create test scenarios with known solutions

2. **Action Integration Tests** (`tests/integration/test_react_action_integration.py`)
   - Test ReAct with real Python functions
   - Test ReAct with MCP tool integration
   - Test mixed action types in single reasoning loop
   - Test error recovery across action types

### CLI Tests

1. **ReAct CLI Tests** (`tests/cli/test_react_cli.py`)
   - Test workflow execution with ReAct nodes
   - Test ReAct configuration validation
   - Test error reporting for ReAct issues
   - Test interactive ReAct debugging

## Implementation Tasks

### Phase 1: Core ReAct Framework (High Priority)

1. **Implement ReAct Controller**
   - Create `ReActController` class with reasoning loop
   - Add response parsing for thought/action/observation patterns
   - Implement action extraction and validation
   - Add termination logic and iteration limits

2. **Create Action Framework**
   - Implement `ReActAction` base class and registry
   - Create action wrappers for Python functions
   - Add action description generation for LLM context
   - Implement parameter binding and validation

3. **Implement ReAct Node**
   - Create `ReActNode` class for workflow integration
   - Add ReAct configuration schema and validation
   - Implement goal interpolation and success criteria
   - Add reasoning history management

### Phase 2: Advanced Features (Medium Priority)

1. **Enhanced Reasoning Templates**
   - Create configurable reasoning templates
   - Add domain-specific reasoning patterns
   - Implement template customization and inheritance
   - Add reasoning quality validation

2. **Action Integration**
   - Integrate with Python function loading
   - Add MCP tool action support
   - Create built-in utility actions (web search, file operations)
   - Implement action chaining and composition

3. **Context Management**
   - Implement intelligent context summarization
   - Add reasoning history compression
   - Support long-running reasoning sessions
   - Add context persistence and recovery

### Phase 3: Optimization and Advanced Features (Lower Priority)

1. **Performance Optimization**
   - Optimize reasoning loop performance
   - Add parallel action execution
   - Implement reasoning result caching
   - Add performance monitoring and metrics

2. **Advanced Reasoning Patterns**
   - Implement hierarchical goal decomposition
   - Add collaborative multi-agent reasoning
   - Support conditional and branching reasoning
   - Add learning from reasoning outcomes

3. **Debugging and Observability**
   - Create reasoning trace visualization
   - Add step-by-step debugging support
   - Implement reasoning quality metrics
   - Add reasoning pattern analysis

## Testing Strategy

1. **Mock-Based Unit Testing**
   - Test reasoning logic with mock LLM responses
   - Test action execution with mock tools
   - Test all error conditions and edge cases
   - Focus on parsing and control flow logic

2. **Integration Testing with Real Components**
   - Test with actual LLM for reasoning quality
   - Test with real tools and functions
   - Validate end-to-end problem solving
   - Test performance and reliability

3. **Scenario-Based Testing**
   - Create test problems with known solutions
   - Test various reasoning complexity levels
   - Validate different action types and combinations
   - Test failure and recovery scenarios

## Documentation Updates

1. **Update project_tasks.md**
   - Add ReAct pattern implementation to Phase 2
   - Mark current TODO status
   - Add testing and integration requirements

2. **Create User Documentation**
   - Add ReAct pattern examples to README
   - Create ReAct workflow configuration guide
   - Document available actions and integration
   - Add troubleshooting guide for ReAct issues

3. **Developer Documentation**
   - Document ReAct action development guidelines
   - Create reasoning template customization guide
   - Document performance optimization techniques
   - Add examples for common ReAct patterns

## Success Criteria

1. **Functional Requirements**
   - Execute multi-step reasoning loops with action execution
   - Support various action types (Python, MCP, built-in)
   - Handle complex problems requiring multiple information gathering steps
   - Provide clear reasoning traces and decision explanations

2. **Non-Functional Requirements**
   - Reasoning loop execution < 5 seconds per iteration
   - Support for 20+ iteration reasoning loops
   - 95% success rate for well-defined problems
   - Clear error reporting and debugging support

3. **Integration Requirements**
   - Seamless integration with existing workflow patterns
   - Support for all existing action types
   - Backward compatibility with current specifications
   - Comprehensive test coverage (>90%)

## Dependencies

1. **Core Dependencies**
   - LLM client integration for reasoning
   - Action execution framework
   - Text parsing and pattern matching
   - State management and persistence

2. **Integration Dependencies**
   - Python function loading system
   - MCP client integration
   - Workflow state management
   - Error handling and logging

This ReAct pattern implementation will enable ELF to support sophisticated autonomous reasoning and problem-solving workflows, dramatically expanding its capabilities for complex task automation and intelligent decision-making.