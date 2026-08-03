---
description: 'Move resolved/closed bugs out of BUGS.md into count-bucketed .gald3r/archive/ history via `gald3r bug archive` (T497).'
subsystem_memberships: [BUG_AND_QUALITY]
execution_tier: orchestration
---
Archive terminal bug history into `.gald3r/archive/` while keeping `BUGS.md` as an active quality index.

```
@g-bug-archive
@g-bug-archive --apply
@g-bug-archive --include-recent
@g-bug-archive --apply --include-recent --recent-window-days 7
```

## What This Command Does

Runs the compiled **`gald3r bug archive`** verb (T497 -- backs g-rl-33's Active Index Archive
Gate, which previously had no deterministic implementation).

The verb moves resolved/closed/wontfix bug history out of the active index and into count-based
archive buckets:

- Index files: `.gald3r/archive/archive_bugs_0000_0999.md`, `.gald3r/archive/archive_bugs_1000_1999.md`, ...
- Bug files: `.gald3r/archive/bugs/bugs_0000_0999/`, `.gald3r/archive/bugs/bugs_1000_1999/`, ...

Buckets hold at most 1000 archive entries/files and are assigned by archive entry ordinal, not by
BUG-NNN. Each archived file's frontmatter gains an `archive:` provenance block (slot, index
path, archived-at date, source project, original bug id).

## Flags

| Flag | Effect |
|---|---|
| (none) | Dry-run preview -- classifies every candidate, writes nothing. |
| `--apply` | Actually move files, update the DB, and rewrite `BUGS.md`. |
| `--include-recent` | Also archive terminal bugs resolved within the recency window (default: excluded). |
| `--recent-window-days N` | Override the default 14-day recency window. |
| `--json` | Machine-readable report (candidates, held-back-as-recent). |

## Safety

- Dry-run is the default -- `--apply` is required to write anything.
- Recently resolved bugs stay active unless `--include-recent` is supplied.
- Never deletes history: files move, they are not removed. The bug row in `gald3r.db` is
  relocated out of the live `bugs` table (so `gald3r db verify` never reports an `orphan_row`)
  -- `status_history` rows are preserved as permanent audit trail.
- Apply leaves (and idempotently re-writes) an `## Archive Pointers` block in `BUGS.md`'s
  hand-curated header, linking every archive index file -- it survives future
  `gald3r db rebuild`/`bug archive` runs the same way the rest of that header does.
- As with any `--apply` destructive verb, only run it when the active task explicitly
  authorizes archival work -- the CLI itself has no session/task-authorization concept, so this
  is an agent-level discipline, not something the verb enforces.
