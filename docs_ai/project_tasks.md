# Project Tasks

## Phase 1: MVP Functionality

### CLI Functionality
- [x] Add a `awa` command to the CLI, and it defaults to `help`
- [x] Add a `awa --help` command to the CLI
- [x] Add a `awa ./specs/<spec_name>.yaml` command to the CLI

### Spec Functionality
- [x] Define a spec schema in JSON-Schema, in `docs_specs/spec_schema.md`
- [x] Create a simple example spec in YAML, in `specs/basic_chat.yaml`. It has one step and one agent and just returns the result from an input prompt.
- [x] Create `spec`, `compiler` and `runner` as well as the `yaml_loader`.
- [ ] Implmement basic LLM call using LangGraph
  - [ ] Create an `llm_client` file that implements the OpenAI API and returns a client that the `compiler.py` `make_llm_node` function can use





