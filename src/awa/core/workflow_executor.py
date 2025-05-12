# src/awa/core/workflow_executor.py

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from awa.core.workflow_loader import WorkflowLoader
from awa.core.workflow_model import Workflow, StepDef, AgentDef, ToolDef
from awa.core.llm_integration import AgentExecutor
from awa.core.llm_client import LLMClientRegistry
from awa.core.errors import LLMClientError, WorkflowExecutorError, StepDependencyError
import logging
from functools import partial
import asyncio

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Configure logging to output to console
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class StepExecutor:
    """Base class for step executors."""
    
    def __init__(self, step: StepDef):
        self.step = step
        
    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute the step with the given input data.
        
        Args:
            input_data: The input data for the step
            
        Returns:
            The result of the step execution
        """
        raise NotImplementedError

class AgentStepExecutor(StepExecutor):
    """Executor for agent steps."""
    
    def __init__(self, step: StepDef, agent_executor: AgentExecutor):
        super().__init__(step)
        self.agent_executor = agent_executor
        
    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute an agent step.
        
        Args:
            input_data: The input data for the step
            
        Returns:
            The result of the agent execution
        """
        return await asyncio.to_thread(self.agent_executor.execute, input_data)

class ToolStepExecutor(StepExecutor):
    """Executor for tool steps."""
    
    def __init__(self, step: StepDef, tool_func: Callable):
        super().__init__(step)
        self.tool_func = tool_func
        
    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute a tool step.
        
        Args:
            input_data: The input data for the step
            
        Returns:
            The result of the tool execution
        """
        tool_params = self.step.tool_params or {}
        return self.tool_func(input_data, **tool_params)

class SubworkflowStepExecutor(StepExecutor):
    """Executor for subworkflow steps."""
    
    def __init__(self, step: StepDef, workflow_path: Path):
        super().__init__(step)
        self.workflow_path = workflow_path
        
    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute a nested workflow step.
        
        Args:
            input_data: The input data for the step
            
        Returns:
            The result of the subworkflow execution
        """
        nested_executor = WorkflowExecutor(self.workflow_path)
        return await nested_executor.execute(input_data)

class WorkflowExecutor:
    """Executes a workflow by managing its execution context and step execution."""
    
    def __init__(self, workflow_path: Path):
        """Initialize the workflow executor.
        
        Args:
            workflow_path: Path to the workflow YAML file
        """
        self.workflow = WorkflowLoader.load_workflow(workflow_path)
        self.results: Dict[str, Any] = {}
        self.agent_executors: Dict[str, AgentExecutor] = {}
        self.tool_registry: Dict[str, Callable] = {}
        
        # Initialize agent executors
        for agent in self.workflow.agents:
            self.agent_executors[agent.id] = AgentExecutor(agent, self.workflow.defaults.get('llm_client'))
        
        self.step_executors = self._create_step_executors()
        
    def _create_step_executors(self) -> List[StepExecutor]:
        """Create executors for all steps in the workflow."""
        return [
            self._create_step_executor(step)
            for step in self.workflow.steps
        ]
        
    def _create_step_executor(self, step: StepDef) -> StepExecutor:
        """Create an executor for a specific step.
        
        Args:
            step: The step to create an executor for
            
        Returns:
            The appropriate step executor
            
        Raises:
            ValueError: If the step type is invalid
        """
        if step.agent_id:
            return AgentStepExecutor(step, self.agent_executors[step.agent_id])
        elif step.tool_id:
            return ToolStepExecutor(step, self.tool_registry[step.tool_id])
        elif step.workflow:
            return SubworkflowStepExecutor(step, Path(step.workflow))
        raise ValueError("Invalid step type")
        
    def register_tool(self, tool_id: str, tool_func: Callable) -> None:
        """Register a tool function.
        
        Args:
            tool_id: The ID of the tool
            tool_func: The function implementing the tool
        """
        self.tool_registry[tool_id] = tool_func
        
    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute the workflow with the given input data.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            The final output of the workflow
            
        Raises:
            ExecutionError: If any step fails to execute
        """
        self.results["USER_INPUT"] = input_data
        self.results["user"] = input_data
        
        # Log workflow start
        logger.info(f"Starting workflow execution with input: {input_data}")
        
        # Execute each step in order
        for executor in self.step_executors:
            if not self._should_execute_step(executor.step):
                continue
                
            input_data = self._get_step_input(executor.step)
            try:
                result = await executor.execute(input_data)
                self.results[executor.step.id] = result
            except Exception as e:
                logger.error(f"Step {executor.step.id} failed: {str(e)}")
                await self._handle_error(executor.step, e)
                
        # Get final output
        final_result = self.results[self.workflow.output.step]
        logger.info(f"Workflow completed successfully")
        return self._save_output(final_result)
        
    def _get_step_input(self, step: StepDef) -> Dict[str, Any]:
        """Get the input data for a step.
        
        Args:
            step: The step to get input for
            
        Returns:
            The input data for the step
            
        Raises:
            StepDependencyError: If a required step dependency is missing
        """
        source = step.input.source
        logger.debug(f"Getting input for step {step.id} from source: {source}")
        
        # Check if it's a special input source
        if source in ["USER_INPUT", "user"]:
            raw_input = self.results[source]
            # For agent steps, format the input as {"input": {"message": input_data}}
            if step.agent_id:  # Check if this is an agent step
                return {"input": {"message": raw_input}}  # Format for template {{ input.message }}
            return raw_input
            
        # Get data from previous step
        try:
            previous_result = self.results[source]
        except KeyError:
            logger.error(f"Failed to get result for step {source}")
            raise StepDependencyError(f"Step {source} has not been executed yet")
        
        # If key is specified, get that specific field
        if step.input.key:
            if not isinstance(previous_result, dict):
                raise ValueError(f"Step {source} result is not a dictionary, cannot extract key {step.input.key}")
            return previous_result.get(step.input.key, {})
            
        return previous_result
        
    def _should_execute_step(self, step: StepDef) -> bool:
        """Determine if a step should be executed based on its condition.
        
        Args:
            step: The step to check
            
        Returns:
            True if the step should be executed, False otherwise
        """
        if not step.condition:
            return True
            
        # Evaluate Jinja-like condition expression
        try:
            # This is a simplified version - in production we'd use a proper template engine
            condition = step.condition.replace("{{", "self.results['").replace("}}", "']")
            return eval(condition)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition for step {step.id}: {e}")
            return False
        
    async def _handle_error(self, step: StepDef, error: Exception) -> None:
        """Handle errors during step execution.
        
        Args:
            step: The step that failed
            error: The error that occurred
        """
        logger.error(f"Step {step.id} failed: {str(error)}")
        if step.on_error:
            try:
                error_handler = self.tool_registry[step.on_error.tool_id]
                await error_handler(step.on_error.params)
            except Exception as e:
                logger.error(f"Error handler for step {step.id} failed: {str(e)}")
        
    def _save_output(self, output: Any) -> Any:
        """Save the final output of the workflow.
        
        Args:
            output: The output to save
            
        Returns:
            The saved output
        """
        # TODO: Implement output saving logic
        return output

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create a simple echo tool
        def echo_tool(data: dict, **kwargs) -> dict:
            return {"echo": data.get("message", "No message provided")}
        
        # Initialize the executor
        workflow_path = Path("workflows/basic_chat.yaml")
        executor = WorkflowExecutor(workflow_path)
        
        # Register tools (if any)
        # executor.context.register_tool("echo", echo_tool)
        
        # Execute with sample input
        input_data = {"message": "How many 'r's are in the word 'strawberry'?"}
        result = await executor.execute(input_data)
        print("\nWorkflow result:", result)
    
    # Run the main function
    asyncio.run(main())