---
name: g-skl-platform-augment
description: Authoritative reference for Augment Code (Auggie CLI + VS Code + JetBrains) customization in gald3r projects. Covers .augment/ commands/agents/skills/hooks/rules + settings.json MCP, CLAUDE.md/AGENTS.md and .claude/.agents reuse, plugins/marketplace, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/augment/
vault_docs_url: https://docs.augmentcode.com
docs_url: https://docs.augmentcode.com
docs_url_secondary:
  - https://docs.augmentcode.com/cli/hooks
  - https://docs.augmentcode.com/cli/subagents
  - https://docs.augmentcode.com/cli/skills
  - https://docs.augmentcode.com/cli/custom-commands
  - https://docs.augmentcode.com/cli/rules
  - https://docs.augmentcode.com/cli/plugins
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in .augment/settings.json (PreToolUse/PostToolUse/Stop/SessionStart/SessionEnd; .ps1 supported)"
  rules: "✅ .augment/rules/*.md (always_apply/agent_requested/manual) + .augment-guidelines + reads CLAUDE.md/AGENTS.md"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .augment / .claude / .agents skills dirs"
  commands: "✅ custom slash commands .augment/commands/*.md (also .claude/.agents)"
  agents: "✅ native subagents .augment/agents/ (md + YAML; parallel)"
  mcp: "✅ native — ~/.augment/settings.json + auggie mcp add/list/remove"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-augment

Activate for: setting up gald3r with Augment Code (Auggie CLI / VS Code / JetBrains), authoring commands/agents/skills/hooks/rules, or verifying the Augment gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — the Auggie CLI natively supports commands, rules, agents, skills, hooks, and MCP, and
> reads `.claude/` + `.agents/` + `CLAUDE.md`/`AGENTS.md`, so gald3r's Claude-Code artifacts are
> largely reusable. (Verified 2026-06-02 against https://docs.augmentcode.com.)

## 1. Platform Overview

**Augment Code** — a VS Code extension, a JetBrains plugin, and the **`auggie` CLI**, with a codebase
**Context Engine** (semantic retrieval). The **CLI** is the full-extensibility surface; the IDE
extensions expose rules/guidelines + MCP + the index.

## 2. Config Layout

```
<project-root>/
├── CLAUDE.md / AGENTS.md           ← read by Auggie (Claude / agents compatible)
├── .augment-guidelines             ← legacy root guidelines (single file)
└── .augment/
    ├── rules/    *.md               ← always_apply | agent_requested | manual
    ├── commands/ *.md               ← custom slash commands
    ├── agents/   *.md               ← subagents (markdown + YAML)
    ├── skills/   <name>/SKILL.md    ← Agent Skills (agentskills.io standard)
    └── settings.json                ← hooks + MCP
```

Auggie **also** discovers `.claude/` and `.agents/` command/skill/agent trees → **gald3r's Claude-Code
tree works as-is on Augment.**

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.claude/` tree (+ `CLAUDE.md`/`AGENTS.md`)** — Auggie
loads it natively. Or package a Claude-Code-format **plugin bundle** (commands + agents + skills +
hooks + rules + MCP) and publish via `auggie plugin marketplace add owner/repo`.

### Verify
```powershell
Test-Path .augment/settings.json    # hooks + MCP config
Test-Path .claude/commands ; Test-Path .claude/skills ; Test-Path .claude/agents
```

## 4. Common Pitfalls

- Two surfaces: full extensibility is **CLI-only**; the IDE extensions are narrower. `manual`-type
  rules are **IDE-only** (the CLI skips them — use `always_apply`/`agent_requested`).
- Hooks + MCP are **settings-driven** (`.augment/settings.json`), not standalone committed files.
- Use `.md` (not Cursor's `.mdc`) for rule files — parity sync swaps the extension.
- Per-rule `globs:` path-scoping is not documented; approximate with `agent_requested` descriptions.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `.augment/settings.json`; PreToolUse/PostToolUse/Stop/SessionStart/SessionEnd; `.ps1` supported |
| Skills (`g-skl-*/SKILL.md`) | ✅ | agentskills.io; discovered in `.augment` / `.claude` / `.agents` skills dirs |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.augment/agents/` (md + YAML, parallel) |
| Commands (`@g-*`) | ✅ | `.augment/commands/*.md` (also `.claude/commands/`, `.agents/commands/`) |
| Rules (`g-rl-*`) | ✅ | `.augment/rules/*.md` + `.augment-guidelines`; reads `CLAUDE.md`/`AGENTS.md` |
| MCP | ✅ | `~/.augment/settings.json`; `auggie mcp add/list/remove` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs augment` (crawl_max_age_days: 14).
