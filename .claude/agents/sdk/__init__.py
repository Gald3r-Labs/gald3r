"""
Anthropic Agent SDK Integration for Claude Code SubAgents

This package provides the base infrastructure for SDK-powered agents
with shared context, workflows, and Cursor primitives integration.

Includes robust fallback and error handling for 100% system availability.
"""

# Core SDK components (when implemented)
# from .base_agent import BaseAgent
# from .context import AgentContext
# from .workflow import AgentWorkflow

# Fallback and health monitoring (implemented)
from .fallback import (
    FallbackHandler,
    HybridAgentInvoker,
    FailureReason,
    AgentType
)

from .health import (
    HealthMonitor,
    HealthStatus,
    SDKAvailabilityCheck,
    APIKeyCheck,
    AgentFilesCheck,
    ContextStorageCheck,
    ResourceCheck,
    NetworkCheck
)

__all__ = [
    # Core components (pending)
    # "BaseAgent",
    # "AgentContext",
    # "AgentWorkflow",

    # Fallback and error handling
    "FallbackHandler",
    "HybridAgentInvoker",
    "FailureReason",
    "AgentType",

    # Health monitoring
    "HealthMonitor",
    "HealthStatus",
    "SDKAvailabilityCheck",
    "APIKeyCheck",
    "AgentFilesCheck",
    "ContextStorageCheck",
    "ResourceCheck",
    "NetworkCheck",
]

__version__ = "0.2.0"  # Fallback system implemented
