# src/awa/core/llm_client.py

from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Base model for LLM responses"""
    content: str = Field(
        description="The main content of the response"
    )
    usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token usage statistics"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata from the LLM response"
    )


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def chat(self, messages: list[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send a chat message to the LLM and get a response.
        
        Args:
            messages: List of message dictionaries with role and content
            **kwargs: Additional parameters for the LLM call
            
        Returns:
            LLMResponse: The response from the LLM
        """
        pass


class LLMClientRegistry:
    """Registry for different LLM client implementations"""
    _registry: Dict[str, Type[BaseLLMClient]] = {}
    _instances: Dict[str, BaseLLMClient] = {}
    
    @classmethod
    def register(cls, client_type: str, client_class: Type[BaseLLMClient]) -> None:
        """Register a new LLM client implementation.
        
        Args:
            client_type: The type identifier for the client
            client_class: The client implementation class
        """
        cls._registry[client_type] = client_class
        
    @classmethod
    @lru_cache(maxsize=128)
    def get_client(cls, config: 'LLMClient') -> BaseLLMClient:
        """Get an instance of the appropriate LLM client based on configuration.
        
        Args:
            config: The LLM client configuration
            
        Returns:
            BaseLLMClient: An instance of the appropriate client
            
        Raises:
            ValueError: If no client implementation is registered for the type
        """
        # Create a hashable key from the configuration
        key = f"{config.type}-{config.model}"
        
        # Check if we already have an instance
        if key in cls._instances:
            return cls._instances[key]
            
        # Get the appropriate client class
        client_class = cls._registry.get(config.type)
        if not client_class:
            raise ValueError(f"No LLM client implementation registered for type: {config.type}")
            
        # Create and cache the instance
        instance = client_class(config)
        cls._instances[key] = instance
        return instance


class LLMClientConfig:
    """Configuration for LLM clients"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM client configuration.
        
        Args:
            config: Dictionary containing LLM client configuration
        """
        self.type = config.get('type')
        self.model = config.get('model')
        self.params = config.get('params', {})
        
    def get_params(self) -> Dict[str, Any]:
        """Get all parameters for the LLM client.
        
        Returns:
            Dict[str, Any]: Combined parameters from config and defaults
        """
        return self.params


class LLMClientFactory:
    """Factory for creating LLM clients based on configuration"""
    
    @staticmethod
    def create_client(config: 'LLMClient') -> BaseLLMClient:
        """Create an LLM client instance based on configuration.
        
        Args:
            config: The LLM client configuration
            
        Returns:
            BaseLLMClient: An instance of the appropriate client
        """
        return LLMClientRegistry.get_client(config)


class LLMClientError(Exception):
    """Base exception for LLM client errors"""
    pass


class LLMRateLimitError(LLMClientError):
    """Raised when the LLM API rate limit is exceeded"""
    pass


class LLMConnectionError(LLMClientError):
    """Raised when there's a connection issue with the LLM API"""
    pass
