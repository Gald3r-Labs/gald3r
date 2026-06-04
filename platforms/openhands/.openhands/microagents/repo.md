# Repository Context

> **LEGACY surface** — `.openhands/microagents/repo.md` is the legacy repository-microagent
> path. It still auto-loads, but the current PRIMARY always-on surface is repo-root `AGENTS.md`
> (see PLATFORM_SPEC.md §2/§9 #5). Prefer placing this content in `AGENTS.md` going forward.
> OpenHands loads this microagent for every session on this repo. Edit the
> canonical copy under `.gald3r_sys/platforms/.openhands/` — not the installed copy.

## Task Management (gald3r)
This project uses gald3r for task tracking.
- Active tasks: `.gald3r/TASKS.md`
- Task details: `.gald3r/tasks/task{id}_*.md`
- Constraints: `.gald3r/CONSTRAINTS.md`

## Development Workflow
1. Read the active task before implementing.
2. Reference the task ID in all commits: `feat(T{id}): ...`.
3. Mark tasks complete by updating the task YAML status and `.gald3r/TASKS.md`.

## Bug Protocol
Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.
