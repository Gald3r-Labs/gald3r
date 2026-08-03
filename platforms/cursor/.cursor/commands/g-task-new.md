---
description: 'Deprecated alias for @g-task-add — create a new task via g-skl-tasks CREATE TASK operation.'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: guarded_prompt
---
> **Deprecated**: Use `@g-task-add` instead. This alias is kept for backward compatibility.

Create a new task. Activates **g-skl-tasks** → CREATE TASK operation.

Provide: task title and brief description. The skill handles ID assignment, complexity scoring, file creation, and TASKS.md entry atomically.
