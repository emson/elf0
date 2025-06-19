
import pytest

from elf0.utils.yaml_loader import (
    load_yaml_file,
    load_yaml_files,
    merge_yaml_data,
    save_yaml_file,
)

# Test data
VALID_YAML_CONTENT = """
version: "0.1"
description: "Test spec"
llms:
  llm1:
    type: openai
    model_name: gpt-4.1-mini
    temperature: 0.5
workflow:
  type: sequential
  nodes:
    - id: start
      kind: agent
      ref: llm1
  edges: []
"""

def test_load_yaml_file(tmp_path):
    """Test loading a valid YAML file."""
    # Arrange
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(VALID_YAML_CONTENT)

    # Act
    data = load_yaml_file(str(yaml_file))

    # Assert
    assert data["version"] == "0.1"
    assert data["description"] == "Test spec"
    assert "llms" in data
    assert "workflow" in data

def test_load_yaml_file_not_found():
    """Test loading a non-existent YAML file."""
    # Act & Assert
    with pytest.raises(FileNotFoundError):
        load_yaml_file("nonexistent.yaml")

def test_load_yaml_file_invalid_yaml(tmp_path):
    """Test loading an invalid YAML file."""
    # Arrange
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("invalid: yaml: content: [")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        load_yaml_file(str(yaml_file))
    assert "Error parsing YAML file" in str(exc_info.value)

def test_load_yaml_files(tmp_path):
    """Test loading multiple YAML files from a directory."""
    # Arrange
    (tmp_path / "file1.yaml").write_text("key1: value1")
    (tmp_path / "file2.yaml").write_text("key2: value2")

    # Act
    data = load_yaml_files(str(tmp_path))

    # Assert
    assert len(data) == 2
    assert "file1" in data
    assert "file2" in data
    assert data["file1"]["key1"] == "value1"
    assert data["file2"]["key2"] == "value2"

def test_save_yaml_file(tmp_path):
    """Test saving data to a YAML file."""
    # Arrange
    data = {"key": "value", "nested": {"key": "value"}}
    yaml_file = tmp_path / "output.yaml"

    # Act
    save_yaml_file(str(yaml_file), data)

    # Assert
    assert yaml_file.exists()
    loaded_data = load_yaml_file(str(yaml_file))
    assert loaded_data == data

def test_merge_yaml_data():
    """Test merging YAML data dictionaries."""
    # Arrange
    base = {
        "key1": "value1",
        "nested": {"key": "value"},
        "list": [1, 2, 3]
    }
    override = {
        "key2": "value2",
        "nested": {"key": "new_value"},
        "list": [4, 5, 6]
    }

    # Act
    result = merge_yaml_data(base, override)

    # Assert
    assert result["key1"] == "value1"  # Preserved from base
    assert result["key2"] == "value2"  # Added from override
    assert result["nested"]["key"] == "new_value"  # Overridden
    assert result["list"] == [1, 2, 3, 4, 5, 6]  # Concatenated
