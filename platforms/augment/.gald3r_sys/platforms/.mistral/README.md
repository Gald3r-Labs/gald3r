# Mistral (Mistral Vibe CLI) — gald3r Deploy Scaffold

**Config surface**: `.vibe/` + `config.toml` (TOML) + `AGENTS.md` — NOT `.mistral/`, NOT YAML.

This directory is the gald3r deploy scaffold for **Mistral**. The directory is named
`.mistral/` only as the scaffold's internal label; the platform that actually reads gald3r
config is **Mistral Vibe CLI**, which uses a `.vibe/` directory and `config.toml`.

> **Read `PLATFORM_SPEC.md` (in this directory) first.** It is the authoritative,
> doc-verified (2026-05-26) description of what works on Mistral vs. what is Cursor-generic,
> including the Known Gaps section and the correction of a prior fabricated `.mistral/config.yaml`.

Authoritative install + customization guide: **`g-skl-platform-mistral`**
(`.gald3r_sys/skills/g-skl-platform-mistral/SKILL.md`).

---

## "Mistral" is three products — gald3r targets one

| Surface | What it is | gald3r config target? |
|---|---|---|
| **Mistral Vibe CLI** | Open-source terminal coding agent (`.vibe/` + `config.toml` + `AGENTS.md`) | ✅ Yes |
| **Mistral Code** | Closed JetBrains/VSCode plugin | ❌ No config files |
| **Le Chat** | Web/app chat (MCP connectors only) | ❌ Not a file-config surface |

## Honest capability table (from PLATFORM_SPEC.md)

Legend: ✅ verified · ⚠️ partial / format-mismatch · ❌ not supported · ❓ untested.

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |

- **Hooks ⚠️** — docs reference `.vibe/` hooks but publish no schema; gald3r `g-hk-*.ps1`
  hooks cannot be wired without an event taxonomy. No `hooks.json` is shipped here.
- **Rules ⚠️** — instructions inject via `AGENTS.md` (no scoped `.mdc`-style rule files).
- **Skills ✅** — Vibe implements the Agent Skills spec (folder-per-skill `SKILL.md`);
  gald3r frontmatter needs light adaptation (`allowed-tools` / `user-invocable`).
- **Commands ⚠️** — slash commands exist but only via the skill mechanism; no command-file dir.
- **MCP ✅** — `.vibe/config.toml` `[[mcp_servers]]` (TOML).

## Files in this scaffold

- **`PLATFORM_SPEC.md`** — authoritative capability + gap analysis (start here).
- **`mistral_instructions.md`** — deploy guide (folder layout, real `.vibe/config.toml` surface).
- **`instructions.md`** — gald3r task workflow / commit format / bug protocol for `AGENTS.md`.

No Cursor-specific artifacts (`hooks.json`, `.ps1` hook wiring, `.mdc` rules) are shipped here —
the spec does not confirm any of those work on Mistral Vibe.
