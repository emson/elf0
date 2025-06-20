# src/elf/utils/yaml_loader.py
from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(file_path: str) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary.

    Args:
        file_path: Path to the YAML file to load

    Returns:
        The parsed YAML content as a dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"YAML file not found: {file_path}"
        raise FileNotFoundError(msg)

    raw = path.read_text()
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as e:
        msg = f"Error parsing YAML file {file_path}: {e!s}"
        raise yaml.YAMLError(msg) from e

def load_yaml_files(directory: str, pattern: str = "*.yaml") -> dict[str, dict[str, Any]]:
    """Load all YAML files matching a pattern in a directory.

    Args:
        directory: Path to the directory to search
        pattern: Glob pattern to match files (default: "*.yaml")

    Returns:
        Dictionary mapping filenames to parsed YAML content
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        msg = f"Directory not found: {directory}"
        raise FileNotFoundError(msg)

    result = {}
    for yaml_file in path.glob(pattern):
        result[yaml_file.stem] = load_yaml_file(str(yaml_file))

    return result

def save_yaml_file(file_path: str, data: dict[str, Any]) -> None:
    """Save a dictionary as a YAML file.

    Args:
        file_path: Path where to save the YAML file
        data: Dictionary to save as YAML
    """
    path = Path(file_path)

    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def merge_yaml_data(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge two YAML data dictionaries, with override taking precedence.

    Args:
        base: Base dictionary to merge into
        override: Dictionary with values that override the base

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        # If both values are dictionaries, merge them recursively
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_yaml_data(result[key], value)
        # If both values are lists, concatenate them
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        # Otherwise, override the value
        else:
            result[key] = value

    return result
