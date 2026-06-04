---
subsystem_memberships: [TASK_MANAGEMENT]
---
# g-mission

Run an autonomous goal-locked loop until a verifiable completion condition is satisfied: $ARGUMENTS

Aliases: `@g-juggernaut`, `@g-kamikaze`

## Usage

```
@g-mission <condition>
@g-mission <condition> --budget <N>
@g-mission <condition> --until-empty
@g-mission <condition> --until-empty --budget <N>
@g-mission status
@g-mission clear
@g-mission --from-task T{id}
```

### Overnight / extended AFK runs (IMPORTANT — read before going AFK)

**Do NOT type `@g-mission resume` manually for extended runs.** That requires you to be present each time. Instead, use the wrapper script from a PowerShell terminal — it handles all auto-resumes for you:

```powershell
# Run this in a PowerShell terminal before going AFK / to bed
# It loops automatically — you do not need to return until it stops itself
.\scripts\mission-overnight.ps1
```

The script calls `claude -p "@g-mission resume --until-empty --budget 999"` in a loop. It parses `EXIT_REASON:` from each session to decide auto-resume vs real stop. You do nothing until the script exits or you come back.

For unattended runs (overnight, meetings, AFK), use the wrapper script instead of typing `@g-mission resume` between sessions:

```powershell
# Resume an existing mission — runs until QUEUE_EMPTY, CONDITION_MET, or a real blocker
.\scripts\mission-overnight.ps1

# Start a new mission and drain all ai_safe tasks overnight
.\scripts\mission-overnight.ps1 -Condition "drain all ai_safe tasks"

# Use a specific model
.\scripts\mission-overnight.ps1 -ClaudeArgs "--model claude-opus-4-7"
```

The script loops the `claude` CLI invocation automatically:
- `CONTEXT_GATE` and `BUDGET_EXHAUSTED` → **transparent auto-resume** (no human input, 5-second gap between sessions)
- `QUEUE_EMPTY`, `CONDITION_MET` → loop ends (success)
- Any blocking code (`AI_SAFE_BLOCKED`, `BLAST_RADIUS_HIGH`, `PCAC_CONFLICT`, etc.) → loop ends, human review required

A 12-hour overnight run at 20-30 min per session = up to 36 sessions × 3-10 tasks = 100-360 tasks while you sleep.

**Why sessions exist at all:** The agent's context window has a hard ceiling — at ~75% fill, continuing mid-task would risk memory loss and partial work. The checkpoint commits everything cleanly, then the wrapper relaunches immediately. Context resets are transparent in overnight mode.

**Equivalent to Claude Code's `/goal`:** `scripts/mission-overnight.ps1` is our implementation of the same pattern Claude Code uses natively — a post-session evaluator that fires automatically without user prompts.

## What it does

`g-mission` is gald3r's autonomous completion loop. You state a verifiable end condition; the agent works toward it across as many `g-go` iterations as needed. After every iteration a lightweight evaluator checks whether the condition holds. If not, the loop continues. If yes, the mission is complete.

This is distinct from `@g-goal` (which sets a goal that `g-go` reads but does not loop autonomously) and from `@g-go-go` (which runs until tasks are exhausted). `g-mission` runs until YOUR stated condition is provably true — the stopping criterion is yours, not the task queue.

### `--until-empty` mode

When `--until-empty` is passed, the mission does **not** stop when the stated condition is first achieved. Instead:

1. The stated condition becomes a **gate** — it must be met before the second phase begins.
2. Once the gate passes, the mission automatically transitions to `@g-go-go` mode and continues working through all remaining `ai_safe: true` tasks in the queue.
3. The mission ends only when **both** the condition is met **and** the `ai_safe` queue is empty (or budget is exhausted).
4. The turn budget applies across both phases combined.

This is the closest analog to `/goal` on other platforms — state the primary objective, then let the agent clear the surrounding backlog without stopping.

```
# Example: verify CLI works, then clear the rest of the safe backlog
@g-mission "gald3r_agent CLI exits 0 with ollama" --until-empty --budget 60
```

Write `mode: until-empty` in `ACTIVE_MISSION.md` when this flag is active so the evaluator knows to switch phases rather than terminate on first success.

#### ⛔ CRITICAL — `--until-empty` converts soft-pauses to skips

**In `--until-empty` mode, the following items that would normally pause a standard mission become SKIPS instead.** The agent logs each skip to `temp_scripts/_deferred_questions.md` and immediately moves on to the next task. They do NOT pause the loop. They do NOT trigger a summary. They do NOT end the session early.

| Normally pauses | `--until-empty` behavior |
|---|---|
| `blast_radius: high` | **SKIP** — log with reason, continue |
| Task scope exceeds one session | **SPLIT** into subtasks, tackle T{id}a, continue |
| Cross-repo touches (workspace_repos: [...]) | **Run the Clean Controller Gate on each repo in the touch set first.** If all pass (clean or only owned paths dirty), proceed with the full task. Only skip if a required repo is inaccessible on disk or has unrelated dirty paths that block a safe commit. Note: `workspace_touch_policy: member_only` is a **write-scope limiter** (changes land in the named member repo) — it is **NOT** a location gate requiring the agent to run from inside the member repo. The controller implements `member_only` tasks by writing to member on-disk paths after Clean Controller Gate passes. (BUG-098) |
| Design/product judgment required | **SKIP** — log as "needs human decision", continue |
| Missing prereq infrastructure (e.g., file doesn't exist yet) | **SKIP** — log as "blocked by missing dep", continue |

**Only these items remain as true pauses even in `--until-empty` mode:**

- `ai_safe: false` — hard stop, always
- PCAC `[ORDER]` or `[CONFLICT]` inbox items — hard stop, always
- Budget exhausted — hard stop, always

Everything else: **skip and continue.** The deferred questions file is the skip ledger. The mission loop does NOT stop because a task is hard, complex, or touches other repos.

#### ⛔ CRITICAL — "the remaining queue looks hard" is NOT a valid stop condition

**The agent must scan tasks individually, not assess the queue globally.** The following patterns are FORBIDDEN as stop reasons in `--until-empty` mode:

| Forbidden stop reason | What to do instead |
|---|---|
| "Most remaining tasks are cross-repo" | Scan each one. Run the Clean Controller Gate per repo. Proceed if repos are accessible and clean. Most gald3r work IS cross-repo — blanket skipping cross-repo tasks defeats the mission. |
| "Most remaining tasks need design judgment" | Scan each one. Skip the judgment-heavy ones. Keep looping. |
| "The queue looks like it's mostly hard" | This is not a scan. Do the scan. |
| "Nothing obvious is left" | Verify by actually reading every open/ task frontmatter. |
| "I recommend the user seed more tasks" | Only acceptable AFTER the loop has individually assessed and skipped every remaining task. |

**Required loop termination check in `--until-empty` mode:**

Before writing a session checkpoint and stopping, the agent MUST be able to answer YES to one of:
1. Context ≥ 75% (checkpoint, resume later)
2. Budget exhausted
3. Hard stop condition hit (`ai_safe: false` or PCAC conflict)
4. **Every single task in `open/`, `in-progress/`, and `paused/` has been individually read and individually either claimed, completed, or logged as a named skip in `_deferred_questions.md`**

A global queue assessment does not satisfy condition 4. If the agent has not read every task file, it has not finished the loop.

> **Alias names explained:**
> - `@g-juggernaut` — unstoppable forward momentum; no backing down until condition met
> - `@g-kamikaze` — all-in; burns turns until done

---

## Write an effective condition

The evaluator judges your condition against what the agent has surfaced in the conversation. Write the condition as something the agent's own output can demonstrate:

| Good condition | Why |
|---|---|
| `all tests in gald3r_throne pass and tsc exits 0` | Agent runs tests; output proves it |
| `T{id} is marked [✅] in TASKS.md` | Agent updates TASKS.md; file state proves it |
| `desktop/ and docker/ removed from gald3r_dev (git status clean)` | Agent runs git rm + status; output proves it |
| `CHANGELOG.md has entries for every completed task this week` | Agent reads git log + CHANGELOG; diff proves it |

**Tips:**
- One measurable end state per condition
- State how the agent should prove it (`tsc exits 0`, `git status clean`, `vitest: 0 failed`)
- Add constraints that must hold (`no other test files modified`, `no new bugs introduced`)
- To bound duration: add `or stop after N turns` to the condition text

---

## Steps

### Set (`@g-mission <condition>` or `@g-mission --from-task T{id}`)

1. Parse the condition text OR resolve from task:
   - `--from-task T{id}`: read the task's `title:` and acceptance criteria as the condition; set `linked_task: T{id}`
   - Free-form: use the literal text after `@g-mission`
2. Parse `--budget <N>` if supplied (default: 30 iterations).
3. Parse `--until-empty` if supplied; set `mode: until-empty` in frontmatter (default: `mode: condition-only`).
4. Write `.gald3r/config/ACTIVE_MISSION.md`:
   ```yaml
   ---
   id: mission-YYYYMMDDTHHMMSSZ
   condition: "<the condition text>"
   linked_task: T{id}          # or null
   set_at: <ISO 8601 UTC>
   turn_budget: 30             # overridden by --budget N
   turns_consumed: 0
   last_eval_reason: ""
   mode: condition-only        # condition-only | until-empty
   phase: gate                 # gate (working toward condition) | drain (g-go-go clearing queue)
   status: active              # active | achieved | abandoned
   set_by: <session or "user">
   ---

   # Active Mission

   **Condition**: <condition text>

   ## Evaluator Notes
   <!-- Evaluator appends reason after each turn -->
   ```
4. Set `@g-goal` from the same condition (so `g-go` has the goal injected into context).
5. Announce: `🎯 Mission set: "<condition>" (budget: N turns)`
6. **Immediately begin**: run `@g-go-go` with the mission context injected.

### Autonomous loop (runs internally after each g-go-go iteration)

After every `g-go` iteration completes:

1. **Evaluate**: the agent self-checks the condition against what it has surfaced in the conversation:
   - Run the stated verification command/check if one was specified
   - Read the relevant file state (TASKS.md, git status, test output, etc.)
   - Determine: does the condition hold? Yes / No + reason
2. **If NO**: append evaluator reason to `ACTIVE_MISSION.md` `## Evaluator Notes`, increment `turns_consumed`, continue loop
3. **If YES** (`mode: condition-only`):
   - Update `ACTIVE_MISSION.md` `status: achieved`
   - Clear `ACTIVE_GOAL.md` (`@g-goal clear`)
   - Report the **final mission summary** (see format below)
3. **If YES** (`mode: until-empty`, `phase: gate`):
   - Update `ACTIVE_MISSION.md` `phase: drain`
   - Report: `✅ Gate condition met after N turns. Transitioning to drain phase — clearing ai_safe task queue.`
   - **Do NOT offer push here** — the mission is still running; continue looping with `@g-go-go` semantics
   - When the `ai_safe` queue is empty:
     - Update `ACTIVE_MISSION.md` `status: achieved`
     - Clear `ACTIVE_GOAL.md`
     - Report the **final mission summary** (see format below)
3. **If YES** (`mode: until-empty`, `phase: drain`): skip re-evaluating the condition; check if `ai_safe` queue is empty
   - If tasks remain: claim next `ai_safe` task, continue loop — **do NOT offer push between tasks**
   - If queue empty: `status: achieved`, report the **final mission summary** (see format below)
#### Final mission summary format (used at `status: achieved` only)

```
✅ Mission complete after N turns: "<condition>"

Tasks shipped: T{id1} ({title}), T{id2} ({title}), ...
Commits: {N} commits on {branch} — {first_sha}..{last_sha}

Review your changes, then push when ready:
  git log origin/{branch}..HEAD --oneline   # review commit list
  git push origin {branch}                  # publish when satisfied
```

**Push offer rules:**
- The push offer appears **once** — in this final summary only
- Session checkpoints do NOT include a push offer (mission is still running)
- Gate→drain transitions do NOT include a push offer (still running)
- Between-task completions do NOT include a push offer (still running)
- If the user says "yes" / "go ahead" / "push it" in reply to this summary: push immediately

4. **If budget exhausted** (`turns_consumed >= turn_budget`):
   - Update `status: abandoned`
   - Surface: `⏸️ Mission turn budget exhausted (N turns). Last evaluator note: <reason>. Run @g-mission status to review, or @g-mission --budget N to extend.`
   - Pause for user direction — do NOT auto-extend

### Status (`@g-mission status`)

Read `.gald3r/config/ACTIVE_MISSION.md` and display:

```
🎯 Mission status
Condition:    <condition>
Linked task:  T{id} (or "none")
Set at:       <set_at>
Turns:        <turns_consumed> / <turn_budget>
Status:       active | achieved | abandoned
Last eval:    <last_eval_reason>
```

If no mission file exists: `No active mission. Set one with @g-mission <condition>`

### Clear (`@g-mission clear`)

1. Update `ACTIVE_MISSION.md` `status: abandoned` (preserve audit trail; do not delete)
2. Run `@g-goal clear`
3. Confirm: `🛑 Mission cleared.`

---

## Differences from related commands

| Command | When to use |
|---|---|
| `@g-goal` | Set a persistent goal that `g-go` reads; manual iteration control |
| `@g-go-go` | Run until the task queue is exhausted (no explicit condition) |
| `@g-mission` | Run until YOUR stated condition is provably met; stop when done |
| `@g-mission --until-empty` | Run until condition met, THEN drain the full `ai_safe` queue; closest to `/goal` on other platforms |
| `@g-juggernaut` | Alias for `@g-mission`; use when you want unstoppable forward momentum |
| `@g-kamikaze` | Alias for `@g-mission`; use when it's all-in, no stopping |

---

## Cross-repo and workspace safety

### Declaring the mission's blast radius (required for multi-repo conditions)

If the mission condition touches more than one git root, declare the repos upfront:

```
@g-mission all tests pass and tsc exits 0 --repos gald3r_throne,gald3r_valhalla
@g-mission T1218 cleanup complete --from-task T1218
```

When `--repos` is supplied, write the list into `ACTIVE_MISSION.md` frontmatter as:
```yaml
touch_repos: [gald3r_throne, gald3r_valhalla]   # manifest repository.id values
```

When `--from-task T{id}` is used, inherit `workspace_repos:` and `extended_touch_repos:` directly from the task's frontmatter — no separate `--repos` needed.

If neither is supplied and the condition mentions a member repo name, extract it and prompt the user to confirm the blast radius before starting the loop.

### Clean Controller Gate — between every iteration

Before each new `g-go` iteration starts AND before any coordinator shared write (TASKS.md, BUGS.md, CHANGELOG.md, review-result commits), run the full Clean Controller Gate and member touch-set expansion:

1. Run `git status --short` at the orchestration root (gald3r_dev)
2. For each repo in `touch_repos:`, also run `git status --short` at that root
3. If **any** root has unrelated dirty paths → **pause the mission** before the next iteration; do not auto-commit unrelated changes; surface the exact dirty paths and ask for direction
4. If dirty paths are **exclusively safe gald3r housekeeping** (task/bug status files, CHANGELOG entries owned by this mission) → the Gald3r Housekeeping Commit Gate auto-commits them before the next iteration proceeds (standard `chore(gald3r)` commit)

### Member repo write rules (task files and gald3r state)

Member repos (declared in `workspace_manifest.yaml` with marker-only `.gald3r/`) are **read targets only** during a mission:

- **DO**: read member repo source code, run tests in member repos, commit implementation changes to member repos
- **DO NOT**: write `.gald3r/` task files, BUGS.md, TASKS.md, or any gald3r control-plane state into a member repo — that state lives in the controller (gald3r_dev) only
- If a task spec has `workspace_repos: [member_id]`, the implementing agent may write code to that member's git root but all task-status writes go to the controller's `.gald3r/tasks/` and TASKS.md

### ai_safe and blast_radius gates

The mission loop respects per-task safety metadata:

| Task frontmatter | Mission behavior |
|---|---|
| `ai_safe: true` | Proceed autonomously |
| `ai_safe: false` | **Pause mission** before claiming this task; surface to user: "Task T{id} has `ai_safe: false` — manual review required before autonomous execution. Approve or skip?" |
| `blast_radius: low` | Proceed |
| `blast_radius: medium` | Proceed; note in mission evaluator log |
| `blast_radius: high` | **Pause mission**; surface: "Task T{id} has `blast_radius: high` — confirm before proceeding" |
| `requires_verification: true` | Task must go through `[🔍]` → independent verifier before mission counts it as done; mission loop does NOT self-verify these |

### PCAC inbox re-check cadence during long missions

PCAC inbox is checked:
- At mission start (standard session-start check)
- Every 30 minutes of elapsed mission time (coordinator re-runs `g-hk-pcac-inbox-check.ps1 -BlockOnConflict`)
- Before any coordinator shared write (TASKS.md, BUGS.md, CHANGELOG)

If the inbox check returns `INBOX CONFLICT GATE` (exit code 2) at any point mid-mission:
- **Pause the loop immediately** — do not start the next iteration
- Surface: `⚠️ PCAC conflict detected mid-mission. Run @g-pcac-read to resolve before mission continues.`
- Preserve `ACTIVE_MISSION.md` with `status: paused` (not abandoned) so the mission can resume after resolution

### Resuming a paused mission

```
@g-mission resume
@g-mission resume --budget 300    # override budget for an overnight long-run
```

1. Read `ACTIVE_MISSION.md` — confirm `status: paused` OR `status: active` (session checkpoint, not true pause)
2. Re-run PCAC inbox check; confirm clean
3. Re-run Clean Controller Gate on all repos in `touch_repos:`
4. Resume the loop from where it left off (condition not yet met, budget not exhausted)
5. If `--budget N` supplied on resume, update `turn_budget:` in `ACTIVE_MISSION.md` and reset `turns_consumed: 0` for this session only (accumulated prior turns are preserved in Evaluator Notes)

**`ACTIVE_MISSION.md` persists across Claude session resets.** If the CLI is killed, the terminal crashes, or context fills mid-mission, the mission file survives. The user simply pastes a new `@g-mission resume` prompt into the fresh session — no re-setup needed. The agent reads the file and continues from the last checkpoint row.

### Drain phase task queue scan order

When `mode: until-empty` and `phase: drain`, scan for claimable tasks in this order:

1. `.gald3r/tasks/open/` — all files with `ai_safe: true` and `status: pending`
2. `.gald3r/tasks/in-progress/` — tasks that were started but not finished (re-claim and continue)
3. `.gald3r/tasks/paused/` — only if the pause reason is resolvable within mission scope

Within each folder, claim in priority order: `critical` → `high` → `medium` → `low`. Within same priority, claim lowest task ID first (oldest work first).

### Session-end checkpoint (NOT a "pause")

#### Context threshold — when to trigger the checkpoint

**Trigger the session checkpoint when context usage reaches 75%.** This is the correct balance:
- **Too low (≤33%)**: wastes session capacity; the next resume starts with ~15-25% startup overhead (rules + AGENTS.md + ACTIVE_MISSION.md), so stopping at 33% leaves almost no usable room per session
- **Too high (>85%)**: risks running out of room mid-task or mid-checkpoint write
- **75% target**: leaves ~25% headroom to finish the current in-flight task and write the checkpoint cleanly

**Do NOT stop early because:**
- The task queue has hard tasks remaining (split and continue instead)
- The current task took more turns than expected
- A prior task's commit added context

**DO stop and write the checkpoint when:**
- Context reaches 75%
- The current task just completed and committed (natural task boundary, context ≥ 60%)
- Budget is exhausted

#### Checkpoint procedure

When the checkpoint condition triggers:

1. Finish the task currently in-flight — do NOT checkpoint mid-task, leaving work uncommitted
2. Write a **session checkpoint** row to `ACTIVE_MISSION.md ## Evaluator Notes` — include tasks completed, commits made, and next task to claim
3. Keep `status: active` (do NOT change to `paused` or `paused-partial`)
4. Do NOT write a "Mission Report" with "paused-partial" framing — this misleads the user into thinking the mission stalled
5. The user resumes with `@g-mission resume`; the agent reads ACTIVE_MISSION.md and continues immediately

**Correct session-end output format:**
```
✅ Session checkpoint — N tasks shipped (T{id1}, T{id2}, ...), M commits on {branch}. Working tree clean.
EXIT_REASON: <exit_code> — <one-line rule reference>
Next task on resume: T{next_id} ({title}).
Run @g-mission resume to continue.
```

**Exit codes (exactly one must appear on every exit/pause/checkpoint):**

| Code | Trigger | What it means |
|---|---|---|
| `CONTEXT_GATE` | ctx ≥ 75% | Normal session boundary — context fill hit the checkpoint threshold (see §Session-end checkpoint) |
| `BUDGET_EXHAUSTED` | `turns_consumed` ≥ `turn_budget` | Turn budget from `--budget N` consumed; resume resets counter |
| `QUEUE_EMPTY` | No claimable `ai_safe: true` tasks remain | Drain phase complete; all open ai_safe tasks claimed or skipped |
| `CONDITION_MET` | Evaluator check passes | Mission condition provably achieved; final summary follows |
| `PCAC_CONFLICT` | `g-hk-pcac-inbox-check.ps1` exits 2 | INBOX conflict gate fired mid-mission; run `@g-pcac-read` to resolve |
| `AI_SAFE_BLOCKED` | Next task has `ai_safe: false` | Human review required before next task can be claimed autonomously |
| `BLAST_RADIUS_HIGH` | Next task has `blast_radius: high` | Explicit user approval required before proceeding |
| `CLEAN_GATE_BLOCKED` | Dirty unrelated paths in touch-set | Unrelated uncommitted changes in orchestration root or a member repo; commit/stash them first |
| `DEPENDENCY_BLOCKED` | All remaining tasks have unmet deps | Every remaining queued task is waiting on another open task — no claimable work exists |
| `HUMAN_DECISION_REQUIRED` | Design question can't be inferred | A task requires a user choice that cannot be resolved from existing docs/code/specs |
| `SAFETY_GATE` | Schema migration / destructive DDL / `git rm` | Non-autonomous operation encountered; see §What cannot span a mission autonomously |

**Rules:**
- Every exit message MUST include exactly one `EXIT_REASON:` line
- `CONTEXT_GATE` and `BUDGET_EXHAUSTED` are **non-blocking** — mission stays `status: active`; user resumes with `@g-mission resume`
- All other codes set `status: paused` in `ACTIVE_MISSION.md`; re-run pre-flight checks on resume
- Do NOT combine multiple codes — pick the **primary** trigger
- Include the specific triggering rule or value in the one-liner: e.g., `CONTEXT_GATE — ctx=76%, threshold=75%` or `AI_SAFE_BLOCKED — T1199 has ai_safe: false`

**Incorrect session-end output (do NOT produce):**
```
Mission Report — paused-partial
Status: paused-partial — substantive progress, queue not fully empty
17 tasks deferred...
```

### What cannot span a mission autonomously (always stops for user)

- Tasks with `ai_safe: false`
- Tasks with `blast_radius: high`
- PCAC `[ORDER]` or `[CONFLICT]` inbox items arriving mid-mission
- Any dirty unrelated paths in the member touch-set that aren't owned by this mission
- Schema migrations or destructive DDL in gald3r_valhalla
- Removals from git (`git rm`) of non-scratch files

### ⛔ HARD RULE: "Scope too large" is NEVER a valid defer reason

**Deferring a task because it is large or complex is FORBIDDEN in mission mode.** The only valid defer reasons are the items listed above. If you find yourself writing "scope too large", "multi-hundred-line", "not pilot-sized", "bigger than one session", or any equivalent — STOP. That is a SPLIT, not a DEFER.

**Required response to any over-sized task:**

1. Immediately decompose it: create `T{id}a`, `T{id}b`, etc. via `@g-task-add`
2. Mark the parent task `status: speccing` with a `#decomposed-into: [T{id}a, T{id}b, ...]` note
3. Claim and implement `T{id}a` (the smallest independently shippable slice) in the current iteration
4. Continue the mission loop — do NOT write a summary and stop

**The same rule applies to cross-repo tasks:** if a task nominally touches `workspace_repos: [gald3r_throne]` but its first AC is purely `gald3r_dev` documentation, spec-writing, or scaffolding — do the `gald3r_dev`-only portion as `T{id}a`, file `T{id}b` for the cross-repo implementation, and continue.

**What IS a valid reason to skip (not defer) a task and keep looping:**
- `ai_safe: false` — log it, skip it, move to next task
- `blast_radius: high` — surface to user mid-mission, skip it if user does not respond within the same turn, log the skip
- Requires a human design decision that genuinely cannot be inferred from existing docs/code — log, skip, move on
- ALL PREREQ tasks are still open (not just "complex" — literally blocked by unfinished dependency)

**Skipped tasks stay in the queue.** Deferred tasks get a subtask filed. The mission loop NEVER exits because tasks are hard.

## Full gald3r citizenship (MANDATORY inside the loop)

`g-mission` is NOT a raw execution bypass. Every `g-go` iteration inside the mission loop runs as a full gald3r citizen. This means:

### Task and bug management (still required)
- **New tasks**: if work is discovered that isn't tracked, create a task via `g-task-add` before starting it — even mid-mission
- **Bug discovery gate**: any pre-existing bug encountered must get a `BUG-NNN` entry + inline annotation — mission mode does not exempt this (`g-rl-35`)
- **Todo/stub gate**: any stub or TODO written must be annotated `TODO[TASK-X→TASK-Y]` with a follow-up task filed before the iteration is marked complete (`g-rl-34`)
- **Code changes require task or bug reference** — no orphan code changes, even inside a mission run

### Backlog awareness (active, not passive)
The agent operating under a mission actively manages the path to the condition:
- **Mandatory split** (hard rule — see above): if a task is too large for one iteration, IMMEDIATELY decompose into subtasks and tackle subtask 1. Do NOT log the parent as deferred. Do NOT write a summary and stop.
- **Resequencing**: if the optimal order to reach the condition changes (e.g., a blocker surfaces), reorder the pending task queue — update TASKS.md priority/order accordingly
- **Dependency surfacing**: if a task is blocked by another that doesn't yet exist, create the blocking task and sequence it before the blocked one
- **Condition narrowing**: as work progresses, the agent may note in `ACTIVE_MISSION.md ## Evaluator Notes` which sub-conditions are already met and which remain, helping each iteration focus precisely
- **Session boundaries do NOT pause a mission**: when the agent's context fills or a session ends naturally, the ACTIVE_MISSION.md remains `status: active`. The user resumes with `@g-mission resume`. The agent does NOT write a "paused-partial" summary that implies the work stalled — it writes a "session checkpoint" that shows progress made and the next task to claim on resume.

### What the mission changes (only)
- The **exit criterion**: instead of "queue exhausted," the loop exits when the stated condition is provably met
- The **context anchor**: each iteration opens with `MISSION: <condition>` injected alongside the goal, keeping every iteration aligned
- The **turn accounting**: `turns_consumed` increments each major iteration; budget exhaustion pauses rather than auto-extends

Everything else — safety gates, gald3r housekeeping commits, PCAC inbox checks, review checkpoints, member marker invariants — applies without modification.

## Safety rules

- Never auto-extend a turn budget — always pause and surface the reason when budget is exhausted
- Never skip the PCAC INBOX gate — even in mission mode, inbox conflicts stop the loop
- Never mark mission `achieved` without running the verification check (`tsc`, `vitest`, `git status`, etc.) — evaluator must see actual command output
- `@g-kamikaze` mode does not reduce safety checks — the name is flavor only
- Coordinator-owned gald3r writes still happen after each g-go iteration (housekeeping commit gate applies)
- Mission does not suppress the bug-discovery gate, todo-completion gate, or code-change-requires-task gate

### ⛔ NO `git push` without explicit goal authorization

**`g-mission` NEVER runs `git push` autonomously.** Commits are local and reversible — pushes are public and permanent. The mission accumulates commits freely as its audit trail, but remote publication requires explicit human authorization.

**The only way push is permitted inside a mission:**
- The mission's condition statement explicitly includes push (e.g., `"ship and push T1259"`, `"publish to GitHub"`, `"push on completion"`)
- The user issues a separate `@g-git-push` command after reviewing commits

**What this means in practice:**
- After each task commit: stay local, continue the loop
- At session checkpoint: stay local, report commits ready to push
- At mission `achieved`: output the final mission summary with commit list and push offer (see format above). Do not offer push at any earlier point.
- Never infer push intent from words like "ship", "deploy", "release", or "publish a skill" — those mean the file work, not the remote push

---

## Non-interactive / Claude Code equivalent

Claude Code uses `/goal` for this pattern. In Cursor, `@g-mission` is the equivalent:

```
# Claude Code
/goal all tests in test/auth pass and the lint step is clean

# gald3r / Cursor  
@g-mission all tests in gald3r_throne pass and tsc exits 0
@g-juggernaut all tests in gald3r_throne pass and tsc exits 0
@g-kamikaze all tests in gald3r_throne pass and tsc exits 0
```

---

## Related

- Spec: see `.gald3r/tasks/` for T{id} once created
- Config: `.gald3r/config/ACTIVE_MISSION.md`
- Depends on: `@g-goal`, `@g-go-go`, `@g-go`
- Inspired by: Claude Code `/goal`, Cursor `babysit` skill pattern
