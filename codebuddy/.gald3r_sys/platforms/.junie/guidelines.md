# gald3r Development Guidelines (LEGACY surface)

> LEGACY: `.junie/guidelines.md` is the legacy Junie guidelines location, still supported
> by older builds. The PREFERRED surface is `.junie/AGENTS.md` (this folder) -- keep both
> in sync for compatibility. Junie injects whichever it finds first per the search order
> (custom path -> `.junie/AGENTS.md` -> root `AGENTS.md` -> this legacy file). Edit the
> canonical copy under `.gald3r_sys/platforms/.junie/` -- not the installed copy.

## Before Starting Any Task
1. Read `.gald3r/TASKS.md` for the current task list.
2. Read the active task file in `.gald3r/tasks/task{id}_*.md`.
3. Check `.gald3r/CONSTRAINTS.md` for architectural limits.

## Commit Format
- `feat(T{id}): description` — new task work
- `fix(BUG-{id}): description` — bug fix

## Bug Discovery
When encountering bugs, do NOT silently ignore them.
Pre-existing bugs: create an entry in `.gald3r/BUGS.md`.

## Task Completion
Update the task status in `.gald3r/tasks/task{id}_*.md` and `.gald3r/TASKS.md`.

## Code Standards
- No bare `TODO` comments — use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Match the conventions already present in the file you are editing.
