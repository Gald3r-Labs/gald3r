# Gemini / Antigravity Platform — gald3r Configuration Guide

**Platform**: Google Antigravity (Gemini-powered AI-first IDE)
**Config Folder**: `.agent/`
**gald3r Version**: 1.4
**Official Docs**: https://antigravity.google/docs
**Version**: Public Preview (Nov 2025+)

---

## Folder Layout

```
.agent/
├── commands/        # Slash commands — invoked with /g-command-name
│   └── g-*.md
├── hooks/           # PowerShell automation hooks
│   ├── g-hk-session-start.ps1
│   ├── g-hk-agent-complete.ps1
│   ├── g-hk-validate-shell.ps1
│   ├── g-hk-setup-user.ps1
│   └── README.md
├── rules/           # Workspace rules (.md format)
│   └── g-rl-*.md
├── skills/          # Reusable knowledge modules
│   └── g-skl-*/
│       └── SKILL.md
└── workflows/       # Gemini workflow definitions (equivalent to agents in Cursor/Claude)
    └── g-*.md       # Invoked as /g-name — same user-facing invocation as other platforms
```

**Note**: There is no `agents/` subfolder in `.agent/`. Gemini uses `workflows/` for what Cursor and Claude Code call "agents." See the Workflows section below.

---

## What Makes Gemini / Antigravity Unique

### No `agents/` Folder — Uses `workflows/` Instead
This is the most confusing structural difference. In Cursor and Claude Code, specialized AI assistants live in `agents/`. In Gemini/Antigravity, the equivalent concept is called **Workflows** and lives in `workflows/`. The files use the same `g-` naming prefix as commands on all other platforms.

**Why this difference exists**: Antigravity's agent model is workflow-first. The IDE is built around planning and executing workflows, not just calling pre-defined agents. A "workflow" in Gemini is a slash-command that can include `// turbo` annotations for auto-execution steps.

**Important**: Workflow files are named `g-*.md` (e.g., `g-setup.md`) so they invoke cleanly as `/g-setup` — the same slash command users already know from Claude Code and OpenCode. The `workflows/` folder location is enough to distinguish them from `commands/` when working on the system internally. You do not need to type a different prefix to use them.

### GEMINI.md Auto-Loading
`GEMINI.md` in the project root is Antigravity's project instruction file (equivalent to `CLAUDE.md`). It supplements `AGENTS.md` with Gemini-specific configuration.

Priority order Antigravity loads context:
```
AGENTS.md → GEMINI.md → .agent/rules/ → ~/.gemini/GEMINI.md (global)
```

### GUARDRAILS.md
`GUARDRAILS.md` originated as a Gemini feature — a file that accumulates learned constraints to prevent repeated failures. All platforms in gald3r now load GUARDRAILS.md via the session-start hook, but it is most natively supported in Antigravity.

### Rules Use `.md` Format (Same as Claude Code)
```yaml
---
description: "What this rule does"
activation: "always_on"   # always_on | glob | model_decision | manual
globs: ["**/*.py"]        # Only for activation: "glob"
---
# Rule content
```

Note: Antigravity uses `activation: "always_on"` in frontmatter rather than `alwaysApply: true` (Cursor/Claude). The `g-rl-*.md` files in `.agent/rules/` use the same content as other platforms but Antigravity may read the frontmatter differently. Keep content in the body (below frontmatter) — that's what all platforms read.

### Turbo Annotations in Workflows
Workflows support `// turbo` annotation to mark steps that auto-execute without user approval:
```markdown
## Step 1: Load context
// turbo
Read .gald3r/TASKS.md and PROJECT.md

## Step 2: Confirm with user
Which task should I start?
```
Only use `// turbo` for safe, idempotent operations. Don't use it on destructive steps.

### Global vs Workspace Rules
Gemini has a two-level rule hierarchy:
- **Global**: `~/.gemini/GEMINI.md` — applies across all projects
- **Workspace**: `.agent/rules/` — project-specific, takes priority

### MCP Configuration
MCP servers go in `mcp_config.json` at the project root (not inside `.agent/`):
```json
{
  "mcpServers": {
    "gald3r": { "url": "http://localhost:8092/mcp" }
  }
}
```

---

## gald3r Naming Conventions

| Component | Prefix | Location |
|-----------|--------|----------|
| Workflows (≈agents) | `g-` | `.agent/workflows/g-*.md` |
| Skills | `g-skl-` | `.agent/skills/g-skl-*/SKILL.md` |
| Commands | `g-` | `.agent/commands/g-*.md` |
| Rules | `g-rl-` | `.agent/rules/g-rl-*.md` |
| Hooks | `g-hk-` | `.agent/hooks/g-hk-*.ps1` |

**Note**: Workflows and commands share the `g-` prefix — their location (`workflows/` vs `commands/`) distinguishes them when working on the system. Users see only `/g-name` regardless of which folder backs it.

---

## FAQ

**Q: Why is there no `agents/` folder?**
A: Gemini/Antigravity uses `workflows/` for the same purpose. Agent-like behaviors are defined as slash-command workflows rather than named sub-agents. The IDE invokes them via `/workflow-name`.

**Q: Are the workflows the same as commands?**
A: Nearly identical in content. In Gemini, `workflows/` are explicitly slash-command workflows with optional `// turbo` steps. The `commands/` folder is also present for Gemini — both serve similar purposes. `workflows/` is the more idiomatic Gemini location. Both are invoked with `/g-name`.

**Q: Do phase files (g-phase-add, g-phase-pivot, etc.) in workflows still make sense?**
A: Those are legacy v2 workflow files. In v3 (sequential task IDs), phases are no longer a hard concept. The files are kept for backward compatibility but won't be used in new projects.

---

## Comparison to Other Platforms

| Feature | Gemini (.agent) | Cursor | Claude Code | Codex | OpenCode |
|---------|-----------------|--------|-------------|-------|----------|
| Rules format | `.md` | `.mdc` | `.md` | via AGENTS.md | `.md` |
| Command prefix | `/` | `@` | `/` | via AGENTS.md | `/` |
| Agents folder | ❌ uses `workflows/` | ✅ `agents/` | ✅ `agents/` | ❌ | ✅ `agents/` |
| Hooks | ✅ Full | ✅ Full | ✅ Full + extra | ❌ None | ❌ None |
| Skills | ✅ | ✅ | ✅ | ✅ | via AGENTS.md |
| Project instruction file | `GEMINI.md` | — | `CLAUDE.md` | AGENTS.md | AGENTS.md |
