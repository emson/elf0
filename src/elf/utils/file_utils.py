from pathlib import Path
from typing import List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

def is_valid_file(path: Path) -> bool:
    """Check if a path exists and is a file."""
    return path.exists() and path.is_file()

def read_files_content(files: List[Path]) -> str:
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
            with open(current_path, 'r', encoding='utf-8') as f:
                content_parts.append(f"Content of {current_path.name}:\n{f.read()}\n---")
        except Exception as e:
            logger.warning(f"Could not read context file '{file_path}': {e}. Skipping.")
    return "\n".join(content_parts)

def parse_comma_separated_files(file_str: str) -> List[Path]:
    """Parse a comma-separated string of file paths.
    
    Args:
        file_str: A string containing comma-separated file paths.
        
    Returns:
        A list of valid Path objects.
    """
    valid_files = []
    for f_name in file_str.split(','):
        path = Path(f_name.strip())
        if is_valid_file(path):
            valid_files.append(path)
        else:
            logger.warning(f"Context file '{f_name.strip()}' not found or is not a file. Skipping.")
    return valid_files

def parse_context_files(context_files_input: Optional[List[Path]]) -> str:
    """
    Parse and read content from a list of context file paths.
    
    Handles paths that might themselves be comma-separated strings of filenames.
    
    Args:
        context_files_input: List of Path objects. Some Path objects' string
                             representations might be comma-separated filenames.
                             
    Returns:
        Combined content from all valid context files.
    """
    if not context_files_input:
        return ""
        
    actual_files_to_read: List[Path] = []
    processed_paths_for_deduplication = set() # To avoid processing the same file path string multiple times

    for path_item in context_files_input:
        path_str = str(path_item).strip()
        
        if not path_str:
            continue

        # Handle cases where a single Path item might represent a comma-separated list
        # This behavior is retained from the original CLI logic.
        if ',' in path_str:
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

def parse_at_references(prompt: str) -> Tuple[str, List[Path]]:
    """
    Parse @file references from a prompt string.
    
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
    at_pattern = r'@([^\s@]+(?:\.[^\s@]+)*)'
    matches = re.findall(at_pattern, prompt)
    
    referenced_files_set = set() # Use a set to store unique Path objects
    
    for match in matches:
        path = Path(match)
        if is_valid_file(path):
            referenced_files_set.add(path)
        else:
            logger.warning(f"Referenced file '@{match}' not found or is not a file. Skipping.")
    
    # Convert set to list for consistent return type, sort for deterministic order if needed
    referenced_files = sorted(list(referenced_files_set), key=lambda p: str(p))

    # Remove @ references from the prompt
    cleaned_prompt = re.sub(at_pattern, '', prompt).strip()
    # Clean up extra whitespace that might result from removal and multiple spaces
    cleaned_prompt = ' '.join(cleaned_prompt.split())
    
    return cleaned_prompt, referenced_files 