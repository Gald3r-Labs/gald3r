# gald3r Task Management

> Kiro injects every steering file into every session. Edit the canonical copy
> under `.gald3r_sys/platforms/.kiro/steering/` — not the installed copy.

Tasks are tracked in `.gald3r/TASKS.md`. Active task detail lives in `.gald3r/tasks/`.
Read `.gald3r/PROJECT.md` for the mission and `.gald3r/CONSTRAINTS.md` before making
architecture decisions. Always reference the active task ID in commit messages:
`feat(T{id}): ...` / `fix(BUG-{id}): ...`.

Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.

Kiro specs map to gald3r PRDs: `requirements.md` -> acceptance criteria,
`design.md` -> technical design. Use Kiro specs and gald3r tasks together; do not
duplicate tracking.
