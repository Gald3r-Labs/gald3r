# Claude Code Platform — gald3r Configuration Guide

**Platform**: Claude Code (Anthropic's CLI + VSCode extension)
**Config Folder**: `.claude/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.anthropic.com/en/docs/claude-code
**Invocation**: `claude` CLI or VSCode extension

---

## Folder Layout

```
.claude/
├── CLAUDE.md        # Project-level Claude instructions (auto-loaded every session)
├── settings.json    # MCP servers, permissions, env vars (shared)
├── local.settings.json  # Machine-specific overrides (gitignored)
├── hooks.json       # Hook event configuration
├── agents/          # SubAgent definitions
│   ├── g-agnt-*.md  # gald3r agents (g-agnt- prefix)
│   ├── README.md    # Agent index
│   └── sdk/         # Python agent SDK (experimental, mirrors .cursor/agents/sdk/)
├── commands/        # Slash commands — invoked with /g-command-name
│   └── g-*.md
├── hooks/           # PowerShell/Bash hook scripts
│   ├── g-hk-session-start.ps1
│   ├── g-hk-agent-complete.ps1
│   ├── g-hk-validate-shell.ps1
│   └── g-hk-setup-user.ps1
├── rules/           # AI behavior rules (.md format)
│   └── g-rl-*.md
└── skills/          # Reusable knowledge modules
    └── g-skl-*/
        └── SKILL.md
```

---

## What Makes Claude Code Unique

### Rules Use Plain `.md` Format
Unlike Cursor's `.mdc` format, Claude Code rules are plain markdown files. The YAML frontmatter format is nearly identical but uses `.md` extension:
```yaml
---
description: "What this rule does"
globs: ["**/*.py"]
alwaysApply: false
---
# Rule content
```

### Commands Use `/` Prefix
```
/g-setup
/g-task-new
/g-code-review
```

### Two Settings Files
- `settings.json` — committed, shared across machines (MCP servers, team permissions)
- `local.settings.json` — gitignored, machine-specific overrides (personal API keys, local MCP URLs)

### CLAUDE.md Auto-Loading
Claude Code automatically loads `.claude/CLAUDE.md` at the start of every session. The root `CLAUDE.md` is also auto-loaded. Both files work together — root `CLAUDE.md` sets project context, `.claude/CLAUDE.md` adds Claude-specific instructions.

### Full Hooks Support
Claude Code has the richest hook system of all platforms. Available hook events:
- `sessionStart` — new conversation begins
- `stop` — agent loop ends
- `beforeShellExecution` — before shell commands
- `afterFileEdit` — after any file is edited
- `preToolUse` / `postToolUse` — around every tool call

Configured via `hooks.json`:
```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{"command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/g-hk-session-start.ps1"}],
    "stop": [{"command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/g-hk-agent-complete.ps1"}],
    "beforeShellExecution": [{"command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/g-hk-validate-shell.ps1"}]
  }
}
```

### MCP Configuration
MCP is configured in `settings.json`:
```json
{
  "mcpServers": {
    "gald3r_docker": {
      "url": "http://localhost:8092/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### Agents SDK
The `agents/sdk/` folder mirrors `.cursor/agents/sdk/` — a Python SDK for building custom agent integrations. Not auto-loaded by Claude Code. See `agents/sdk/README.md`.

---

## gald3r Naming Conventions

| Component | Prefix | Example |
|-----------|--------|---------|
| Agents | `g-agnt-` | `g-agnt-task-manager.md` |
| Skills | `g-skl-` | `g-skl-tasks/SKILL.md` |
| Commands | `g-` | `g-setup.md` |
| Rules | `g-rl-` | `g-rl-33-enforcement_catchall.md` |
| Hooks | `g-hk-` | `g-hk-session-start.ps1` |

---

## Parity with Cursor

`.claude/` is nearly identical to `.cursor/` with two differences:
1. Rules are `.md` not `.mdc`
2. Command prefix is `/` not `@`

Everything else — agents, skills, commands content, hooks logic — is the same. When you update a skill or command in `.cursor/`, copy the change to `.claude/` as well.

---

## Comparison to Other Platforms

| Feature | Claude Code | Cursor | Gemini (.agent) | Codex | OpenCode |
|---------|-------------|--------|-----------------|-------|----------|
| Rules format | `.md` | `.mdc` | `.md` | via AGENTS.md | `.md` |
| Command prefix | `/` | `@` | `/` | via AGENTS.md | `/` |
| Agents folder | ✅ `agents/` | ✅ `agents/` | ❌ uses `workflows/` | ❌ via config.toml | ✅ `agents/` |
| Hooks | ✅ Full + extra events | ✅ Full | ✅ Full | ❌ None | ❌ None |
| Skills | ✅ | ✅ | ✅ | ✅ | via AGENTS.md |
| MCP config | `settings.json` | `.cursor/mcp.json` | `mcp_config.json` | `config.toml` | `opencode.json` |
