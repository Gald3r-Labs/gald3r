# gald3r Project Rules (Warp — Agent Mode)

> Warp auto-discovers this ALL-CAPS rules file at the repo root and applies it to every
> Agent / Active AI session in this project. If both WARP.md and AGENTS.md exist, WARP.md
> takes priority. Edit the canonical copy under .gald3r_sys/platforms/.warp/ — not the
> installed copy. See AGENTS.md for the full universal gald3r contract.

## Task Management
- All work is tracked in .gald3r/TASKS.md.
- Read the active task in .gald3r/tasks/task{id}_*.md before implementing.
- Reference the task ID in commits: feat(T{id}): description | fix(BUG-{id}): description.

## Architecture
- Read .gald3r/CONSTRAINTS.md before architectural decisions.
- Subsystem boundaries are documented in .gald3r/SUBSYSTEMS.md.

## Terminal Discipline
- This is a Windows/PowerShell-capable project where applicable — match the host shell.
- Run long-lived servers as background tasks; do not block the Agent session.

## Bug Protocol
- Pre-existing bugs: document in .gald3r/BUGS.md — never silently ignore.

## Code Standards
- No bare TODO comments — use TODO[TASK-{id}->TASK-{new_id}] and file a follow-up task.
- Match the conventions already present in the file you are editing.
- Make surgical changes; do not refactor adjacent code that is out of scope.
