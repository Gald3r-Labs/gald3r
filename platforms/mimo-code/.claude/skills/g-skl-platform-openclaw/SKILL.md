---
name: g-skl-platform-openclaw
description: Authoritative reference for OpenClaw (self-hosted AI agent gateway — Discord/Telegram/Slack/WhatsApp) customization in gald3r projects. Covers the AGENTS.md + SOUL.md instruction-file convention, folder-per-skill SKILL.md (which double as slash commands), TypeScript HOOK.md hooks, sessions_spawn sub-agents, native MCP client+server, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/openclaw/
vault_docs_url: https://docs.openclaw.ai
docs_url: https://docs.openclaw.ai
docs_url_secondary:
  - https://docs.openclaw.ai/concepts/agent-workspace
  - https://docs.openclaw.ai/tools/slash-commands
  - https://docs.openclaw.ai/tools/skills
  - https://docs.openclaw.ai/tools/subagents
  - https://docs.openclaw.ai/automation/hooks
  - https://docs.openclaw.ai/cli/mcp
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native event-driven hooks (HOOK.md + handler.ts, openclaw.json) — TypeScript handlers, OpenClaw event taxonomy; gald3r g-hk-*.py NOT drop-in (rewrite to handler.ts)"
  rules: "✅ AGENTS.md (operating rules) + SOUL.md (hard 'never do X') + MEMORY.md injected every session; prose-only, no .mdc typed rules"
  skills: "✅ Agent Skills (folder-per-skill SKILL.md) precedence-loaded; install to ~/.openclaw/workspace/skills/; skills double as slash commands"
  commands: "✅ user-invocable skills → /skill <name>; direct command registration; native Discord/Telegram registration (~v2026.2.23)"
  agents: "✅ per-persona agents via bindings + runtime sub-agents via sessions_spawn tool (maxSpawnDepth default 1; /subagents is inspect-only)"
  mcp: "✅ native client + server — mcp.servers in openclaw.json (openclaw mcp add/set/configure); stdio/HTTP-SSE/streamable-http; openclaw mcp serve"
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


# g-skl-platform-openclaw

Activate for: setting up gald3r with OpenClaw, authoring `AGENTS.md` / `SOUL.md`, understanding
OpenClaw's folder-per-skill + slash-command + TypeScript-hook surface, or verifying the OpenClaw
gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — OpenClaw natively supports commands, rules, agents, skills, hooks, and MCP (client +
> server), and reads `AGENTS.md` + `SOUL.md`, so gald3r's `AGENTS.md` + `g-skl-*/SKILL.md` artifacts
> are largely reusable. The one real porting cost is **hooks** (`.py` → `handler.ts`). (Verified
> 2026-06-02 against https://docs.openclaw.ai; supersedes the prior `last_doc_scan: never` /
> `status: ⚠️` assessment.)

## 1. Platform Overview

**OpenClaw** — an open-source, self-hosted **AI agent gateway** oriented around chat channels
(Discord / Telegram / Slack / WhatsApp), not an in-editor IDE coding agent. It runs as a **gateway**
process out of a per-user file **workspace** (default `~/.openclaw/workspace`), with config at
`~/.openclaw/openclaw.json`. Despite a sparse landing page, the docs expose a deep file-based
extensibility surface: SKILL.md Agent Skills (which double as slash commands), TypeScript HOOK.md
lifecycle hooks, native MCP client + server, sub-agents via `sessions_spawn`, and a layered
instruction-file convention (`AGENTS.md` + `SOUL.md` + memory files).

## 2. Config Layout

```
~/.openclaw/
├── openclaw.json                  ← primary config (mcp.servers, bindings, hooks, model registry)
└── workspace/                     ← agent workspace (per-persona scope)
    ├── AGENTS.md                  ← primary operating contract (loaded every session)
    ├── SOUL.md                    ← persona / voice / hard "never do X" rules
    ├── TOOLS.md / IDENTITY.md / USER.md / HEARTBEAT.md / MEMORY.md   ← workspace files (all load)
    ├── memory/   YYYY-MM-DD-HHMM.md  ← auto-written by session-memory hook on /new, /reset
    ├── skills/   <name>/SKILL.md  ← Agent Skills (folder-per-skill; double as /skill <name>)
    └── hooks/    <name>/HOOK.md + handler.ts   ← event-driven TypeScript hooks
```

Skills are **precedence-loaded** (workspace > `.agents/skills` > `~/.agents/skills` >
`~/.openclaw/skills` > bundled > plugin; highest source wins on a name collision). There is **no
documented project-local `.openclaw/`** — point the workspace at the repo or install gald3r skills
into the workspace `skills/` dir.

## 3. gald3r Integration

**Cheapest high-parity install:** ship gald3r rule prose into **`AGENTS.md`** (operating rules) +
**`SOUL.md`** (hard guardrails) — both load every session — and install gald3r `g-skl-*/SKILL.md`
into the OpenClaw **workspace** `skills/` dir (folder-per-skill is identical to gald3r; each
`user-invocable` skill is automatically a `/skill <name>` slash command). Re-declare MCP servers via
`openclaw mcp set`. **Hooks need a TypeScript rewrite** (`handler.ts`) — gald3r's `.py` hooks
(`python <path>`) are not portable as-is.

### Verify
```powershell
Test-Path "$HOME/.openclaw/openclaw.json"                 # gateway config (mcp.servers, bindings, hooks)
Test-Path "$HOME/.openclaw/workspace/AGENTS.md"           # operating contract
Test-Path "$HOME/.openclaw/workspace/SOUL.md"             # persona + hard rules
Test-Path "$HOME/.openclaw/workspace/skills/g-skl-tasks/SKILL.md"   # a gald3r skill in the workspace
```

## 4. Common Pitfalls

- **Reads `AGENTS.md` + `SOUL.md`, NOT `CLAUDE.md`.** Put operating rules in `AGENTS.md`, hard
  "never do X" guardrails in `SOUL.md`. No `OPENCLAW.md` exists.
- **Hooks are TypeScript** (`HOOK.md` + `handler.ts`) with an OpenClaw event taxonomy
  (`gateway:startup` / `agent:bootstrap` / `command:new` / `session:compact:*` / `message:*`) — gald3r
  `g-hk-*.py` are **[STUB] / unverified**; rewrite to `handler.ts` (or shell out from one via
  `python <path>`). Do not fabricate an event→hook mapping.
- **Rules are prose, not typed.** No Cursor-style `rules/*.mdc` or per-glob scoping — fold `g-rl-*`
  into `AGENTS.md` / `SOUL.md`.
- **Skills install to the workspace** (`~/.openclaw/workspace/skills/`), not the repo root
  automatically — point the workspace at the repo or install into it.
- **Sub-agents spawn via the `sessions_spawn` tool**, not a file; `/subagents` is inspect-only;
  `maxSpawnDepth` defaults to **1** (recursive nesting gated).
- **MCP is centralized** in `openclaw.json` (`mcp.servers`); gald3r MCP defs are not auto-imported.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ✅ | native `HOOK.md` + `handler.ts` (TypeScript) in `openclaw.json`; events `command:*` / `session:compact:*` / `agent:bootstrap` / `gateway:*` / `message:*`; gald3r `.py` NOT drop-in — rewrite to `handler.ts` ([STUB]) |
| Skills (`g-skl-*/SKILL.md`) | ✅ | folder-per-skill `SKILL.md` (`name`+`description`); precedence-loaded; install to `~/.openclaw/workspace/skills/`; skills double as slash commands |
| Agents (`g-agnt-*.md`) | ✅ | per-persona agents via `bindings` + runtime sub-agents via `sessions_spawn` (`maxSpawnDepth` default 1; `/subagents` inspect-only) |
| Commands (`@g-*`) | ✅ | user-invocable skills → `/skill <name>`; direct command registration; native Discord/Telegram registration (~v2026.2.23); Lobster workflow pipelines |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md` + `SOUL.md` + `MEMORY.md` injected every session; prose-only (no `.mdc`); `session-memory` hook auto-persists last 15 msgs |
| MCP | ✅ | native client + server — `mcp.servers` in `openclaw.json` (`openclaw mcp add/set/configure`, `/mcp` UI); stdio / HTTP-SSE / streamable-http; `openclaw mcp serve` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs openclaw` (crawl_max_age_days: 14).
