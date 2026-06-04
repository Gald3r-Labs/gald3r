---
name: gald3r
description: "gald3r project management framework — task tracking, bug reporting, goal management, and AI agent coordination"
allowed-tools: Read, Write, Bash
user-invocable: true
---
# gald3r Framework

This skill gives CodeBuddy access to the gald3r project management framework.

## Project Navigation
- **Active tasks**: `.gald3r/TASKS.md`
- **Task detail**: `.gald3r/tasks/task{id}_{slug}.md`
- **Bugs**: `.gald3r/BUGS.md` + `.gald3r/bugs/`
- **Project mission & goals**: `.gald3r/PROJECT.md`
- **Hard constraints**: `.gald3r/CONSTRAINTS.md`

## Task Status Emojis
- `[📋]` pending
- `[🔄]` in-progress
- `[🔍]` awaiting-verification
- `[✅]` completed
- `[❌]` cancelled

## Commit Convention
```
type(scope): brief description

Task: #T{id}
```
Types: `feat` | `fix` | `chore` | `docs` | `refactor` | `test`

## Working Agreement
1. Always read the task spec before coding
2. Check `CONSTRAINTS.md` for hard rules that cannot be bypassed
3. Log any pre-existing bugs discovered (never silently ignore)
4. Offer a commit when implementation is complete
