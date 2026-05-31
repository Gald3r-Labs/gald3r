---
name: g-skl-platform-roo
description: Authoritative reference for Roo Code (VS Code extension) customization in gald3r projects. Covers .roo/rules/, mode-specific rules, custom modes (.roomodes), slash commands, MCP, and gald3r install verification.
docs_url: https://docs.roocode.com
crawl_max_age_days: 14
vault_doc_path: research/platforms/roo/
vault_docs_url: https://docs.roocode.com
token_budget: low
capability_status:
  hooks: "❌ none — Roo has no native lifecycle hook system; gald3r hooks run manually / via git core.hooksPath"
  rules: "✅ .roo/rules/ + .roo/rules-{slug}/ (recursive, alphabetical) with .roorules legacy fallback (doc-confirmed)"
  skills: "⚠️ no native folder-per-skill auto-load; surfaced via .roo/commands/ or by-name reference"
  commands: "⚠️ .roo/commands/*.md slash commands (doc-confirmed); gald3r command payload not yet shipped to scaffold"
  mcp: "⚠️ supported — project .roo/mcp.json (doc-confirmed); gald3r payload not shipped, server set per-machine"
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-roo

Activate for: setting up gald3r with Roo Code, authoring `.roorules`, understanding Roo's mode system, or verifying Roo gald3r integration.

---

## 1. Platform Overview

**Roo Code** (formerly Roo Cline) is a fork of Cline with enhanced agentic capabilities, custom AI modes (Code, Architect, Debug, Ask, Orchestrator), boomerang task orchestration, project slash commands, and first-class MCP. It is a VS Code extension.

- **Modes**: built-in (Code, Architect, Debug, Ask, Orchestrator) + custom modes in `.roomodes` — each can have separate rules
- **Rules (modern)**: `.roo/rules/` (all modes) + `.roo/rules-{slug}/` (per mode) — directories, read recursively & alphabetically
- **Rules (legacy fallback)**: single files `.roorules` / `.roorules-{slug}` (used only when the `.roo/` dirs are empty/missing); `.clinerules` also read for Cline compatibility
- **AGENTS.md**: auto-loaded from repo root (unless `roo-cline.useAgentRules:false`)
- **Commands**: `.roo/commands/*.md` slash commands (filename = command name)
- **MCP**: full MCP support — project `.roo/mcp.json` (team-shareable)
- **Hooks**: ❌ none — no native lifecycle hook system
- **Memory bank**: `memory-bank/` is an inherited Cline convention, not a Roo-native feature

**gald3r target tier**: VS Code extension. Shares Cline ancestry but diverges on rules dirs, modes, and slash commands. See `PLATFORM_SPEC.md` (this folder) for the full 9-section spec and capability table.

---

## 2. Config File Layout

```
<project-root>/
├── .roo/
│   ├── rules/              ← general rules, ALL modes (recursive, alphabetical) — modern form
│   ├── rules-{slug}/       ← mode-specific rules (e.g. rules-code/, rules-architect/)
│   ├── commands/           ← project slash commands (filename = command name) — *.md
│   └── mcp.json            ← project-level MCP server config (team-shareable)
├── .roomodes               ← custom mode definitions (YAML preferred; JSON accepted)
├── AGENTS.md               ← auto-loaded agent rules (unless roo-cline.useAgentRules:false)
│  ── legacy single-file fallbacks (used only when .roo/ dirs are empty/missing) ──
├── .roorules               ← general rules fallback (≈ .roo/rules/)
├── .roorules-{slug}        ← mode-specific rules fallback (≈ .roo/rules-{slug}/)
├── .clinerules             ← Cline-compatibility fallback (Roo can read it)
└── memory-bank/            ← optional Cline-style memory (convention, not native)
```

**Format**: Plain markdown (`.md`). Roo does NOT use Cursor's `.mdc`.
**Precedence**: directory form (`.roo/rules/`) takes precedence over the single-file legacy form;
project config takes precedence over global (`~/.roo/`).
**Current gald3r scaffold** (`.gald3r_sys/platforms/.roo/`) ships the **legacy** form only
(`.roorules`, `.roorules-architect`, `.clinerules`) — see Known Gaps.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only roo
```

Writes gald3r rules to `.roorules`. Also writes `.clinerules` as fallback.

### Mode-Specific Rules

For Architect mode (planning/design work), add gald3r architecture context:

```markdown
# .roorules-architect
Always read .gald3r/PLAN.md and .gald3r/CONSTRAINTS.md before making architecture decisions.
Subsystem changes require reading .gald3r/subsystems/{name}.md.
```

---

## 4. Verification

```bash
Test-Path .roorules
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Modern Roo prefers the **directory** form (`.roo/rules/`) over single-file `.roorules`; the dir
  form takes precedence when both exist. Empty/missing `.roo/rules/` falls back to `.roorules`.
- Within a rules directory, files load **recursively and alphabetically** — name files to control
  ordering. Mode-specific rules (`.roo/rules-{slug}/`) appear **before** general rules in the prompt.
- `AGENTS.md` is auto-loaded unless `roo-cline.useAgentRules:false` — don't double up rules content
  between `AGENTS.md` and `.roo/rules/`.
- Boomerang / Orchestrator sub-tasks may run in different modes — verify cross-mode rule loading.

## 6. Known Gaps (features that do NOT work on Roo Code)

Honest status vs. the Cursor reference (`g-skl-platform-cursor`). Full detail in `PLATFORM_SPEC.md`.

- **❌ Hooks**: Roo has **no native lifecycle hook system** (no `hooks.json`, no sessionStart/stop/
  preToolUse/beforeShellExecution). gald3r `g-hk-*.ps1` hooks must run manually or via git
  `core.hooksPath`. This is the largest gap.
- **⚠️ Skills**: no native folder-per-skill auto-relevance loading (Cursor's `.cursor/skills/<name>/`
  contract is absent). Skills are reachable only as `.roo/commands/` slash commands or by-name
  reference from rules.
- **⚠️ Agents**: `g-agnt-*.md` files are not auto-discovered. Roo's analog is custom **modes**
  (`.roomodes`); generating gald3r agents into modes is not yet implemented.
- **⚠️ Scaffold is legacy-form only**: `.gald3r_sys/platforms/.roo/` ships `.roorules` /
  `.roorules-architect` / `.clinerules` (root single-file legacy), NOT the modern `.roo/rules/`,
  `.roo/commands/`, `.roo/mcp.json`, or `.roomodes`. Roo still reads the legacy form (deploy works),
  but does not use the modern layout — a follow-up modernization item.
- **❓ Docs freshness**: `last_doc_scan: never`. Spec claims are from a manual 2026-05-26 doc crawl,
  not a `@g-platform-scan-docs roo` run.
