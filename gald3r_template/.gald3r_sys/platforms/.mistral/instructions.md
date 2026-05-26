# Project Instructions — gald3r

> Mistral Vibe loads this file (via `.mistral/config.yaml`) at session start.
> Edit the canonical copy under `.gald3r_sys/platforms/.mistral/` — not the installed copy.

## Task Workflow
Before any implementation:
1. Read `.gald3r/TASKS.md` for active tasks.
2. Read `.gald3r/tasks/task{id}_*.md` for task details.
3. Check `.gald3r/CONSTRAINTS.md` for architectural limits.

## Commit Format
- `feat(T{id}): description` — new task work
- `fix(BUG-{id}): description` — bug fix

## Bug Discovery
Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.

## Code Standards
- No bare `TODO` comments — use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Match the conventions already present in the file you are editing.
