---
name: g-skl-memory
description: >
  Capture structured insights, session summaries, and search cross-session agent memory
  via gald3r_valhalla MCP tools. Dual-mode: degrades to file-based g-skl-learn when
  backend is unavailable. Full semantic search requires Docker backend (adv tier).
version: 1.0.0
min_tier: adv
triggers:
  - "capture insight"
  - "remember this"
  - "store memory"
  - "search memory"
  - "what did we decide"
  - "cross-session memory"
  - "capture session"
  - "memory search"
  - g-memory
requires:
  - gald3r_valhalla MCP server (Docker backend) for full semantic search
  - memory_capture_insight MCP tool
  - memory_capture_session MCP tool
  - memory_search MCP tool
  - memory_search_combined MCP tool
fallback:
  - g-skl-learn (file-based insight capture when backend unavailable)
---

# g-skl-memory

**Full capability**: requires gald3r_valhalla Docker backend.
**Degraded mode**: when backend unavailable, use `g-skl-learn` for file-based insight capture.

**Activate for**: Capturing important decisions mid-session, storing how-to procedures, searching what was decided in past sessions, end-of-session summaries.

---

## Dual-Mode Behavior

| Operation | Backend Available | Backend Unavailable |
|---|---|---|
| Capture insight | `memory_capture_insight` → PostgreSQL | `g-skl-learn` → `.gald3r/learned-facts.md` |
| Capture session | `memory_capture_session` → PostgreSQL | Manual CLAUDE.md/AGENTS.md update |
| Search memory | `memory_search` (semantic vector search) | `Grep` on `.gald3r/learned-facts.md` |
| Combined search | `memory_search_combined` (turns + captures) | File grep only |

---

## Operations

### CAPTURE INSIGHT — Store a specific learning

Use `memory_capture_insight` when you learn something worth preserving across sessions.

**Best for**:
- User preferences (code style, naming, formatting)
- Procedures (how to deploy, test patterns, git flow)
- Corrections (mistakes to avoid)
- Architectural decisions + rationale
- Project context that took effort to establish

```
memory_capture_insight(
  insight="Always use `uv run` instead of `python` in this project. The venv is managed by UV.",
  category="procedure",
  topic="python-venv",
  project_id="<from .gald3r/.project_id>",
  project_path="G:/path/to/project",
  scope="project",
  platform="cursor"
)
```

**Parameters**:
| Param | Required | Description |
|---|---|---|
| `insight` | ✅ | 1-4 sentences, specific and actionable |
| `category` | ✅ | `procedure` \| `preference` \| `correction` \| `decision` \| `context` \| `general` |
| `topic` | recommended | Short label — reusing same topic **updates** rather than duplicates |
| `project_id` | recommended | From `.gald3r/.project_id` |
| `project_path` | recommended | Absolute project root path |
| `scope` | optional | `project` \| `user` \| `session` \| `global` (default: project) |
| `platform` | optional | `cursor` \| `claude_code` \| `antigravity` \| `vscode` |

**Dedup behavior**: Same `topic` → updates existing insight with diff tracking instead of creating a duplicate.

---

### CAPTURE SESSION — End-of-session summary

Use at the end of every session on platforms without automatic hooks (Gemini, VS Code).

```
memory_capture_session(
  summary="Implemented tier-sync script fixes for .copilot and .github directories. Stubbed all deprecated harvest/ingest skills across 15 targets.",
  project_path="G:/path/to/project",
  project_id="<from .gald3r/.project_id>",
  platform="cursor",
  key_decisions="File-level sync replaces dir-level for .copilot/.github to prevent skip-if-exists bug",
  files_changed="scripts/tier_sync.ps1, gald3r_template_full/.copilot/commands/*, gald3r_template_adv/.copilot/commands/*"
)
```

---

### SEARCH — Find past decisions and context

```
memory_search(
  query="how did we set up the Oracle connection pooling",
  project_id="<project_id>",
  limit=5
)
```

```
memory_search_combined(
  query="tier sync script fixes",
  project_id="<project_id>",
  limit=8
)
```

**`memory_search`**: searches `agent_memory_captures` (active captures + insights)
**`memory_search_combined`**: searches both `agent_turns` (passive file-based) AND `agent_memory_captures` — broader but slower

**Parameters**:
| Param | Description |
|---|---|
| `query` | Natural language question |
| `project_id` | Filter to project (optional — searches all if omitted) |
| `platform` | Filter by IDE platform (optional) |
| `user_id` | Filter by user (optional) |
| `limit` | Max results 1-20 (default: 5) |

---

### SESSION CONTEXT — Load memory at session start

Use `memory_context` to get a token-budgeted context block at session start (rule g-rl-25 triggers this automatically for Cursor):

```
memory_context(
  project_id="<project_id>",
  max_tokens=2000
)
```

---

## When to Call (Best Practices)

| Trigger | Action |
|---|---|
| Learn user preference mid-session | `memory_capture_insight(category="preference", ...)` |
| Establish a new procedure | `memory_capture_insight(category="procedure", ...)` |
| Make architectural decision | `memory_capture_insight(category="decision", ...)` |
| Correct a repeated mistake | `memory_capture_insight(category="correction", ...)` |
| End of session (Gemini/VS Code) | `memory_capture_session(summary=..., ...)` |
| Session start — load context | `memory_context(project_id=...)` |
| "What did we decide about X?" | `memory_search(query="...")` |

---

## File-Based Fallback (no backend)

When gald3r_valhalla is unavailable, use `g-skl-learn` instead:
- Insights written to `.gald3r/learned-facts.md` as bullet points
- Searchable via `Grep` on that file
- Format: `- **[topic]**: insight text _(YYYY-MM-DD)_`
- Session summaries written to `CLAUDE.md` / `AGENTS.md` Learned Workspace Facts sections

---

## Availability Check

```
gald3r_server_status()
```
If unavailable → fall back to `g-skl-learn` for captures, `Grep` for search.
