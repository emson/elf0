# src/awa/core/errors.py

from typing import Optional
from pydantic import BaseModel

class AWAError(Exception):
    """Base exception for all AWA errors"""
    pass

class WorkflowError(AWAError):
    """Base exception for workflow-related errors"""
    pass

class WorkflowLoaderError(WorkflowError):
    """Raised when there are issues loading a workflow"""
    pass

class WorkflowExecutorError(WorkflowError):
    """Base exception for workflow execution errors"""
    pass

class StepDependencyError(WorkflowExecutorError):
    """Raised when a step's dependencies are not met"""
    pass

class LLMClientError(WorkflowExecutorError):
    """Base exception for LLM client errors"""
    pass

class LLMRateLimitError(LLMClientError):
    """Raised when the LLM API rate limit is exceeded"""
    pass

class LLMConnectionError(LLMClientError):
    """Raised when there's a connection issue with the LLM API"""
    pass

class LLMValidationError(LLMClientError):
    """Raised when LLM response validation fails"""
    pass

class ToolError(WorkflowExecutorError):
    """Base exception for tool-related errors"""
    pass

class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found"""
    pass

class ToolExecutionError(ToolError):
    """Raised when tool execution fails"""
    pass

class ValidationError(AWAError):
    """Raised when validation fails"""
    pass

class ConfigurationError(AWAError):
    """Raised when configuration is invalid"""
    pass
