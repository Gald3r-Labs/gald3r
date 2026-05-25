# Aider Platform — gald3r Configuration Guide

**Platform**: Aider (terminal AI coding tool, auto-commits)
**Config Folder**: `.aider/` (scaffold) + root `.aider.conf.yml`
**gald3r Version**: 1.0.0
**Official Docs**: https://aider.chat/docs
**Config File**: `.aider.conf.yml` (project root)
**Authoritative skill**: `g-skl-platform-aider`

---

## Folder Layout

```
<project-root>/
├── .aider.conf.yml         # Aider configuration (model, auto-commits, read-only context)
├── CONVENTIONS.md          # Project conventions — Aider reads this automatically if present
└── .aiderignore            # Files excluded from Aider context (like .gitignore)
```

**What Aider does NOT have:**
- No `agents/` folder — Aider is a single-agent CLI tool
- No `commands/` folder — invocation is via the `aider` CLI and chat
- No `rules/` folder — behavioral guidance lives in `CONVENTIONS.md`
- No `hooks/` folder — Aider has no lifecycle hook system

---

## What Makes Aider Unique

### Auto-Commits
Aider creates a git commit after every accepted edit. This can conflict with gald3r's
task-scoped commit discipline (one logical commit per task, `feat(T{id}): ...`). Either:
- Set `auto-commits: false` in `.aider.conf.yml` and commit manually with gald3r conventions, OR
- Keep auto-commits on and squash/audit before pushing.

### Read-Only Context Files
Aider reads "read-only" files for persistent context without editing them. Point Aider at
gald3r control-plane files so it always has task and constraint context:

```yaml
# .aider.conf.yml
model: claude-opus-4-5
auto-commits: false
read:
  - .gald3r/PROJECT.md
  - .gald3r/CONSTRAINTS.md
  - CONVENTIONS.md
```

### CONVENTIONS.md
Aider auto-loads `CONVENTIONS.md` from the project root. This is the gald3r behavioral
surface for Aider — task references, commit format, and code standards live here.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (Aider does not auto-discover; reference in chat) |
| Agents | (none — single-agent tool) |
| Commands | (none — `aider` CLI invocation) |
| Rules | embedded in `CONVENTIONS.md` and `read:` gald3r files |

---

## Config Files Shipped

- **`.aider.conf.yml`** — Aider config with gald3r read-only context and auto-commits disabled.
- **`CONVENTIONS.md`** — gald3r task/commit/code conventions Aider loads automatically.

These are installed to the project root (not into `.aider/`), because Aider reads them
from root by convention.

---

## gitignore Decision (T1277 AC6)

Aider's config files (`.aider.conf.yml`, `CONVENTIONS.md`) are **source** — keep them tracked.
`.aiderignore` is also source. Aider does not generate a root output directory of its own,
so there is nothing to gitignore for this platform in an installed project.

---

## Verification

```powershell
Test-Path .aider.conf.yml
Test-Path CONVENTIONS.md
aider --config .aider.conf.yml --version
```

---

## Common Pitfalls

- Auto-commits conflict with task-scoped commits — disable or audit (see above).
- Read-only files count against the context token budget — do not add large `TASKS.md`.
- `.aiderignore` should exclude `.gald3r/` task files so Aider never edits coordination state.
