---
name: g-skl-platform-kiro
description: Authoritative reference for Kiro IDE (Amazon) customization in gald3r projects. Covers .kiro/steering/ layout, spec-driven development, hooks, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro/
vault_docs_url: https://kiro.dev/docs
token_budget: low
---

# g-skl-platform-kiro

Activate for: setting up gald3r in Kiro IDE, authoring steering files, understanding Kiro's spec-driven development model, or verifying Kiro gald3r integration.

---

## 1. Platform Overview

**Kiro** is Amazon's AI IDE (launched 2025) built on VS Code. It introduces a spec-driven development model where AI agents work from structured specifications. Features steering files for persistent context injection.

- **Steering files**: Markdown files in `.kiro/steering/` — injected into every Kiro session
- **Specs**: `.kiro/specs/` — structured feature specs with requirements, tasks, design
- **Hooks**: `.kiro/hooks/` — automation triggered on file changes
- **Agent**: Kiro's AI agent reads steering + specs for context

**gald3r target tier**: Amazon IDE. Spec-driven model maps naturally to gald3r task/PRD workflow.

---

## 2. Config File Layout

```
<project-root>/
└── .kiro/
    ├── steering/                   ← Always-injected context files
    │   ├── product.md              ← Product context (maps to .gald3r/PROJECT.md)
    │   ├── structure.md            ← Codebase structure
    │   └── tech.md                 ← Tech stack guidance
    ├── specs/                      ← Feature specifications
    │   └── {feature}/
    │       ├── requirements.md
    │       └── design.md
    └── hooks/                      ← Automation hooks
        └── {hook-name}.md
```

**Format**: Plain markdown. Steering files are injected automatically. Specs are referenced on demand.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only kiro
```

Creates `.kiro/steering/gald3r.md` with gald3r task management context.

### Recommended Steering Files

**`.kiro/steering/gald3r.md`**:
```markdown
# gald3r Task Management
Tasks are tracked in .gald3r/TASKS.md. Active task IDs are in .gald3r/tasks/.
Read .gald3r/PROJECT.md for mission and .gald3r/CONSTRAINTS.md before making architecture decisions.
Always reference the active task ID in commit messages.
```

### Mapping Kiro Specs → gald3r PRDs

Kiro specs map naturally to gald3r PRDs:
- `requirements.md` → PRD acceptance criteria
- `design.md` → PRD technical design

---

## 4. Verification

```bash
Test-Path .kiro/steering
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Steering files are injected in full — keep each under 2K tokens for context budget
- Kiro's spec system is additive with gald3r tasks — use both (specs for Kiro UI, tasks for gald3r tracking)
- `.kiro/` is Kiro IDE specific; do not confuse with Kiro-CLI which uses the same dir but different conventions
