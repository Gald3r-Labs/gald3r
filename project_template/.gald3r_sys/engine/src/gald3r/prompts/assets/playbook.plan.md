---
id: playbook.plan
kind: playbook
title: "Planning & Feature-Staging Judgment"
inputs: []
tier: slim
source: skills/g-skl-plan/SKILL.md
version: 1
---
# Planning & Feature-Staging Judgment

The mechanics (ID allocation, writing `PLAN.md` / `FEATURES.md` / `features/*.md`,
index regeneration) are handled by the engine (`gald3r feature …` / `gald3r goal …`).
This asset is the *judgment* the engine cannot do: what to plan, and when to promote.

## The Hierarchy
`PLAN.md` is the one-page master strategy (current focus, deliverable index, build
order, milestone history) — kept short; details live in Feature files. Each feature
moves through `staging → specced → committed → shipped`.

## Scope Check (ask BEFORE staging anything)
1. What user-visible capability does this enable?
2. Which subsystems are affected?
3. What approach(es) have been identified?

If you can't answer #1 in one sentence, it isn't a feature yet — it's an idea
(capture it to the idea board instead).

## Promotion Judgment
- **staging → specced** — promote only when enough research/approaches exist to write
  *formal acceptance criteria*. Specced means "we know what done looks like."
- **specced → committed** — promote when you're ready to create real tasks for it.
  Committed features must have tasks; an empty committed feature is a planning smell.
- **committed → shipped** — only when fully implemented AND verified.

## Build-Order Thinking
Order by dependency and leverage, not by enthusiasm. Surface the *active work* (the
committed/specced features in priority order) and keep completed work as history.
Record major direction changes in milestone history with dates — the "why" is the
durable part.

## Follow-Through (non-negotiable)
Never leave `PLAN.md` referencing a feature that has no file, and never leave a
deliverable-index row without its corresponding staged feature. Plan and artifacts
move together or not at all.

## LOCK_PLAN (implementation planning gate)
Before implementation on a task, derive a *locked* plan into the task file:
objectives (acceptance criteria reworded), the relevant active constraints (by ID +
one-line summary, scoped to overlapping subsystems), and concrete numbered steps that
each name a file and an operation. Lock it. On deviation, mark `DEVIATION_DETECTED`,
note what changed against the affected step, then re-lock before proceeding — review
compares the locked steps against the actual diff, and undocumented divergence fails.
