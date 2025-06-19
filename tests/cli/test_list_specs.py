from pathlib import Path

from typer.testing import CliRunner

# Assuming your Typer app is instantiated in elf.cli as 'app'
# If your project structure is different, you might need to adjust this import path
# e.g., from src.elf.cli import app
from elf0.cli import app

runner = CliRunner()

def create_spec_file(dir_path: Path, filename: str, content: str):
    """Helper function to create a spec file in the given directory."""
    (dir_path / filename).write_text(content)

def test_list_specs_no_specs_directory(tmp_path, monkeypatch):
    """Test behavior when the './specs' directory does not exist."""
    monkeypatch.chdir(tmp_path)  # Change current working directory to tmp_path

    result = runner.invoke(app, ["list-specs"])

    assert result.exit_code == 0
    # Check for the key phrase, ignoring the exact path format
    assert "Specs directory 'specs' not found" in result.stdout

def test_list_specs_empty_directory(tmp_path, monkeypatch):
    """Test behavior when the './specs' directory is empty."""
    monkeypatch.chdir(tmp_path)
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()

    result = runner.invoke(app, ["list-specs"])

    assert result.exit_code == 0
    # Check for the key phrase, ignoring the exact path format
    assert "No spec files (.yaml or .yml) found in 'specs'" in result.stdout

def test_list_specs_with_various_files(tmp_path, monkeypatch):
    """Test listing of various spec files, ignoring non-YAML and sub-directory files."""
    monkeypatch.chdir(tmp_path)
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()

    # Spec 1: with description field
    create_spec_file(specs_dir, "spec_a.yaml", "description: This is spec_a description.\nkey: value")
    # Spec 2: with comment description (note: will be sorted after spec_a)
    create_spec_file(specs_dir, "spec_b.yml", "# This is spec_b comment description\nother_key: other_value")
    # Spec 3: no description
    create_spec_file(specs_dir, "spec_c.yaml", "no_desc_key: data")
    # Non-YAML file (should be ignored)
    create_spec_file(specs_dir, "other.txt", "some text data")
    # YAML in subdirectory (should be ignored)
    sub_dir = specs_dir / "subdir"
    sub_dir.mkdir()
    create_spec_file(sub_dir, "subspec.yaml", "description: I am in a subdir.")

    result = runner.invoke(app, ["list-specs"])
    assert result.exit_code == 0
    stdout = result.stdout

    # Check for spec_a (plain text filename and description)
    assert "spec_a.yaml" in stdout
    assert "  This is spec_a description." in stdout

    # Check for spec_b (plain text filename and description)
    assert "spec_b.yml" in stdout
    assert "  This is spec_b comment description" in stdout # '#' removed from comment

    # Check for spec_c (plain text filename and description)
    assert "spec_c.yaml" in stdout
    assert "  No description available." in stdout

    # Check that non-YAML and sub-dir files are NOT listed
    assert "other.txt" not in stdout
    assert "subspec.yaml" not in stdout
    assert "I am in a subdir." not in stdout

    # Check relative order (alphabetical: spec_a, spec_b, spec_c)
    idx_spec_a_name = stdout.find("spec_a.yaml")
    idx_spec_b_name = stdout.find("spec_b.yml")
    idx_spec_c_name = stdout.find("spec_c.yaml")

    assert -1 < idx_spec_a_name < idx_spec_b_name < idx_spec_c_name

    # Check indentation of descriptions
    assert stdout.count("\n  ") >= 3 # Each description should be indented

def test_list_specs_with_invalid_yaml_content(tmp_path, monkeypatch):
    """Test handling of spec files with invalid YAML content."""
    monkeypatch.chdir(tmp_path)
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()

    create_spec_file(specs_dir, "good_spec.yaml", "description: This is a perfectly good spec.")
    # Invalid YAML file (malformed)
    create_spec_file(specs_dir, "invalid_content.yaml", "description: hello\n  bad_indent: - item1\n - item2") # Malformed YAML

    result = runner.invoke(app, ["list-specs"])

    assert result.exit_code == 0
    stdout = result.stdout

    # Check for the good spec (plain text filename and description)
    assert "good_spec.yaml" in stdout
    assert "  This is a perfectly good spec." in stdout

    # Check for the invalid spec (plain text filename and description)
    assert "invalid_content.yaml" in stdout
    assert "  No description available." in stdout

def test_list_specs_description_not_string(tmp_path, monkeypatch):
    """Test handling of spec files where 'description' field is not a string."""
    monkeypatch.chdir(tmp_path)
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()

    create_spec_file(specs_dir, "non_string_desc.yaml", "description: [1, 2, 3]\nkey: value")

    result = runner.invoke(app, ["list-specs"])
    assert result.exit_code == 0
    stdout = result.stdout

    # Check for the spec (plain text filename and description)
    assert "non_string_desc.yaml" in stdout
    assert "  No description available." in stdout
