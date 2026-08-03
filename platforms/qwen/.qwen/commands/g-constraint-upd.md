---
description: 'Edit an existing constraint definition in CONSTRAINTS.md via g-skl-constraints UPDATE operation.'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: guarded_prompt
---
Update an existing constraint. Activates **g-skl-constraints** → UPDATE operation.

```
@g-constraint-upd C-NNN
@g-constraint-upd C-NNN --field enforcement --value "Enforced by g-go-code AC gate step b2"
```

Edits a constraint definition block in CONSTRAINTS.md. Appends to Change Log. Requires a clear rationale for any modification.
