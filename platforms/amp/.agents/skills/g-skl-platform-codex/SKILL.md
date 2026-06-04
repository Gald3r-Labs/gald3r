---
name: g-skl-platform-codex
description: Authoritative reference for OpenAI Codex (codex CLI / IDE / app) customization in gald3r projects. Covers config.toml, AGENTS.md instruction file, .agents/skills Agent Skills, .codex/agents TOML subagents, 10-event hooks (hooks.json / [hooks]), [mcp_servers.*] MCP, execpolicy/Memories rules, plugins/apps, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/openai/
vault_docs_url: https://developers.openai.com/codex
docs_url: https://developers.openai.com/codex
docs_url_secondary:
  - https://developers.openai.com/codex/guides/agents-md
  - https://developers.openai.com/codex/hooks
  - https://developers.openai.com/codex/subagents
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/codex/cli/slash-commands
  - https://developers.openai.com/codex/mcp
  - https://developers.openai.com/codex/plugins
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks via hooks.json / [hooks] in config.toml (10 events: SessionStart…Stop; .ps1 via command handlers)"
  rules: "✅ AGENTS.md instruction hierarchy + Memories (~/.codex/memories/) + execpolicy hard allow/block"
  skills: "✅ Agent Skills (open SKILL.md standard) in .agents/skills + $HOME/.agents/skills"
  commands: "✅ ~40 built-in slash commands; user-defined via skills (Custom Prompts deprecated)"
  agents: "✅ native subagents .codex/agents/*.toml (parallel; explicit-spawn only; /agent)"
  mcp: "✅ native — [mcp_servers.<name>] in config.toml (stdio + HTTP); codex mcp add; /mcp"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-codex

Activate for: setting up gald3r with OpenAI Codex (codex CLI / IDE / app), authoring config.toml / AGENTS.md / skills / subagents / hooks / rules / MCP, or verifying the Codex gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Codex natively supports commands, rules, agents, skills, hooks (10 lifecycle events),
> and MCP, all driven by `config.toml`. Codex reads **`AGENTS.md` (NOT `CLAUDE.md`)** and discovers
> skills via the **open Agent Skills `SKILL.md` standard** (`.agents/skills/`), so gald3r's skill
> artifacts are directly portable. (Verified 2026-06-02 against https://developers.openai.com/codex.)

## 1. Platform Overview

**OpenAI Codex** — the **`codex` CLI**, an IDE integration, and a hosted app, all governed by a
single schema-validated **`config.toml`** (model, sandbox/approval, MCP, hooks, agents, skill
registration). The CLI is the full-extensibility surface; the IDE/app share the config plus an MCP
settings panel.

- **Model**: e.g. `model = "gpt-5-codex"` (OpenAI/o-series + other providers)
- **Approval policy** (`approval_policy`) + **sandbox** (`sandbox_mode`, e.g. `workspace-write`) gate execution; `execpolicy` adds hard allow/block
- **Instruction file**: **`AGENTS.md`** (NOT `CLAUDE.md`) — plus `AGENTS.override.md` / `TEAM_GUIDE.md` / `.agents.md` fallbacks and global `~/.codex/AGENTS.md`

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                     ← read by Codex (NOT CLAUDE.md); override/fallbacks too
├── .agents/
│   └── skills/  <name>/SKILL.md  ← Agent Skills (open standard, shared w/ Claude/others)
└── .codex/
    ├── config.toml               ← model, sandbox/approval, [mcp_servers.*], [hooks], [[skills.config]]
    ├── hooks.json                ← lifecycle hooks (or inline [hooks] in config.toml)
    ├── agents/   *.toml          ← subagents (standalone TOML)
    └── prompts/  *.md            ← Custom Prompts → slash commands (DEPRECATED; use skills)

~/.codex/{config.toml, AGENTS.md, agents/, memories/, prompts/}   ← global tree (merged below project)
$HOME/.agents/skills/                                             ← personal Agent Skills
```

Codex resolves **most-specific-wins** (project `.codex/` over `~/.codex/`; nested `AGENTS.md` over
root over global) → **gald3r's open-standard `.agents/skills/` tree works as-is on Codex.**

## 3. gald3r Integration

**Cheapest full-parity install: ship gald3r's `.agents/skills/g-skl-*/SKILL.md` (open standard) +
an `AGENTS.md`** — Codex loads both natively. Map `g-agnt-*` to `.codex/agents/*.toml`, wire
`g-hk-*.ps1` via `hooks.json`/`[hooks]` (10 events), declare MCP under `[mcp_servers.*]`, and fold
`g-rl-*` always-apply rules into `AGENTS.md` (hard guards optionally as `execpolicy` rules /
`PreToolUse` hooks). For user-defined `@g-*` workflows prefer **skills** (Custom Prompts are
deprecated). Bundle/distribute via **Codex Plugins** (`/plugins`).

### Verify
```powershell
Test-Path .codex/config.toml        # model, sandbox/approval, [mcp_servers.*], [hooks], [[skills.config]]
Test-Path AGENTS.md                 # instruction file (NOT CLAUDE.md)
Test-Path .agents/skills            # open-standard Agent Skills
Test-Path .codex/hooks.json         # or [hooks] inline in config.toml
codex --version                     # CLI installed
```

## 4. Common Pitfalls

- Instruction file is **`AGENTS.md`, not `CLAUDE.md`** — Codex does not read `CLAUDE.md`. Author the `AGENTS.md` form (override/fallbacks: `AGENTS.override.md`, `TEAM_GUIDE.md`, `.agents.md`).
- Subagents are **TOML** (`.codex/agents/*.toml`, keys `name`/`description`/`developer_instructions`), **not** markdown+YAML, and are **explicit-spawn only** (`/agent` or natural language) — never auto-spawned.
- **Custom Prompts (`~/.codex/prompts/`) are DEPRECATED** — use **skills** for reusable invocable workflows; built-in slash commands cover the rest.
- Hooks + MCP are **config-driven** (`hooks.json` / `[hooks]` and `[mcp_servers.*]` in `config.toml`), not standalone discovery folders. For `.ps1` handlers, shell `pwsh`/`powershell` in the hook `command`.
- Config is `.codex/config.toml` (TOML, schema-validated); project merges below `~/.codex/config.toml` most-specific-wins. The legacy `codex.config.json` + `suggest`/`auto-edit`/`full-auto` form is superseded.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `hooks.json` / `[hooks]` in config.toml; 10 events (SessionStart, SubagentStart, PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop) |
| Skills (`g-skl-*/SKILL.md`) | ✅ | open Agent Skills standard; discovered in `.agents/skills/` + `$HOME/.agents/skills/`; `/skills` or `$`-mention |
| Agents (`g-agnt-*`) | ✅ | native subagents `.codex/agents/*.toml` (parallel; explicit-spawn only; `/agent`) |
| Commands (`@g-*`) | ✅ | ~40 built-in slash commands; user-defined via skills (Custom Prompts deprecated) |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md` hierarchy + Memories (`~/.codex/memories/`) + execpolicy hard allow/block |
| MCP | ✅ | `[mcp_servers.<name>]` in config.toml (stdio + HTTP); `codex mcp add`; `/mcp` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs codex` (crawl_max_age_days: 7).
