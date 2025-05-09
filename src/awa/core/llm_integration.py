# src/awa/core/llm_integration.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from awa.core.llm_client import BaseLLMClient, LLMResponse
from awa.core.errors import LLMClientError, LLMRateLimitError, LLMConnectionError
from awa.core.models import LLMClientConfig
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAILLMClient(BaseLLMClient):
    """Implementation of BaseLLMClient for OpenAI API"""
    
    def __init__(self, config: LLMClientConfig):
        """Initialize the OpenAI LLM client.
        
        Args:
            config: The LLM client configuration
        """
        self.config = config
        self.client = OpenAI()
        
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send a chat message to OpenAI and get a response.
        
        Args:
            messages: List of message dictionaries with role and content
            **kwargs: Additional parameters for the API call
            
        Returns:
            LLMResponse: The response from OpenAI
        """
        try:
            # Merge default params with kwargs
            params = {**self.config.get_params(), **kwargs}
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                **params
            )
            
            # Parse the response
            content = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            return LLMResponse(
                content=content,
                usage=usage,
                metadata={
                    'model': response.model,
                    'created': response.created
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMClientError(f"OpenAI API error: {str(e)}") from e


# Register the OpenAI client with the registry
from .llm_client import LLMClientRegistry
LLMClientRegistry.register("openai", OpenAILLMClient)


class AgentExecutor:
    """Executes agent steps using the appropriate LLM client"""
    
    def __init__(self, agent: 'AgentDef', global_config: Optional['LLMClient'] = None):
        """Initialize the agent executor.
        
        Args:
            agent: The agent configuration
            global_config: Global LLM client configuration (optional)
        """
        self.agent = agent
        self.global_config = global_config
        
    def _get_llm_config(self) -> 'LLMClient':
        """Get the LLM configuration for this agent.
        
        Returns:
            LLMClient: The LLM client configuration
        """
        if self.agent.llm_client:
            return self.agent.llm_client
        elif self.global_config:
            return self.global_config
        raise ValueError("No LLM client configuration found for agent")
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with the given input data.
        
        Args:
            input_data: The input data for the agent
            
        Returns:
            Dict[str, Any]: The agent's response
        """
        try:
            # Get LLM configuration
            llm_config = self._get_llm_config()
            
            # Create LLM client
            llm_client = self._create_llm_client(llm_config)
            
            # Format messages
            messages = self._format_messages(input_data)
            
            # Execute chat
            response = llm_client.chat(messages)
            
            # Parse and return response
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            raise
            
    def _create_llm_client(self, config: Dict[str, Any]) -> BaseLLMClient:
        """Create the appropriate LLM client.
        
        Args:
            config: The LLM client configuration as a dictionary
            
        Returns:
            BaseLLMClient: The created LLM client
        """
        from .llm_client import LLMClientFactory
        from .llm_client import LLMClientConfig
        
        # Create LLM client configuration
        try:
            llm_config = LLMClientConfig(config)
        except Exception as e:
            logger.error(f"Failed to create LLM client config: {str(e)}")
            raise
        
        return LLMClientFactory.create_client(llm_config)
        
    def _format_messages(self, input_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Format the input data into messages for the LLM.
        
        Args:
            input_data: The input data to format
            
        Returns:
            List[Dict[str, str]]: Formatted messages
        """
        # Format system prompt
        system_msg = {"role": "system", "content": self.agent.system_prompt}
        
        # Format user prompt with input data
        user_msg = {"role": "user", "content": self.agent.user_prompt.format(**input_data)}
        
        return [system_msg, user_msg]
        
    def _parse_response(self, response: LLMResponse) -> Dict[str, Any]:
        """Parse the LLM response.
        
        Args:
            response: The LLM response to parse
            
        Returns:
            Dict[str, Any]: Parsed response data
        """
        if self.agent.output_parser:
            # TODO: Implement output parsing logic
            return {"content": response.content}
        return {"content": response.content}
