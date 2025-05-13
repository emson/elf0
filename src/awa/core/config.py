# src/awa/core/config.py
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

def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment variables.
    
    Returns:
        The OpenAI API key
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set in environment
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return api_key

def create_llm_config(config: Union[Dict[str, Any], LLMConfig]) -> LLMConfig:
    """
    Create an LLMConfig instance from a dictionary or existing LLMConfig, adding API key from environment.
    
    Args:
        config: Either a dictionary containing LLM configuration parameters or an existing LLMConfig instance
        
    Returns:
        An LLMConfig instance with API key from environment
    """
    if isinstance(config, dict):
        # If it's a dictionary, create a new config without the api_key
        config_dict = {k: v for k, v in config.items() if k != 'api_key'}
        return LLMConfig(**config_dict, api_key=get_openai_api_key())
    else:
        # If it's already an LLMConfig, create a new one with the updated api_key
        config_dict = config.model_dump(exclude={'api_key'})
        return LLMConfig(**config_dict, api_key=get_openai_api_key())