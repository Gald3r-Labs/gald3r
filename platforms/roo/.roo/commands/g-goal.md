---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Set, view, or clear a persistent session goal that locks the agent on target across iterations: $ARGUMENTS

## Usage
- `@g-goal <description>` — set active goal (creates/overwrites `.gald3r/config/ACTIVE_GOAL.md`)
- `@g-goal status` — show current active goal, turn count, and progress
- `@g-goal clear` — remove `.gald3r/config/ACTIVE_GOAL.md`
- `@g-goal --from-task T{id}` — derive goal from a task's title and link the task ID

## What it does

`@g-goal` writes a session-persistent goal to `.gald3r/config/ACTIVE_GOAL.md` (YAML frontmatter). Once set:

- `g-go`, `g-go-code`, and `g-go-go` read the goal at session start and inject it as `CURRENT GOAL: <description>` into working context.
- After every AC-gate iteration, the implementing agent self-checks: "Does this action advance the goal?" — drift triggers a re-anchor pass.
- The goal survives context compression and session restarts (file-backed persistence).
- A `turn_budget` (default 50) tracks consumed turns; when exhausted, the loop surfaces a budget notice and pauses for user direction.

This locks the agent on target: the goal is re-checked each turn, drift is self-corrected, and the loop exits gracefully when the turn budget is exhausted.

## Sub-operations

### Set (`@g-goal <description>` or `@g-goal --from-task T{id}`)

1. Parse `<description>` (the literal text passed after `@g-goal`) OR resolve from `--from-task T{id}`:
   - Read `.gald3r/tasks/task{id}_*.md` (look in both active `tasks/` and `archive/tasks/`)
   - Use the task's `title:` field as the description
   - Set `linked_task: T{id}` in the goal frontmatter
2. Get current UTC timestamp (`yyyy-MM-ddTHH:mm:ssZ`).
3. Write `.gald3r/config/ACTIVE_GOAL.md`:
   ```yaml
   ---
   id: goal-YYYYMMDDTHHMMSSZ
   description: "<the goal text>"
   linked_task: T{id}    # or null when free-form
   set_at: <ISO 8601 UTC timestamp>
   turn_budget: 50
   turns_consumed: 0
   set_by: <session identifier or "user">
   ---

   # Active Goal

   <the goal text>

   ## Notes (optional)
   Free-form notes the agent may append while working under this goal.
   ```
4. Confirm to user: `🎯 Goal set: "<description>" (turn budget: 50)`.

### Status (`@g-goal status`)

1. Read `.gald3r/config/ACTIVE_GOAL.md` if present.
2. Display:
   ```
   🎯 Active goal: <description>
   Linked task: T{id} (or "none")
   Set at:      <set_at>
   Turn budget: <turns_consumed> / <turn_budget>
   ```
3. If missing: `No active goal — set one with @g-goal <description>`.

### Clear (`@g-goal clear`)

1. Delete `.gald3r/config/ACTIVE_GOAL.md` if it exists.
2. Confirm: `🎯 Goal cleared.`

## Goal-Locked Loop Integration

When `.gald3r/config/ACTIVE_GOAL.md` exists, every `@g-go`, `@g-go-code`, and `@g-go-go` invocation:

1. **Session-start injection** — read the goal file and prepend to working context:
   `CURRENT GOAL: <description> (turn <turns_consumed>/<turn_budget>, task T{id})`
2. **AC-gate goal alignment** — after each `g-go-code` AC-gate iteration, the implementing agent self-checks: "Did this action advance `<description>`?" If not, re-anchor on the goal before continuing.
3. **Turn accounting** — increment `turns_consumed` on every major loop iteration; if `turns_consumed >= turn_budget`, surface a `🎯 Goal turn budget exhausted` notice and pause for user direction.
4. **Drift correction** — when the agent detects that the work in flight has drifted off-goal (subjective check based on the goal text), restate the goal before the next action.

## Auto-set via `g-go-code --with-goal T{id}`

When `g-go-code` is invoked with `--with-goal T{id}`, behavior is equivalent to `@g-goal --from-task T{id}` followed by `g-go-code tasks {id}` — the goal is set first, then the implementation begins under that goal lock.

The same flag works with `@g-go --with-goal T{id}` and `@g-go-go --with-goal T{id}`.

## Related

- Spec: `.gald3r/tasks/task965_g_go_persistent_goal_ralph_loop.md`
- Pattern: persistent session goal with turn-budget exit
- Integrates with: `g-go`, `g-go-code`, `g-go-go`
- Config file: `.gald3r/config/ACTIVE_GOAL.md`

Let's go.
