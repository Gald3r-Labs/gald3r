---
description: 'Summarize vault health: note counts by type, active paths, recent log.md activity, migration warnings'
argument-hint: '[none]'
subsystem_memberships: [VAULT_AND_RESEARCH]
execution_tier: orchestration
---
Show vault status: $ARGUMENTS

## What This Command Does

Summarizes vault health, scale, and recent activity.

## Report

- active vault path
- active repos mirror path
- total note count
- counts by note type
- recent `log.md` entries
- migration candidate warning if local fallback notes exist
- next recommended actions
