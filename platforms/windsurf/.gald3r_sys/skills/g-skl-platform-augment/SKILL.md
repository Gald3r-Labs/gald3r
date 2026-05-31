---
name: g-skl-platform-augment
description: Authoritative reference for Augment Code (VS Code + JetBrains + auggie CLI) customization in gald3r projects. Covers .augment-guidelines, .augment/rules/, the Context Engine, MCP, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/augment/
vault_docs_url: https://docs.augmentcode.com
docs_url: https://docs.augmentcode.com
docs_url_secondary:
  - https://docs.augmentcode.com/setup-augment/guidelines
  - https://www.augmentcode.com/mcp
last_doc_scan: never
capability_status:
  hooks: "❌ no native hook system (no lifecycle events / hooks.json)"
  rules: "✅ .augment/rules/*.md (always/auto/manual types) + root .augment-guidelines; .md not .mdc"
  skills: "❌ no skills-loading framework"
  commands: "❌ no user slash-command / workflow namespace"
  mcp: "⚠️ supported, but settings-driven (no confirmed repo-tracked config file)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-augment

Activate for: setting up gald3r with Augment Code, authoring workspace guidelines, understanding Augment's context engine, or verifying Augment gald3r integration.

---

> Capability ratings and the full 9-section breakdown live in `PLATFORM_SPEC.md` (this folder).
> Status: ⚠️ partial — rules solid; no native hooks/skills/commands/agents.

## 1. Platform Overview

**Augment Code** is an enterprise-focused AI coding assistant available as a VS Code extension, a JetBrains plugin, and the `auggie` CLI. It features deep codebase indexing (the **Context Engine**), context-aware completions, and a chat/agent interface. Enterprise tier supports team-shared guidelines.

- **Context engine**: Indexes entire codebase for semantic retrieval (NOT a user-writable rules store)
- **Guidelines / rules**: Workspace-level instructions injected into sessions
- **Completions**: Tab-to-accept, multi-line completions
- **JetBrains + CLI**: VS Code extension, JetBrains plugin, and the `auggie` CLI

**gald3r target**: VS Code + JetBrains + `auggie` CLI. Instructions via the root `.augment-guidelines` file and/or `.augment/rules/*.md`.

---

## 2. Config File Layout

```
<project-root>/
├── .augment-guidelines          ← legacy single-file workspace guidelines (root)
└── .augment/
    └── rules/                   ← modern rules directory (markdown, frontmatter-typed)
        └── *.md                 ← type: always | auto | manual
```

**Format**: Plain markdown. The root **`.augment-guidelines`** (no `.md` extension) applies to all
Agent/Chat sessions; `.augment/rules/*.md` files are typed via frontmatter (`always`/`auto`/`manual`).

> **Correction**: earlier text referenced `.augment/guidelines.md` and `augment.yaml`. The documented
> surfaces are the root `.augment-guidelines` file and the `.augment/rules/` directory. `augment.yaml`
> is not a documented gald3r-relevant config surface.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only augment
```

Creates the root `.augment-guidelines` file (and/or `.augment/rules/*.md`) with gald3r task management context.

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

```powershell
Test-Path .augment-guidelines
Test-Path .augment/rules
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Augment's Context Engine index is separate from guidelines — guidelines/rules are for behavioral instructions, the index is for code retrieval
- `manual`-type rules are IDE-only — the `auggie` CLI skips them (use `always`/`auto` for CLI-relevant gald3r rules)
- Use `.md`/`.mdx` for rule files, NOT Cursor's `.mdc` (parity sync swaps the extension)
- User/global rules live in IDE settings / home directory and are NOT repo-tracked or gald3r-managed

---

## 6. Known Gaps (does NOT work on Augment)

See `PLATFORM_SPEC.md` §9 for the full assessment. Summary of features that do not work here:

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ❌ | No native lifecycle/hook system, no `hooks.json`. Session-start context injection and pre-commit checks run manually or via always-rules text. |
| Skills (`g-skl-*/SKILL.md`) | ❌ | No skills-loading framework. Skill content is prose-only inside guidelines. |
| Agents (`g-agnt-*.md`) | ❌ | No user-agent-definition contract. Personas become rule text. |
| Commands (`@g-*`) | ❌ | No user slash-command / workflow namespace. Commands are doc-only. |
| Rules (`g-rl-*`) | ✅ | Works via `.augment/rules/*.md` + `.augment-guidelines`. Per-file `globs:` scoping unverified (❓). |
| MCP | ⚠️ | Supported, but settings-driven — no confirmed repo-tracked config file, so not fully captured by a repo install. |

**Honesty**: `last_doc_scan: never`. Ratings derive from a brief May-2026 doc check + the existing
skill, not a full `@g-platform-scan-docs augment` crawl. No `.augment/` config exists in this repo
to install-test. Promote `❓`/`⚠️` → `✅` only with evidence recorded in `PLATFORM_SPEC.md`.
