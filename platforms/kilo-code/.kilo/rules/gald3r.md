# gald3r Framework Conventions

## Project Structure
This project uses gald3r for AI-assisted project management.
- Tasks: `.gald3r/tasks/` — sequential IDs, YAML frontmatter
- Bugs: `.gald3r/bugs/`
- Goals: `.gald3r/PROJECT.md`
- Constraints: `.gald3r/CONSTRAINTS.md`

## Task Status Emojis
- `[📋]` pending  `[🔄]` in-progress  `[🔍]` awaiting-verification  `[✅]` completed  `[❌]` cancelled

## Commit Format
```
type(scope): description

Task: #T{id}
```

## Working with Tasks
1. Before starting work, check `.gald3r/TASKS.md` for priorities
2. Read the task spec at `.gald3r/tasks/task{id}_{slug}.md`
3. Check `.gald3r/CONSTRAINTS.md` for hard rules
4. Update task status in the spec file as you progress
5. Offer a git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>" when done

## Code Standards
- Never introduce breaking changes to public interfaces without a task
- All AI-generated commits must reference a task ID
- Pre-existing bugs found during work → log to `.gald3r/BUGS.md`
