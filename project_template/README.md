# {project_name}

This project runs on **[Gald3r](https://github.com/wrm3/gald3r) Unity** -- a hybrid setup for
**both Cursor and Claude Code** over one shared `.gald3r/` brain. Plan in Cursor, code & review
in Claude; both tools share the same tasks, bugs, plans, and constraints.

## Getting started
Open in **Cursor** or **Claude Code** and run **`@g-setup`** (Cursor) / **`/g-setup`** (Claude).

## Where things live
| Path | What |
|---|---|
| `AGENTS.md` | Universal instructions -- source of truth for agent behavior |
| `.cursor/` | Cursor config (rules, skills, agents, commands, hooks) |
| `.claude/` | Claude Code config (skills, commands, agents, hooks, settings) |
| `.gald3r/` | Shared project memory: tasks, bugs, plans, constraints |

## Common commands
`@g-status` / `/g-status` - `@g-go` / `/g-go` - `@g-task-new` - `@g-bug-report` - `@g-medic`.
Full catalog on the [Gald3r Wiki](https://github.com/wrm3/gald3r/wiki/Commands).

---
*Replace this README with your own as your project grows. Powered by gald3r v2.3.0.*
