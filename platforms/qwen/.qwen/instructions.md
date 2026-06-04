# Project Instructions — gald3r

> Qwen Code loads this file (via `.qwen/config.yaml`) at session start. Edit the
> canonical copy under `.gald3r_sys/platforms/.qwen/` — not the installed copy.

## Task Management
Tasks are tracked in `.gald3r/TASKS.md`.
Before implementing: read the active task in `.gald3r/tasks/task{id}_*.md`.
Commit format: `feat(T{id}): description` / `fix(BUG-{id}): description`.

## Architecture Constraints
Read `.gald3r/CONSTRAINTS.md` before architectural decisions.
Subsystem boundaries are in `.gald3r/SUBSYSTEMS.md`.

## Bug Protocol
Never silently ignore bugs. Pre-existing bugs: document in `.gald3r/BUGS.md`.

## Code Standards
- No bare `TODO` comments — use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Match the conventions already present in the file you are editing.
