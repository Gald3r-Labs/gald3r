---
subsystem_memberships: [TASK_MANAGEMENT]
---
Steer a running g-go-code worktree session mid-flight without restarting it: $ARGUMENTS

## Usage
- `@g-steer T{id} "<steering prompt>"` — drop a one-shot steering instruction into the running session's worktree
- `@g-steer T{id} --role code --owner {owner} "<steering prompt>"` — disambiguate when multiple worktrees exist for the same task

## What it does

`@g-steer` writes `steer.md` to the **worktree root** of an in-flight `g-go-code` task. The running
implementation session polls for this file at **every AC-gate iteration** (step b2.5). When found,
it injects the prompt as a high-priority steering instruction, logs `STEERED by user at turn N` to
the task's `## Status History`, then **deletes** `steer.md` so the steer fires exactly once.

This lets you redirect work in flight — narrow the focus, skip a sub-task, change an approach — without
killing the session and losing its context. It is the complement to `@g-queue` (which adds work to do
*after* the goal completes) and to `g-go-code --resume` (which restarts a crashed session).

Steering is **one-shot and latest-wins**: a second `@g-steer` before the first is consumed overwrites
the pending steer. Each new redirection requires a new `@g-steer` call.

## Sub-operations

### Write a steer (`@g-steer T{id} "<prompt>"`)

1. Parse `T{id}` (the target task) and the quoted `<steering prompt>` text from `$ARGUMENTS`.
   Default `--role code` and `--owner` to the current session owner (e.g. the IDE/platform slug) when
   not supplied.
2. Invoke the worktree helper to write `steer.md` (overwrite — latest steer wins):
   ```powershell
   .\.gald3r_sys\skills\g-skl-git-commit\scripts\gald3r_worktree.ps1 -Action Steer -TaskId {id} -Role code -Owner {owner} -SteerText "<steering prompt>" -Json
   ```
   Installed templates may call the helper from the `g-skl-git-commit/scripts/gald3r_worktree.ps1`
   skill directory when no root `scripts/` copy exists.
3. The helper writes `steer.md` atomically (temp file + rename) at the worktree root so the running
   session never reads a half-written file.
4. Confirm to user: `🧭 Steer queued for T{id} — the running session will pick it up at the next AC-gate.`

If no gald3r-owned worktree exists for `T{id}` / role / owner, the helper errors with "cannot steer"
— there is no running session to redirect. Start one with `@g-go-code tasks {id}` first.

## How the running session consumes it

`g-go-code` step b2.5 (Steer poll) runs the read-and-clear mode of the same helper at each AC-gate:

```powershell
.\.gald3r_sys\skills\g-skl-git-commit\scripts\gald3r_worktree.ps1 -Action Steer -TaskId {id} -Role code -Owner {owner} -Json
```

- `steered: false` → silent no-op, loop continues.
- `steered: true` → inject `steer_prompt`, log `STEERED by user at turn N`, helper deletes `steer.md`.

## Related

- Command: `g-queue` — append follow-up work processed after the main goal completes
- Command: `g-go-code` — the session that polls for `steer.md` (see "Mid-Flight Course Correction")
- Helper: `.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_worktree.ps1` (`-Action Steer`)
- Spec: T969 — Worktree /steer + /queue
- File: `<worktree>/steer.md` (one-shot, deleted after injection)

Let's steer.
