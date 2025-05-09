# Project Tasks

## Phase 1: MVP Functionality

### CLI Functionality
- [x] Add a `awa` command to the CLI, and it defaults to `help`
- [x] Add a `awa --help` command to the CLI
- [x] Add a `awa ./workflows/<workflow_name>.yaml` command to the CLI

### Workflow Functionality
- [x] Define a workflow schema in JSON-Schema, in `docs_specs/workflow_schema.md`
- [x] Create a simple example workflow in YAML, in `workflows/basic_chat.yaml`. It has one step and one agent and just returns the result from an input prompt.
- [x] Create a pydantic model for the workflow schema in `core/workflow_model.py`
- [x] Create a `core/workflow_loader.py` that loads a workflow from a YAML file into the model
- [ ] Create a `core/workflow_executor.py` that executes a workflow, it loads the workflow file and then has an `execute` function that takes a `workflow` and `input` parameters





