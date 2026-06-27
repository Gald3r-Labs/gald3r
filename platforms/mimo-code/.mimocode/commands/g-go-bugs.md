---
subsystem_memberships: [BUG_AND_QUALITY]
---
Dedicated bug-fix pipeline — reproduce → fix → regression test → adversarial review: $ARGUMENTS

## Mode: BUG-FIX PIPELINE

`g-go-bugs` is a **two-phase pipeline** specialized for fixing open bugs. Phase 1 reproduces and
fixes each bug in severity order; Phase 2 spawns an independent reviewer agent to verify the fix.

> **Independence guarantee**: The Phase 2 reviewer is a fresh Task subagent. It has **no access**
> to Phase 1's conversation history, implementation decisions, or working context. It verifies
> the fix cold from the committed checkpoint.

> **Difference from `@g-go`**: `g-go` processes both tasks and bugs, bugs-first. `g-go-bugs`
> processes ONLY bugs — useful for dedicated bug-blitz sessions without disturbing the task queue.
> The T1114 auto-task bridge ensures high/critical bugs already have linked fix tasks, so both
> paths are complementary.

---

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between
options, or approve a proposal.** This command is designed for fire-and-forget operation. The
user typed it and is not watching this session.

The **only** valid reasons to stop are the documented **hard-gate failures** (WPAC conflict
exit-code `2`, dirty orchestration root outside the staging allowlist, `[🚨]` bugs, or all bugs
deferred). Everything else is resolved silently by the auto-plan rules.

---

## Invocation

```
@g-go-bugs                          # fix all open bugs, critical→high→medium→low
@g-go-bugs severity:critical,high   # only critical + high
@g-go-bugs severity:medium,low      # only medium + low
@g-go-bugs bug:BUG-042              # specific bug
@g-go-bugs bug:BUG-042,BUG-043      # specific bugs (comma-separated)
@g-go-bugs --dry-run                # report what would be fixed, no changes
```

---

## Auto-Plan Algorithm (no explicit bug IDs in `$ARGUMENTS`)

When `$ARGUMENTS` is empty or contains only severity filters:

1. Read `.gald3r/BUGS.md` for all bugs with `status: Open` (indicators `[🔴]` `[🟠]` `[🟡]` `[⚪]`)
2. Apply severity filter if given (e.g. `severity:critical,high` → only `[🔴]` `[🟠]`)
3. Skip `[🚨]` bugs (requires-user-attention) — log in Skipped section, never auto-retry
4. Skip bugs where `verifier_claim_expires_at` has not expired (non-expired `[🕵️]` claims)
5. Order: Critical → High → Medium → Low (within same severity, lower BUG-NNN first)
6. Zero runnable bugs → output `[g-go-bugs] No runnable bugs. Nothing to fix.` and exit cleanly

When `$ARGUMENTS` provides explicit bug IDs (`bug:BUG-NNN`), use those exactly.

---

## Step 0 — Workspace Member Clean-Status Preflight (T1431)

Before the WPAC gate / bug-queue build / claim / worktree creation, run the **read-only** workspace
member clean-status preflight: scan `.gald3r/workspace/workspace_manifest.yaml`, run
`git -C <path> status --short` on each `autonomous_child` member, and either print
`Workspace clean -- N members checked` (proceed) or a per-repo dirty-status table asking the user
to commit/stash first. Never auto-commits or writes. `--skip-member-clean-check` bypasses with a
printed warning. Additive to the Housekeeping Commit Gate. **Full authoritative algorithm: see
`g-go.md` Step 0.**

---

## WPAC inbox Gate (Only When WPAC is configured)

Before any bug claiming or implementation, run the re-callable inbox check if WPAC is configured:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py", ".agent\hooks\g-hk-wpac-inbox-check.py", ".codex\hooks\g-hk-wpac-inbox-check.py", ".opencode\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

WPAC is configured only when `.gald3r/workspace/topology.md` declares at least one
parent/child/sibling relationship. A Workspace-Control manifest and local `INBOX.md` alone are
not sufficient. If the check reports `INBOX CONFLICT GATE` or exits code `2`, stop and run
`@g-wpac-read`. If WPAC is not configured, skip and report `WPAC: not configured / skipped`.

---

## Gald3r Housekeeping Commit Gate (T531)

After the WPAC gate passes and before the Clean Controller Gate:

```powershell
.\scripts\gald3r_housekeeping_commit.py -Mode preflight -Apply -Json
```

- `clean` → continue
- `safe-gald3r-housekeeping` → helper auto-commits safe `.gald3r/` paths, continue
- `unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` → HARD STOP with exact paths

Re-run with `-Mode post-write -Apply` after each coordinator-owned shared `.gald3r` write.

---

## Clean Controller Gate

Run `git status --short` at the orchestration git root. If anything is listed outside this
run's explicit staging allowlist, STOP. Do not claim bugs or create worktrees until unrelated
changes are committed or stashed.

---

## Phase 1: Bug-Fix Implementation

For each target bug in order (critical → high → medium → low):

### 1. Claim the Bug

Mark the bug `[🔄]` / `status: in-progress` in both BUGS.md and the bug file. Append:
```
| YYYY-MM-DD | open | in-progress | Claimed for fix — g-go-bugs Phase 1 |
```

Create or reuse a coding worktree:
```powershell
.\scripts\gald3r_worktree.py -Action Create -BugId {bug_id} -Role code -Owner {platform_or_agent_slug} -Json
```

### 2. Read the Bug Spec

Read `.gald3r/bugs/open/bugNNN_{slug}.md` (use discovery pattern `Get-ChildItem .gald3r/bugs -Recurse -Filter "bug*.md"`). Note:
- Reproduction steps
- Expected vs actual behavior
- Linked fix task (if `fix_task_id:` populated by T1114 auto-bridge)
- Subsystems affected

### 3. Reproduce

Run the failing test or manually verify the symptom exists at current HEAD.

- **Reproduced** → proceed to Fix
- **Cannot reproduce at HEAD** → skip with note; mark `[⚪]` / `status: cannot-reproduce`; append Status History: `| YYYY-MM-DD | in-progress | open | Cannot reproduce at HEAD — skipped |`; do NOT attempt fix

### 4. Fix

Implement the minimal fix. No scope creep beyond resolving the described symptom.

Apply workspace routing check: run `g-skl-workspace` ENFORCE_SCOPE before editing files.

**AC gate** — before proceeding:
- Does the fix resolve the described symptom? → proceed
- Unresolved → return to Fix
- **Bug-discovery check**: pre-existing bugs found during fix → BUG entry + comment (g-rl-35)
- **Constraint check**: any CONSTRAINTS.md violation blocks `[🔍]`

### 5. Regression Test

Add or update a test that would have caught this bug. Acceptable forms:
- A new test case in an existing test file
- A new test file if no suitable one exists
- A documented manual test script if automated testing is not applicable to this subsystem

The regression test MUST fail before the fix and pass after it.

### 6. Mark Awaiting Review

In both BUGS.md and the bug file:
- Change indicator to `[🔍]` / `status: awaiting-fix-review`
- Append Status History: `| YYYY-MM-DD | in-progress | awaiting-fix-review | Fix implemented + regression test added |`

Create a checkpoint commit:
```
fix({subsystem}): BUG-{id} — {brief description}

Bug: BUG-{id}
Root cause: {one line}
Regression test: {test file/name}
```

---

## Phase 1 Completion

After all target bugs processed:

```
[g-go-bugs] Phase 1 complete
  Fixed → [🔍]: BUG-{ids}
  Checkpoint → {branch}@{commit_sha}
  Skipped/Blocked: {list with reasons}
```

If zero bugs reached `[🔍]` → skip Phase 2:
```
[g-go-bugs] Phase 1 completed 0 bugs — Phase 2 skipped.
```

---

## Phase 2: Adversarial Review (independent agent)

> **Only runs if Phase 1 marked at least 1 bug `[🔍]`.**

The Phase 2 reviewer is a fresh Task subagent with no Phase 1 context. It verifies the fix
against the checkpoint commit independently.

### Spawn

```
[g-go-bugs] Spawning Phase 2 reviewer for: Bug {bug IDs}
[g-go-bugs] Reviewer is a fresh agent — no Phase 1 context. Adversarial independence: ✓
```

Spawn a Task subagent with:
- The bug IDs being reviewed
- Coordinator-managed override: "Return PASS/FAIL payloads and Status History rows only. Do not write BUGS.md or bug files; the coordinator owns all writes."
- No Phase 1 context

### Reviewer Protocol

The reviewer, for each `[🔍]` bug:

1. **Claims** bug as `[🕵️]` / `verification-in-progress` before inspection
2. **Creates review worktree** from the Phase 1 checkpoint (T170 `review` worktree)
3. **Verifies**:
   - Re-runs the reproduction steps → confirms fix resolves the symptom
   - Runs regression test → must pass
   - Runs full test suite (if available) → no new failures introduced
4. **PASS** → returns PASS payload + verification note
5. **FAIL** → returns FAIL payload + Status History row; triggers stuck-loop check (≥3 FAILs → `[🚨]`)

Reviewer does NOT write BUGS.md or bug files — returns result payload to coordinator.

### Coordinator Finalizes

After reviewer completes:
1. Batch-update `BUGS.md` (PASS → `[✅]` Resolved; FAIL → `[🟠]`/`[🔴]` back to Open)
2. Batch-update bug files (PASS → `status: resolved`, `resolved_date`; FAIL → `status: open`)
3. Update linked fix task (if any) via `fix_task_id` frontmatter: PASS → `[✅]`; FAIL → `[📋]`
4. Create review-result commit with explicit path staging
5. Write Pipeline Session Summary (see format below)

---

## Follow-Up Task Filing Gate (MANDATORY — before Pipeline Session Summary)

Before writing the summary, handle all follow-up items surfaced during the run:

1. Identify ALL follow-up items (deferred sub-features, gaps, adjacent bugs found)
2. For each, call `g-skl-tasks CREATE TASK` — capture the returned `task_id`
3. Reference actual task IDs in the summary — NEVER slug-only names

---

## Pipeline Session Summary

```markdown
## g-go-bugs Session Summary

Run: g-go-bugs {args}
Bugs attempted: N

- ✅ BUG-{id}: {title} — fixed + verified (regression test: {test name})
- ❌ BUG-{id}: {title} — fix failed: {reason}
- ⏸️ BUG-{id}: {title} — could not reproduce at HEAD, skipped
- ⏭️ BUG-{id}: {title} — skipped: {reason}

### Follow-Up Tasks Filed
- T{id}: {title} — {reason surfaced}
(or: None)

### Final State
- ✅ Resolved: {N}
- 📋 Failed (back to open): {M}
- ⏸️ Skipped: {K}
- Total commits this run: {C}
```

---

## --dry-run Mode

When `--dry-run` is passed, the coordinator reports what WOULD be fixed without making any changes:

```markdown
## g-go-bugs Dry Run

Target bugs (in fix order):
1. [🔴] BUG-{id}: {title} (critical) — linked fix task: T{id} / no fix task yet
2. [🟠] BUG-{id}: {title} (high) — linked fix task: T{id}
3. [🟡] BUG-{id}: {title} (medium) — no fix task
...

Skipped:
- [🚨] BUG-{id}: {title} — requires user attention
- [🕵️] BUG-{id}: {title} — verifier claim active until {expiry}

Total runnable: N
```

No files are written in dry-run mode.

---

## Spawned-agent task/bug creation (T585 AC3)

During this run, **any** task or bug a spawned agent needs to create (deferred sub-feature,
newly discovered bug, follow-up) goes into the **hot inbox**, never a direct `tasks/open/` /
`bugs/open/` write + index regeneration:

- **Preferred** — call the engine verb (`gald3r task create …` / `gald3r bug report …`, or the
  `gald3r_task_*` / `gald3r_bug_*` MCP tools). When the run marker
  (`.gald3r/logs/ggo_run_state.json` `active: true`, or `GALD3R_AGENT_RUN=1`) is set, the engine
  **auto-routes** the new item to `tasks/inbox/` / `bugs/inbox/` as an id-less, uuid-suffixed
  draft — no id is assigned at create time.
- **Manual fallback** (no engine) — hand-write the draft directly into `tasks/inbox/` /
  `bugs/inbox/` (id-less, uuid-suffixed filename). Do **not** write `tasks/open/` / `bugs/open/`
  or touch `TASKS.md` / `BUGS.md`.

The hot-inbox **intake** (run at each iteration boundary — see the inbox-intake step) is the
*single ID-assigning authority*: it assigns ids atomically, so N concurrent agents can never
collide on the next id. This is the spawn-side complement of that intake step.

## Behavioral Rules

| Rule | Why |
|------|-----|
| Cannot-reproduce → skip, not fail | Flaky reproduction wastes cycles — log and move on |
| Regression test REQUIRED per fix | Prevents recurrence; closes the test-coverage gap |
| Phase 1 never marks `[✅]` — only `[🔍]` | Phase 2 reviewer owns `[✅]` |
| Phase 2 reviewer has NO Phase 1 context | Adversarial independence guarantee |
| `[🚨]` bugs are NEVER auto-retried | Human-only resolution (T047) |
| Coordinator batch-writes BUGS.md after Phase 2 | Prevents concurrent line-edit conflicts |
| Fix task updated on PASS/FAIL (via `fix_task_id`) | T1114 auto-bridge loop closure |
| NEVER ask questions mid-run | Fire-and-forget design |

---

## Examples

```
@g-go-bugs                          # fix all open bugs
@g-go-bugs severity:critical,high   # blitz critical + high only
@g-go-bugs bug:BUG-042              # fix one specific bug
@g-go-bugs --dry-run                # preview fix queue
```

**For parallel execution** (faster on large bug queues):
```
@g-go-bugs-swarm
@g-go-bugs-swarm severity:critical
```

Let's fix some bugs.
