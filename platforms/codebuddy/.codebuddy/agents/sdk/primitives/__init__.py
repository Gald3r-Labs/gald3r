"""
Cursor Primitives Integration for Agent SDK

Provides SDK agents with access to Cursor's core primitives:
- Plugins: MCP tool invocation
- Memory: Persistent storage and recall
- Commands: Slash command execution
- Hooks: Lifecycle event triggers

Usage:
    from .primitives import Plugins, Memory, Commands, Hooks

    # In your agent
    plugins = Plugins()
    result = plugins.call("mcp__brave_search", query="API design patterns")

    memory = Memory(agent_name="backend-developer")
    memory.store("db_preference", "PostgreSQL")
    preference = memory.recall("db_preference")
"""

from .plugins import Plugins
from .memory import Memory
from .commands import Commands
from .hooks import Hooks

__all__ = ["Plugins", "Memory", "Commands", "Hooks"]
