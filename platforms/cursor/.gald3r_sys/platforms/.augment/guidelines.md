# gald3r Development Guidelines

> Augment Code auto-injects this file into every session. Edit the canonical
> copy under `.gald3r_sys/platforms/.augment/` — not the installed copy.

## Task Management
- All work is tracked in `.gald3r/TASKS.md`.
- Read the active task file in `.gald3r/tasks/task{id}_*.md` before implementing.
- Reference the task ID in commit messages: `feat(T{id}): ...`.

## Architecture
- Read `.gald3r/CONSTRAINTS.md` before architectural decisions.
- Subsystem boundaries are documented in `.gald3r/SUBSYSTEMS.md`.

## Code Standards
- No bare `TODO` comments — use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Bug discovery: document pre-existing bugs in `.gald3r/BUGS.md` — never silently ignore.
- Match the conventions already present in the file you are editing.

## Commit Format
- `feat(T{id}): description` — new task work
- `fix(BUG-{id}): description` — bug fix
