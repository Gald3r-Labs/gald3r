---
description: 'Archive a feature staging doc via g-skl-features ARCHIVE FEATURE, moving it to features/archive/'
subsystem_memberships: [RELEASE_AND_VERSIONING]
execution_tier: orchestration
---
Archive a feature staging doc. Activates **g-skl-features** → ARCHIVE FEATURE operation.

```
@g-feat-del feat-NNN
@g-feat-del feat-NNN --reason "Superseded by feat-MMM"
```

Marks feature as `status: archived` in YAML and FEATURES.md index. Moves file to `features/archive/`.
Does NOT hard-delete — audit trail preserved.
