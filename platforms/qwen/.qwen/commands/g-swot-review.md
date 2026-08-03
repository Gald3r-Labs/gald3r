---
description: 'Run a 5-pass SWOT analysis on the current project phase and write a report to .gald3r/logs/swot/.'
argument-hint: '[notes]'
subsystem_memberships: [BUG_AND_QUALITY]
execution_tier: orchestration
---
Run SWOT analysis on current project phase: $ARGUMENTS



Run a structured SWOT analysis on the current project phase.

## Behavior

1. Read the `g-swot-review` skill at `.cursor/skills/g-swot-review/SKILL.md`
2. Execute all 5 analysis passes as described in the skill
3. Write report to `.gald3r/logs/swot/YYYY-MM-DD_swot_review.md`
4. Display summary to user
