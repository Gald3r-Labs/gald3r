---
name: g-skl-platform-hermes
description: Authoritative reference for Hermes Agent (Nous Research — self-improving CLI + Telegram/Discord/Slack gateway) customization in gald3r projects. Covers ~/.hermes/ config (config.yaml/.env), AGENTS.md-native instruction loading (auto-injected with SOUL.md/CLAUDE.md/.cursorrules), agentskills.io SKILL.md skills (the gald3r distribution opportunity), delegate_task subagents, MCP (mcp_servers), the native config.yaml hooks: surface (17+ events, pre_tool_call blocking), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/hermes/
vault_docs_url: https://hermes-agent.nousresearch.com/docs
docs_url: https://hermes-agent.nousresearch.com/docs
docs_url_secondary:
  - https://hermes-agent.nousresearch.com/docs/user-guide/configuration
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
  - https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
  - https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
  - https://github.com/NousResearch/hermes-agent
last_doc_scan: 2026-06-20
capability_status:
  hooks: "✅ native — config.yaml hooks: shell-hook block (JSON-stdin, 17+ events incl. on_session_start/pre_tool_call); pre_tool_call blocks via {action:block}; non-blocking on hook error (verify firing)"
  rules: "✅ AGENTS.md + SOUL.md auto-injected into system prompt + ~/.hermes/memories/MEMORY.md + USER.md — advisory, hardenable via a pre_tool_call hook"
  skills: "✅ agentskills.io SKILL.md folder-per-skill in ~/.hermes/skills/<cat>/<name>/ — gald3r g-skl-* directly portable (only name+description required); distribute via taps"
  commands: "⚠️ partial — built-in slash commands + every skill is /skill-name; NO user command-file primitive"
  agents: "✅ native subagents via delegate_task (goal or batch tasks:[...]; delegation.max_concurrent_children/max_spawn_depth); no declared agent file → deliver g-agnt-* as Skills"
  mcp: "✅ native — mcp_servers: in ~/.hermes/config.yaml (stdio command/args/env OR HTTP url/headers; .[mcp] extra)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-hermes

Activate for: setting up gald3r with Hermes Agent (Nous Research CLI / gateway), authoring or porting skills onto Hermes, wiring MCP via `~/.hermes/config.yaml`, shipping `AGENTS.md` as the instruction surface, or verifying the Hermes gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — Hermes natively supports **Skills, Rules/memory, MCP, and Hooks** (plus `delegate_task`
> subagents and an **`AGENTS.md`-native** instruction file). **Commands are the only partial primitive**
> (skills-as-`/skill-name`, no command-file primitive). Headline: Hermes Skills use the
> **agentskills.io `SKILL.md` standard gald3r already ships**, so gald3r skills are **directly portable**
> — distribute them as a Hermes **tap**. (Re-verified 2026-06-20 against
> github.com/NousResearch/hermes-agent + hermes-agent.nousresearch.com/docs — corrects an earlier pass
> that wrongly marked Hooks absent.)

## 1. Platform Overview

**Hermes Agent** — Nous Research's self-improving, channel-native agent. A CLI plus a multi-platform
**gateway** (Telegram, Discord, Slack, WhatsApp, Signal, Email). Distinctive traits: an autonomous
learning loop that **writes its own skills** from experience, persistent cross-session memory, and
isolated **subagents** (the `delegate_task` model — single `goal` or batch `tasks:[...]`). All state
lives under **`~/.hermes/`** (`$HERMES_HOME`; `%LOCALAPPDATA%\hermes` on native Windows).

## 2. Config Layout

```
~/.hermes/                          ← all state (or $HERMES_HOME)
├── config.yaml                     ← settings: model, toolsets, memory, compression, mcp_servers:
├── .env                            ← secrets only (API keys, bot tokens)
├── auth.json                       ← OAuth provider creds
├── SOUL.md                         ← persona (system-prompt slot #1, auto-loaded)
├── memories/ MEMORY.md, USER.md    ← persistent memory (auto-loaded)
└── skills/ <category>/<name>/SKILL.md   ← Agent Skills (agentskills.io) → /<name>

<project-root>/
└── AGENTS.md                       ← auto-injected into system prompt (NATIVE; also .hermes.md/CLAUDE.md/.cursorrules)
```

No `.hermes/` **project** tree — config is user-global; project influence is via the auto-injected
context files only. Skills distribute as **taps** (`hermes skills publish` / `hermes skills tap add owner/repo`).

## 3. gald3r Integration

**Cheapest install: ship `AGENTS.md` + distribute gald3r skills as a Hermes tap.** Hermes auto-injects
`AGENTS.md` (no `CLAUDE.md` shim, no migration step) — fold `g-rl-*` rules into it. For **hard
enforcement**, wire `g-hk-*` logic into the `config.yaml` `hooks:` block: SessionStart `.gald3r/`
injection onto `on_session_start`, PreToolUse guardrails onto `pre_tool_call` (return
`{"action":"block",…}` to gate). Publish `g-skl-*/SKILL.md` to a repo and `hermes skills tap add <repo>`
— they index and surface as `/<name>` natively. Wire MCP via `mcp_servers:` in `~/.hermes/config.yaml`.
Optionally add a gald3r `SOUL.md` persona.

### Verify
```powershell
Test-Path $HOME/.hermes/config.yaml                          # main config (mcp_servers: AND hooks: live here)
Test-Path AGENTS.md                                          # auto-injected instruction surface
Test-Path $HOME/.hermes/skills                               # skills tree (g-skl-*/SKILL.md)
Test-Path $HOME/.hermes/SOUL.md                              # if shipping the gald3r persona
Select-String -Path $HOME/.hermes/config.yaml -Pattern '^hooks:'   # confirm the gald3r hooks: block is wired
# Confirm a gald3r skill resolves: run /skills in the Hermes CLI and look for the g-skl-* entries
```

## 4. Common Pitfalls

- **Hooks live in `config.yaml`, not a hooks dir** — `g-hk-*` logic wires into the `hooks:` block as
  shell commands (JSON-stdin); `pre_tool_call` can hard-**block** via `{"action":"block",…}`. Caveat:
  hook *failures* are swallowed (non-blocking-on-error), so enforce only via an explicit block action,
  and verify the hook actually fires (some builds report missed firings).
- **Instruction file is `AGENTS.md`-native** (auto-injected with `SOUL.md`/`CLAUDE.md`/`.cursorrules`).
  Ship `AGENTS.md`; do **not** assume a `.hermes/` project config tree exists.
- **Skills need only `name`+`description`** — `version`/`author`/`license`/`platforms`/`metadata.hermes.*`
  are **optional/recommended**; a baseline gald3r `SKILL.md` loads as-is (adding the three is
  distribution polish, not a requirement).
- **Commands = skills only** — there is no user-authored command-file primitive; every skill is a
  `/skill-name`. Distribute/update via taps, not a `.hermes/commands/` dir.
- **Subagents aren't declared** — spawned via `delegate_task` (`goal`/`tasks:[...]`), no `g-agnt-*`
  file mapping; deliver agent behaviors as **Skills**.
- **Gateway surfaces** — in Telegram/Discord/Slack prefer summarized status (or `--json`/`--toon`)
  over wide `TASKS.md` markdown tables (they truncate in chat).

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | native `config.yaml` `hooks:` shell hooks (JSON-stdin, 17+ events incl. `on_session_start`/`pre_tool_call`); `pre_tool_call` blocks via `{action:block}`; non-blocking on hook error |
| Skills (`g-skl-*/SKILL.md`) | ✅ | agentskills.io standard; `~/.hermes/skills/<cat>/<name>/SKILL.md`; `/skill-name`; **directly portable** (only `name`+`description` required) → distribute as a tap |
| Agents (`g-agnt-*`) | ✅ | native subagents via `delegate_task` (`goal`/batch `tasks:[...]`; `delegation.*` bounds); no declared agent file → deliver as Skills |
| Commands (`@g-*`) | ⚠️ | built-in slash set + every skill = `/skill-name`; **no command-file primitive** |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md` + `SOUL.md` auto-injected + `~/.hermes/memories/`; advisory, hardenable via a `pre_tool_call` hook |
| MCP | ✅ | `mcp_servers:` in `~/.hermes/config.yaml` (stdio `command`/`args`/`env` OR HTTP `url`/`headers`); `.[mcp]` extra |

**Distribution opportunity:** gald3r's `SKILL.md` artifacts are the **agentskills.io standard Hermes
uses** — publish them as a tap for native one-command install onto Hermes.

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs hermes`
(crawl_max_age_days: 14). Correct docs host: `hermes-agent.nousresearch.com/docs` +
`github.com/NousResearch/hermes-agent` (the prior `https://hermes.dev` stub URL was wrong).
