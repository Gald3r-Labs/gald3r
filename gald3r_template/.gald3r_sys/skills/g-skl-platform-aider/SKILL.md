---
name: g-skl-platform-aider
description: Authoritative reference for Aider (terminal AI coding tool) customization in gald3r projects. Covers .aider.conf.yml, CONVENTIONS.md, model config, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/aider/
vault_docs_url: https://aider.chat/docs
---

# g-skl-platform-aider

Activate for: setting up gald3r with Aider, authoring `.aider.conf.yml`, configuring read-only files, or verifying Aider gald3r integration.

---

## 1. Platform Overview

**Aider** is a popular terminal-based AI coding tool that makes git commits automatically. It reads a configuration file and can be pointed at "read-only" context files for persistent project context.

- **Config**: `.aider.conf.yml` or `~/.aider.conf.yml` (global)
- **Read-only files**: Files Aider reads for context but won't edit
- **CONVENTIONS.md**: Project conventions file that Aider reads at session start
- **Git integration**: Auto-commits after each accepted edit

**gald3r target tier**: CLI tool. Config via `.aider.conf.yml` + read-only context files.

---

## 2. Config File Layout

```
<project-root>/
├── .aider.conf.yml         ← Aider configuration
├── CONVENTIONS.md          ← Project conventions (Aider reads this automatically if present)
└── .aiderignore            ← Files to exclude from Aider's context (like .gitignore)
```

**`.aider.conf.yml` format:**
```yaml
model: claude-opus-4-5
auto-commits: true
read:
  - .gald3r/PROJECT.md
  - .gald3r/CONSTRAINTS.md
  - CONVENTIONS.md
```

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only aider
```

Creates `.aider.conf.yml` pointing at gald3r context files as read-only inputs.

### CONVENTIONS.md

Create `CONVENTIONS.md` at project root — Aider reads this automatically:

```markdown
# Development Conventions

## Task References
Always reference active task: feat(T{id}): ...
Tasks tracked in .gald3r/TASKS.md

## Commit Style
feat(T{id}): description
fix(BUG-{id}): description

## Code Standards
- No bare TODO comments
- Read .gald3r/CONSTRAINTS.md before architecture changes
```

### Read-Only Context

Add gald3r files as read-only so Aider uses them for context without editing:
```bash
aider --read .gald3r/PROJECT.md --read .gald3r/CONSTRAINTS.md
```

---

## 4. Verification

```bash
Test-Path .aider.conf.yml
aider --config .aider.conf.yml --version
```

---

## 5. Common Pitfalls

- Aider auto-commits can conflict with gald3r's task-scoped commit discipline — disable `auto-commits: true` or audit commits
- Read-only files are included in context token budget — be selective (don't include TASKS.md if large)
- `.aiderignore` should exclude `.gald3r/` task files to avoid Aider modifying them
