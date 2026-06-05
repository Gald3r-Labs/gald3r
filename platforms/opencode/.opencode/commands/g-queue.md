---
subsystem_memberships: [TASK_MANAGEMENT]
---
Queue follow-up work into a running g-go-code worktree session, to run after the main goal completes: $ARGUMENTS

## Usage
- `@g-queue T{id} "<follow-up prompt>"` — append a follow-up item to the running session's queue
- `@g-queue T{id} --role code --owner {owner} "<follow-up prompt>"` — disambiguate when multiple worktrees exist for the same task
- `@g-queue T{id} --list` — read the pending follow-up queue without appending

## What it does

`@g-queue` appends a follow-up prompt to `queue.md` at the **worktree root** of an in-flight
`g-go-code` task. Unlike `@g-steer` (which interrupts the current trajectory immediately), queued
items are **not** processed mid-task — they are drained only after the main goal's acceptance criteria
are all met and the task reaches `[🔍]` (g-go-code step 7d).

`queue.md` is an append-only checklist (`- [ ]` per item). Each call adds one item; ordering is
preserved. This lets you stack up "while you're in there, also do X" work without disrupting the
current goal or losing the worktree's context.

## Sub-operations

### Append a follow-up (`@g-queue T{id} "<prompt>"`)

1. Parse `T{id}` (the target task) and the quoted `<follow-up prompt>` text from `$ARGUMENTS`.
   Default `--role code` and `--owner` to the current session owner when not supplied.
2. Invoke the worktree helper to append the item:
   ```powershell
   .\.gald3r_sys\skills\g-skl-git-commit\scripts\gald3r_worktree.ps1 -Action Queue -TaskId {id} -Role code -Owner {owner} -QueueText "<follow-up prompt>" -Json
   ```
   Installed templates may call the helper from the `g-skl-git-commit/scripts/gald3r_worktree.ps1`
   skill directory when no root `scripts/` copy exists.
3. The helper creates `queue.md` with a header on first write, then appends `- [ ] <prompt>` (internal
   newlines collapsed so each item stays on one row).
4. Confirm to user: `📥 Queued for T{id} — will be processed after the main goal completes ({pending_count} pending).`

### List the queue (`@g-queue T{id} --list`)

```powershell
.\.gald3r_sys\skills\g-skl-git-commit\scripts\gald3r_worktree.ps1 -Action Queue -TaskId {id} -Role code -Owner {owner} -Json
```

Returns `pending_count` and the `items` array. Display each pending item; report `(empty)` when none.

If no gald3r-owned worktree exists for `T{id}` / role / owner, the helper errors — there is no running
session to queue against. Start one with `@g-go-code tasks {id}` first.

## How the running session drains it

`g-go-code` step 7d (Drain Follow-Up Queue) runs after the main task reaches `[🔍]`:

- **In-scope + small** items → handled inline within the same worktree, then checked off (`- [x]`).
- **Distinct deliverables** → filed as real follow-up tasks via `g-skl-tasks CREATE TASK` (Follow-Up
  Task Filing Gate — never a slug-only name) and referenced next to the checked-off item.

Draining never blocks the `[🔍]` of the main task.

## Related

- Command: `g-steer` — one-shot mid-flight steering (interrupts the current trajectory)
- Command: `g-go-code` — the session that drains `queue.md` (see step 7d + "Mid-Flight Course Correction")
- Helper: `.claude/skills/g-skl-git-commit/scripts/gald3r_worktree.ps1` (`-Action Queue`)
- Spec: T969 — Worktree /steer + /queue
- File: `<worktree>/queue.md` (append-only checklist)

Let's queue.
