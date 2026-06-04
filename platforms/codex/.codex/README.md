# Codex (OpenAI Codex CLI) -- gald3r Deploy Scaffold

Authoritative install + customization guide: **`g-skl-platform-codex`** (.gald3r_sys/skills/g-skl-platform-codex/SKILL.md).

See **`PLATFORM_SPEC.md`** in this directory for verified platform capability details (Phase 1 research, T1464).
Phase 2 deploy artifact adaptation: see T1489 in TASKS.md.

## Scaffold contents

| File | Purpose |
|---|---|
| `config.toml` | Master Codex config (modern TOML, schema-validated): model, sandbox, approval policy, `[features]`, `[[skills.config]]` skill registrations, `[agents.*]` inline roles. **This is NOT the legacy `codex.config.json`** -- see PLATFORM_SPEC.md. |
| `codex_instructions.md` | gald3r setup/configuration guide for Codex. |
| `PLATFORM_SPEC.md` | Verified capability matrix and Known Gaps (Phase 1). |

## Key platform facts (from PLATFORM_SPEC.md)

- **Instruction file**: root `AGENTS.md` (NOT inside `.codex/`) -- the only always-apply enforcement surface.
- **No native hooks** -- no `sessionStart`/`stop`/`beforeShellExecution` lifecycle events; PowerShell hooks do not auto-fire.
- **No native commands folder** -- gald3r `g-*` workflows surface as skills + `AGENTS.md` guidance.
- **No rules folder** -- enforcement lives in root `AGENTS.md` + `config.toml` agent descriptions.
- **Skills require explicit registration** in `config.toml` via `[[skills.config]]` (no folder auto-discovery).
- **MCP supported** but declared in `config.toml`; exact table key not yet doc-verified.

Run `@g-platform-scan-docs codex` to refresh docs freshness (`last_doc_scan: never`).
