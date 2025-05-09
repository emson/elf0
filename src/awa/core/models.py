# src/awa/core/models.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class LLMClientConfig(BaseModel):
    """Configuration for an LLM client"""
    type: str = Field(..., description="Type of LLM client (e.g., 'openai', 'anthropic')")
    model: str = Field(..., description="Model name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")

class ToolConfig(BaseModel):
    """Configuration for a tool"""
    id: str = Field(..., description="Unique identifier for the tool")
    description: str = Field(..., description="Description of the tool")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")

class AgentConfig(BaseModel):
    """Configuration for an agent"""
    id: str = Field(..., description="Unique identifier for the agent")
    system_prompt: str = Field(..., description="System prompt for the agent")
    user_prompt: str = Field(..., description="User prompt template")
    llm_client: Optional[LLMClientConfig] = Field(None, description="LLM client configuration")
    tools: list[str] = Field(default_factory=list, description="List of tool IDs")
    output_parser: str = Field(..., description="Output parser type")
