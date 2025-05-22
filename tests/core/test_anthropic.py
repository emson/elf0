import pytest
import sys
from unittest.mock import Mock, patch
from elf.core.llm_client import LLMClient
from elf.core.spec import LLM
from elf.core.config import create_llm_config, LLMConfig, get_api_key

def test_get_api_key_validation(monkeypatch):
    """Test that get_api_key properly validates API key requirements."""
    # Remove the API key from environment to test missing key scenario
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    
    # Test missing API key for Anthropic
    with pytest.raises(ValueError, match="Required API key ANTHROPIC_API_KEY"):
        get_api_key("anthropic")
    
    # Test unknown provider
    with pytest.raises(ValueError, match="Unknown provider"):
        get_api_key("unknown")

def test_create_llm_config_validation(monkeypatch):
    """Test that create_llm_config properly validates configuration."""
    # Remove the API key from environment to test missing key scenario
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    
    # Test missing type
    with pytest.raises(ValueError, match="llm_type must be provided or present in config"):
        create_llm_config({"model_name": "claude-3-sonnet-20240229"})
    
    # Test missing API key for Anthropic
    with pytest.raises(ValueError, match="Required API key ANTHROPIC_API_KEY"):
        create_llm_config({
            "type": "anthropic",
            "model_name": "claude-3-sonnet-20240229",
            "temperature": 0.7
        })

def test_claude_sonnet_4_integration(monkeypatch):
    """Test that Claude Sonnet 4 can be used through the LLMClient."""
    # Create a mock for the anthropic module
    mock_anthropic_module = Mock()
    mock_anthropic_client = Mock()
    mock_anthropic_module.Anthropic.return_value = mock_anthropic_client
    
    # Mock the messages.create response
    mock_response = Mock()
    mock_response.content = [Mock(text="4")]
    mock_anthropic_client.messages.create.return_value = mock_response

    # Patch sys.modules to intercept the import of 'anthropic'
    with patch.dict(sys.modules, {'anthropic': mock_anthropic_module}):
        # Create a minimal LLM spec for Claude Sonnet 4
        llm_spec = LLM(
            type="anthropic",
            model_name="claude-3-sonnet-20240229",
            temperature=0.7,
            params={
                "max_tokens": 1000,
                "system_prompt": "You are a helpful AI assistant."
            }
        )
        
        # Create config with API key
        # We need to ensure ANTHROPIC_API_KEY is set for this specific test, 
        # as create_llm_config will try to fetch it if not provided in llm_spec
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fake_key_for_test")
        config = create_llm_config(llm_spec.model_dump(), llm_type="anthropic")
        
        # Verify config has required fields
        assert isinstance(config, LLMConfig)
        assert config.type == "anthropic"
        assert config.model_name == "claude-3-sonnet-20240229"
        
        # Create LLM client
        client = LLMClient(config)
        
        # Test a simple generation
        response = client.generate("What is 2+2?")
        assert isinstance(response, str)
        assert len(response) > 0
        assert response == "4"
        
        # Verify the mock was called correctly
        mock_anthropic_module.Anthropic.assert_called_once_with(api_key="fake_key_for_test")
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]['model'] == "claude-3-sonnet-20240229"
        assert call_args[1]['messages'][0]['content'] == "What is 2+2?" 