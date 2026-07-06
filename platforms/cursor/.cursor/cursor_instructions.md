# Cursor Platform — gald3r Configuration Guide

**Platform**: Cursor IDE (AI-first fork of VSCode)
**Config Folder**: `.cursor/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.cursor.com
**Cursor Version**: 2.5+

---

## Folder Layout

```
.cursor/
├── agents/          # SubAgent definitions — specialized AI assistants
│   ├── g-agnt-*.md  # gald3r agents (g-agnt- prefix)
│   ├── README.md    # Agent index and usage guide
├── commands/        # @-commands — invoked with @g-command-name
│   └── g-*.md
├── hooks/           # PowerShell automation hooks (auto-executed by Cursor)
│   ├── g-hk-session-start.py
│   ├── g-hk-agent-complete.py
│   ├── g-hk-validate-shell.py
│   ├── g-hk-setup-user.py
│   └── state/       # Hook state files (gitignored, machine-specific)
├── rules/           # Always-on AI behavior rules (.mdc format — CURSOR ONLY)
│   └── g-rl-*.mdc
└── skills/          # Reusable knowledge modules (lazy-loaded on relevance)
    └── g-skl-*/
        └── SKILL.md
```

---

## What Makes Cursor Unique

### Rules Use `.mdc` Format (Cursor-Only)
Cursor rules use `.mdc` (Markdown Cursor) files with YAML frontmatter. This is unique to Cursor — no other platform uses this extension. The other platforms (Claude Code, Gemini) use plain `.md` for rules.

```yaml
---
description: "What this rule does"
globs: ["**/*.py"]   # Optional: apply only to matching files
alwaysApply: true    # true = always active; false = loaded when relevant
---
# Rule content here
```

### Commands Use `@` Prefix
In Cursor, commands are invoked with `@`:
```
@g-setup
@g-task-new
@g-code-review
```
All other platforms use `/` prefix.

### Full Hooks Support
Cursor has the most complete hooks implementation. Verified wired events (see `PLATFORM_SPEC.md` §6):
- `sessionStart` — runs when a new Composer conversation begins
- `stop` — runs when the agent loop ends
- `beforeShellExecution` — runs before any shell command (can deny dangerous commands)
- `preToolUse` — runs before matching edit/shell tool calls (gald3r guards, PRD freeze, member guard)

Wiring lives in **`.cursor/hooks.json`** (the repo `.cursor/` root — NOT inside `.cursor/hooks/`).

### SubAgents (`agents/`)
Cursor supports named sub-agents. Each `.md` file in `agents/` defines a specialized assistant with its own tools, model, and focus. Invoke with `@agent-name` in chat.

### MCP Configuration
Cursor's MCP config goes in `.cursor/mcp.json` (not committed — machine-specific):
```json
{
  "mcpServers": {
    "gald3r": { "url": "http://localhost:8092/mcp" }
  }
}
```

---

## gald3r Naming Conventions

| Component | Prefix | Example |
|-----------|--------|---------|
| Agents | `g-agnt-` | `g-agnt-task-manager.md` |
| Skills | `g-skl-` | `g-skl-tasks/SKILL.md` |
| Commands | `g-` | `g-setup.md` |
| Rules | `g-rl-` | `g-rl-33-enforcement_catchall.mdc` |
| Hooks | `g-hk-` | `g-hk-session-start.py` |

---

## SDK Folder

The `agents/sdk/` folder contains an experimental Python agent SDK with base classes, context management, and workflow primitives. This is **not auto-loaded by Cursor** — it's a developer tool for building custom agent integrations programmatically. See `agents/sdk/README.md` for usage.

---

## Hooks Configuration

Hooks are wired in **`.cursor/hooks.json`** (top-level in the `.cursor/` folder). Each entry has a
full `command` invocation, an optional `matcher` regex (over tool names), and an optional `_hook_md`
companion-doc path (T1171). The live file in this scaffold is the source of truth; the snippet below
is illustrative:
```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{"command": "uv run python .cursor/hooks/g-hk-session-start.py", "_hook_md": ".cursor/hooks/g-hk-session-start.md"}],
    "stop": [{"command": "uv run python .cursor/hooks/g-hk-agent-complete.py", "_hook_md": ".cursor/hooks/g-hk-agent-complete.md"}],
    "beforeShellExecution": [{"command": "uv run python .cursor/hooks/g-hk-validate-shell.py", "_hook_md": ".cursor/hooks/g-hk-validate-shell.md"}],
    "preToolUse": [{"matcher": "Edit|Write|MultiEdit|Patch", "command": "uv run python .cursor/hooks/g-hk-pre-tool-call-gald3r-guard.py", "_hook_md": ".cursor/hooks/g-hk-pre-tool-call-gald3r-guard.md"}]
  }
}
```
See `PLATFORM_SPEC.md` §6 for the full verified event/hook table.

---

## Comparison to Other Platforms

| Feature | Cursor | Claude Code | Gemini (.agent) | Codex | OpenCode |
|---------|--------|-------------|-----------------|-------|----------|
| Rules format | `.mdc` | `.md` | `.md` | via AGENTS.md | `.md` |
| Command prefix | `@` | `/` | `/` | via AGENTS.md | `/` |
| Agents folder | ✅ `agents/` | ✅ `agents/` | ❌ uses `workflows/` | ❌ via config.toml | ✅ `agents/` |
| Hooks | ✅ Full | ✅ Full | ✅ Full | ❌ None | ❌ None |
| Skills | ✅ | ✅ | ✅ | ✅ | via AGENTS.md |
| MCP config | `.cursor/mcp.json` | `.claude/settings.json` | `mcp_config.json` | `config.toml` | `opencode.json` |
