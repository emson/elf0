# src/elf/core/config.py
from typing import Any, Dict, Optional, Union
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging # Added logger

# Configure a logger for this module
logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """Configuration for an LLM client."""
    model_name: str
    temperature: float = 0.7
    params: Dict[str, Any] = {}
    api_key: Optional[str] = None

def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from .env file.
    If found, variables are loaded and can override existing system environment variables.
    If not found, the function proceeds silently, allowing reliance on system-set variables.
    
    Args:
        env_path: Optional path to .env file. If not provided, looks for .env in project root.
    """
    # Determine the default path relative to the project root (assuming config.py is in src/elf/core)
    project_root = Path(__file__).parent.parent.parent.parent
    default_path = project_root / '.env'
    
    path_to_use = Path(env_path) if env_path is not None else default_path
    
    if path_to_use.exists():
        # override=True allows .env to take precedence over system variables, useful for local dev
        loaded = load_dotenv(dotenv_path=str(path_to_use), override=True)
        if loaded:
            logger.info(f"Environment variables loaded from: {path_to_use}")
        else:
            logger.warning(f"Found .env file at {path_to_use}, but it might be empty or failed to load.")
    else:
        logger.info(f".env file not found at {path_to_use}. Relying on system environment variables.")

def get_api_key(provider_name: str) -> Optional[str]:
    """
    Get the API key for a provider from environment variables.
    
    Args:
        provider_name: The name of the provider (e.g., 'openai', 'anthropic', 'ollama')
        
    Returns:
        The API key if required and found, None if not required.
        
    Raises:
        ValueError: If the provider requires an API key but none is found in the environment.
    """
    # Providers that don't require API keys
    NO_API_KEY_PROVIDERS = {'ollama'}
    
    provider_name_lower = provider_name.lower()
    if provider_name_lower in NO_API_KEY_PROVIDERS:
        logger.info(f"Provider '{provider_name}' does not require an API key.")
        return None
        
    env_var_name = f"{provider_name.upper()}_API_KEY"
    api_key = os.getenv(env_var_name)
    if not api_key:
        # This error should propagate if the key is genuinely required and missing.
        raise ValueError(f"Required API key {env_var_name} for provider '{provider_name}' not found in environment variables.")
    logger.info(f"API key found for provider '{provider_name}' using environment variable {env_var_name}.")
    return api_key

def create_llm_config(config: Union[Dict[str, Any], LLMConfig], llm_type: Optional[str] = None) -> LLMConfig:
    """
    Create an LLM configuration with API key handling.
    The API key is sourced first from the input config, then from environment variables if needed.
    
    Args:
        config: The LLM configuration dictionary or LLMConfig object.
        llm_type: The type of the LLM provider (e.g., 'openai', 'anthropic'), 
                  used to fetch the correct API key if not already in `config`.
                  If `config` is a dict, `llm_type` can also be inferred from `config['type']`.
                  If `config` is an `LLMConfig` object, `llm_type` can be inferred from `config.type` (if `type` attr exists).
        
    Returns:
        An LLMConfig object with the API key populated if required and found.
        
    Raises:
        ValueError: If a required API key is not found (propagated from get_api_key).
    """
    if isinstance(config, dict):
        current_config_dict = config.copy()
        # Try to determine llm_type if not explicitly passed but available in the config dict
        effective_llm_type = llm_type or current_config_dict.get('type')
    elif isinstance(config, LLMConfig):
        current_config_dict = config.model_dump() # Get dict from Pydantic model
        # Try to determine llm_type if not explicitly passed but available in the config object (assuming it has a 'type' field)
        effective_llm_type = llm_type or getattr(config, 'type', None) 
    else:
        raise TypeError("Input 'config' must be a dictionary or an LLMConfig instance.")

    api_key_to_use: Optional[str] = current_config_dict.get('api_key')

    if not api_key_to_use and effective_llm_type: # API key not in spec, try to load from env
        # get_api_key will return None if not required (e.g., for 'ollama')
        # or raise ValueError if required but not found.
        api_key_to_use = get_api_key(effective_llm_type)
    
    # Update the dictionary with the resolved API key if found (or if it was None for non-key providers)
    if api_key_to_use is not None:
        current_config_dict['api_key'] = api_key_to_use
    elif 'api_key' not in current_config_dict: # Ensure api_key field exists for LLMConfig if not set
        current_config_dict['api_key'] = None

    return LLMConfig(**current_config_dict)

# Load environment variables from .env file when this module is imported.
# This ensures it's done once at the beginning.
load_env_file()