# gald3r Framework Conventions

This project uses gald3r for AI-assisted project management.

## Core Files
- `.gald3r/TASKS.md` — task index
- `.gald3r/tasks/task{id}_{slug}.md` — individual task specs
- `.gald3r/BUGS.md` — bug index
- `.gald3r/PROJECT.md` — mission and goals
- `.gald3r/CONSTRAINTS.md` — hard rules (read before major changes)

## Task Workflow
1. Find your task in `TASKS.md`
2. Read the full spec: `.gald3r/tasks/task{id}_{slug}.md`
3. Check `CONSTRAINTS.md` for hard rules
4. Implement and update the task's `## Status History`
5. Offer a commit with `Task: #T{id}` trailer

## Status Emojis
`[📋]` pending · `[🔄]` in-progress · `[🔍]` awaiting-verification · `[✅]` completed · `[❌]` cancelled

## Commit Format
```
type(scope): description

Task: #T{id}
```
