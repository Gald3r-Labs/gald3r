# Windsurf IDE (by Codeium) — gald3r Deploy Scaffold

**Config folder**: root `.windsurfrules` (+ optional `.windsurf/rules/`, `.windsurf/workflows/`)

This directory is the gald3r deploy scaffold for **Windsurf IDE**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity sync tooling.

Authoritative install + customization guide: **`g-skl-platform-windsurf`**
(`.gald3r_sys/skills/g-skl-platform-windsurf/SKILL.md`).

See **`PLATFORM_SPEC.md`** in this directory for the verified platform capability assessment
(Phase 1 research, T1466). Phase 2 deploy-artifact adaptation: T1491.

---

## Honest Capability Status

Legend: ✅ verified working · ⚠️ partial / surface-dependent · ❌ not supported · ❓ untested.

> **Caveat**: `PLATFORM_SPEC.md` carries `last_doc_scan: never`. Ratings below are authored from
> prior Windsurf knowledge, the shipped SKILL.md, and the existing deploy scaffold — NOT from a
> fresh `@g-platform-scan-docs windsurf` crawl. Windsurf's rules system moved through several
> formats (legacy `.windsurfrules` → `.windsurf/rules/*.md` with activation modes) and Cascade
> workflows are recent. Treat `⚠️`/`❓` cells as provisional until a dated crawl records evidence
> in PLATFORM_SPEC § Verification Evidence.

| Feature | Location | Status | Notes |
|---------|----------|--------|-------|
| Always-apply rules | `.windsurfrules` (root) | ⚠️ | Works, but **legacy** single-file format. Plain Markdown, auto-injected into Cascade. This is what gald3r ships. |
| Per-rule files | `.windsurf/rules/*.md` | ⚠️ | Current model with activation modes (Always On / Manual / Model Decision / Glob). Extension is `.md` (not Cursor's `.mdc`); activation-mode frontmatter keys not re-crawled. |
| Persistent memory | `~/.codeium/windsurf/memories/` | ❓ | Cascade-managed memory store + global user rules — **not gald3r-authored**. Windsurf-only superset over Cursor. |
| Agents (named personas) | (none) | ❌ | **Cascade is the only agent.** No `.windsurf/agents/` path, no multi-agent selection. gald3r `g-agnt-*` personas collapse to rule text only. |
| Skills | (none) | ❌ | **No native skills discovery** equivalent to `.cursor/skills/`. Cascade does not auto-load `SKILL.md`. Skills degrade to `.windsurfrules` summaries. |
| Commands (`g-*`) | (none / workflows) | ⚠️ | No native command runtime. Cascade **workflows** (`.windsurf/workflows/*.md`, `/`-invoked) are the nearest analog — manual, not auto-mapped to the gald3r command catalog. |
| Workflows | `.windsurf/workflows/*.md` | ❓ | Mechanism known from docs (`/`-slash invoked); no `.windsurf/workflows/` present to install-test here. |
| Hooks (local PS1) | (none) | ❌ | **No documented lifecycle hook system** for gald3r `g-hk-*.ps1`. Hooks run manually or via git `core.hooksPath` at best. (`❓` for any newer Cascade automation feature — not usable as gald3r hooks.) |
| MCP | `~/.codeium/windsurf/mcp_config.json` | ⚠️ | Supported via Cascade. Config path differs from Cursor's `.cursor/mcp.json` — **NOT single-path portable**. |

This table mirrors the PLATFORM_SPEC §9 Known Gaps and Capability Summary.

---

## Scaffold contents

| File | Purpose |
|---|---|
| `.windsurfrules` (generated at install) | gald3r always-apply rule subset (task gate, commit format, bug protocol), auto-injected into Cascade. Keep under ~8K tokens for the Cascade context budget. |
| `windsurf_instructions.md` | gald3r setup/configuration guide for Windsurf (folder layout, conventions, gitignore decision). |
| `PLATFORM_SPEC.md` | Verified capability matrix and Known Gaps (Phase 1, T1466). |
| `README.md` | This file. |

> The scaffold ships **no** `hooks.json`, `.ps1` hook wiring, `agents/`, `skills/`, or `commands/`
> folders for Windsurf — none of those have a native Windsurf surface (PLATFORM_SPEC §3–§6). Their
> absence is intentional, not an incomplete install.

---

## Folder layout (what gald3r writes vs. what Windsurf owns)

```
<project-root>/
├── .windsurfrules               ← gald3r writes (always-apply rule subset)         ⚠️ legacy
└── .windsurf/
    ├── rules/*.md               ← optional current per-rule files (activation modes) ⚠️
    └── workflows/*.md           ← Cascade workflows, /-invoked (hand-authored)       ❓
~/.codeium/windsurf/memories/    ← Cascade memory + global rules (Cascade-managed, outside repo)
~/.codeium/windsurf/mcp_config.json ← Cascade MCP config (different path than Cursor)
```

---

## Feedback Loop

The PLATFORM_SPEC ratings are deliberately conservative. To promote a `❓`/`⚠️` to `✅`, record dated
evidence (a doc citation or an install-test result) in PLATFORM_SPEC § Verification Evidence and
re-run `@g-platform-check`. A fresh `@g-platform-scan-docs windsurf` crawl clears the
`last_doc_scan: never` caveat. If a scaffold artifact does not behave as the table claims on your
Windsurf version, that is a known gap (not a bug in your install) — please open a GitHub issue with
your Windsurf version so the rating can be updated with evidence.
