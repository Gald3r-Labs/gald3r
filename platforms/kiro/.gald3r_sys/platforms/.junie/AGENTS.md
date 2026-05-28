# gald3r Development Guidelines

> JetBrains Junie auto-injects this file into every task's prompt context. It is the
> **preferred** guidelines surface (`.junie/AGENTS.md`); the legacy `.junie/guidelines.md`
> in this folder is still supported by older Junie builds. Edit the canonical copy under
> `.gald3r_sys/platforms/.junie/` -- not the installed copy.
>
> Junie guidelines search order: custom IDE-settings path -> `.junie/AGENTS.md` ->
> root `AGENTS.md` -> legacy `.junie/guidelines.md` (or `.junie/guidelines/`).

## Before Starting Any Task
1. Read `.gald3r/TASKS.md` for the current task list.
2. Read the active task file in `.gald3r/tasks/task{id}_*.md`.
3. Check `.gald3r/CONSTRAINTS.md` for architectural limits.

## Commit Format
- `feat(T{id}): description` -- new task work
- `fix(BUG-{id}): description` -- bug fix

## Bug Discovery
When encountering bugs, do NOT silently ignore them.
Pre-existing bugs: create an entry in `.gald3r/BUGS.md`.

## Task Completion
Update the task status in `.gald3r/tasks/task{id}_*.md` and `.gald3r/TASKS.md`.

## Code Standards
- No bare `TODO` comments -- use `TODO[TASK-{id}->TASK-{new_id}]` and file a follow-up task.
- Match the conventions already present in the file you are editing.

## gald3r Roles (no native agent files on Junie)
Junie is a single agentic assistant -- it has no file-defined agent roster. Approximate gald3r
agent roles by asking Junie to act in that capacity:
- task-manager: create/update/complete tasks and keep TASKS.md in sync.
- planner: write features and plans under `.gald3r/`.
- qa-engineer: track bugs in BUGS.md.
- code-reviewer: review for quality and security before completion.

## MCP
Junie supports MCP servers natively via `.junie/mcp/mcp.json` (project, commit-shareable).
See `mcp/mcp.json` in this scaffold for a reference template -- gald3r capabilities that need
executable tooling are exposed through MCP, not through skills or slash-commands (Junie has
neither). The Action Allowlist (IDE settings) governs which tools Junie may run without
confirmation; it is an approval gate, not a hook system.
