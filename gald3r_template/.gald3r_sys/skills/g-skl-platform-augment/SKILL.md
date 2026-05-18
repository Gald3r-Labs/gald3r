---
name: g-skl-platform-augment
description: Authoritative reference for Augment Code (VS Code + JetBrains) customization in gald3r projects. Covers guidelines file, workspace instructions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/augment/
vault_docs_url: https://docs.augmentcode.com
---

# g-skl-platform-augment

Activate for: setting up gald3r with Augment Code, authoring workspace guidelines, understanding Augment's context engine, or verifying Augment gald3r integration.

---

## 1. Platform Overview

**Augment Code** is an enterprise-focused AI coding assistant available as a VS Code extension and JetBrains plugin. It features deep codebase indexing, context-aware completions, and a chat interface. Enterprise tier supports team-shared guidelines.

- **Context engine**: Indexes entire codebase for semantic search
- **Guidelines**: Workspace-level instructions injected into sessions
- **Completions**: Tab-to-accept, multi-line completions
- **JetBrains**: Full parity with VS Code extension

**gald3r target tier**: Enterprise VS Code + JetBrains. Guidelines via `.augment/guidelines.md`.

---

## 2. Config File Layout

```
<project-root>/
└── .augment/
    └── guidelines.md       ← Workspace-level instructions (auto-injected)
```

**Format**: Plain markdown. Augment reads `guidelines.md` from the `.augment/` directory.

**Alternative**: Some versions use `augment.yaml` for structured configuration — check your extension version.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only augment
```

Creates `.augment/guidelines.md` with gald3r task management context.

### Guidelines Content

```markdown
# gald3r Development Guidelines

## Task Management
- All work tracked in .gald3r/TASKS.md
- Read active task file before starting implementation
- Reference task ID in commit messages: feat(T{id}): ...

## Architecture
- Read .gald3r/CONSTRAINTS.md before architectural decisions
- Subsystem boundaries documented in .gald3r/SUBSYSTEMS.md

## Code Standards
- No bare TODO comments — use TODO[TASK-{id}→TASK-{new_id}] format
- Bug discovery: document in .gald3r/BUGS.md via g-qa-engineer
```

---

## 4. Verification

```bash
Test-Path .augment/guidelines.md
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Augment's codebase index is separate from guidelines — guidelines are for behavioral instructions
- JetBrains version may read from a different path (`~/.augment/` vs `.augment/`) — check IDE docs
- Enterprise team guidelines may override workspace guidelines depending on tier
