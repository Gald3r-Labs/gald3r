---
description: 'Deprecated alias for @g-task-upd — update a task''s status via g-skl-tasks UPDATE STATUS operation.'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: guarded_prompt
---
> **Deprecated**: Use `@g-task-upd` instead. This alias is kept for backward compatibility.

Update task status. Activates **g-skl-tasks** → UPDATE STATUS operation.

Provide: task ID and new status. The skill handles file update, TASKS.md sync, and subsystem Activity Log update.
