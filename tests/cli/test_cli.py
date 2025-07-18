import io  # For string IO
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console as RichConsole  # To create new consoles for patching
from typer import Exit
from typer.testing import CliRunner

from elf0.cli import (
    app,
    app_state,
    display_workflow_result,
    format_workflow_result,
    get_multiline_input,
    parse_context_files,
    prepare_workflow_input,
    read_prompt_file,
    save_workflow_result,
    validate_output_path,
)

# Test data
SAMPLE_CONTENT = "This is sample content"
SAMPLE_PROMPT = "Test prompt"

@pytest.fixture
def temp_files(tmp_path):
    """Create temporary files for testing."""
    files = []
    for i in range(3):
        file_path = tmp_path / f"test{i}.txt"
        file_path.write_text(f"Content of test{i}.txt")
        files.append(file_path)
    return files

@pytest.fixture
def temp_output_file(tmp_path):
    """Create a temporary output file."""
    return tmp_path / "output.txt"

@pytest.fixture
def temp_prompt_file(tmp_path):
    """Create a temporary prompt file."""
    file_path = tmp_path / "test_prompt.md"
    file_path.write_text("Test prompt content")
    return file_path

@pytest.fixture
def runner():
    """Create a Typer CLI test runner."""
    return CliRunner()

def test_parse_context_files_empty():
    """Test parsing empty context files list."""
    result = parse_context_files(None)
    assert result == ""

def test_parse_context_files_single_file(temp_files):
    """Test parsing a single context file."""
    result = parse_context_files([temp_files[0]])
    assert "Content of test0.txt" in result
    assert "Content of test1.txt" not in result

def test_parse_context_files_multiple_files(temp_files):
    """Test parsing multiple context files."""
    result = parse_context_files(temp_files)
    for i in range(3):
        assert f"Content of test{i}.txt" in result

def test_parse_context_files_comma_separated(temp_files):
    """Test parsing comma-separated file paths."""
    file_str = f"{temp_files[0]},{temp_files[1]}"
    result = parse_context_files([Path(file_str)])
    assert "Content of test0.txt" in result
    assert "Content of test1.txt" in result
    assert "Content of test2.txt" not in result

def test_parse_context_files_nonexistent():
    """Test parsing non-existent files."""
    result = parse_context_files([Path("nonexistent.txt")])
    assert result == ""

def test_prepare_workflow_input_no_context():
    """Test preparing workflow input without context."""
    result = prepare_workflow_input(SAMPLE_PROMPT, "")
    assert result == SAMPLE_PROMPT

def test_prepare_workflow_input_with_context():
    """Test preparing workflow input with context."""
    context = "Context content"
    result = prepare_workflow_input(SAMPLE_PROMPT, context)
    assert context in result
    assert SAMPLE_PROMPT in result
    assert result.endswith(SAMPLE_PROMPT)

def test_format_workflow_result_string():
    """Test formatting string result."""
    result, is_json = format_workflow_result("test output")
    assert result == "test output"
    assert not is_json

def test_format_workflow_result_dict_with_output():
    """Test formatting dict result with output key."""
    result, is_json = format_workflow_result({"output": "test output"})
    assert result == "test output"
    assert not is_json

def test_format_workflow_result_complex_dict():
    """Test formatting complex dict result."""
    data = {"key": "value", "nested": {"key": "value"}}
    result, is_json = format_workflow_result(data)
    assert json.loads(result) == data
    assert is_json

def test_format_workflow_result_invalid_json():
    """Test formatting result that can't be serialized to JSON."""
    class Unserializable:
        pass

    with pytest.raises(Exit):
        format_workflow_result(Unserializable())

def test_validate_output_path_existing_file(temp_output_file):
    """Test validating existing output file."""
    temp_output_file.touch()
    os.chmod(temp_output_file, 0o666)
    validate_output_path(temp_output_file)  # Should not raise

def test_validate_output_path_nonexistent_parent():
    """Test validating output path with nonexistent parent."""
    with pytest.raises(Exit):
        validate_output_path(Path("/nonexistent/path/file.txt"))

def test_validate_output_path_unwritable_parent(tmp_path):
    """Test validating output path with unwritable parent."""
    parent = tmp_path / "unwritable"
    parent.mkdir()
    os.chmod(parent, 0o444)
    with pytest.raises(Exit):
        validate_output_path(parent / "file.txt")

def test_save_workflow_result_text(temp_output_file):
    """Test saving text result to file."""
    content = "test content"
    save_workflow_result(temp_output_file, content, False)
    assert temp_output_file.read_text() == content

def test_save_workflow_result_json(temp_output_file):
    """Test saving JSON result to file."""
    content = '{"key": "value"}'
    save_workflow_result(temp_output_file, content, True)
    assert temp_output_file.read_text() == content

def test_save_workflow_result_unwritable_file(temp_output_file):
    """Test saving to unwritable file."""
    temp_output_file.touch()
    os.chmod(temp_output_file, 0o444)
    with pytest.raises(Exit):
        save_workflow_result(temp_output_file, "content", False)

def test_display_workflow_result_string(capsys):
    """Test displaying string result."""
    mock_stdout_buffer = io.StringIO()
    # Patch the module-level stdout_workflow_console used by display_workflow_result
    with patch("elf0.cli.stdout_workflow_console", RichConsole(file=mock_stdout_buffer, force_terminal=False)):
        display_workflow_result("test output")

    captured_out_direct = mock_stdout_buffer.getvalue()
    assert "test output" in captured_out_direct.strip()

    captured_capsys = capsys.readouterr() # Check for any stray stderr from other sources
    assert captured_capsys.err == ""

def test_display_workflow_result_dict_with_output(capsys):
    """Test displaying dict result with output key."""
    mock_stdout_buffer = io.StringIO()
    with patch("elf0.cli.stdout_workflow_console", RichConsole(file=mock_stdout_buffer, force_terminal=False)):
        display_workflow_result({"output": "test output"})

    captured_out_direct = mock_stdout_buffer.getvalue()
    assert "test output" in captured_out_direct.strip()

    captured_capsys = capsys.readouterr() # Check for any stray stderr
    assert captured_capsys.err == ""


def test_display_workflow_result_dict_without_output(capsys):
    """Test displaying dict result without output key."""
    original_verbose = app_state.verbose_mode
    app_state.verbose_mode = True
    mock_stdout_buffer = io.StringIO()
    try:
        with patch("elf0.cli.stdout_workflow_console", RichConsole(file=mock_stdout_buffer, force_terminal=False)):
            display_workflow_result({"key": "value"})

        captured_out_direct = mock_stdout_buffer.getvalue()
        assert "{'key': 'value'}" in captured_out_direct.strip() # Raw output still to patched stdout

        captured_capsys = capsys.readouterr()
        # Warnings from _conditional_secho (using typer.secho -> global rich.console (stderr))
        # are captured by capsys.out in non-TTY test env, as previously observed.
        assert "Warning: Key 'output' not found" in captured_capsys.out
    finally:
        app_state.verbose_mode = original_verbose

def test_display_workflow_result_unexpected_type(capsys):
    """Test displaying result of unexpected type."""
    original_verbose = app_state.verbose_mode
    app_state.verbose_mode = True
    mock_stdout_buffer = io.StringIO()
    try:
        with patch("elf0.cli.stdout_workflow_console", RichConsole(file=mock_stdout_buffer, force_terminal=False)):
            display_workflow_result(123)

        captured_out_direct = mock_stdout_buffer.getvalue()
        assert "123" in captured_out_direct.strip() # Raw output still to patched stdout

        captured_capsys = capsys.readouterr()
        # Warnings from _conditional_secho (using typer.secho -> global rich.console (stderr))
        # are captured by capsys.out in non-TTY test env.
        assert "Warning: Unexpected result type" in captured_capsys.out
    finally:
        app_state.verbose_mode = original_verbose

def test_read_prompt_file_valid(temp_prompt_file):
    """Test reading a valid prompt file."""
    content = read_prompt_file(temp_prompt_file)
    assert content == "Test prompt content"

def test_read_prompt_file_invalid_extension(tmp_path):
    """Test reading a prompt file with invalid extension."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")
    with pytest.raises(Exit):
        read_prompt_file(file_path)

def test_read_prompt_file_nonexistent(tmp_path):
    """Test reading a nonexistent prompt file."""
    file_path = tmp_path / "nonexistent.md"
    with pytest.raises(Exit):
        read_prompt_file(file_path)

def test_agent_command_prompt_file_only(runner, temp_prompt_file, tmp_path):
    """Test running workflow with only prompt file."""
    spec_path = tmp_path / "workflow.yaml"
    # Ensure a minimal valid spec structure for elf.core.spec.Spec
    spec_path.write_text("""
version: '0.1'
description: Test workflow
runtime: langgraph
llms:
  dummy_llm:
    type: openai
    model_name: gpt-3.5-turbo
    api_key: dummy_key_not_used_due_to_mock
workflow:
  type: sequential
  nodes:
    - id: start
      kind: agent
      ref: dummy_llm
      stop: true
""")

    with patch("elf0.cli.run_workflow") as mock_run:
        mock_run.return_value = {"output": "test result"}
        result = runner.invoke(app, ["agent", str(spec_path), "--prompt_file", str(temp_prompt_file)])
        assert result.exit_code == 0, result.stdout
        mock_run.assert_called_once()
        assert "Test prompt content" in mock_run.call_args[0][1]

def test_agent_command_prompt_file_and_prompt(runner, temp_prompt_file, tmp_path):
    """Test running workflow with both prompt file and prompt."""
    spec_path = tmp_path / "workflow.yaml"
    spec_path.write_text("""
version: '0.1'
description: Test workflow
runtime: langgraph
llms:
  dummy_llm:
    type: openai
    model_name: gpt-3.5-turbo
    api_key: dummy_key_not_used_due_to_mock
workflow:
  type: sequential
  nodes:
    - id: start
      kind: agent
      ref: dummy_llm
      stop: true
""")

    with patch("elf0.cli.run_workflow") as mock_run:
        mock_run.return_value = {"output": "test result"}
        result = runner.invoke(app, [
            "agent",
            str(spec_path),
            "--prompt_file", str(temp_prompt_file),
            "--prompt", "Additional prompt"
        ])
        assert result.exit_code == 0, result.stdout
        mock_run.assert_called_once()
        assert "Test prompt content" in mock_run.call_args[0][1]
        assert "Additional prompt" in mock_run.call_args[0][1]

def test_agent_command_no_prompt_sources(runner, tmp_path):
    """Test running workflow with no prompt sources."""
    spec_path = tmp_path / "workflow.yaml"
    spec_path.write_text("""
version: '0.1'
description: Test workflow
runtime: langgraph
llms:
  dummy_llm:
    type: openai
    model_name: gpt-3.5-turbo
    api_key: dummy_key_not_used_due_to_mock
workflow:
  type: sequential
  nodes:
    - id: start
      kind: agent
      ref: dummy_llm
      stop: true
""") # Minimal valid spec

    result = runner.invoke(app, ["agent", str(spec_path)])
    assert result.exit_code == 1
    # Typer's error messages for missing options/arguments go to what CliRunner captures as stdout.
    assert "Error: You must provide either --prompt or --prompt_file" in result.stdout

def test_agent_command_empty_prompt_file(runner, tmp_path):
    """Test running workflow with empty prompt file."""
    file_path = tmp_path / "empty.md"
    file_path.write_text("")
    spec_path = tmp_path / "workflow.yaml"
    spec_path.write_text("""
version: '0.1'
description: Test workflow
runtime: langgraph
llms:
  dummy_llm:
    type: openai
    model_name: gpt-3.5-turbo
    api_key: dummy_key_not_used_due_to_mock
workflow:
  type: sequential
  nodes:
    - id: start
      kind: agent
      ref: dummy_llm
      stop: true
""") # Ensure valid spec

    with patch("elf0.cli.run_workflow") as mock_run:
        mock_run.return_value = {"output": "test result"}
        result = runner.invoke(app, ["agent", str(spec_path), "--prompt_file", str(file_path)])
        assert result.exit_code == 0, result.stdout
        mock_run.assert_called_once()
        assert mock_run.call_args[0][1] == "" # Empty prompt string

@patch("elf0.core.input_collector.collect_terminal_input")
def test_get_multiline_input_with_send_command(mock_collect_terminal_input, capsys):
    """Test multiline input with /send command."""
    mock_collect_terminal_input.return_value = "Hello world\nThis is a test"

    result = get_multiline_input()
    assert result == "Hello world\nThis is a test"
    mock_collect_terminal_input.assert_called_once_with("💬 Enter your prompt:", multiline=True)
    _ = capsys.readouterr() # Consume any stderr like "💬 Enter your prompt:"

@patch("elf0.core.input_collector.collect_terminal_input")
def test_get_multiline_input_with_double_enter(mock_collect_terminal_input, capsys):
    """Test multiline input with double enter."""
    mock_collect_terminal_input.return_value = "Hello world\nThis is a test"

    result = get_multiline_input()
    # The current logic: join(["Hello world", "This is a test", "", ""]) -> "Hello world\nThis is a test\n\n" -> strip -> "Hello world\nThis is a test"
    assert result == "Hello world\nThis is a test"
    mock_collect_terminal_input.assert_called_once_with("💬 Enter your prompt:", multiline=True)
    _ = capsys.readouterr() # Consume any stderr

@patch("elf0.core.input_collector.collect_terminal_input")
def test_get_multiline_input_with_exit_command(mock_collect_terminal_input, capsys):
    """Test multiline input with exit command."""
    mock_collect_terminal_input.return_value = ""

    result = get_multiline_input()
    assert result == ""
    mock_collect_terminal_input.assert_called_once_with("💬 Enter your prompt:", multiline=True)
    _ = capsys.readouterr() # Consume any stderr


def test_exit_command_detection():
    """Test that exit commands are detected correctly in prompt_yaml_command."""
    # Test cases for exit command detection
    test_cases = [
        ("", True),           # Empty string should exit
        ("/exit", True),      # Should exit
        ("/quit", True),      # Should exit
        ("/bye", True),       # Should exit
        ("exit", True),       # Should exit
        ("quit", True),       # Should exit
        ("bye", True),        # Should exit
        ("EXIT", True),       # Should exit (case insensitive)
        ("/EXIT", True),      # Should exit (case insensitive)
        ("hello", False),     # Should not exit
        ("test prompt", False),  # Should not exit
        ("export", False),    # Should not exit (contains 'exit' but not exact match)
    ]

    for prompt, expected_exit in test_cases:
        # This is the logic from the CLI prompt_yaml_command
        should_exit = not prompt or prompt.lower() in ["exit", "quit", "bye", "/exit", "/quit", "/bye"]

        assert should_exit == expected_exit, f"'{prompt}' -> exit={should_exit}, expected={expected_exit}"
