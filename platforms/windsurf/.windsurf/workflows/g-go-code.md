---
subsystem_memberships: [TASK_MANAGEMENT]
---
Implementation-only backlog execution: $ARGUMENTS

## Mode: IMPLEMENT ONLY

This command runs **coding and bug-fixing** — it does NOT verify. Every completed item is
marked `[🔍]` (Awaiting Verification) so a **separate agent session** can independently confirm it.

> **Scope is set by the coordinator, not here.** Workspace scope (`--local` / `--workspace <id>`
> / `--workspace` / the `g_go_default_scope` config default) is resolved by the `g-go` /
> `g-go-swarm` coordinator at its Auto-Plan Step 1a and handed down as the already-filtered work
> queue (or explicit task IDs). When `g-go-code` is invoked directly with explicit task IDs, it
> implements exactly those IDs. When invoked directly with no IDs, treat the scope as **local-only**
> — `g-go-code` does not re-evaluate `g_go_default_scope`; let `g-go` own the controller-default
> workspace_all expansion.

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

## Completion Signal Contract (T1175)

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

## Journal Capture on Novel Pattern (T1010)

After a task reaches `[🔍]`, IF the implementation surfaced a **novel pattern,
decision rule, or anti-pattern** worth remembering for next time, write **one**
concise entry to the active agent's journal:

```
{platform}/agents/{slug}/journal/YYYY-MM-DD-{task-ref}-{slug}.md
```

- Frontmatter and 3–10 line body per `{platform}/agents/JOURNAL_FORMAT.md`
  (`date`, `agent`, `task_ref`, `category`, `tags`).
- Use `category: anti-pattern` for mistakes-to-avoid — `g-rl-25` surfaces these
  prominently at the next session start so the same trap is not re-hit.
- **Not every task earns an entry.** Skip routine work; brevity is the point.
- This is durable, offline, per-agent learning (no Docker/DB) and supplements
  `g-skl-learn`'s project-wide `learned-facts.md`. It is **not** part of the
  mandatory completion signal — a missing journal entry never blocks `[🔍]`.

## Iteration and Timeout Limits (T1175)

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

## Session Resume after Crash (`--resume T{id}` — T967)

Long-horizon implementation can be interrupted by a process kill, OOM, or power loss. `g-go-code` writes a **continuity artifact** at each mid-task checkpoint (step 4a) and the code-complete checkpoint commit (step 7b), so a crashed session can resume from the last clean state instead of replaying conversation history.

The continuity artifact (`continuity_artifact.md`, written into the task's worktree) is a structured resume summary — **not** a transcript. It records: task ID, completed ACs (checked list), pending ACs, last tool summary, next planned action, and blockers. It is written **atomically** (temp file + rename) and **before** the checkpoint commit, so it survives an interrupt mid-commit. It complements `gald3r worktree session` (literal JSONL transcript): the artifact answers *"where was I and what is left"*.

### Behavior

When `$ARGUMENTS` contains `--resume T{id}`:

1. **Locate the worktree** for `T{id}` via `gald3r worktree resume -TaskId {id} -Role code -Owner {owner}`. The helper reads `.gald3r-worktree.json` (`last_checkpoint_sha`, `continuity_artifact_path`) and the worktree's `continuity_artifact.md`.
2. **Print the resume banner** (verbatim format):
   ```
   Resuming from checkpoint {sha} — {N} ACs complete, {M} remaining
   ```
   `{N}`/`{M}` are the checked (`- [x]`) / unchecked (`- [ ]`) AC counts read from the artifact.
3. **Inject the artifact as a context prefix** — the artifact body (returned as `context_prefix` under `-Json`) is prepended to the implementation context so the resumed session re-grounds on the goal, the ACs already done, and the next planned action before claiming new tool work.
4. **Continue the b/c/d/e/f loop** from the pending ACs. The worktree, branch, and `last_checkpoint_sha` are reused — no new worktree is created for the resumed task.

```powershell
# Resume a crashed implementation of T824 from its last checkpoint
gald3r worktree resume -TaskId 824 -Role code -Owner cursor -Json
```

If no worktree or no `continuity_artifact.md` exists for the task, `--resume` reports that there is nothing to resume and falls back to a normal (fresh) implementation pass.

## Mid-Flight Course Correction (`/steer` + `/queue` — T969)

A running `g-go-code` session does **not** need to be restarted to redirect it. Two small files
dropped into the **worktree root** let a user steer the work in flight or queue follow-up work to
run after the main goal completes. Both files are written by their own commands (`@g-steer`,
`@g-queue`) and consumed by this command at well-defined points in the loop. Like `--resume`, the
mechanism is file-grounded so it survives context compression and works across separate sessions.

| File (at worktree root) | Written by | Read by | Lifecycle |
|---|---|---|---|
| `steer.md` | `@g-steer T{id} "..."` | g-go-code AC-gate poll (step b2.5) | One-shot: injected as a steering prompt, then **deleted** |
| `queue.md` | `@g-queue T{id} "..."` | g-go-code drain step (step 7d) | Append-only list; each `- [ ]` item processed after the main goal completes |

Both files live at the **worktree root** for the task (`<worktree>/steer.md`, `<worktree>/queue.md`),
i.e. the per-branch isolated checkout created by `gald3r worktree create`. The
worktree helper owns all reads/writes so the file format and locating logic stay in one place:

```powershell
# @g-steer writes (overwrite — latest steer wins)
gald3r worktree steer -TaskId 824 -Role code -Owner cursor -SteerText "focus on the accept loop, skip the auth tests" -Json

# g-go-code AC-gate poll (read + clear; one-shot)
gald3r worktree steer -TaskId 824 -Role code -Owner cursor -Json

# @g-queue appends a follow-up
gald3r worktree queue -TaskId 824 -Role code -Owner cursor -QueueText "after done, also add prometheus metrics" -Json

# g-go-code drain reads the pending queue
gald3r worktree queue -TaskId 824 -Role code -Owner cursor -Json
```

Installed templates may call the helper from the `gald3r worktree`
skill directory when no root `scripts/` copy exists (same resolution rule as `--resume`).

### steer.md — interrupt the current trajectory

At **every AC-gate iteration** (step b2.5 below), the implementer polls for `steer.md`. If it
exists:

1. **Inject** the file's `## Steering Prompt` body as a high-priority steering instruction into the
   next reasoning step — it takes precedence over the prior plan for the remainder of the task.
2. **Log** `STEERED by user at turn N` (N = current AC-gate iteration count) to the task's
   `## Status History` and surface the same line in the running output.
3. **Delete** `steer.md` after injection (the helper's read mode does this). The steer is
   one-shot — a new steer requires a new `@g-steer` write. This prevents a stale steer from
   re-firing on every subsequent iteration.

If no `steer.md` exists, the poll is a silent no-op (`steered: false`) and the loop continues.

### queue.md — follow-up work after the main goal

`queue.md` is an append-only checklist of follow-up prompts. It is **not** processed mid-task —
items are drained only after the main goal's acceptance criteria are all met and the task reaches
`[🔍]` (step 7d below). Each `- [ ]` item becomes a follow-up unit of work: the implementer either
(a) handles it inline within the same worktree when it is small and in-scope, or (b) when it is a
distinct deliverable, files a real follow-up task via `g-skl-tasks CREATE TASK` (per the Follow-Up
Task Filing Gate) and references it. Drained items are checked off (`- [x]`) in `queue.md` so a
resumed or re-run session does not reprocess them.

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


### Step 0 — Workspace Member Clean-Status Preflight (T1431)

Before the WPAC gate / task selection / claim / worktree creation, run the **read-only** workspace
member clean-status preflight: scan `.gald3r/workspace/workspace_manifest.yaml`, run
`git -C <path> status --short` on each `autonomous_child` member, and either print
`Workspace clean -- N members checked` (proceed) or a per-repo dirty-status table asking the user
to commit/stash first. Never auto-commits or writes. `--skip-member-clean-check` bypasses with a
printed warning. Additive to the Housekeeping Commit Gate. **Full authoritative algorithm: see
`g-go.md` Step 0.**

---

### WPAC inbox Gate (Only When WPAC is configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a WPAC participant. WPAC is configured only when `.gald3r/workspace/topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a WPAC group member.

If WPAC is configured, run the re-callable WPAC inbox check when the hook exists.

> **Tool routing (BUG-031)**: on Windows, invoke this snippet through the **PowerShell tool**, not Bash. It uses PowerShell-only syntax (`@(...)` array, `Where-Object`, `Test-Path`, `Select-Object`, pipeline). Routing it through Bash produces a parse error such as ``syntax error near unexpected token `('`` — that failure is a tool-selection error, **NOT** a real WPAC conflict gate. Re-run via PowerShell. On Linux/macOS hosts use `pwsh` if available; if neither shell can reach the hook, treat the gate as advisory and let Workspace-Control routing re-evaluate.

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py", ".agent\hooks\g-hk-wpac-inbox-check.py", ".codex\hooks\g-hk-wpac-inbox-check.py", ".opencode\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-wpac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the WPAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
gald3r housekeep -Mode preflight -Apply -TaskId <id-when-known> -Json
```

Behavior:

- **`clean`** -> continue.
- **`safe-gald3r-housekeeping`** -> the helper stages **only** allowlisted controller `.gald3r/` paths via explicit `git add -- <paths>` (never `git add .`), re-checks for drift, and creates a focused `chore(gald3r): preflight gald3r housekeeping` commit. The run continues automatically.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown `.gald3r` paths / member-repo `config-fault`** -> the helper exits non-zero, the existing Clean Controller Gate hard-block applies, and the run STOPs with the exact unsafe paths listed.

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/wpac_auto_actions.log, workspace/sent_orders/, workspace/inbox.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the WPAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `<gald3r_source>`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r worktree create -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/workspace/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

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

**Regression canonical (BUG-031 family)** — the WPAC inbox hook lookup snippet that triggered T1144:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
```

This snippet appears literally in the WPAC inbox Gate section below. It is PowerShell-only — invoking it via `Bash(...)` produces `syntax error near unexpected token '('` (exit 2). That error is a **tool-routing failure**, NOT a real WPAC conflict or hook-missing state. Re-route through PowerShell and the call succeeds; do not enter an error-driven retry loop.

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
- **Active workflow profile (T1239)** — load once via `gald3r project-type resolve` (active
  skill folder; see g-skl-tasks "Reading the active profile"). Its
  `task_statuses[]` (`id`, `symbol`, `skip_in_pipeline`) is the source of truth
  for claimable-vs-skip and status-transition order, replacing hardcoded status
  strings (AC1). Absent `.gald3r/config/workflow_profiles/` → built-in
  `software_dev` lifecycle (unchanged behavior).
- `git log --oneline -10` — recent changes

### 2. Build the Work Queue

**Bugs first (Tier 1), then tasks (Tier 2).** Claimable-vs-skip below follows the
active profile's `task_statuses[].skip_in_pipeline` (T1239 AC1); the symbols shown
are the `software_dev` defaults.

**Tier 1 — Open bugs:**
- From `BUGS.md` + `bugs/` files; Critical → High → Medium → Low
- Skip bugs with external blockers
- **Skip `[🚨]` bugs** — log in Skipped section as "Requires-User-Attention — human review needed"

**Tier 2 — Pending tasks:**
- Status `[ ]` (pending), `[📋]` (ready), or stale `[📝]` (speccing claim expired)
- **Skip non-expired `[📝]` speccing claims** — log owner/expiry in Skipped section as "Speccing-In-Progress"
- For stale `[📝]` claims, append a Status History takeover row naming the prior `spec_owner` before proceeding
- **NOT** `[🚨]` (requires-user-attention) — **skip entirely**, log in Skipped section as "Requires-User-Attention — human review needed"
- **Skip `[⌛]` (waiting) tasks** — prerequisites (`spec_task_reqs` or `spec_reqs`) not yet met; use `@g-task-upd --promote` when ready
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
gald3r worktree create -TaskId {id} -Role code -Owner {platform_or_agent_slug} -Json
```

Installed templates may call the helper from the `gald3r worktree` skill directory when no root `scripts/` copy exists.

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
python scripts/graph_impact.py -File "{file_to_be_modified}" -Depth 2 -Json
```

Direct MCP equivalent (when calling tools by name):

```jsonc
// example_app MCP server (muninn plugin)
{ "tool": "graph_impact", "arguments": { "file_path": "{file_to_be_modified}" } }
```

Review the returned `files` list (each entry `{path, relation}` with `relation` ∈ `imports | calls | imports+calls`). If the impact scan reveals > 3 transitively dependent files, add them to the implementation context window before writing. This prevents cross-file breakage ("agent edits one file and breaks another"). Non-blocking: proceed even if the script returns `warning: not_indexed` or falls back to the ripgrep backend.

Use `.claude/skills/g-skl-muninn/scripts/graph_impact.py` for all impact analysis (T1158).

**b0.1a Index freshness check (T1149)** — before relying on impact results, check index state (the wrapper reports it; or call `graph_status` via MCP):

- **Index absent** (`index_missing` / `warning: not_indexed`) → emit this warning, then proceed on the ripgrep fallback (non-blocking):
  ```
  ⚠️ Codebase graph index not found.
     Build it:  python -m docker.gald3r.tools.plugins.muninn.indexers.python_indexer --root .
                node  docker/gald3r/tools/plugins/muninn/indexers/ts_indexer.js  --root .   (TS/JS)
     Or run @g-setup (it offers to build the index + wire the post-commit refresh hook).
     Impact scan falling back to ripgrep — blast-radius estimates may be incomplete.
  ```
- **Index stale** (`graph_status` → `stale: true`, >24h old) **AND** the post-commit hook (`g-hk-graph-update.py`) is not installed → surface a one-line advisory (non-blocking): `ℹ️ Graph index >24h old; install the post-commit refresh hook (see @g-setup) to keep it fresh.`
- **Index fresh** (post-commit hook running) → run silently; no output unless the `files` list is non-empty.

**b0.2 Graphify Code-Graph Query (T874b, opt-in)**

Read `.gald3r/config/AGENT_CONFIG.md` → `context_reduction_mode.graphify_b0_enabled`. When `true`, the coordinator runs a single graph query before bucket spawn (or before single-agent implementation), captures the result as a small context block (typical ≤200 tokens), and passes it to implementer subagents as part of the briefing. When `false` (safe default), this step is skipped and Step b0.1 alone gates the impact context.

Backend fallback order (g-skl-graphify §Backends):

1. **gald3r_muninn MCP** (preferred, T1158) — `graph_impact` / `graph_callers` / `graph_callees` / `graph_deps` for symbol-level call/import resolution. Auto-loaded into the example_app MCP server; see `.mcp.json` `gald3r_muninn` entry.
2. **graphify CLI** — when muninn is unavailable, run `graphify query --root . --symbol {target}` against the local `.graphify/` index. See g-skl-graphify §SETUP for indexing guidance.
3. **tree-sitter + ripgrep fallback** — when neither backend is reachable, fall back to the legacy grep-based context-prep (Step b0.1 + ad-hoc reads). Do NOT halt the run.

Failure modes (never halt the run):

- **Missing backend** — example_app MCP server unreachable AND muninn plugin import fails AND `graphify` CLI not on PATH AND no `.graphify/` index → log "graphify b0 skipped: no backend reachable" and fall through to legacy.
- **Graph staleness** — index older than the orchestration root's last commit (muninn `graph_status` returns `stale: true` when index >24h old) → emit a warning; still use the result (advisory) and append a note recommending re-indexing via the muninn indexer or `graphify update`.
- **Query timeout** (>5s) — abort the query, log "graphify b0 timeout — fell back to legacy", proceed.
- **Empty result** — query returned no symbols / no edges → log "graphify b0 empty — fell back to legacy"; proceed with Step b0.1 context.

The b0.2 query is **advisory**, **non-blocking**, and **single tool call** (g-rl-37 "Think in Code" — one query, ≤200 tokens of returned context). Operators opt in by flipping `graphify_b0_enabled: true` in `AGENT_CONFIG.md`.

**b1) `post_write_lint` step — Post-Write Lint Gate (T919 + T977)** — this is the **delta-lint** step of the implementation loop. It runs **immediately after each `Write` or `StrReplace`/Edit tool call**, inside the per-item b/c/d/e/f loop — *not* at the end-of-task AC gate (b2). The goal is to shrink the feedback loop: catch a syntax error on the file you just wrote and fix it inline **before** advancing to the next write, instead of discovering a pile of broken files when the b2 AC gate or a downstream test runs.

> **Loop placement (explicit)**: `post_write_lint` belongs to the implementation loop (Step 4 → b), one rung below b2. After every Write/Edit, run `post_write_lint` → fix inline if it fails → then continue editing. The b2 AC gate and the b3.5 Definition-of-Done gate remain the end-of-task gates; `post_write_lint` is the per-write gate that feeds them clean files.

Canonical entry point (PowerShell, runs the per-extension check for you):

```powershell
python scripts/gald3r_post_write_lint.py -FilePath "{relative_path_to_written_file}" -ProjectRoot . -Json
```

Per-language lint commands (single-line PowerShell-safe per g-rl-08 — no multi-line `python -c`):

| Extension | PowerShell lint command (run from the worktree/project root) |
|-----------|-------------|
| `.py` | `python -m py_compile "{file}"` |
| `.json` | `python -c "import json,sys; json.load(open(sys.argv[1]))" "{file}"` |
| `.yaml` / `.yml` | `python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]).read())" "{file}"` |
| `.toml` | `python -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" "{file}"` |
| `.ts` / `.tsx` / `.js` | `npx tsc --noEmit` (only when a `tsconfig.json` is present; else skip) |
| `.ps1` / `.psm1` / `.psd1` | `$errs=$null; [System.Management.Automation.Language.Parser]::ParseFile("{file}", [ref]$null, [ref]$errs) > $null; if ($errs.Count) { throw $errs[0].Message }` — or the lighter `[scriptblock]::Create((Get-Content "{file}" -Raw)) > $null` (throws on a syntax error). The shipped helper uses `PSParser::Tokenize`, which also throws on malformed PowerShell. |
| Markdown / `.md` / TASKS.md / other prose | Pass silently (use `--skip-post-lint` for explicit prose-only runs) |

Each `python -c` form is **single-line** and passes the file as `sys.argv[1]` so PowerShell never has to interpolate the path into the Python string (avoids the quoting/parse pitfalls called out in g-rl-08). On a clean parse the command exits `0`; on a syntax error it raises and exits non-zero.

If the helper script exits non-zero (`exit 2` = syntax error), **stop and fix the file before proceeding (AC4 — inline fix)**. Do not advance to the next write. Treat a `post_write_lint` failure the same as a TypeScript compile error — it blocks continuation. Re-run `post_write_lint` on the fixed file; only a clean (exit 0) result lets the loop continue.

**`--skip-post-lint` flag (AC5)** — when `$ARGUMENTS` contains `--skip-post-lint`, the `post_write_lint` step is suppressed for the whole session. Use it for documentation-only or coordination-only runs (Markdown, `TASKS.md`/`BUGS.md` index edits, `.gald3r/` housekeeping) where a syntax linter has nothing meaningful to check. The flag does **not** disable the b2 AC gate or b3.5 DoD gate — it only skips the per-write delta lint. The helper already passes silently on prose/unknown extensions, so `--skip-post-lint` is mainly an explicit-intent signal that avoids spawning the lint subprocess at all on non-code writes; record `post_write_lint: SKIPPED (--skip-post-lint)` once in the session summary when it is set.

**Worked examples (AC6)** — three delta-lint scenarios showing the fix-inline-before-proceeding loop:

*Python write* — you just wrote `src/services/charge.py`:

```powershell
# Right after the Write/Edit tool call:
python scripts/gald3r_post_write_lint.py -FilePath "src/services/charge.py" -ProjectRoot . -Json
# Equivalent raw check the helper runs:
python -m py_compile "src/services/charge.py"
# exit 0  -> {"ok":true,"message":"Syntax OK (.py)",...}  -> continue the loop
# exit 2  -> {"ok":false,"message":"Syntax error (.py)","detail":"... IndentationError ..."}
#            -> STOP, fix the indentation/typo in charge.py, re-run the lint, only then proceed
```

*JSON write* — you just wrote `config/feature_flags.json`:

```powershell
python scripts/gald3r_post_write_lint.py -FilePath "config/feature_flags.json" -ProjectRoot . -Json
# Equivalent raw check:
python -c "import json,sys; json.load(open(sys.argv[1]))" "config/feature_flags.json"
# A trailing comma -> json.decoder.JSONDecodeError -> exit 2 -> fix the comma inline, re-run, then continue
```

*YAML write* — you just wrote `.github/workflows/ci.yml`:

```powershell
python scripts/gald3r_post_write_lint.py -FilePath ".github/workflows/ci.yml" -ProjectRoot . -Json
# Equivalent raw check:
python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]).read())" ".github/workflows/ci.yml"
# A bad indent / tab -> yaml.scanner.ScannerError -> exit 2 -> fix the indentation inline, re-run, then continue
```

In all three cases the rule is identical: **lint the file you just wrote → if it fails, fix it inline and re-lint → only a clean exit 0 advances the loop to the next write.**

**Parity note (AC7)** — this `g-go-code.md` under canonical `project_template/.claude/commands/` is the **source of truth** for the `post_write_lint` step. The per-IDE mirrors (`.claude/commands/g-go-code.md`, `.cursor/commands/g-go-code.md`, and the other platform copies) are **propagated later** by `custom_scripts/platform_parity_sync.ps1` — do **not** hand-edit the mirrors. The lint helper `gald3r_post_write_lint.py` lives under the same canonical `.gald3r_sys/scripts/` tree and is synced alongside.

**b2) AC gate** — before moving on, walk every `- [ ]` acceptance criterion in the task spec:
  - Is this criterion now satisfied? Check the actual files, not just intent.
  - Any unmet criterion → return to **(b)** and address it.
  - Cannot meet a criterion this session → log as a Blocker in step 5 and **skip this task entirely** (do not mark `[🔍]` for partial work).
  - **Stub/TODO scan**: search files modified for this task for bare `# TODO`, `// TODO`, `pass` (non-abstract), `raise NotImplementedError`, `throw new Error("not implemented")` — each is an unmet criterion until annotated `TODO[TASK-X→TASK-Y]` with a follow-up task created (see `g-rl-34`)
  - **Bug-discovery check**: any pre-existing bug encountered while implementing must have a BUG entry + `BUG[BUG-{id}]` comment before `[🔍]`; bugs introduced by this task must be fixed inline (see `g-rl-35`)
  - **Constraint check**: run `@g-constraint-check` mentally — does this implementation violate any active constraint? Any `🚫 VIOLATION` blocks `[🔍]`
  - **Workspace boundary check**: run `g-skl-workspace` ENFORCE_SCOPE before editing and before `[🔍]`; omitted metadata is current-repo-only, unknown manifest repo IDs block, and member repo writes require explicit `workspace_repos`, compatible `workspace_touch_policy`, authorization text, reviewed member git status, and manifest write permission. **`workspace_touch_policy: member_only` is a write-scope limiter (changes land exclusively in the named member repo) — it is NOT a location gate requiring the agent to be opened inside the member repo. The controller may implement `member_only` tasks by writing to member on-disk paths after the Clean Controller Gate passes on that member root. (BUG-098)**
  - All criteria confirmed met → continue.
**b2.5) Steer poll (T969)** — at every AC-gate iteration, poll for a user steer dropped into the worktree root:
  ```powershell
  gald3r worktree steer -TaskId {id} -Role code -Owner {owner} -Json
  ```
  - `steered: false` → silent no-op; continue the loop.
  - `steered: true` → **inject** the returned `steer_prompt` body as a high-priority steering instruction for the next reasoning step (it takes precedence over the prior plan for the rest of this task), **log** `STEERED by user at turn N` to `## Status History` (and the running output), and note that the helper has already **deleted** `steer.md` so the steer fires exactly once. Re-evaluate the AC list under the new steering before proceeding. See "Mid-Flight Course Correction (`/steer` + `/queue`)" above.
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
**f)** Stamp implementation branch + SHA on task file frontmatter (BUG-095 fix, T1373):
  Before writing the `[🔍]` status, capture and write to the task file's YAML frontmatter:
  ```powershell
  $branch = git branch --show-current 2>$null
  $sha    = git rev-parse HEAD 2>$null
  ```
  Write both into the task file immediately after `completed_date:`:
  ```yaml
  implementation_branch: <branch>   # e.g. dev
  implementation_sha: <full-40-char-sha>
  ```
  If `git` is unavailable or returns an error, leave both fields as empty string `''` — a stamping failure must NEVER prevent the `[🔍]` transition. In `--swarm` mode, each bucket agent stamps its own tasks; the coordinator does NOT re-stamp.
**g)** Queue status update → mark `[🔍]` (NOT `[✅]`) in both task file and TASKS.md during the final batch write
**h)** Move to next item

> **IMPORTANT**: Mark every completed item `[🔍]`, never `[✅]`.
> `[✅]` requires a separate agent session running `@g-go-review`.

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

**Continuity artifact write (T967):** after the self-evaluation and the Status History row, write the **continuity artifact** so the session is resumable from this checkpoint after a crash:

```powershell
gald3r worktree checkpoint -TaskId {id} -Role code -Owner {owner} `
    -Goal "{1-line task goal}" `
    -CompletedAcs "{AC text}","{AC text}" `
    -PendingAcs "{AC text}","{AC text}" `
    -LastToolSummary "{what the last operations did}" `
    -NextAction "{what this session will do next}" `
    -Blockers "{none|description}"
```

This writes `continuity_artifact.md` atomically into the worktree and updates the `.gald3r-worktree.json` marker (`continuity_artifact_path`; `last_checkpoint_sha` is set later by step 7b once a commit exists). The artifact is the structured resume summary read by `g-go-code --resume T{id}`.

**Rules:**
- Checkpoint is **mandatory** — not optional. Fires every N major operations with no exceptions.
- A task completed with ≥1 checkpoints must show those rows in `## Status History` before being marked `[🔍]`.
- The continuity artifact write is part of the checkpoint — write it BEFORE any checkpoint commit so it survives a crash mid-commit.
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

### 5b. Skill Authoring (Opt-In, Complexity-Gated) (T1251)

After Auto-Learn captures *facts*, this step optionally captures a *procedure* — authoring a
new `SKILL.md` when the just-completed task discovered a non-trivial repeatable workflow. This
closes the procedural-memory loop: the skill library grows through use instead of only by hand.
Fact capture (5a) is "what I now know"; skill authoring (5b) is "how I'd do this again".

**Runs only after the task is marked `[🔍]`, before Step 6.** It is opt-in and never blocks the
pipeline — declining or skipping is a normal outcome, not an error.

**AC1 — Complexity gate (ALL evaluated; trigger when ANY ≥1 fires):**

| Signal | How it is measured |
|--------|--------------------|
| 5+ distinct file edits | Count `Write` + `Edit`/`StrReplace` calls in this task's b4 Handoff Report `Files Changed` |
| Error recovery occurred | A post-write lint/syntax check returned `exit 2` and was fixed, OR `Issues Discovered` is non-empty |
| User course-correction | A `/steer` interrupt (Step 156 flow) was applied during this task |
| Non-trivial multi-step pattern | Task `complexity_score` ≥ 7 in frontmatter, OR the locked Implementation Plan (Step 0) had ≥4 ordered steps |

If **no** signal fires → skip silently (note `🧩 skill-authoring: not triggered (below complexity gate)`).

**AC6 — Opt-out:** When the gate fires, prompt once: *"This task discovered a reusable
workflow. Author a draft skill for it? (y/N)"*. In autopilot / non-interactive / swarm runs the
default is **N** (defer) — record the candidate in the Handoff Report (see AC7) rather than
writing a file unprompted. Declining is **not** an error and never fails the task.

**AC3 — Synthesis:** When authoring proceeds, synthesize the discovered pattern into gald3r's
native `SKILL.md` format (the format already defined in `AGENTS.md`). Capture: the trigger
condition, the ordered procedure, the gotchas hit (from `Issues Discovered`), and a worked
example. Do **not** copy task-specific identifiers — generalize to the reusable pattern.

**AC4 — Write location (canonical-first):** Write the draft to the canonical source as an
auto-generated skill, distinguished by the `g-skl-auto-` prefix and `auto_generated: true`
frontmatter (NOT a subfolder — the skills tree is flat for parity deployment):

```
.claude/skills/g-skl-auto-<slug>/SKILL.md
```

Frontmatter (gald3r SKILL.md standard + provenance):

```yaml
---
name: g-skl-auto-<slug>
description: <one-line trigger + what it does>
tags: [auto-generated, <domain-tags>]
category: auto-generated
auto_generated: true
source_task: T<id>
authored_date: "<YYYY-MM-DD>"
review_status: draft   # human promotes to `reviewed` to bless it
---
```

> Auto-generated skills land as `review_status: draft`. They are usable immediately but flagged
> for human blessing — surface drafts via `@g-skill-review`.

**AC5 — Cross-platform parity:** Never hand-copy into each IDE platform dir. After writing the
canonical skill, deployment to `.claude/skills/`, `.cursor/skills/`, `.agent/skills/`, etc. is
handled by:

```powershell
custom_scripts/platform_parity_sync.ps1 -SyncGaldSys -Sync
```

In a single-repo / member-only run where cross-repo propagation is out of scope, deploy only to
the **local** platform dirs of the active repo and note that ecosystem-wide parity is deferred to
the next `-SyncGaldSys -Sync`.

**AC7 — Handoff Report event:** Record the outcome as a `[📝]` line in the task's
`## Handoff Report` (under a `Skills Authored` note), regardless of branch taken:

```markdown
- [📝] Skill authoring: <one of>
      authored g-skl-auto-<slug> (review_status: draft)   |
      candidate deferred (opt-out) — pattern: <summary>    |
      not triggered (below complexity gate)
```

Include a one-line summary in the handoff: `📝 1 draft skill authored (g-skl-auto-<slug>)` —
omit when not triggered.

> **Skill *update*** (improving an existing skill) is out of scope here — creation only.

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

0. **Continuity artifact first (T967)**: ensure the worktree's `continuity_artifact.md` reflects the final pre-commit state (run `gald3r worktree checkpoint ...` if it has drifted since the last mid-task checkpoint). Writing it before the commit guarantees a crash mid-commit still leaves a resumable artifact.
1. Stage only intended paths by explicit allowlist.
2. Include implementation files plus coordinator-owned shared writes needed for `[🔍]` handoff.
3. Commit with a message that names the implemented task/bug IDs and states that the commit is ready for independent review.
4. Record the checkpoint branch and commit SHA in the handoff summary, and write the SHA back onto the marker so resume reports it: `gald3r worktree checkpoint -TaskId {id} -Role code -Owner {owner} -CheckpointSha {sha}` (updates `last_checkpoint_sha` + refreshes the artifact).

Snapshot review mode is fallback-only. Use it when the user explicitly requests uncommitted review, when a source cannot be made branch-addressable, or when a failed reconciliation must be inspected read-only. Do not make dirty snapshot mode the default.

### 7b-pr. Optional GitHub PR-Open Hook (T1291)

**Run AFTER the checkpoint commit in step 7b — never before.** This hook is triple-gated to ensure zero behavior change when GitHub integration is disabled.

**Triple-gate evaluation (must ALL be true to invoke):**
1. Read `.gald3r/.identity` → `project_type=software_development` (else skip silently)
2. Read `.gald3r/config/AGENT_CONFIG.md` → `github_integration: enabled` (else skip silently)
3. Read `.gald3r/config/AGENT_CONFIG.md` → `github_pr_hooks: enabled` (else skip silently)

**When all three gates pass:** invoke `g-pr-open --task <id>` for each task that transitioned `[🔄]→[🔍]` this session.

**Behavior:**
- Invocation happens AFTER shared writes (TASKS.md, task file) AND the checkpoint commit.
- A PR-open failure does NOT roll back the `[🔍]` status — the implementation is done; the PR is a delivery artifact.
- On success: append Status History row: `| {date} | in-progress | awaiting-verification | {agent} | PR opened: {pr_url} |`
- On failure: append Status History row: `| {date} | awaiting-verification | awaiting-verification | {agent} | PR-open failed: {error}; task stays [🔍] |` and surface a notice in the session summary so the user can retry manually.
- In `--swarm` mode: the coordinator runs this hook once per completed task after reconciliation, not per-bucket.

**Default state:** all three flags are `disabled` / absent → behavior is byte-identical to pre-T1291.

### 7c. Rolling Implementation Waves

`g-go-code` and `g-go-code --swarm` must optimize for throughput. A code-complete checkpoint is a stable handoff point, not a global stop sign.

After a checkpoint commit is created:

1. Recompute the runnable queue immediately.
2. Treat dependencies that are `[🔍]` / `awaiting-verification` as implementation-satisfied when they have a branch-addressable checkpoint and the downstream task does not declare `requires_verified_dependencies: true`.
3. Start the next coding wave from the latest checkpoint or member-repo branch that contains the dependency output.
4. Record checkpoint-dependent downstream work in the dependent task's Status History:
   `Started on unverified dependency T{id} at checkpoint {sha}; rework required if review fails.`
5. Continue coding until no runnable work remains, a WPAC conflict appears, Workspace-Control preflight fails, or a task explicitly requires verified dependencies.

Review remains mandatory, but `g-go-code*` only prepares the handoff. It must not start the review lane itself. A later review failure requeues only the failed item and any downstream tasks that explicitly consumed its checkpoint. Do not stop unrelated implementation work merely because a prior item is awaiting review.

Tasks may force the old strict behavior with:

```yaml
requires_verified_dependencies: true
```

Use that field for destructive operations, irreversible migrations, public release/signing, production writes, security-sensitive changes, or any task whose acceptance criteria explicitly require verified predecessor behavior.

### 7d. Drain Follow-Up Queue (T969)

After a task's main goal is complete (all AC met, task at `[🔍]`) and before recomputing the next rolling wave, drain any follow-up prompts the user queued for that task's worktree:

```powershell
gald3r worktree queue -TaskId {id} -Role code -Owner {owner} -Json
```

For each pending `- [ ]` item returned in `items`:

1. **In-scope + small** → handle it inline within the same worktree (additional edits + the standard b1/b2/b2.5 gates), then check the item off (`- [x]`) in `queue.md`.
2. **Distinct deliverable** → file a real follow-up task via `g-skl-tasks CREATE TASK` (Follow-Up Task Filing Gate — never a slug-only name), reference the new `T{id}` next to the checked-off item, and include it in the session summary's "Follow-Up Tasks Filed" block.

If `pending_count: 0`, this step is a silent no-op. Queue draining never blocks the `[🔍]` of the main task — the main goal completing is what triggers the drain, not the other way around.

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


### WPAC inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the WPAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-wpac-read` before continuing.

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

**File-scope output (T1059 lock claim)**: alongside `buckets = [[task_ids...]]`, record each bucket's planned file set (`bucket_planned_paths` = the union of its tasks' `workspace_repos` / planned touch set / subsystem-to-file mapping, as repo-relative paths). Because buckets are partitioned on subsystem/file boundaries, these sets do not overlap by construction. Each set is passed verbatim to `-LockFiles` at Step S6 so overlaps are enforced as `LOCK_CONFLICT` at worktree-create time.

**Step S5: Display partition plan**
```
[SWARM] Work queue: {M} items → {N} agents
  Bucket 1: Task 7 (vault-knowledge-store), Task 9 (vault-knowledge-store)
  Bucket 2: Task 10 (task-lifecycle-management), Task 11 (behavioral-rules-engine)
  Bucket 3: Task 12 (cross-project-coordination-WPAC)
Spawning {N} implementation agents...
```

**Step S6: Spawn sub-agents**
- Before spawning, create or reuse one coding worktree per bucket:
  ```powershell
  gald3r worktree create -TaskId bucket-{bucket_number} -Role code-swarm -Owner {platform_or_agent_slug} -BucketId {bucket_number} -LockFiles {bucket_planned_paths} -BucketTtlMinutes 60 -StaleBaseAction Recreate -Json
  ```
  **`-StaleBaseAction Recreate` is mandatory for rolling-wave bucket worktrees.** Without it,
  iteration-2+ bucket worktrees silently reuse the iteration-1 worktrees (same `TaskId
  bucket-N`), which forked from the session-start HEAD. Implementers then miss all Alembic
  migrations, model files, and router wiring committed by prior iterations. With `Recreate`,
  the helper detects that the stored `base_sha` predates the current HEAD, removes the stale
  worktree, and creates a fresh one from the latest commit. Task-specific worktrees (not
  bucket worktrees) should default to `-StaleBaseAction Warn` so stale-base conditions are
  surfaced but not silently discarded.
- **Swarm file-lock claim (T1059, mandatory for `code-swarm`).** `-BucketId {bucket_number}` plus `-LockFiles {bucket_planned_paths}` (the bucket's planned file set from Step S4) make the helper write a lock manifest *before* the worktree exists. If another active bucket already claims an overlapping path, `-Action Create` fails with `LOCK_CONFLICT` and the colliding bucket is never spawned. `-Role code-swarm` **fails closed** (`LOCK_REQUIRED`) when `-LockFiles` is empty, so the lock layer can never silently no-op. Routing every bucket through `gald3r worktree` is what makes the lock apply — do not create bucket worktrees by any other path. `-BucketTtlMinutes 60` sets the claim lifetime (expiry = created_at + 2×TTL).
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
0. **Lock report (T1059)**: before reconciling, run `gald3r worktree lock-report -Json` and surface any multi-bucket path in the session summary as a `WARN` (not a hard block) — this complements the overlap check in step 2 and the Swarm Reconciliation Gate.
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
@g-go-code --skip-post-lint docs-only
```

`--skip-post-lint` suppresses the per-write `post_write_lint` delta-lint step (Step 4 b1) for the
session — use it for documentation-only / `TASKS.md`-update runs where a syntax linter has nothing
to check. It does not disable the b2 AC gate or b3.5 DoD gate.

`--mode fast` and `--mode cheap` are equivalent (both → haiku-class). `--mode standard` is
the explicit form of the default (sonnet-class). Omit the flag to inherit the host IDE's
current model.

`--max-iterations N` caps the total item count for the session (default `5`, env override
`GALD3R_MAX_ITERATIONS`). `--timeout-minutes M` caps the wall-clock budget (default `30`,
env override `GALD3R_TIMEOUT_MINUTES`). Whichever hits first stops new claims cleanly; the
in-flight item finishes and the session writes its summary. See "Iteration and Timeout
Limits" above for full semantics.

Let's implement.

## Push offer (final session summary only)

After all items are marked `[🔍]` and the session summary is written, include a single push offer:

```
{N} commits are ready on {branch}. Review and push when satisfied:
  git log origin/{branch}..HEAD --oneline
  git push origin {branch}
Want me to push now?
```

**Rules:** Offer push **once**, at the end of the session summary only. Do NOT offer push after each individual task commit — the session is still running. If the user replies "yes": push immediately.


## Structured output (`--json` / `--toon`) — T1381 / T1382

This command supports machine-readable output in addition to its default text/markdown:

- `--json` → structured JSON envelope via **g-skl-json-output** (`{ gald3r_version, generated_at, command, schema, data }`). For scripting, CI gates, dashboards.
- `--toon` → **g-skl-toon-output** TOON: compact, lossless, LLM-friendly (tabular arrays state keys once; ≥20% smaller than JSON). For agent handoff / context injection / vault ingestion.
- `--md` forces markdown. With no flag, AGENT_CONFIG `output_format` decides (default `markdown`, unchanged).

Output is saved to `html_output_dir` (default `docs/`) as `YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.json|.toon` per g-rl-01.
