---
name: g-skl-platform-cline
description: Authoritative reference for Cline (VS Code extension) customization in gald3r projects. Covers .clinerules layout, custom instructions, memory banks, and gald3r install verification.
docs_url: https://docs.cline.bot
crawl_max_age_days: 14
vault_doc_path: research/platforms/cline/
vault_docs_url: https://github.com/clinebot/cline
token_budget: low
capability_status:
  hooks: ❌      # no native hook system at all
  rules: ✅      # .clinerules/ dir or legacy file auto-injected (no glob scoping)
  skills: ❌     # no skills primitive; SKILL.md not auto-discovered
  commands: ⚠️   # Workflows (/<name>) cover a manually-ported subset only
  mcp: ✅        # strong (MCP marketplace, stdio + remote)
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-cline

Activate for: setting up gald3r with Cline, authoring `.clinerules`, configuring Cline memory banks, or verifying Cline gald3r integration.

---

## 1. Platform Overview

**Cline** (formerly Claude Dev) is a highly popular open-source VS Code extension for agentic AI coding. It reads project-level instructions from `.clinerules` and supports memory bank files for persistent context across sessions.

- **Agentic mode**: Full tool use (read/write files, run commands, browser use)
- **Rules**: `.clinerules` auto-injected at session start
- **Memory Bank**: Persistent markdown files in `memory-bank/` directory
- **MCP**: Full MCP support via Cline settings

**gald3r target tier**: VS Code extension (high install base). Rules via `.clinerules`.

---

## 2. Config File Layout

Cline supports **two rules layouts**: a modern `.clinerules/` *directory* (recommended) and a
legacy single `.clinerules` *file*.

```
<project-root>/
├── .clinerules/            ← (modern) rules DIRECTORY — every .md inside is auto-injected
│   ├── gald3r-rules.md     ← gald3r always-apply rules
│   └── workflows/          ← workflow files, invoked as /<workflow-name>
│       └── *.md
├── .clinerules             ← (legacy) single rules FILE (directory form preferred)
└── memory-bank/            ← prompted convention; persistent context (NOT auto-written by Cline)
    ├── projectbrief.md
    ├── activeContext.md
    └── progress.md
```

**Format**: Plain markdown. In the directory form, every `.md` is concatenated and injected; there
is **no `alwaysApply`/`globs` frontmatter scoping** — all rules are effectively always-apply.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only cline
```

Writes gald3r always-apply rules to `.clinerules`.

### Rules Content

gald3r writes its core session rules (from root `commands/` and always-apply subset) to `.clinerules`. Keep under ~4K tokens.

### Memory Bank

Create `memory-bank/projectbrief.md` to surface gald3r PROJECT.md mission to Cline sessions:

```markdown
# Project Brief
[paste .gald3r/PROJECT.md mission here]
```

---

## 4. Verification

```bash
Test-Path .clinerules
node bin/install.js --list --target .
```

Expected: `.clinerules` present, `cline` row shows `detected: yes`.

---

## 5. Common Pitfalls

- Prefer the `.clinerules/` **directory** form (multiple `.md` files) over the legacy single
  `.clinerules` file — the older SKILL.md text incorrectly said subdirectory rules are unsupported
- Memory bank files need to be manually updated — Cline reads but does not auto-write them
- Large rules (>8K tokens) compete for context; keep concise

---

## 6. Known Gaps (features that do NOT work on Cline)

Honest gap list vs. the Cursor reference. See `PLATFORM_SPEC.md` §9 for full detail and disposition.

| Capability | Cline status | Notes |
|---|---|---|
| **Hooks** | ❌ none | No native lifecycle hook system; gald3r `g-hk-*.ps1` + `hooks.json` do NOT run. Hook-driven behavior must become rules text or run out-of-band. |
| **Skills** | ❌ none | No skills primitive; `g-skl-*/SKILL.md` files are NOT auto-discovered. Only manual port to a workflow. |
| **Agents** | ❌ none | Single agent; no `g-agnt-*` persona registry or selection. |
| **Commands** | ⚠️ partial | Workflows (`/<name>`) cover only a manually-ported subset; the 174-command gald3r namespace is not auto-mounted. |
| **Per-rule glob scoping** | ❌ none | `.clinerules/` has no `alwaysApply`/`globs` frontmatter — every rule is always-apply. |

**Cline's standout strength is MCP** (in-editor marketplace, stdio + remote servers) — on par with
or ahead of the Cursor reference.

> **Verification status**: `last_doc_scan: never`. Ratings authored from prior knowledge + existing
> SKILL.md; no `.clinerules` config in this repo to inspect. Re-verify via `@g-platform-scan-docs
> cline` before promoting any `⚠️`/`❌` rating.
