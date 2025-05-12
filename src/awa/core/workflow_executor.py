# src/awa/core/workflow_executor.py

from typing import Dict, Any, Optional, List, Callable, TypeVar, Protocol, Type, cast
from pathlib import Path
import asyncio
import logging
from functools import partial

from awa.core.workflow_loader import WorkflowLoader
from awa.core.workflow_model import Workflow, StepDef, AgentDef, ToolDef
from awa.core.llm_integration import AgentExecutor
from awa.core.llm_client import LLMClientRegistry
from awa.core.errors import WorkflowExecutorError, StepDependencyError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Configure logging to output to console
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Type definitions for clarity
StepResult = Any
InputData = Dict[str, Any]
StepID = str

class StepExecutor(Protocol):
    """Protocol defining the interface for all step executors"""
    
    @property
    def step_id(self) -> str:
        """Return the ID of the step this executor handles"""
        ...
    
    async def execute(self, input_data: InputData) -> StepResult:
        """Execute the step with the provided input data"""
        ...

class AgentStepExecutor:
    """Executes steps that involve LLM agent interaction"""
    
    def __init__(self, step: StepDef, agent_executor: AgentExecutor):
        self._step = step
        self._agent_executor = agent_executor
    
    @property
    def step_id(self) -> str:
        return self._step.id
    
    async def execute(self, input_data: InputData) -> StepResult:
        """Execute an agent step using the configured LLM"""
        logger.debug(f"Executing agent step {self._step.id} with input: {input_data}")
        # Run agent in thread pool to avoid blocking event loop
        return await asyncio.to_thread(self._agent_executor.execute, input_data)

class ToolStepExecutor:
    """Executes steps that involve running tool functions"""
    
    def __init__(self, step: StepDef, tool_func: Callable):
        self._step = step
        self._tool_func = tool_func
    
    @property
    def step_id(self) -> str:
        return self._step.id
    
    async def execute(self, input_data: InputData) -> StepResult:
        """Execute a tool step with the provided function"""
        logger.debug(f"Executing tool step {self._step.id} with input: {input_data}")
        # Get tool parameters from step definition
        tool_params = self._step.tool_params or {}
        # Execute the tool function with input and parameters
        return self._tool_func(input_data, **tool_params)

class SubworkflowStepExecutor:
    """Executes steps that involve running a nested workflow"""
    
    def __init__(self, step: StepDef, workflow_path: Path):
        self._step = step
        self._workflow_path = workflow_path
    
    @property
    def step_id(self) -> str:
        return self._step.id
    
    async def execute(self, input_data: InputData) -> StepResult:
        """Execute a nested workflow step"""
        logger.debug(f"Executing subworkflow step {self._step.id} with input: {input_data}")
        # Create a new executor for the nested workflow
        nested_executor = WorkflowExecutor(self._workflow_path)
        # Execute the nested workflow with the provided input
        return await nested_executor.execute(input_data)

class ExecutionMode:
    """Handles different execution modes for steps"""
    
    @staticmethod
    async def execute_serial(executor: StepExecutor, input_data: InputData) -> StepResult:
        """Execute a step in serial mode (default)"""
        return await executor.execute(input_data)
    
    @staticmethod
    async def execute_map(executor: StepExecutor, input_data: List[Any]) -> List[StepResult]:
        """Execute a step in map mode (process each item in a list)"""
        if not isinstance(input_data, list):
            raise ValueError(f"Map execution mode requires a list input, got {type(input_data)}")
        
        # Create a task for each item in the input list
        tasks = [executor.execute({"item": item}) for item in input_data]
        # Execute all tasks concurrently and return results
        return await asyncio.gather(*tasks)
    
    @staticmethod
    async def execute_parallel(executor: StepExecutor, input_data: InputData) -> List[StepResult]:
        """Execute a step in parallel mode (process concurrently)"""
        # Implementation depends on specific parallel execution requirements
        # For now, similar to map but with different input structure
        return await ExecutionMode.execute_map(executor, input_data)

class WorkflowContext:
    """Manages the state and context for a workflow execution"""
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.results: Dict[StepID, Any] = {}
        self.agent_executors: Dict[str, AgentExecutor] = {}
        self.tool_registry: Dict[str, Callable] = {}
    
    def register_tool(self, tool_id: str, tool_func: Callable) -> None:
        """Register a tool function in the context"""
        self.tool_registry[tool_id] = tool_func
    
    def register_agent_executors(self, llm_client_registry: LLMClientRegistry) -> None:
        """Initialize agent executors for all agents in the workflow"""
        default_client = self.workflow.defaults.get('llm_client') if self.workflow.defaults else None
        
        for agent in self.workflow.agents:
            # Create an agent executor for each agent definition
            client = agent.llm_client or default_client
            if not client:
                raise WorkflowExecutorError(f"No LLM client specified for agent {agent.id}")
            
            self.agent_executors[agent.id] = AgentExecutor(agent, client)
    
    def set_result(self, step_id: StepID, result: Any) -> None:
        """Store a step result in the context"""
        self.results[step_id] = result
    
    def get_result(self, step_id: StepID) -> Any:
        """Get a step result from the context"""
        try:
            return self.results[step_id]
        except KeyError:
            raise StepDependencyError(f"Result for step {step_id} not available")
    
    def get_input_for_step(self, step: StepDef) -> InputData:
        """Prepare input data for a step based on its configuration"""
        source = step.input.source
        logger.debug(f"Getting input for step {step.id} from source: {source}")
        
        # Special input sources
        if source in ["USER_INPUT", "user"]:
            raw_input = self.results[source]
            # Format for agent steps
            if step.agent_id:
                return {"input": {"message": raw_input}}
            return raw_input
        
        # Get data from previous step
        try:
            previous_result = self.results[source]
        except KeyError:
            raise StepDependencyError(f"Step {source} has not been executed yet")
        
        # Extract specific key if configured
        if step.input.key:
            if not isinstance(previous_result, dict):
                raise ValueError(f"Step {source} result is not a dictionary, cannot extract key {step.input.key}")
            return previous_result.get(step.input.key, {})
        
        return previous_result
    
    def should_execute_step(self, step: StepDef) -> bool:
        """Determine if a step should be executed based on its condition"""
        if not step.condition:
            return True
        
        try:
            # Simple condition evaluation (in production, use a proper template engine)
            condition = step.condition.replace("{{", "self.results['").replace("}}", "']")
            return eval(condition)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition for step {step.id}: {e}")
            return False

class WorkflowExecutor:
    """Executes a workflow by managing step execution and context"""
    
    def __init__(self, workflow_path: Path):
        """Initialize the workflow executor
        
        Args:
            workflow_path: Path to the workflow YAML file
        """
        self.workflow_path = workflow_path
        self.workflow = WorkflowLoader.load_workflow(workflow_path)
        self.context = WorkflowContext(self.workflow)
        
        # Initialize LLM client registry
        self.llm_client_registry = LLMClientRegistry()
        
        # Initialize agent executors
        self.context.register_agent_executors(self.llm_client_registry)
    
    def create_step_executor(self, step: StepDef) -> StepExecutor:
        """Create an appropriate executor for a step
        
        Args:
            step: The step definition
            
        Returns:
            A step executor for the given step
            
        Raises:
            ValueError: If the step type is invalid
        """
        if step.agent_id:
            return AgentStepExecutor(step, self.context.agent_executors[step.agent_id])
        elif step.tool_id:
            return ToolStepExecutor(step, self.context.tool_registry[step.tool_id])
        elif step.workflow:
            return SubworkflowStepExecutor(step, Path(step.workflow))
        
        raise ValueError(f"Invalid step type for step {step.id}")
    
    def register_tool(self, tool_id: str, tool_func: Callable) -> None:
        """Register a tool function for use in the workflow
        
        Args:
            tool_id: The ID of the tool to register
            tool_func: The function implementing the tool
        """
        self.context.register_tool(tool_id, tool_func)
    
    async def handle_error(self, step: StepDef, error: Exception) -> None:
        """Handle errors during step execution
        
        Args:
            step: The step that failed
            error: The error that occurred
        """
        logger.error(f"Step {step.id} failed: {str(error)}")
        
        # Execute error handler if configured
        if step.on_error == "retry":
            # Retry logic would go here
            pass
        elif step.on_error == "skip":
            # Skip logic - already handled by continuing the loop
            pass
        elif step.on_error == "fail":
            # Re-raise the error
            raise WorkflowExecutorError(f"Step {step.id} failed: {str(error)}") from error
    
    async def execute(self, input_data: InputData) -> Any:
        """Execute the workflow with the given input data
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            The final output of the workflow
            
        Raises:
            WorkflowExecutorError: If workflow execution fails
        """
        # Initialize context with input
        self.context.results["USER_INPUT"] = input_data
        self.context.results["user"] = input_data
        
        # Log workflow start
        logger.info(f"Starting workflow execution: {self.workflow.description}")
        
        # Execute each step in order
        for step in self.workflow.steps:
            logger.info(f"Processing step: {step.id}")
            
            # Check if step should be executed
            if not self.context.should_execute_step(step):
                logger.info(f"Skipping step {step.id} (condition not met)")
                continue
            
            # Get input data for step
            try:
                step_input = self.context.get_input_for_step(step)
            except Exception as e:
                logger.error(f"Failed to get input for step {step.id}: {e}")
                await self.handle_error(step, e)
                continue
            
            # Create step executor
            executor = self.create_step_executor(step)
            
            # Execute step based on mode
            try:
                if step.mode == "serial":
                    result = await ExecutionMode.execute_serial(executor, step_input)
                elif step.mode == "map":
                    result = await ExecutionMode.execute_map(executor, step_input)
                elif step.mode == "parallel":
                    result = await ExecutionMode.execute_parallel(executor, step_input)
                else:
                    raise ValueError(f"Unknown execution mode: {step.mode}")
                
                # Store result in context
                self.context.set_result(step.id, result)
                logger.info(f"Step {step.id} completed successfully")
                
            except Exception as e:
                logger.error(f"Step {step.id} execution failed: {e}")
                await self.handle_error(step, e)
        
        # Get final result
        try:
            output_step = self.workflow.output.step
            final_result = self.context.get_result(output_step)
            logger.info("Workflow completed successfully")
            
            # Save output if configured
            if self.workflow.output.save_to:
                # Implement output saving logic here
                pass
            
            return final_result
            
        except Exception as e:
            logger.error(f"Failed to get workflow output: {e}")
            raise WorkflowExecutorError(f"Failed to get workflow output: {str(e)}") from e

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
        executor.register_tool("echo", echo_tool)
        
        # Execute with sample input
        input_data = {"message": "How many 'r's are in the word 'strawberry'?"}
        result = await executor.execute(input_data)
        print("\nWorkflow result:", result)
    
    # Run the main function
    asyncio.run(main())