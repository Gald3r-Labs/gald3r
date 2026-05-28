"""
Context System for Hybrid Agent Architecture

Provides unified context management for SDK and prompt-based agents.

Components:
- schema: Pydantic models for context structure
- manager: Context lifecycle management (CRUD, archiving, cleanup)
- utils: Helper functions for context operations

Author: Database Expert Agent
Date: 2025-11-01
Task: 052 - Anthropic Agent SDK Integration
"""

from .schema import (
    AgentContext,
    AgentMode,
    AgentState,
    AgentStatus,
    CommandExecution,
    FallbackLog,
    HookEvent,
    MemoryContext,
    SharedArtifacts,
    WorkflowMetadata,
)
from .manager import ContextManager

__all__ = [
    # Schema models
    "AgentContext",
    "AgentMode",
    "AgentState",
    "AgentStatus",
    "CommandExecution",
    "FallbackLog",
    "HookEvent",
    "MemoryContext",
    "SharedArtifacts",
    "WorkflowMetadata",
    # Manager
    "ContextManager",
]

__version__ = "1.0.0"
