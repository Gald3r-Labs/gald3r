---
description: 'Deprecated alias for g-feat-add; stage a new feature via g-skl-features STAGE (status: staging)'
subsystem_memberships: [RELEASE_AND_VERSIONING]
execution_tier: guarded_prompt
---
> **Deprecated**: Use `@g-feat-add` instead. This alias is kept for backward compatibility.

Stage a new feature in the feature backlog. Activates **g-skl-features** → STAGE operation.

Creates `features/featNNN_slug.md` with `status: staging`. Does NOT create tasks.
