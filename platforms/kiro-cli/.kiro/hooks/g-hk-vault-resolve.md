# Hook: g-hk-vault-resolve

Resolves the gald3r vault and repos-mirror locations and guarantees the
working directory layout exists before anything else in the session touches
the vault. Companion `.md` added with the T1627 wiring (the script predates
the T1171 companion contract).

## Fires On

The **canonical `session-start` event** (T1627, WS-A-4). Wired in
`g_hk_core.py` `CONCERN_CHAIN["session-start"]` and registered directly on
the Claude Code (`.claude/settings.json` `hooks.SessionStart`) and Cursor
(`.cursor/hooks.json` `sessionStart`) triggers. Also imported in-process by
the sibling vault hooks (`g-hk-vault-reindex.py`, `g-hk-vault-migrate.py`,
`raw-inbox-watcher.py`) as their path resolver — the Python analogue of
dot-sourcing the retired `.ps1`.

## What It Does

1. Reads `vault_location` / `repos_location` from `.gald3r/.identity`, with
   `.env` fallbacks (`GALD3R_VAULT_LOCATION` / `GALD3R_KNOWLEDGE_WELL_PATH` /
   `GALD3R_REPOS_LOCATION`).
2. Falls back to the local `.gald3r/vault/` and `.gald3r/repos/` when the
   shared location is unset, `{LOCAL}`, or not writable.
3. Flags `VaultMigrationCandidate` when the local vault holds markdown notes
   while a different shared vault is configured — the divergence signal
   `g-hk-vault-migrate --if-diverged` gates on.
4. Ensures the project's `projects/<name>/sessions|decisions` vault
   directories exist.

## Side Effects

- Creates the local fallback and resolved vault/repos directories plus the
  per-project vault subtree when missing (idempotent `mkdir -p` semantics).
- Prints nothing in standalone mode; never blocks the session (always exits 0).

## Related Tasks

- T1627 (WS-A-4) — registered the vault chain + raw-inbox watcher.
- T1584 — Python port of the original `.ps1` hook.
- Consumers: `g-hk-vault-reindex.py`, `g-hk-vault-migrate.py`,
  `raw-inbox-watcher.py`, `g-hk-session-start.py` (inline port).
