Promote a specced feature to committed — triggers interactive task creation. Activates **g-skl-features** → PROMOTE operation.

```
/g-feat-promote feat-NNN
```

**Flow**:
1. Reads `## Draft Tasks` from the feature staging doc as starting suggestions
2. Interactively asks: "Create task for: '{{description}}'? [y/n/edit]"
3. Creates confirmed tasks via g-skl-tasks (each gets a TASK-NNN ID)
4. Updates feature status: `specced → committed`
5. Links tasks back to feature via `features: [feat-NNN]`

**Prerequisite**: Feature must be `status: specced`. Use `/g-feat-spec feat-NNN` first to add ACs and draft tasks.
