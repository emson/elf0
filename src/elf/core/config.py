# src/elf/core/config.py
from typing import Any, Dict, Optional, Union, Literal
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging # Added logger

# Configure a logger for this module
logger = logging.getLogger(__name__)

# Central provider configuration
PROVIDER_CONFIG = {
    'openai': {'requires_api_key': True},
    'anthropic': {'requires_api_key': True},
    'ollama': {'requires_api_key': False}
}

class LLMConfig(BaseModel):
    """Configuration for an LLM client."""
    type: Literal['openai', 'anthropic', 'ollama']  # Added type field
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
            logger.info(f"[dim]Environment loaded from {path_to_use.name}[/dim]")
        else:
            logger.warning("[yellow]⚠ .env file found but empty or failed to load[/yellow]")
    else:
        logger.info("[dim]No .env file - using system environment[/dim]")

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
    provider_name_lower = provider_name.lower()
    
    # Check if provider exists in configuration
    if provider_name_lower not in PROVIDER_CONFIG:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    # Check if provider requires API key
    if not PROVIDER_CONFIG[provider_name_lower]['requires_api_key']:
        logger.info(f"[dim]Provider {provider_name} - no API key required[/dim]")
        return None
        
    env_var_name = f"{provider_name.upper()}_API_KEY"
    api_key = os.getenv(env_var_name)
    
    # Explicitly check for missing API key
    if api_key is None or api_key.strip() == "":
        raise ValueError(f"Required API key {env_var_name}")
        
    logger.info(f"[green]✓ API key found for {provider_name}[/green]")
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
                  If `config` is an `LLMConfig` object, `llm_type` can be inferred from `config.type`.
        
    Returns:
        An LLMConfig object with the API key populated if required and found.
        
    Raises:
        ValueError: If a required API key is not found (propagated from get_api_key).
        ValueError: If llm_type is not provided and cannot be inferred from config.
    """
    if isinstance(config, dict):
        current_config_dict = config.copy()
        # Try to determine llm_type if not explicitly passed but available in the config dict
        effective_llm_type = llm_type or current_config_dict.get('type')
    elif isinstance(config, LLMConfig):
        current_config_dict = config.model_dump() # Get dict from Pydantic model
        # Try to determine llm_type if not explicitly passed but available in the config object
        effective_llm_type = llm_type or getattr(config, 'type', None)
    else:
        raise TypeError("Input 'config' must be a dictionary or an LLMConfig instance.")

    if not effective_llm_type:
        raise ValueError("llm_type must be provided or present in config")

    # Ensure type is set in the config
    current_config_dict['type'] = effective_llm_type

    # Handle API key
    api_key_to_use: Optional[str] = current_config_dict.get('api_key')
    
    # Always try to get API key - get_api_key will handle the validation
    if not api_key_to_use:
        api_key_to_use = get_api_key(effective_llm_type)
    
    # Update the dictionary with the resolved API key
    current_config_dict['api_key'] = api_key_to_use

    return LLMConfig(**current_config_dict)

# Load environment variables from .env file when this module is imported.
# This ensures it's done once at the beginning.
load_env_file()