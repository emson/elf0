# src/elf/utils/yaml_loader.py
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents as a dictionary.
    
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
        raise FileNotFoundError(f"YAML file not found: {file_path}")
        
    raw = path.read_text()
    try:
        data = yaml.safe_load(raw)
        return data
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {str(e)}")

def load_yaml_files(directory: str, pattern: str = "*.yaml") -> Dict[str, Dict[str, Any]]:
    """
    Load all YAML files matching a pattern in a directory.
    
    Args:
        directory: Path to the directory to search
        pattern: Glob pattern to match files (default: "*.yaml")
        
    Returns:
        Dictionary mapping filenames to parsed YAML content
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")
        
    result = {}
    for yaml_file in path.glob(pattern):
        result[yaml_file.stem] = load_yaml_file(str(yaml_file))
        
    return result

def save_yaml_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save a dictionary as a YAML file.
    
    Args:
        file_path: Path where to save the YAML file
        data: Dictionary to save as YAML
    """
    path = Path(file_path)
    
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open('w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def merge_yaml_data(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two YAML data dictionaries, with override taking precedence.
    
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

# Maintain backward compatibility
def load_spec(path: str) -> Any:
    """
    Load and validate a YAML spec file into a Spec model.
    For backward compatibility - imports Spec here to avoid circular import.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Validated Spec object
    """
    from elf.core.spec import Spec
    
    data = load_yaml_file(path)
    try:
        spec = Spec.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Spec validation error: {e}")
    return spec