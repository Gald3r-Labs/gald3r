---
name: g-skl-platform-mistral
description: Authoritative reference for Mistral Vibe CLI coding agent customization in gald3r projects. Covers the .vibe/ config tree, AGENTS.md instructions, Agent-Skills SKILL.md, MCP servers, and honest capability boundaries.
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
docs_url: https://docs.mistral.ai/mistral-vibe/terminal
vault_docs_url: https://docs.mistral.ai/mistral-vibe/terminal
last_doc_scan: 2026-05-26
capability_status:
  hooks: partial      # docs reference .vibe/ hooks but publish no schema — cannot wire gald3r hooks
  rules: partial      # AGENTS.md injection only; no scoped .mdc rule system
  skills: full        # native Agent Skills spec, folder-per-skill SKILL.md (frontmatter needs light adaptation)
  commands: partial   # slash commands exist but only via the skill mechanism; no command-file dir
  mcp: full           # .vibe/config.toml [[mcp_servers]] (Vibe CLI)
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-mistral

Activate for: setting up gald3r with Mistral Vibe CLI, authoring Mistral project instructions, or
verifying Mistral gald3r integration.

> Full capability breakdown: see `PLATFORM_SPEC.md` in this folder (9 verified sections).

---

## 1. Platform Overview

"Mistral" coding is **three products** — gald3r targets only the config-driven one:

| Surface | What it is | gald3r config target? |
|---|---|---|
| **Mistral Vibe CLI** | Open-source terminal coding agent (`mistral-vibe`, Devstral 2 / Codestral) | ✅ Yes — reads `.vibe/` + `AGENTS.md` |
| **Mistral Code** | JetBrains/VSCode IDE plugin (enterprise bundle) | ❌ Closed plugin; no config files |
| **Le Chat** | Web/app chat with MCP connectors + memories | ⚠️ MCP connectors only; not files |

- **Config root**: `.vibe/` directory (user `~/.vibe/`, project `./.vibe/`) — **TOML**, not YAML.
- **Instructions**: `AGENTS.md` (the same cross-platform standard gald3r already uses).
- **Models**: Devstral 2 (default), Codestral (FIM/completion), via providers in `config.toml`.

> **Correction (T1478)**: an earlier version of this skill described a `.mistral/config.yaml`
> scheme. That was **fabricated** — it does not exist. The real surface is `.vibe/config.toml`.

---

## 2. Config File Layout

```
~/.vibe/                      ← user-global
├── config.toml               ← models, providers, tools, [[mcp_servers]], enabled_skills
├── .env                      ← API keys
├── AGENTS.md                 ← user-level instructions
├── agents/<name>.toml        ← custom agent / subagent profiles
├── prompts/<id>.md           ← custom system prompts (system_prompt_id)
└── skills/<name>/SKILL.md    ← user-level skills

<project-root>/
├── AGENTS.md                 ← project instructions (override user-level)
└── .vibe/
    ├── config.toml           ← project overlay
    ├── skills/<name>/SKILL.md ← project skills
    ├── agents/<name>.toml    ← project agent profiles
    └── prompts/<id>.md
```

Resolution: project paths layer over user paths; files closer to the working directory win.

---

## 3. gald3r Integration

The strongest fit is **`AGENTS.md`** — gald3r already generates it, and Vibe consumes it directly
with no transformation. Recommended minimal install footprint:

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
transport = "http"
url = "http://localhost:8000"
startup_timeout_sec = 15
tool_timeout_sec = 120
```

> The parity pipeline (`platform_parity_sync.ps1`) does **not** currently write `.vibe/`. There is
> no automated Mistral install path yet — integration is manual `AGENTS.md` authoring today.

---

## 4. Verification

```powershell
Test-Path .vibe
Test-Path AGENTS.md
mistral-vibe --version    # or: vibe --version  (confirm CLI install)
```

---

## 5. Common Pitfalls

- Config is **`.vibe/config.toml` (TOML)**, NOT `.mistral/config.yaml` (that path is fictional).
- "Mistral Code" (IDE plugin) and "Le Chat" do not read these files — only **Vibe CLI** does.
- Codestral uses a separate API endpoint (codestral.mistral.ai) vs general Mistral API.
- Keep API keys in `~/.vibe/.env` / environment variables, never in committed `config.toml`.

---

## 6. Known Gaps

Honest boundaries vs. the Cursor reference (full detail in `PLATFORM_SPEC.md` §9):

- **Hooks ⚠️**: docs say `.vibe/` "contributes hooks" but publish **no event list or schema** —
  gald3r's `g-hk-*.ps1` + `hooks.json` cannot be ported until Mistral documents the format.
- **Rules ⚠️**: no `.mdc` scoped-rule system; gald3r's 38 `g-rl-*` rules collapse into a single
  `AGENTS.md` blob (no `globs`, no per-rule on-demand loading).
- **Commands ⚠️**: slash commands are **skill-provided only** — there is no command-file
  directory like `.cursor/commands/`; gald3r's command files have no native landing zone.
- **Agents ⚠️**: Vibe agents are **TOML behavior profiles**, not gald3r's markdown agents; no
  automatic conversion.
- **Skills ✅ (with caveat)**: native Agent Skills spec + folder-per-skill `SKILL.md` matches, but
  Vibe expects `allowed-tools` / `user-invocable` keys gald3r skills don't emit (light adaptation).
- **No install automation**: `platform_parity_sync.ps1` has no `.vibe/` writer — future work.
