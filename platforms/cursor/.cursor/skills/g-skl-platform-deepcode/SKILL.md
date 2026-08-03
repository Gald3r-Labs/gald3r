---
name: g-skl-platform-deepcode
description: Authoritative reference for Deep Code CLI (lessweb/deepcode-cli, a third-party community terminal AI coding assistant for the deepseek-v4 model family) customization in gald3r projects. Covers AGENTS.md, .agents/skills + .deepcode/skills Agent Skills, MCP inside .deepcode/settings.json, the fixed built-in slash-command set (no user commands), the absent hook/subagent surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/deepcode/
vault_docs_url: https://github.com/lessweb/deepcode-cli
docs_url: https://github.com/lessweb/deepcode-cli
docs_url_secondary:
  - https://raw.githubusercontent.com/lessweb/deepcode-cli/main/docs/mcp.md
  - https://raw.githubusercontent.com/lessweb/deepcode-cli/main/docs/configuration.md
  - https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode
last_doc_scan: 2026-07-18
capability_status:
  hooks: "❌ no lifecycle-hook framework; only a post-turn-only notify shell script in settings.json (cannot block tool calls)"
  rules: "✅ native — AGENTS.md, scaffolded via /init, the single instruction/rules surface (no .deepcode/rules/, no memory dir)"
  skills: "✅ native — Agent Skills (SKILL.md) discovered from .deepcode/skills/ (native) and .agents/skills/ (interop); gald3r targets .agents/skills/"
  commands: "⚠️ fixed built-in slash set only (/new /resume /continue /model /raw /init /skills /mcp /undo /exit); no user-defined command directory"
  agents: "❌ single AI assistant; no sub-agents, agent roles, or distinct agent modes documented"
  mcp: "✅ native — mcpServers object inside settings.json (no standalone .mcp.json); inspect via /mcp"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# g-skl-platform-deepcode

Activate for: setting up gald3r with Deep Code CLI (`lessweb/deepcode-cli`), shipping Agent
Skills, priming `AGENTS.md`, configuring MCP inside `settings.json`, or verifying the Deep Code
gald3r install.

---

> Full 8-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️
> partial parity** — Deep Code natively supports **rules** (`AGENTS.md`), **skills** (Agent
> Skills), and **MCP** (`mcpServers` in `settings.json`); **partial commands** (fixed built-in
> slash set only); **no subagents and no lifecycle hooks**. A real, actively-maintained
> **third-party community** CLI (kept per owner directive: "if it can be made to work, keep"),
> not a doc-only or nonexistent project. (Live-verified 2026-07-18, cross-checked against an
> independent 2026-06-02 scan — the two agree on every capability cell.)

## 1. Platform Overview

**Deep Code** (`@vegamo/deepcode-cli` on npm, `lessweb/deepcode-cli` on GitHub) is a third-party
terminal AI coding assistant optimized for the `deepseek-v4` model family. DeepSeek's own docs
list it under "Agent Integrations" with an explicit third-party disclaimer. It operates as a
**single AI assistant** — no subagents — with a config surface shared between the CLI and the
Deep Code VS Code extension.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                        ← instruction file (scaffolded via /init)
├── .agents/skills/ <name>/SKILL.md  ← Agent Skills (cross-client interop path — gald3r target)
└── .deepcode/
    ├── settings.json                ← model/env + mcpServers + notify (post-turn callback only)
    └── skills/  <name>/SKILL.md     ← Deep Code's own native project skills path

~/.deepcode/settings.json            ← global config, SHARED with the Deep Code VS Code extension
~/.agents/skills/ <name>/SKILL.md    ← user-global Agent Skills (interop path)
```

Settings-file scope layering is field-by-field (project overrides user field-by-field, not a
whole-file replace) — a project `settings.json` containing only `mcpServers` is valid.

## 3. gald3r Integration

Ship gald3r's **`AGENTS.md`** + **`.agents/skills/<name>/SKILL.md`** tree — Deep Code discovers
both natively today. Surface gald3r commands **as skills** (invocable via the `/` picker) since
there is no custom-command directory. Configure MCP via `mcpServers` inside
`.deepcode/settings.json` — remember it also applies to the shared VS Code surface.

```bash
gald3r platform install deepcode --into <target-dir>
```

### Verify
```powershell
Test-Path AGENTS.md ; Test-Path .agents/skills
Select-String 'mcpServers' .deepcode/settings.json
```

## 4. Common Pitfalls

- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** — the single rules/instruction surface,
  scaffolded via `/init`; no `.deepcode/rules/`, no `.mdc` files, no separate memory store.
- **No custom commands** — only a fixed built-in slash set; there is no `.deepcode/commands/`
  (or equivalent) directory. Map gald3r `@g-*`/`/g-*` commands to Skills instead.
- **No lifecycle hooks** — the only automation is a post-turn-only `notify` shell script
  (`settings.json`); it cannot block tool calls, inject session-start context, or gate commits.
- **No subagents** — a single AI assistant; fold agent behavior into `AGENTS.md` or per-skill
  `SKILL.md` context instead of `g-agnt-*` files.
- **MCP config is field-layered inside `settings.json`**, not a standalone `.mcp.json` — the
  prior generator path (`.deepcode/.mcp.json`) was a dead file Deep Code never read (T387 fix).

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ❌ | No lifecycle-hook framework; `notify` is post-turn-only, cannot block |
| Skills (`g-skl-*/SKILL.md`) | ✅ | `.deepcode/skills/` (native) + `.agents/skills/` (interop, gald3r target) |
| Agents (`g-agnt-*.md`) | ❌ | Single AI assistant; no sub-agents/roles/modes documented |
| Commands (`@g-*`) | ⚠️ | Fixed built-in slash set only; no user-defined command directory — map to Skills |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md`, scaffolded via `/init`; single instruction surface |
| MCP | ✅ | `mcpServers` object inside `.deepcode/settings.json` (no standalone `.mcp.json`); `/mcp` to inspect |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next
`@g-platform-scan-docs deepcode` (crawl_max_age_days: 14).
