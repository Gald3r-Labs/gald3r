---
name: g-skl-platform-windsurf
description: Authoritative reference for Windsurf IDE customization in gald3r projects. Covers .windsurfrules layout, Cascade agent integration, rules format, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
vault_docs_url: https://docs.windsurf.com
docs_url: https://docs.windsurf.com
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
capability_status:
  hooks: ❌      # no documented lifecycle hook wiring for gald3r g-hk-*.ps1
  rules: ⚠️      # real, but legacy .windsurfrules vs current .windsurf/rules/*.md; .md not .mdc
  skills: ❌     # no native skills discovery; rule-text summaries only
  commands: ⚠️   # no native command runtime; Cascade workflows are a manual, non-mapped analog
  mcp: ⚠️        # supported via ~/.codeium/windsurf/mcp_config.json (Windsurf-specific path)
  docs_fresh: ❌ # last_doc_scan: never — no crawl performed
last_doc_scan: never
---

# g-skl-platform-windsurf

Activate for: setting up gald3r in Windsurf IDE, authoring Windsurf rules, understanding `.windsurfrules` structure, or verifying Windsurf gald3r integration.

---

## 1. Platform Overview

**Windsurf** (by Codeium) is a VS Code-based AI-first IDE featuring the **Cascade** agentic AI system. Windsurf supports global and workspace-level rules that are automatically injected into Cascade sessions.

- **Cascade**: Multi-step agentic AI that reads `rules` context automatically
- **Rules system**: Project-level `.windsurfrules`, global user rules
- **MCP**: Supports MCP servers via settings

**gald3r target tier**: VS Code family (similar rule injection to Cursor). Skills are served from root `skills/` via gald3r install.

---

## 2. Config File Layout

```
<project-root>/
├── .windsurfrules          ← Project-level rules (auto-injected into Cascade)
└── .windsurf/
    └── rules/              ← Per-file or per-folder rule overrides (optional)
```

**Global rules**: Managed in Windsurf settings UI → AI → Rules (stored in `~/.codeium/windsurf/memories/`).

**Format**: Plain markdown. No frontmatter required. All content injected as context.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only windsurf
```

Installs to `.windsurf/` in the target project.

### Rules File

gald3r writes its always-apply rules to `.windsurfrules`. Keep under 8K tokens for Cascade context budget.

### Skills

Windsurf does not have a native skills discovery path equivalent to Cursor's `.cursor/skills/`. Approach:
1. Surface skill content via `.windsurfrules` (compact summary)
2. Use `@mention` patterns in Cascade prompts to reference skill names

---

## 4. Verification

```bash
# Confirm rules file exists
Test-Path .windsurfrules

# Confirm install
node bin/install.js --list --target .
```

Expected: `.windsurfrules` present, `windsurf` row shows `detected: yes`.

---

## 5. Common Pitfalls

- Windsurf has both formats: legacy `.windsurfrules` at root AND current `.windsurf/rules/*.md` (per-rule files with activation modes). gald3r ships the legacy `.windsurfrules`; both are honored.
- Global user rules override project rules in some Cascade versions — test with project-scoped rules first
- Cascade context window is separate from inline completion context; rules are injected into Cascade only

---

## 6. Known Gaps (vs. Cursor reference)

Honest status — Windsurf is the closest Tier 2 platform to Cursor (both VS Code forks), but several
Cursor primitives have **no native equivalent**. See `PLATFORM_SPEC.md` (this folder) for the full
9-section assessment and verification evidence.

| Capability | Windsurf | Note |
|---|---|---|
| **Hooks** | ❌ | No documented lifecycle hook file that fires gald3r `g-hk-*.ps1`. Hooks run manually or via git `core.hooksPath` only. |
| **Skills** | ❌ | No native skills discovery path (no `.windsurf/skills/`). Skills degrade to compact summaries inside `.windsurfrules`. |
| **Agents** | ❌ | Cascade is the single built-in agent. No agents folder, no named-persona selection — gald3r `g-agnt-*` personas collapse to rule text. |
| **Commands** | ⚠️ | No native command runtime. Cascade **workflows** (`.windsurf/workflows/*.md`, `/`-invoked) are the nearest analog but are not auto-mapped from the gald3r `g-*` command set. |
| **Rules** | ⚠️ | Real and strong, but split across legacy `.windsurfrules` and current `.windsurf/rules/*.md` (activation modes); extension is `.md`, not Cursor's `.mdc`. |
| **MCP** | ⚠️ | Supported via `~/.codeium/windsurf/mcp_config.json` — a Windsurf-specific path, not portable from Cursor's `.cursor/mcp.json`. |

**Windsurf-only superset**: Cascade maintains an auto-generated **memory** store under
`~/.codeium/windsurf/memories/` that Cursor lacks. It is Cascade-managed, not gald3r-authored.

> **Honesty note**: `last_doc_scan: never`. Ratings are authored from prior Windsurf knowledge +
> the existing deploy scaffold, NOT a fresh crawl. Promote `❓`/`⚠️` only with dated evidence after
> `@g-platform-scan-docs windsurf`.
