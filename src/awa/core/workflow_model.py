# src/awa/core/workflow_model.py

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic.functional_validators import AfterValidator
from datetime import datetime
import re
from pathlib import Path


class LLMClient(BaseModel):
    """Configuration for LLM client"""
    type: str = Field(
        description="Type of LLM client (e.g., 'openai', 'anthropic')",
        examples=["openai", "anthropic", "local_vllm"]
    )
    model: str = Field(
        description="Model name to use",
        examples=["gpt-4", "claude-3"]
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters for the LLM client"
    )


class ToolDef(BaseModel):
    """Definition of a tool that can be used in the workflow"""
    id: str = Field(
        description="Unique identifier for the tool",
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    description: str = Field(
        description="Brief description of what the tool does"
    )


class AgentDef(BaseModel):
    """Definition of an agent that executes steps in the workflow"""
    id: str = Field(
        description="Unique identifier for the agent",
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    llm_client: Optional[LLMClient] = Field(
        default=None,
        description="LLM client configuration for this agent (optional if using defaults)"
    )
    system_prompt: str = Field(
        description="System prompt for the agent"
    )
    user_prompt: str = Field(
        description="User prompt template for the agent"
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="List of tool IDs this agent can use"
    )
    output_parser: Optional[str] = Field(
        default=None,
        description="Output parser to use for this agent's responses"
    )


class StepInput(BaseModel):
    """Input configuration for a workflow step"""
    source: str = Field(
        description="Source of the input (e.g., 'USER_INPUT' or previous step ID)"
    )
    key: Optional[str] = Field(
        default=None,
        description="Optional key to extract from the source if it's a dictionary"
    )


class StepBranch(BaseModel):
    """Branching configuration for workflow steps"""
    source: str = Field(
        description="Source to branch on"
    )
    cases: Dict[str, str] = Field(
        description="Mapping of case values to next step IDs"
    )


class StepDef(BaseModel):
    """Definition of a workflow step"""
    id: str = Field(
        description="Unique identifier for the step",
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    agent_id: Optional[str] = Field(
        default=None,
        description="ID of the agent to execute this step"
    )
    tool_id: Optional[str] = Field(
        default=None,
        description="ID of the tool to use for this step"
    )
    workflow: Optional[str] = Field(
        default=None,
        description="Path to nested workflow YAML file"
    )
    input: StepInput = Field(
        description="Input configuration for this step"
    )
    mode: Literal["serial", "map", "parallel"] = Field(
        default="serial",
        description="Execution mode for this step"
    )
    branch: Optional[StepBranch] = Field(
        default=None,
        description="Branching configuration for this step"
    )
    condition: Optional[str] = Field(
        default=None,
        description="Jinja expression to conditionally execute this step"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to override for this step's LLM client"
    )
    tool_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to pass to the tool"
    )
    on_error: Literal["retry", "skip", "fail"] = Field(
        default="fail",
        description="Error handling strategy"
    )
    max_retries: Optional[int] = Field(
        default=None,
        description="Maximum number of retries on error"
    )

    @model_validator(mode='after')
    def validate_step_type(cls, values):
        """Ensure exactly one of agent_id, tool_id, or workflow is provided"""
        step_types = [values.agent_id, values.tool_id, values.workflow]
        if sum(1 for x in step_types if x is not None) != 1:
            raise ValueError("Exactly one of agent_id, tool_id, or workflow must be provided")
        return values


class OutputDef(BaseModel):
    """Configuration for workflow output"""
    step: str = Field(
        description="ID of the step that produces the final output"
    )
    save_to: Optional[Dict[str, str]] = Field(
        default=None,
        description="Configuration for saving the output"
    )


class Workflow(BaseModel):
    """Main workflow model"""
    version: str = Field(
        description="Version of the workflow schema",
        pattern=r"^\d+\.\d+(\.\d+)?$"
    )
    description: str = Field(
        description="Human-readable description of the workflow's purpose"
    )
    defaults: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Global defaults for LLM client configuration"
    )
    tools: List[ToolDef] = Field(
        default_factory=list,
        description="List of tools available in the workflow"
    )
    agents: List[AgentDef] = Field(
        description="List of agents that can execute steps"
    )
    steps: List[StepDef] = Field(
        description="Ordered list of steps to execute"
    )
    output: OutputDef = Field(
        description="Configuration for the workflow output"
    )

    model_config = ConfigDict(
        strict=True,
        extra='forbid',
        validate_assignment=True
    )

    @model_validator(mode='after')
    def validate_ids(cls, values):
        """Validate that all referenced IDs exist in their respective lists"""
        # Validate agent IDs in steps
        agent_ids = {agent.id for agent in values.agents}
        for step in values.steps:
            if step.agent_id and step.agent_id not in agent_ids:
                raise ValueError(f"Step references non-existent agent: {step.agent_id}")

        # Validate tool IDs in steps
        tool_ids = {tool.id for tool in values.tools}
        for step in values.steps:
            if step.tool_id and step.tool_id not in tool_ids:
                raise ValueError(f"Step references non-existent tool: {step.tool_id}")

        return values

    @model_validator(mode='after')
    def validate_output_step(cls, values):
        """Validate that the output step exists"""
        output_step_id = values.output.step
        step_ids = {step.id for step in values.steps}
        if output_step_id and output_step_id not in step_ids:
            raise ValueError(f"Output references non-existent step: {output_step_id}")
        return values