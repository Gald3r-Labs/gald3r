# Cursor Primitives - Quick Reference

One-page reference for SDK agents using primitives.

## Import

```python
from .primitives import Plugins, Memory, Commands, Hooks
```

## Plugins

```python
# Initialize
plugins = Plugins()
plugins_with_context = Plugins(context=agent_context)

# Call a plugin
result = plugins.call("mcp__brave_search", query="FastAPI auth", max_results=5)
# result = {"status": "success", "plugin": "...", "data": {...}}

# List available
available = plugins.list_available()
# ["mcp__brave_search", "mcp__github", ...]

# Get log
log = plugins.get_invocation_log()
```

**Common Plugins**: `mcp__brave_search`, `mcp__github`, `mcp__postgres`, `mcp__fetch`

## Memory

```python
# Initialize (per agent)
memory = Memory(agent_name="backend-developer")

# Store
memory.store("database_preference", "PostgreSQL",
            metadata={"source": "user", "confidence": 0.95})

# Recall
db = memory.recall("database_preference")
db = memory.recall("missing_key", default="MySQL")  # with default

# Search
results = memory.search("authentication")

# List all
all_memories = memory.list_all()

# Delete
memory.delete("old_key")

# Stats
stats = memory.get_stats()
```

**Storage**: `.cursor/memory/agent_decisions/{agent_name}/memory.json`

## Commands

```python
# Initialize
commands = Commands()
commands_with_context = Commands(context=agent_context)

# Execute
result = commands.execute("/review-pr", pr_number=123)
# result = {"status": "success", "command": "...", "output": "..."}

# Execute without args
result = commands.execute("/status")

# List available
available = commands.list_available()
# [{"name": "review-pr", "file": "...", "description": "..."}]

# Get history
history = commands.get_history()
```

**Common Commands**: `@g-code-review`, `@g-status`, `@g-task-new`, `@g-git-commit`

## Hooks

```python
# Initialize (per agent)
hooks = Hooks(agent_name="backend-developer")

# Trigger events
hooks.trigger("agent-start", context={"task": "Build API"})

hooks.trigger("agent-complete",
             context={"task": "Build API"},
             result={"status": "success", "files_created": 5})

hooks.trigger("agent-error",
             context={"task": "Build API"},
             error="Database connection failed")

# Get event log
log = hooks.get_event_log()

# Create hook templates
hooks.create_hook_template("agent-start")
```

**Events**: `agent-start`, `agent-complete`, `agent-error`
**Hook Scripts**: `.cursor/hooks/{event}.sh`

## Complete Agent Example

```python
from ..base_agent import BaseAgent
from ..primitives import Plugins, Memory, Commands, Hooks

class BackendDeveloper(BaseAgent):
    def __init__(self):
        super().__init__(name="backend-developer")

        # Initialize primitives
        self.memory = Memory(agent_name=self.name)
        self.plugins = Plugins()
        self.commands = Commands()
        self.hooks = Hooks(agent_name=self.name)

    def process(self, context):
        # Start hook
        self.hooks.trigger("agent-start", context=context)

        try:
            # Check preferences
            db = self.memory.recall("database_preference", default="PostgreSQL")

            # Research examples
            if context.get("search_examples"):
                results = self.plugins.call("mcp__brave_search",
                                          query=f"{context['task']} examples")
                context.set("examples", results["data"])

            # Implement feature
            result = self._implement(context, database=db)

            # Run tests
            test_result = self.commands.execute("/run-tests", suite="backend")

            if test_result["status"] == "success":
                # Remember success
                self.memory.store("last_success", {
                    "task": context.get("task"),
                    "approach": result.approach
                })

                # Complete hook
                self.hooks.trigger("agent-complete",
                                 context=context,
                                 result=result)

                return {"status": "completed", "tests_passing": True}

        except Exception as e:
            # Error hook
            self.hooks.trigger("agent-error", context=context, error=str(e))
            raise
```

## Error Handling

All primitives return structured results:

```python
result = plugins.call("mcp__nonexistent")
if result["status"] == "error":
    print(f"Error: {result['error']}")

result = commands.execute("/nonexistent")
if result["status"] == "error":
    print(f"Error: {result['error']}")

result = hooks.trigger("invalid-event")
if result["status"] == "error":
    print(f"Error: {result['error']}")

# Memory uses defaults
value = memory.recall("nonexistent", default="fallback")
```

## Best Practices

### Memory
- Use descriptive keys: `database_preference`, not `db`
- Add metadata for important decisions
- Namespace by agent automatically handled
- Clean up old memories periodically

### Plugins
- Check result status before using data
- Use with context for automatic logging
- Clear cache when needed: `plugins.clear_cache()`
- List available before calling

### Commands
- Verify command exists: `commands.list_available()`
- Check execution status
- Use history for debugging: `commands.get_history()`
- Pass context for automatic logging

### Hooks
- Keep hook scripts fast (< 5 seconds)
- Always trigger start/complete/error
- Use event log for debugging
- Handle hook failures gracefully

## Files & Directories

```
.cursor/agents/sdk/primitives/
├── plugins.py              # Plugins primitive
├── memory.py               # Memory primitive
├── commands.py             # Commands primitive
├── hooks.py                # Hooks primitive
└── README.md               # Full documentation

.cursor/memory/
└── agent_decisions/
    └── {agent_name}/
        └── memory.json     # Persistent memories

.cursor/hooks/
├── agent-start.sh          # Start hook
├── agent-complete.sh       # Completion hook
└── agent-error.sh          # Error hook

.cursor/commands/
└── *.md                    # Command definitions
```

## Quick Troubleshooting

**Plugins not working?**
- Check MCP server is running
- Verify plugin name with `list_available()`

**Memory not persisting?**
- Check `.cursor/memory/agent_decisions/` exists
- Verify file permissions

**Commands not found?**
- Verify `.cursor/commands/` contains command files
- Use `list_available()` to check

**Hooks not executing?**
- Verify `.cursor/hooks/` contains scripts
- Check scripts are executable (`chmod +x`)
- Review event log with `get_event_log()`

## More Information

- **Full Documentation**: `README.md`
- **Examples**: `examples_*.py` files
- **Tests**: `test_primitives.py`
- **Task**: `.gald3r/tasks/task052_anthropic_agent_sdk_integration.md`
