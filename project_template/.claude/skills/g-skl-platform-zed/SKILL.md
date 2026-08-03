---
name: g-skl-platform-zed
description: Authoritative reference for Zed (agent panel + ACP host) customization in gald3r projects. Covers the .rules-first project-instructions precedence list, native AGENTS.md (project + personal ~/.config/zed/AGENTS.md), native Agent Skills (.agents/skills/, shared with Codex/Amp/Deep Code), native MCP (context_servers), External Agents hosted via the Agent Client Protocol (agent_servers), the absent hooks/commands surfaces, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/zed/
vault_docs_url: https://zed.dev/docs/ai/external-agents
docs_url: https://zed.dev/docs/ai/external-agents
docs_url_secondary:
  - https://zed.dev/docs/ai/agent-settings
  - https://zed.dev/docs/ai/instructions
  - https://zed.dev/docs/ai/skills
  - https://zed.dev/docs/ai/mcp
  - https://zed.dev/docs/ai/agent-panel
  - https://agents.md/
last_doc_scan: 2026-07-03
capability_status:
  hooks: "❌ no published event taxonomy/schema for hand-authored hooks (Tool Permissions/Agent Sandboxing are access-control, not an event bus)"
  rules: "✅ native AGENTS.md (project root + personal ~/.config/zed/AGENTS.md); .rules legacy filename outranks AGENTS.md if both exist"
  skills: "✅ native Agent Skills (SKILL.md) in .agents/skills/, name+description frontmatter, shared convention with Codex/Amp/Deep Code"
  commands: "❌ no dedicated user-authored slash-command file format; only built-in /compact documented — Skills fill the invocation role"
  agents: "❌ no project-scoped agent roster; Zed's own agent is Profile/UI-configured, third parties attach via ACP agent_servers"
  mcp: "✅ native MCP via context_servers in .zed/settings.json (local command/args/env or remote url/headers); forwarded to ACP External Agents too"
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

# g-skl-platform-zed

Activate for: setting up gald3r with Zed, authoring skills/AGENTS.md for Zed, or verifying the Zed
gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️
> partial parity** — Zed natively supports rules (`AGENTS.md`, project + personal scope), Agent
> Skills, and MCP. There is **no** project-scoped agent roster (Zed's own agent is Profile/UI-based;
> third-party agents attach as **External Agents** via the **Agent Client Protocol**), **no**
> dedicated custom-commands file format (Skills fill that role), and **no** published
> hooks/lifecycle-event system for hand-authored hooks. (Verified 2026-07-03 against
> https://zed.dev/docs/ai/external-agents and the Zed AI docs nav.)

## 1. Platform Overview

**Zed** (`zed.dev`) — a Rust-native, GPU-accelerated code editor. Its **Agent Panel** hosts Zed's
own built-in agent alongside **External Agents** (Claude Code, Kimi Code, Codex, Copilot, Cursor,
OpenCode, Pi Coding Agent, ...) attached via the open **Agent Client Protocol (ACP)** — making Zed
both an editor and a hosting/distribution surface for other vendors' coding agents. Zed is also a
native adopter of the open `AGENTS.md` instructions standard (https://agents.md/).

## 2. Config Layout

```
<project-root>/
├── .rules OR AGENTS.md              ← project instructions (.rules wins if BOTH exist)
└── .agents/
    └── skills/   <name>/SKILL.md    ← Agent Skills (name/description frontmatter + body)

~/.config/zed/AGENTS.md              ← personal/global instructions (Windows: %APPDATA%\Zed\AGENTS.md)
~/.agents/skills/  <name>/SKILL.md   ← user-global Agent Skills

(.zed/settings.json)                 ← Zed-owned: "agent_servers" (External ACP agents) +
                                        "context_servers" (MCP)
```

> **Correction (vs. naive assumption):** Zed does **not** simply read `AGENTS.md` — it picks the
> first match from a 9-entry fallback list where **`.rules` outranks `AGENTS.md`**. If a project
> already has a `.rules`/`.cursorrules`/`.windsurfrules`/`.clinerules` file from an older tool's
> setup, that file silently wins over gald3r's `AGENTS.md` until removed.

## 3. gald3r Integration

**Cheapest high-parity install:** ship `AGENTS.md` at the project root (Zed's natively-supported,
recommended format) plus the `.agents/skills/` tree for gald3r's `g-skl-*/SKILL.md` files (drop-in,
same convention already used for Codex/Amp/Deep Code — zero adaptation).

### Verify
```powershell
Test-Path AGENTS.md              # project instructions (check no higher-precedence .rules exists)
Test-Path .rules                 # if present, it OUTRANKS AGENTS.md — flag to the user
Test-Path .agents/skills         # Agent Skills tree
```

## 4. Common Pitfalls

- `.rules` **outranks** `AGENTS.md` in Zed's fixed fallback list — do not assume `AGENTS.md` is
  read if a legacy `.rules`/`.cursorrules`/`.windsurfrules`/`.clinerules` file is already present.
- The personal `~/.config/zed/AGENTS.md` (`%APPDATA%\Zed\AGENTS.md` on Windows) is **machine-global,
  not per-project** — gald3r does not write to it; document it as user-owned context.
- There is **no** project-scoped agent roster file — Zed's own agent is Settings/Profile-configured,
  and third-party agents attach via ACP (`agent_servers` in `.zed/settings.json`, itself Zed-owned).
  Do not fabricate an `agents/` folder Zed does not read.
- There is **no** dedicated custom-commands file format — only `/compact` is a documented built-in
  slash command. gald3r's `@g-*` commands ride entirely on the `.agents/skills/` tree instead.
- There is **no** documented hooks/lifecycle-event system for hand-authored hooks — do not fabricate
  a `hooks.json`/settings-driven hook file.
- `.zed/settings.json` is a **single Zed-owned file** carrying `agent_servers` + `context_servers` +
  every other editor setting — do not ship a full replacement; document the merge snippets instead
  (see `zed_instructions.md` in the `zed` platform overlay).
- Re-check on the next `@g-platform-scan-docs zed` (crawl_max_age_days: 14) — the ACP Registry and
  External Agents roster are actively expanding.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ❌ | no published event taxonomy/schema for hand-authored hooks; Tool Permissions/Agent Sandboxing are access-control, not an event bus |
| Skills (`g-skl-*/SKILL.md`) | ✅ | native Agent Skills in `.agents/skills/` (project) + `~/.agents/skills/` (global), `name`/`description` frontmatter, direct-children-only; same convention as Codex/Amp/Deep Code |
| Agents (`g-agnt-*.md`) | ❌ | no project-scoped agent roster; Zed's own agent is Profile/UI-configured, External Agents attach via ACP `agent_servers` |
| Commands (`@g-*`) | ❌ | no dedicated user-authored slash-command file format; only built-in `/compact` documented — Skills fill the invocation role |
| Rules (`g-rl-*`) | ✅ | native `AGENTS.md` (project root + personal `~/.config/zed/AGENTS.md`); `.rules` legacy filename outranks `AGENTS.md` if both exist |
| MCP | ✅ | native `context_servers` in `.zed/settings.json` (local `command`/`args`/`env` or remote `url`/`headers`); same servers forwarded to ACP-hosted External Agents |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs zed`
(crawl_max_age_days: 14).
