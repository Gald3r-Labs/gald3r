# Project Context — gald3r

> Goose reads this file at session start. Edit the canonical copy under
> `.gald3r_sys/platforms/.goose/` — not the installed copy.

## Task Management
All tasks are tracked in `.gald3r/TASKS.md`. Before implementing, read the active task in
`.gald3r/tasks/task{id}_*.md`. Read `.gald3r/CONSTRAINTS.md` before architectural changes.

## Commit Convention
- `feat(T{id}): description` — new task work
- `fix(BUG-{id}): description` — bug fix

## Bug Protocol
Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.

## gald3r MCP (optional)
If the gald3r MCP extension is configured, use it for task/bug/vault operations
(see `.goose/config.yaml`).
