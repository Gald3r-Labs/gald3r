---
id: rubric.swot
kind: rubric
title: "SWOT Review Rubric"
inputs: []
tier: full
source: skills/g-skl-swot-review/SKILL.md
version: 1
---
# SWOT Review Rubric

Perform a structured SWOT analysis on the current project phase. Assess across
five dimensions, then synthesize findings into the S/W/O/T framing.

## The Five Assessment Dimensions
1. Phase Progress — completed vs. total tasks per phase; velocity (tasks/week over
   the last 30 days); stalled tasks (in-progress with no update in 48h+); phases
   over 80% done flagged for gate review.
2. Architectural Compliance — recent changes vs. declared constraints and subsystem
   boundaries; flag new file patterns that don't match declared subsystems (drift).
3. Code Quality Signals — TODO/FIXME density; oversized files; files changed with
   no corresponding test changes; stub patterns (pass, NotImplementedError, "not
   implemented" throws).
4. Goal Alignment — does recent work map to stated goals? Flag goals with no
   activity in 14+ days and orphan tasks aligned to no goal.
5. Technical Debt — open bugs by severity; follow-up tasks from completion gates;
   stale queue entries; debt-to-feature ratio = (bug_fix + refactor) / feature tasks.

## S/W/O/T Framing (how to sort findings)
- Strengths — completed tasks, clean commits, resolved bugs, steady velocity.
- Weaknesses — stalled tasks, growing bug count, constraint violations, untested changes.
- Opportunities — idle goals ready to resume, unblocked dependencies, idea-board items.
- Threats — accumulating technical debt, stale tasks, architectural drift.

End with prioritized, actionable recommendations — not just observations.

## Health Score (0–100)
Start at 100, then subtract:
- −5 per stalled task (in-progress > 48h)      − −3 per task awaiting verification > 24h
- −2 per open bug                              − −5 per critical bug
- −1 per TODO added in the last 7 days         − −3 per oversized file
- −5 per architectural constraint violation
- +2 per task completed in the last 7 days (bonus, capped at +20)

A critical score (<40) signals the phase needs intervention before proceeding.
