Implementation-only backlog execution: $ARGUMENTS

## Mode: IMPLEMENT ONLY

This command runs **coding and bug-fixing** — it does NOT verify. Every completed item is
marked `[🔍]` (Awaiting Verification) so a **separate agent session** can independently confirm it.

## Model-Tier Selection (`--mode fast|standard|cheap`)

`g-go-code` accepts an optional `--mode` flag in `$ARGUMENTS` that selects the model tier for
this session. The flag is **advisory**: when running inside Cursor or any IDE that controls
its own model selection, `--mode` is recorded in Status History but the actual model used is
whatever the IDE is configured for. When running through a CLI that supports model override
(`claude --model ...`, `codex --model ...`), agents map `--mode` to the appropriate `--model`
argument before spawning subagents.

### Mode mapping table

| `--mode` | Tier | Claude model | Cursor model | Use when |
|----------|------|--------------|--------------|----------|
| `fast` (alias `cheap`) | haiku-class | `claude-haiku-4-5` | `gpt-4o-mini` / `haiku` | Simple tasks, cost-sensitive runs, bucket agents on parallel-safe work |
| `standard` (default) | sonnet-class | `claude-sonnet-4-6` | `sonnet-4` | Most tasks, coordinator role, anything requiring real reasoning |
| (no flag) | inherit | session default | session default | Fall through to the IDE-configured default model |

`cheap` is a strict alias for `fast` (same tier, same model mapping). Use whichever reads
more naturally for the session — they are interchangeable.

### Resolution precedence (highest wins)

1. **Task YAML `preferred_model:`** — if the task being implemented sets `preferred_model:`
   (`haiku` | `sonnet` | `opus` | `fast` | `standard`) in its frontmatter, that overrides the
   session `--mode` for that specific task only. Use this to force a complex task onto Opus
   even when the session is running in `fast`, or to keep a trivial follow-up on Haiku even
   when the session is running in `standard`.
2. **Session `--mode` flag** — when `$ARGUMENTS` contains `--mode fast`, `--mode standard`,
   or `--mode cheap`, that mode applies to every queued item that does not override.
3. **Session default** — when neither is set, fall through to whatever the host IDE is
   currently configured for. Do not pick a tier silently.

### Status History mode logging (AC5)

When the implementation agent claims a task and moves it to `[🔄]` / `in-progress` (or
directly to `[🔍]` / `awaiting-verification` for fast single-pass items), the claim's Status
History row MUST include the resolved mode in its `Message` column. Format:

```
| YYYY-MM-DD HH:MM | pending | in-progress | autopilot-impl | mode=fast — Claimed for implementation |
| YYYY-MM-DD HH:MM | in-progress | awaiting-verification | autopilot-impl | mode=standard — Implementation complete; {1-line summary} |
```

The `mode=<tier>` token (`fast`, `standard`, `cheap`, `inherit`) is the audit trail.
Reviewers and post-mortem analysis use it to correlate model-tier choice with implementation
quality. Omitting it on the claim row is a procedural violation.

## Implementation-Only Boundary

`g-go-code` and `g-go-code --swarm` must not spawn reviewer agents, run `g-go-review`, run `g-go-review-swarm`, or invoke `gald3r-code-reviewer` / full adversarial review subagents.

Allowed implementation readiness checks are limited to smoke/unit-style evidence:
- Import/build/typecheck/lint commands relevant to the changed files.
- Focused unit tests or existing fast test gates.
- Acceptance-criteria self-check against the task or bug spec.
- Workspace, constraint, stub/TODO, and bug-discovery gates required before marking `[🔍]`.

The output may include a review handoff and checkpoint SHA. It must not perform the review. Use `g-go` / `g-go --swarm` for implement-plus-auto-review, or `g-go-review` / `g-go-review --swarm` for review-only.

## Completion Signal Contract (T1175 — Sandcastle pattern)

`g-go-code` MUST NOT mark a task `[🔍]` (Awaiting Verification) based on "agent feels done" or "end of turn" heuristics. A **completion signal** is a structured, file-grounded artifact set that the next-stage reviewer can verify cold without re-reading the implementer's reasoning.

A valid completion signal consists of **all** of the following — every item is mandatory:

1. **Handoff Report section is filled** (T1097) — the task file contains a `## Handoff Report` section with all five required subsections populated: `Files Changed`, `Commands Run`, `Issues Discovered`, `Left Undone`, `Procedure Compliance`. An empty header is not a signal.
2. **All AC checkboxes resolved** — every `- [ ]` line under `## Acceptance Criteria` is either checked (`- [x]`) or explicitly carried out and the section ends with no orphan unchecked criteria. Partial implementation is a Blocker (Step 6), not a `[🔍]`.
3. **DoD Gate passed or explicitly SKIPPED** (T1099/T1168) — Step b3.5 ran and the Status History row records `dod_gate: PASS` or `dod_gate: SKIPPED (<reason>)`. A `dod_gate: FAIL` row means the signal is not yet produced.
4. **Status History claim + completion row written** — the task file `## Status History` has the b3 row (`| YYYY-MM-DD HH:MM | in-progress | awaiting-verification | <agent> | mode=<tier> — Implementation complete; <summary> |`) appended.
5. **Post-write lint passed for every modified file** (T919) — Step b1 returned exit 0 for each Write/Edit; no syntax errors are outstanding.
6. **Implementation Plan was locked** (T879) — `## Implementation Plan` exists on the task file with `Lock Status: LOCKED`, unless `--skip-plan` was passed and the justification is recorded in the session summary. Any `DEVIATION:` notes are present on affected steps (not silently rewritten).

**Signal absence handling**: if any of the six conditions above is not satisfied, the implementer MUST either (a) loop back to the relevant step and complete it, or (b) classify the item as Blocked and log it in `## Deferred Items` § Blockers — never silently mark `[🔍]`.

**Why this matters**: the next agent (`g-go-review` or any reviewer) reads the task file cold and uses these artifacts as the authoritative ground-truth for the work claimed complete. Missing signal pieces are the root cause of the "passed review but actually broken" failure mode.

## Iteration and Timeout Limits (T1175 — Sandcastle pattern)

`g-go-code` accepts dual stop-conditions in `$ARGUMENTS`. **Whichever limit hits first stops the run cleanly**; the limit is not a hard kill — it is a soft "no new claims, finish what's in flight, write the summary" boundary.

| Flag | Default | Override env var | Behavior |
|------|---------|------------------|----------|
| `--max-iterations N` | `5` | `GALD3R_MAX_ITERATIONS` | Maximum number of items the implementer will claim and process this session. After N items finish, stop claiming new ones and finalize. Counts both PASS and BLOCKED items. |
| `--timeout-minutes M` | `30` | `GALD3R_TIMEOUT_MINUTES` | Wall-clock budget in minutes from the moment the work queue is built. When elapsed minutes ≥ M and an item finishes, stop claiming new ones and finalize. Does not interrupt an in-flight item mid-edit. |

**Enforcement rules:**

- Both limits are advisory at the start of each item, not preemptive. The implementer checks them between items, not inside a single item's b/c/d/e/f loop.
- Either limit hitting triggers the **same** finalization path: the in-flight item completes naturally (or is logged as Blocked if it cannot finish), then the batch status write + checkpoint commit + session summary run as normal.
- In `--swarm` mode the limits apply to the **coordinator's scheduling decisions**: max-iterations caps the total items partitioned across all buckets; timeout-minutes is a wall-clock fence for the coordinator (bucket agents have no individual timer).
- Env-var overrides allow per-machine tuning without editing command files (helpful for CI vs interactive). Explicit `$ARGUMENTS` flags override env vars.
- The session summary MUST include the stop reason: `Stop reason: queue exhausted | max-iterations (N of N) | timeout-minutes (M elapsed) | hard-gate blocker`.

**Why dual limits**: relying on iteration count alone fails when a single complex task burns the entire run budget; relying on timeout alone fails when many trivial items get cut off without a clean stopping point. Dual limits give a predictable upper bound on both attempts and wall-clock.

## ⚙️ Pure Executor Contract

`g-go-code` is a **pure executor** — it receives a task spec routed by the `g-go` coordinator and
produces implementation output. It does **not** self-route to other agents, does **not** spawn
reviewers, and does **not** write shared `.gald3r/` coordination surfaces directly.

**Bucket mode** (received via swarm briefing from the coordinator):
- **`parallel`** — this bucket has no cross-bucket dependencies; implement independently and return results.
- **`sequential`** — this bucket depends on upstream bucket handoff data; read the upstream output before implementing.

Bucket agents return to the coordinator: patch bundle, generated artifacts, test/lint evidence,
changed-file inventory, and proposed Status History rows. The coordinator performs **all** shared
writes (TASKS.md, BUGS.md, task files, CHANGELOG.md, generated prompts, parity output, commits).

---


### PCAC Inbox Gate (Only When PCAC Is Configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a PCAC participant. PCAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a PCAC group member.

If PCAC is configured, run the re-callable PCAC inbox check when the hook exists.

> **Tool routing (BUG-031)**: on Windows, invoke this snippet through the **PowerShell tool**, not Bash. It uses PowerShell-only syntax (`@(...)` array, `Where-Object`, `Test-Path`, `Select-Object`, pipeline). Routing it through Bash produces a parse error such as ``syntax error near unexpected token `('`` — that failure is a tool-selection error, **NOT** a real PCAC conflict gate. Re-run via PowerShell. On Linux/macOS hosts use `pwsh` if available; if neither shell can reach the hook, treat the gate as advisory and let Workspace-Control routing re-evaluate.

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the PCAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -TaskId <id-when-known> -Json
```

Behavior:

- **`clean`** -> continue.
- **`safe-gald3r-housekeeping`** -> the helper stages **only** allowlisted controller `.gald3r/` paths via explicit `git add -- <paths>` (never `git add .`), re-checks for drift, and creates a focused `chore(gald3r): preflight gald3r housekeeping` commit. The run continues automatically.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown `.gald3r` paths / member-repo `config-fault`** -> the helper exits non-zero, the existing Clean Controller Gate hard-block applies, and the run STOPs with the exact unsafe paths listed.

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/pcac_auto_actions.log, linking/sent_orders/, linking/INBOX.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the PCAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `gald3r_dev`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r_worktree.ps1 -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/linking/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

4. **Touch-set expansion (v2 — optional signals)** — Union extra repository roots into the same per-root checks (still **not** a blanket scan of every manifest member):
   - **`extended_touch_repos:`** — optional task/bug YAML list of additional manifest `repository.id` values beyond `workspace_repos`.
   - **`touch_repos:` (swarm handoffs)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
   - **Subsystem `locations:` absolutes** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested strings). For values matching a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` elsewhere), if the path exists, resolve `git -C <dir> rev-parse --show-toplevel` (use the file's parent directory when the path is a file). Each distinct root **other than** the orchestration root joins the touch set. Relative paths do not expand the set.

### Pre-Reconciliation Clean Gate (before coordinator shared writes)

Also re-run the **Gald3r Housekeeping Commit Gate** with `-Mode post-write -Apply` against the orchestration root immediately after each coordinator-owned shared `.gald3r` write so safe controller coordination state lands in a focused `chore(gald3r): commit g-go coordination state` commit before the next major phase begins.


Immediately before the coordinator merges bucket results into the primary checkout, updates shared `.gald3r` indexes or task/bug files as coordinator-owned writes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits: **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (steps 1 + 3 + 4). For `--swarm` runs, if unrelated dirty paths appear in **any** of those roots during parallel bucket work, **fail closed** — do not apply those shared writes; keep patches, artifacts, and evidence; report **per-root** blockers using the same blocker family as checkpoint and review-result commits.

## Session-Start: Load Active Goal (Goal-Locked Loop)

> Fires immediately after safety gates pass, before implementation begins. If no active goal is set, this section is a no-op.

If `.gald3r/config/ACTIVE_GOAL.md` exists:

1. Read the file. Parse its YAML frontmatter (`description`, `linked_task`, `set_at`, `turn_budget`, `turns_consumed`).
2. Inject into working context as the prefix:
   ```
   CURRENT GOAL: <description> (turn <turns_consumed>/<turn_budget>, task T{id})
   ```
3. Increment `turns_consumed` by 1 and write the updated value back to `ACTIVE_GOAL.md`.
4. If `turns_consumed >= turn_budget`:
   - Surface `🎯 Goal turn budget exhausted — pausing for user direction.`
   - Stop the run cleanly. The user must extend the budget (`@g-goal <description>` to reset) or clear the goal (`@g-goal clear`).

If `--with-goal T{id}` was passed in `$ARGUMENTS`:

1. Treat as if `@g-goal --from-task T{id}` were just run: read `.gald3r/tasks/task{id}_*.md` (active or archive), set `ACTIVE_GOAL.md` from the task title, then proceed with `tasks {id}` as the work filter.
2. Set `linked_task: T{id}` and the description from the task `title:` field. Default `turn_budget: 50`.

If no `ACTIVE_GOAL.md` exists and no `--with-goal` flag is present, proceed without a goal lock (normal operation).

**Goal-aligned AC gate**: after each AC-gate iteration (step b2 below), the implementing agent self-checks: "Did this action advance `<description>`?" If not, re-anchor on the goal in the next reasoning step. This is a soft drift-correction — not a hard block. If drift is severe (3+ consecutive AC-gate iterations failing the alignment check), surface a `🎯 Goal drift detected` notice in the session summary and consider invoking `@g-goal status` to verify the lock is current.

See `g-goal` command (parity across all 6 IDE platforms) for the full goal-locked loop specification.

---

## Execution Protocol

### Step 0a — Shell Router (T1144, before any tool call)

Before issuing any shell, hook, or git command in this run, **probe once** and lock the shell route for the session. This complements the always-apply rule `g-rl-00-always` §6 ("Shell Context — OS + Shell Probe") and prevents the bash-vs-PowerShell token-waste loop documented in BUG-031 / T1144.

**Probe (one signal, not a diagnostic loop):**

| Signal | Route |
|---|---|
| `$env:OS` contains `Windows`, or `$IsWindows -eq $true`, or harness reports `Shell: PowerShell` | **PowerShell route** — use a `PowerShell` / `Shell` tool when available |
| `uname -s` returns `Linux` / `Darwin`, `$BASH_VERSION` is set, or harness reports `Shell: Bash` | **bash/zsh route** — use the `Bash` tool |

**Lock and route every subsequent invocation through the chosen interpreter.** Do not mix syntaxes inside a single tool call — the tool, not the snippet, picks the parser. If the harness exposes both `Bash` and `PowerShell` tools on Windows, prefer the PowerShell tool for PowerShell snippets.

Concrete syntax differences to keep in mind (mirrors `g-rl-00-always` §6):

- Arrays: `@(...)` (PS) vs `(...)` / `arr=(a b c)` (bash)
- Statement separators: `;` sequential (PS, both); `&&` short-circuit (bash always, PS 7+)
- Env vars: `$env:VAR` (PS) vs `$VAR` / `${VAR}` (bash)
- Paths: `\` (PS, `/` also accepted on Windows) vs `/` (bash)
- File-exists test: `Test-Path $p` (PS) vs `[ -f "$p" ]` (bash)
- Pipeline filters: `Where-Object { ... }` (PS) vs `grep` / `awk` / `xargs` (bash)

**Regression canonical (BUG-031 family)** — the PCAC inbox hook lookup snippet that triggered T1144:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
```

This snippet appears literally in the PCAC Inbox Gate section below. It is PowerShell-only — invoking it via `Bash(...)` produces `syntax error near unexpected token '('` (exit 2). That error is a **tool-routing failure**, NOT a real PCAC conflict or hook-missing state. Re-route through PowerShell and the call succeeds; do not enter an error-driven retry loop.

When in doubt on Windows, default to PowerShell for any snippet that uses `@(`, `$env:`, `Where-Object`, `Select-Object`, `Test-Path`, or backslash paths. Linux/macOS hosts use `pwsh` if available, otherwise fall back to bash equivalents.

---

### 1. Load Context (Before Touching Anything)

Read in this order:
- `.gald3r/PROJECT.md` — mission, goals, ecosystem context
- `.gald3r/PLAN.md` — current milestones
- `.gald3r/BUGS.md` — open bugs (**read before TASKS** — bugs run first)
- `.gald3r/TASKS.md` — master task list
- `.gald3r/CONSTRAINTS.md` — guardrails (if exists)
- `.gald3r/DECISIONS.md` — past decisions (if exists, read-only)
- `git log --oneline -10` — recent changes

### 2. Build the Work Queue

**Bugs first (Tier 1), then tasks (Tier 2).**

**Tier 1 — Open bugs:**
- From `BUGS.md` + `bugs/` files; Critical → High → Medium → Low
- Skip bugs with external blockers
- **Skip `[🚨]` bugs** — log in Skipped section as "Requires-User-Attention — human review needed"

**Tier 2 — Pending tasks:**
- Status `[ ]` (pending), `[📋]` (ready), or stale `[📝]` (speccing claim expired)
- **Skip non-expired `[📝]` speccing claims** — log owner/expiry in Skipped section as "Speccing-In-Progress"
- For stale `[📝]` claims, append a Status History takeover row naming the prior `spec_owner` before proceeding
- **NOT** `[🚨]` (requires-user-attention) — **skip entirely**, log in Skipped section as "Requires-User-Attention — human review needed"
- **Skip `[⏸️]` (paused) tasks** — stored in `tasks/paused/`; must be manually unpaused before g-go-code picks them up
- **Skip `[🚫]` (cancelled) tasks** — stored in `tasks/cancelled/`; terminal state, never eligible for implementation
- No unmet dependencies, with the rolling-pipeline exception below: a dependency at `[🔍]` counts as **implementation-satisfied** for follow-on coding unless the downstream task declares `requires_verified_dependencies: true`
- Not `ai_safe: false`
- Priority: Critical → High → Medium → Low

Supported `$ARGUMENTS` filters:
- Task IDs: `@g-go-code tasks 7, 9`
- Bug IDs: `@g-go-code bugs BUG-003`
- Subsystem: `@g-go-code subsystem vault-hooks-automation`
- `@g-go-code bugs-only` / `@g-go-code tasks-only`

### 2a. Resolve Speccing Claims Before Worktrees

Before Step 3 worktree allocation, resolve task-spec claims in the primary checkout:
- For a bare `[ ]` task with no complete task file, run `g-skl-tasks` `CLAIM-FOR-SPEC` -> `WRITE-SPEC` -> `PROMOTE-SPEC` first.
- Skip non-expired `[📝]` claims before allocating a coding worktree.
- For expired `[📝]` claims, append a Status History takeover row naming the prior `spec_owner`, then finish/promote the spec before worktree creation.
- Only `[📋]` tasks or stale claims successfully promoted to `[📋]` proceed to coding worktree creation.

### 2b. Harvested Task Pre-Flight Check (T810)

**Applies to any task with `harvested_from:` in its YAML frontmatter.** Tasks created before this feature lacked the field — those pass silently. Only tasks explicitly generated by `g-skl-res-apply` will carry the field.

For each queued task that has `harvested_from:` set:

1. **Read subsystem spec** — Find the task's `subsystems:` list. For each subsystem, read `.gald3r/subsystems/{name}.md`. Extract the `locations:` paths and read the key files there. Produce a 3-5 line bullet summary of what is currently implemented.

2. **Scan pending queue** — Search `TASKS.md` for other tasks in status `[📋]` or `[🔄]` that reference the same subsystem(s) in their frontmatter. List: task ID, title, status.

3. **Display context panel:**
   ```
   ⚠️ HARVESTED TASK PRE-FLIGHT
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Task:    T{id} — {title}
   Source:  {harvested_from} (analyzed {harvest_date})
   Type:    {harvest_type}

   Subsystem: {subsystem_name}
   Existing implementation:
     • {bullet 1}
     • {bullet 2}
     • {bullet 3}

   Other pending tasks for same subsystem:
     T{n}: "{title}" [{status}]
     (none) if queue is empty
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

4. **Decision gate by `harvest_type`:**
   - `harvest_type: additive` — Display panel, then **proceed automatically.** The task adds new capability; no comparison gate needed.
   - `harvest_type: replacement` without `harvest_approved: true` — **BLOCK.** Do not implement. Pause and present the panel to the user asking: "This harvested task would replace existing functionality. Confirm to proceed, or type `skip` to defer this task." Log the task in the run's Skipped section as "Awaiting harvest comparison confirmation."
   - `harvest_type: replacement` with `harvest_approved: true` — Display panel as context, then proceed.
   - No `harvest_from:` field — Pass silently; no panel shown. (Legacy tasks created before T810.)

> **`--override-harvest-check` flag** — When this flag is passed to `@g-go-code`, replacement-type harvested tasks are treated as if `harvest_approved: true` and proceed without blocking. Use for batch runs after explicit human review of the harvest intake report.

### Step 0: Generate Locked Implementation Plan (Manus Planning Gate — T879)

**Runs after work queue is finalized, before any file edits or worktree creation.**

Skip this step only when `--skip-plan` is explicitly passed (trivial single-file tasks). `--skip-plan` is not the default and must be justified in the session summary.

For each queued task or bug, generate a locked implementation plan and append it to the task/bug file under `## Implementation Plan`. The plan locks intent before code touches the filesystem. Any mid-implementation divergence must be documented as a `DEVIATION:` note — do not silently rewrite history.

**Plan template** (append to the task file):

```markdown
## Implementation Plan
**Objectives:** [each Acceptance Criterion reworded as a concrete objective]
**Constraints:** [active CONSTRAINTS.md constraints relevant to this task's subsystems — list by ID and 1-line summary]
**Steps:**
1. [first concrete implementation step — name the file and operation]
2. [second step]
3. [continue as needed]
**Success Criteria:** [mirrors the AC checkboxes verbatim]
**Lock Status:** LOCKED
**Locked at:** YYYY-MM-DD
```

**Lock rules:**
- Write the plan, set `Lock Status: LOCKED`, then proceed to coding. Never skip writing the plan section.
- If implementation must deviate from a planned step, append `DEVIATION: {reason}` under the affected step and continue — do not stop, do not silently rewrite.
- After implementation, `g-go-review` reads `## Implementation Plan` and compares against the actual diff to flag undocumented divergences.
- Use `g-skl-plan` `LOCK_PLAN` operation to generate the plan (reads AC + active CONSTRAINTS.md constraints).

### 3. Pre-Create Coding Worktrees (Before Editing)

After speccing claims are resolved and before any implementation file changes or primary-checkout status writes, isolate every queued item with the T170 helper:

```powershell
.\scripts\gald3r_worktree.ps1 -Action Create -TaskId {id} -Role code -Owner {platform_or_agent_slug} -Json
```

Installed templates may call the helper from the `g-skl-git-commit/scripts/gald3r_worktree.ps1` skill directory when no root `scripts/` copy exists.

Rules:
- Worktree root defaults to `$env:GALD3R_WORKTREE_ROOT`, else `<repo-parent>/.gald3r-worktrees/<repo-name>`.
- The helper must refuse nested worktrees inside the active checkout.
- The helper blocks when the active checkout is dirty unless the **Clean Controller Gate** is satisfied with a documented `-AllowDirty` override in the owning task or bug `## Status History` (see `g-rl-33`).
- Map helper JSON to claim metadata: `worktree_path` → `worktree_path`, `worktree_branch` → `worktree_branch`, `created_at` → `worktree_created_at`, and `owner` → `worktree_owner`.
- Run implementation commands from the worktree root. Keep the primary checkout for queue coordination and final status writes.
- Pre-create all queued item worktrees before marking any item `[🔍]`; this prevents legitimate gald3r status writes from making later worktree creation look unsafe.
- If worktree creation fails, preserve any existing files, record the reason in Deferred Items, and skip the item rather than editing the primary checkout.
- **Agent liveness heartbeat (T1058)**: at claim time, write `agent_heartbeat: now` and `agent_heartbeat_expires: now + 10 min` to the task YAML. Refresh both fields every 5 minutes during active bucket work. Use the env var `GALD3R_HEARTBEAT_TTL_MINUTES` if set.

### 4. Work Through Items Sequentially

For each item:

**a)** Read the task/bug file — understand objective and acceptance criteria
**b)** If the item is a bare `[ ]` task with no complete spec, run `g-skl-tasks` `CLAIM-FOR-SPEC` → `WRITE-SPEC` → `PROMOTE-SPEC` first; skip non-expired `[📝]` claims. Then create/reuse the coding worktree and implement the solution inside that worktree

**b-1) Validation Contract Pre-Gate (T1096)** — before claiming any task, verify the `## Acceptance Criteria` section contains **checkbox items** (`- [ ]`). If the AC section is missing or contains only prose (no checkboxes):

- **Block** the task claim
- Write a note: "AC_VALIDATION_FAIL: task {N} — Acceptance Criteria missing or prose-only; requires checkbox format before implementation can begin"
- Log to work queue as "Skipped - AC_GATE: needs checkbox AC before implement"
- Move to the next task

This gate ensures g-go-review has a pre-defined, unambiguous contract to check. AC prose = unbounded scope = high re-work risk.

**Fast pass**: If the task has ≥3 checkbox AC items, the gate passes immediately with no extra action.

**b0) Impact Scan + Code-Graph Context Query (T921 + T874b + T1158)** — before writing any file, run the cross-file impact analysis to understand blast radius, and (when enabled) query the pre-built code graph to seed implementer context with ~200 tokens instead of grepping linearly.

**b0.1 Impact Scan (T921 → T1158, default-on)**

Call `graph_impact` on each file in the task touch set via gald3r_muninn MCP. The PowerShell wrapper is the canonical entry point and falls back automatically when the muninn graph is not indexed:

```powershell
.\scripts\graph_impact.ps1 -File "{file_to_be_modified}" -Depth 2 -Json
```

Direct MCP equivalent (when calling tools by name):

```jsonc
// gald3r_valhalla MCP server (muninn plugin)
{ "tool": "graph_impact", "arguments": { "file_path": "{file_to_be_modified}" } }
```

Review the returned `files` list (each entry `{path, relation}` with `relation` ∈ `imports | calls | imports+calls`). If the impact scan reveals > 3 transitively dependent files, add them to the implementation context window before writing. This prevents cross-file breakage ("agent edits one file and breaks another"). Non-blocking: proceed even if the script returns `warning: not_indexed` or falls back to the ripgrep backend.

Migration note (T1158): the prior `scripts/gitnexus_impact.ps1` is deprecated; it now forwards to `graph_impact.ps1` automatically so legacy callers keep working. Update any custom automation to call the new script directly.

**b0.2 Graphify Code-Graph Query (T874b, opt-in)**

Read `.gald3r/config/AGENT_CONFIG.md` → `context_reduction_mode.graphify_b0_enabled`. When `true`, the coordinator runs a single graph query before bucket spawn (or before single-agent implementation), captures the result as a small context block (typical ≤200 tokens), and passes it to implementer subagents as part of the briefing. When `false` (safe default), this step is skipped and Step b0.1 alone gates the impact context.

Backend fallback order (g-skl-graphify §Backends):

1. **gald3r_muninn MCP** (preferred, T1158) — `graph_impact` / `graph_callers` / `graph_callees` / `graph_deps` for symbol-level call/import resolution. Auto-loaded into the gald3r_valhalla MCP server; see `.mcp.json` `gald3r_muninn` entry.
2. **graphify CLI** — when muninn is unavailable, run `graphify query --root . --symbol {target}` against the local `.graphify/` index. See g-skl-graphify §SETUP for indexing guidance.
3. **tree-sitter + ripgrep fallback** — when neither backend is reachable, fall back to the legacy grep-based context-prep (Step b0.1 + ad-hoc reads). Do NOT halt the run.

Failure modes (never halt the run):

- **Missing backend** — gald3r_valhalla MCP server unreachable AND muninn plugin import fails AND `graphify` CLI not on PATH AND no `.graphify/` index → log "graphify b0 skipped: no backend reachable" and fall through to legacy.
- **Graph staleness** — index older than the orchestration root's last commit (muninn `graph_status` returns `stale: true` when index >24h old) → emit a warning; still use the result (advisory) and append a note recommending re-indexing via the muninn indexer or `graphify update`.
- **Query timeout** (>5s) — abort the query, log "graphify b0 timeout — fell back to legacy", proceed.
- **Empty result** — query returned no symbols / no edges → log "graphify b0 empty — fell back to legacy"; proceed with Step b0.1 context.

The b0.2 query is **advisory**, **non-blocking**, and **single tool call** (g-rl-37 "Think in Code" — one query, ≤200 tokens of returned context). Operators opt in by flipping `graphify_b0_enabled: true` in `AGENT_CONFIG.md`.

**b1) Post-Write Lint Gate (T919)** — after each Write or StrReplace tool call, run the language-appropriate syntax check:

```powershell
.\scripts\gald3r_post_write_lint.ps1 -FilePath "{relative_path_to_written_file}" -ProjectRoot . -Json
```

| Extension | Lint command |
|-----------|-------------|
| `.py` | `python -m py_compile {file}` |
| `.json` | `python -c "import json; json.load(open('{file}'))"` |
| `.yaml` / `.yml` | `python -c "import yaml; yaml.safe_load(open('{file}').read())"` |
| `.toml` | `python -c "import tomllib; tomllib.load(open('{file}', 'rb'))"` |
| `.ts` / `.tsx` / `.js` | `npx tsc --noEmit` (when tsconfig present) |
| `.ps1` | PowerShell AST parser |
| Other | Pass silently |

If the script exits non-zero (`exit 2` = syntax error), **stop and fix the file before proceeding**. Do not advance to the next write. Treat a lint failure the same as a TypeScript compile error — it blocks continuation.

**b2) AC gate** — before moving on, walk every `- [ ]` acceptance criterion in the task spec:
  - Is this criterion now satisfied? Check the actual files, not just intent.
  - Any unmet criterion → return to **(b)** and address it.
  - Cannot meet a criterion this session → log as a Blocker in step 5 and **skip this task entirely** (do not mark `[🔍]` for partial work).
  - **Stub/TODO scan**: search files modified for this task for bare `# TODO`, `// TODO`, `pass` (non-abstract), `raise NotImplementedError`, `throw new Error("not implemented")` — each is an unmet criterion until annotated `TODO[TASK-X→TASK-Y]` with a follow-up task created (see `g-rl-34`)
  - **Bug-discovery check**: any pre-existing bug encountered while implementing must have a BUG entry + `BUG[BUG-{id}]` comment before `[🔍]`; bugs introduced by this task must be fixed inline (see `g-rl-35`)
  - **Constraint check**: run `@g-constraint-check` mentally — does this implementation violate any active constraint? Any `🚫 VIOLATION` blocks `[🔍]`
  - **Workspace boundary check**: run `g-skl-workspace` ENFORCE_SCOPE before editing and before `[🔍]`; omitted metadata is current-repo-only, unknown manifest repo IDs block, and member repo writes require explicit `workspace_repos`, compatible `workspace_touch_policy`, authorization text, reviewed member git status, and manifest write permission.
  - All criteria confirmed met → continue.
**b3) Queue Status History** — collect the row that will be appended before marking `[🔍]`:
  ```
  | YYYY-MM-DD | pending | awaiting-verification | Implementation complete; {1-line summary} |
  ```
  If the task file has no `## Status History` section yet, add it first (backfill row: `| {created_date} | — | pending | Task created (backfill) |`).
**b3.5) Definition-of-Done Gate — Per-Criterion Model Evaluator (T1099 + T1168)** — after implementation, before marking `[🔍]`, run a per-criterion structured evaluation of the task's `## Acceptance Criteria` checklist using a cheap model tier (Haiku, gemini-flash-lite, etc.). This catches confirmation-bias premature `[🔍]` marks where the implementation agent thinks it shipped AC but missed a checkbox.

**Opt-in policy**: This gate is opt-in per task. Run it when **any** of the following is true:

1. Task YAML frontmatter has `requires_dod_gate: true`
2. Project `.gald3r/config/AGENT_CONFIG.md` sets `dod_gate_enabled: always`
3. Task has `requires_verification: true` AND `AGENT_CONFIG.md` sets `dod_gate_enabled: auto` (default)

When `dod_gate_enabled: never` is set project-wide, the gate is suppressed regardless of task-level flags. When task has `requires_dod_gate: false` (explicit), the gate is suppressed even if `dod_gate_enabled: always`.

When the gate does not run, log `dod_gate: SKIPPED (opt-out)` to Status History and proceed to **b4**.

**Per-criterion evaluator prompt** (invoke once per `- [ ] criterion` row using the cheapest available model):

```
You are evaluating ONE acceptance criterion against an implementation.

Criterion: {criterion text}

Files modified this task:
{list of file paths from b4 Handoff Report — files changed/created/deleted}

Brief implementation summary:
{1-3 sentence summary of what was done}

Question: Is this criterion satisfied by the current code?
Respond in this exact format:
VERDICT: PASS | FAIL | UNSURE
EVIDENCE: <file:line> or <file (no line)> or "no direct evidence found"
REASON: <one-sentence justification>
```

**Aggregation logic**:

| Outcome | Action |
|---------|--------|
| All criteria `PASS` | Proceed to **b4 Handoff Report** → `[🔍]` |
| Any criterion `FAIL` | **BLOCK**. Do not mark `[🔍]`. Return to **(b)** for one targeted fix pass, then re-run the gate (max 1 retry). After 1 failed retry, log Status History `dod_gate: FAIL` and either (i) keep the task at `[🔄]` with a Blocker note for the next session, or (ii) if `--swarm`, return the FAIL verdict to the coordinator as part of the bucket handoff. |
| Any criterion `UNSURE` (none `FAIL`) | Surface to coordinator (single-agent: surface to user; `--swarm`: include in bucket handoff). Coordinator/user decides: (a) treat as PASS and mark `[🔍]`, (b) treat as FAIL and loop, or (c) escalate to `g-go-review` for human-style verification. Do NOT silently auto-pass UNSURE. |
| Cheap model unavailable / network error | Log `dod_gate: SKIPPED (model unavailable)` and fall through to legacy YES/NO check (T1099 behavior). Never halt the run on infrastructure failure. |

**Status History row** (always append after gate, even on SKIP):

```
| {timestamp} | in-progress | {next_status} | {agent} | dod_gate: {PASS|FAIL|UNSURE|SKIPPED} — {summary_line} |
```

Where `{summary_line}` is one of:

- `all N criteria PASS`
- `N PASS / M FAIL / K UNSURE — FAIL: {first_failed_criterion_short_label}`
- `N PASS / K UNSURE — needs coordinator decision`
- `SKIPPED ({opt-out|model-unavailable|opt-out-task-flag})`

**Per-criterion detail** (optional, append below Status History row when at least one FAIL or UNSURE exists, for audit and `g-go-review` cross-check):

```
### DoD Gate Detail — {timestamp}
- AC1 `{first 60 chars of criterion}`: PASS — commands/g-go-code.md:416 — "criterion text matches step b3.5"
- AC2 `{...}`: FAIL — no direct evidence found — "criterion not visible in modified files"
- AC3 `{...}`: UNSURE — skills/g-skl-tasks/SKILL.md:197 — "field present but behavior not exercised"
```

**Cost guard**: The gate runs **once** per task per `[🔍]` attempt (plus 1 retry after FAIL). Per-criterion prompts are short and target a Haiku-tier model — typical cost is well under the savings from preventing one failed `g-go-review` cycle.
**b4) Fill Handoff Report** (REQUIRED before `[🔍]`) — fill in the `## Handoff Report` section of the task file:
  - **Files Changed**: list every file created, modified, or deleted (one path per line)
  - **Commands Run**: key commands with exit codes (e.g. `uv run pytest` → exit 0)
  - **Issues Discovered**: pre-existing bugs found, blockers hit, surprises
  - **Left Undone**: stubbed items, deferred scope, `TODO[TASK-X→TASK-Y]` references
  - **Procedure Compliance**: Yes / Partial / No — note any gate deviations
  If the task file has no `## Handoff Report` section, create it above `## Agent Notes`.
**c)** Validate — lint, test, check files exist
**d)** Record decisions — if you chose approach A over B, append to `.gald3r/DECISIONS.md`
**e)** Update subsystem Activity Log — for each subsystem in the task's `subsystems:` field, append to `.gald3r/subsystems/{name}.md` Activity Log: `| {date} | TASK | {id} | {title} | — |`. Create a stub spec if the file doesn't exist.
**f)** Queue status update — **C-026 enforced — two different writers, never the same agent**:

| Who | What to write | What NOT to write |
|-----|--------------|------------------|
| **Bucket agent** (in a worktree) | Individual task file only — update `status:` frontmatter and `## Status History` row | **MUST NOT touch `.gald3r/TASKS.md`** — return a coordinator proposal instead |
| **Coordinator** (primary checkout) | `.gald3r/TASKS.md` batch update after all buckets reconcile | Never edits task files directly when reconciling bucket proposals |

**Bucket proposal format** (include in the bucket handoff):
```
TASKS.md row proposal: | [🔍] | [T{id}](tasks/open/task{id}_*.md) | {title} | {subsystem} | {date} |
```

In single-agent (non-swarm) mode from the **primary checkout** (not a worktree), both writes are allowed — write the task file first, then immediately batch-update TASKS.md in the same final write pass (step 8). Verify you are NOT in a worktree with `git worktree list` — if the command returns more than one entry and your cwd is not the primary path, you are a bucket agent.

**g)** Move to next item

> **IMPORTANT**: Mark every completed item `[🔍]`, never `[✅]`.
> `[✅]` requires a separate agent session running `@g-go-review`.
>
> **C-026**: Bucket worktree agents write task files only. TASKS.md is coordinator-only. The pre-commit hook will block a worktree commit that stages TASKS.md.

### 4a. Mid-Task Checkpoint (Mandatory, Every N Major Operations)

**`CHECKPOINT_TOOL_CALL_INTERVAL`**: Default **20** major operations (file reads, shell commands, file writes). Override via `.gald3r/config/AGENT_CONFIG.md` key `checkpoint_interval`.

**Trigger**: After every N major tool operations within a single task's implementation, pause for a brief self-evaluation **before continuing**.

**Self-evaluation covers:**
1. **AC alignment** — How many acceptance criteria are satisfied vs. remaining? Is current trajectory sufficient?
2. **Scope check** — Am I within the declared `subsystems:` and `workspace_repos:` boundaries? Any creep?
3. **Blocking obstacles** — Anything discovered that may prevent completing this task? (missing files, unclear spec, external dep)
4. **Token budget** — Rough estimate of remaining context; flag if >75% consumed with significant work still remaining.

**Output formats:**

Healthy:
```
## Mid-Task Checkpoint (operation N/20): HEALTHY
AC progress: {X}/{total} satisfied. No blockers. Continuing.
```

Needs correction:
```
## Mid-Task Checkpoint (operation N/20): NEEDS_CORRECTION
⚠️ CHECKPOINT: {issue description}
AC progress: {X}/{total} satisfied. Blocker: {description}.
Correction plan: {1-2 sentences}.
```

**Task file audit trail** — Before continuing, append to the task's `## Status History`:
```
| YYYY-MM-DD | in-progress | in-progress | CHECKPOINT {N}: {1-line summary}. AC: {X}/{total}. Blockers: {none|description}. Continuing. |
```

**Rules:**
- Checkpoint is **mandatory** — not optional. Fires every N major operations with no exceptions.
- A task completed with ≥1 checkpoints must show those rows in `## Status History` before being marked `[🔍]`.
- If checkpoint yields `NEEDS_CORRECTION` with an unresolvable blocker, surface `⚠️ CHECKPOINT: [issue]` in the next message and log as Blocked in step 6.
- In `--swarm` mode, each bucket agent runs independent checkpoints; the coordinator does not aggregate them.

### 5. Docs Check (Per Task)

After each task, ask: does this add/remove/change user-facing behavior?
- **YES** → Append entry to `CHANGELOG.md` (root); update `README.md` if relevant section exists
- **NO** (internal refactor only) → skip

### 5a. Auto-Learn Extraction (Per Task)

After the docs check, run the auto-learn extraction for each task moved to `[🔍]`:

1. **Read the task's `## Status History`** and implementation notes from the task file.
2. **Extract**: "Given this implementation, what architectural decision, pattern, or watch-out should the next agent know?" Produce 0–3 candidate facts. Skip entirely if no meaningful insight emerges.
3. **Dedup**: read `.gald3r/learned-facts.md`. Skip any candidate fact that is a substring match (case-insensitive, first 80 chars) of an existing entry.
4. **Append** novel facts with the format:
   ```
   - [YYYY-MM-DD] {extracted_fact} (context: T{task_id})
   ```
   Append under the most appropriate heading (`## Architecture & Conventions`, `## Recurring Preferences`, or `## Watch-Outs & Gotchas`). Create the section if missing.
5. **Count new facts** and include in the handoff summary: `🧠 {N} new fact(s) learned from T{task_id}` (omit if 0).
6. **MCP chain** (when backend is available): call `memory_capture_session` with the extracted facts as the session content.

> **Skip silently** when `.gald3r/learned-facts.md` does not exist — note in summary as `🧠 learned-facts.md not found — skipped`.
> **Manual `/g-learn` still works** as before; this step does not replace it.

### 6. Question & Blocker Collection

DO NOT stop to ask. Collect silently:

```markdown
## Deferred Items

### Questions (Need Human Answer)
- Q1: [question] (task #X)

### Blockers (Could Not Proceed)
- B1: Task #X — [reason]

### Decisions Made (FYI)
- D1: Task #X — chose A over B because [reason]
```

### 7. Record Decisions

Before the handoff message, append any new decisions to `.gald3r/DECISIONS.md`:
- Use the next sequential ID after the last entry (`D{NNN}`)
- Include: Date | Decision | Rationale | this-agent

### 7a. Coordinator-Only Shared Writes

For swarm mode, bucket agents are patch producers, not shared-ledger writers. They must return:

- Patch bundle or explicit changed-file list.
- Generated artifacts produced inside the assigned worktree.
- Test/lint evidence.
- Proposed Status History rows and status transitions.
- Requested shared writes (`.gald3r`, `CHANGELOG.md`, generated prompts, parity sync) for the coordinator to perform.

Bucket agents must not directly write or commit shared coordination surfaces:

- `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task files, bug files, archive indexes, INBOX/sent_orders ledgers.
- `CHANGELOG.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`.
- Generated Copilot prompts/instructions, parity copies, or platform-wide sync output.
- Final `git add`, `git commit`, `git merge`, or broad staging commands.

The coordinator alone performs shared writes after all bucket outputs are collected and reconciled.

### 7b. Code-Complete Checkpoint Commit

Default review handoff is branch-addressable. After successful implementation reconciliation and shared writes, the coordinator creates a code-complete checkpoint commit before handing work to review:

1. Stage only intended paths by explicit allowlist.
2. Include implementation files plus coordinator-owned shared writes needed for `[🔍]` handoff.
3. Commit with a message that names the implemented task/bug IDs and states that the commit is ready for independent review.
4. Record the checkpoint branch and commit SHA in the handoff summary.

Snapshot review mode is fallback-only. Use it when the user explicitly requests uncommitted review, when a source cannot be made branch-addressable, or when a failed reconciliation must be inspected read-only. Do not make dirty snapshot mode the default.

### 7c. Rolling Implementation Waves

`g-go-code` and `g-go-code --swarm` must optimize for throughput. A code-complete checkpoint is a stable handoff point, not a global stop sign.

After a checkpoint commit is created:

1. Recompute the runnable queue immediately.
2. Treat dependencies that are `[🔍]` / `awaiting-verification` as implementation-satisfied when they have a branch-addressable checkpoint and the downstream task does not declare `requires_verified_dependencies: true`.
3. Start the next coding wave from the latest checkpoint or member-repo branch that contains the dependency output.
4. Record checkpoint-dependent downstream work in the dependent task's Status History:
   `Started on unverified dependency T{id} at checkpoint {sha}; rework required if review fails.`
5. Continue coding until no runnable work remains, a PCAC conflict appears, Workspace-Control preflight fails, or a task explicitly requires verified dependencies.

Review remains mandatory, but `g-go-code*` only prepares the handoff. It must not start the review lane itself. A later review failure requeues only the failed item and any downstream tasks that explicitly consumed its checkpoint. Do not stop unrelated implementation work merely because a prior item is awaiting review.

Tasks may force the old strict behavior with:

```yaml
requires_verified_dependencies: true
```

Use that field for destructive operations, irreversible migrations, public release/signing, production writes, security-sensitive changes, or any task whose acceptance criteria explicitly require verified predecessor behavior.

### 8. Final Status Batch + Handoff

After all attempted items are implemented and validated, reconcile their worktree diffs into the primary checkout, then batch-write `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task files, bug files, docs logs, and changelog entries for all successful items. Do not let one item's status write block another item's worktree creation.

Reconciliation rule for each successful worktree:
1. Inspect `git status --short` in the worktree.
2. Stage only intended implementation files in the worktree with `git add -A -- {paths}` so new files are included. Never use `git add .` in a swarm worktree.
3. Export `git diff --binary --cached HEAD` from the worktree.
4. Apply to the primary checkout with `git apply --3way --index`.
5. If the patch does not apply cleanly, leave the worktree and branch intact and list the item under Skipped / Blocked with its path.
6. Reject or manually resolve any patch that touches shared coordination surfaces; those changes must be represented as coordinator requests, not applied as bucket-owned edits.

After the final shared-write pass, create the checkpoint commit before review. If the checkpoint commit cannot be created, leave the implemented items at `[🔍]` only when the handoff explicitly names snapshot mode and the dirty checkout path reviewers must inspect.

```markdown
## Implementation Session Summary

> **Follow-Up Task Filing Gate**: Before writing this summary, call `g-skl-tasks CREATE TASK` for
> every follow-up item surfaced during this run (deferred sub-features, out-of-scope gaps, stub
> annotations). Reference actual task IDs (e.g. `T1110`) — NEVER slug-style names. If task creation
> fails, log it as a BLOCKER. Named-but-not-filed follow-ups are a policy violation.

### Moved to [🔍] (Awaiting Verification)
- [🔍] Task #X: {title}
- [🔍] Bug BUG-00N: {title}

### Skipped (Blocked)
- Task #Y: {reason}

### Deferred Questions & Blockers
{collected items from step 5}

### Follow-Up Tasks Filed
- T{id}: {title} — {why surfaced during this run}
(none surfaced — or list all filed task IDs with titles)

### Decisions Made This Session
{append these to .gald3r/DECISIONS.md}

### 🧠 Auto-Learn Summary
{N} new fact(s) appended to `.gald3r/learned-facts.md` (or "none / file not found").

### Handoff
{N} task(s) / {M} bug(s) moved to [🔍].
Implementation checkpoint: {branch}@{commit_sha} (default review source)
Handoff only: for independent verification, open a NEW agent session and run @g-go-review. Do not launch that reviewer from g-go-code.
Rolling waves: {continued|stopped}; next runnable queue: {ids or none}; verified-dependency blockers: {ids or none}
```

## Behavioral Rules

| Rule | Why |
|------|-----|
| Never ask questions mid-execution | Uninterrupted autonomous work |
| Never spawn reviewer agents from g-go-code* | Implementation mode stays focused on coding and readiness checks |
| Mark completed items `[🔍]`, never `[✅]` | Enforce independent verification gate |
| Keep coding across `[🔍]` dependencies unless strict verification is declared | Preserve fast product development while review catches up |
| Log every decision made | Future agents and humans need the audit trail |
| Skip tasks you can't complete | Maximize total output |
| Respect CONSTRAINTS.md | Never violate project guardrails |
| Abort if destructive (schema drop, data loss) | Safety first — log it as a blocker |


### PCAC Inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the PCAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-pcac-read` before continuing.

## Swarm Mode (`--swarm`)

When `$ARGUMENTS` includes `--swarm`, activate the **COORDINATOR PHASE** before any implementation.
Swarm mode partitions the work queue into conflict-safe buckets and spawns N parallel agents.

### Coordinator Phase (runs FIRST when --swarm is present)

**Step S1: Build full work queue** — same rules as standard mode (Steps 1–2 above), including skipping non-expired `[📝]` speccing claims and logging stale-claim takeovers.

**Step S2: Evaluate swarm eligibility after workspace preflight**
- If 0 qualifying items remain → exit with the existing empty queue or blocker message.
- If workspace preflight rejects a candidate (unknown `workspace_repos` member, target path is not a git root, unauthorized member write, or similar Workspace-Control denial) → stop with a blocker message. Do not offer swarm fallback for invalid workspace routing.
- If exactly 1 qualifying item remains and preflight passes → automatically downgrade to standard single-agent implementation mode and continue without asking for confirmation:
  `[SWARM] Single runnable item — auto-downgrading to @g-go-code standard mode`
- If 2 or more qualifying items remain → continue with swarm agent-count calculation and partitioning.
- After each checkpoint, rerun S1/S2 as a rolling wave. Previously completed `[🔍]` dependencies from this or earlier checkpoints count as implementation-satisfied unless a downstream task declares `requires_verified_dependencies: true`.

**Step S3: Compute agent count** (Smart Agent Count Formula)

| Queue size | Agents |
|-----------|--------|
| 1 | 1 (no swarm — fallback) |
| 2–4 | 2 |
| 5–9 | `ceil(count / 3)` (2–3) |
| 10–14 | 4 |
| 15+ | 5 (hard cap) |

**Step S4: Partition into conflict-safe buckets**

```
1. Build conflict_graph:
   For each pair (A, B) in work_queue:
     CONFLICT if: shared subsystem in subsystems[] OR A depends_on B OR B depends_on A

2. Greedy partition:
   Sort work_queue by priority (Critical→Low)
   For each item:
     Assign to the first existing bucket with no conflict with any item already in it
     If no bucket fits → open new bucket (up to agent_count limit)
     If max buckets hit → assign to smallest bucket (accept conflict; note it)

3. Output: buckets = [[task_ids...], [task_ids...], ...]
```

**Primary axis**: subsystem boundaries (same subsystem → same bucket).
**Secondary axis**: file-lock zones (tasks both touching TASKS.md/BUGS.md directly → same bucket).
**Dependency rule**: if A depends on B → same bucket, or B's bucket runs first.

**Step S5: Display partition plan**
```
[SWARM] Work queue: {M} items → {N} agents
  Bucket 1: Task 7 (vault-knowledge-store), Task 9 (vault-knowledge-store)
  Bucket 2: Task 10 (task-lifecycle-management), Task 11 (behavioral-rules-engine)
  Bucket 3: Task 12 (cross-project-coordination-pcac)
Spawning {N} implementation agents...
```

**Step S6: Spawn sub-agents**
- Before spawning, create or reuse one coding worktree per bucket:
  ```powershell
  .\scripts\gald3r_worktree.ps1 -Action Create -TaskId bucket-{bucket_number} -Role code-swarm -Owner {platform_or_agent_slug} -Json
  ```
- Branch/worktree names must include the bucket role plus repo/owner suffix from the helper contract.
- Each bucket agent receives its assigned `worktree_path` and `worktree_branch` and must run implementation from that worktree root.
- Bucket agents MUST NOT directly write shared `.gald3r/TASKS.md` / `.gald3r/BUGS.md`, task/bug status files, `CHANGELOG.md`, generated Copilot prompts, parity output, or commits. They return proposed status changes, changed-file inventory, generated artifacts, and evidence to the coordinator.
- Bucket agents MUST NOT run `git add .`; use explicit path staging only when creating a patch bundle, and exclude `.gald3r-worktree.json`, worktree ownership metadata, terminal transcripts, local logs, and other non-deliverable artifacts.
- Use the Agent tool to spawn N agents, each receiving:
  - The full `g-go-code` prompt (this command file content)
  - A `tasks X, Y, Z` filter argument restricting to that bucket's items only
  - The bucket worktree metadata
- Run all agents. Each follows the standard protocol on its slice.

**Step S7: Collect and merge**
After all sub-agents complete:
1. Inspect each bucket worktree with `git status --short` and `git diff --stat`.
2. Detect overlapping shared-file edits before applying patches. If two buckets request the same shared file, defer that file to the coordinator's final write.
3. Reconcile one bucket at a time: stage only intended bucket files in the bucket worktree with `git add -A -- {paths}`, export `git diff --binary --cached HEAD`, then apply it to the primary checkout with `git apply --3way --index`; do not overwrite user edits.
4. If reconciliation cannot be completed cleanly, leave the bucket worktree and branch intact and list it under Skipped / Blocked with its path.
5. Batch-write `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task files, bug files, `CHANGELOG.md`, generated Copilot prompts/instructions, and parity outputs only after bucket outputs are reconciled.
6. Run parity sync and prompt regeneration at most once from the coordinator after final shared writes.
7. Create one code-complete checkpoint commit from the primary checkout so review swarms can create clean `review-swarm` worktrees from a committed source.
8. Recompute the work queue for the next rolling wave. Continue immediately when new items become runnable through `[🔍]` checkpoint dependencies and no strict verification gate applies.
9. Write the unified handoff when no further coding wave can run:

```markdown
## Swarm Implementation Session Summary

### Swarm Configuration
- Agents spawned: N
- Partition strategy: subsystem-boundary
- Total items in queue: M

### Bucket Results
| Bucket | Agent | Tasks | Status |
|--------|-------|-------|--------|
| 1 | Agent-1 | 7, 9 | [🔍] ×2 |
| 2 | Agent-2 | 10, 11 | [🔍] ×1, Blocked ×1 |

### Moved to [🔍] (Awaiting Verification)
{merged list from all agents}

### Skipped / Blocked
{merged list from all agents}

### Follow-Up Tasks Filed
- T{id}: {title} — {why surfaced}
(none surfaced — or list all filed task IDs with titles. Named-but-not-filed follow-ups are a policy violation.)

### Handoff
{total} task(s) / {total} bug(s) moved to [🔍].
Implementation checkpoint: {branch}@{commit_sha} (default review-swarm source)
Handoff only: for independent verification, open a NEW agent session and run @g-go-review --swarm. Do not launch that reviewer from g-go-code-swarm.
Rolling waves completed: {count}; checkpoint-dependent downstream items: {ids}; strict verified-dependency blockers: {ids or none}
```

---

## Usage Examples

```
@g-go-code
@g-go-code tasks 14, 15
@g-go-code bugs BUG-001, BUG-002
@g-go-code subsystem cross-project
@g-go-code bugs-only
@g-go-code --swarm
@g-go-code --swarm tasks 7, 9, 10, 11, 12
@g-go-code --swarm bugs-only
@g-go-code --mode fast tasks 14, 15
@g-go-code --mode standard tasks 14, 15
@g-go-code --mode cheap bugs BUG-001
@g-go-code --swarm --mode fast
@g-go-code --max-iterations 3 tasks 14, 15, 16, 17, 18
@g-go-code --timeout-minutes 15 bugs-only
@g-go-code --max-iterations 10 --timeout-minutes 60 --swarm
@g-go-code --max-iterations 1 tasks 14
```

`--mode fast` and `--mode cheap` are equivalent (both → haiku-class). `--mode standard` is
the explicit form of the default (sonnet-class). Omit the flag to inherit the host IDE's
current model.

`--max-iterations N` caps the total item count for the session (default `5`, env override
`GALD3R_MAX_ITERATIONS`). `--timeout-minutes M` caps the wall-clock budget (default `30`,
env override `GALD3R_TIMEOUT_MINUTES`). Whichever hits first stops new claims cleanly; the
in-flight item finishes and the session writes its summary. See "Iteration and Timeout
Limits" above for full semantics.

Let's implement.
