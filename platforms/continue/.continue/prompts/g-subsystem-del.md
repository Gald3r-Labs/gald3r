---
description: 'Mark a subsystem deprecated in its spec and SUBSYSTEMS.md via g-skl-subsystems DEPRECATE SUBSYSTEM.'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
---
Deprecate a subsystem. Activates **g-skl-subsystems** → DEPRECATE SUBSYSTEM operation.

```
@g-subsystem-del subsystem-name
@g-subsystem-del subsystem-name --reason "Merged into feature-staging-pipeline"
```

Marks subsystem as `status: deprecated` in spec file YAML frontmatter and SUBSYSTEMS.md index.
Does NOT delete the spec file (audit trail preserved).
Prompts to reassign any tasks still referencing this subsystem name.
