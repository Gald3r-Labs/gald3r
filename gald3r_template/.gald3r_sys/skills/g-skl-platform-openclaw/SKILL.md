---
name: g-skl-platform-openclaw
description: Authoritative reference for OpenClaw AI agent customization in gald3r projects. Covers SOUL.md pattern, workspace skill conventions, and caveman-compatible integration.
crawl_max_age_days: 14
vault_doc_path: research/platforms/openclaw/
vault_docs_url: https://github.com/openclaw/openclaw
token_budget: low
---

# g-skl-platform-openclaw

Activate for: setting up gald3r with OpenClaw, authoring `SOUL.md`, understanding OpenClaw's caveman-compatible workspace skill pattern, or verifying OpenClaw gald3r integration.

---

## 1. Platform Overview

**OpenClaw** is a caveman-ecosystem-compatible AI coding agent that uses `SOUL.md` as its primary project context file. It follows the caveman pattern (single source + CI generation) and is designed for workspace-level skill discovery.

- **SOUL.md**: Project identity and context file (analogous to AGENTS.md / CLAUDE.md)
- **Workspace skills**: Reads from `skills/` at project root (caveman-compatible)
- **Config**: Minimal — SOUL.md + skills/ directory
- **Ecosystem**: Part of the caveman-derived agent ecosystem

**gald3r target tier**: Caveman-ecosystem compatible. Direct root `skills/` reader — zero extra wiring needed post-T1042.

---

## 2. Config File Layout

```
<project-root>/
├── SOUL.md                 ← Project identity + context (primary config)
└── skills/                 ← Canonical skill source (OpenClaw reads directly)
    └── {skill-name}/
        └── SKILL.md
```

**`SOUL.md` format**: Plain markdown. Acts as the project's AI identity document.

---

## 3. gald3r Integration

**OpenClaw reads directly from root `skills/` — after T1042, gald3r's canonical source IS the skills/ dir.**

### Install

```bash
node bin/install.js --only openclaw
```

Creates `SOUL.md` with gald3r project identity content.

### SOUL.md Content

```markdown
# SOUL — {Project Name}

## Identity
This project uses gald3r for AI-assisted development. gald3r provides task management,
quality assurance, and multi-platform skill delivery.

## Context
- Tasks: .gald3r/TASKS.md
- Constraints: .gald3r/CONSTRAINTS.md  
- Project mission: .gald3r/PROJECT.md

## Skills
All skills available in the root skills/ directory (T1042 canonical source).

## Commit Convention
feat(T{id}): description | fix(BUG-{id}): description
```

### Skills Discovery

OpenClaw reads from `skills/` natively — the T1042 root `skills/` dir is the target. **No extra wiring needed.**

---

## 4. Verification

```bash
Test-Path SOUL.md
Test-Path skills/g-skl-tasks/SKILL.md
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- SOUL.md is the primary identity file — do not confuse with AGENTS.md (which gald3r also uses)
- OpenClaw reads root `skills/` directly; platform-specific dirs (`.cursor/skills/`) are not read by OpenClaw
- T1042's root `skills/` dir IS the OpenClaw integration — no additional install step beyond T1042
