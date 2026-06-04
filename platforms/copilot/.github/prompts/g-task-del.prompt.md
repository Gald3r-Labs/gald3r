Archive (soft-delete) a task. Activates **g-skl-tasks** → ARCHIVE TASK operation.

```
@g-task-del TASK-NNN
@g-task-del TASK-NNN --reason "Superseded by feat-NNN"
```

Moves task file to `tasks/archive/`, updates TASKS.md status to `[❌]`, appends to Status History.
Does NOT hard-delete — audit trail preserved.
