---
name: g-skl-platform-mistral
description: Authoritative reference for Mistral Vibe CLI (mistral-vibe) coding agent customization in gald3r projects. Covers the .vibe/ config tree (TOML), AGENTS.md instructions, native Agent-Skills SKILL.md, native custom agents + subagents, MCP servers, experimental hooks, and honest capability boundaries.
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
vault_docs_url: https://docs.mistral.ai/mistral-vibe/terminal
docs_url: https://docs.mistral.ai/mistral-vibe/terminal
docs_url_secondary:
  - https://docs.mistral.ai/vibe/code/cli/configuration
  - https://docs.mistral.ai/vibe/code/cli/skills
  - https://docs.mistral.ai/vibe/code/cli/agents
  - https://docs.mistral.ai/vibe/code/cli/mcp-servers
  - https://github.com/mistralai/mistral-vibe
last_doc_scan: 2026-06-02
capability_status:
  hooks: "⚠️ experimental post-agent-turn lifecycle only (v2.9.0); no schema/file location; no pre-tool/session-start/pre-commit — cannot wire gald3r hooks"
  rules: "⚠️ AGENTS.md layered injection (+ optional custom system prompt via prompts/<id>.md); no scoped .mdc/glob rule system"
  skills: "✅ native Agent Skills (agentskills.io SKILL.md) in ~/.vibe/skills, ./.vibe/skills, ./.agents/skills + skill_paths"
  commands: "⚠️ slash commands only via skills (user-invocable: true → /skill-name); no command-file directory"
  agents: "✅ native custom agents + subagents (.vibe/agents/*.toml; vibe --agent; agent_type=subagent)"
  mcp: "✅ native — config.toml [[mcp_servers]] (http/streamable-http/stdio); no OAuth yet"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-mistral

Activate for: setting up gald3r with Mistral Vibe CLI (`mistral-vibe`), authoring Mistral project
instructions / skills / agents, or verifying the Mistral gald3r integration.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️ partial
> parity.** Native: **skills, agents/subagents, MCP**. Partial: **hooks** (experimental post-agent-turn
> only), **rules** (`AGENTS.md` injection, no `.mdc` scoping), **commands** (skill-provided only).
> Vibe reads **`AGENTS.md`** (NOT `CLAUDE.md`); config is **TOML** under `.vibe/` (no `.mistral/`, no
> YAML). (Verified 2026-06-02 against docs.mistral.ai + github.com/mistralai/mistral-vibe; latest
> observed v2.13.0.)

## 1. Platform Overview

"Mistral" coding is **three products** — gald3r targets only the config-driven one:

| Surface | What it is | gald3r config target? |
|---|---|---|
| **Mistral Vibe CLI** | Open-source terminal coding agent (`mistral-vibe`) | ✅ Yes — reads `.vibe/` + `AGENTS.md` |
| **Mistral Code** | JetBrains/VSCode IDE plugin (enterprise bundle) | ❌ Closed plugin; no config files |
| **Le Chat** | Web/app chat with MCP connectors + memories | ❌ Not a file-config surface |

- **Config root**: `.vibe/` (user `~/.vibe/`, project `./.vibe/`) — **TOML**, not YAML. There is **no
  `.mistral/` directory**.
- **Instructions**: **`AGENTS.md`** (the same cross-platform standard gald3r already uses) — **not
  `CLAUDE.md`**.
- **Trusted-folders gate**: project `.vibe/` config loads only when the working directory is trusted
  (`trusted_folders.toml`).

## 2. Config Layout

```
~/.vibe/                       ← user-global
├── config.toml                ← models, providers, tools, [[mcp_servers]], enabled_skills (TOML)
├── .env                       ← API keys
├── AGENTS.md                  ← user-level instructions
├── agents/<name>.toml         ← custom agent / subagent profiles (TOML)
├── prompts/<id>.md            ← custom system prompts (system_prompt_id)
└── skills/<name>/SKILL.md     ← user-level skills (agentskills.io)

<project-root>/
├── AGENTS.md                  ← project instructions (override user-level; closer files win)
└── .vibe/
    ├── config.toml            ← project overlay
    ├── skills/<name>/SKILL.md ← project skills (also ./.agents/skills/)
    ├── agents/<name>.toml     ← project agent / subagent profiles
    └── prompts/<id>.md
```

Resolution: project paths layer over user paths; files closer to the working directory win. Project
`.vibe/` loads **only in trusted folders**.

## 3. gald3r Integration

**Cheapest high-value install: ship gald3r's `AGENTS.md`** — Vibe consumes it directly with no
transformation. gald3r skills (`g-skl-*/SKILL.md`) load natively (agentskills.io); native agents/
subagents exist but need markdown→TOML conversion.

```markdown
# AGENTS.md (gald3r section)

## Task Workflow
Before any implementation:
1. Read .gald3r/TASKS.md for active tasks
2. Read .gald3r/tasks/task{id}_*.md for task details
3. Check .gald3r/CONSTRAINTS.md for architectural limits

## Commit Format
feat(T{id}): description
fix(BUG-{id}): description

## Bug Discovery
Pre-existing bugs: document in .gald3r/BUGS.md — never silently ignore.
```

MCP servers (optional) go in `.vibe/config.toml`:

```toml
[[mcp_servers]]
name = "my_http_server"
transport = "http"             # http | streamable-http | stdio
url = "http://localhost:8000"
startup_timeout_sec = 15
tool_timeout_sec = 120
```

> The parity pipeline (`platform_parity_sync.ps1`) does **not** currently write `.vibe/`. There is no
> automated Mistral install path yet — integration is manual `AGENTS.md` authoring today.

### Verify
```powershell
Test-Path AGENTS.md
Test-Path .vibe
mistral-vibe --version    # or: vibe --version  (confirm CLI install)
```

## 4. Common Pitfalls

- Vibe reads **`AGENTS.md`**, NOT `CLAUDE.md`. Config is **`.vibe/config.toml` (TOML)**, NOT
  `.mistral/config.yaml` (that path is fictional).
- "Mistral Code" (IDE plugin) and "Le Chat" do not read these files — only **Vibe CLI** does.
- Project `.vibe/` config (skills/agents/prompts/hooks) loads **only in trusted folders**
  (`trusted_folders.toml`).
- Slash commands are **skill-provided only** (`user-invocable: true`) — there is no command-file
  directory like `.cursor/commands/`.
- Vibe skill frontmatter expects `allowed-tools` / `user-invocable`; gald3r skills emit
  `subsystem_memberships` / `token_budget` (unknown keys ignored — light adaptation).
- Keep API keys in `~/.vibe/.env` / environment variables, never in committed `config.toml`.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Skills (`g-skl-*/SKILL.md`) | ✅ | native agentskills.io; `~/.vibe/skills`, `./.vibe/skills`, `./.agents/skills`, `skill_paths` |
| Agents (`g-agnt-*.md`) | ✅ | native custom agents + subagents `.vibe/agents/*.toml` (`vibe --agent`; `agent_type=subagent`); **needs md→TOML port** |
| MCP | ✅ | `config.toml` `[[mcp_servers]]` (http / streamable-http / stdio); namespaced `{server}_{tool}`; no OAuth yet |
| Hooks (`g-hk-*.ps1`) | ⚠️ | experimental **post-agent-turn** only (v2.9.0); no schema/file location; no pre-tool/session-start/pre-commit |
| Rules (`g-rl-*`) | ⚠️ | `AGENTS.md` layered injection (+ optional custom system prompt); no scoped `.mdc`/glob rules |
| Commands (`@g-*`) | ⚠️ | slash commands only via skills (`user-invocable: true` → `/skill-name`); no command-file dir |

## 6. Known Gaps

> **Ground-truth hook events (T1538/T1554):** mistral ships an **experimental `.vibe/` hook surface**
> (Type: `experimental`) — a single **post-agent-turn** lifecycle point (v2.9.0, 2026-04-28) — but
> publishes **no event list, file location, or schema**, so the wiring is undocumented. The
> authoritative, machine-readable statement of this — the (currently undocumented) event list and how
> gald3r hook behaviors must run until it is verified (manually, via rules text, or via git
> `core.hooksPath`) — lives in [`PLATFORM_SPEC.md` -> `## Hook System`](./PLATFORM_SPEC.md). Reference
> that block rather than re-listing hook details here. The gald3r `g-hk-*.ps1` wiring for mistral is
> **[STUB] / unverified** — do not fabricate an event-to-hook mapping.
> **Last verified against platform version:** mistral v2.13.0 (docs crawl `last_doc_scan: 2026-06-02`).
> Re-verify the event names in `PLATFORM_SPEC.md` `## Hook System` on the next
> `@g-platform-scan-docs mistral`.

Honest boundaries vs. the Cursor reference (full detail in `PLATFORM_SPEC.md` §1–§9):

- **Hooks ⚠️**: experimental **post-agent-turn** lifecycle only (v2.9.0); no published event list or
  schema, and no pre-tool/session-start/pre-commit — gald3r's `g-hk-*.ps1` + `hooks.json` cannot be
  ported until Mistral documents the format. (issue #250 CLOSED unimplemented; #531 OPEN)
- **Rules ⚠️**: no `.mdc` scoped-rule system; gald3r's `g-rl-*` rules collapse into a single
  `AGENTS.md` blob (no `globs`, no per-rule on-demand loading); optional custom system prompt via
  `prompts/<id>.md` + `system_prompt_id`.
- **Commands ⚠️**: slash commands are **skill-provided only** (`user-invocable: true`) — no command-file
  directory like `.cursor/commands/`; gald3r's command files have no native landing zone.
- **Agents ✅ (with caveat)**: native custom agents + subagents, but Vibe agents are **TOML behavior
  profiles**, not gald3r's markdown agents — a port needs markdown→TOML conversion; `safety` is
  visual-only (not enforcement).
- **Skills ✅ (with caveat)**: native Agent Skills spec + folder-per-skill `SKILL.md` matches, but Vibe
  expects `allowed-tools` / `user-invocable` keys gald3r skills don't emit (light adaptation).
- **MCP ✅ (with caveat)**: native `[[mcp_servers]]`, but the CLI does **not yet support OAuth** MCP
  servers.
- **No install automation**: `platform_parity_sync.ps1` has no `.vibe/` writer — future work.
