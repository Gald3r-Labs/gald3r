# SOUL — {project_name}

> OpenClaw reads this file as the project's AI identity document. Edit the
> canonical copy under `.gald3r_sys/platforms/.openclaw/` — not the installed copy.

## Identity
This project uses gald3r for AI-assisted development — task management, quality assurance,
and multi-platform skill delivery, all file-first under `.gald3r/`.

## Context
- Tasks: `.gald3r/TASKS.md` (active detail in `.gald3r/tasks/`)
- Constraints: `.gald3r/CONSTRAINTS.md`
- Mission: `.gald3r/PROJECT.md`
- Bugs: `.gald3r/BUGS.md`

## Skills
gald3r skills use OpenClaw's `skills/<name>/SKILL.md` folder-per-skill format. Install them into
the OpenClaw workspace `skills/` dir (or point `agents.defaults.workspace` at this repo) — OpenClaw
does NOT read an arbitrary repo root automatically. See `PLATFORM_SPEC.md` for the install path.

## Commit Convention
`feat(T{id}): description` | `fix(BUG-{id}): description`

## Bug Protocol
Pre-existing bugs: document in `.gald3r/BUGS.md` — never silently ignore.
