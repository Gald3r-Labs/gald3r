# Cursor Primitives Integration for Agent SDK

This module provides Agent SDK agents with access to Cursor's core primitives:

- **Plugins**: Invoke MCP tools
- **Memory**: Persistent storage and recall
- **Commands**: Execute slash commands
- **Hooks**: Lifecycle event triggers

## Overview

The primitives system enables SDK agents to leverage Cursor's full capabilities while maintaining structured context sharing and state management.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SDK Agent                                 │
│  (Backend Developer, Frontend Developer, etc.)               │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Plugins    │ │    Memory    │ │   Commands   │
    │  (MCP Tools) │ │ (Persistent) │ │ (Slash Cmds) │
    └──────────────┘ └──────────────┘ └──────────────┘
            │               │               │
            └───────────────┼───────────────┘
                            ▼
                    ┌──────────────┐
                    │    Hooks     │
                    │ (Lifecycle)  │
                    └──────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Cursor IDE System    │
                │  - .cursor/memory/    │
                │  - .cursor/hooks/     │
                │  - .cursor/commands/  │
                │  - MCP plugins        │
                └───────────────────────┘
```

## Installation

The primitives module is included in the Agent SDK installation:

```python
from .primitives import Plugins, Memory, Commands, Hooks
```

## Usage

### 1. Plugins

Invoke MCP plugins (tools) from your agent:

```python
from .primitives import Plugins

# Initialize
plugins = Plugins()

# Search for examples
search_results = plugins.call(
    "mcp__brave_search",
    query="FastAPI authentication best practices",
    max_results=5
)

# Access results
for result in search_results["data"]["results"]:
    print(f"- {result['title']}: {result['url']}")

# List available plugins
available = plugins.list_available()
# ["mcp__brave_search", "mcp__filesystem", "mcp__github", ...]

# Get invocation log
log = plugins.get_invocation_log()
```

#### With Agent Context

```python
# Pass context to automatically store results
plugins = Plugins(context=agent_context)

# Result is automatically stored in agent_context["plugin_results"]
result = plugins.call("mcp__brave_search", query="API design patterns")
```

#### Common Plugins

- `mcp__brave_search`: Web search
- `mcp__filesystem`: File system operations
- `mcp__github`: GitHub API
- `mcp__postgres`: PostgreSQL database
- `mcp__sqlite`: SQLite database
- `mcp__memory`: Memory system
- `mcp__fetch`: HTTP requests
- `mcp__playwright`: Browser automation

### 2. Memory

Store and recall agent decisions, preferences, and learnings:

```python
from .primitives import Memory

# Initialize for specific agent
memory = Memory(agent_name="backend-developer")

# Store a preference
memory.store("database_preference", "PostgreSQL",
            metadata={"source": "user_request", "confidence": 0.95})

# Recall a preference
db = memory.recall("database_preference")  # "PostgreSQL"
db_or_default = memory.recall("missing_key", default="MySQL")

# Search for related memories
auth_memories = memory.search("authentication")
# Returns all memories with "authentication" in key, value, or metadata

# List all memories
all_memories = memory.list_all()
for key, entry in all_memories.items():
    print(f"{key}: {entry['value']} (stored: {entry['timestamp']})")

# Delete a memory
memory.delete("old_preference")

# Get statistics
stats = memory.get_stats()
# {
#   "total_memories": 10,
#   "agent": "backend-developer",
#   "oldest_memory": "2025-10-01T12:00:00Z",
#   "newest_memory": "2025-11-01T15:30:00Z"
# }
```

#### Memory Storage

Memories are persisted to:
```
.cursor/memory/agent_decisions/{agent_name}/memory.json
```

This allows memories to survive across sessions and be shared between agent invocations.

#### Example: Learning User Preferences

```python
class BackendDeveloper(BaseAgent):
    def __init__(self):
        super().__init__(name="backend-developer")
        self.memory = Memory(agent_name=self.name)

    def process(self, context):
        # Check if user has database preference
        db_pref = self.memory.recall("database_preference")

        if db_pref:
            print(f"[Memory] Using preferred database: {db_pref}")
            context.set("database_type", db_pref)
        else:
            # Ask user and remember choice
            db_choice = context.get("database_type", "PostgreSQL")
            self.memory.store("database_preference", db_choice,
                            metadata={"learned_from": context.get("task")})

        # Remember successful patterns
        if result.success:
            self.memory.store("last_successful_pattern", {
                "task": context.get("task"),
                "approach": result.approach,
                "files_created": result.files,
                "timestamp": context.get("timestamp")
            })
```

### 3. Commands

Execute slash commands programmatically:

```python
from .primitives import Commands

# Initialize
commands = Commands()

# Execute a command
result = commands.execute("/review-pr", pr_number=123)
# {
#   "status": "success",
#   "command": "review-pr",
#   "output": "PR #123 reviewed: 3 issues found",
#   "timestamp": "2025-11-01T15:30:00Z"
# }

# Execute with multiple arguments
result = commands.execute("/status", format="json", verbose=True)

# List available commands
available = commands.list_available()
# [
#   {"name": "review-pr", "file": "/path/to/review-pr.md", "description": "..."},
#   {"name": "status", "file": "/path/to/status.md", "description": "..."}
# ]

# Get execution history
history = commands.get_history()
for execution in history:
    print(f"{execution['command']}: {execution['result']['status']}")
```

#### With Agent Context

```python
# Pass context to automatically log command executions
commands = Commands(context=agent_context)

# Execution is automatically logged in agent_context["commands_executed"]
result = commands.execute("/run-tests", suite="backend")
```

#### Example: Agent Workflow

```python
class BackendDeveloper(BaseAgent):
    def __init__(self):
        super().__init__(name="backend-developer")
        self.commands = Commands()

    def process(self, context):
        # Implement feature
        self._implement_api(context)

        # Run tests via command
        test_result = self.commands.execute("/run-tests", suite="api")

        if test_result["status"] == "success":
            # Trigger code review
            review_result = self.commands.execute("/review")
            context.set("review_passed", review_result["status"] == "success")

        return context
```

### 4. Hooks

Trigger lifecycle events for validation, logging, and notifications:

```python
from .primitives import Hooks

# Initialize for specific agent
hooks = Hooks(agent_name="backend-developer")

# Trigger agent start
hooks.trigger("agent-start", context={"task": "Build authentication API"})

# Trigger agent completion
hooks.trigger("agent-complete",
             context={"task": "Build authentication API"},
             result={"status": "success", "files_created": 5})

# Trigger agent error
try:
    # ... agent work ...
    pass
except Exception as e:
    hooks.trigger("agent-error",
                 context={"task": "Build authentication API"},
                 error=str(e))

# Get event log
event_log = hooks.get_event_log()
for event in event_log:
    print(f"[{event['timestamp']}] {event['event']}: {event['agent']}")
```

#### Hook Scripts

Hooks execute bash scripts in `.cursor/hooks/`:

- `agent-start.sh`: Triggered when agent starts
- `agent-complete.sh`: Triggered when agent completes
- `agent-error.sh`: Triggered on agent error

Event data is passed as JSON via stdin.

#### Creating Hook Templates

```python
hooks = Hooks(agent_name="backend-developer")

# Create default hook templates
for event in ["agent-start", "agent-complete", "agent-error"]:
    hooks.create_hook_template(event)
```

#### Example Hook Script

```bash
#!/bin/bash
# .cursor/hooks/agent-complete.sh

# Read event data (JSON via stdin)
EVENT_DATA=$(cat)

# Extract fields
AGENT=$(echo "$EVENT_DATA" | jq -r '.agent')
TASK=$(echo "$EVENT_DATA" | jq -r '.data.context.task')

# Log completion
echo "[$(date)] Agent $AGENT completed: $TASK" >> .cursor/logs/completions.log

# Send notification (optional)
# notify-send "Agent Completed" "$AGENT: $TASK"

exit 0
```

#### Example: Full Lifecycle Tracking

```python
class BackendDeveloper(BaseAgent):
    def __init__(self):
        super().__init__(name="backend-developer")
        self.hooks = Hooks(agent_name=self.name)

    def process(self, context):
        # Trigger start hook (for validation/logging)
        self.hooks.trigger("agent-start", context=context)

        try:
            # Do work
            result = self._implement_backend(context)

            # Trigger completion hook
            self.hooks.trigger("agent-complete",
                             context=context,
                             result=result)

            return result

        except Exception as e:
            # Trigger error hook
            self.hooks.trigger("agent-error",
                             context=context,
                             error=str(e))
            raise
```

## Complete Agent Example

Here's a complete example of an SDK agent using all primitives:

```python
# .cursor/agents/sdk/agents/backend_developer.py
from ..base_agent import BaseAgent
from ..primitives import Plugins, Memory, Commands, Hooks

class BackendDeveloper(BaseAgent):
    """Backend development specialist with full primitives integration"""

    def __init__(self):
        super().__init__(
            name="backend-developer",
            description="Backend development specialist",
            model="claude-opus-4-5"
        )

        # Initialize primitives
        self.memory = Memory(agent_name=self.name)
        self.plugins = Plugins()
        self.commands = Commands()
        self.hooks = Hooks(agent_name=self.name)

    def process(self, context):
        """
        Main agent processing with primitives integration

        Args:
            context: AgentContext with shared state

        Returns:
            Updated context with results
        """
        # 1. Trigger start hook
        self.hooks.trigger("agent-start", context=context)

        try:
            task = context.get("task")

            # 2. Check memory for user preferences
            db_pref = self.memory.recall("database_preference")
            test_framework = self.memory.recall("test_framework", default="pytest")

            print(f"[Memory] Database: {db_pref}, Tests: {test_framework}")

            # 3. Search for examples using plugin
            if context.get("search_examples", False):
                search_results = self.plugins.call(
                    "mcp__brave_search",
                    query=f"{task} implementation example",
                    max_results=5
                )
                context.set("reference_examples", search_results["data"])

            # 4. Implement backend
            result = self._implement_backend(
                task=task,
                db_type=db_pref,
                test_framework=test_framework
            )

            # 5. Run tests via command
            test_result = self.commands.execute("/run-tests", suite="backend")

            if test_result["status"] == "success":
                # 6. Remember successful pattern
                self.memory.store("last_successful_pattern", {
                    "task": task,
                    "approach": result.approach,
                    "timestamp": context.get("timestamp")
                })

                # 7. Update context
                context.set("backend_complete", True)
                context.set("tests_passing", True)
                context.set("api_endpoints", result.endpoints)

                # 8. Trigger completion hook
                self.hooks.trigger("agent-complete",
                                 context=context,
                                 result=result)

                return {
                    "status": "completed",
                    "endpoints": result.endpoints,
                    "tests_passing": True
                }
            else:
                raise Exception("Tests failed")

        except Exception as e:
            # Trigger error hook
            self.hooks.trigger("agent-error",
                             context=context,
                             error=str(e))
            raise

    def _implement_backend(self, task, db_type, test_framework):
        """Actual backend implementation logic"""
        # ... implementation ...
        pass
```

## Integration with Agent Context

All primitives can automatically integrate with agent context:

```python
from ..context import AgentContext
from ..primitives import Plugins, Memory, Commands, Hooks

# Create context
context = AgentContext({"task": "Build auth API"})

# Initialize primitives with context
plugins = Plugins(context=context)
commands = Commands(context=context)

# Use primitives - results automatically stored in context
plugins.call("mcp__brave_search", query="auth patterns")
commands.execute("/review-pr", pr_number=123)

# Context now contains:
# {
#   "task": "Build auth API",
#   "plugin_results": {
#     "mcp__brave_search": {...}
#   },
#   "commands_executed": [
#     {"/review-pr": {"pr_number": 123, "result": {...}}}
#   ]
# }
```

## Best Practices

### Memory

1. **Namespace by agent**: Each agent has its own memory space
2. **Add metadata**: Include source, confidence, timestamps
3. **Clean up old memories**: Use delete() for obsolete data
4. **Search before store**: Check if preference already exists

### Plugins

1. **Cache results**: Plugin results are cached automatically
2. **Handle errors**: Check result["status"] before using data
3. **Clear cache**: Use clear_cache() for fresh data
4. **Pass context**: Initialize with context for automatic storage

### Commands

1. **Check availability**: Use list_available() to verify commands exist
2. **Handle failures**: Commands may fail, check result["status"]
3. **Review history**: Use get_history() for debugging
4. **Pass context**: Initialize with context for automatic logging

### Hooks

1. **Keep hooks fast**: Hooks should complete in < 5 seconds
2. **Log events**: Use event log for debugging
3. **Handle errors gracefully**: Hook failures shouldn't break agent
4. **Use for notifications**: Good for alerting on completions/errors

## Error Handling

All primitives return structured results with error information:

```python
# Plugin error
result = plugins.call("mcp__nonexistent")
if result["status"] == "error":
    print(f"Plugin error: {result['error']}")

# Command error
result = commands.execute("/nonexistent")
if result["status"] == "error":
    print(f"Command error: {result['error']}")

# Hook error
result = hooks.trigger("invalid-event")
if result["status"] == "error":
    print(f"Hook error: {result['error']}")

# Memory always succeeds (returns default if not found)
value = memory.recall("nonexistent", default="fallback")
```

## File Structure

```
.cursor/
├── agents/sdk/primitives/
│   ├── __init__.py          # Module exports
│   ├── plugins.py           # Plugins integration
│   ├── memory.py            # Memory system
│   ├── commands.py          # Slash commands
│   ├── hooks.py             # Lifecycle hooks
│   └── README.md            # This file
├── memory/
│   └── agent_decisions/
│       └── {agent_name}/
│           └── memory.json  # Agent memories
├── hooks/
│   ├── agent-start.sh       # Start hook
│   ├── agent-complete.sh    # Completion hook
│   └── agent-error.sh       # Error hook
└── commands/
    ├── review-pr.md         # Command definitions
    ├── status.md
    └── ...
```

## Testing

Test each primitive individually:

```python
# test_primitives.py
from .primitives import Plugins, Memory, Commands, Hooks

def test_plugins():
    plugins = Plugins()
    result = plugins.call("mcp__brave_search", query="test")
    assert result["status"] == "success"

def test_memory():
    memory = Memory(agent_name="test-agent")
    memory.store("test_key", "test_value")
    assert memory.recall("test_key") == "test_value"

def test_commands():
    commands = Commands()
    available = commands.list_available()
    assert len(available) > 0

def test_hooks():
    hooks = Hooks(agent_name="test-agent")
    result = hooks.trigger("agent-start", context={"test": "data"})
    assert result["status"] == "success"
```

## Troubleshooting

### Plugins not working

- Check MCP server is running
- Verify plugin name (use list_available())
- Check API keys/credentials

### Memory not persisting

- Verify .cursor/memory/ directory exists
- Check file permissions
- Ensure agent_name is consistent

### Commands not found

- Verify .cursor/commands/ directory exists
- Check command file name matches command name
- Use list_available() to see available commands

### Hooks not triggering

- Verify .cursor/hooks/ directory exists
- Make hook scripts executable (chmod +x)
- Check hook script syntax
- Review hook event log

## Resources

- **Agent SDK Base**: `../.cursor/agents/sdk/base_agent.py`
- **Context System**: `../.cursor/agents/sdk/context.py`
- **Task File**: `.gald3r/tasks/task052_anthropic_agent_sdk_integration.md`
- **Cursor Docs**: https://docs.cursor.com

## Support

For issues or questions:

1. Check this README
2. Review example implementations
3. Check event/execution logs
4. File issue in project repository

---

**Version**: 1.0.0
**Last Updated**: 2025-11-01
**Status**: Production Ready
