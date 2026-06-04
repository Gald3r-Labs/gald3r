Archive terminal bug history into `.gald3r/archive/` while keeping `BUGS.md` as an active quality index.

```
@g-bug-archive --dry-run
@g-bug-archive --apply
@g-bug-archive --dry-run --include-recent
```

## What This Command Does

Delegates to **g-skl-bugs** -> ARCHIVE BUGS.

The command moves resolved/closed bug history out of the active index and into count-based archive buckets:

- Index files: `.gald3r/archive/archive_bugs_0000_0999.md`, `.gald3r/archive/archive_bugs_1000_1999.md`, ...
- Bug files: `.gald3r/archive/bugs/bugs_0000_0999/`, `.gald3r/archive/bugs/bugs_1000_1999/`, ...

Buckets hold at most 1000 archive entries/files and are assigned by archive entry ordinal, not by BUG-NNN.

## Safety

- Dry-run is the default.
- Apply requires an active task that explicitly authorizes archival work.
- Open, in-progress, awaiting-verification, verification-in-progress, and requires-user-attention bugs must stay in `BUGS.md`.
- Recently resolved bugs stay active unless `--include-recent` is supplied.
- Archive apply must leave an Archive Pointers section in `BUGS.md`.
