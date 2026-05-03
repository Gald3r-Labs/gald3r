# Context Storage and Persistence System

**Part of Task 052: Anthropic Agent SDK Integration**

This system provides unified context management for hybrid agent workflows, supporting both SDK-based and prompt-based agents.

## Architecture Overview

```
.claude/agent_context/
├── sdk/              # SDK Context objects (future)
├── json/             # JSON files (current storage)
├── active/           # Active workflows (symlinks)
└── archived/         # Completed workflows
```

## Components

### 1. Context Schema (`schema.py`)

Pydantic models defining the context structure:

- **AgentContext**: Main context object with workflow state
- **AgentState**: Individual agent execution state
- **SharedArtifacts**: Artifacts shared between agents
- **MemoryContext**: Memory system integration
- **WorkflowMetadata**: Workflow metadata and TTL settings

**Key Features**:
- ✅ Strongly typed with Pydantic validation
- ✅ JSON-safe serialization for prompt-based agents
- ✅ Support for SDK and prompt-based agent modes
- ✅ Hook events, command executions, fallback tracking
- ✅ Memory system integration
- ✅ Plugin results storage

### 2. Context Manager (`manager.py`)

Handles context lifecycle operations:

- **Create**: `create_context()` - Create new workflow context
- **Save**: `save_context()` - Persist context to disk
- **Load**: `load_context()` - Load context by workflow ID
- **Archive**: `archive_context()` - Move completed workflows to archive
- **Cleanup**: `cleanup_expired()` - Remove contexts exceeding TTL
- **Search**: `search_contexts()` - Query contexts with filters
- **Stats**: `get_context_stats()` - Storage statistics

**Key Features**:
- ✅ Automatic TTL-based cleanup (default 72 hours)
- ✅ Active workflow tracking via symlinks
- ✅ Archiving completed workflows
- ✅ Flexible search and filtering
- ✅ Storage statistics and monitoring

### 3. Context Adapter (`../prompt-based/context_adapter.py`)

Bridges SDK and prompt-based agents:

- **to_json()**: Convert SDK context to JSON file
- **from_json()**: Load context from JSON
- **update_context()**: Update context with agent results
- **from_text()**: Parse text output into structured data
- **create_context_summary()**: Human-readable context summary

**Key Features**:
- ✅ Bidirectional SDK ↔ JSON conversion
- ✅ Text parsing with smart extraction (files, status, tests)
- ✅ JSON block detection in agent output
- ✅ Simplified context updates for prompt agents

### 4. Context Utilities (`utils.py`)

Helper functions for context operations:

- **validate_context()**: Check for common issues
- **merge_contexts()**: Merge parallel workflow contexts
- **analyze_context_performance()**: Performance metrics
- **export_context_report()**: Generate markdown reports
- **cleanup_old_contexts()**: Bulk cleanup utility

**Key Features**:
- ✅ Context validation with issue detection
- ✅ Performance analysis and efficiency scoring
- ✅ Report generation for workflow review
- ✅ Batch cleanup operations

## Usage Examples

### Example 1: Create and Save Context

```python
from .cursor.agents.sdk.context import ContextManager, AgentMode

# Initialize manager
manager = ContextManager()

# Create new context
context = manager.create_context(
    task="Implement user authentication system",
    project_path="/mnt/c/git/myproject",
    priority="high",
    workflow_type="fullstack_feature",
    tags=["auth", "security"],
    ttl_hours=72  # 3 days
)

print(f"Created workflow: {context.workflow_id}")
```

### Example 2: SDK Agent Using Context

```python
from .cursor.agents.sdk.context import ContextManager

# Load existing context
manager = ContextManager()
context = manager.load_context("550e8400-e29b-41d4-a716-446655440000")

# Mark agent started
context.mark_agent_started("backend-developer", agent_type=AgentMode.SDK)

# Update agent state
state = context.get_agent_state("backend-developer")
state.files_created = ["src/auth/login.ts", "src/auth/logout.ts"]
state.plugins_called = ["mcp__brave_search"]
state.tests_passing = True

# Update shared artifacts
context.shared_artifacts.api_endpoints = [
    {"path": "/api/auth/login", "method": "POST"},
    {"path": "/api/auth/logout", "method": "POST"}
]

# Mark completed
context.mark_agent_completed("backend-developer")

# Save updates
manager.save_context(context)
```

### Example 3: Prompt-Based Agent Using Context

```python
from .cursor.agents.prompt_based.context_adapter import ContextAdapter

# Initialize adapter
adapter = ContextAdapter()

# Load context for prompt agent
workflow_id = "550e8400-e29b-41d4-a716-446655440000"
context_data = adapter.from_json(workflow_id)

# Show summary to prompt agent
summary = adapter.create_context_summary(workflow_id)
print(summary)

# Agent does work...

# Parse agent's text output
agent_output = """
✅ Backend implementation complete

Files Created:
- src/api/users.ts
- src/models/user.ts

Tests: 25 tests passed
"""

result = adapter.from_text(agent_output)

# Update context with results
adapter.update_context(
    workflow_id,
    "backend-developer",
    {
        "status": "completed",
        "files_created": result["files_created"],
        "tests_passing": result["tests_passing"]
    }
)
```

### Example 4: Context Cleanup and Archiving

```python
from .cursor.agents.sdk.context import ContextManager

manager = ContextManager()

# Archive completed workflow
manager.archive_context("550e8400-e29b-41d4-a716-446655440000")

# Cleanup expired contexts (dry run first)
expired_ids = manager.cleanup_expired(dry_run=True)
print(f"Found {len(expired_ids)} expired contexts")

# Actually cleanup
manager.cleanup_expired(dry_run=False)

# Get storage stats
stats = manager.get_context_stats()
print(f"Active: {stats['active_contexts']}")
print(f"Archived: {stats['archived_contexts']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

### Example 5: Performance Analysis

```python
from .cursor.agents.sdk.context import ContextManager
from .cursor.agents.sdk.context.utils import analyze_context_performance, export_context_report

manager = ContextManager()
context = manager.load_context("550e8400-e29b-41d4-a716-446655440000")

# Analyze performance
metrics = analyze_context_performance(context)
print(f"Efficiency Score: {metrics['efficiency_score']:.1f}/100")
print(f"Total Duration: {metrics['total_duration_seconds']:.1f}s")
print(f"Files Created: {metrics['total_files_created']}")
print(f"Plugins Used: {metrics['plugins_used']}")

# Export report
export_context_report(
    context,
    f".claude/agent_context/reports/{context.workflow_id}.md"
)
```

### Example 6: Search and Query

```python
from .cursor.agents.sdk.context import ContextManager

manager = ContextManager()

# Search by task keywords
contexts = manager.search_contexts(
    task_query="authentication",
    priority="high",
    status="completed",
    limit=10
)

for ctx in contexts:
    print(f"{ctx.workflow_id}: {ctx.task}")
    print(f"  Duration: {(ctx.completed_at - ctx.started_at).total_seconds():.1f}s")
    print(f"  Agents: {len(ctx.agents_completed)}")

# List active workflows
active = manager.list_active_contexts()
print(f"\nActive workflows: {len(active)}")

# List archived by type
archived = manager.list_archived_contexts(
    workflow_type="fullstack_feature",
    since=datetime.utcnow() - timedelta(days=7),
    limit=20
)
print(f"Recent fullstack features: {len(archived)}")
```

## Context Schema Structure

### Full Context Example

```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-01T12:00:00Z",
  "updated_at": "2025-11-01T12:30:00Z",
  "completed_at": "2025-11-01T12:30:00Z",

  "task": "Implement user authentication system",
  "phase": "completed",
  "agent_mode": "hybrid",

  "agents_completed": ["database-expert", "backend-developer", "frontend-developer"],
  "current_agent": null,
  "next_agent": null,

  "shared_artifacts": {
    "database_schema": {
      "tables": ["users", "sessions", "tokens"],
      "migrations": ["001_create_users.sql"]
    },
    "api_endpoints": [
      {"path": "/api/auth/login", "method": "POST", "file": "src/auth/login.ts"},
      {"path": "/api/auth/logout", "method": "POST", "file": "src/auth/logout.ts"}
    ],
    "implementation_files": ["src/auth/login.ts", "src/auth/logout.ts"],
    "plugin_results": {
      "brave_search": {"query": "auth best practices", "results": [...]}
    }
  },

  "agent_states": {
    "backend-developer": {
      "status": "completed",
      "agent_type": "sdk",
      "started_at": "2025-11-01T12:10:00Z",
      "completed_at": "2025-11-01T12:20:00Z",
      "files_created": ["src/auth/login.ts", "src/auth/logout.ts"],
      "tests_passing": true,
      "plugins_called": ["mcp__brave_search"],
      "memory_accessed": ["database_preference"]
    }
  },

  "memory_context": {
    "user_preferences": {
      "database_preference": "PostgreSQL",
      "test_framework": "pytest"
    }
  },

  "hook_events": [
    {"event": "agent-start", "agent": "backend-developer", "timestamp": "2025-11-01T12:10:00Z"},
    {"event": "agent-complete", "agent": "backend-developer", "timestamp": "2025-11-01T12:20:00Z"}
  ],

  "commands_executed": [
    {"/review-pr": {"pr_number": 123, "result": "approved"}}
  ],

  "fallback_log": [],

  "metadata": {
    "project_path": "/mnt/c/git/myproject",
    "priority": "high",
    "workflow_type": "fullstack_feature",
    "tags": ["auth", "security"],
    "ttl_hours": 72,
    "archived": false
  },

  "version": 1
}
```

## TTL and Archiving Strategy

### Default TTL Settings

- **Active Workflows**: 72 hours (3 days)
- **Completed Workflows**: Auto-archived immediately
- **Archived Workflows**: Kept indefinitely (manual cleanup)

### Lifecycle Flow

```
1. Create Context
   ↓
2. Active Workflow (in .claude/agent_context/json/)
   ↓
3. Complete Workflow
   ↓
4. Auto-Archive (move to .claude/agent_context/archived/)
   ↓
5. [Optional] Manual Cleanup After 30+ Days
```

### Cleanup Recommendations

Run cleanup weekly:

```bash
# Dry run first
python -m cursor.agents.sdk.context.manager cleanup --dry-run

# Archive expired contexts (>72 hours)
python -m cursor.agents.sdk.context.manager cleanup

# Delete old archived contexts (>30 days)
python -m cursor.agents.sdk.context.manager delete-old --days 30
```

## Storage Best Practices

### Do ✅

- Set appropriate TTL based on project duration
- Archive completed workflows immediately
- Run cleanup regularly to prevent storage bloat
- Use tags for easy filtering and search
- Export important workflows as reports before cleanup
- Monitor storage stats periodically

### Don't ❌

- Store large binary data in context (use file paths instead)
- Keep contexts indefinitely without archiving
- Ignore validation warnings
- Delete contexts without archiving first
- Store sensitive data (API keys, passwords) in context
- Manually edit context JSON files (use manager API)

## Performance Considerations

### Storage Overhead

- Average context size: 5-50 KB
- 1000 contexts ≈ 5-50 MB
- Indexing: Symlinks for active workflows (O(1) lookup)

### Optimization Tips

1. **Limit artifact size**: Store file paths, not file contents
2. **Use custom data sparingly**: Keep agent-specific data minimal
3. **Archive aggressively**: Move completed workflows immediately
4. **Clean up regularly**: Remove contexts > 30 days old
5. **Use search filters**: Narrow results before loading contexts

## Integration with Other Systems

### Memory System

Context automatically integrates with Claude Code Memory:

```python
# Memory preferences are accessible in context
db_pref = context.memory_context.user_preferences.get("database_preference")

# Agents can store learnings
context.memory_context.agent_learnings["auth_pattern"] = {
    "pattern": "JWT with refresh tokens",
    "success": True
}
```

### Hooks System

Hook events are automatically logged:

```python
# Hooks triggered by agents are recorded
context.add_hook_event("agent-start", "backend-developer", success=True)

# Query hook history
start_events = [e for e in context.hook_events if e.event == "agent-start"]
```

### Plugin Results

Plugin calls are tracked and results stored:

```python
# Store plugin results in shared artifacts
context.shared_artifacts.plugin_results["brave_search"] = {
    "query": "authentication patterns",
    "results": search_results
}

# Other agents can access plugin results
cached_results = context.shared_artifacts.plugin_results.get("brave_search")
```

## Troubleshooting

### Issue: Context Not Found

```python
context = manager.load_context(workflow_id)
if not context:
    # Check all directories
    print(f"Searched in:")
    print(f"  - {manager.json_dir}")
    print(f"  - {manager.active_dir}")
    print(f"  - {manager.archived_dir}")
```

### Issue: Context Expired Prematurely

```python
# Extend TTL
context.metadata.ttl_hours = 168  # 7 days
manager.save_context(context)
```

### Issue: Validation Errors

```python
from cursor.agents.sdk.context.utils import validate_context

issues = validate_context(context)
for issue in issues:
    print(f"⚠️ {issue}")
```

### Issue: Storage Full

```python
# Get stats
stats = manager.get_context_stats()
print(f"Total size: {stats['total_size_mb']} MB")

# Cleanup aggressively
manager.cleanup_expired(dry_run=False)

# Delete old archived contexts
from cursor.agents.sdk.context.utils import cleanup_old_contexts
deleted = cleanup_old_contexts(days_old=30, dry_run=False)
print(f"Deleted {len(deleted)} old contexts")
```

## Testing

Run tests:

```bash
# Test schema
python .claude/agents/sdk/context/schema.py

# Test manager
python .claude/agents/sdk/context/manager.py

# Test adapter
python .claude/agents/prompt-based/context_adapter.py

# Test utilities
python .claude/agents/sdk/context/utils.py
```

## API Reference

See inline documentation in source files:

- `schema.py`: Context models and validation
- `manager.py`: Context lifecycle management
- `context_adapter.py`: Prompt-based agent bridge
- `utils.py`: Helper functions and analysis

## Version History

- **v1.0.0** (2025-11-01): Initial implementation
  - Context schema with Pydantic validation
  - Context manager with CRUD operations
  - Context adapter for prompt-based agents
  - TTL and archiving system
  - Performance analysis utilities

---

**Author**: Database Expert Agent
**Task**: 052 - Anthropic Agent SDK Integration
**Date**: 2025-11-01
