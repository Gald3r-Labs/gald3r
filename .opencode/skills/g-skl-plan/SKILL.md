---
name: g-skl-plan
description: Own and manage PLAN.md (master strategy) and features/ (individual Feature files) — create plans, stage features, validate scope, and keep the deliverable index current.
---
# g-plan

**Files Owned**: `.gald3r/PLAN.md`, `.gald3r/FEATURES.md`, `.gald3r/features/*.md`

**Activate for**: "create plan", "new feature", "stage feature", "define requirements", "what's the plan", "update PLAN.md", "write PRD", "spec this out".

**Hierarchy**: `PLAN.md` is the master strategy. `FEATURES.md` is the feature index. Each `features/*.md` is a staged feature moving through: `staging → specced → committed → shipped`.

---

## Operation: CREATE / UPDATE PLAN.md

`PLAN.md` is the one-page strategy doc — deliverable index, build order, milestone history. Kept short; details live in Feature files.

```markdown
# PLAN.md — {project_name} Master Plan

## Current Focus
{Describe current development focus — 1-2 sentences}

## Deliverable Index

| ID | Title | Status | Subsystems | Notes |
|----|-------|--------|------------|-------|
| feat-001 | Foundation | shipped | task-mgmt, setup | Completed 2026-01-01 |

## Build Order

### Active Work
{List committed/specced features with priority}

### Completed
{List shipped features}

## Milestone History
{Record major direction changes with dates}
```

> **MANDATORY FOLLOW-THROUGH**: If you add any feature rows to the Deliverable Index,
> you MUST in the same response:
> 1. Create each referenced Feature file at `.gald3r/features/featNNN_descriptive_name.md` (use the STAGE FEATURE operation below)
> 2. Add each Feature to `FEATURES.md` index
>
> Do NOT leave PLAN.md referencing features that don't have files.

---

## Operation: STAGE FEATURE (new feature, defaults to staging)

1. **Scope check** (ask before writing anything):
   1. What user-visible capability does this enable?
   2. Which subsystems are affected?
   3. What approach(es) have been identified?

2. **Determine next Feature ID**: read `FEATURES.md`, find highest feat-NNN → increment

3. **Create Feature file** at `.gald3r/features/featNNN_descriptive_name.md`:
```yaml
---
id: feat-NNN
title: 'Feature Title'
status: staging          # staging | specced | committed | shipped
goal: ''                 # optional: G-NN from PROJECT.md
min_tier: slim           # slim | full | adv
subsystems: []
harvest_sources: []
created_date: 'YYYY-MM-DD'
promoted_date: ''
committed_date: ''
completed_date: ''
---

# Feature: {title}

## Summary
[1-3 sentence description of the user-visible capability]

## Collected Approaches
<!-- approaches gathered from harvest tools, discussions, research -->

## Potential Deliverables
- Deliverable 1

## Draft Tasks
<!-- populated manually when promoting to specced -->
- [ ] Task: description
```

4. **Add to FEATURES.md** index under Staging section

5. **Optionally add to PLAN.md** Deliverable Index if strategically significant

---

## Operation: SPEC FEATURE (staging → specced)

When enough research exists, promote staging → specced by:
1. Updating `status: specced` in the feature file YAML
2. Adding `promoted_date: YYYY-MM-DD`
3. Filling in formal Acceptance Criteria
4. Moving feature row in `FEATURES.md` to Specced section

---

## Operation: UPDATE FEATURE STATUS

Status flow: `staging → specced → committed → shipped`

Update status in the Feature file YAML and sync to `FEATURES.md` index row.

---

## FEATURES.md Structure

```markdown
# FEATURES.md — {project_name}

## Features Index

### Shipped
| ID | Title | Status | Tasks | Notes |

### Committed
| ID | Title | Status | Tasks | Notes |

### Staging / Specced
| ID | Title | Status | Notes |

<!-- Status: staging | specced | committed | shipped -->
```
