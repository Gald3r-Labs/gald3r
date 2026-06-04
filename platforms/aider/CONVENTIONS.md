# Development Conventions — gald3r

> This is the gald3r behavioral surface for the Aider platform. Aider does NOT
> auto-load it by filename — it is pinned as read-only context via `read:` in
> `.aider.conf.yml` (or `/read-only CONVENTIONS.md` / `aider --read CONVENTIONS.md`).
> Edit the canonical copy under `.gald3r_sys/platforms/.aider/` — not the installed copy.

## Task References
- All work is tracked in `.gald3r/TASKS.md`.
- Read the active task file in `.gald3r/tasks/task{id}_*.md` before implementing.
- Read `.gald3r/CONSTRAINTS.md` before any architectural change.

## Commit Style
- `feat(T{id}): description` — new task work
- `fix(BUG-{id}): description` — bug fix
- Subject line <= 72 chars, imperative mood.

## Code Standards
- No bare `TODO` comments — use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.
- Match the conventions of the file you are editing.

## Aider-Specific
- Auto-commits are disabled (`.aider.conf.yml`) so commits follow the conventions above.
- `.gald3r/` task files are read-only context — do not edit them from an Aider session.
