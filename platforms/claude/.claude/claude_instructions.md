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
├── settings.json    # OFFICIAL config surface: MCP servers, permissions, env, "hooks" block
├── settings.local.json  # User-local overrides (gitignored — official name)
├── local.settings.json  # Legacy/local overrides (non-standard name; see PLATFORM_SPEC §9)
├── hooks.json       # gald3r hook wiring (NON-standard top-level file; see PLATFORM_SPEC §6)
├── agents/          # SubAgent definitions
│   ├── g-agnt-*.md  # gald3r agents (g-agnt- prefix)
│   ├── README.md    # Agent index
├── commands/        # Slash commands — invoked with /g-command-name
│   └── g-*.md
├── hooks/           # PowerShell/Bash hook scripts
│   ├── g-hk-session-start.py
│   ├── g-hk-agent-complete.py
│   ├── g-hk-validate-shell.py
│   └── g-hk-setup-user.py
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

### Hooks Support (⚠️ partial — read PLATFORM_SPEC §6/§9)

Claude Code has a native hooks system, but this is the **weakest-verified area** for
gald3r parity. Two config surfaces exist and the event-name shapes differ:

**Official surface — `settings.json` (key `"hooks"`).** This is the supported location.
Official lifecycle events (capitalized): `SessionStart`, `SessionEnd`,
`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Notification`, `Stop`,
`SubagentStop`, `PreCompact`. The shape is **matcher-grouped**:

```jsonc
// settings.json — OFFICIAL shape
"hooks": {
  "PreToolUse": [
    { "matcher": "Edit|Write|MultiEdit",
      "hooks": [ { "type": "command",
                   "command": "powershell.exe -ExecutionPolicy Bypass -File .claude/hooks/g-hk-...ps1" } ] }
  ],
  "Stop": [ { "hooks": [ { "type": "command", "command": "..." } ] } ]
}
```

**gald3r surface — `hooks.json` (NON-standard top-level file).** gald3r also ships a
`hooks.json`. Its `PreToolUse` block already uses the correct nested shape, but its
`sessionStart` / `stop` / `beforeShellExecution` entries use **lowercase** (Cursor-era)
event names. **`beforeShellExecution` has no official Claude Code equivalent**, and the
lowercase `sessionStart`/`stop` entries may **silently not fire** on current Claude Code.

> ⚠️ **Known gap (PLATFORM_SPEC §6/§9):** Until firing behavior is confirmed and the
> wiring is consolidated onto the official `settings.json` `"hooks"` block, treat
> lowercase `hooks.json` entries as **unverified**. `hooks.json` carries inline `_gap`
> annotations. Do not delete working config — verify first. Tracked as a follow-up.

There are **no** `afterFileEdit` / `preToolUse` / `postToolUse` lowercase events on
Claude Code — those were listed in an earlier Cursor-generic version of this guide and
are not part of Claude Code's documented event set.

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
The experimental Python Agent SDK previously at `agents/sdk/` was moved to the gald3r maintainer tree and no longer ships in installs (T1652 D1).

---

## gald3r Naming Conventions

| Component | Prefix | Example |
|-----------|--------|---------|
| Agents | `g-agnt-` | `g-agnt-task-manager.md` |
| Skills | `g-skl-` | `g-skl-tasks/SKILL.md` |
| Commands | `g-` | `g-setup.md` |
| Rules | `g-rl-` | `g-rl-33-enforcement_catchall.md` |
| Hooks | `g-hk-` | `g-hk-session-start.py` |

---

## Parity with Cursor

`.claude/` is broadly similar to `.cursor/`, with these differences:
1. Rules are `.md` not `.mdc`
2. Command prefix is `/` not `@`
3. **Hooks are NOT 1:1.** Claude Code's official hook config is `settings.json` `"hooks"`
   with capitalized, matcher-grouped events; gald3r's `hooks.json` carries lowercase
   Cursor-era event names (`sessionStart`/`stop`/`beforeShellExecution`) that may not
   fire. See the Hooks Support section above and **PLATFORM_SPEC §6/§9**.

Agents, skills, and commands content map cleanly (Claude Code has first-class native
subagents and Agent Skills — a strength over the Cursor reference). When you update a
skill or command in `.cursor/`, the same content propagates to `.claude/` via
`platform_parity_sync.ps1`. Hook **wiring**, however, is platform-specific — do not
assume a Cursor `hooks.json` entry fires identically on Claude Code.

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
