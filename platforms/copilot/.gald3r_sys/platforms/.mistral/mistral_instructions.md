# Mistral Vibe CLI Platform — gald3r Configuration Guide

**Platform**: Mistral Vibe CLI (open-source terminal coding agent; Devstral 2 / Codestral)
**Config surface**: `.vibe/` directory + `config.toml` (TOML) + `AGENTS.md`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.mistral.ai/mistral-vibe/terminal/configuration
**Authoritative skill**: `g-skl-platform-mistral`
**Authoritative capability + gap analysis**: `PLATFORM_SPEC.md` (this directory) — read first.

> "Mistral" is three products. Only **Mistral Vibe CLI** reads project config files.
> Mistral Code (closed IDE plugin) and Le Chat (web chat, MCP connectors only) are NOT
> gald3r config targets. See `PLATFORM_SPEC.md` for the full breakdown.

---

## Folder Layout (Mistral Vibe CLI)

Vibe reads config from a **`.vibe/`** directory (user-global `~/.vibe/` and project-scoped),
plus a layered `AGENTS.md`. Project config overlays user config (closer paths override).

```
<project-root>/
├── AGENTS.md                  # project instructions (gald3r's primary instruction file)
└── .vibe/
    ├── config.toml            # main config (models, providers, tools, MCP servers) — TOML
    ├── skills/<name>/SKILL.md # project skills (Agent Skills spec)
    ├── agents/<name>.toml     # custom agent / subagent profiles (TOML behavior profiles)
    └── prompts/<id>.md        # custom system prompts (referenced by system_prompt_id)
```

User-global equivalents live under `~/.vibe/` (with `.env` for credentials and
`trusted_folders.toml` for the trusted-execution allowlist).

**Correction vs. prior gald3r scaffold**: there is **no** `.mistral/` config folder, **no**
`config.yaml`, and **no** `mistral.yaml`. The previous scaffold described a fabricated
`.mistral/config.yaml` YAML scheme. The real surface is **TOML** under `.vibe/`. The fabricated
`config.yaml` has been removed (T1503).

---

## Capability Notes (honest — see PLATFORM_SPEC.md §3–§9)

| Component | Mistral Vibe reality |
|-----------|----------------------|
| Instructions | `AGENTS.md` — consumed directly, no transformation (strongest parity ✅) |
| Skills | ✅ native Agent Skills spec — `.vibe/skills/<name>/SKILL.md`; gald3r frontmatter needs light adaptation (`allowed-tools` / `user-invocable`) |
| Agents | Native, but TOML behavior profiles (`.vibe/agents/<name>.toml`) — not gald3r's markdown `g-agnt-*.md`; no auto-conversion ⚠️ |
| Commands | Slash commands exist but only via the skill mechanism — no flat command-file directory ⚠️ |
| Rules | `AGENTS.md` injection only — no scoped `.mdc`-style glob rules ⚠️ |
| Hooks | Docs reference `.vibe/` "hooks" but publish no event schema — gald3r `g-hk-*.ps1` cannot be wired ⚠️ |
| MCP | ✅ `.vibe/config.toml` `[[mcp_servers]]` (TOML) |

---

## MCP (Vibe CLI)

Configured in `.vibe/config.toml`. Do NOT place API keys inline — use environment variables.

```toml
[[mcp_servers]]
name = "my_http_server"
transport = "http"
url = "http://localhost:8000"
api_key_env = "MY_API_KEY_ENV_VAR"
startup_timeout_sec = 15
tool_timeout_sec = 120
```

`enabled_tools` / `disabled_tools` gate MCP-provided tools (e.g. `disabled_tools = ["mcp_*"]`).
(Le Chat MCP connectors are a separate product surface, not a gald3r file target.)

---

## gitignore Decision

`AGENTS.md` and committed `.vibe/` config are **source** — keep them tracked. Never commit API
keys; use `~/.vibe/.env` or environment variables (kept out of version control).

---

## Verification

```powershell
Test-Path .vibe
mistral-vibe --version
```

---

## Common Pitfalls

- The config surface is `.vibe/config.toml` (TOML) — NOT `.mistral/config.yaml` (YAML).
- Mistral Vibe is emerging — config conventions may change; verify against your version.
- The hook schema is unpublished — do not fabricate a `hooks.json` equivalent.
- Never commit API keys; use environment variables / `~/.vibe/.env`.
