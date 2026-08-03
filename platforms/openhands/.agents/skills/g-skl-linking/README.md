---
subsystem_memberships: [WORKSPACE_COORDINATION, PROJECT_IDENTITY_SETUP]
---
# g-skl-linking
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Unified linking file-mirror (D7 / T1610): pulls the server-owned world_tree linking
registry (parent/child/sibling + project_type/skills, keyed by project UUID) and writes
the human-readable local mirror under `.gald3r/linking/`. Offline, the local mirror is
authoritative; reconcile on reconnect is non-destructive (conflicts open review items,
never overwrite).

## When to use

- Invoke via `@g-linking-pull` / `@g-linking-status` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- `g-skl-wpac-claim` / `g-skl-wpac-adopt` / `g-skl-wpac-spawn` — register edges; this skill mirrors them
- `g-skl-workspace` — owns the shared connectivity shim + verb transport
