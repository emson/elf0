# src/awa/core/workflow_loader.py
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import ValidationError
from awa.core.workflow_model import Workflow


class WorkflowLoaderError(Exception):
    """Base exception for workflow loading errors"""
    pass

class WorkflowLoader:
    """Loads and validates workflow YAML files"""
    
    def __init__(self, yaml_path: Path):
        """
        Initialize the loader with a YAML file path
        
        Args:
            yaml_path: Path to the workflow YAML file
        """
        self.yaml_path = yaml_path
        self._raw_data: Optional[Dict[str, Any]] = None
        self._workflow: Optional[Workflow] = None

    def load(self) -> Workflow:
        """
        Load and validate the workflow YAML file
        
        Returns:
            Workflow: Validated workflow model
            
        Raises:
            WorkflowLoaderError: If there are any issues loading or validating the workflow
        """
        try:
            self._read_yaml()
            self._validate_data()
            return self._workflow
        except Exception as e:
            raise WorkflowLoaderError(f"Failed to load workflow: {str(e)}") from e

    def _read_yaml(self) -> None:
        """Read the YAML file into raw data"""
        try:
            with open(self.yaml_path, 'r') as f:
                self._raw_data = yaml.safe_load(f)
            if not self._raw_data:
                raise ValueError("Workflow file is empty")
        except yaml.YAMLError as e:
            raise WorkflowLoaderError(f"YAML parsing error: {str(e)}")
        except FileNotFoundError:
            raise WorkflowLoaderError(f"Workflow file not found: {self.yaml_path}")

    def _validate_data(self) -> None:
        """Validate the raw data and create the workflow model"""
        try:
            self._workflow = Workflow(**self._raw_data)
        except ValidationError as e:
            raise WorkflowLoaderError(f"Workflow validation failed: {str(e)}")

    @property
    def workflow(self) -> Optional[Workflow]:
        """Get the loaded workflow (None if not loaded)"""
        return self._workflow

    @classmethod
    def load_workflow(cls, yaml_path: Path) -> Workflow:
        """
        Convenience method to load a workflow from a YAML file
        
        Args:
            yaml_path: Path to the workflow YAML file
            
        Returns:
            Workflow: Validated workflow model
            
        Raises:
            WorkflowLoaderError: If there are any issues loading the workflow
        """
        loader = cls(yaml_path)
        return loader.load()


if __name__ == "__main__":
    # Load workflow using the class method
    workflow = WorkflowLoader.load_workflow(Path("workflows/basic_chat.yaml"))
    print("Workflow loaded successfully!")
    
    # Or using the instance method
    loader = WorkflowLoader(Path("workflows/basic_chat.yaml"))
    workflow = loader.load()
    print("Workflow loaded successfully!")
    
