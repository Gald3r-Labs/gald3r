---
name: g-skl-platform-openclaw
description: Authoritative reference for OpenClaw AI agent customization in gald3r projects. Covers the SOUL.md persona pattern, workspace skill conventions, and the OpenClaw hooks/MCP/commands surface.
docs_url: https://docs.openclaw.ai
docs_url_secondary:
  - https://github.com/openclaw/openclaw
  - https://docs.openclaw.ai/cli/skills
  - https://docs.openclaw.ai/cli/hooks
  - https://docs.openclaw.ai/cli/mcp
crawl_max_age_days: 14
vault_doc_path: research/platforms/openclaw/
vault_docs_url: https://github.com/openclaw/openclaw
last_doc_scan: never
capability_status:
  hooks: "⚠️"      # native hooks exist (HOOK.md + handler.ts, openclaw.json) but gald3r .ps1 payload non-portable
  rules: "❌"      # no native rules/.mdc mechanism; guidance folds into SOUL.md/AGENTS.md
  skills: "⚠️"     # SKILL.md folder-per-skill matches gald3r, but install lands in ~/.openclaw/workspace/skills/ (install-dependent, unverified live)
  commands: "⚠️"   # native slash (/new, /reset) + CLI commands exist; gald3r g-*.md not ingested
  mcp: "⚠️"        # first-class MCP (mcp.servers in openclaw.json), but gald3r server set not translated/tested
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
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

**gald3r target tier**: workspace `skills/` reader.

> **CORRECTION (T1479, verified vs. docs.openclaw.ai)**: earlier text in this skill called OpenClaw
> a "minimal SOUL.md + root skills/" reader with no hooks, commands, or MCP. The 2026 public docs
> show OpenClaw is a full **local-first autonomous agent** with a real **hooks system**, **slash
> commands**, and **first-class MCP** — and that it reads `~/.openclaw/workspace/skills/`, not the
> repo root "natively." See **`PLATFORM_SPEC.md`** in this directory for the verified, corrected
> capability assessment and the Known Gaps below.

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

- SOUL.md is the primary persona file — do not confuse with AGENTS.md (OpenClaw reads BOTH, plus TOOLS.md and MEMORY.md)
- OpenClaw reads its **workspace** `skills/` dir (`~/.openclaw/workspace/skills/` by default), NOT the repo root automatically — the workspace must be pointed at the repo, or gald3r skills installed into the workspace
- Platform-specific dirs (`.cursor/skills/`) are not read by OpenClaw

---

## 6. Known Gaps (vs. Cursor reference)

Full detail + verification evidence in **`PLATFORM_SPEC.md`** (this directory). Summary:

| Capability | Status | Gap |
|---|---|---|
| Hooks | ⚠️ | Native hooks exist (`HOOK.md` + `handler.ts`, wired in `~/.openclaw/openclaw.json`), but gald3r's PowerShell `g-hk-*.ps1` payload is **non-portable** and the event taxonomy differs (`gateway:startup`/`agent:bootstrap`/`command:new` vs gald3r `sessionStart`/`stop`/`preToolUse`) |
| Rules | ❌ | No native `rules/` or `.mdc` mechanism; gald3r `g-rl-*` rules must fold into `SOUL.md`/`AGENTS.md` prose |
| Skills | ⚠️ | `skills/<name>/SKILL.md` folder-per-skill matches gald3r, but installs land in the OpenClaw **workspace** dir, not the repo root automatically (install-path dependent; not verified on a live install) |
| Commands | ⚠️ | Native slash commands (`/new`, `/reset`) + CLI exist; gald3r `g-*.md` command files are **not** ingested as executable commands |
| Agents | ⚠️ | OpenClaw is itself an agent runtime, but does not discover gald3r `g-agnt-*.md` files; personas come from `SOUL.md`/`AGENTS.md`/`IDENTITY.md` |
| MCP | ⚠️ | First-class (`mcp.servers` in `openclaw.json`, stdio/SSE/streamable-http), but gald3r MCP server definitions are not auto-imported — re-declare via `openclaw mcp set` |
| Docs freshness | ❓ | `last_doc_scan: never` — **needs `@g-platform-scan-docs openclaw`** to confirm exact SKILL.md frontmatter fields honored, full hook event list, and whether a project-local `.openclaw/` is supported. All findings are public-doc-derived and **install-unverified**. |
