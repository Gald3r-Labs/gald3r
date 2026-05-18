---
name: g-skl-cli-cursor
description: Cursor CLI (agent command) — modes, Cloud Agent handoff, API mode, session management, and multi-agent coordination from the terminal.
---

# g-skl-cli-cursor — Cursor CLI

Reference docs will live in: `{vault_location}/research/platforms/cursor/` once populated via `@g-ingest-docs`.

## When to Use

- Running Cursor agents headlessly (CI, overnight tasks, batch jobs)
- Handing tasks off to Cursor Cloud Agent from the terminal
- Multi-agent workflows without the IDE open
- Debugging why an agent session isn't picking up the right context

## Modes

| Mode | Flag | Use for |
|------|------|---------|
| **Agent** | default | Autonomous implementation — full tool access |
| **Plan** | `--plan` | Read-only planning, no file writes |
| **Ask** | `--ask` | Q&A / exploration, read-only |
| **Debug** | `--debug` | Error investigation, read-only |

```bash
agent "implement the login feature"           # Agent mode (default)
agent --plan "design the auth architecture"   # Plan mode
agent --ask "how does this codebase work?"    # Ask mode
```

## Cloud Agent Handoff

Pass long-running tasks to Cursor Cloud Agent (runs asynchronously):

```bash
agent --cloud "refactor the database layer following CONSTRAINTS.md rules"
```

Cloud Agent runs in a separate VM, reports back via PR or notification.
Best for: tasks >30 min, tasks that require multiple restarts, overnight work.

## API / Non-Interactive Mode

```bash
agent --no-interactive "update all test fixtures"
```

Reads context from project files, executes, exits. No prompts.
Suitable for CI pipeline integration.

## Session Management

```bash
agent --resume {session-id}      # Resume a previous session
agent --max-turns 50             # Limit agent loop iterations
```

Session IDs are shown at session start. Sessions have a TTL (default 24h).

## Multi-Agent Coordination

Cursor agents can spawn sub-agents via task files:
- Create task files in `.gald3r/tasks/` with `ai_safe: true`
- Each sub-agent picks up a task independently
- Coordinate via `.gald3r/linking/INBOX.md` for PCAC messaging

## Limitations vs GUI

- No live file diff preview
- No inline suggestion acceptance
- Hooks (`hooks.json`) still fire — respect them
- Cannot browse the web interactively

## Vault Reference

Once `@g-ingest-docs` is run for `cursor`, full docs will be at:
`{vault_location}/research/platforms/cursor/`
