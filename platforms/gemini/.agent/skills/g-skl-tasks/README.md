---
subsystem_memberships: [TASK_MANAGEMENT]
---
# g-skl-tasks

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this
> page is for developers browsing the skill library on GitHub.

## What it does

Owns every piece of task data in `.gald3r/`. One skill, four files:

- `.gald3r/TASKS.md` — the active task index.
- `.gald3r/tasks/**/*.md` — one Markdown file per task, organized into status subfolders (`open/`, `in-progress/`, `awaiting-verification/`, `completed/YYYY/MM/DD/`).
- `.gald3r/archive/archive_tasks_*.md` and `.gald3r/archive/tasks/**` — bounded archive ledger plus archived task files.

If TASKS.md and the underlying task files ever disagree, this skill is the only thing that may reconcile them.

## When to use

- "create a task", "add a task", "make a task", "spec it out"
- "update task status", "complete task", "fail this task"
- Anything referencing a task ID (`T123`, `Task 42`, `#103`)
- Sync drift between `TASKS.md` and `tasks/`
- Sprint planning, complexity scoring, dependency graph review
- Pre-work file verification before claiming work

If you see a "phantom" (in TASKS.md but no file) or an "orphan" (file but not in TASKS.md), activate this skill before doing anything else.

## Trigger phrases (auto-routed to this skill via g-rl-33)

```
create a task | add a task | make a task | task and spec | spec it out
please task | add to tasks | task this | create a task(2) | task them
```

## Examples

### Create a new task

```
@g-task-add "Add SHA-256 verification to install pipeline"
```

Produces a `task{NNNN}_*.md` file in `tasks/open/` and appends a row to TASKS.md. The skill enforces sequential ID numbering (next ID = highest existing + 1).

### Move a task through its lifecycle

```
@g-task-upd 1043 --status in-progress
@g-task-upd 1043 --status awaiting-verification
@g-task-upd 1043 --status completed
```

Each transition updates both the task file frontmatter and the TASKS.md index. The file moves to the matching subfolder.

### Sync check

```
@g-task-sync-check
```

Walks both surfaces and reports phantoms, orphans, status mismatches, and TASKS.md formatting drift.

## File ownership boundary

This skill is the **only** thing that may write to:

- `.gald3r/TASKS.md`
- `.gald3r/tasks/**/*.md`
- `.gald3r/archive/archive_tasks_*.md`
- `.gald3r/archive/tasks/**`

Other agents must route through `@g-task-*` commands rather than touching these files directly. This is enforced by `g-rl-33` (the .gald3r/ Folder Gate).

## See also

- `g-skl-bugs` — sibling skill for the parallel bug surface
- `g-skl-plan` — owns PLAN.md and the feature → task pipeline
- `g-rl-33` — enforcement rules that route to this skill
- `g-rl-34` — TODO/stub follow-up task creation gate (writes here)
