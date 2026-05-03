---
name: g-skl-swot-review
description: >-
  Automated SWOT analysis for the current project phase. Reviews progress,
  architectural compliance, code quality, goal alignment, and technical debt.
  Runs weekly via heartbeat or on-demand.
---

# g-swot-review

Perform a structured SWOT analysis on the current project phase.

## When to Use

- Weekly scheduled review via heartbeat (`weekly-swot` routine)
- Manual trigger: `@g-swot-review`
- When phase progress needs assessment
- Before phase completion gate review

## Analysis Passes

Execute all 5 passes in order, collecting metrics for the report.

### Pass 1: Phase Progress Assessment

1. Read `.gald3r/TASKS.md` — count completed vs total per phase
2. Read task files to get `completed_date` timestamps
3. Calculate velocity: tasks completed per week over last 30 days
4. Identify stalled tasks: `status: in-progress` with no heartbeat update in 48+ hours
5. Flag phases approaching completion (>80% done) for gate review

### Pass 2: Architectural Constraint Compliance

1. Read `.gald3r/CONSTRAINTS.md` (if exists)
2. Run `git log --since="7 days ago" --oneline` to get recent commits
3. Check `.gald3r/SUBSYSTEMS.md` for undeclared subsystem interactions
4. Flag any new file patterns not matching declared subsystems

### Pass 3: Code Quality Signals

1. Run `git diff HEAD~7..HEAD --stat` to get changed files
2. Count TODO/FIXME comments: `rg -c "TODO|FIXME" --glob "*.py" --glob "*.ts" --glob "*.ps1"`
3. Check for files exceeding 1500 lines (gald3r rule)
4. Identify files changed but with no corresponding test changes
5. Flag stub patterns: `pass`, `NotImplementedError`, `throw new Error("not implemented")`

### Pass 4: Goal Alignment

1. Read `.gald3r/PROJECT.md` goals section (if exists)
2. For each active goal, check if recent tasks reference it
3. Identify goals with no task activity in 14+ days
4. Flag orphan tasks (tasks not aligned to any goal)

### Pass 5: Technical Debt Inventory

1. Read `.gald3r/BUGS.md` — count open bugs by severity
2. Count follow-up tasks from TODO completion gate (tasks with `dependencies` pointing to completed tasks)
3. Check `.gald3r/config/WAKEUP_QUEUE.md` for stale entries (>7 days old)
4. Estimate debt-to-feature ratio: (bug_fix + refactor tasks) / (feature tasks)

## Output Format

Write report to `.gald3r/logs/swot/YYYY-MM-DD_swot_review.md`:

```markdown
---
date: YYYY-MM-DD
type: swot_review
phase: N
health_score: NN
trigger: scheduled|manual
---

# SWOT Review — Phase N: {Phase Name}

## Summary
- **Phase Progress**: N/M tasks (X%)
- **Velocity**: N.N tasks/week (last 30 days)
- **Health Score**: NN/100

## Strengths
- [From completed tasks, clean commits, resolved bugs]

## Weaknesses
- [From stalled tasks, growing bug count, constraint violations]

## Opportunities
- [From idle goals, unblocked dependencies, idea board items]

## Threats
- [From technical debt, stale tasks, architectural drift]

## Recommendations
1. [Prioritized action items]

## Raw Metrics
| Metric | Value |
|--------|-------|
| Tasks completed (7d) | N |
| Bugs opened (7d) | N |
| Bugs closed (7d) | N |
| TODO comments added (7d) | N |
| Files > 1500 lines | N |
| Stalled tasks | N |
| Orphan tasks (no goal) | N |
```

## Health Score Calculation

Start at 100, subtract:
- -5 per stalled task (in-progress > 48h)
- -3 per task awaiting verification > 24h
- -2 per open bug
- -5 per critical bug
- -1 per TODO comment added in last 7 days
- -3 per file > 1500 lines
- -5 per architectural constraint violation
- +2 per task completed in last 7 days (bonus, cap at +20)

## Integration

- Heartbeat routine: `weekly-swot` (Fridays 2:00 PM)
- KPI metrics captured: `health_score`, `stalled_tasks`, `goal_alignment_ratio`, `constraint_violations`
- Critical health (<40) triggers WAKEUP_QUEUE entry
