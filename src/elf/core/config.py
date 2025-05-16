# src/elf/core/config.py
from typing import Any, Dict, Optional, Union
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

class LLMConfig(BaseModel):
    """Configuration for an LLM client."""
    model_name: str
    temperature: float = 0.7
    params: Dict[str, Any] = {}
    api_key: Optional[str] = None

def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Optional path to .env file. If not provided, looks for .env in project root.
    """
    default_path = Path(__file__).parent.parent.parent.parent / '.env'
    
    path_to_use = Path(env_path) if env_path is not None else default_path
    
    if path_to_use.exists():
        load_dotenv(str(path_to_use))
    else:
        raise FileNotFoundError(f"No .env file found at {path_to_use}")

def get_api_key(provider_name: str) -> str:
    """
    Get API key for a given provider from environment variables.
    
    Args:
        provider_name: The name of the provider (e.g., 'openai', 'anthropic').
        
    Returns:
        The API key for the specified provider.
        
    Raises:
        ValueError: If the API key for the provider is not set in environment.
    """
    env_var_name = f"{provider_name.upper()}_API_KEY"
    api_key = os.getenv(env_var_name)
    if not api_key:
        raise ValueError(f"{env_var_name} not found in environment variables")
    return api_key

def create_llm_config(config: Union[Dict[str, Any], LLMConfig], llm_type: Optional[str] = None) -> LLMConfig:
    """
    Create an LLMConfig instance from a dictionary or existing LLMConfig, adding API key from environment.
    
    Args:
        config: Either a dictionary containing LLM configuration parameters or an existing LLMConfig instance.
        llm_type: The type of the LLM provider (e.g., 'openai', 'anthropic'), used to fetch the correct API key.
        
    Returns:
        An LLMConfig instance with API key from environment.
    """
    api_key_to_use = None
    if llm_type: # llm_type is available (e.g. from spec.type)
        api_key_to_use = get_api_key(llm_type)
    elif isinstance(config, dict) and 'type' in config: # llm_type not passed, but type is in dict
        api_key_to_use = get_api_key(config['type'])
    elif not isinstance(config, dict) and hasattr(config, 'type'): # llm_type not passed, config is LLMConfig obj
         # This case might not be hit if llm_type is always passed from spec
        api_key_to_use = get_api_key(config.type) # type: ignore
    else:
        # Fallback or raise error if API key cannot be determined.
        # For now, let's try OpenAI as a default if no type is specified and key is needed.
        # This maintains some backward compatibility if an old-style config without type is passed.
        try:
            api_key_to_use = get_api_key('openai')
        except ValueError:
            # If OPENAI_API_KEY is not found, and no other type is specified,
            # we might not need an API key (e.g. for local Ollama models).
            # So, we allow api_key to remain None.
            pass


    if isinstance(config, dict):
        # If it's a dictionary, create a new config.
        # Ensure 'api_key' from input dict doesn't override the fetched one.
        config_dict = {k: v for k, v in config.items() if k != 'api_key'}
        return LLMConfig(**config_dict, api_key=api_key_to_use) # type: ignore
    else:
        # If it's already an LLMConfig, create a new one with the updated api_key.
        config_dict = config.model_dump(exclude={'api_key'})
        return LLMConfig(**config_dict, api_key=api_key_to_use)