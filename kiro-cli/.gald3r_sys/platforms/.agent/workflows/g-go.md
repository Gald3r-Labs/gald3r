Autonomous backlog execution: $ARGUMENTS

## What This Command Does

Works through the task backlog autonomously, completing as many tasks as possible in a single session. All questions, blockers, and decisions that need human input are collected and presented at the end — never interrupting the flow.

## Execution Protocol

### 1. Load Context (Before Touching Anything)

Read the following files **in this order** to understand the project state:
- `.gald3r/PROJECT.md` — mission, goals, ecosystem context
- `.gald3r/PLAN.md` — current project milestones and development focus
- `.gald3r/FEATURES.md` — PRD index (understand delivery intent)
- `.gald3r/SUBSYSTEMS.md` — subsystem registry (understand scope before touching files)
- `.gald3r/BUGS.md` — open bugs (**read before TASKS** — never implement a fix that re-introduces a known bug)
- `.gald3r/TASKS.md` — master task list
- `.gald3r/CONSTRAINTS.md` — guardrails (if exists)
- `git log --oneline -10` — recent changes

### 2. Build the Work Queue

**Bugs come before tasks.** If BUGS.md has any open bugs with status `Open` or `In Progress`, those enter the queue first — before any pending tasks. A known broken thing should not be skipped in favor of new work.

Work queue construction order:

**Tier 1 — Open bugs (from BUGS.md + individual bug files in `bugs/`):**
- Severity: Critical bugs first, then High, Medium, Low
- Only bugs with no external blocker (e.g. not waiting on an API key or upstream fix)

**Tier 2 — Pending tasks (from TASKS.md):**
- Status is `[ ]` (pending) or `[📋]` (ready)
- No unmet dependencies (prerequisite tasks are `[✅]`)
- Not explicitly marked as `ai_safe: false`
- Not blocked by human input
- Priority: Critical → High → Medium → Low

If `$ARGUMENTS` restricts the queue, supported filters:
- Task IDs: `@g-go tasks 7, 9, 12`
- Bug IDs: `@g-go bugs BUG-003, BUG-007`
- Subsystem: `@g-go subsystem vault-hooks-automation`
- Tier only: `@g-go bugs-only` / `@g-go tasks-only`
- Combined: `@g-go subsystem cross-project bugs-only`


### 3. Work Through Tasks Sequentially

For each task in the queue:

**a) Read the task file** — understand objective and acceptance criteria
**b) Implement the solution** — write code, make changes, satisfy acceptance criteria
**c) Validate** — run any available tests, check lints, verify the work
**d) Update task status** — mark `[✅]` in both the task file and TASKS.md
**e) Move to next task**

### 4. Question & Blocker Collection

**DO NOT** stop to ask questions during execution. Instead, maintain a running log:

```markdown
## Deferred Items

### Questions (Need Human Answer)
- Q1: [question] (encountered during task #X)
- Q2: [question] (encountered during task #Y)

### Blockers (Could Not Proceed)
- B1: Task #X — [why it's blocked]
- B2: Task #Y — [missing dependency / credentials / unclear spec]

### Decisions Made (FYI)
- D1: Task #X — chose approach A over B because [reason]
- D2: Task #Y — interpreted ambiguous spec as [interpretation]
```

### 5. Session Summary (Always End With This)

After completing as many tasks as possible, present:

```markdown
## Backlog Execution Summary

### Completed
- [✅] Task #X: {title}
- [✅] Task #Y: {title}

### Skipped (Blocked)
- Task #Z: {reason — dependency, needs human, unclear spec}

### Failed (Attempted but couldn't finish)
- Task #W: {what went wrong}

### Deferred Questions & Blockers
{the collected questions and blockers from step 4}

### Recommended Next Steps
1. [what to do next]
2. [what to do next]

### Git Status
- Changes committed: Yes/No
- Uncommitted changes: {list if any}
```

## Behavioral Rules

| Rule | Why |
|------|-----|
| Never ask questions mid-execution | The whole point is uninterrupted autonomous work |
| Log every decision you make autonomously | User needs to review what you decided |
| Skip tasks you can't complete, don't fail the whole run | Maximize total output |
| Commit after each completed task (if user allows) | Preserve progress incrementally |
| Respect CONSTRAINTS.md | Don't violate project guardrails |
| Stop if a task would be destructive (schema drops, data loss) | Safety first — log it as a blocker |

## Usage Examples

**Work everything available:**
```
@g-go
```

**Work specific tasks:**
```
@g-go tasks 7, 9, 12
```

**Work specific bugs:**
```
@g-go bugs BUG-003, BUG-007
```

**Work a specific subsystem (bugs + tasks):**
```
@g-go subsystem vault-hooks-automation
```

**Bugs only:**
```
@g-go bugs-only
```

**Work only critical/high priority:**
```
@g-go critical and high only
```

Let's get to work.
