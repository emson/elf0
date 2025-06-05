# tests/core/test_structured_output.py

import pytest
from elf.core.spec import Spec


class TestStructuredOutput:
    """Test structured output functionality for Spec models."""
    
    def test_json_to_spec_conversion_success(self):
        """Test that valid JSON converts to Spec and then to clean YAML."""
        # Arrange: Valid JSON matching Spec schema
        valid_json = '''{
            "version": "1.0",
            "description": "Test simulation spec",
            "runtime": "langgraph",
            "llms": {
                "test_llm": {
                    "type": "openai",
                    "model_name": "gpt-4.1-mini",
                    "temperature": 0.3
                }
            },
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "test_node",
                        "kind": "agent",
                        "ref": "test_llm",
                        "config": {
                            "prompt": "Test prompt: {input}"
                        },
                        "output_key": "test_output",
                        "stop": true
                    }
                ],
                "edges": []
            }
        }'''
        
        # Act: Convert JSON to Spec, then to YAML
        spec = Spec.from_structured_json(valid_json)
        yaml_output = spec.to_yaml_string()
        
        # Assert: Verify conversion success and clean output
        assert spec is not None
        assert yaml_output is not None
        assert "```" not in yaml_output  # No markdown fences
        assert yaml_output.strip().startswith("version:")
        assert "test_llm" in yaml_output
        assert "test_node" in yaml_output
    
    def test_json_with_markdown_fences_handling(self):
        """Test that JSON wrapped in markdown fences is handled correctly."""
        # Arrange: JSON with markdown fences (simulating LLM output)
        fenced_json = '''```json
        {
            "version": "1.0",
            "description": "Test with fences",
            "runtime": "langgraph",
            "llms": {
                "sim_llm": {
                    "type": "openai",
                    "model_name": "gpt-4.1-mini"
                }
            },
            "workflow": {
                "type": "sequential",
                "nodes": [
                    {
                        "id": "simple_node",
                        "kind": "agent",
                        "ref": "sim_llm",
                        "config": {
                            "prompt": "Simple test: {input}"
                        },
                        "stop": true
                    }
                ],
                "edges": []
            }
        }
        ```'''
        
        # Act: Convert fenced JSON to Spec
        spec = Spec.from_structured_json(fenced_json)
        yaml_output = spec.to_yaml_string()
        
        # Assert: Verify successful parsing despite fences
        assert spec.version == "1.0"
        assert spec.description == "Test with fences"
        assert len(spec.workflow.nodes) == 1
        assert spec.workflow.nodes[0].id == "simple_node"
        assert "```" not in yaml_output  # Clean output without fences
    
    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises appropriate error."""
        # Arrange: Invalid JSON
        invalid_json = '''{"version": "1.0", "invalid": }'''
        
        # Act & Assert: Verify error handling
        with pytest.raises(ValueError, match="Invalid JSON"):
            Spec.from_structured_json(invalid_json)
    
    def test_json_schema_generation(self):
        """Test that JSON schema is generated for structured output."""
        # Act: Generate schema
        schema = Spec.get_json_schema_for_structured_output()
        
        # Assert: Verify schema contains expected structure
        assert schema is not None
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "version" in schema["properties"]
        assert "runtime" in schema["properties"]
        assert "workflow" in schema["properties"]
    
    def test_spec_validation_with_missing_required_fields(self):
        """Test that Spec validation fails with missing required fields."""
        # Arrange: JSON missing required workflow
        incomplete_json = '''{
            "version": "1.0",
            "runtime": "langgraph",
            "llms": {
                "test_llm": {
                    "type": "openai", 
                    "model_name": "gpt-4.1-mini"
                }
            }
        }'''
        
        # Act & Assert: Verify validation error
        with pytest.raises(ValueError, match="Spec validation error"):
            Spec.from_structured_json(incomplete_json)