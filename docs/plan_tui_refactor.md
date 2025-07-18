# TUI Refactoring Plan: Unified Input Collection System

## Executive Summary

This plan outlines the refactoring of terminal user interface (TUI) input collection to create a unified, consistent system across CLI prompt commands and interactive workflows. The goal is to ensure both systems use the same terminal handoff functionality while maintaining backward compatibility.

## Requirements Analysis

### Primary Requirements
1. **Consistency**: CLI `prompt` command and interactive workflows must use the same underlying input collection system
2. **Terminal Handoff**: Both systems must integrate with the spinner pause/resume functionality
3. **Backward Compatibility**: Existing functionality must remain unchanged
4. **Minimal Changes**: Use the least invasive approach to achieve consistency

### Secondary Requirements
- Maintain robust error handling and retry logic
- Preserve processing feedback and user experience
- Keep code maintainable and follow best practices
- Ensure proper separation of concerns

## Current State Analysis

### File Locations and Current Logic Flow

#### `src/elf0/functions/utils.py` (Lines 126-215)
**Function**: `get_user_input(state: WorkflowState, prompt: str) -> WorkflowState`
**Current Logic Flow**:
```
1. set_collecting_input() ← Signal start of input collection
2. time.sleep(0.2) ← Wait for spinner to stop
3. Display prompt with Rich formatting
4. Collect input with retry logic:
   - If terminal: _collect_enhanced_input()
   - If non-terminal: _collect_simple_input()
5. Handle exit commands
6. Show processing feedback
7. Return WorkflowState
8. clear_collecting_input() ← Signal end of input collection
```
**Features**: ✅ Terminal handoff, ✅ Robust error handling, ✅ Processing feedback

#### `src/elf0/cli.py` (Lines 529-581)
**Function**: `get_multiline_input() -> str`
**Current Logic Flow**:
```
1. Display prompt with Rich formatting
2. Create PromptSession with history and lexer
3. Collect input in loop:
   - Handle submission commands (/send, double-enter)
   - Handle exit commands
   - Collect lines until submission
4. Return joined string
```
**Features**: ❌ No terminal handoff, ❌ Basic error handling, ❌ No processing feedback

#### `src/elf0/cli.py` (Lines 137-193)
**Function**: `progress_spinner(message: str) -> Generator[None]`
**Current Logic Flow**:
```
1. If verbose mode: yield (no spinner)
2. If non-verbose mode:
   - Create Rich Live spinner
   - Start background monitoring thread
   - Monitor is_collecting_input() state
   - Pause/resume spinner based on input state
   - Clean shutdown on exit
```
**Features**: ✅ Terminal handoff monitoring, ✅ Thread management

### Problem Statement

The CLI `prompt` command (`get_multiline_input()`) does not integrate with the terminal handoff system, causing:
- Users cannot see cursor during input collection
- Characters don't appear in real-time
- Inconsistent user experience between CLI and workflow modes
- Code duplication for similar functionality

## Target State Design

### Proposed Logic Flow Architecture

#### Core Input Collection Module
**New File**: `src/elf0/core/input_collector.py`
```
Core Function: collect_terminal_input(prompt: str, multiline: bool = True) -> str
Logic Flow:
1. set_collecting_input() ← Signal start
2. time.sleep(0.2) ← Wait for spinner handoff
3. Display prompt with Rich formatting
4. Collect input with robust error handling:
   - Terminal detection
   - Retry logic with fallbacks
   - Exit command handling
5. Show processing feedback
6. clear_collecting_input() ← Signal end
7. Return raw string input
```

#### Wrapper Functions
**Location**: `src/elf0/core/input_collector.py`
```
CLI Wrapper: get_cli_input() -> str
- Calls collect_terminal_input()
- Returns string for CLI compatibility

Workflow Wrapper: get_workflow_input(state: WorkflowState, prompt: str) -> WorkflowState
- Calls collect_terminal_input()
- Wraps result in WorkflowState format
- Handles state-specific logic
```

### Updated File Logic Flows

#### `src/elf0/functions/utils.py` (Refactored)
**Function**: `get_user_input(state: WorkflowState, prompt: str) -> WorkflowState`
**New Logic Flow**:
```
1. Extract prompt from state if needed
2. Call get_workflow_input(state, prompt) from input_collector
3. Return WorkflowState result
```
**Reduction**: ~90 lines → ~15 lines

#### `src/elf0/cli.py` (Refactored)
**Function**: `get_multiline_input() -> str`
**New Logic Flow**:
```
1. Display introductory messages
2. Call get_cli_input() from input_collector
3. Return string result
```
**Reduction**: ~53 lines → ~10 lines

#### `src/elf0/cli.py` (Unchanged)
**Function**: `progress_spinner(message: str) -> Generator[None]`
**Logic Flow**: Remains identical - no changes needed

## Implementation Plan

### Phase 1: Create Core Input Collection Module

#### Step 1.1: Create `src/elf0/core/input_collector.py`
- Define `InputCollectionError` exception class
- Implement `collect_terminal_input()` core function
- Consolidate logic from both existing functions
- Add comprehensive error handling and retry logic

#### Step 1.2: Create Wrapper Functions
- Implement `get_cli_input()` wrapper
- Implement `get_workflow_input()` wrapper
- Ensure proper abstraction and separation of concerns

### Phase 2: Refactor Existing Functions

#### Step 2.1: Update `src/elf0/functions/utils.py`
- Replace `get_user_input()` implementation
- Import and use `get_workflow_input()`
- Maintain exact same function signature and return type

#### Step 2.2: Update `src/elf0/cli.py`
- Replace `get_multiline_input()` implementation
- Import and use `get_cli_input()`
- Maintain exact same function signature and return type

### Phase 3: Testing and Validation

#### Step 3.1: Unit Testing
- Test core input collection functionality
- Test wrapper function behavior
- Verify error handling and edge cases

#### Step 3.2: Integration Testing
- Test CLI prompt command with terminal handoff
- Test interactive workflows continue working
- Verify spinner pause/resume behavior

#### Step 3.3: User Experience Testing
- Verify cursor visibility during input collection
- Confirm real-time character display
- Test exit commands and error scenarios

## Risk Assessment and Mitigation

### Low Risk Items
- ✅ Core input collection logic is well-tested
- ✅ Terminal handoff system is proven to work
- ✅ Wrapper pattern provides clean abstraction

### Medium Risk Items
- ⚠️ Function signature changes (mitigated by maintaining exact interfaces)
- ⚠️ Import dependencies (mitigated by keeping imports minimal)

### High Risk Items
- 🚨 Breaking existing functionality (mitigated by extensive testing)
- 🚨 Threading issues (mitigated by reusing proven terminal handoff code)

## Success Criteria

### Functional Requirements
- [ ] CLI prompt command shows cursor and real-time typing
- [ ] Interactive workflows continue working without changes
- [ ] Both systems use identical input collection behavior
- [ ] Exit commands work consistently across both systems
- [ ] Error handling is robust and consistent

### Non-Functional Requirements
- [ ] Code reduction of ~100 lines through consolidation
- [ ] Improved maintainability through shared logic
- [ ] No performance degradation
- [ ] Thread safety maintained

## File Modification Summary

### New Files
- `src/elf0/core/input_collector.py` (~100 lines)

### Modified Files
- `src/elf0/functions/utils.py` (Lines 126-215 → simplified)
- `src/elf0/cli.py` (Lines 529-581 → simplified)

### Unchanged Files
- `src/elf0/cli.py` (progress_spinner function remains identical)
- `src/elf0/core/input_state.py` (no changes needed)

## Best Practices Adherence

### Code Organization
- ✅ Single responsibility principle (one input collection system)
- ✅ DRY principle (eliminate code duplication)
- ✅ Separation of concerns (core logic vs. wrappers)

### Error Handling
- ✅ Graceful degradation with fallback mechanisms
- ✅ Proper exception handling and cleanup
- ✅ User-friendly error messages

### Threading
- ✅ Thread-safe state management
- ✅ Proper resource cleanup
- ✅ Reuse of proven terminal handoff patterns

## Conclusion

This refactoring plan provides a minimal, low-risk approach to unifying the input collection systems while maintaining all existing functionality. The use of a core module with wrapper functions ensures clean abstraction while enabling significant code reduction and improved maintainability.

The key insight is that both systems need the same fundamental capability (terminal input collection with handoff) but present it through different interfaces. By creating a shared core with appropriate wrappers, we achieve consistency without breaking existing APIs.