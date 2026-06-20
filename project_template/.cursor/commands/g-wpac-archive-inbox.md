---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
Archive stale [DONE] WPAC inbox messages and prune the index: $ARGUMENTS

## What This Command Does

Moves resolved (`[DONE]`/`[RESOLVED]`) WPAC inbox messages older than a threshold (default **30 days**) out of the active index and into `.gald3r/linking/messages/archive/`, then prunes their rows from `INBOX.md`. Keeps the active index lightweight (target: <= 50 active rows). Uses the shared script `gald3r_wpac_inbox.ps1` (or its `.py` twin).

The inbox is a lightweight INDEX table (`INBOX.md`) backed by one file per message under `.gald3r/linking/messages/`. Archiving never deletes data: messages are relocated, and an append-only `archive_index.md` records what was moved and when.

## Workflow

### 1. Migrate if needed
If `INBOX.md` is still in the legacy flat-body format, the script auto-migrates it to the index layout first (idempotent — safe to re-run).

### 2. Archive stale [DONE] items
Run the archive operation:

```powershell
# Default 30-day threshold
.gald3r_sys/scripts/gald3r_wpac_inbox.ps1 -Archive -ProjectRoot .

# Custom threshold (e.g. 14 days)
.gald3r_sys/scripts/gald3r_wpac_inbox.ps1 -Archive -ThresholdDays 14 -ProjectRoot .
```

Or, equivalently, via the inbox-check hook:

```powershell
.claude/hooks/g-hk-wpac-inbox-check.ps1 -Archive -ThresholdDays 30 -ProjectRoot .
```

The script:
- Selects `[DONE]`/`[RESOLVED]` rows whose backing message file `created_at` is older than the threshold.
- Moves those message files to `.gald3r/linking/messages/archive/`.
- Appends a row per moved message to `.gald3r/linking/messages/archive/archive_index.md`.
- Removes the archived rows from the active `INBOX.md`.

### 3. Report
Confirm how many messages were archived and the resulting active row count.

## Usage Examples

```
@g-wpac-archive-inbox
@g-wpac-archive-inbox 14        # archive [DONE] older than 14 days
```

## Notes

- Idempotent: re-running with nothing eligible is a no-op.
- The session-start inbox check prompts you to run this command when the active
  index carries more than 50 `[DONE]` rows.
- Open items (`[OPEN]`), pending `[ORDER]`/`[REQUEST]`, and `[CONFLICT]` rows are
  never archived.

## Delegates To
`.gald3r_sys/scripts/gald3r_wpac_inbox.ps1` (Archive operation); `g-skl-wpac-read` for reviewing inbox items.
