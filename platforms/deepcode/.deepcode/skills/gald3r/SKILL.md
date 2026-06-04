---
name: gald3r
description: "gald3r project management — task tracking, bug reporting, goal management, and AI agent coordination for software projects"
allowed-tools: Read, Write, Bash
---
# gald3r Framework

This skill gives Deep Code access to gald3r project management capabilities.

## Key Commands

- **Task status**: Review `.gald3r/TASKS.md` for current task list
- **Create task**: Use `@g-task-new` conventions when creating `.gald3r/tasks/` files
- **Bug report**: Log bugs to `.gald3r/BUGS.md` and `.gald3r/bugs/`
- **Project status**: Read `.gald3r/PROJECT.md` for mission and goals

## Task Status Emojis
- `[📋]` pending  `[🔄]` in-progress  `[🔍]` awaiting-verification  `[✅]` completed  `[❌]` cancelled

## Commit Format
```
type(scope): description

Task: #T{id}
```
Types: feat, fix, chore, docs, refactor, test

## File Conventions
- Tasks: `.gald3r/tasks/task{id}_{slug}.md`
- Bugs: `.gald3r/bugs/bug{id}_{slug}.md`
- Sequential IDs — never reuse
