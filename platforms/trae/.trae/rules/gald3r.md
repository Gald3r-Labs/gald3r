# gald3r Framework Conventions

This project uses gald3r for AI-assisted project management. Follow these conventions when working in this codebase.

## Project Structure
- **Tasks**: `.gald3r/tasks/task{id}_{slug}.md` — sequential IDs, YAML frontmatter
- **Task index**: `.gald3r/TASKS.md`
- **Bugs**: `.gald3r/bugs/bug{id}_{slug}.md` + `.gald3r/BUGS.md`
- **Project mission**: `.gald3r/PROJECT.md`
- **Hard constraints**: `.gald3r/CONSTRAINTS.md` — read before any significant change

## Task Status Emojis
| Emoji | Status |
|-------|--------|
| `[📋]` | pending |
| `[🔄]` | in-progress |
| `[🔍]` | awaiting-verification |
| `[✅]` | completed |
| `[❌]` | cancelled |

## Commit Format
```
type(scope): brief description

Task: #T{id}
```
Types: `feat` · `fix` · `chore` · `docs` · `refactor` · `test`

## Agent Conventions
1. Read the task spec before implementing — context is in the task file
2. Check `CONSTRAINTS.md` for rules that cannot be bypassed
3. Bugs discovered during work that predate this task → log them (never ignore)
4. Sequential task IDs — never reuse an ID from a completed task
5. Offer a commit after completing implementation
