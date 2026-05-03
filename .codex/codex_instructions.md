# Codex Platform — gald3r Configuration Guide

**Platform**: OpenAI Codex (CLI agent)
**Config Folder**: `.codex/`
**gald3r Version**: 1.0.0
**Official Docs**: https://developers.openai.com/codex
**Config File**: `.codex/config.toml`

---

## Folder Layout

```
.codex/
├── config.toml      # Main Codex configuration (model, skills, agents, features)
├── INSTALL.md       # Setup instructions for Codex
└── skills/          # Reusable knowledge modules
    └── g-skl-*/
        └── SKILL.md
```

**What Codex does NOT have:**
- No `agents/` folder — agents defined inline in `config.toml` under `[agents]`
- No `commands/` folder — Codex uses AGENTS.md for behavioral instructions
- No `rules/` folder — enforcement rules embedded in AGENTS.md (root) and via `config.toml` behavior
- No `hooks/` folder — Codex does not support lifecycle hooks

---

## What Makes Codex Unique

### No Hooks
Codex has no hook system. There is no equivalent of `sessionStart`, `stop`, or `beforeShellExecution`. All behavioral enforcement must come from `config.toml` agent definitions and `AGENTS.md`.

### No Commands Folder
Codex does not have a commands discovery system. Instead:
- Skills in `.codex/skills/` provide workflow instructions
- Agents in `config.toml` define specialized roles
- `AGENTS.md` at the project root carries behavioral instructions

### No Rules Folder
Codex has no native rules directory. Enforcement rules are handled two ways:
1. **`AGENTS.md`** root file — Codex reads this natively; the gald3r Enforcement Rules section contains all critical rules
2. **`config.toml` agent descriptions** — agent role descriptions encode behavioral guardrails

### config.toml is the Master Config
Everything for Codex lives in `config.toml`:
```toml
model = "gpt-5-codex"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[features]
multi_agent = true
shell_tool = true

# Register skills (only paths that actually exist!)
[[skills.config]]
path = ".codex/skills/g-skl-tasks"
enabled = true

# Define agent roles
[agents.task-manager]
description = "Manages gald3r task lifecycle..."
```

### Skills Are Explicitly Registered
Unlike Cursor/Claude/Gemini where skills are auto-discovered by folder scanning, Codex requires **explicit registration** of each skill in `config.toml`. Only register paths that actually exist — missing paths will cause startup errors.

**Currently registered skills** (all 17 gald3r core skills):
- `g-skl-bugs`, `g-skl-code-review`, `g-skl-dependency-graph`
- `g-skl-git-commit`, `g-skl-ideas`, `g-skl-medic`
- `g-skl-plan`, `g-skl-project`, `g-skl-qa`, `g-skl-review`
- `g-skl-setup`, `g-skl-status`
- `g-skl-subsystems`, `g-skl-swot-review`, `g-skl-tasks`, `g-skl-verify-ladder`

### Multi-Agent Support
Codex supports multi-agent mode via `config.toml`. Agent roles are defined as named sections:
```toml
[agents]
max_threads = 6
max_depth = 2

[agents.task-manager]
description = "..."

[agents.planner]
description = "..."
```

### Sandbox Configuration
Codex runs in a sandboxed environment. The `sandbox_mode = "workspace-write"` setting allows file writes within the workspace. The `approval_policy = "on-request"` means Codex asks before executing commands.

Windows-specific:
```toml
[windows]
sandbox = "elevated"
```

---

## gald3r Naming Conventions

| Component | Prefix | Location |
|-----------|--------|----------|
| Skills | `g-skl-` | `.codex/skills/g-skl-*/SKILL.md` |
| Agents | (inline) | `config.toml [agents.*]` |
| Commands | (none) | via AGENTS.md + skills |
| Rules | (none) | via AGENTS.md enforcement section |

---

## Enforcement Without Rules

Since Codex has no rules folder, enforcement is delivered via `AGENTS.md`. The root `AGENTS.md` has a dedicated **Enforcement Rules** section that covers:
- Error reporting (zero tolerance — all errors logged to BUGS.md)
- Task completion gate (no marking complete with stubs)
- Code change gate (task required before code changes)
- Session start sync (load CONSTRAINTS.md, display context)
- .gald3r/ folder gate (use skills for all .gald3r/ operations)
- Documentation placement, PowerShell conventions

**Always read `AGENTS.md` before starting any session in Codex.**

---

## AGENTS.md Role
In Codex, `AGENTS.md` at the project root is the primary behavioral instruction file. It is read natively by Codex at startup. This single file replaces what Cursor spreads across `rules/`, `agents/`, and project-level files.

---

## Comparison to Other Platforms

| Feature | Codex | Cursor | Claude Code | Gemini | OpenCode |
|---------|-------|--------|-------------|--------|----------|
| Rules | via AGENTS.md | `.mdc` files | `.md` files | `.md` files | `.md` files |
| Commands | via AGENTS.md | `@g-*` | `/g-*` | `/g-*` | `/g-*` |
| Agents | `config.toml` | `agents/` | `agents/` | `workflows/` | `agents/` |
| Hooks | ❌ None | ✅ Full | ✅ Full | ✅ Full | ❌ None |
| Skills | ✅ (explicit) | ✅ (auto) | ✅ (auto) | ✅ (auto) | via AGENTS.md |
| Config file | `config.toml` | `hooks.json` + `mcp.json` | `settings.json` + `hooks.json` | `mcp_config.json` | `opencode.json` |
