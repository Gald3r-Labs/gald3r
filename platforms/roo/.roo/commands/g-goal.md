---
description: 'Set, view, or clear a persistent session goal (ACTIVE_GOAL.md) with turn-budget drift correction for g-go.'
argument-hint: '<description> | status | clear | --from-task T<id>'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: guarded_prompt
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
2. **Inventory-shaped condition check (BUG-645 Fix Direction #1).** Before writing the
   file, scan `<description>` for an INVENTORY shape — a literal count of items
   ("I have N tasks that are not complete", "finish the 40 open bugs", "clear all N
   items") rather than an OUTCOME. An inventory-shaped condition becomes
   **permanently unsatisfiable** the moment real work starts: completing items moves
   the count further from N, never toward it. If detected:
   - Propose an outcome-shaped rewrite to the user before writing the file, e.g.
     `"complete the ~40 open tasks"` → `"backlog drained: zero runnable non-gated
     tasks remain"`.
   - Only proceed with the literal inventory wording if the user explicitly confirms
     they want it as-is — never silently auto-rewrite.
3. Get current UTC timestamp (`yyyy-MM-ddTHH:mm:ssZ`).
4. Write `.gald3r/config/ACTIVE_GOAL.md`:
   ```yaml
   ---
   id: goal-YYYYMMDDTHHMMSSZ
   description: "<the goal text>"
   linked_task: T{id}    # or null when free-form
   set_at: <ISO 8601 UTC timestamp>
   turn_budget: 50
   turns_consumed: 0
   set_by: <session identifier or "user">
   condition_discharged: false
   reinvoke_count: 0
   zero_remaining_work_streak: 0
   last_remaining_work_count: ""
   stagnant_checks: 0
   ---

   # Active Goal

   <the goal text>

   ## Notes (optional)
   Free-form notes the agent may append while working under this goal.
   ```
5. Confirm to user: `🎯 Goal set: "<description>" (turn budget: 50)`.

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

## Quit Conditions (BUG-645 — mechanically enforced, not prose-only)

Items 1–4 above are agent self-discipline; they are backed by a **mechanical
Stop-hook enforcement layer**, `g-hk-goal-stop-detect` (fires on the `stop` event,
mirroring `g-hk-ggo-stop-detect`'s proven `authorized_hard_stop` +
`min(budget, ceiling)` pattern from the g-go-go autopilot loop), so a session can
never livelock re-blocking Stop with identical feedback the way the BUG-645 incident
did (~70 minutes, ~25 identical no-op turns after the goal's work was already done):

- **Terminal-state clause** — set `condition_discharged: true` in
  `.gald3r/config/ACTIVE_GOAL.md`'s frontmatter the moment you determine the goal is
  genuinely satisfied OR has become permanently unsatisfiable (mirrors
  `authorized_hard_stop` semantics — a documented, sanctioned terminal state, never
  silence). The hook also auto-detects this: when the project's open task/bug queue
  reads empty across 2 consecutive stop checks, it sets this flag itself and allows
  the stop.
- **Re-invoke ceiling** — the hook caps re-blocks at
  `min(turn_budget - turns_consumed, 5)`; once reached, it allows the stop and
  surfaces a notification instead of looping further.
- **Escalation over repetition** — if the remaining-work count has not moved across
  3 consecutive stop checks (the actual BUG-645 signature: identical feedback, zero
  forward progress), the hook allows the stop and notifies rather than waiting for
  the numeric ceiling.

None of this weakens genuine goal enforcement — a satisfiable, still-in-progress
goal continues to re-block exactly as items 1–4 describe. See
`hooks/g-hk-goal-stop-detect.md` for the full state machine.

## Auto-set via `g-go-code --with-goal T{id}`

When `g-go-code` is invoked with `--with-goal T{id}`, behavior is equivalent to `@g-goal --from-task T{id}` followed by `g-go-code tasks {id}` — the goal is set first, then the implementation begins under that goal lock.

The same flag works with `@g-go --with-goal T{id}` and `@g-go-go --with-goal T{id}`.

## Related

- Spec: `.gald3r/tasks/task965_g_go_persistent_goal_ralph_loop.md`
- Pattern: persistent session goal with turn-budget exit
- Integrates with: `g-go`, `g-go-code`, `g-go-go`
- Config file: `.gald3r/config/ACTIVE_GOAL.md`
- Quit-condition enforcement: `hooks/g-hk-goal-stop-detect.py` (BUG-645) — terminal-state
  clause + re-invoke ceiling, mirroring `hooks/g-hk-ggo-stop-detect.py`'s proven pattern.

Let's go.
