Process the vault raw/ inbox: $ARGUMENTS

## What This Command Does

Invokes the Phase 2 raw inbox watcher (`raw-inbox-watcher.ps1`) which scans
`{vault}/raw/` for dropped files and routes each one rules-based:

| Drop Type                   | Routed To                              |
|-----------------------------|----------------------------------------|
| `*.md`                      | `research/articles/`                   |
| Single URL in `*.txt`       | `g-skl-ingest-url`                     |
| Single YouTube URL `*.txt`  | `g-skl-ingest-youtube`                 |
| Multi-line `*.txt`          | wrapped to `.md` in `research/articles/` |
| `*.pdf`                     | deferred to Phase 3 → `raw/failed/`    |
| `*.png` / `*.jpg`           | deferred to Phase 3 → `raw/failed/`    |

On success, files move to `raw/processed/YYYY-MM-DD/`.
On failure, files move to `raw/failed/` with a sibling `error.md`.

A summary entry is appended to `vault/log.md` per run (C-006).

## Phase 2 Limitations

- Manual trigger only (no FileSystemWatcher service yet)
- No LLM classification (that lives in Phase 3 / Task 112)
- PDFs and images are deferred — they are NOT lost, they wait in `raw/failed/`

## Usage

```powershell
# Standard run
pwsh .cursor/hooks/raw-inbox-watcher.ps1

# Preview without moving anything
pwsh .cursor/hooks/raw-inbox-watcher.ps1 -DryRun

# Verbose classification output
pwsh .cursor/hooks/raw-inbox-watcher.ps1 -Verbose
```

`@g-vault-process-inbox` should invoke the watcher script directly with no
additional arguments unless `$ARGUMENTS` requests `dry-run` or `verbose`.

## Behavior

- Re-running on an empty inbox is a no-op (exit 0)
- Idempotent: never re-processes files already in `processed/` or `failed/`
- Cross-platform: PowerShell 7+ (Windows native, pwsh on Linux/macOS)
- C-001 (file-first vault), C-006 (operations logged), C-009/C-010 (parity) apply
