---
description: 'Rename a feature''s slug and title via g-skl-features RENAME, updating file, YAML, and index'
subsystem_memberships: [RELEASE_AND_VERSIONING]
execution_tier: orchestration
---
Rename a feature slug and title. Activates **g-skl-features** → RENAME operation.

```
/g-feat-rename feat-NNN "New Feature Title"
```

Safe rename: updates filename slug, YAML title field, FEATURES.md index row, and any task file cross-references.
Feature ID (feat-NNN) is stable — only the slug and title change.
