# GEMINI.md - {project_name}

> Gemini / Google Antigravity-specific context for this project.
> See `agents.md` for universal instructions shared across all IDEs.
> Run `@g-setup` to initialize gald3r and auto-fill the placeholders below.

---

## Project Overview

**{project_name}** — {one sentence description}

---

## Gemini-Specific Configuration

### IDE Folders

```
.agent/
├── rules/       # Always-on rules (loaded automatically)
├── skills/      # Reusable skill packages
└── workflows/   # /slash-command automations
```

### Invoking Commands

Use `/g-command-name` syntax in Gemini:

| Command | Description |
|---------|-------------|
| `/g-setup` | Initialize gald3r |
| `/g-status` | Project status overview |
| `/g-task-new` | Create a new task |
| `/g-task-update` | Update task status |
| `/g-bug-report` | Report a bug |
| `/g-code-review` | Code review |
| `/g-plan` | Create or update project plan |
| `/g-medic` | Health check and repair `.gald3r/` |
| `/g-git-commit` | Structured git commits |
| `/g-idea-capture` | Capture an idea |
| `/g-workspace-status` | Show Workspace-Control manifest status |
| `/g-workspace-validate` | Validate Workspace-Control manifest and routing metadata |
| `/g-workspace-export --dry-run` | Show export plan only; no files are written |
| `/g-workspace-sync --dry-run` | Show sync plan only; no files are written |

See `docs/COMMANDS.md` for the full list.

---

## Gemini Agent Notes

### Mode Selection
- Use **Planning mode** for complex, multi-step tasks
- Use **Fast mode** for simple edits and renames
- Set Artifact Review Policy to "Request Review" for critical features

### Workflows
Workflows support `// turbo` for steps that should auto-execute without user approval. Use only for safe, idempotent operations.

### Rules
Rules in `.agent/rules/` are loaded automatically. Keep individual rule files under ~300 lines to avoid consuming excessive context.

### GUARDRAILS.md
Update `GUARDRAILS.md` when the agent encounters repeated failure patterns. This file accumulates learned constraints that prevent repeat mistakes.

### MCP Configuration
MCP servers are configured in `.mcp.json` at the project root.

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

## Task Management

### Direct Edit Policy
Edit these files directly without asking for permission:
- `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, `.gald3r/PLAN.md`, `.gald3r/PROJECT.md`
- All files in `.gald3r/tasks/`, `.gald3r/bugs/`, `.gald3r/features/`

### Atomic Updates
Always update BOTH in the same response:
1. Task file YAML: `status: completed`
2. TASKS.md entry: `[🔄]` → `[✅]`

Never update one without the other.

---

## Security

- Never commit API keys, tokens, or passwords
- Use environment variables for secrets
- Always use parameterized queries

---

**gald3r version**: 1.0.0
**Platform**: Gemini / Google Antigravity
**Universal instructions**: See `agents.md`
