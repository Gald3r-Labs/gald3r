# Hook: raw-inbox-watcher

## Fires On
Manual / on-demand only (Phase 2 design). Invoked via `@g-vault-process-inbox` or directly: `python .cursor/hooks/raw-inbox-watcher.py`. No FileSystemWatcher service is installed — Phase 3 will add a watcher daemon.

## What It Does
Scans `{vault}/raw/` for dropped files, classifies each by extension and content (rules-based — no LLM in Phase 2), and routes accepted files to the appropriate vault destination via existing `g-skl-ingest-*` skills. Re-running on an empty `raw/` is a no-op. Supports `-DryRun` for inspection-only mode and `-VaultPathOverride` for non-default vault locations.

## Side Effects
- Moves accepted files from `{vault}/raw/` to `{vault}/raw/processed/YYYY-MM-DD/`.
- Moves rejected files to `{vault}/raw/failed/` and writes an `error.md` sibling explaining the failure.
- Triggers downstream ingest skills (which may write vault notes, update `_index.yaml`, etc.).

## Related Tasks
- Vault subsystem — raw inbox processing (Phase 2)
- `g-skl-vault` raw ingestion lifecycle
