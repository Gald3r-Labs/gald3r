---
name: g-skl-platform-kiro
description: Authoritative reference for Kiro (Amazon's agentic IDE + Kiro CLI, the Q Developer CLI rebrand) customization in gald3r projects. Covers .kiro/ steering/prompts/agents/skills + settings/mcp.json, Agent Hooks (IDE file-event + CLI lifecycle), AGENTS.md instruction file, spec-driven workflow, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro/
vault_docs_url: https://kiro.dev/docs
docs_url: https://kiro.dev/docs
docs_url_secondary:
  - https://kiro.dev/docs/hooks/
  - https://kiro.dev/docs/chat/subagents/
  - https://kiro.dev/docs/skills/
  - https://kiro.dev/docs/chat/slash-commands/
  - https://kiro.dev/docs/steering/
  - https://kiro.dev/docs/mcp/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native Agent Hooks — IDE file-event triggers + CLI lifecycle (agentSpawn/userPromptSubmit/preToolUse/postToolUse/Stop)"
  rules: "✅ Steering .kiro/steering/*.md (Always/Conditional/Manual/Auto inclusion modes) + reads AGENTS.md"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .kiro/skills/ — same standard gald3r uses (Kiro 0.9)"
  commands: "✅ slash commands + local prompts .kiro/prompts/ (@name); skills/subagents auto-register"
  agents: "✅ native subagents .kiro/agents/ (IDE md+YAML; CLI JSON; parallel, own context window)"
  mcp: "✅ native — .kiro/settings/mcp.json (+ ~/.kiro, workspace precedence); subagent wildcard scoping"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-kiro

Activate for: setting up gald3r with Kiro (the Kiro IDE or the Kiro CLI), authoring steering/prompts/agents/skills/hooks, mapping the spec-driven workflow, or verifying the Kiro gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Kiro 0.9 natively supports commands, rules, agents, skills, hooks, and MCP, reads the
> `AGENTS.md` standard, and uses the **same open Agent Skills standard** as gald3r, so gald3r
> `SKILL.md` packages are directly portable. (Verified 2026-06-02 against https://kiro.dev/docs.)

## 1. Platform Overview

**Kiro** (Amazon) ships in two product lines: an **agentic IDE** (VS Code-based) and the **Kiro
CLI** (the rebrand of Amazon Q Developer CLI). Extension mechanisms are largely shared, with config
under `.kiro/` (workspace) and `~/.kiro/` (global). Its flagship feature is **spec-driven
development** (`requirements.md`/`design.md`/`tasks.md`), a natural seam for gald3r task/PRD parity.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                       ← read by Kiro (always-included; NOT CLAUDE.md)
└── .kiro/
    ├── steering/   *.md            ← rules/context (product/tech/structure + custom); 4 inclusion modes
    ├── prompts/    *.md            ← local prompts / slash commands (invoked @name)
    ├── agents/     *.md            ← subagents (IDE: markdown + YAML; CLI: JSON config)
    ├── skills/     <name>/SKILL.md ← Agent Skills (agentskills.io standard)
    ├── specs/      {feature}/      ← requirements.md / design.md / tasks.md (spec-driven dev)
    ├── hooks                       ← IDE Agent Hooks (file-event triggers)
    └── settings/mcp.json           ← MCP config (merged with ~/.kiro, workspace precedence)
```

Skills, steering, prompts, and MCP are **shared** across IDE and CLI. **Agents** differ (IDE md+YAML
vs CLI JSON) and **hooks** differ (IDE file-event triggers vs CLI lifecycle events).

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `g-skl-*/SKILL.md` tree straight into `.kiro/skills/`**
— Kiro uses the **identical open Agent Skills standard**, so there is **no per-platform port**. Add
`AGENTS.md` (always-read) and a `.kiro/steering/gald3r.md` context file; map gald3r rules to steering
inclusion modes and gald3r lifecycle hooks to the **CLI** events.

### Verify
```powershell
Test-Path .kiro/skills            # gald3r Agent Skills (drop-in)
Test-Path .kiro/steering          # rules/context (Always/Conditional/Manual/Auto)
Test-Path .kiro/settings/mcp.json # MCP config
Test-Path AGENTS.md               # always-included instruction file
```

## 4. Common Pitfalls

- Two surfaces: **agents** are IDE md+YAML (`.kiro/agents/*.md`) vs CLI **JSON** config; **hooks**
  are IDE **file-event** triggers (save/create/delete, prompt submit, tool, spec task, manual) vs
  CLI **lifecycle** events (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`Stop`).
- Kiro reads **`AGENTS.md`**, **not** `CLAUDE.md`/`GEMINI.md`. `AGENTS.md` is always-included and
  does **not** honor steering inclusion modes.
- Use `.md` (not Cursor's `.mdc`) for steering/rules — parity sync swaps the extension. gald3r's
  `alwaysApply: true` → **Always** mode; `description:`-scoped → **Auto**/**Conditional**.
- gald3r lifecycle `g-hk-*.ps1` map cleanly to the **CLI** events; the **IDE** file-event model fits
  file-save-style hooks only. A `.ps1` runs as the `Run Command` / shell action.
- MCP transport types (stdio/SSE/HTTP) and any steering size limit were not documented on the pages
  crawled — re-verify on the next scan.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | IDE file-event Agent Hooks + CLI lifecycle (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`Stop`); model differs by surface |
| Skills (`g-skl-*/SKILL.md`) | ✅ | agentskills.io standard in `.kiro/skills/` — **same standard gald3r uses**, directly portable (Kiro 0.9) |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.kiro/agents/` (IDE md+YAML; CLI JSON; parallel, own context window, appear as slash commands) |
| Commands (`@g-*`) | ✅ | slash commands + local prompts `.kiro/prompts/*.md` (`@name`); skills/subagents auto-register |
| Rules (`g-rl-*`) | ✅ | Steering `.kiro/steering/*.md` (Always/Conditional/Manual/Auto inclusion modes); reads `AGENTS.md` |
| MCP | ✅ | `.kiro/settings/mcp.json` (+ `~/.kiro`, workspace precedence); subagent wildcard scoping (`@figma/*`); transport types ❓ |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs kiro` (crawl_max_age_days: 7).
