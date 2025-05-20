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

def get_api_key(provider_name: str) -> Optional[str]:
    """
    Get the API key for a provider from environment variables.
    
    Args:
        provider_name: The name of the provider (e.g., 'openai', 'anthropic', 'ollama')
        
    Returns:
        The API key if required and found, None if not required or not found
        
    Raises:
        ValueError: If the provider requires an API key but none is found
    """
    # Providers that don't require API keys
    NO_API_KEY_PROVIDERS = {'ollama'}
    
    if provider_name.lower() in NO_API_KEY_PROVIDERS:
        return None
        
    env_var_name = f"{provider_name.upper()}_API_KEY"
    api_key = os.getenv(env_var_name)
    if not api_key:
        raise ValueError(f"{env_var_name} not found in environment variables")
    return api_key

def create_llm_config(config: Union[Dict[str, Any], LLMConfig], llm_type: Optional[str] = None) -> LLMConfig:
    """
    Create an LLM configuration with API key handling.
    
    Args:
        config: The LLM configuration dictionary or LLMConfig object
        llm_type: The type of the LLM provider (e.g., 'openai', 'anthropic'), used to fetch the correct API key.
        
    Returns:
        An LLMConfig object with the API key populated if required
    """
    api_key_to_use = None
    if llm_type: # llm_type is available (e.g. from spec.type)
        try:
            api_key_to_use = get_api_key(llm_type)
        except ValueError as e:
            # If the provider doesn't require an API key, continue without one
            if "not found in environment variables" in str(e):
                pass
            else:
                raise
    elif isinstance(config, dict) and 'type' in config: # llm_type not passed, but type is in dict
        try:
            api_key_to_use = get_api_key(config['type'])
        except ValueError as e:
            if "not found in environment variables" in str(e):
                pass
            else:
                raise
    elif not isinstance(config, dict) and hasattr(config, 'type'): # llm_type not passed, config is LLMConfig obj
        try:
            api_key_to_use = get_api_key(config.type)
        except ValueError as e:
            if "not found in environment variables" in str(e):
                pass
            else:
                raise
    
    # Create or update the config
    if isinstance(config, dict):
        config_dict = config.copy()
        if api_key_to_use is not None:
            config_dict['api_key'] = api_key_to_use
        return LLMConfig(**config_dict)
    else:
        if api_key_to_use is not None:
            config.api_key = api_key_to_use
        return config