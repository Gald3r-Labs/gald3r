---
name: g-skl-platform-kiro
description: Authoritative reference for Kiro IDE (Amazon) customization in gald3r projects. Covers .kiro/steering/ layout, spec-driven development, hooks, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro/
vault_docs_url: https://kiro.dev/docs
docs_url: https://kiro.dev/docs
capability_status:
  hooks: ⚠️       # native JSON hooks (.kiro/hooks/*.json) but file-event, not session/tool-lifecycle
  rules: ⚠️       # steering files (.kiro/steering/*.md); no per-rule glob scoping
  skills: ❌       # no SKILL.md discovery mechanism in Kiro IDE
  commands: ⚠️    # no command-file surface; partial via hooks + steering
  mcp: ✅          # .kiro/settings/mcp.json (doc-verified)
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-kiro

Activate for: setting up gald3r in Kiro IDE, authoring steering files, understanding Kiro's spec-driven development model, or verifying Kiro gald3r integration.

---

## 1. Platform Overview

**Kiro** is Amazon's AI IDE (launched 2025) built on VS Code. It introduces a spec-driven development model where AI agents work from structured specifications. Features steering files for persistent context injection.

- **Steering files**: Markdown (`.md`) in `.kiro/steering/` (project) and `~/.kiro/steering/` (global) — injected into every Kiro session
- **Specs**: `.kiro/specs/{feature}/` — structured feature specs (`requirements.md`, `design.md`, `tasks.md`)
- **Hooks**: `.kiro/hooks/*.json` — native agent hooks, **JSON** files with a `when`/`then` schema, triggered by file events
- **MCP**: `.kiro/settings/mcp.json` (workspace) / `~/.kiro/settings/mcp.json` (global)
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
    ├── hooks/                      ← Native agent hooks (JSON, NOT markdown)
    │   └── {hook-name}.json        ← { name, version, when: {type, patterns}, then: {type, command} }
    └── settings/
        └── mcp.json                ← workspace MCP config (mcpServers schema)

~/.kiro/                            ← GLOBAL (user-wide) tree
├── steering/                       ← global steering, all workspaces
└── settings/mcp.json               ← global MCP config
```

**Format**: Steering and specs are plain markdown (auto-injected / on-demand). Hooks are **JSON**
(`when`/`then`, file-event triggered). MCP config is JSON. See `PLATFORM_SPEC.md` for full details.

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
- Hooks are **JSON** (`.kiro/hooks/*.json`), not markdown — earlier docs that said `.md` were wrong

---

## 6. Known Gaps (vs. Cursor reference)

Honest status — see `PLATFORM_SPEC.md` §9 for full detail.

| Capability | Status | Note |
|---|---|---|
| Agents (`g-agnt-*.md`) | ❌ | No agent-file discovery in Kiro IDE. Express agent roles in steering. (Custom agents exist only in Kiro **CLI**.) |
| Skills (`g-skl-*/SKILL.md`) | ❌ | No SKILL.md auto-load. Fold skill knowledge into steering. "Powers" are a separate, unmapped concept. |
| Commands (`@g-*`/`/g-*`) | ⚠️ | No command-file surface. Document in steering or wire as hook `runCommand` actions. |
| Hooks | ⚠️ | Native JSON hook system (strength), but **file-event** triggered (`when.type: fileEdited`) — gald3r's `sessionStart`/`stop`/`preToolUse` lifecycle hooks have no native equivalent and run manually. |
| Rules | ⚠️ | Steering provides persistent context but **no per-rule glob scoping** (`.mdc` `alwaysApply`/`globs` degrade to whole-file steering). |
| MCP | ✅ | `.kiro/settings/mcp.json` (doc-verified). Timeout behavior ❓. |
| No top-level instruction file | n/a | Kiro uses steering, not `AGENTS.md`/`CLAUDE.md` — gald3r writes `.kiro/steering/gald3r.md`. |
| Doc freshness | ❓ | `last_doc_scan: never` — folder/format facts from May-2026 manual doc read; run `@g-platform-scan-docs kiro` to confirm. |
| Install/runtime | ❓ | `node bin/install.js --only kiro` and live IDE behavior not exercised here. |
