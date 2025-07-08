import logging
from pathlib import Path
import re

import yaml  # PyYAML library for YAML parsing

logger = logging.getLogger(__name__)

def is_valid_file(path: Path) -> bool:
    """Check if a path exists and is a file."""
    return path.exists() and path.is_file()

def is_valid_directory(path: Path) -> bool:
    """Check if a path exists and is a directory."""
    return path.exists() and path.is_dir()

def is_relevant_file(path: Path) -> bool:
    """Check if a file should be included in directory scanning."""
    # Skip hidden files
    if path.name.startswith("."):
        return False

    # Define relevant extensions
    relevant_exts = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".rs", ".go", ".rb", ".php", ".sh", ".sql", ".r", ".scala", ".kt",
        ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".env", ".cfg",
        ".md", ".rst", ".txt", ".adoc"
    }

    # Skip known binary extensions
    binary_exts = {
        ".pyc", ".pyo", ".class", ".exe", ".dll", ".so", ".o", ".a",
        ".zip", ".tar", ".gz", ".7z", ".rar", ".pdf", ".jpg", ".jpeg",
        ".png", ".gif", ".svg", ".mp4", ".avi", ".mp3", ".wav"
    }

    suffix = path.suffix.lower()

    if suffix in relevant_exts:
        return True
    if suffix in binary_exts:
        return False

    # Handle extensionless files
    if not suffix and path.is_file():
        try:
            # Simple size check
            if path.stat().st_size > 1024 * 1024:  # 1MB
                return False
            # Basic text detection
            with path.open("rb") as f:
                sample = f.read(min(1024, path.stat().st_size))
                if not sample:
                    return False
                # Check if mostly printable ASCII characters
                ascii_printable_start = 32  # Space character
                ascii_printable_end = 126   # Tilde character
                ascii_tab = 9
                ascii_newline = 10
                ascii_carriage_return = 13
                text_threshold = 0.7

                printable_chars = sum(1 for b in sample
                                    if ascii_printable_start <= b <= ascii_printable_end
                                    or b in (ascii_tab, ascii_newline, ascii_carriage_return))
                return printable_chars / len(sample) > text_threshold
        except (OSError, UnicodeDecodeError):
            return False

    return False

def get_directory_files(directory: Path, max_files: int = 5) -> list[Path]:
    """Get relevant files from a directory (non-recursive)."""
    relevant_files = []

    try:
        for item in directory.iterdir():
            if item.is_file() and is_relevant_file(item):
                relevant_files.append(item)
                if len(relevant_files) >= max_files:
                    logger.warning(f"Directory '@{directory}' contains many files. "
                                 f"Only including first {max_files} relevant files.")
                    break

        return sorted(relevant_files, key=lambda p: p.name.lower())

    except PermissionError:
        logger.warning(f"Permission denied accessing directory '@{directory}'")
        return []
    except OSError as e:
        logger.warning(f"Could not read directory '@{directory}': {e}")
        return []

def read_files_content(files: list[Path]) -> str:
    """Read content from a list of files.

    Args:
        files: List of paths to files to read.

    Returns:
        Combined content from all valid files, with headers indicating filename.
    """
    content_parts = []
    for file_path in files:
        try:
            current_path = Path(file_path) # Ensure it's a Path object
            with current_path.open(encoding="utf-8") as f:
                # Show directory context for files from directories
                if len(str(current_path.parent)) > 1:  # Not just "."
                    header = f"Content of {current_path.parent}/{current_path.name}"
                else:
                    header = f"Content of {current_path.name}"
                content_parts.append(f"{header}:\n{f.read()}\n---")
        except OSError as e:
            logger.warning(f"Could not read context file '{file_path}': {e}. Skipping.")
    return "\n".join(content_parts)

def parse_comma_separated_files(file_str: str) -> list[Path]:
    """Parse a comma-separated string of file paths.

    Args:
        file_str: A string containing comma-separated file paths.

    Returns:
        A list of valid Path objects.
    """
    valid_files = []
    for f_name in file_str.split(","):
        path = Path(f_name.strip())
        if is_valid_file(path):
            valid_files.append(path)
        else:
            logger.warning(f"Context file '{f_name.strip()}' not found or is not a file. Skipping.")
    return valid_files

def parse_context_files(context_files_input: list[Path] | None) -> str:
    """Parse and read content from a list of context file paths.

    Handles paths that might themselves be comma-separated strings of filenames.

    Args:
        context_files_input: List of Path objects. Some Path objects' string
                             representations might be comma-separated filenames.

    Returns:
        Combined content from all valid context files.
    """
    if not context_files_input:
        return ""

    actual_files_to_read: list[Path] = []
    processed_paths_for_deduplication = set() # To avoid processing the same file path string multiple times

    for path_item in context_files_input:
        path_str = str(path_item).strip()

        if not path_str:
            continue

        # Handle cases where a single Path item might represent a comma-separated list
        # This behavior is retained from the original CLI logic.
        if "," in path_str:
            # Avoid reprocessing if this exact comma-separated string was already seen
            if path_str not in processed_paths_for_deduplication:
                files_from_csv = parse_comma_separated_files(path_str)
                for f in files_from_csv:
                    # Add to actual_files_to_read only if not already added (by Path object equality)
                    if f not in actual_files_to_read:
                         actual_files_to_read.append(f)
                processed_paths_for_deduplication.add(path_str)
        else:
            # Single file path
            path_obj = Path(path_str)
            # Add to actual_files_to_read only if not already added
            if path_obj not in actual_files_to_read:
                if is_valid_file(path_obj):
                    actual_files_to_read.append(path_obj)
                else:
                    # This warning is also covered by parse_comma_separated_files if it were called,
                    # but direct calls also need it.
                    logger.warning(f"Context file '{path_obj}' not found or is not a file. Skipping.")

    # The original code did not explicitly deduplicate files passed to _read_files_content,
    # but the collection process here with `actual_files_to_read.append(f)` if f not in ...
    # introduces deduplication based on Path object equality. This is generally good.
    return read_files_content(actual_files_to_read)

def parse_at_references(prompt: str) -> tuple[str, list[Path]]:
    """Parse @file references from a prompt string.

    Args:
        prompt: The input prompt that may contain @filename references.

    Returns:
        A tuple containing:
            - cleaned_prompt: The prompt with @file references removed.
            - referenced_files: A list of valid Path objects for files found.
    """
    # Regex to find @filename.ext patterns.
    # It looks for '@' followed by one or more non-whitespace, non-'@' characters,
    # optionally followed by a dot and more such characters (for the extension).
    at_pattern = r"@([^\s@]+(?:\.[^\s@]+)*)"
    matches = re.findall(at_pattern, prompt)

    referenced_files_set = set() # Use a set to store unique Path objects

    for match in matches:
        path = Path(match)
        if is_valid_file(path):
            referenced_files_set.add(path)
        elif is_valid_directory(path):
            directory_files = get_directory_files(path)
            referenced_files_set.update(directory_files)
            if directory_files:
                logger.info(f"Directory '@{match}' expanded to {len(directory_files)} files")
        else:
            logger.warning(f"Referenced path '@{match}' not found. Skipping.")

    # Convert set to list for consistent return type, sort for deterministic order if needed
    referenced_files = sorted(referenced_files_set, key=lambda p: str(p))

    # Remove @ references from the prompt
    cleaned_prompt = re.sub(at_pattern, "", prompt).strip()
    # Clean up extra whitespace that might result from removal and multiple spaces
    cleaned_prompt = " ".join(cleaned_prompt.split())

    return cleaned_prompt, referenced_files

# Helper function to list spec files
def list_spec_files(specs_dir: Path, directory_filter: str | None = None) -> list[Path]:
    """Lists YAML spec files with optional directory filtering.

    Args:
        specs_dir: The Path to the specs directory
        directory_filter: None for all directories (excluding archive), or specific subdirectory name

    Returns:
        List of Path objects for matching spec files
    """
    if not specs_dir.exists() or not specs_dir.is_dir():
        logger.debug(f"Specs directory '{specs_dir}' does not exist or is not a directory.")
        return []

    spec_files = []

    if directory_filter is None:
        # Recursive scan - get files from all subdirectories and root, excluding archive
        spec_files_set = set()
        for item in specs_dir.rglob("*.yaml"):
            if item.is_file() and "archive" not in item.parts:
                spec_files_set.add(item)
        for item in specs_dir.rglob("*.yml"):
            if item.is_file() and "archive" not in item.parts:
                spec_files_set.add(item)
        spec_files = list(spec_files_set)
    else:
        # Single directory scan
        target_dir = specs_dir / directory_filter
        if target_dir.exists() and target_dir.is_dir():
            for item in target_dir.iterdir():
                if item.is_file() and item.suffix.lower() in (".yaml", ".yml"):
                    spec_files.append(item)
        else:
            logger.warning(f"Directory filter '{directory_filter}' not found in '{specs_dir}'")
            return []

    return sorted(spec_files, key=lambda p: p.name)

# Helper function to extract description from a spec file
def extract_spec_description(file_path: Path) -> str:
    """Extracts a description from a YAML spec file.

    Priority:
    1. Top-level 'description' field in YAML.
    2. First comment line in the file.
    3. "No description available."

    Args:
        file_path: Path to the spec file.

    Returns:
        The extracted description string.
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            content = f.read()

            # Try to parse YAML and get 'description' field
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict) and "description" in data and isinstance(data["description"], str):
                    return data["description"].strip()
            except yaml.YAMLError as e:
                logger.warning(f"Could not parse YAML from '{file_path}': {e}. Trying to find comments.")
            except OSError as e: # Catch other potential errors during YAML processing
                logger.warning(f"An unexpected error occurred during YAML parsing for '{file_path}': {e}. Trying to find comments.")


            # If no 'description' field, look for the first comment line
            f.seek(0) # Reset file pointer to read lines from the beginning
            for line in f:
                stripped_line = line.strip()
                if stripped_line.startswith("#"):
                    # Return the comment, removing the '#' and leading/trailing whitespace
                    return stripped_line[1:].strip()

            return "No description available."

    except FileNotFoundError:
        logger.exception(f"Spec file '{file_path}' not found during description extraction.")
        return "Error: File not found."
    except Exception as e:
        logger.exception(f"Could not read or process spec file '{file_path}': {e}")
        return "Error reading file."
