import pytest

from elf0.core.config import LLMConfig, create_llm_config, get_api_key
from elf0.core.spec import LLM


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

def test_anthropic_config_creation(monkeypatch):
    """Test that Anthropic configuration is created correctly."""
    # Set API key for configuration
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

    # Create a minimal LLM spec for Claude
    llm_spec = LLM(
        type="anthropic",
        model_name="claude-3-sonnet-20240229",
        temperature=0.7,
        params={
            "max_tokens": 1000,
            "system_prompt": "You are a helpful AI assistant."
        }
    )

    # Create config
    config = create_llm_config(llm_spec.model_dump(), llm_type="anthropic")

    # Verify config has required fields
    assert isinstance(config, LLMConfig)
    assert config.type == "anthropic"
    assert config.model_name == "claude-3-sonnet-20240229"
    assert config.temperature == 0.7
    assert config.api_key == "test_key"
    assert config.params["max_tokens"] == 1000
    assert config.params["system_prompt"] == "You are a helpful AI assistant."
