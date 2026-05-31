---
name: g-skl-platform-codex
description: Authoritative reference for OpenAI Codex CLI customization in gald3r projects. Covers .codex/ folder layout, config.toml, approval/sandbox policy, skills registration, MCP, and install verification.
docs_url: https://developers.openai.com/codex
docs_url_secondary: https://developers.openai.com/codex/config-schema.json
crawl_max_age_days: 7
vault_doc_path: research/platforms/openai/
vault_docs_url: https://developers.openai.com/codex
token_budget: low
capability_status:
  hooks: ❌          # no native lifecycle-event / hook system
  rules: ⚠️          # no rules folder; always-apply via root AGENTS.md
  skills: ⚠️         # supported but require explicit [[skills.config]] registration
  commands: ❌       # no slash/workflow command palette
  mcp: ⚠️            # protocol supported; exact config.toml table key unverified
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-codex

Activate for: setting up Codex CLI in a gald3r project, authoring `.codex/` configs, understanding approval modes, verifying Codex parity, or answering questions about Codex CLI's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://developers.openai.com/codex
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://developers.openai.com/codex
     (+ config schema https://developers.openai.com/codex/config-schema.json)
   → READ new vault notes at research/platforms/openai/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**Codex CLI** (`codex` command) is OpenAI's open-source terminal-based coding agent.
Config-file-centric: a single schema-validated `.codex/config.toml` drives model, sandbox,
approval policy, skill registration, and inline agent roles.

- **Model**: `model = "gpt-5-codex"` (configurable; OpenAI/o-series and other providers)
- **Approval policy** (`approval_policy`): e.g. `on-request` (asks before executing), plus
  more/less permissive policies per the config schema
- **Sandbox** (`sandbox_mode`): e.g. `workspace-write` (writes confined to the workspace);
  Windows uses `[windows] sandbox = "elevated"`
- **Features**: `[features] multi_agent`, `shell_tool`, `shell_snapshot`, `undo`
- **MCP**: declared in `config.toml` (exact table key per config-schema — verify before asserting)

> **Modern config note**: this skill targets `.codex/config.toml` (TOML, with
> `#:schema https://developers.openai.com/codex/config-schema.json`). Legacy gald3r notes
> referenced `codex.config.json` and `suggest`/`auto-edit`/`full-auto` mode names — those are
> superseded by `config.toml` + `approval_policy`/`sandbox_mode`.

**gald3r target**: config-heavy platform — skills (explicitly registered) + inline agent roles.
**No native rules directory. No commands folder. No hooks.** Always-apply enforcement lives in
the root `AGENTS.md`.

---

## 2. Folder Layout

```
.codex/                       ← Codex CLI config
├── config.toml               ← master config (model, sandbox, approval, [features],
│                                [[skills.config]] registrations, [agents.*] roles)
├── INSTALL.md                ← gald3r setup instructions (optional)
└── skills/                   ← skill folders; only registered paths are active
    └── g-skl-*/SKILL.md

AGENTS.md                     ← project ROOT (not in .codex/) — always-apply instructions
```

**No rules directory** — Codex uses root `AGENTS.md` for always-apply instructions; no `rules/` subfolder.
**No commands directory** — there is no slash-command palette; gald3r `g-*` workflows are delivered via skills + `AGENTS.md`.
**No agents directory** — agent roles are defined **inline** in `config.toml` under `[agents.*]`; `g-agnt-*.md` files do NOT auto-load.

**Skills**: registered explicitly in `config.toml` via `[[skills.config]]` blocks. Only paths that exist on disk should be registered (missing paths can cause startup errors). This repo registers the 17 gald3r core skills, not the full set.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `AGENTS.md` at project root | Markdown | ✅ Every session |
| Skills | `.codex/skills/g-skl-*/SKILL.md` | Markdown | ⚠️ Only if registered in `config.toml` `[[skills.config]]` |
| Agents | `config.toml` `[agents.*]` (inline) | TOML | ⚠️ Inline only — `g-agnt-*.md` files do not load |
| Commands | (none) | n/a | ❌ No command palette — use skills + `AGENTS.md` |
| MCP servers | `config.toml` (table key per config-schema) | TOML | ⚠️ Config-declared; exact key unverified |
| Hooks | Not supported | n/a | ❌ No lifecycle events |

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| skills/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| No rules dir | n/a | n/a | n/a |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/openai/
```

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Codex CLI docs (primary `docs_url`) | https://developers.openai.com/codex |
| Codex config schema | https://developers.openai.com/codex/config-schema.json |
| Codex CLI repo | https://github.com/openai/codex |

---

## 9. Common Pitfalls

1. **No rules directory** — Codex has no `.codex/rules/` folder. Always-apply rules go in root `AGENTS.md`. Parity sync skips rules for `.codex/` (RulesExt is null).
2. **Skills must be REGISTERED** — Codex does not auto-discover skill folders. Each skill needs a `[[skills.config]]` block in `config.toml` with `enabled = true`. Register only paths that exist on disk — a missing registered path can cause a startup error.
3. **No hook system** — gald3r's PowerShell session-start / inbox / pre-commit hooks do NOT auto-fire on Codex. Their logic must be invoked manually or restated in `AGENTS.md`. Shell execution is gated by `approval_policy` (e.g. `on-request`) + `sandbox_mode` (e.g. `workspace-write`), not by hooks.
4. **No command palette** — there is no `@g-*` / `/g-*` system. Describe intent in natural language; Codex matches it to a registered skill.
5. **Config file is `config.toml`** — project config at `.codex/config.toml`, optional user-level at `~/.codex/config.toml`. TOML, schema-validated against `https://developers.openai.com/codex/config-schema.json`. The legacy `codex.config.json` + `mcpServers`-JSON form is superseded. ❓ Confirm the exact MCP table key in `config.toml` against the config schema before declaring servers.

---

## 10. Install Verification Checklist

```
✅ .codex/config.toml exists (model, sandbox, approval, [[skills.config]], [agents.*])
✅ .codex/skills/ has the gald3r core skills, and each is registered in config.toml
✅ AGENTS.md exists at project root (always-apply rules + Enforcement Rules section)
✅ codex --version runs without error
✅ OPENAI_API_KEY is set (or other provider key)
✅ sandbox_mode / approval_policy set so gald3r file ops are permitted (e.g. workspace-write + on-request)
✅ No .codex/rules/, .codex/commands/, or .codex/hooks/ expected (not supported)
```

---

## 11. Known Gaps (vs. Cursor reference — honest status)

Capability summary (see `PLATFORM_SPEC.md` for full evidence and disposition):

| Hooks | Rules | Skills | Commands | MCP |
|---|---|---|---|---|
| ❌ | ⚠️ | ⚠️ | ❌ | ⚠️ |

**Hard gaps (not achievable on Codex today):**
- **Hooks ❌** — no lifecycle-event system; no `sessionStart`/`stop`/`beforeShellExecution`. gald3r hooks do not auto-fire.
- **Commands ❌** — no slash-command / workflow palette.
- **Agent-file auto-discovery ❌** — `g-agnt-*.md` files do not load; roles are inline `[agents.*]` in `config.toml` only.
- **Rules folder ❌** — no `.codex/rules/`.

**Soft / partial parity (achievable with config):**
- **Rules ⚠️** — always-apply enforcement delivered via root `AGENTS.md` instead of a rules folder.
- **Skills ⚠️** — supported but require explicit `[[skills.config]]` registration; only 17 core skills shipped (not the full ~90).
- **MCP ⚠️** — protocol supported and config-declared, but the exact `config.toml` table key is ❓ unverified and no servers are currently declared in this repo's config.

**Docs freshness**: `last_doc_scan: never`. Run `@g-platform-scan-docs codex`
(crawl `https://developers.openai.com/codex` + the config-schema URL) to verify the MCP key,
`AGENTS.md` merge precedence, and the approval/sandbox policy enumerations, then upgrade `⚠️`/`❓`
cells to `✅` with evidence.
