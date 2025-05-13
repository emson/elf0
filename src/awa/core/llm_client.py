from typing import Any, Dict
import openai
from .config import LLMConfig, create_llm_config

class LLMClient:
    """Client for interacting with LLMs through OpenAI's API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM client with configuration."""
        self.config = create_llm_config(config)
        openai.api_key = self.config.api_key
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM for the given prompt.
        
        Args:
            prompt: The input prompt to send to the LLM
            
        Returns:
            The generated response text
        """
        try:
            # Get max_tokens from params if it exists
            max_tokens = self.config.params.get('max_tokens')
            
            # Create messages array with system prompt if it exists
            messages = []
            if 'system_prompt' in self.config.params:
                messages.append({
                    "role": "system",
                    "content": self.config.params['system_prompt']
                })
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = openai.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Error generating response from LLM: {str(e)}") 