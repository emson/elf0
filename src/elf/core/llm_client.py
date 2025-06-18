# src/elf/core/llm_client.py
from typing import TYPE_CHECKING, Any, Protocol

import openai

from .spec import LLM as LLMSpecModel

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam


# Protocol for LLM Providers
class BaseLLMProvider(Protocol):
    """Protocol for LLM provider implementations."""

    def __init__(self, model_name: str, api_key: str | None, temperature: float, params: dict[str, Any]):
        """Initialize the provider.

        Args:
            model_name: The specific model name for this provider.
            api_key: The API key for the provider.
            temperature: The sampling temperature.
            params: Additional provider-specific parameters.
        """
        ...

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a response from the LLM.

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

    def __init__(self, model_name: str, api_key: str | None, temperature: float, params: dict[str, Any]):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.params = params

        if not self.api_key:
            msg = "OpenAI API key is required."
            raise ValueError(msg)
        openai.api_key = self.api_key

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate response using OpenAI."""
        max_tokens = self.params.get("max_tokens")
        # Allow system_prompt from params to override the direct argument for backward compatibility or spec-driven system_prompt
        final_system_prompt = self.params.get("system_prompt", system_prompt)

        messages: list[ChatCompletionMessageParam] = []
        if final_system_prompt:
            messages.append({
                "role": "system",
                "content": str(final_system_prompt)
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Build kwargs dynamically, omitting temperature if it is None or default (1)
        create_kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            **({"max_tokens": max_tokens} if max_tokens is not None else {})
        }

        # Only include temperature if it's not the OpenAI default (1)
        if self.temperature is not None and self.temperature != 1:
            create_kwargs["temperature"] = self.temperature

        try:
            response = openai.chat.completions.create(**create_kwargs)
        except openai.BadRequestError as e:  # type: ignore[attr-defined]
            # Handle models that reject non-default temperature. Retry without it once.
            if ("temperature" in str(e).lower()) and ("unsupported" in str(e).lower()) and ("default" in str(e).lower()):
                create_kwargs.pop("temperature", None)
                response = openai.chat.completions.create(**create_kwargs)
            else:
                raise

        content = response.choices[0].message.content
        return content if content is not None else ""

# Placeholder for Anthropic Provider
class AnthropicProvider(BaseLLMProvider):
    """LLM Provider for Anthropic models."""

    def __init__(self, model_name: str, api_key: str | None, temperature: float, params: dict[str, Any]):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.params = params

        if not self.api_key:
            msg = "Anthropic API key is required."
            raise ValueError(msg)

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            msg = (
                "The 'anthropic' package is required to use AnthropicProvider. "
                "Please install it with: pip install anthropic"
            )
            raise ImportError(
                msg
            )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate response using Anthropic."""
        try:
            # Get parameters with sensible defaults
            max_tokens = self.params.get("max_tokens", 4096)  # Anthropic's default max
            final_system_prompt = self.params.get("system_prompt", system_prompt)

            # Prepare messages
            messages = [{"role": "user", "content": prompt}]

            # Build kwargs for the API call
            kwargs = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }

            # Only add system if it has a value
            if final_system_prompt:
                kwargs["system"] = final_system_prompt

            # Create the completion
            response = self.client.messages.create(**kwargs)

            # Extract and return the response text
            return response.content[0].text

        except Exception as e:
            msg = f"Error generating response from Anthropic (model {self.model_name}): {e!s}"
            raise RuntimeError(
                msg
            )

# Ollama Provider Implementation (Local, no API key)
class OllamaProvider(BaseLLMProvider):
    """LLM Provider for Ollama models."""

    def __init__(self, model_name: str, api_key: str | None, temperature: float, params: dict[str, Any]):
        self.model_name = model_name
        self.temperature = temperature
        self.params = params
        self.base_url = self.params.get("base_url", "http://localhost:11434") # Default Ollama URL

        # For Ollama, we use the openai client but point it to the Ollama server
        # API key is not typically used unless Ollama server is configured to require it.
        self.client = openai.OpenAI(base_url=f"{self.base_url}/v1", api_key="ollama") # api_key can be dummy for local

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate response using Ollama with OpenAI client compatibility."""
        max_tokens = self.params.get("max_tokens")
        final_system_prompt = self.params.get("system_prompt", system_prompt)

        messages: list[ChatCompletionMessageParam] = []
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
            **({"max_tokens": max_tokens} if max_tokens is not None else {})
        )

        content = response.choices[0].message.content
        return content if content is not None else ""

class LLMClient:
    """Client for interacting with LLMs through various providers.
    Dynamically selects the provider and model based on the provided LLM specification.
    """

    _provider_map: dict[str, type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        # Register other providers here
    }

    def __init__(self, llm_spec: LLMSpecModel):
        """Initialize the LLM client with a specific LLM configuration from the spec.

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
            msg = f"Unknown LLM provider type: {provider_type}"
            raise ValueError(msg)

        ProviderClass = self._provider_map[provider_type]

        # The api_key should already be populated in llm_spec by create_llm_config
        self.provider: BaseLLMProvider = ProviderClass(
            model_name=self.spec.model_name,
            api_key=self.spec.api_key, # Assumes api_key is now part of LLMSpecModel or handled by create_llm_config
            temperature=self.spec.temperature,
            params=self.spec.params
        )

    def generate(self, prompt: str) -> str:
        """Generate a response from the configured LLM for the given prompt.

        Args:
            prompt: The input prompt to send to the LLM.

        Returns:
            The generated response text.

        Raises:
            RuntimeError: If there's an error generating a response.
        """
        try:
            # System prompt can be part of params in the spec
            system_prompt_from_spec = self.spec.params.get("system_prompt")
            return self.provider.generate(prompt, system_prompt=system_prompt_from_spec) # type: ignore
        except Exception as e:
            # Catch potential NotImplementedError from Anthropic placeholder
            if isinstance(e, NotImplementedError):
                raise
            msg = f"Error generating response from LLM provider {self.spec.type} (model {self.spec.model_name}): {e!s}"
            raise RuntimeError(msg)

# Example of how create_llm_config from config.py would be used with LLMSpecModel
# This is conceptual, as the actual instantiation will happen in the compiler.
#
# from .config import create_llm_config
#
# raw_spec_from_yaml = {
#     'type': 'openai',
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
# config_with_api_key = create_llm_config(pydantic_llm_spec.model_dump(), llm_type=pydantic_llm_spec.type)
#
# # 3. Update the pydantic_llm_spec with the api_key from config_with_api_key
# # This step is crucial: LLMSpecModel needs an api_key field or create_llm_config needs to return LLMSpecModel
# # Assuming LLMSpecModel will be updated to include an Optional[str] api_key field:
# # pydantic_llm_spec_with_key = LLMSpecModel(**config_with_api_key.model_dump())
#
# # 4. Then, LLMClient can be initialized
# # client = LLMClient(pydantic_llm_spec_with_key)
