# Hook: raw-inbox-watcher

## Fires On
The **canonical `stop` event with `--hook-mode`** (T1627, WS-A-4). Wired in `g_hk_core.py` `CONCERN_CHAIN["stop"]` and registered directly on the Claude Code (`.claude/settings.json` `hooks.Stop`) and Cursor (`.cursor/hooks.json` `stop`) triggers — deliberately BEFORE `g-hk-vault-reindex.py`, so routed files land in the same index regen. In hook mode the exit code is always 0 (a lifecycle hook must never block the host session); failures are still moved to `raw/failed/` and flagged. Also invocable manually via `@g-vault-process-inbox` or directly: `python .claude/hooks/raw-inbox-watcher.py`. No FileSystemWatcher service is installed — Phase 3 will add a watcher daemon.

## What It Does
Scans `{vault}/raw/` for dropped files, classifies each by extension and content (rules-based — no LLM in Phase 2), and routes accepted files to the appropriate vault destination via existing `g-skl-ingest-*` skills. Re-running on an empty `raw/` is a no-op (which keeps the stop-chain registration cheap). Supports `-DryRun` for inspection-only mode and `-VaultPathOverride` for non-default vault locations.

## Side Effects
- Moves accepted files from `{vault}/raw/` to `{vault}/raw/processed/YYYY-MM-DD/`.
- Moves rejected files to `{vault}/raw/failed/` and writes an `error.md` sibling explaining the failure.
- Appends a run-summary block to `{vault}/log.md`.
- Triggers downstream ingest skills (which may write vault notes, update `_index.yaml`, etc.).

## Related Tasks
- T1627 (WS-A-4) — registered the watcher on the canonical `stop` event.
- Vault subsystem — raw inbox processing (Phase 2)
- `g-skl-vault` raw ingestion lifecycle
