# g-mission

Run an autonomous goal-locked loop until a verifiable completion condition is satisfied: $ARGUMENTS

Aliases: `@g-juggernaut`, `@g-kamikaze`

## Usage

```
@g-mission <condition>
@g-mission <condition> --budget <N>
@g-mission status
@g-mission clear
@g-mission --from-task T{id}
```

## What it does

`g-mission` is gald3r's autonomous completion loop. You state a verifiable end condition; the agent works toward it across as many `g-go` iterations as needed. After every iteration a lightweight evaluator checks whether the condition holds. If not, the loop continues. If yes, the mission is complete.

This is distinct from `@g-goal` (which sets a goal that `g-go` reads but does not loop autonomously) and from `@g-go-go` (which runs until tasks are exhausted). `g-mission` runs until YOUR stated condition is provably true — the stopping criterion is yours, not the task queue.

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
3. Write `.gald3r/config/ACTIVE_MISSION.md`:
   ```yaml
   ---
   id: mission-YYYYMMDDTHHMMSSZ
   condition: "<the condition text>"
   linked_task: T{id}          # or null
   set_at: <ISO 8601 UTC>
   turn_budget: 30             # overridden by --budget N
   turns_consumed: 0
   last_eval_reason: ""
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
3. **If YES**: 
   - Update `ACTIVE_MISSION.md` `status: achieved`
   - Clear `ACTIVE_GOAL.md` (`@g-goal clear`)
   - Report: `✅ Mission complete after N turns: "<condition>"`
4. **If budget exhausted** (`turns_consumed >= turn_budget`):
   - Update `status: abandoned`
   - Surface: `⏸️ Mission turn budget exhausted (N turns). Condition not yet met. Last evaluator note: <reason>. Run @g-mission status to review, or @g-mission --budget N to extend.`
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
| `@g-mission` | Run until YOUR stated condition is provably met; auto-loops |
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
```

1. Read `ACTIVE_MISSION.md` — confirm `status: paused`
2. Re-run PCAC inbox check; confirm clean
3. Re-run Clean Controller Gate on all repos in `touch_repos:`
4. Resume the loop from where it left off (condition not yet met, budget not exhausted)

### What cannot span a mission autonomously (always stops for user)

- Tasks with `ai_safe: false`
- Tasks with `blast_radius: high`
- PCAC `[ORDER]` or `[CONFLICT]` inbox items arriving mid-mission
- Any dirty unrelated paths in the member touch-set that aren't owned by this mission
- Schema migrations or destructive DDL in gald3r_valhalla
- Removals from git (`git rm`) of non-scratch files

## Full gald3r citizenship (MANDATORY inside the loop)

`g-mission` is NOT a raw execution bypass. Every `g-go` iteration inside the mission loop runs as a full gald3r citizen. This means:

### Task and bug management (still required)
- **New tasks**: if work is discovered that isn't tracked, create a task via `g-task-add` before starting it — even mid-mission
- **Bug discovery gate**: any pre-existing bug encountered must get a `BUG-NNN` entry + inline annotation — mission mode does not exempt this (`g-rl-35`)
- **Todo/stub gate**: any stub or TODO written must be annotated `TODO[TASK-X→TASK-Y]` with a follow-up task filed before the iteration is marked complete (`g-rl-34`)
- **Code changes require task or bug reference** — no orphan code changes, even inside a mission run

### Backlog awareness (active, not passive)
The agent operating under a mission actively manages the path to the condition:
- **Subtask discovery**: if a task turns out to be larger than one iteration, split it — create child tasks and link with `dependencies:`
- **Resequencing**: if the optimal order to reach the condition changes (e.g., a blocker surfaces), reorder the pending task queue — update TASKS.md priority/order accordingly
- **Dependency surfacing**: if a task is blocked by another that doesn't yet exist, create the blocking task and sequence it before the blocked one
- **Condition narrowing**: as work progresses, the agent may note in `ACTIVE_MISSION.md ## Evaluator Notes` which sub-conditions are already met and which remain, helping each iteration focus precisely

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
