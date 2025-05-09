# src/awa/core/workflow_executor.py

from typing import Dict, Any, Optional, List, Callable, Union
from pathlib import Path
from awa.core.workflow_loader import WorkflowLoader
from awa.core.workflow_model import Workflow, StepDef, AgentDef, ToolDef
from awa.core.llm_integration import AgentExecutor
from awa.core.llm_client import LLMClientRegistry
from awa.core.errors import LLMClientError, WorkflowExecutorError, StepDependencyError
import logging
from functools import partial
import asyncio

logger = logging.getLogger(__name__)

class ExecutionError(Exception):
    """Base exception for workflow execution errors"""
    pass

class StepDependencyError(ExecutionError):
    """Raised when a step's dependencies are not met"""
    pass

class WorkflowContext:
    """Execution context for a workflow"""
    
    def __init__(self, workflow: Workflow):
        """Initialize the workflow context.
        
        Args:
            workflow: The workflow to execute
        """
        self.workflow = workflow
        self.step_results: Dict[str, Any] = {}
        self.agent_executors: Dict[str, AgentExecutor] = {}
        self.tool_registry: Dict[str, Callable] = {}
        
        # Initialize agent executors
        for agent in workflow.agents:
            self.agent_executors[agent.id] = AgentExecutor(agent, workflow.defaults.get('llm_client'))
        
    def get_step_result(self, step_id: str) -> Any:
        """Get the result of a previous step.
        
        Args:
            step_id: The ID of the step to get results from
            
        Returns:
            The result of the step
            
        Raises:
            StepDependencyError: If the step hasn't been executed yet
        """
        if step_id not in self.step_results:
            raise StepDependencyError(f"Step {step_id} has not been executed yet")
        return self.step_results[step_id]
        
    def register_tool(self, tool_id: str, tool_func: Callable) -> None:
        """Register a tool function.
        
        Args:
            tool_id: The ID of the tool
            tool_func: The function implementing the tool
        """
        self.tool_registry[tool_id] = tool_func

class WorkflowExecutor:
    """Executes a workflow by managing its execution context and step execution."""
    
    def __init__(self, workflow_path: Path):
        """Initialize the workflow executor.
        
        Args:
            workflow_path: Path to the workflow YAML file
        """
        self.workflow = WorkflowLoader.load_workflow(workflow_path)
        self.context = WorkflowContext(self.workflow)
        
    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute the workflow with the given input data.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            The final output of the workflow
            
        Raises:
            ExecutionError: If any step fails to execute
        """
        # Store initial input with both possible names for backward compatibility
        self.context.step_results["USER_INPUT"] = input_data
        self.context.step_results["user"] = input_data
        
        # Log workflow start
        logger.info(f"Starting workflow execution with input: {input_data}")
        
        # Execute each step in order
        for step in self.workflow.steps:
            logger.info(f"Executing step: {step.id}")
            await self._execute_step(step)
        
        # Get final output
        final_step = self.context.get_step_result(self.workflow.output.step)
        logger.info(f"Workflow completed successfully")
        return self._save_output(final_step)
        
    async def _execute_step(self, step: StepDef) -> None:
        """Execute a single step.
        
        Args:
            step: The step to execute
            
        Raises:
            ExecutionError: If the step fails to execute
        """
        if not self._should_execute_step(step):
            return
            
        try:
            # Get input data
            input_data = self._get_input_data(step)
            
            # Execute based on step type
            if step.agent_id:
                await self._execute_agent_step(step, input_data)
            elif step.tool_id:
                await self._execute_tool_step(step, input_data)
            elif step.workflow:
                await self._execute_subworkflow(step, input_data)
            else:
                raise ValueError("Step must have exactly one of agent_id, tool_id, or workflow")
                
        except Exception as e:
            logger.error(f"Step {step.id} failed: {str(e)}")
            await self._handle_error(step, e)
            
    async def _execute_agent_step(self, step: StepDef, input_data: Dict[str, Any]) -> None:
        """Execute an agent step.
        
        Args:
            step: The agent step to execute
            input_data: The input data for the step
        """
        executor = self.context.agent_executors[step.agent_id]
        result = await asyncio.to_thread(executor.execute, input_data)
        self.context.step_results[step.id] = result
        
    async def _execute_tool_step(self, step: StepDef, input_data: Dict[str, Any]) -> None:
        """Execute a tool step.
        
        Args:
            step: The tool step to execute
            input_data: The input data for the step
        """
        tool_func = self.context.tool_registry[step.tool_id]
        tool_params = step.tool_params or {}
        result = tool_func(input_data, **tool_params)
        self.context.step_results[step.id] = result
        
    async def _execute_subworkflow(self, step: StepDef, input_data: Dict[str, Any]) -> None:
        """Execute a nested workflow step.
        
        Args:
            step: The subworkflow step to execute
            input_data: The input data for the step
        """
        nested_executor = WorkflowExecutor(Path(step.workflow))
        result = await nested_executor.execute(input_data)
        self.context.step_results[step.id] = result
        
    def _get_input_data(self, step: StepDef) -> Dict[str, Any]:
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
            return self.context.step_results[source]
            
        # Get data from previous step
        try:
            previous_result = self.context.get_step_result(source)
        except StepDependencyError:
            logger.error(f"Failed to get result for step {source}")
            raise
        
        # If key is specified, get that specific field
        if step.input.key:
            logger.debug(f"Extracting key {step.input.key} from previous result")
            return previous_result[step.input.key]
            
        return previous_result
        
    def _should_execute_step(self, step: StepDef) -> bool:
        """Check if a step should be executed based on conditions.
        
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
            condition = step.condition.replace("{{", "self.context.step_results['").replace("}}", "']")
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
        if isinstance(error, LLMClientError):
            if step.on_error == "retry" and step.max_retries:
                # TODO: Implement retry logic
                pass
            elif step.on_error == "skip":
                logger.warning(f"Skipping failed step {step.id} due to LLM error")
                return
        
        raise error
        
    def _save_output(self, output_data: Any) -> Any:
        """Save the final output if configured.
        
        Args:
            output_data: The data to save
            
        Returns:
            The saved output data
        """
        if self.workflow.output.save_to:
            # Get variables from the output data
            variables = output_data if isinstance(output_data, dict) else {}
            
            # Render the path using the SaveConfig model
            output_path = self.workflow.output.save_to.render_path(variables)
            
            # TODO: Implement actual saving logic
            logger.info(f"Output saved to {output_path}")
            
        return output_data

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
        input_data = {"message": "Hello, what can you do?"}
        result = await executor.execute(input_data)
        print("\nWorkflow result:", result)
    
    # Run the main function
    asyncio.run(main())