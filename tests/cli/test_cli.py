import pytest
from pathlib import Path
from typing import List
from elf.cli import (
    parse_context_files,
    prepare_workflow_input,
    format_workflow_result,
    validate_output_path,
    save_workflow_result,
    display_workflow_result,
    read_prompt_file,
    agent_command,
    app
)
from typer import Exit
import json
import os
from unittest.mock import patch
from typer.testing import CliRunner

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
    display_workflow_result("test output")
    captured = capsys.readouterr()
    assert "test output" in captured.out

def test_display_workflow_result_dict_with_output(capsys):
    """Test displaying dict result with output key."""
    display_workflow_result({"output": "test output"})
    captured = capsys.readouterr()
    assert "test output" in captured.out

def test_display_workflow_result_dict_without_output(capsys):
    """Test displaying dict result without output key."""
    display_workflow_result({"key": "value"})
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "{'key': 'value'}" in captured.out

def test_display_workflow_result_unexpected_type(capsys):
    """Test displaying result of unexpected type."""
    display_workflow_result(123)
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "123" in captured.out

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
    spec_path.write_text("name: test\nruntime: langgraph\nworkflow:\n  nodes: []")
    
    # Mock run_workflow to avoid actual execution
    with patch('elf.cli.run_workflow') as mock_run:
        mock_run.return_value = {"output": "test result"}
        result = runner.invoke(app, ["agent", str(spec_path), "--prompt_file", str(temp_prompt_file)])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        assert "Test prompt content" in mock_run.call_args[0][1]

def test_agent_command_prompt_file_and_prompt(runner, temp_prompt_file, tmp_path):
    """Test running workflow with both prompt file and prompt."""
    spec_path = tmp_path / "workflow.yaml"
    spec_path.write_text("name: test\nruntime: langgraph\nworkflow:\n  nodes: []")
    
    # Mock run_workflow to avoid actual execution
    with patch('elf.cli.run_workflow') as mock_run:
        mock_run.return_value = {"output": "test result"}
        result = runner.invoke(app, [
            "agent",
            str(spec_path),
            "--prompt_file", str(temp_prompt_file),
            "--prompt", "Additional prompt"
        ])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        assert "Test prompt content" in mock_run.call_args[0][1]
        assert "Additional prompt" in mock_run.call_args[0][1]

def test_agent_command_no_prompt_sources(runner, tmp_path):
    """Test running workflow with no prompt sources."""
    spec_path = tmp_path / "workflow.yaml"
    spec_path.write_text("name: test\nruntime: langgraph\nworkflow:\n  nodes: []")
    
    result = runner.invoke(app, ["agent", str(spec_path)])
    assert result.exit_code == 1
    assert "Error: You must provide either --prompt or --prompt_file" in result.stdout

def test_agent_command_empty_prompt_file(runner, tmp_path):
    """Test running workflow with empty prompt file."""
    file_path = tmp_path / "empty.md"
    file_path.write_text("")
    spec_path = tmp_path / "workflow.yaml"
    spec_path.write_text("name: test\nruntime: langgraph\nworkflow:\n  nodes: []")
    
    # Mock run_workflow to avoid actual execution
    with patch('elf.cli.run_workflow') as mock_run:
        mock_run.return_value = {"output": "test result"}
        result = runner.invoke(app, ["agent", str(spec_path), "--prompt_file", str(file_path)])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][1] == "" 