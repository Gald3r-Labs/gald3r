# Gemini CLI Project Instructions

> This file is read by Gemini CLI (gemini command). Keep it focused and concise.

## Imported Context
<!-- @./.gemini/context/*.md if you add context files -->

## Operating Rules
- Read PLAN.md before broad architectural changes
- Update TASKS.md when work is completed  
- Follow patterns in .agent/rules/ for project conventions
- Prefer small, reviewable changes

## gald3r Integration
Skills and agents live in .agent/ (separate from .gemini/):
- .agent/skills/ - gald3r skill files
- .agent/agents/ - gald3r agent definitions
- .agent/rules/ - project rules

## Commands
Native Gemini CLI commands are in .gemini/commands/*.toml.

# <!-- gald3r GEMINI.md START -->
# GEMINI.md - {project_name}

> Gemini / Google Antigravity identity overlay for this project.
> **Universal instructions live in [`AGENTS.md`](./AGENTS.md)** — read it first.
> This file holds ONLY Gemini-specific notes; shared architecture, commands,
> task-management, vault, parity, security, and enforcement rules are in `AGENTS.md`.
> Run `@g-setup` to initialize gald3r and auto-fill `{project_name}`.

---

## Gemini-Specific Configuration

### IDE Folders

```
.agent/
├── rules/       # Always-on rules (loaded automatically)
├── skills/      # Reusable skill packages
└── workflows/   # /slash-command automations
```

### Command Prefix
Use `/g-command-name` syntax in Gemini. The full command catalog is in `AGENTS.md`
and `docs/COMMANDS.md` — it is **not duplicated here**.

### Mode Selection
- Use **Planning mode** for complex, multi-step tasks.
- Use **Fast mode** for simple edits and renames.
- Set Artifact Review Policy to "Request Review" for critical features.

### Workflows
Workflows support `// turbo` for steps that should auto-execute without user
approval. Use only for safe, idempotent operations.

### Rules
Rules in `.agent/rules/` load automatically. They are referenced, not inlined here —
trimming this file does not disable them. Keep individual rule files under ~300
lines to avoid consuming excessive context.

### GUARDRAILS.md
Update `GUARDRAILS.md` when the agent encounters repeated failure patterns. This
file accumulates learned constraints that prevent repeat mistakes.

### MCP Configuration
MCP servers are configured in `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "gald3r": {
      "url": "http://localhost:8092/mcp"
    }
  }
}
```

---

> All other guidance — project structure, command catalog, task status indicators
> and direct-edit policy, vault knowledge system, parity model, security, and
> enforcement rules — is in [`AGENTS.md`](./AGENTS.md). It is intentionally
> **not duplicated here**.

---

**Platform**: Gemini / Google Antigravity
**Universal instructions**: See [`AGENTS.md`](./AGENTS.md)

# <!-- gald3r GEMINI.md END -->

