# Warp Platform — gald3r Configuration Guide

**Platform**: Warp (AI-native terminal — agent mode + Warp Drive workflows)
**Config Folder**: `.warp/` (workflow stubs) + shell profile integration
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.warp.dev
**Config Surface**: Warp Drive workflows (`.warp/workflows/`), shell profile env vars
**Authoritative skill**: `g-skl-platform-warp`

---

## Folder Layout

```
<project-root>/
└── .warp/
    └── workflows/          # Warp Drive workflow stubs (gald3r status / commit / new-task)
        ├── gald3r-status.yaml
        └── gald3r-commit.yaml
```

Warp's own config lives at `~/.warp/` (themes, launch configs). Warp does **not** use a
project-level rules file like `.windsurfrules` or `.clinerules`.

**What Warp does NOT have:**
- No project rules file — Warp's context is session-level, not project-file based
- No `agents/`, `commands/`, or lifecycle `hooks/` in the IDE sense

---

## What Makes Warp Unique

### Terminal-First Paradigm
Warp's AI operates on the terminal session context, not project files. gald3r rules do not
auto-inject. Integration is via:
1. **Shell profile env vars** — surface the active task / project into the session.
2. **Warp Drive workflows** — shareable, parameterized command snippets.

### Warp Drive Workflows
Warp Drive workflows are cloud-backed, shareable command templates. gald3r ships workflow
stubs (status, commit) that map to gald3r operations. Import them into Warp Drive or keep
them as project-local reference.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (invoked via shell, not auto-injected) |
| Agents | (none — Warp agent mode via chat) |
| Commands | Warp Drive workflows (`.warp/workflows/*.yaml`) |
| Rules | shell profile env vars (no project rules file) |

---

## Shell Profile Integration

Add to `~/.bashrc` / `~/.zshrc` / PowerShell profile so Warp sessions carry gald3r context:

```bash
export GALD3R_ACTIVE_TASK=$(grep '\[🔄\]' .gald3r/TASKS.md 2>/dev/null | head -1)
export GALD3R_PROJECT=$(head -3 .gald3r/PROJECT.md 2>/dev/null)
```

---

## Config Files Shipped

- **`.warp/workflows/gald3r-status.yaml`** — show active gald3r tasks.
- **`.warp/workflows/gald3r-commit.yaml`** — commit with a task-scoped message.

---

## gitignore Decision (T1277 AC6)

`.warp/workflows/*.yaml` are **source** — keep them tracked. Warp's user config
(`~/.warp/`) is outside the project. No generated project output dir needs gitignoring.

---

## Verification

```powershell
Test-Path .warp/workflows
```

---

## Common Pitfalls

- Warp's AI mode uses session context, not project files — gald3r rules do not auto-inject.
- Warp Drive workflows are cloud-backed — set up the workspace before team sharing.
- Terminal-first: skills/agents apply via shell invocation, not IDE integration.
