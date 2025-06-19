# tests/core/test_spec_referencing.py
from pathlib import Path
import tempfile

import pytest

from elf.core.spec import (
    CircularReferenceError,
    Spec,
    _deep_merge_dicts,
)


class TestSpecReferencing:
    """Test cases for YAML workflow referencing functionality."""

    def test_deep_merge_dicts_basic(self):
        """Test basic dictionary merging."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 4}, "e": 5}
        result = _deep_merge_dicts(base, override)

        expected = {"a": 1, "b": {"c": 4, "d": 3}, "e": 5}
        assert result == expected

    def test_deep_merge_dicts_list_override(self):
        """Test that lists are replaced entirely (override semantics)."""
        base = {"items": [1, 2, 3], "other": "value"}
        override = {"items": [4, 5]}
        result = _deep_merge_dicts(base, override)

        expected = {"items": [4, 5], "other": "value"}
        assert result == expected

    def test_deep_merge_dicts_type_mismatch(self):
        """Test that merging incompatible types raises an error."""
        base = {"key": "string"}
        override = {"key": {"nested": "dict"}}

        with pytest.raises(ValueError, match="Cannot merge incompatible types"):
            _deep_merge_dicts(base, override)

    def test_simple_reference_loading(self):
        """Test loading a spec that references another spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create base spec
            base_spec = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "chat_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "chat", "kind": "agent", "ref": "chat_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Create referencing spec
            referencing_spec = {
                "reference": "./base.yaml",
                "description": "Custom chat with reference"
            }

            # Write files
            import yaml
            with open(tmpdir / "base.yaml", "w") as f:
                yaml.dump(base_spec, f)
            with open(tmpdir / "referencing.yaml", "w") as f:
                yaml.dump(referencing_spec, f)

            # Load the referencing spec
            spec = Spec.from_file(str(tmpdir / "referencing.yaml"))

            # Verify the merge worked
            assert spec.description == "Custom chat with reference"
            assert spec.llms["chat_llm"].model_name == "gpt-4o-mini"
            assert spec.workflow.nodes[0].id == "chat"

    def test_reference_with_override(self):
        """Test that referencing spec can override values from base spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create base spec
            base_spec = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "chat_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "chat", "kind": "agent", "ref": "chat_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Create referencing spec with overrides
            referencing_spec = {
                "reference": "./base.yaml",
                "llms": {
                    "chat_llm": {
                        "temperature": 0.2  # Override temperature
                    }
                }
            }

            # Write files
            import yaml
            with open(tmpdir / "base.yaml", "w") as f:
                yaml.dump(base_spec, f)
            with open(tmpdir / "referencing.yaml", "w") as f:
                yaml.dump(referencing_spec, f)

            # Load the referencing spec
            spec = Spec.from_file(str(tmpdir / "referencing.yaml"))

            # Verify the override worked
            assert spec.llms["chat_llm"].temperature == 0.2
            assert spec.llms["chat_llm"].model_name == "gpt-4o-mini"  # Should remain from base

    def test_nested_references(self):
        """Test chain of references (A -> B -> C)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create base spec (C)
            base_spec = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "chat_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "chat", "kind": "agent", "ref": "chat_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Create middle spec (B)
            middle_spec = {
                "reference": "./base.yaml",
                "llms": {
                    "chat_llm": {
                        "temperature": 0.5
                    }
                }
            }

            # Create top spec (A)
            top_spec = {
                "reference": "./middle.yaml",
                "description": "Top level spec"
            }

            # Write files
            import yaml
            with open(tmpdir / "base.yaml", "w") as f:
                yaml.dump(base_spec, f)
            with open(tmpdir / "middle.yaml", "w") as f:
                yaml.dump(middle_spec, f)
            with open(tmpdir / "top.yaml", "w") as f:
                yaml.dump(top_spec, f)

            # Load the top spec
            spec = Spec.from_file(str(tmpdir / "top.yaml"))

            # Verify the chain worked
            assert spec.description == "Top level spec"
            assert spec.llms["chat_llm"].temperature == 0.5  # From middle
            assert spec.llms["chat_llm"].model_name == "gpt-4o-mini"  # From base

    def test_circular_reference_detection(self):
        """Test that circular references are detected and raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create specs with circular reference (A -> B -> A)
            spec_a = {
                "reference": "./spec_b.yaml",
                "description": "Spec A"
            }

            spec_b = {
                "reference": "./spec_a.yaml",
                "description": "Spec B"
            }

            # Write files
            import yaml
            with open(tmpdir / "spec_a.yaml", "w") as f:
                yaml.dump(spec_a, f)
            with open(tmpdir / "spec_b.yaml", "w") as f:
                yaml.dump(spec_b, f)

            # Loading should raise CircularReferenceError
            with pytest.raises(CircularReferenceError, match="Circular reference detected"):
                Spec.from_file(str(tmpdir / "spec_a.yaml"))

    def test_missing_reference_file(self):
        """Test that missing referenced files raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create spec that references non-existent file
            referencing_spec = {
                "reference": "./nonexistent.yaml",
                "description": "Referencing missing file"
            }

            # Write file
            import yaml
            with open(tmpdir / "referencing.yaml", "w") as f:
                yaml.dump(referencing_spec, f)

            # Loading should raise FileNotFoundError
            with pytest.raises(FileNotFoundError, match="Referenced file not found"):
                Spec.from_file(str(tmpdir / "referencing.yaml"))

    def test_absolute_path_reference(self):
        """Test that absolute path references work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create base spec
            base_spec = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "chat_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "chat", "kind": "agent", "ref": "chat_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Create referencing spec with absolute path
            base_path = str(tmpdir / "base.yaml")
            referencing_spec = {
                "reference": base_path,  # Absolute path
                "description": "Absolute reference"
            }

            # Write files
            import yaml
            with open(tmpdir / "base.yaml", "w") as f:
                yaml.dump(base_spec, f)
            with open(tmpdir / "referencing.yaml", "w") as f:
                yaml.dump(referencing_spec, f)

            # Load the referencing spec
            spec = Spec.from_file(str(tmpdir / "referencing.yaml"))

            # Verify it worked
            assert spec.description == "Absolute reference"
            assert spec.llms["chat_llm"].model_name == "gpt-4o-mini"

    def test_no_reference_loads_normally(self):
        """Test that specs without reference field load normally."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create normal spec without reference
            normal_spec = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "chat_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "chat", "kind": "agent", "ref": "chat_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Write file
            import yaml
            with open(tmpdir / "normal.yaml", "w") as f:
                yaml.dump(normal_spec, f)

            # Load the spec
            spec = Spec.from_file(str(tmpdir / "normal.yaml"))

            # Verify it loaded correctly
            assert spec.llms["chat_llm"].model_name == "gpt-4o-mini"
            assert spec.workflow.nodes[0].id == "chat"
