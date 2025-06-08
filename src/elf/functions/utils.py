# src/elf/functions/utils.py
"""Utility functions for Elf workflows."""

from ..core.compiler import WorkflowState
from typing import Dict, Any

def get_user_input(state: WorkflowState, prompt: str = "Please provide input:") -> WorkflowState:
    """
    Function that requests user input via CLI.
    
    Args:
        state: Current workflow state
        prompt: Question or prompt to display to user
        
    Returns:
        Updated workflow state with user response
    """
    print(f"\n📝 {prompt}")
    user_response = input("> ")
    
    return {
        **state,
        'user_input': user_response,
        'output': f"User provided: {user_response}"
    }

def text_processor(state: WorkflowState, operation: str = "count_words") -> WorkflowState:
    """
    Process text from workflow state.
    
    Args:
        state: Current workflow state
        operation: Processing operation to perform
        
    Returns:
        Updated workflow state with processed results
    """
    # Use output if available, otherwise fall back to input
    text = state.get("output") or state.get("input", "")
    
    if operation == "count_words":
        word_count = len(text.split()) if text else 0
        return {
            **state,
            "output": f"Word count: {word_count}",
            "word_count": word_count,
            "processed_text": text
        }
    elif operation == "uppercase":
        transformed = text.upper()
        return {
            **state,
            "output": transformed,
            "transformation": "uppercase"
        }
    elif operation == "length":
        char_count = len(text)
        return {
            **state,
            "output": f"Character count: {char_count}",
            "character_count": char_count,
            "processed_text": text
        }
    else:
        return {
            **state,
            "output": f"Unknown operation: {operation}",
            "error_context": f"Unsupported operation: {operation}"
        }