# tests/core/test_referencing_integration.py
from pathlib import Path
import tempfile

import yaml

from elf0.core.compiler import compile_to_langgraph
from elf0.core.spec import Spec


class TestReferencingIntegration:
    """Integration tests for end-to-end workflow compilation with references."""

    def test_compile_referenced_workflow(self):
        """Test that a workflow with references can be compiled successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create base reasoning workflow (similar to basic_reasoning.yaml)
            base_reasoning = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "reasoning_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7,
                        "params": {
                            "max_tokens": 1000,
                            "system_prompt": """You are a highly trained Language Model to help users.
Your role as an assistant involves thoroughly exploring questions
through a systematic thinking process before providing the final
precise and accurate solutions."""
                        }
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "reasoning_step", "kind": "agent", "ref": "reasoning_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Create routing workflow that references the reasoning workflow
            routing_workflow = {
                "reference": "./reasoning_base.yaml",
                "description": "A workflow that routes to reasoning",
                "llms": {
                    "classifier_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.2
                    },
                    "reasoning_llm": {
                        "temperature": 0.5  # Override temperature from base
                    }
                },
                "workflow": {
                    "type": "custom_graph",
                    "nodes": [
                        {
                            "id": "classifier",
                            "kind": "agent",
                            "ref": "classifier_llm",
                            "stop": False
                        },
                        {
                            "id": "reasoning_handler",
                            "kind": "agent",
                            "ref": "reasoning_llm",
                            "stop": True
                        }
                    ],
                    "edges": [
                        {
                            "source": "classifier",
                            "target": "reasoning_handler",
                            "condition": "state.get('output') == 'reasoning'"
                        }
                    ]
                }
            }

            # Write files
            with open(tmpdir / "reasoning_base.yaml", "w") as f:
                yaml.dump(base_reasoning, f)
            with open(tmpdir / "routing.yaml", "w") as f:
                yaml.dump(routing_workflow, f)

            # Load and compile the workflow
            spec = Spec.from_file(str(tmpdir / "routing.yaml"))

            # Verify the spec was merged correctly
            assert spec.description == "A workflow that routes to reasoning"
            assert "classifier_llm" in spec.llms
            assert "reasoning_llm" in spec.llms
            assert spec.llms["reasoning_llm"].temperature == 0.5  # Overridden
            assert spec.llms["classifier_llm"].temperature == 0.2  # New

            # Verify workflow structure
            assert spec.workflow.type == "custom_graph"  # Overridden
            assert len(spec.workflow.nodes) == 2
            assert len(spec.workflow.edges) == 1

            # Compile to StateGraph
            graph = compile_to_langgraph(spec)

            # Verify graph was created successfully
            assert graph is not None
            # The graph should have our nodes
            # Note: We can't easily inspect LangGraph internals, but if compilation
            # succeeds without error, it means the spec was valid

    def test_prompt_routing_with_reasoning_reference(self):
        """Test a realistic scenario: prompt routing that references basic reasoning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a basic reasoning workflow (similar to our actual basic_reasoning.yaml)
            basic_reasoning = {
                "version": "0.1",
                "runtime": "langgraph",
                "llms": {
                    "reasoning_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7,
                        "params": {
                            "max_tokens": 1000,
                            "system_prompt": """You are a highly trained Language Model to help users.
Your role as an assistant involves thoroughly exploring questions
through a systematic thinking process before providing the final
precise and accurate solutions. Please structure your response into
two main sections: Thought and Solution."""
                        }
                    }
                },
                "workflow": {
                    "type": "sequential",
                    "nodes": [
                        {"id": "reasoning_step", "kind": "agent", "ref": "reasoning_llm", "stop": True}
                    ],
                    "edges": []
                }
            }

            # Create a prompt routing workflow that uses the reasoning as a fallback
            prompt_routing = {
                "reference": "./basic_reasoning.yaml",
                "description": "Routes prompts to different handlers, using reasoning as fallback",
                "llms": {
                    "classifier_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.2
                    },
                    "chat_llm": {
                        "type": "openai",
                        "model_name": "gpt-4o-mini",
                        "temperature": 0.7
                    }
                },
                "workflow": {
                    "type": "custom_graph",
                    "nodes": [
                        {
                            "id": "prompt_classifier",
                            "kind": "agent",
                            "ref": "classifier_llm",
                            "stop": False
                        },
                        {
                            "id": "general_chat_handler",
                            "kind": "agent",
                            "ref": "chat_llm",
                            "stop": True
                        },
                        {
                            "id": "deep_reasoning_handler",
                            "kind": "agent",
                            "ref": "reasoning_llm",  # Using reasoning LLM from referenced file
                            "stop": True
                        }
                    ],
                    "edges": [
                        {
                            "source": "prompt_classifier",
                            "target": "general_chat_handler",
                            "condition": "state.get('output') == 'general_chat'"
                        },
                        {
                            "source": "prompt_classifier",
                            "target": "deep_reasoning_handler",
                            "condition": "state.get('output') == 'deep_reasoning'"
                        }
                    ]
                }
            }

            # Write files
            with open(tmpdir / "basic_reasoning.yaml", "w") as f:
                yaml.dump(basic_reasoning, f)
            with open(tmpdir / "prompt_routing.yaml", "w") as f:
                yaml.dump(prompt_routing, f)

            # Load and compile
            spec = Spec.from_file(str(tmpdir / "prompt_routing.yaml"))

            # Verify the merge worked as expected
            assert len(spec.llms) == 3  # reasoning_llm, classifier_llm, chat_llm
            assert "reasoning_llm" in spec.llms
            assert "classifier_llm" in spec.llms
            assert "chat_llm" in spec.llms

            # Verify workflow structure
            assert len(spec.workflow.nodes) == 3
            node_ids = {node.id for node in spec.workflow.nodes}
            assert node_ids == {"prompt_classifier", "general_chat_handler", "deep_reasoning_handler"}

            # Verify that the deep_reasoning_handler references the reasoning_llm from the base
            reasoning_handler = next(node for node in spec.workflow.nodes if node.id == "deep_reasoning_handler")
            assert reasoning_handler.ref == "reasoning_llm"

            # Compile to ensure it's valid
            graph = compile_to_langgraph(spec)
            assert graph is not None

    def test_backwards_compatibility(self):
        """Test that existing workflows without references still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a traditional workflow without references
            traditional_spec = {
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
            with open(tmpdir / "traditional.yaml", "w") as f:
                yaml.dump(traditional_spec, f)

            # Load and compile
            spec = Spec.from_file(str(tmpdir / "traditional.yaml"))
            graph = compile_to_langgraph(spec)

            # Should work exactly as before
            assert spec.llms["chat_llm"].model_name == "gpt-4o-mini"
            assert spec.workflow.nodes[0].id == "chat"
            assert graph is not None
