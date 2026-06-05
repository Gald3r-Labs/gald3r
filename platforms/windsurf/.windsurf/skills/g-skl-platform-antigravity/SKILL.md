---
name: g-skl-platform-antigravity
description: Authoritative reference for Google Antigravity (agent-first IDE + CLI + SDK) customization in gald3r projects. Covers AGENTS.md/GEMINI.md instruction files, .agents/ rules/skills/hooks + .antigravity/mcp.json, Workflows (slash commands), dynamic subagents, lifecycle hooks, Scheduled Tasks, and gald3r install verification. Post-2.0-relaunch (I/O 2026); skill path + hook payload pin via install test.
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
vault_docs_url: https://antigravity.google/docs/home
docs_url: https://antigravity.google/docs/home
docs_url_secondary:
  - https://antigravity.google/docs/hooks
  - https://antigravity.google/docs/subagents
  - https://antigravity.google/docs/skills
  - https://antigravity.google/docs/rules-workflows
  - https://antigravity.google/docs/mcp
  - https://antigravity.google/docs/command
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in hooks.json (before/after_tool_call, before/after_model_call, on_loop_stop, on_error; stdin/stdout JSON; shell scripts)"
  rules: "✅ Markdown rules (Manual/Always On/Model Decision/Glob) in .agents/rules + GEMINI.md; reads AGENTS.md"
  skills: "✅ Agent Skills (Anthropic SKILL.md) in .agents/.antigravity/.agent skills dirs (path pin via install test)"
  commands: "✅ Workflows (saved-prompt slash commands) /workflow-name; ~/.gemini/antigravity/global_workflows/"
  agents: "✅ native dynamic subagents (Orchestrator-spawned); ⚠️ no file-based g-agnt-*.md discovery"
  mcp: "✅ native — .antigravity/mcp.json or ~/.gemini/antigravity/mcp_config.json + MCP Store GUI"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-antigravity

Activate for: setting up gald3r with Google **Antigravity** (IDE / CLI / SDK), authoring
workflows/rules/skills/hooks, wiring MCP, or verifying the Antigravity gald3r install.

---

> Full breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full parity**
> — the post-2.0 IDE/CLI harness natively supports Workflows (commands), rules, dynamic subagents,
> skills, hooks, and MCP, and reads `AGENTS.md` + `GEMINI.md` while discovering Anthropic-format
> `SKILL.md`, so gald3r's `AGENTS.md` + `g-skl-*` artifacts are largely reusable. (Verified
> 2026-06-02 against https://antigravity.google/docs — JS-SPA docs; evidence cross-checked from
> verbatim extractions + Google codelabs.)

> **⚠️ VOLATILE / NEW PLATFORM.** Antigravity relaunched agent-first ~**2026-05-19**; Subagents /
> Hooks / Scheduled Tasks announced at **I/O 2026**. Keep `crawl_max_age_days: 7`. Two unknowns to
> **pin via a live install test** before hard-coding into installers: (1) the exact skills dir
> (`.agents/skills` vs `.antigravity/skills` vs `.agent/skills`), and (2) the hook payload schema.

## 1. Platform Overview

**Google Antigravity** (DeepMind) — an **agent-first** platform: a desktop **IDE**, a **CLI**, and an
**SDK** sharing **one agent harness** (common settings/config across the suite). Backed by Gemini
models; security centers on **Trusted Workspaces**. An **Orchestrator** decomposes goals and spawns
**dynamic subagents** that run async in the background.

> **Two products, one name:** capabilities here are the **IDE/CLI harness**. The hosted Gemini API
> **"Managed Agents"** (`ai.google.dev`) is a **separate** surface that currently lacks custom tools
> and subagent delegation — do **not** conflate it with the IDE/CLI harness rated in this skill.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                         ← cross-tool instructions (also Cursor / Claude Code)
├── GEMINI.md                         ← Antigravity-specific (HIGHER precedence than AGENTS.md)
└── .agents/
    ├── rules/    *.md                ← Manual | Always On | Model Decision | Glob (≤12,000 chars)
    ├── skills/   <name>/SKILL.md     ← Agent Skills (Anthropic standard) [path pin via install test]
    └── hooks.json                    ← lifecycle hooks (workspace)
.antigravity/
    └── mcp.json                      ← MCP { "mcpServers": { ... } } (project-local)

~/.gemini/                            ← user-global (Gemini-namespaced)
├── GEMINI.md  ·  AGENTS.md           ← global rules (AGENTS.md cross-tool, v1.20.3+)
├── config/                           ← global hooks.json customization dir
└── antigravity/
    ├── skills/                       ← global Agent Skills
    ├── mcp_config.json               ← global MCP config
    └── global_workflows/             ← saved-prompt Workflows (slash commands, /)
```

Precedence: **System Rules** (immutable, DeepMind) > **`GEMINI.md`** > **`AGENTS.md`**. gald3r
already generates `AGENTS.md` → **baseline integration works as-is on Antigravity.**

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `AGENTS.md` + `g-skl-*/SKILL.md`** — Antigravity reads
the instruction file and discovers Anthropic-format skills natively. Put **Antigravity-only must-win
directives in `GEMINI.md`** (it outranks `AGENTS.md`). Map `@g-*` commands to **Workflows**, `g-rl-*`
to **Always On** / **Model Decision** rules, and wire `g-hk-*.ps1` via `hooks.json`
(`before_model_call` ≈ session-start, `on_loop_stop` ≈ stop, `before_tool_call` ≈ pre-tool guard).
Fold `g-agnt-*` into rules/skills — subagents are **dynamic** (no file-based role discovery).

### Verify
```powershell
Test-Path AGENTS.md                                    # instruction file Antigravity reads
Test-Path .antigravity/mcp.json                        # project MCP (or ~/.gemini/antigravity/mcp_config.json)
Test-Path .agents/hooks.json                           # lifecycle hooks
Test-Path .agents/skills ; Test-Path .antigravity/skills ; Test-Path .agent/skills   # pin which path is live
```

## 4. Common Pitfalls

- **Wrong instruction file**: Antigravity reads `AGENTS.md` + `GEMINI.md` — **not** `CLAUDE.md`. For
  Antigravity-only overrides use `GEMINI.md` (outranks `AGENTS.md`).
- **Agents don't auto-map**: subagents are **dynamic** (Orchestrator-spawned). There is **no**
  honored `.agents/agents/` dir for `g-agnt-*.md` — fold agent guidance into rules/skills.
- **Managed Agents ≠ harness**: don't rate hooks/subagents from the hosted Gemini API surface.
- **Skill dir not canonical**: `.agents/skills` vs `.antigravity/skills` vs `.agent/skills` — pin via
  install test before hard-coding.
- **Hooks are shell scripts**: official examples are `.sh`; wire `g-hk-*.ps1` via
  `{ "type":"command", "command":"powershell -File …" }`; **pin payload schema** via install test.
- **File-size caps**: rule and workflow files are limited to **12,000 chars** each.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `hooks.json`; before/after_tool_call, before/after_model_call, on_loop_stop, on_error; stdin/stdout JSON; shell (`.ps1` via `powershell -File`) |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Anthropic `SKILL.md` standard; `.agents`/`.antigravity`/`.agent` skills dirs (pin path) + `~/.gemini/antigravity/skills/` |
| Agents (`g-agnt-*.md`) | ✅ / ⚠️ | ✅ native **dynamic** subagents (Orchestrator); ⚠️ **no** file-based `g-agnt-*.md` discovery — fold into rules/skills |
| Commands (`@g-*`) | ✅ | Workflows `/workflow-name`; title/description/steps; `~/.gemini/antigravity/global_workflows/`; ≤12,000 chars |
| Rules (`g-rl-*`) | ✅ | Markdown; Manual / Always On / Model Decision / Glob; `.agents/rules/` + `GEMINI.md`; reads `AGENTS.md` |
| MCP | ✅ | `.antigravity/mcp.json` / `~/.gemini/antigravity/mcp_config.json`; MCP Store GUI |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs antigravity` (`crawl_max_age_days: 7`).
