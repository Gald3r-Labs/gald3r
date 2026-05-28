# gald3r Project Rules (Roo Code — all modes)

> Modern directory form. Roo reads `.roo/rules/*.md` recursively, alphabetically,
> for ALL modes. This takes precedence over the legacy root `.roorules` single file
> when both are present. Edit the canonical copy under
> `.gald3r_sys/platforms/.roo/.roo/rules/` — not the installed copy.

## Task Management
- All work is tracked in `.gald3r/TASKS.md`.
- Read the active task in `.gald3r/tasks/task{id}_*.md` before implementing.
- Reference the task ID in commits: `feat(T{id}): description` | `fix(BUG-{id}): description`.

## Architecture
- Read `.gald3r/CONSTRAINTS.md` before architectural decisions.
- Subsystem boundaries are in `.gald3r/SUBSYSTEMS.md`.

## Bug Protocol
- Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.

## Code Standards
- No bare TODO comments — use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Match the conventions already present in the file you are editing.
