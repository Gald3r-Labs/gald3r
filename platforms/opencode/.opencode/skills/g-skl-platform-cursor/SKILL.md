---
name: g-skl-platform-cursor
description: Authoritative reference for Cursor IDE customization in gald3r projects. Covers .cursor/ folder layout, all supported primitives (rules/skills/agents/commands/hooks/MCP), AGENTS.md instruction file, .claude/.codex/.agents cross-tool reuse, parity tiers, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/cursor/
vault_docs_url: https://cursor.com/docs
docs_url: https://cursor.com/docs
docs_url_secondary:
  - https://cursor.com/docs/hooks
  - https://cursor.com/docs/subagents.md
  - https://cursor.com/help/customization/skills
  - https://cursor.com/changelog/1-6
  - https://cursor.com/docs/context/rules
  - https://cursor.com/docs/context/mcp
last_doc_scan: 2026-06-02
reference_implementation: true
capability_status:
  hooks: "✅ native lifecycle hooks in .cursor/hooks.json (sessionStart/stop/preToolUse/beforeShellExecution + large event surface; stdio JSON)"
  rules: "✅ .cursor/rules/*.mdc (alwaysApply/globs/description; 4 application types) + AGENTS.md + User/Team rules"
  skills: "✅ Agent Skills (SKILL.md) folder-per-skill in .cursor/skills + .agents/skills (auto-load)"
  commands: "✅ custom slash commands .cursor/commands/*.md (Cursor 1.6)"
  agents: "✅ native subagents .cursor/agents/ (md + YAML; parallel); also reads .claude/.codex agents"
  mcp: "✅ native — .cursor/mcp.json / ~/.cursor/mcp.json / Settings (stdio + SSE + HTTP; OAuth)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-cursor

Activate for: setting up gald3r with Cursor IDE (or the Cursor CLI / SDK), authoring
commands/agents/skills/hooks/rules, understanding `.cursor/` structure, verifying Cursor parity, or
answering questions about Cursor's capabilities.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ reference
> platform — full parity** — Cursor natively supports commands, rules, agents, skills, hooks, and MCP,
> and reads `.claude/agents/` + `.codex/agents/` + `.agents/skills/` + `AGENTS.md`, so gald3r's
> Claude/codex agent/skill artifacts are largely reusable. (Verified 2026-06-02 against
> https://cursor.com/docs.)

## 1. Platform Overview

**Cursor** — an AI-first IDE built on VS Code with deep agent-mode integration, running locally as a
desktop app, plus a **Cursor CLI** (`agent`, with Cloud Agent handoff) and a **TypeScript SDK** for
programmatic agents. The **IDE** is the full-extensibility surface. Cursor is the gald3r **reference
platform**: all primitives originate in `.cursor/` and propagate to the other 22 platforms via
`custom_scripts/platform_parity_sync.ps1`.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                      ← read by Cursor (root + nested dirs; primary instruction file)
├── .cursorrules                   ← legacy single-file instructions (still recognized)
└── .cursor/
    ├── rules/    *.mdc            ← alwaysApply | apply-intelligently | globs | manual
    ├── commands/ *.md             ← custom slash commands (Cursor 1.6)
    ├── agents/   *.md             ← subagents (markdown + YAML; parallel; Cursor 2.4)
    ├── skills/   <name>/SKILL.md  ← Agent Skills (SKILL.md; folder-per-skill; Cursor 2.4)
    ├── hooks.json                 ← native hook wiring at .cursor/hooks.json (TOP-LEVEL, not in hooks/)
    └── mcp.json                   ← MCP server config (or ~/.cursor/mcp.json / Cursor settings)
```

Cursor **also** discovers `.claude/agents/` + `.codex/agents/` (subagents) and `.agents/skills/`
(skills) → **gald3r's Claude/codex agent/skill trees work as-is on Cursor.**

**Key**: `.mdc` is Cursor-specific for rules; other platforms use `.md` (parity sync maps it). The
primary instruction file is **`AGENTS.md`**, NOT `CLAUDE.md`.

## 3. gald3r Integration

**Cursor is the canonical source** — author here first. Ship gald3r's `AGENTS.md` + the `.cursor/`
tree (rules/commands/agents/skills/hooks/MCP); Cursor also discovers `.claude/agents/` +
`.codex/agents/` + `.agents/skills/`, so Claude/codex agent/skill artifacts are reused without a
Cursor-specific port. Run `.\custom_scripts\platform_parity_sync.ps1` to propagate to all other
targets.

### Verify
```powershell
Test-Path .cursor/hooks.json     # native hook wiring (top-level, not in hooks/)
Test-Path .cursor/rules ; Test-Path .cursor/skills ; Test-Path .cursor/agents ; Test-Path .cursor/commands
Test-Path AGENTS.md              # primary instruction file (root)
```

## 4. Common Pitfalls

- **Rules must use `.mdc`** — Cursor only auto-loads rules with the `.mdc` extension. Other platforms
  use `.md`; parity sync handles the mapping.
- **Skills are folder-per-skill** — each must be `.cursor/skills/<name>/SKILL.md`; a loose `.md` in
  `skills/` root is NOT picked up.
- **`hooks.json` is top-level** — it lives at `.cursor/hooks.json` (repo `.cursor/` root), NOT inside
  `.cursor/hooks/`; `_hook_md` fields point at companion `.md` files in `.cursor/hooks/`.
- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** — Cursor reads `AGENTS.md` (root + nested) and
  legacy `.cursorrules`, but does not treat `CLAUDE.md` as a first-class input. Keep `AGENTS.md`
  authoritative.
- **Memories folded into Rules** — per-project auto Memories (v1.0, June 2025) were removed/folded into
  **Rules** in v2.1.x; use `.cursor/rules/*.mdc` as the durable always-on surface.
- **MCP timeout** — default is 60s; for long-running tools set `mcp.server.timeout: 600000` in Cursor
  settings.json.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `.cursor/hooks.json`; stdio JSON bidirectional; large event surface (sessionStart…afterAgentThought + Tab/workspaceOpen); Cursor 1.7 |
| Skills (`g-skl-*/SKILL.md`) | ✅ | folder-per-skill auto-load in `.cursor/skills/` + `.agents/skills/`; `/skill-name` or `@skill-name`; Cursor 2.4 |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.cursor/agents/` (md + YAML, parallel); also reads `.claude/agents/` + `.codex/agents/`; Cursor 2.4 |
| Commands (`@g-*`) | ✅ | `.cursor/commands/*.md` (filename = slash command); Cursor 1.6 |
| Rules (`g-rl-*`) | ✅ | `.cursor/rules/*.mdc` (alwaysApply/globs/description; 4 types) + `AGENTS.md` + User/Team rules |
| MCP | ✅ | `.cursor/mcp.json` / `~/.cursor/mcp.json` / Settings; stdio + SSE + Streamable HTTP; OAuth + multi-user |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs cursor` (crawl_max_age_days: 7).
