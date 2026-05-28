# Anthropic Agent SDK - Base Infrastructure

Core SDK infrastructure for Cursor SubAgents with shared context, workflows, and structured agent-to-agent communication.

## Overview

This package provides the foundational classes for building SDK-powered agents:

- **BaseAgent**: Base class all agents inherit from
- **AgentContext**: Shared context for agent collaboration
- **AgentWorkflow**: Orchestrator for multi-agent workflows

## Architecture

```
BaseAgent (Abstract)
├── process() - Agent-specific logic (must implement)
├── run() - Execution wrapper with retries/logging
├── invoke_tool() - Cursor tool invocation
└── State management

AgentContext
├── Shared artifacts (data passing)
├── Agent state tracking
├── JSON serialization
├── Persistence to disk
└── TTL/cleanup

AgentWorkflow
├── run_sequential() - One agent after another
├── run_parallel() - Multiple agents concurrently
├── run_conditional() - Conditional execution
└── Progress tracking
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Create a Custom Agent

```python
from base_agent import BaseAgent
from context import AgentContext

class BackendDeveloper(BaseAgent):
    """Backend development specialist"""

    def __init__(self):
        super().__init__(
            name="backend-developer",
            description="Backend API and server-side logic",
            model="claude-opus-4-5",
            tools=["Read", "Edit", "Write", "Bash", "Grep"],
            enable_memory=True,
            enable_plugins=True,
            enable_hooks=True
        )

    def process(self, context: AgentContext):
        """
        Main agent logic

        Args:
            context: Shared context with task and artifacts

        Returns:
            Agent result dictionary
        """
        # Get task from context
        task = context.get("task")
        database_schema = context.get("database_schema", {})

        # Do backend work
        self.logger.info(f"Implementing backend for: {task}")

        # Example: Read existing code
        # content = self.invoke_tool("Read", file_path="src/api/routes.py")

        # Update context for next agent
        context.set("backend_complete", True)
        context.set("api_endpoints", [
            "/api/auth/login",
            "/api/auth/logout",
            "/api/users"
        ])

        return {
            "status": "completed",
            "endpoints_created": 3,
            "tests_passing": True
        }
```

### 2. Run a Single Agent

```python
from context import AgentContext

# Create context
context = AgentContext(
    task="Build user authentication API",
    priority="high"
)

# Run agent
backend = BackendDeveloper()
result = backend.run(context)

print(f"Status: {result['status']}")
print(f"Endpoints: {context.get('api_endpoints')}")

# Save context
context.save()
```

### 3. Sequential Workflow (3 Agents)

```python
from workflow import AgentWorkflow
from agents import DatabaseExpert, BackendDeveloper, FrontendDeveloper

# Create workflow
workflow = AgentWorkflow()

# Create context
context = workflow.create_context(
    task="Build user authentication system"
)

# Run agents sequentially
result = workflow.run_sequential([
    ("database-expert", DatabaseExpert()),
    ("backend-developer", BackendDeveloper()),
    ("frontend-developer", FrontendDeveloper())
], context)

if result["status"] == "completed":
    print("All agents completed successfully!")
    print(f"Agents run: {result['agents_run']}")
```

### 4. Parallel Workflow (Multiple Services)

```python
# Build 3 microservices in parallel
result = workflow.run_parallel([
    ("auth-service", BackendDeveloper()),
    ("user-service", BackendDeveloper()),
    ("payment-service", BackendDeveloper())
], context)

print(f"Completed: {result['agents_completed']}")
print(f"Failed: {result['agents_failed']}")
```

### 5. Conditional Workflow

```python
def needs_migration(ctx):
    """Only run if database changes detected"""
    return ctx.get("database_changes", False)

def needs_security_audit(ctx):
    """Only run if handling authentication"""
    return ctx.get("handles_authentication", False)

result = workflow.run_conditional([
    ("backend-developer", BackendDeveloper(), None),  # Always runs
    ("database-expert", DatabaseExpert(), needs_migration),  # Conditional
    ("security-auditor", SecurityAuditor(), needs_security_audit),  # Conditional
    ("test-runner", TestRunner(), None)  # Always runs
], context)
```

## API Reference

### BaseAgent

**Constructor Parameters:**
- `name` (str): Agent identifier (e.g., "backend-developer")
- `description` (str): Brief description of agent purpose
- `model` (str): Claude model (default: "claude-opus-4-5")
- `tools` (List[str]): Cursor tools (e.g., ["Read", "Write", "Bash"])
- `enable_memory` (bool): Enable Memory system access
- `enable_plugins` (bool): Enable Plugin invocation
- `enable_hooks` (bool): Enable lifecycle hooks
- `max_retries` (int): Maximum retry attempts (default: 3)
- `timeout` (int): Execution timeout in seconds (default: 300)

**Methods:**
- `process(context) -> Dict`: Main agent logic (abstract, must implement)
- `run(context) -> Dict`: Execute agent with error handling/retries
- `invoke_tool(tool_name, **kwargs) -> Any`: Invoke Cursor tool
- `get_context_value(context, key, default) -> Any`: Safely get from context
- `set_context_value(context, key, value)`: Safely set in context

**Agent State:**
```python
{
    "status": "initialized" | "running" | "completed" | "failed",
    "started_at": "2025-11-01T12:00:00Z",
    "completed_at": "2025-11-01T12:05:00Z",
    "error": None | "error message",
    "retry_count": 0
}
```

### AgentContext

**Constructor Parameters:**
- `task` (str): Task description
- `workflow_id` (str): Unique workflow ID (auto-generated)
- `user_id` (str): User who initiated workflow
- `project_path` (str): Absolute project path
- `priority` (str): "low" | "medium" | "high" | "critical"
- `ttl_hours` (int): Time-to-live in hours (default: 24)
- `initial_data` (Dict): Initial shared artifacts

**Methods:**
- `get(key, default=None) -> Any`: Get value from shared artifacts
- `set(key, value)`: Set value in shared artifacts
- `update(data: Dict)`: Update multiple values
- `delete(key)`: Delete key from artifacts
- `get_agent_state(agent_name) -> Dict`: Get specific agent state
- `set_agent_state(agent_name, state: Dict)`: Set agent state
- `add_hook_event(event: Dict)`: Log hook event
- `add_fallback(agent, reason, fallback_to)`: Log SDK → prompt-based fallback
- `to_dict() -> Dict`: Convert to dictionary
- `to_json(indent=2) -> str`: Convert to JSON string
- `from_dict(data) -> AgentContext`: Create from dictionary (classmethod)
- `from_json(json_str) -> AgentContext`: Create from JSON (classmethod)
- `save(context_dir=None) -> Path`: Save to disk
- `load(workflow_id, context_dir=None) -> AgentContext`: Load from disk (classmethod)
- `archive() -> Path`: Archive completed context
- `is_expired() -> bool`: Check if TTL exceeded
- `cleanup_expired(context_dir=None)`: Clean up expired contexts (classmethod)

**Context Structure:**
```python
{
    "metadata": {
        "workflow_id": "uuid",
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp",
        "version": 1,
        "ttl_hours": 24,
        "user_id": "user123",
        "project_path": "/path/to/project",
        "priority": "high"
    },
    "task": "Task description",
    "phase": "planning" | "implementation" | "testing" | ...,
    "agents_completed": ["agent1", "agent2", ...],
    "current_agent": "agent3",
    "shared_artifacts": {
        "database_schema": {...},
        "api_endpoints": [...],
        "implementation_files": [...],
        # Agent-specific data
    },
    "agent_states": {
        "agent1": {"status": "completed", ...},
        "agent2": {"status": "running", ...}
    },
    "hook_events": [
        {"event": "agent-start", "agent": "agent1", "timestamp": "..."},
        {"event": "agent-complete", "agent": "agent1", "timestamp": "..."}
    ],
    "fallback_log": [
        {"agent": "agent2", "reason": "SDK timeout", "fallback_to": "prompt-based"}
    ]
}
```

### AgentWorkflow

**Constructor Parameters:**
- `max_parallel_agents` (int): Maximum parallel agents (default: 5)
- `enable_progress_tracking` (bool): Enable progress logging (default: True)

**Methods:**
- `create_context(task, **kwargs) -> AgentContext`: Create new workflow context
- `load_context(workflow_id) -> AgentContext`: Load existing context
- `run_sequential(agents: List[Tuple], context) -> Dict`: Sequential execution
- `run_parallel(agents: List[Tuple], context) -> Dict`: Parallel execution
- `run_conditional(agents: List[Tuple], context) -> Dict`: Conditional execution
- `get_workflow_status(workflow_id) -> Dict`: Get workflow status
- `cancel_workflow(workflow_id)`: Cancel active workflow
- `archive_workflow(workflow_id)`: Archive completed workflow
- `cleanup_expired_workflows()`: Clean up expired workflows

**Workflow Result:**
```python
{
    "status": "completed" | "partial" | "failed",
    "agents_run": ["agent1", "agent2", ...],
    "agents_completed": ["agent1", "agent2"],  # Parallel only
    "agents_failed": ["agent3"],  # Parallel only
    "agents_skipped": ["agent4"],  # Conditional only
    "results": {
        "agent1": {"status": "completed", ...},
        "agent2": {"status": "completed", ...}
    },
    "error": "error message" | None
}
```

## Context Persistence

Contexts are automatically saved to disk:

```
.cursor/
└── agent_context/
    ├── active/           # Active workflow contexts
    │   └── {workflow_id}.json
    └── archived/         # Completed/expired contexts
        └── {workflow_id}.json
```

Load a context later:
```python
context = AgentContext.load("550e8400-e29b-41d4-a716-446655440000")
```

## Error Handling

Agents automatically retry on failure:

```python
# Agent will retry up to 3 times with exponential backoff
backend = BackendDeveloper()
backend.max_retries = 3  # Override default

try:
    result = backend.run(context)
except RuntimeError as e:
    print(f"Agent failed after {backend.state['retry_count']} attempts: {e}")
```

## Logging

Logs are written to:
- `.cursor/logs/agents/{agent_name}.log` - Agent-specific logs
- `.cursor/logs/workflows/workflow.log` - Workflow orchestration logs

```python
# Access agent logger
self.logger.info("Starting backend implementation")
self.logger.debug(f"Database schema: {schema}")
self.logger.error(f"Failed to create endpoint: {e}")
```

## Examples

See the `/examples` directory for complete working examples:

- `examples/01_single_agent.py` - Run a single agent
- `examples/02_sequential_workflow.py` - Database → Backend → Frontend
- `examples/03_parallel_workflow.py` - Multiple microservices
- `examples/04_conditional_workflow.py` - Conditional agent execution
- `examples/05_context_persistence.py` - Save/load contexts
- `examples/06_custom_agent.py` - Build your own agent

## Best Practices

### 1. Keep Context Minimal
Only store data that other agents need. Don't bloat the context with internal implementation details.

```python
# Good
context.set("api_endpoints", ["/api/users", "/api/auth"])

# Bad
context.set("entire_source_code", "... 10,000 lines ...")
```

### 2. Use Meaningful Keys
Use clear, descriptive keys for shared artifacts.

```python
# Good
context.set("database_schema", schema)
context.set("api_endpoints", endpoints)
context.set("backend_complete", True)

# Bad
context.set("data", schema)
context.set("stuff", endpoints)
context.set("done", True)
```

### 3. Check Context Before Use
Always check if required data exists in context.

```python
def process(self, context):
    database_schema = context.get("database_schema")

    if not database_schema:
        return {
            "status": "failed",
            "error": "Database schema not found. Run database-expert first."
        }

    # Continue with implementation...
```

### 4. Return Structured Results
Return consistent result dictionaries from agents.

```python
def process(self, context):
    # ... implementation

    return {
        "status": "completed",  # Required
        "artifacts": {...},     # What you created
        "next_agent": "frontend-developer",  # Optional routing
        "metadata": {...}       # Additional info
    }
```

### 5. Use Hooks for Side Effects
Use hooks for logging, notifications, metrics, etc.

```python
backend = BackendDeveloper()
backend.enable_hooks = True

# Hooks will automatically trigger:
# - agent-start: When agent begins
# - agent-complete: When agent succeeds
# - agent-error: When agent fails
```

## Troubleshooting

### Context Not Found
```python
try:
    context = AgentContext.load("workflow-id")
except FileNotFoundError:
    print("Context not found. May have been archived or expired.")
```

### Agent Fails Silently
Check agent logs:
```bash
cat .cursor/logs/agents/backend-developer.log
```

### Workflow Hangs
Set shorter timeout:
```python
backend = BackendDeveloper()
backend.timeout = 60  # 60 seconds
```

### Context Too Large
Check context size and clean up unnecessary data:
```python
context_json = context.to_json()
print(f"Context size: {len(context_json)} bytes")

# Remove large artifacts
context.delete("large_dataset")
```

## Next Steps

1. **Implement Custom Agents**: Create agents for your specific needs
2. **Build Workflows**: Combine agents into powerful workflows
3. **Integrate Primitives**: Add Memory, Plugins, Commands, Hooks
4. **Test Multi-Agent**: Test 5+ agent workflows for reliability
5. **Benchmark Performance**: Compare SDK vs prompt-based agents

## Related Documentation

- **Task 052**: Full task specification in `.gald3r/tasks/task052_anthropic_agent_sdk_integration.md`
- **SubAgents Guide**: `docs/CLAUDE_SUBAGENTS_GUIDE.md`
- **Fallback Handler**: `.cursor/agents/sdk/fallback.py` (to be implemented)
- **Primitives Integration**: `.cursor/agents/sdk/primitives/` (to be implemented)

## Version

**Version**: 0.1.0
**Status**: Base Infrastructure Complete
**Date**: 2025-11-01

---

**Part of Task 052: Anthropic Agent SDK Integration**
