# src/elf/core/llm_client.py
from typing import Any, Dict, List, Protocol, Optional, Union
import openai
from openai.types.chat import ChatCompletionMessageParam
from .config import create_llm_config
from .spec import LLM as LLMSpecModel

# Protocol for LLM Providers
class BaseLLMProvider(Protocol):
    """Protocol for LLM provider implementations."""
    
    def __init__(self, model_name: str, api_key: Optional[str], temperature: float, params: Dict[str, Any]):
        """
        Initialize the provider.
        
        Args:
            model_name: The specific model name for this provider.
            api_key: The API key for the provider.
            temperature: The sampling temperature.
            params: Additional provider-specific parameters.
        """
        ...

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user input prompt.
            system_prompt: An optional system prompt.
            
        Returns:
            The generated response text.
        """
        ...

# OpenAI Provider Implementation
class OpenAIProvider(BaseLLMProvider):
    """LLM Provider for OpenAI models."""
    
    def __init__(self, model_name: str, api_key: Optional[str], temperature: float, params: Dict[str, Any]):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.params = params
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required.")
        openai.api_key = self.api_key

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using OpenAI."""
        max_tokens = self.params.get('max_tokens')
        # Allow system_prompt from params to override the direct argument for backward compatibility or spec-driven system_prompt
        final_system_prompt = self.params.get('system_prompt', system_prompt)

        messages: List[ChatCompletionMessageParam] = []
        if final_system_prompt:
            messages.append({
                "role": "system",
                "content": str(final_system_prompt)
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        return content if content is not None else ""

# Placeholder for Anthropic Provider
class AnthropicProvider(BaseLLMProvider):
    """LLM Provider for Anthropic models (Placeholder)."""
    
    def __init__(self, model_name: str, api_key: Optional[str], temperature: float, params: Dict[str, Any]):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.params = params
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required.")
        
        # Placeholder: Initialize Anthropic client here
        # import anthropic # Example
        # self.client = anthropic.Anthropic(api_key=self.api_key)


    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Anthropic (Placeholder)."""
        # Placeholder: Implement Anthropic API call
        # final_system_prompt = self.params.get('system_prompt', system_prompt)
        # max_tokens = self.params.get('max_tokens', 2048) # Anthropic uses max_tokens_to_sample
        
        # response = self.client.messages.create(
        #     model=self.model_name,
        #     max_tokens=max_tokens,
        #     temperature=self.temperature,
        #     system=final_system_prompt,
        #     messages=[
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        # return response.content[0].text
        raise NotImplementedError(
            f"AnthropicProvider for model {self.model_name} is not yet implemented. "
            f"Prompt: {prompt[:100]}..., System Prompt: {system_prompt}"
        )

# Ollama Provider Implementation (Local, no API key)
class OllamaProvider(BaseLLMProvider):
    """LLM Provider for Ollama models."""

    def __init__(self, model_name: str, api_key: Optional[str], temperature: float, params: Dict[str, Any]):
        self.model_name = model_name
        self.temperature = temperature
        self.params = params
        self.base_url = self.params.get('base_url', 'http://localhost:11434') # Default Ollama URL
        
        # For Ollama, we use the openai client but point it to the Ollama server
        # API key is not typically used unless Ollama server is configured to require it.
        self.client = openai.OpenAI(base_url=f"{self.base_url}/v1", api_key="ollama") # api_key can be dummy for local

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Ollama with OpenAI client compatibility."""
        max_tokens = self.params.get('max_tokens')
        final_system_prompt = self.params.get('system_prompt', system_prompt)

        messages: List[ChatCompletionMessageParam] = []
        if final_system_prompt:
            messages.append({
                "role": "system",
                "content": str(final_system_prompt)
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens # type: ignore
        )
        
        content = response.choices[0].message.content
        return content if content is not None else ""

class LLMClient:
    """
    Client for interacting with LLMs through various providers.
    Dynamically selects the provider and model based on the provided LLM specification.
    """
    
    _provider_map: Dict[str, type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        # Register other providers here
    }

    def __init__(self, llm_spec: LLMSpecModel):
        """
        Initialize the LLM client with a specific LLM configuration from the spec.
        
        Args:
            llm_spec: An LLMSpecModel object containing the LLM configuration
                      (type, model_name, temperature, params, api_key).
                      The `create_llm_config` function from `config.py` should
                      be used to populate the `api_key` field in `llm_spec`
                      before passing it to this constructor.
                      
        Raises:
            ValueError: If the provider type in llm_spec is unknown or if API key is missing when required.
        """
        self.spec = llm_spec
        
        provider_type = self.spec.type
        if provider_type not in self._provider_map:
            raise ValueError(f"Unknown LLM provider type: {provider_type}")
            
        ProviderClass = self._provider_map[provider_type]
        
        # The api_key should already be populated in llm_spec by create_llm_config
        self.provider: BaseLLMProvider = ProviderClass(
            model_name=self.spec.model_name,
            api_key=self.spec.api_key, # Assumes api_key is now part of LLMSpecModel or handled by create_llm_config
            temperature=self.spec.temperature,
            params=self.spec.params
        )
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the configured LLM for the given prompt.
        
        Args:
            prompt: The input prompt to send to the LLM.
            
        Returns:
            The generated response text.
            
        Raises:
            RuntimeError: If there's an error generating a response.
        """
        try:
            # System prompt can be part of params in the spec
            system_prompt_from_spec = self.spec.params.get('system_prompt')
            return self.provider.generate(prompt, system_prompt=system_prompt_from_spec) # type: ignore
        except Exception as e:
            # Catch potential NotImplementedError from Anthropic placeholder
            if isinstance(e, NotImplementedError):
                raise e
            raise RuntimeError(f"Error generating response from LLM provider {self.spec.type} (model {self.spec.model_name}): {str(e)}")

# Example of how create_llm_config from config.py would be used with LLMSpecModel
# This is conceptual, as the actual instantiation will happen in the compiler.
#
# from .config import create_llm_config
#
# raw_spec_from_yaml = {
#     '_type': 'openai',
#     'model_name': 'gpt-4o-mini',
#     'temperature': 0.5,
#     'params': {'max_tokens': 100}
# }
#
# # 1. Create the Pydantic model from the raw dict
# pydantic_llm_spec = LLMSpecModel(**raw_spec_from_yaml)
#
# # 2. Populate/override API key using create_llm_config
# # create_llm_config now needs the llm_type to fetch the correct key
# config_with_api_key = create_llm_config(pydantic_llm_spec.model_dump(), llm_type=pydantic_llm_spec._type)
#
# # 3. Update the pydantic_llm_spec with the api_key from config_with_api_key
# # This step is crucial: LLMSpecModel needs an api_key field or create_llm_config needs to return LLMSpecModel
# # Assuming LLMSpecModel will be updated to include an Optional[str] api_key field:
# # pydantic_llm_spec_with_key = LLMSpecModel(**config_with_api_key.model_dump())
#
# # 4. Then, LLMClient can be initialized
# # client = LLMClient(pydantic_llm_spec_with_key)