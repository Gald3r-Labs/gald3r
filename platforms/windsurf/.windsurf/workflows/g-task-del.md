---
description: 'Hard-delete a mis-routed task via git rm + commit, per g-rl-33 Routing Error Hard Delete (`gald3r task delete`, T497).'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: orchestration
---
Purge a task that was created in the WRONG repository (a routing error). Runs the compiled
**`gald3r task delete`** verb (T497 -- backs g-rl-33's Routing Error Hard Delete rule, which
previously had no deterministic implementation).

```
@g-task-del T53 --reason "Created in the wrong repo; canonical copy is T12 in gald3r_world_tree"
@g-task-del T53 --reason "..." --apply
```

## What This Command Is For

**Only for genuine routing errors** -- a task file that should never have existed in this
repository at all, because the correct owning repository is a different one. This is NOT a
general-purpose "cancel this task" or "I changed my mind" command:

- Task no longer wanted, superseded, or deprioritized -> use `@g-task-upd` to set an appropriate
  status; the record stays as history.
- Task was created in the wrong repo -> THIS command.

## What This Command Does

Per g-rl-33's "Routing Error Hard Delete" rule, the ONLY correct response to a routing error is
an unconditional `git rm` + commit -- **never** a `cancelled` stub, a `moved`/`routed` status, or
a forwarding pointer (those actively mislead other agents reading across repos into thinking a
deliberate cancellation decision was made). `gald3r task delete`:

1. Locates the task file and requires a non-empty `--reason` (dry-run or apply -- always).
2. `git rm`s the file (falls back to a plain filesystem delete if the file was never
   git-tracked).
3. Removes the task's row from `gald3r.db` (plus its `task_deps` edges) so `gald3r db verify`
   never reports an `orphan_row` for it.
4. Regenerates `TASKS.md` so it no longer links to the removed file.
5. Commits with message `chore(tasks): purge T{id} routing error`, including the `--reason` text
   and a `Task: #{id}` trailer.

**Before running `--apply`:** create the canonical task in the CORRECT repository first (with an
Agent Notes entry referencing any prototype work done here), per g-rl-33's full protocol.

## Flags

| Flag | Effect |
|---|---|
| (none) | Dry-run preview -- reports the file, any tasks still depending on it, and the commit message that would be used. Writes nothing. |
| `--apply` | Actually `git rm` the file, remove the DB row, and commit. |
| `--reason TEXT` | **Required** (both dry-run and apply) -- the auditable "why" for the purge. |
| `--json` | Machine-readable report. |

## Safety

- Dry-run is the default -- `--apply` is required to write or commit anything.
- Never a soft-delete/cancelled stub: g-rl-33 forbids that alternative outright.
- If other on-disk tasks still list this id as a `dependencies:` entry, the report/output warns
  -- the delete proceeds anyway (routing-error deletion is unconditional per the rule), but
  those referencing tasks' dependency lists need a follow-up fix.
