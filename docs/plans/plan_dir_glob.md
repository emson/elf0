# Plan: Directory Reference Support (@directory/)

## Overview

Extend Elf0's existing file reference system (`@file.py`) to support directory references (`@src/`) with intelligent file discovery and filtering.

## Requirements Analysis

### Current State
- **File references**: `@path/to/file.py` works perfectly
- **Implementation**: `src/elf0/utils/file_utils.py:parse_at_references()`
- **Usage**: CLI commands and interactive mode
- **Flow**: Parse → Validate → Read → Include in prompt

### New Requirements
- **Directory references**: `@path/to/directory/` syntax
- **Intelligent filtering**: Include relevant files (code, config, docs)
- **Safety limits**: Prevent overwhelming LLM with too many files
- **Backward compatibility**: All existing functionality preserved

### Design Decisions
- **Syntax**: `@directory/` (no asterisk) - clean and consistent with existing pattern
- **Recursion**: Single level only (non-recursive) for performance and clarity
- **File filtering**: Smart detection of relevant file types
- **Ordering**: Alphabetical sorting for consistent, predictable output

## Implementation Plan

### Phase 1: Core Logic Enhancement

#### File Locations and Changes

**Primary file**: `src/elf0/utils/file_utils.py`

**Function modifications**:
1. **`parse_at_references()` (lines 102-136)** - Extend to handle directories
2. **Add new helper functions** after `is_valid_file()` (after line 11)
3. **Enhance `read_files_content()` (lines 13-30)** - Better headers for directory files

#### New Helper Functions

```python
def is_valid_directory(path: Path) -> bool:
    """Check if a path exists and is a directory."""
    return path.exists() and path.is_dir()

def is_relevant_file(path: Path) -> bool:
    """Check if a file should be included in directory scanning.
    
    Includes code, configuration, and documentation files.
    Excludes binary files, hidden files, and generated files.
    """
    # Define relevant file extensions
    code_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
                 '.rs', '.go', '.rb', '.php', '.sh', '.sql', '.r', '.scala', '.kt'}
    config_exts = {'.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.env', '.cfg'}
    doc_exts = {'.md', '.rst', '.txt', '.adoc'}
    
    # Skip hidden files and directories
    if path.name.startswith('.'):
        return False
    
    # Skip common binary/generated files
    skip_exts = {'.pyc', '.pyo', '.class', '.exe', '.dll', '.so', '.o', '.a',
                 '.zip', '.tar', '.gz', '.7z', '.rar', '.pdf', '.jpg', '.jpeg',
                 '.png', '.gif', '.svg', '.mp4', '.avi', '.mp3', '.wav'}
    
    suffix = path.suffix.lower()
    
    # Include relevant files
    if suffix in code_exts or suffix in config_exts or suffix in doc_exts:
        return True
    
    # Exclude known binary files
    if suffix in skip_exts:
        return False
    
    # Handle files without extension (Makefile, Dockerfile, etc.)
    if not suffix and path.is_file():
        try:
            # Size limit check (1MB)
            if path.stat().st_size > 1024 * 1024:
                return False
            # Basic text file detection
            with path.open('rb') as f:
                sample = f.read(min(1024, path.stat().st_size))
                if not sample:
                    return False
                # Check if mostly printable characters
                printable = sum(1 for b in sample if 32 <= b <= 126 or b in (9, 10, 13))
                return printable / len(sample) > 0.7
        except (OSError, UnicodeDecodeError):
            return False
    
    return False

def get_directory_files(directory: Path, max_files: int = 50) -> list[Path]:
    """Get relevant files from a directory (non-recursive).
    
    Args:
        directory: Directory to scan
        max_files: Maximum number of files to return (safety limit)
        
    Returns:
        List of relevant file paths, sorted alphabetically
    """
    relevant_files = []
    
    try:
        for item in directory.iterdir():
            if item.is_file() and is_relevant_file(item):
                relevant_files.append(item)
                
                # Safety limit to prevent overwhelming LLM
                if len(relevant_files) >= max_files:
                    logger.warning(f"Directory '@{directory}' contains many files. "
                                 f"Only including first {max_files} relevant files.")
                    break
        
        # Sort for consistent, predictable ordering
        return sorted(relevant_files, key=lambda p: p.name.lower())
        
    except PermissionError:
        logger.warning(f"Permission denied accessing directory '@{directory}'")
        return []
    except OSError as e:
        logger.warning(f"Could not read directory '@{directory}': {e}")
        return []
```

#### Enhanced parse_at_references()

**Current logic** (lines 121-126):
```python
for match in matches:
    path = Path(match)
    if is_valid_file(path):
        referenced_files_set.add(path)
    else:
        logger.warning(f"Referenced file '@{match}' not found or is not a file. Skipping.")
```

**New logic**:
```python
for match in matches:
    path = Path(match)
    if is_valid_file(path):
        # Existing file behavior - unchanged
        referenced_files_set.add(path)
    elif is_valid_directory(path):
        # New directory behavior
        directory_files = get_directory_files(path)
        referenced_files_set.update(directory_files)
        if directory_files:
            logger.info(f"Directory '@{match}' expanded to {len(directory_files)} files")
    else:
        logger.warning(f"Referenced path '@{match}' not found. Skipping.")
```

#### Enhanced read_files_content()

**Update file headers** to show directory context:
```python
# Current: f"Content of {current_path.name}:\n{f.read()}\n---"
# New: Show directory context when relevant
if len(str(current_path.parent)) > 1:  # Not just "."
    header = f"Content of {current_path.parent}/{current_path.name}"
else:
    header = f"Content of {current_path.name}"
content_parts.append(f"{header}:\n{f.read()}\n---")
```

### Phase 2: Testing Strategy

Following **@docs/testing_principles.md**:

#### Test at CLI Level (Primary)
**File**: `tests/cli/test_cli.py` (extend existing)

```python
def test_directory_reference_cli(tmp_path, runner):
    """Test CLI command with directory reference."""
    # Arrange: Create test directory with files
    test_dir = tmp_path / "test_src"
    test_dir.mkdir()
    (test_dir / "main.py").write_text("print('hello')")
    (test_dir / "config.json").write_text('{"key": "value"}')
    (test_dir / "README.md").write_text("# Test project")
    
    spec_file = tmp_path / "test_spec.yaml"
    spec_file.write_text(create_minimal_spec())
    
    # Act: Run CLI with directory reference
    result = runner.invoke(app, [
        "agent", str(spec_file), 
        "--prompt", f"Analyze @{test_dir}/"
    ])
    
    # Assert: Command succeeds and includes all relevant files
    assert result.exit_code == 0
    # Don't test exact output format (implementation detail)
    # Test that all files were processed (observable behavior)

def test_mixed_file_and_directory_references(tmp_path, runner):
    """Test CLI with both file and directory references."""
    # Test real use case: mixed references
    # Arrange, Act, Assert pattern

def test_directory_reference_safety_limits(tmp_path, runner):
    """Test directory with many files respects safety limits."""
    # Test edge case: too many files
```

#### Unit Tests for New Functions
**File**: `tests/utils/test_file_utils.py` (new file)

```python
class TestDirectoryFileDiscovery:
    """Test directory file discovery functionality."""
    
    def test_is_relevant_file_code_files(self, tmp_path):
        """Test that code files are identified as relevant."""
        # Arrange
        code_file = tmp_path / "test.py"
        code_file.write_text("print('hello')")
        
        # Act & Assert
        assert is_relevant_file(code_file) is True
    
    def test_is_relevant_file_binary_files(self, tmp_path):
        """Test that binary files are excluded."""
        # Test real use case: avoid binary files
        
    def test_get_directory_files_sorts_output(self, tmp_path):
        """Test that directory files are returned in sorted order."""
        # Test observable behavior: consistent ordering
        
    def test_get_directory_files_respects_limits(self, tmp_path):
        """Test that file count limits are enforced."""
        # Test edge case: safety limits
```

#### Integration Tests
**File**: `tests/integration/test_directory_references.py` (new file)

```python
def test_end_to_end_directory_workflow(tmp_path):
    """Test complete workflow execution with directory references."""
    # Test high-level behavior: full workflow with directory refs
    # Focus on user-facing functionality, not implementation
```

### Phase 3: Edge Cases and Error Handling

#### Edge Cases to Handle
1. **Empty directories** - Return empty list, log info message
2. **Permission denied** - Graceful fallback, clear error message
3. **Symbolic links** - Follow links but detect cycles
4. **Very large files** - Size limits and warnings
5. **Binary files** - Detection and exclusion
6. **Many files** - Safety limits and truncation
7. **Non-existent paths** - Clear error messages
8. **Mixed valid/invalid references** - Process valid ones, warn about invalid

#### Error Handling Patterns
Follow existing patterns in codebase:
- Use `logger.warning()` for non-fatal issues
- Use `logger.info()` for informational messages
- Graceful degradation (skip problematic files, continue processing)
- Clear, actionable error messages

### Phase 4: Documentation Updates

#### Files to Update

**1. README.md**
- Update file reference section with directory examples
- Add new examples in usage sections
- Update quick start guide

**2. CLI Help Text**
**File**: `src/elf0/cli.py`
- Update docstrings for `agent_command()` and `prompt_yaml_command()`
- Add directory reference examples

**3. New Documentation**
**File**: `docs/features/feature_file_references.md` (new)
- Comprehensive guide to file and directory references
- Examples and best practices
- Troubleshooting common issues

#### Documentation Examples

```markdown
### File and Directory References

Include files and directories in your prompts using `@` syntax:

```bash
# Single file
uv run elf0 agent workflow.yaml --prompt "Review @src/main.py"

# Directory (all relevant files)
uv run elf0 agent workflow.yaml --prompt "Analyze all code in @src/"

# Mixed references
uv run elf0 agent workflow.yaml --prompt "Review @config.json and all files in @src/"

# Multiple directories
uv run elf0 agent workflow.yaml --prompt "Compare @src/ and @tests/"
```

**Supported file types in directories:**
- **Code**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.rs`, `.go`, etc.
- **Configuration**: `.json`, `.yaml`, `.xml`, `.toml`, `.ini`, etc.
- **Documentation**: `.md`, `.rst`, `.txt`, etc.
- **Scripts**: `.sh`, `.sql`, Makefile, Dockerfile, etc.

**Automatically excluded:**
- Hidden files (starting with `.`)
- Binary files (images, executables, archives)
- Generated files (`.pyc`, `.class`, etc.)
```

### Phase 5: Backward Compatibility and Migration

#### No Breaking Changes
- All existing `@file.py` syntax continues working
- Same regex pattern captures both files and directories
- Function signatures preserved
- Error handling enhanced, not changed

#### Enhanced User Experience
- Better error messages distinguish files vs directories
- Informational logging shows directory expansion
- Consistent file ordering reduces prompt variation
- Safety limits prevent performance issues

## Testing Strategy Details

### Following Testing Principles

#### 1. Test High-Level Behavior
- **Focus**: CLI commands work with directory references
- **Avoid**: Testing internal file filtering logic details
- **Example**: Test that `uv run elf0 agent spec.yaml --prompt "Review @src/"` succeeds

#### 2. Test Real Use Cases
- **Common scenarios**: Mixed file and directory references
- **Edge cases**: Empty directories, permission errors
- **User workflows**: Code review, documentation generation

#### 3. Maintain Test Independence
- **Setup**: Each test creates its own temporary directory structure
- **Cleanup**: Automatic with `tmp_path` fixture
- **Isolation**: No shared state between tests

#### 4. CLI-Level Testing
- **Primary approach**: Use `CliRunner` for command testing
- **Focus**: Parameter handling and output behavior
- **Avoid**: Direct function calls for CLI features

#### 5. Simple and Clear Tests
- **Naming**: `test_directory_reference_expands_files`
- **Structure**: Clear Arrange-Act-Assert sections
- **Assertions**: Test observable behavior, not implementation

### Test File Organization

```
tests/
├── cli/
│   └── test_cli.py                 # Extended with directory tests
├── utils/
│   └── test_file_utils.py         # New: unit tests for helpers
├── integration/
│   └── test_directory_references.py # New: end-to-end tests
└── fixtures/
    └── test_directory_structures/   # New: test data
```

## Implementation Benefits

### For Users
- **Natural syntax**: `@src/` instead of listing individual files
- **Intelligent filtering**: Only relevant files included automatically
- **Consistent behavior**: Predictable file ordering and inclusion
- **Safety features**: Protection against too many files or binary content

### For Developers
- **Minimal changes**: Extends existing architecture cleanly
- **Reusable code**: New helpers useful for other features
- **Testable design**: Clear separation of concerns
- **Error resilience**: Graceful handling of edge cases

### For Maintainers
- **Backward compatibility**: No disruption to existing workflows
- **Clear logging**: Easy to debug and troubleshoot
- **Extensible design**: Easy to add new file types or filters
- **Well-tested**: Comprehensive test coverage

## Risk Mitigation

### Performance Risks
- **File count limits**: Maximum 50 files per directory
- **File size limits**: Skip files larger than 1MB
- **Memory management**: Stream file reading where possible

### Security Risks
- **Permission handling**: Graceful permission denied handling
- **Path traversal**: No recursive directory scanning
- **Binary file detection**: Prevent including binary content

### User Experience Risks
- **Clear feedback**: Informative messages about file inclusion/exclusion
- **Predictable behavior**: Consistent ordering and filtering
- **Error recovery**: Continue processing when some files fail

## Implementation Timeline

### Phase 1: Core Implementation (Week 1)
- Implement helper functions
- Extend `parse_at_references()`
- Basic manual testing

### Phase 2: Testing (Week 1)
- Create comprehensive test suite
- CLI integration tests
- Edge case testing

### Phase 3: Documentation (Week 1)
- Update README and CLI help
- Create feature documentation
- Usage examples

### Phase 4: Validation (Week 1)
- End-to-end testing
- Performance validation
- User acceptance testing

## Success Criteria

### Functional Requirements
- ✅ `@directory/` syntax works in CLI commands
- ✅ `@directory/` syntax works in interactive mode
- ✅ Mixed file and directory references work
- ✅ Intelligent file filtering excludes binary files
- ✅ Safety limits prevent performance issues
- ✅ All existing functionality preserved

### Quality Requirements
- ✅ Comprehensive test coverage (>90%)
- ✅ No performance regression
- ✅ Clear error messages and logging
- ✅ Documentation updated and accurate
- ✅ Code style consistent with existing codebase

### User Experience Requirements
- ✅ Intuitive syntax matching existing patterns
- ✅ Predictable and consistent behavior
- ✅ Helpful feedback and error messages
- ✅ Smooth migration from existing workflows

This plan ensures a robust, well-tested implementation that extends Elf0's powerful file reference system while maintaining the high quality and reliability users expect.