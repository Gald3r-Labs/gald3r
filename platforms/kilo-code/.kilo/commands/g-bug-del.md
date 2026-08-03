---
description: 'Hard-delete a mis-routed bug via git rm + commit, per g-rl-33 Routing Error Hard Delete (`gald3r bug delete`, T497).'
subsystem_memberships: [BUG_AND_QUALITY]
execution_tier: orchestration
---
Purge a bug that was created in the WRONG repository (a routing error). Runs the compiled
**`gald3r bug delete`** verb (T497 -- backs g-rl-33's Routing Error Hard Delete rule, which
previously had no deterministic implementation).

```
@g-bug-del BUG-12 --reason "Created in the wrong repo; canonical copy is BUG-3 in gald3r_world_tree"
@g-bug-del BUG-12 --reason "..." --apply
```

## What This Command Is For

**Only for genuine routing errors** -- a bug file that should never have existed in this
repository at all. This is NOT how to close a bug as fixed or as a design-ruling wontfix:

- Bug is actually fixed -> `@g-bug-fix` / `gald3r bug resolve`.
- Bug is superseded by a design ruling -> `gald3r bug resolve --wontfix --reason "..."` (BUG-424).
- Bug was created in the wrong repo -> THIS command.

## What This Command Does

Per g-rl-33's "Routing Error Hard Delete" rule (mirrored on the bug side): an unconditional
`git rm` + commit -- never a status-only close, since the bug record itself should not exist
here. `gald3r bug delete`:

1. Locates the bug file and requires a non-empty `--reason` (dry-run or apply -- always).
2. `git rm`s the file (falls back to a plain filesystem delete if the file was never
   git-tracked).
3. Removes the bug's row from `gald3r.db` so `gald3r db verify` never reports an `orphan_row`
   for it.
4. Regenerates `BUGS.md` so it no longer links to the removed file.
5. Commits with message `chore(bugs): purge BUG-{id} routing error`, including the `--reason`
   text.

**Before running `--apply`:** create the canonical bug record in the CORRECT repository first,
per g-rl-33's full protocol.

## Flags

| Flag | Effect |
|---|---|
| (none) | Dry-run preview -- reports the file and the commit message that would be used. Writes nothing. |
| `--apply` | Actually `git rm` the file, remove the DB row, and commit. |
| `--reason TEXT` | **Required** (both dry-run and apply) -- the auditable "why" for the purge. |
| `--json` | Machine-readable report. |

## Safety

- Dry-run is the default -- `--apply` is required to write or commit anything.
- Never a soft-delete/cancelled stub: g-rl-33 forbids that alternative outright.
- Accepts either `BUG-12`, `12`, or `bug-012` as the id.
