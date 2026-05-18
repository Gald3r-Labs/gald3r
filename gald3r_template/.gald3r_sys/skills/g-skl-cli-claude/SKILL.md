---
name: g-skl-cli-claude
description: Claude Code CLI (claude command) — headless flags, session continuation, MCP config, permissions, multi-agent via Agent SDK, and overnight/CI best practices.
---

# g-skl-cli-claude — Claude Code CLI

Reference docs will live in: `{vault_location}/research/platforms/claude-code/` once populated via `@g-ingest-docs`.

## When to Use

- Running Claude headlessly in scripts or CI
- Overnight batch implementation tasks
- Multi-agent orchestration via Claude Agent SDK
- Configuring MCP servers from the terminal

## Core Flags

```bash
claude -p "implement T031 per the task spec"   # Headless (print) mode — non-interactive
claude --model claude-sonnet-4-5               # Override model
claude --output-format json                    # JSON output for scripting
claude --project /path/to/project              # Set project root
claude --max-turns 30                          # Limit agentic loop depth
```

## Session Management

```bash
claude --continue                   # Continue most recent conversation
claude --resume {session-id}        # Resume specific session by ID
```

Session IDs are printed at session start. Use `--output-format json` to capture them in scripts.

## MCP Configuration

```bash
# Use a project-level MCP config
claude --mcp-server "gald3r:node scripts/gald3r-mcp.js"

# MCP config auto-loaded from .claude/mcp.json in project root
```

Claude Code reads `.claude/` directory automatically — settings.json, CLAUDE.md, and mcp.json
are picked up without flags.

## Permissions

```bash
# Standard run — respects all security gates
claude -p "task here"

# Skip permission prompts (ONLY use in trusted, isolated environments)
claude --dangerously-skip-permissions -p "task here"
```

**When `--dangerously-skip-permissions` is safe**:
- Docker container with no credential mounts
- CI VM with ephemeral filesystem
- Isolated sandbox with no network access to prod

**When it is NOT safe**: developer machine, any env with credentials, prod access.

## Multi-Agent (Agent SDK)

Claude can orchestrate sub-agents programmatically:

```python
# Simple orchestration pattern
import anthropic
client = anthropic.Anthropic()

result = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[{"role": "user", "content": "implement X using the task spec"}]
)
```

For parallel sub-agents, each agent should work on independent task files.
Coordinate via `.gald3r/linking/INBOX.md` for cross-agent messaging.

## Overnight / CI Best Practices

- Use `--max-turns` to prevent runaway loops
- Use `--output-format json` to capture session summaries
- Set `ANTHROPIC_API_KEY` in environment (not in source)
- Rate limits: Claude has per-minute and daily token limits; space large batches
- Graceful shutdown: Claude Code handles SIGINT cleanly — use `kill -INT` not `-KILL`

## Config Files (Auto-loaded)

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project context injected at session start |
| `.claude/settings.json` | Hooks, permissions, model preferences |
| `.claude/mcp.json` | MCP server definitions |

## Vault Reference

Once `@g-ingest-docs` is run for `claude-code`, full docs will be at:
`{vault_location}/research/platforms/claude-code/`
