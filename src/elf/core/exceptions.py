# src/elf/core/exceptions.py
"""Custom exceptions for Elf workflows."""


class UserExitRequested(Exception):
    """Raised when user requests to exit the workflow via /exit, /quit, or /bye commands."""


class WorkflowValidationError(Exception):
    """Raised when workflow specification is invalid or missing required components."""

