---
name: g-skl-project
description: Own and manage PROJECT.md (mission, goals, project linking). Single source of truth for project identity. Constraints operations delegated to g-skl-constraints.
token_budget: medium
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-project

**Files Owned**: `.gald3r/PROJECT.md`  
**Constraint operations**: delegated to `g-skl-constraints` (see `g-skl-constraints/SKILL.md`)

**Activate for**: "update goals", "define constraints", "what's the mission", "project linking", "add constraint", "update PROJECT.md", setup/planning steps that need project context.

---

## Operation: CREATE / UPDATE PROJECT.MD

`PROJECT.md` is the project identity document. It holds mission, goals, and cross-project linking. Agents read it at session start to orient themselves.

**Workflow Profile / Project Type (T1280 epic, reconciled by BUG-092 / T1335)**: the active task-lifecycle vocabulary is selected by the **hybrid activation chain** (highest priority first):
1. a task file's own `workflow_profile:` frontmatter,
2. PROJECT.md's optional `workflow_profile:` field,
3. `project_type=` in `.gald3r/.identity` (the primary switch),
4. `freeform` (final fallback).

Canonical profile filenames equal the `project_type` value: `software_development` (default), `content_creation`, `3d_modeling`, `research_analysis`, `freeform` — stored as `.gald3r/config/workflow_profiles/<project_type>.yaml` (schema B). Drop additional profiles there to extend. The `g-skl-project` skill reads/writes `project_type=` in `.identity` (set during `g-setup`); `g-skl-tasks` § Workflow Profiles documents the schema; `g-skl-project-types` `load_profile.py` resolves the chain. (The legacy T1238 `software_dev`/`research` files were archived to `.gald3r/archive/superseded/workflow_profiles/`.)

```markdown
---
workflow_profile: content_creation   # optional override; default = .identity project_type=
---
# PROJECT.md — {project_name}

## Vision
[2-3 sentences: what the world looks like when this succeeds. Plain language — readable by a manager, customer, or exec without technical background. No acronyms, no stack names.]

## Mission
[One paragraph: what this project does, who it's for, and what problem it solves. If you can't explain it without saying "microservices", rewrite it.]

## Goals
Business-readable outcomes. No developer jargon.

- **G-01**: [A concrete outcome users or the business will experience. e.g. "Customers can track their order status without calling support."]
- **G-02**: [Another outcome. e.g. "The team can ship fixes without a scheduled maintenance window."]

## Non-Goals (Explicitly Out of Scope)
- [e.g. "This project will not replace the billing system."]

## Project Linking
No parent, sibling, or child projects configured yet.
Use `@g-topology` to manage relationships.

## Key References
- **Plan**: `PLAN.md` | **Constraints**: `CONSTRAINTS.md` | **Feature**: `features/` | **Tasks**: `TASKS.md`
```

**Gather goals** (ask if not clear from context):
- "What outcome will users experience when this is done?"
- "What does success look like in plain terms, without technical details?"
- "What are we explicitly NOT building?"
- "How will a non-technical person know this worked?"

**Goal quality check** — goals should pass the "manager test": can someone without a CS degree read this and know whether it was achieved? If not, rewrite it.

**Goal change protocol**: never delete — mark old goals as `complete` or `retired` + add Goal Log entry.

---

## Constraint Operations → Delegated to g-skl-constraints

**`CONSTRAINTS.md` is fully owned by `g-skl-constraints`** as of T041 (2026-04-07).

For any constraint operation — add, update, check, list — use `@g-constraints` or read `g-skl-constraints/SKILL.md`.

`g-skl-project` no longer writes to `CONSTRAINTS.md`.

---

## Session Start Display

When PROJECT.md exists, surface:
```
📌 SESSION CONTEXT
Mission: [1 line from PROJECT.md]
Project type: [project_type from .identity] | github_integration: [enabled/disabled]
Goals: G-01: [name] | G-02: [name]
Constraints: [N] active
```

---

## Decision Validation

When creating tasks or making architecture decisions, briefly check:
- "This aligns with G-{ID}" ✅
- "This conflicts with Non-Goal: [X]" ⚠️ — flag for user
- "This violates C-{ID}" 🚫 — stop and explain

---

## Operation: SPECIFICATIONS REVIEW

When `@g-status` or `@g-project` is run, or when explicitly asked to review specs:

1. **Check `specifications_collection/`** exists in `.gald3r/`
2. **List all spec files** — note dates and source
3. **Find last `[✅]` task date** from TASKS.md (most recently completed)
4. **Flag unreviewed**: any spec file with a date **newer** than the last completed task:
   ```
   ⚠️ Unreviewed spec: 2026-04-07_api_contract_v2.md (newer than last completed task 2026-04-06)
   ```
5. **Surface in context**: "Specs: {N} in specifications_collection/ (newest: {date})"

This step is read-only — agents surface specs, they do not modify them.
