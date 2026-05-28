---
description: Create a new gald3r task (file first, then TASKS.md, sequential ID)
argument-hint: <task title / short description>
---

# gald3r New Task

Create a new gald3r task following the gald3r task-creation workflow:

1. Determine the next sequential task ID by scanning `.gald3r/tasks/**` and `.gald3r/TASKS.md`.
2. Create the task file FIRST at `.gald3r/tasks/open/task{id}_{slug}.md` with YAML frontmatter
   (`id`, `title`, `status: pending`, `type`, `priority`, `created`, `requires_verification`,
   `subsystems`, `dependencies`).
3. Add the matching row to `.gald3r/TASKS.md` SECOND.
4. Include a `## Summary`, `## What Needs to Be Done`, `## Acceptance Criteria`, and an
   initial `## Status History` row.

Title / description: $ARGUMENTS
