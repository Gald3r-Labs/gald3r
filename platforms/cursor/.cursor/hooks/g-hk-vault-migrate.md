# Hook: g-hk-vault-migrate

Migrates vault notes from a source vault (default: the local
`.gald3r/vault/`) into a destination vault (default: the resolved shared
vault), then reindexes the destination. Companion `.md` added with the T1627
wiring (the script predates the T1171 companion contract).

## Fires On

The **canonical `session-start` event with `--if-diverged`** (T1627,
WS-A-4). Wired in `g_hk_core.py` `CONCERN_CHAIN["session-start"]` and
registered directly on the Claude Code (`.claude/settings.json`
`hooks.SessionStart`) and Cursor (`.cursor/hooks.json` `sessionStart`)
triggers. In that mode it fires ONLY on vault_location divergence:
`g-hk-vault-resolve` must report `VaultMigrationCandidate` (the local vault
holds markdown notes while a different shared vault is configured and
writable); otherwise it no-ops with a `[SKIP]` line. Manual invocation
without `--if-diverged` migrates unconditionally (`-SourcePath` /
`-DestinationPath` / `-Force`).

## What It Does

1. Consults the `g-hk-vault-resolve.py` sibling for source/destination
   defaults and the divergence signal.
2. Merges `log.md` files block-wise (`## ` headings, dedup, destination
   blocks first).
3. Copies other files when missing at the destination, skips SHA256-equal
   files, and resolves conflicts by frontmatter `date:` (or mtime) —
   newer-or-equal source wins; an older source is kept at the destination
   and reported as a conflict. `-Force` always overwrites.
4. Triggers `g-hk-vault-reindex.py` for the destination so both index
   artifacts reflect the migrated content.

## Side Effects

- Writes/overwrites notes in the destination vault; merges `log.md`.
- Regenerates the destination's `_index.yaml` + `index.md` views.
- Session-idempotent via `GALD3R_HK_VAULT_MIGRATE_APPLIED` (`-ForceRun`
  bypasses). Never crashes the host session.

## Related Tasks

- T1627 (WS-A-4) — registered the vault chain; added the divergence gate.
- T1584 — Python port of the original `.ps1` hook.
- T1600 — removed the `.ps1` fallback branches.
