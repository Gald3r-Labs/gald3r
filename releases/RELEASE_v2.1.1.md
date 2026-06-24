# gald3r v2.1.1

A feature release that brings plugins, a richer vault API, and per-platform workflow profiles
into the engine, plus identity and hook-wiring cleanups.

## Highlights

- **Plugins in the engine.** `gald3r plugin install | remove | list | new | check-compat | update`
  (CLI + MCP tools), backed by a real `PluginSystem` with a manifest schema, an installed ledger,
  registry config, a compatibility floor, and conflict-abort — replacing the old PowerShell scripts.
- **Vault knowledge API.** New `gald3r_vault_note_get` (note as structured JSON),
  `gald3r_vault_backlinks` (who `[[wikilink]]`-references a note), and `gald3r_vault_context`
  (token-budgeted, newest-first context block) — completing the vault search + ingest surface.
- **Vault location selector.** `gald3r vault location [--select default|workspace|project|create_new]`
  with layered resolution (session/project → workspace → user home), persisted to `.gald3r/.identity`.
- **`@g-pt` workflow profiles on every IDE target.** The workflow-profile CLI
  (`list`/`use`/`copy`/`edit`/`validate`) and its skill script now ship across all platform trees,
  not just Claude/Cursor.

## Changed

- **One unified identity home.** `g-hk-setup-user` no longer writes a separate
  `~/.gald3r/user_config.json`; identity is provisioned via the engine and stored at the single
  canonical per-user home, with a one-time forward migration that preserves `user_id`/`machine_id`.

## Fixed

- **Claude Code hook wiring consolidated onto `.claude/settings.json`** (PascalCase lifecycle
  events), retiring the legacy `hooks.json` surface that could silently not fire; the `g-skl-test`
  hook-wiring check (Python + PowerShell) now reads both surfaces and reports identically.

---

_Full technical detail in [CHANGELOG.md](../CHANGELOG.md)._
