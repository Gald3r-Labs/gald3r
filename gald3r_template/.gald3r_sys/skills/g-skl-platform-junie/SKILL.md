---
name: g-skl-platform-junie
description: Authoritative reference for JetBrains Junie (AI coding plugin) customization in gald3r projects. Covers .junie/guidelines.md, custom instructions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/junie/
vault_docs_url: https://www.jetbrains.com/junie/docs
token_budget: low
---

# g-skl-platform-junie

Activate for: setting up gald3r with JetBrains Junie, authoring `.junie/guidelines.md`, or verifying Junie gald3r integration in IntelliJ/PyCharm/WebStorm.

---

## 1. Platform Overview

**JetBrains Junie** is JetBrains' official AI coding assistant integrated into the IntelliJ platform (IntelliJ IDEA, PyCharm, WebStorm, GoLand, etc.). It reads project-level guidelines from `.junie/guidelines.md`.

- **Guidelines**: `.junie/guidelines.md` — injected into every Junie session
- **Agent mode**: Multi-step task execution within the JetBrains IDE
- **Context**: Uses IDE's code intelligence (PSI) for deep code understanding
- **Run configurations**: Junie can execute run configs defined in the IDE

**gald3r target tier**: JetBrains IDEs. Guidelines via `.junie/guidelines.md`.

---

## 2. Config File Layout

```
<project-root>/
└── .junie/
    └── guidelines.md       ← Project-level instructions (auto-injected into Junie)
```

**Format**: Plain markdown. Junie reads `guidelines.md` in full at session start.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only junie
```

Creates `.junie/guidelines.md` with gald3r task management context.

### Recommended guidelines.md

```markdown
# gald3r Development Guidelines

## Before Starting Any Task
1. Read `.gald3r/TASKS.md` for current task list
2. Read active task file in `.gald3r/tasks/task{id}_*.md`
3. Check `.gald3r/CONSTRAINTS.md` for architectural limits

## Commit Format
feat(T{id}): description of change
fix(BUG-{id}): description of fix

## Bug Discovery
When encountering bugs: do NOT silently ignore.
Pre-existing bugs → create entry in `.gald3r/BUGS.md`.

## Task Completion
Update task status in `.gald3r/tasks/task{id}_*.md` and `.gald3r/TASKS.md`.
```

---

## 4. Verification

```bash
Test-Path .junie/guidelines.md
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Junie requires a JetBrains AI subscription — ensure subscription is active
- Guidelines file is read at session start; changes take effect on next Junie activation
- Junie uses JetBrains' PSI for code navigation — gald3r rules that assume file paths may need IDE-relative path adjustments
