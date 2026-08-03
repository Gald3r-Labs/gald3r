---
description: 'Verify tasks/bugs awaiting review in a fresh session: PASS/FAIL scoring, no self-review, auto-commits verdict.'
argument-hint: '[tasks <id...>] [--swarm] [--provider <id>[:<model>]] [--model <id>] [--reviewer-provider <id>] [--reviewer-model <id>]'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: orchestration
---
Verification-only backlog review: $ARGUMENTS

## Mode: REVIEW ONLY

> ⚠️  **Run this in a NEW agent session** — different window, different invocation.
> If you implemented any of these tasks in this session, **skip them** (leave `[🔍]`).
> Self-review defeats the purpose of this gate.

> **Scope is set by the coordinator, not here.** Workspace scope (`--local` / `--workspace <id>`
> / `--workspace` / the `g_go_default_scope` config default) is resolved by the `g-go` /
> `g-go-swarm` coordinator at its Auto-Plan Step 1a and handed down as the already-filtered review
> queue (or explicit task IDs). When `g-go-review` is invoked directly with explicit task IDs, it
> reviews exactly those `[🔍]` IDs. When invoked directly with no IDs, treat the scope as
> **local-only** — `g-go-review` does not re-evaluate `g_go_default_scope`; let `g-go` own the
> controller-default workspace_all expansion.

## Provider & Model Selection (T580, BUG-612 companion)

`$ARGUMENTS` MAY carry an explicit `--provider <provider>[:<model>]` and/or `--model <model>`
(global) plus `--reviewer-provider`/`--reviewer-model` (role-explicit — identical to the global
form here since this command's only role IS the reviewer). Resolution order: role-specific /
global CLI override > invoking host/parent-model mapping (a detected Cursor host maps to
`cursor-agent` + `gpt-5.6-terra-medium` by default; Claude Code / unknown hosts stay `claude`) >
task `preferred_model:` > session default — see `g-go-go.md`'s "Provider & Model Routing"
section for the full precedence/host-mapping table `gald3r autopilot loop` implements in code
(`agent_role_routing.resolve_agent_target("reviewer", ...)`). **Independence is unaffected by
provider/model choice** — a reviewer resolved to a different provider or model than the
implementer still runs in a fresh session with no Phase 1 context; provider/model selection and
review independence are orthogonal concerns and this command enforces both regardless of which
provider was used to implement the work under review.

---


### Step 0 — Workspace Member Clean-Status Preflight (T1431)

Before the WPAC gate / review-queue build / claim / review-worktree creation, run the **read-only**
workspace member clean-status preflight: scan `.gald3r/linking/workspace_manifest.yaml`, run
`git -C <path> status --short` on each `autonomous_child` member, and either print
`Workspace clean -- N members checked` (proceed) or a per-repo dirty-status table asking the user
to commit/stash first. Never auto-commits or writes. `--skip-member-clean-check` bypasses with a
printed warning. Additive to the Housekeeping Commit Gate. **Full authoritative algorithm: see
`g-go.md` Step 0.**

---

### Step 0b — CLI Invocation Rule: `uv run gald3r` (BUG-591)

Every `gald3r <verb>` call in this run (`gald3r housekeep`, `gald3r task`/`gald3r bug` verdict
verbs, `gald3r worktree create` for a review-swarm bucket, `gald3r search`, etc.) MUST run as
**`uv run gald3r <verb>`**, never bare `gald3r`, whenever cwd is a dev checkout of `gald3r_core`.
A bare call can resolve to a stale PATH binary that silently shadows this checkout's dev source
(BUG-591) — including a reviewer's own PASS/FAIL status-write landing in the wrong `.gald3r/`
across a worktree boundary. **Full text, rationale, and the optional machine-actionable staleness
hard-fail check: see `g-go.md` Step 0b.**

---

### WPAC inbox Gate (Only When WPAC is configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a WPAC participant. WPAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a WPAC group member.

If WPAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py", ".agent\hooks\g-hk-wpac-inbox-check.py", ".codex\hooks\g-hk-wpac-inbox-check.py", ".opencode\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { python $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-wpac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If WPAC is not configured, skip this gate and report `WPAC: not configured / skipped`.


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

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/wpac_auto_actions.log, linking/sent_orders/, linking/INBOX.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the WPAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `<gald3r_source>`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r worktree create -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/linking/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

4. **Touch-set expansion (v2 — optional signals)** — Union extra repository roots into the same per-root checks (still **not** a blanket scan of every manifest member):
   - **`extended_touch_repos:`** — optional task/bug YAML list of additional manifest `repository.id` values beyond `workspace_repos`.
   - **`touch_repos:` (swarm handoffs)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
   - **Subsystem `locations:` absolutes** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested strings). For values matching a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` elsewhere), if the path exists, resolve `git -C <dir> rev-parse --show-toplevel` (use the file's parent directory when the path is a file). Each distinct root **other than** the orchestration root joins the touch set. Relative paths do not expand the set.

### Pre-Reconciliation Clean Gate (before coordinator shared writes)

Also re-run the **Gald3r Housekeeping Commit Gate** with `-Mode post-write -Apply` against the orchestration root immediately after each coordinator-owned shared `.gald3r` write so safe controller coordination state lands in a focused `chore(gald3r): commit g-go coordination state` commit before the next major phase begins.


Immediately before the coordinator merges bucket results into the primary checkout, updates shared `.gald3r` indexes or task/bug files as coordinator-owned writes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits: **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (steps 1 + 3 + 4). For `--swarm` runs, if unrelated dirty paths appear in **any** of those roots during parallel bucket work, **fail closed** — do not apply those shared writes; keep patches, artifacts, and evidence; report **per-root** blockers using the same blocker family as checkpoint and review-result commits.

## Execution Protocol

### 0. Branch Pre-Flight (BUG-095 fix, T1374)

**Run before any task scanning or review work.**

1. Read `implementation_branch` from all `[🔍]` task files in `tasks/verification/` (or wherever TASKS.md points).
2. Collect unique non-empty `implementation_branch` values.

**Case A — all tasks share one branch, it differs from current branch:**
```powershell
# Preferred: create a review worktree from the implementation branch (T207 policy)
gald3r worktree create -Branch <implementation_branch> -Role review
# Fallback if worktree helper unavailable:
git checkout <implementation_branch>
```
Log: `🔀 Branch pre-flight: switched to implementation branch (<branch> / <sha[:8]>)`

**Case B — already on the correct branch:**
Log: `✅ Branch pre-flight: already on implementation branch (<branch>)` — continue.

**Case C — `implementation_branch` absent on ALL tasks (legacy, no field):**
Log: `⚠️ Branch pre-flight: no implementation_branch field on tasks — legacy fallback, reviewing on current branch (<branch>)`  — continue.

**Case D — tasks have MIXED `implementation_branch` values:**
```
⛔ Branch pre-flight: multiple implementation branches in review queue:
   - T-NNN: <branch1>
   - T-MMM: <branch2>
Scope your g-go-review to one branch at a time. Run:
  git checkout <branch> && g-go-review --tasks T-NNN,...
```
**STOP — do not proceed.**

**Swarm mode:** The coordinator runs this pre-flight before partitioning buckets. All buckets inherit the resolved `implementation_branch`.

---

### 1. Load Context

Read in this order:
- `.gald3r/TASKS.md` — identify all `[🔍]` (Awaiting Review) tasks and skip non-expired `[🕵️]` verification claims
- `.gald3r/BUGS.md` — identify all bugs with `[🔍]` status in the index table and skip non-expired `[🕵️]` verification claims
- Individual task files for each `[🔍]` task item — **read `## Handoff Report` first** (Files Changed, Commands Run, Issues Discovered, Left Undone, Procedure Compliance), then read acceptance criteria. The Handoff Report is the primary review context; use it to focus verification on changed files and discovered issues.
- Individual bug files (`.gald3r/bugs/bug*.md`) for each `[🔍]` bug — read fix description and affected file/line
- `git log --oneline -10` — understand what was recently implemented
- `.gald3r/CONSTRAINTS.md` — guardrails
- **Active workflow profile (T1239)** — load once via `gald3r project-type resolve` (active
  skill folder; see g-skl-tasks "Reading the active profile"). The review-gate
  status (the `[🔍]`-equivalent), the PASS target, and the FAIL target come from
  the profile's `review_gate` + `task_statuses[]` rather than hardcoded strings
  (AC1). For `software_dev` these resolve to `awaiting-verification` → PASS `done`
  / FAIL `pending` exactly as before; a `content_creation` project reviews
  `in_review` → PASS `rendering`/`published` per its DAG order. Absent
  `.gald3r/config/workflow_profiles/` → built-in `software_dev` lifecycle.

> If a task has no `## Handoff Report` section, note "No Handoff Report" in your review summary and proceed to read the implementation files listed in acceptance criteria directly.

> **Codebase search (g-rl-43 / BUG-519)**: for any codebase content search, prefer
> `gald3r search <pattern> [--path DIR]`; it is **mandatory**, not just preferred, whenever
> a search must see inside `.gald3r/` or `.gald3r_sys/` — the harness/ripgrep `Grep` tool is
> gitignore-aware and silently misses gitignored trees like `.gald3r_sys/` on broad searches.

### 2. Build the Review Queue

Collect all reviewable items — both tasks **and bugs**:
- **Tasks**: all `[🔍]` entries in `TASKS.md`
- **Bugs**: all bugs in `BUGS.md` with `[🔍]` in the status column + verify `status: awaiting-verification` in the individual `bugs/bug*.md` file
- **Skip active claims**: any `[🕵️]` item with a future `verifier_claim_expires_at`
- **Take over stale claims**: include `[🕵️]` items with expired or missing `verifier_claim_expires_at`; append a Status History takeover row and reclaim before review

If `$ARGUMENTS` specifies IDs (e.g. `@g-go-review tasks 14 15` or `@g-go-review bugs BUG-013`), review only those.

**Skip any item you implemented in this session.** Leave it `[🔍]` for a future agent.

Display the queue before reviewing:
```
Review Queue:
  T-014 [🔍] Fix vault path resolution (task)
  T-017 [🔍] Platform parity sync (task)
  BUG-013 [🔍] Null guard on user.profile (bug)
```

### 2a. Claim Review Items

Before inspecting implementation details, claim each selected item:

1. Change the task/bug status from `[🔍]` / `awaiting-verification` to `[🕵️]` / `verification-in-progress`.
2. Add or replace verifier claim metadata:
   ```yaml
   verifier_owner: "{platform_or_agent_slug}"
   verifier_claimed_at: "{ISO-8601 timestamp}"
   verifier_claim_expires_at: "{ISO-8601 timestamp}"  # default 120 minutes
   ```
   **Resolving `{platform_or_agent_slug}` (T580/BUG-612):** this is a recorded audit field, not a
   CLI flag with an auto-default, so it must be filled in explicitly. Read
   `$env:GALD3R_GGO_REVIEWER_PROVIDER` (PowerShell) / `$GALD3R_GGO_REVIEWER_PROVIDER` (bash) — the
   actually-resolved reviewer provider T580's role routing exports whenever it differs from the
   Claude default (Cursor host mapping, an explicit `--reviewer-provider`/`--provider` override,
   ...). If that variable is unset or empty, use your own real host identity (`claude`,
   `cursor-agent`, ...) — never a bare literal guess independent of what actually launched you.
3. Append Status History: `awaiting-verification -> verification-in-progress`.
4. If reclaiming a stale `[🕵️]` item, the Status History message must name the previous `verifier_owner` and claim expiry.
5. Never review an item currently claimed by a different non-expired verifier.

### 2b. Establish Review Isolation

After claiming and before inspecting implementation details, isolate the review source.

**Default: review worktree from checkpoint commit.** Use the shared T170 helper when the review source is branch-addressable. Normal `g-go-code` / `g-go --swarm` handoff provides a code-complete checkpoint branch and commit SHA; prefer that source over dirty snapshot inspection.

```powershell
gald3r worktree create -TaskId {id_or_bucket} -Role review -BaseBranch {review_source_branch_or_HEAD} -Json
```

Owner is auto-resolved (T580/BUG-612): omitting `-Owner` lets the helper pick up your ACTUALLY
resolved reviewer provider (`GALD3R_GGO_REVIEWER_PROVIDER`) before falling back to the pre-T580
`USERNAME`/`USER`/`agent` default — same mechanism as `g-go-code.md` Step 3. Pass `-Owner <value>`
explicitly only to override it.

Before using worktree mode, prove the candidate changes are reachable from `review_source_branch_or_HEAD`:
- If the implementation has a checkpoint commit, record that branch/commit as the review source and create the review worktree from it.
- If `git diff --quiet` is false for the candidate checkout, or required changed paths are not present in the candidate branch, do **not** create a `-BaseBranch HEAD` review worktree. Use snapshot mode instead.
- A review worktree must never inspect a stale clean `HEAD` when the actual candidate exists only as dirty files in another checkout.

Record the helper output in task/bug metadata:

```yaml
review_isolation_mode: worktree
review_worktree_path: "{worktree_path}"
review_worktree_branch: "{worktree_branch}"
review_worktree_owner: "{owner}"
review_worktree_created_at: "{created_at}"
review_source_branch: "{base_branch}"
review_source_commit: "{git rev-parse base_branch}"
```

**Shared-sandbox mode (T1118).** When the `g-go` coordinator hands off `shared_sandbox: true` and a `shared_worktree_path` (the `--shared-sandbox` flow), do **NOT** create a separate `review` worktree. Reuse the named Phase 1 `code` worktree read-only — the Phase 1 checkpoint commits and installed dependencies are already present there, so the reviewer sees the same git/filesystem state without re-cloning. Record:

```yaml
review_isolation_mode: shared-worktree
review_worktree_path: "{shared_worktree_path}"
review_source_branch: "{implementation_branch}"
review_source_commit: "{git rev-parse implementation_branch}"
```

Shared-worktree mode is read-only for the reviewer (same boundary as snapshot mode): inspect files under `shared_worktree_path`, but never modify implementation files there unless the user explicitly requests fix-forward review, in which case the coordinator reconciles the changes. The independence guarantee is unaffected — the reviewer is still a fresh agent with no Phase 1 reasoning context; only the worktree filesystem is shared. This mode applies only when the coordinator passes the shared-sandbox handoff; without it, use the default worktree-from-checkpoint or snapshot fallback below.

**Snapshot mode fallback.** Use snapshot mode instead of creating a review worktree only when the candidate changes are explicitly left uncommitted, dirty, or non-branch-addressable. Record:

```yaml
review_isolation_mode: snapshot
review_snapshot_path: "{absolute checkout/worktree path inspected read-only}"
review_source_branch: "{git branch --show-current}"
review_source_commit: "{git rev-parse HEAD}"
review_source_dirty: true
```

Snapshot mode is read-only. The reviewer may inspect files in the source checkout, but must not modify implementation files there.

If the handoff names a checkpoint commit, do not use snapshot mode unless the checkpoint is missing required changed paths or the user explicitly asks to review dirty state.

**Active implementation worktree conflicts.** If an item still has a non-expired implementation claim or active implementation worktree metadata, do not create a review worktree from it and do not mutate it. Skip the item unless the implementation status is `[🔍]` / awaiting-verification or the handoff explicitly names that worktree as the read-only snapshot source.

**Fix-forward boundary.** Review is read-only by default. If the user explicitly requests fix-forward review, the reviewer may write fixes only inside its own `review` worktree, must return a patch/result payload, and the coordinator must reconcile those changes explicitly. Never edit an implementation worktree or the primary checkout directly during review.

### 2b-i. Verify Worktree Base Commit — MANDATORY (BUG-620)

**Before trusting ANY code read from `review_worktree_path` (or `shared_worktree_path`)**, the
reviewer MUST independently confirm the worktree is actually checked out at, or ahead of, the
stated checkpoint commit. This applies regardless of how the worktree was provisioned — the T170
`gald3r worktree create` helper documented above, or an Agent tool's own `isolation: 'worktree'`
param when the reviewer itself is spawned as a subagent. BUG-620 confirmed, independently, via 3
of 4 fresh reviewers in one review-swarm iteration, that a worktree can be silently pinned at a
commit dozens of commits behind the actual checkpoint SHA under review — with every fix commit
under review literally absent from the checked-out files. Trusting the checkout at face value
risks a false RESOLVE (reviewing stale, already-superseded code that happens to still pass) or a
false REOPEN (missing a real fix present only at the true tip). It self-corrected by luck in that
incident, not by design — this step makes the check mandatory instead of incidental.

Run, in the worktree directory, **before reading or evaluating any file inside it**:

```powershell
git -C {review_worktree_path} rev-parse HEAD
git -C {review_worktree_path} merge-base --is-ancestor {review_source_commit} HEAD
```

- `merge-base --is-ancestor` exits `0` when `HEAD` equals or descends from `review_source_commit`
  (the stated checkpoint SHA) → **verification PASSES**, proceed normally.
- A non-zero exit (or `HEAD` not resolving at all) → the worktree's `HEAD` is stale, diverged, or
  otherwise does not contain the checkpoint commit → **verification FAILS**. Do **not** proceed to
  read or evaluate code from this worktree yet.

**On verification failure, self-correct BEFORE proceeding** — never silently review whatever
happens to be checked out. Pick whichever is fastest and safest for the situation:
- Re-fetch and re-checkout the worktree against the stated checkpoint SHA/branch (`git -C
  {review_worktree_path} fetch`, then `git -C {review_worktree_path} checkout
  {review_source_commit}`), or re-run the T170 `gald3r worktree create` helper to reprovision it.
- Overlay just the files needed via `git -C {review_worktree_path} show
  {review_source_commit}:{path}`, reading the correct commit's content directly rather than
  trusting the rest of the stale checkout.
- A documented fast-forward-only merge into the worktree branch (`git -C {review_worktree_path}
  merge --ff-only {review_source_commit}`), review the now-current files, then revert that merge
  once the review read is complete so the worktree is left as found.

**Report the mismatch — mandatory when verification failed.** The review report / Review Note
MUST explicitly state that a base-commit mismatch was detected and how it was self-corrected, e.g.:
`BASE-COMMIT MISMATCH: worktree HEAD was {stale_sha} (worktree not an ancestor of
{review_source_commit}); re-fetched and re-checked-out before review.` This is required even when
the self-correction fully resolved the issue — the coordinator/user needs to know staleness
occurred, since the underlying worktree-provisioning defect is a separate, out-of-band concern
(likely the Agent tool's own `isolation: 'worktree'` behavior, outside this repo's fix surface)
that this check exists to catch, not to silently paper over.

Applies to `review_isolation_mode: worktree` and `review_isolation_mode: shared-worktree`. Not
required for `review_isolation_mode: snapshot`, since snapshot mode reads `review_source_commit`
directly via `git rev-parse HEAD` in the actual checkout at read time — there is no separately
provisioned worktree to drift from what was stated.

**Standalone vs coordinator-managed writes.**
- Standalone `@g-go-review` records the claimed item's verdict via the verify verb (`gald3r task verify` / `gald3r bug resolve` / `gald3r bug update` — see the Verification Verb Gate in step 3/§"Verification Verb Gate" below, never a hand-edit of the task/bug file or index), then creates the review-result commit after those writes.
- When spawned by `g-go` Phase 2 or `g-go-review --swarm`, reviewers run in coordinator-managed mode: return PASS/FAIL payloads, Status History rows, evidence, and authorized fix-forward patches only. The coordinator owns all task/bug file, `TASKS.md`, `BUGS.md`, changelog/docs, generated prompt, parity sync, final staging, and review-result commit writes.

### 2c. Compute Review Depth (Ladder Level) — T539 throughput-20/hr program

**Before inspecting implementation details** (immediately after establishing review isolation at 2b), compute a **ladder level** for each claimed item. This is the mechanism that lets Step 3 below scale review depth to actual risk instead of applying the same full adversarial pass to every item — the single biggest lever in the owner's 20-verified-items/hour throughput target (2026-07-30, T537-T539).

Run, against the review source resolved at 2b (`review_source_commit` / `review_worktree_path` / `review_snapshot_path`):

```powershell
gald3r task review-depth {id} --diff-range "$(git merge-base main {review_source_commit})..{review_source_commit}" --json
```

For bugs, the same verb exists on the `bug` side:

```powershell
gald3r bug review-depth {id} --diff-range "$(git merge-base main {review_source_commit})..{review_source_commit}" --json
```

(Substitute the actual merge-base against whatever the project's trunk branch is when not `main`. Read-only — this never writes anything; it is safe to run before or after the `[🔍] -> [🕵️]` claim.)

The call returns a JSON payload with `level` (`"minimal"` / `"standard"` / `"thorough"` — see `g-skl-verify-ladder`'s existing level vocabulary; this reuses it, not a new scale), `blast_radius` (`"low"` / `"medium"` / `"high"`), `score`, and `reasons` (a human-readable trail of which score components fired — files touched, subsystem criticality, severity/value score, test delta). Record `review_ladder_level`, `review_ladder_score`, and the `reasons` list for this item; Step 3 below and the verify-verb call both read them.

**Owner safety valve.** The command already applies `review_min_level:` from `.gald3r/config/AGENT_CONFIG.md` (or an explicit `--level` override) as a **floor** — it can only raise the effective level, never lower it. If `review_min_level: thorough` is set, every item resolves to `thorough` regardless of its computed score; this is the sanctioned way to force the whole queue back to today's full-depth behavior without touching any code. `floored: true` / `floor_level` in the JSON payload tell you when this happened — mention it in the per-item review note when it did.

**This is a floor on SPEED, never a ceiling on JUDGMENT.** A reviewer who notices something suspicious at `minimal` or `standard` depth — an AC that doesn't obviously hold, a diff that looks bigger than the numstat implies, a security-sensitive pattern the scorer didn't recognize — MUST escalate that item to `thorough` treatment before recording a verdict. The computed level sets the DEFAULT depth; it never overrides reviewer judgment that more scrutiny is warranted.

### 3. Review Each Item

#### 3A. Review Each Task

For each `[🕵️]` task claimed by this verifier:

**Review depth by ladder level (T539)** — branch on the `review_ladder_level` computed at Step 2c before running (a)-(g) below:

| Level | Run | Skip |
|-------|-----|------|
| `minimal` | (a) read AC, abbreviated (b) — confirm each criterion against a quick read of the diff (not a full re-derivation), confirm lint/tests-green from the Handoff Report or a single listed `verification_commands` run, (c), (d) for anything obviously encountered, (e), (f), (g) | b2, b3, Step S, Step E, Step U |
| `standard` | (a), full per-criterion (b), b2 (workspace boundary — cheap, always run), b3 inline OWASP/STRIDE pass (only when the diff already meets its own web/API/auth/data/integration trigger), (c), (d), (e), (f), (g) | Step S two-phase adversarial scan, Step U (unless an AC explicitly requires a live UI-test gate) |
| `thorough` | Everything — (a) through (g), b2, b3, Step S, Step E, Step U, exactly as documented below (today's default, unchanged) | nothing |

**This table sets the DEFAULT depth only — it is a floor on speed, never a ceiling on judgment** (see Step 2c). Any FAIL, any Critical/High security finding, or reviewer judgment that an item needs deeper scrutiny than its computed level provides ESCALATES that item to `thorough` treatment before recording a verdict, regardless of what Step 2c computed. When you escalate, note why in the review note (`escalated {level} -> thorough: {reason}`).

**a) Read task spec** — list all acceptance criteria
**b) Check each criterion against actual files/code**
  - If `review_isolation_mode: worktree`, inspect files under `review_worktree_path`.
  - If `review_isolation_mode: snapshot`, inspect files under `review_snapshot_path` read-only.
**b2) Workspace boundary check** — run `g-skl-workspace` ENFORCE_SCOPE against changed paths and the task/bug routing metadata; unknown manifest repo IDs, undeclared member writes, docs-only source changes, or member writes without manifest permission fail the item.
**b3) Security pass (inline OWASP/STRIDE)** — for tasks that touch web/API/auth/data/integration code, apply the OWASP Top 10 checklist from `g-skl-code-review` Step 2 to changed files. For tasks adding new services, cross-process boundaries, or significant architectural changes, apply STRIDE. Security findings are rated **Critical / High / Medium / Low**. Report each finding with OWASP/STRIDE category, file:line, and recommended fix. Code annotated with `# nosec: <justification>` or `# security-exempt: <reason>` is waived. Any Critical or High finding → flag as unmet criterion (FAIL). (T539: SKIPPED entirely at `minimal` ladder level — see the Review-depth-by-level table above. Note a critical/security-critical subsystem match already forces `thorough` at Step 2c, so this skip only ever applies to genuinely low-blast-radius, non-critical-subsystem items.)

**Step S — Two-phase security scan (T1167)** — runs **after** b3 inline security pass and **before** the `[🔍] → [✅]` write at step (e). Invokes `g-skl-security-scan` in **Two-Phase Mode** when the candidate review source has any changed files outside of `*.md` / `docs/**` / `CHANGELOG.md` / `README.md` / `LICENSE`. **T539 gate**: only runs at `thorough` ladder level — at `minimal`/`standard`, mark Step S `SKIPPED — ladder level {level} (T539)` in the review note and continue to (c) without invoking the two-phase scan.

  1. **Eligibility** — list changed files via `git diff HEAD~1..HEAD --name-only` against the candidate review source (worktree branch/SHA established in Step 2b, or snapshot path). If all changed paths match the doc-only allowlist, mark Step S as `SKIPPED` and continue to (c).
  2. **Invocation** — call `@g-skl-security-scan` with the active task ID and review isolation mode passed through. The skill writes `.gald3r/reports/security/threat_model.md` (Phase 1) and `.gald3r/reports/security/security_report_YYYYMMDD_HHMMSS.md` (Phase 2).
  3. **Gate verdict** — the skill returns one of:
     - `verdict: PASS` (no Critical/High findings, or all High findings carry justified `# nosec:` waivers) → record paths in the review note; continue to (c).
     - `verdict: BLOCK` (any unwaived Critical or High finding) → treat each blocking finding as an unmet criterion. For the FAIL handling in step (e):
       - Append the security report path to the task's `## Review Note` section.
       - The Status History FAIL row message must name the blocking findings (e.g., `FAIL: Step S — [HIGH-001] SQL injection in api/users.py:87 (see security_report_20260514_213045.md)`).
     - `verdict: SKIPPED` (doc-only diff, missing diff range, or `requires_security_scan: false` and no non-doc changes) → record skip reason in the review note; continue to (c).
  4. **BUG cross-link** — for each Critical/High finding, `g-skl-security-scan` auto-files a BUG via `g-skl-bugs REPORT BUG` (severity mapped from finding severity). The returned BUG IDs are recorded in the security report and in the review session summary "Found pre-existing bugs" list.
  5. **Waivers** — a High finding is honoured as waived only when its line carries a non-empty `# nosec: <≥4-word justification>` or `# security-exempt: <reason>` annotation. Critical findings are NEVER waivable from inside Step S.
  6. **Doc-only short-circuit** — Step S is intentionally skipped when changed files match `^(\*.md|docs/.*|CHANGELOG\.md|README\.md|LICENSE|\.gitignore)$`. The skip is recorded in the review note as `Step S SKIPPED — doc-only diff`.
  7. **Idempotency** — re-running Step S overwrites `threat_model.md` but never overwrites a timestamped `security_report_*.md`. Multiple runs accumulate; the latest report's verdict is the gate verdict for this review pass.

**Step E — Encoding CI scan (T1448, optional/non-blocking)** — after Step S and before (c), reviewers MAY run the encoding-normalize hook in scan mode as a lightweight CI encoding check over the candidate's changed files. (T539: skipped at `minimal` ladder level along with the other optional deep-checks; still optional/MAY at `standard`/`thorough` as documented below.)

```powershell
# Reports (exit 1) if any changed text file needs encoding normalization; writes nothing.
.claude/hooks/g-hk-encoding-normalize.py -Scan
```

This surfaces stray BOMs / CRLF / UTF-16 drift before they reach the integration branch. It is **advisory by default** — a non-clean scan is recorded in the review note (`Step E: N file(s) need encoding normalization`) and is informational, not an automatic FAIL (the pre-commit hook fixes these on commit). Projects that want it enforced can treat a non-zero scan as a FAIL via `encoding_scan_enforced: true` in `AGENT_CONFIG.md`.

**Step U — UI-Test Verification (Task 190 / BUG-354, optional/opt-in)** — after Step E and before (c), reviewers MAY drive+verify a native desktop app (Throne, or any OS-level UI) end-to-end when the candidate change is UI-affecting (touches the desktop app's UI code, a native dialog, or an AC explicitly calls for visual/interaction verification).

  1. **Eligibility** — this step only applies when the task/bug touches UI-affecting code (`g-skl-computer-use` triggers: desktop UI code paths, native dialogs, screen-driven ACs) **and** the reviewer has a concrete, scripted step list to run (see `g-skl-computer-use` SKILL.md Quick Start). No eligible change → skip silently, no note required.
  2. **Invocation** — build (or reuse) a JSON step list per `g-skl-computer-use`'s declarative step format, then invoke the CLI seam (Task 190 / BUG-354):
     ```powershell
     gald3r ui-test run --steps <path-to-steps.json> --json
     ```
     This shells out to `UITestDriver` / `run_ui_test` (`gald3r_core.tools.computer.ui_test_driver`) without requiring the reviewer to import Python. **Dry-run by default** — records the plan, fires no real input, and reports `status: skipped` for any `verify` step (this is expected and NOT a failure). Live drive additionally requires **both** `--live` on the command **and** the host environment variable `GALD3R_COMPUTER_USE_LIVE=1` — the reviewer only sets these deliberately, on a machine handed over for that purpose (never on a shared/CI host by default).
  3. **Gate verdict**:
     - `status: pass` or `status: skipped` (dry-run, no live host available) → record in the review note as informational; does not affect the PASS/FAIL verdict at (c) unless the task's acceptance criteria explicitly require a live UI verification.
     - `status: fail` (live run only — a scripted step or verify check did not match) → treat as an unmet criterion for any AC that explicitly required UI verification; otherwise record as a note and do not auto-fail unrelated ACs.
  4. **Non-blocking by default** — like Step E, this step is advisory unless the task's acceptance criteria explicitly name a live UI-test gate. Most reviews will see it skipped (no eligible UI change, or no live host configured) — record `Step U SKIPPED — {reason}` in the review note.

**c) Score PASS or FAIL per criterion**
**d) Bug check during review** — if you encounter a bug not covered by the task's ACs:
  - Determine: introduced by this task? → flag as unmet criterion → task FAIL
  - Pre-existing? → log BUG entry via `g-skl-bugs`, add `BUG[BUG-{id}]` comment, note in session summary — does NOT fail this task (see `g-rl-35`)
**e) Overall result:**

**T539 auditability requirement**: every verify-verb call below MUST prefix its `--summary`/`--reason` text with `[ladder:{review_ladder_level} score={review_ladder_score}]` (values from Step 2c). This is what makes the ladder level auditable — a human (or a future agent) reading the task's `## Status History` row can see exactly why this item got a lighter or heavier review, without cross-referencing a separate log. When Step 2c's `floored: true`, also include the floor: `[ladder:{level} score={score} floored-by=review_min_level]`.

  - All criteria PASS → **invoke the verify verb — mandatory, this IS how you record the verdict** (see the Verification Verb Gate below):
    ```
    gald3r task verify {id} --pass --summary "[ladder:{review_ladder_level} score={review_ladder_score}] {brief PASS summary}"
    ```
    This performs the DB-first `completed` transition, moves the task file into `tasks/completed/<YYYY>/<MM>/`, appends the Status History row, and resyncs `TASKS.md` — all in one call. Do **not** hand-edit the task file `status:` field or `TASKS.md`'s indicator directly. Then **run docs check (step 3f)**.
  - Any criterion FAIL → **before recording the verdict**:
    1. **🚨 STUCK LOOP CHECK (pre-check)** — count all existing rows in the task's `## Status History` where the Message column contains `FAIL:`. This determines which path below applies.
    2. **Count < 3 — invoke the verify verb, mandatory:**
       ```
       gald3r task verify {id} --fail --reason "[ladder:{review_ladder_level} score={review_ladder_score}] {AC-NNN, AC-NNN} not met — {brief reason}"
       ```
       This performs the DB-first `pending` transition, appends the `FAIL: {reason}` Status History row, and resyncs the task file + `TASKS.md` — all in one call. Do **not** hand-edit the task file `status:` field or `TASKS.md`'s indicator directly — that bypasses the SQLite DB `gald3r task ready` reads from and leaves the task invisible to future queue scans, silently. **This is the exact failure BUG-511 documented**: a review-result commit asserted a FAIL transition (`[🔍] → [📋]`) that no code path had actually performed, and the task sat `awaiting-verification` in the DB — invisible to `gald3r task ready` — until a human found it by hand.
    3. **Count ≥ 3 — `[🚨]` escalation:** run the same `gald3r task verify {id} --fail --reason "..."` call first (still mandatory — it is the only sanctioned way to record the DB-side FAIL verdict), then separately mark the task `[🚨]` (requires-user-attention) by hand-editing the task file YAML `status:` field and `TASKS.md`'s indicator. (No CLI verb exists yet for this escalation status — that is a known gap, not something to work around by inventing a flag; see this bug's follow-up notes.) Append a `## [🚨] Requires User Attention` block to the task file:
         ```markdown
         ## [🚨] Requires User Attention

         This task has failed review **{N} times**. Automated agents will not retry it.

         **Last failure reason**: {last FAIL row message}

         **Human actions available**:
         - Revise acceptance criteria → add "Human reset: AC revised" to Status History → reset to `[📋]`
         - Split into simpler sub-tasks → mark this `[❌]`
         - Cancel → mark `[❌]` with reason
         - Override as complete → mark `[✅]` with manual sign-off note
         ```
    4. **Clear stale provenance (T1380)** — separately from the verb call, reset `implementation_sha: ''` and `implementation_branch: ''` in the task file YAML frontmatter (the verify verb does not do this). This prevents the next implementer from inheriting a SHA that points at a failed attempt. (PASS path: leave sha/branch unchanged — they are correct provenance for completed work.)
    5. Document specific failure reason in task file (Review Note section) — this is supplementary context; it augments but never replaces the verify-verb call in step 2/3 above.
    - The `--reason` text must name which ACs failed and why. A generic or empty reason is not acceptable.
    - **Agents must NEVER autonomously reset `[🚨]` back to `[📋]` — only a human can do this.**

**f) Docs check** (PASS tasks only — fires at true completion):
  - Does this task add/remove/change user-facing behavior? (skills, commands, agents, hooks, rules, conventions)
  - **YES** → append entry to `CHANGELOG.md` under `[Unreleased]`; update `README.md` if a relevant section exists
  - **NO** (internal refactor, task file edits, bug fixes with no interface change) → skip
  - Refer to `g-rl-26-readme-changelog.mdc` for what qualifies and where to update

**g) Auto-Learn Extraction** (fires after each PASS verdict and docs check; also fires for `[🚨]` items):

1. **Read the task's `## Status History`** and implementation notes from the task file.
2. **Extract**: "What architectural decision, pattern, or warning should the next agent know from this verified task?" Produce 0–3 candidate facts. Skip entirely if nothing meaningful emerges.
3. **Dedup**: read `.gald3r/learned-facts.md`; skip candidates already present (case-insensitive substring match, first 80 chars).
4. **Append** novel facts: `- [YYYY-MM-DD] {fact} (context: T{task_id})` under the most appropriate section heading (`## Architecture & Conventions`, `## Recurring Preferences`, or `## Watch-Outs & Gotchas`). Create section if missing.
5. **Failure trajectory** (fires for `[🚨]` items — 3+ FAIL rows — instead of standard extract):
   - Generate a failure-pattern learning: "T{task_id} reached [🚨] after {N} review attempts. Recurring failure: {brief summary of repeated FAIL reason}."
   - Append under `## Watch-Outs & Gotchas`.
6. **Count and include** in the review session summary: `🧠 {N} new fact(s) learned` (omit if 0).
7. **MCP chain** (when backend available): call `memory_capture_session` with the extracted facts.

> **Skip silently** when `.gald3r/learned-facts.md` does not exist — note as `🧠 learned-facts.md not found — skipped`.

**Per-task output format:**
```
REVIEW: Task 014 — g-go role separation
  ✅ g-go-code.md created in <ECOSYSTEM_ROOT>/<template_full>/.cursor/commands/
  ✅ g-go-review.md created with NEW-SESSION warning
  ❌ g-go.md not updated — self-review banner missing
  → RESULT: FAIL — moved back to [📋] — reason recorded in task file
```

#### 3B. Review Each Bug

For each `[🕵️]` bug claimed by this verifier:

**Review depth by ladder level (T539)** — same `review_ladder_level` computed at Step 2c applies here (via `gald3r bug review-depth`): at `minimal`, (c) Regression check is a quick read of the fix's immediate surrounding lines only; at `standard`/`thorough`, scan the broader call chain as documented below. This is a floor on speed, never a ceiling on judgment — escalate to a full regression scan whenever something looks off, same rule as 3A.

**a) Read bug file** — note: title, affected file/line, fix description in Status History
**b) Verify the fix is present** — check the referenced file/line; confirm the bug no longer exists as described
**c) Regression check** — scan surrounding code for obvious regressions introduced by the fix
**d) Overall result:**
  - Fix confirmed present + no regression → **invoke the verify verb, mandatory** (see the Verification Verb Gate below):
    ```
    gald3r bug resolve {id}
    ```
    This moves the bug to `bugs/completed/`, sets `status: completed`, appends the verification note to Status History, and resyncs `BUGS.md` — do **not** hand-edit the bug file `status:` field or `BUGS.md`'s indicator directly. **T539 auditability**: `bug resolve` has no free-text summary field, so immediately append `[ladder:{review_ladder_level} score={review_ladder_score}]` to the bug file's `## Notes` section as a supplementary edit (same "augments, never replaces the verb call" pattern already used for the task-side Review Note).
  - Fix absent or regression found → **invoke the verify verb, mandatory**:
    ```
    gald3r bug update {id} --status open --note "[ladder:{review_ladder_level} score={review_ladder_score}] FAIL: {specific reason the fix is absent/regressed}"
    ```
    This resyncs the bug file `status:` field, `BUGS.md`'s indicator, and appends the note — do **not** hand-edit `BUGS.md` or the bug file directly. This is the bug-side equivalent of the gap BUG-511 documented for tasks: a commit that only *describes* the reopen, without this call, leaves the bug's status stale wherever anything reads it programmatically.

**Bug verdict format:**
```
REVIEW: BUG-013 — Null guard on user.profile
  ✅ Null check present at src/user.ts:142
  ✅ No regression visible in calling code
  → RESULT: PASS — marked [✅] in BUGS.md
```

```
REVIEW: BUG-007 — Race condition on concurrent writes
  ❌ Fix not found — saveRecord() still has no lock at utils/db.ts:88
  → RESULT: FAIL — moved back to [📋] — reason recorded in bug file
```

### 4. Final Results Table

```
REVIEW RESULTS
──────────────────────────────────────────
Task 014    [✅] PASS — all 6 acceptance criteria met
Task 015    [❌] FAIL — DECISIONS.md missing seed entries (criterion 1)
Task 016    [✅] PASS — BACKPORT_REPORT.md present and complete
BUG-013     [✅] PASS — null guard confirmed at src/user.ts:142
BUG-007     [❌] FAIL — fix absent, race condition still present
──────────────────────────────────────────
Total: 3 PASS / 2 FAIL  (Tasks: 2P/1F  |  Bugs: 1P/1F)
```

### 5. Session Summary

```markdown
## Review Session Summary

### Reviewed PASS → [✅]
- Task #X: {title} — {brief note}
- BUG-NNN: {title} — {brief note}

### Reviewed FAIL → back to [📋]
- Task #Y: {title} — {specific failure reason}
- BUG-NNN: {title} — {specific failure reason}

### Skipped (Implemented This Session)
- Task #Z: left at [🔍] — cannot self-review
- BUG-NNN: left at [🔍] — cannot self-review

### 🧠 Auto-Learn Summary
{N} new fact(s) appended to `.gald3r/learned-facts.md` (or "none / file not found").

### Follow-Up Tasks Filed
- T{id}: {title} — {why surfaced during review}
(none surfaced — or list all filed task IDs with titles. Named-but-not-filed follow-ups are a policy violation.)

### Recommended Next Steps
- Re-implement failed tasks: {list}
- Re-fix failed bugs: {list}
- Hand back to implementing agent if blocking
```

## Behavioral Rules

| Rule | Why |
|------|-----|
| Never implement anything | This is read-only review |
| Never mark `[✅]` for work you coded this session | Defeats independence guarantee |
| Document PASS/FAIL per criterion, not just overall | Gives implementing agent actionable feedback |
| Leave `[🔍]` items you can't review (no context) | Don't guess |
| Be strict — partial implementations fail | A task either meets criteria or it doesn't |


### WPAC inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the WPAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-wpac-read` before continuing.

### Coordinator-Only Shared Writes

In `g-go-review --swarm`, reviewers are evidence producers. They must not write shared ledgers or repository-wide generated surfaces. Return:

- PASS/FAIL payloads and criteria evidence.
- Proposed Status History rows.
- Any bug/task follow-up requests (reviewer identifies; coordinator MUST file them as real tasks).
- Fix-forward patch bundles only when the user explicitly authorized fix-forward review.

The coordinator alone performs `.gald3r` status writes, `TASKS.md`/`BUGS.md` updates, changelog/docs updates, generated prompt regeneration, parity sync, final staging, and review-result commit operations.

**Follow-Up Task Filing Gate (coordinator responsibility)**: After collecting all reviewer follow-up requests, and before writing the final Review Session Summary, the coordinator MUST call `g-skl-tasks CREATE TASK` for each follow-up item. Reference actual task IDs (e.g. `T1110`) in the summary — NEVER slug-style names like `T1043-followup-*`. Named-but-not-filed follow-ups are a policy violation.

### Verification Verb Gate (BUG-511 — MANDATORY before any review-result commit)

**Before creating the review-result commit, you MUST have already invoked the state-transition CLI verb for EVERY item in this review batch:**

- Tasks: `gald3r task verify <id> --pass [--summary "..."]` (PASS) or `gald3r task verify <id> --fail --reason "..."` (FAIL) — see step 3A(e).
- Bugs: `gald3r bug resolve <id>` (PASS) or `gald3r bug update <id> --status open --note "FAIL: ..."` (FAIL) — see step 3B(d).

If you have not run the corresponding verb for every item in this batch, **do that now, before committing**. Writing a Status History row, an Agent Notes entry, or a commit message that *describes* a PASS/FAIL transition is not the same as *performing* it — these CLI verbs are the only path that also writes the SQLite DB row that `gald3r task ready` and other queue queries read from (g-rl-40). Hand-editing the task/bug file `status:` field or the `TASKS.md`/`BUGS.md` indicator directly leaves the DB row stuck at its prior status (e.g. `awaiting-verification`), making the item invisible to future queue scans — silently, with no error — exactly as BUG-511 documented (commit `799cf510` claimed a FAIL transition that no code path actually performed; the task stayed `awaiting-verification` in the DB until a human found it by hand).

**A review-result commit with no corresponding verify call for any item in the batch is a Review Result Commit Gate violation (g-rl-33), not a lesser or partial compliance.** This applies identically in standalone and coordinator-managed (`--swarm`) mode — in swarm mode, the coordinator's "batch-update TASKS.md/BUGS.md" step (Step R7 below) means looping this verb once per item, not hand-editing the index files.

### Review-Result Commit

After PASS or FAIL status writes are complete, create a coordinator-owned review-result commit by default. This applies whether all items PASS, all items FAIL, or the review result is mixed. The commit is the audit point for the review verdict, not an optional follow-up offer.

Required flow:
1. Stage only review-owned paths by explicit allowlist, such as the touched task/bug files, `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, review-owned docs/changelog updates, and regenerated review prompt surfaces.
2. Never use `git add .`; exclude `.gald3r-worktree.json`, terminal transcripts, local logs, unrelated files, and other non-deliverable artifacts.
3. Commit with a message that names the reviewed task/bug IDs and whether the result was PASS, FAIL, or mixed.
4. Include the commit SHA in the final review summary.

Allowed reasons not to create the review-result commit are limited to: unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit. If one of these blockers applies, state the blocker explicitly and leave the review status writes uncommitted for human resolution.

### Optional GitHub PR-Close Hook (T1292)

**Run AFTER the review-result commit — never before.** This hook is triple-gated (same as T1291).

**Triple-gate evaluation (must ALL be true to invoke):**
1. Read `.gald3r/.identity` → `project_type=software_development` (else skip silently)
2. Read `.gald3r/config/AGENT_CONFIG.md` → `github_integration: enabled` (else skip silently)
3. Read `.gald3r/config/AGENT_CONFIG.md` → `github_pr_hooks: enabled` (else skip silently)

**When all three gates pass:** invoke `g-pr-close --task <id>` for each reviewed item.

**PASS path:** PR is merged (default: squash-merge via `gh pr merge --squash`). Append Status History row:
```
| {date} | awaiting-verification | completed | {agent} | PR merged: {pr_url} |
```

**FAIL path:** post a review-failure comment on the PR and leave it as Draft. Append Status History row:
```
| {date} | awaiting-verification | pending | {agent} | PR-close skipped (FAIL): failure comment posted on {pr_url} |
```

**Behavior:**
- A PR-close failure does NOT roll back the recorded PASS/FAIL verdict.
- On error: append a notice to the session summary so the user can retry manually.
- In `--swarm` mode: the coordinator runs this hook in the batch-write pass, after the review-result commit.

**Default state:** all three flags are `disabled` / absent → behavior is byte-identical to pre-T1292.

## Swarm Mode (`--swarm`)

When `$ARGUMENTS` includes `--swarm`, activate the **COORDINATOR PHASE** to parallelize review.
Review is read-only — partitioning is simpler than `g-go-code --swarm` (no subsystem conflicts).

### Coordinator Phase (runs FIRST when --swarm is present)

**Step R1: Collect review queue** — all `[🔍]` items plus expired/missing `[🕵️]` verifier claims (or filtered subset if task IDs specified in `$ARGUMENTS`), excluding non-expired `[🕵️]` verifier claims.
Includes both tasks (`TASKS.md`) and bugs (`BUGS.md` + `bugs/*.md`). Label each item `T-NNN` or `BUG-NNN`. Expired `[🕵️]` claims may be reclaimed with a takeover Status History row.

**Step R2: Evaluate swarm eligibility**
- If only 1 qualifying `[🔍]` item → fallback to standard single-agent mode:
  `[SWARM] Single item — running standard mode`
- If 0 qualifying items → exit with "nothing to review" message

**Step R3: Compute agent count** (same Smart Agent Count Formula as g-go-code)

| Queue size | Agents |
|-----------|--------|
| 1 | 1 (no swarm — fallback) |
| 2–4 | 2 |
| 5–9 | `ceil(count / 3)` (2–3) |
| 10–14 | 4 |
| 15+ | 5 (hard cap) |

**Step R4: Partition via round-robin**
```
1. Sort review_queue by priority (Critical→Low)
2. Buckets = [[] for _ in range(agent_count)]
3. For i, item in enumerate(review_queue):
     buckets[i % agent_count].append(item)
4. Output: buckets = [[task_ids...], [task_ids...], ...]
```

No implementation conflict graph is needed because reviewers inspect isolated sources and return payloads; the coordinator owns all final task/bug writes.

**Step R5: Display partition plan**
```
[SWARM] Review queue: {M} items → {N} reviewers
  Reviewer 1: T-014 (high), BUG-013 (medium)
  Reviewer 2: T-015 (high), T-018 (medium)
Spawning {N} reviewer agents...
```

**Step R6: Spawn reviewer agents**
- Before spawning, the coordinator claims every assigned item as `[🕵️]` with `verification-in-progress` metadata.
- Establish one review isolation source per bucket:
  - Create a `review-swarm` worktree with the T170 helper when the bucket source is branch-addressable.
  - Use snapshot mode when the bucket source is an uncommitted checkout/worktree.
  - Pass `review_isolation_mode` plus the worktree or snapshot metadata to each reviewer.
- Use the Agent tool to spawn N agents, each receiving:
  - The full `g-go-review` prompt (this command file content)
  - A filter argument for that reviewer's slice — supports both task IDs and bug IDs:
    `tasks 14 bugs BUG-013` OR `tasks 15 18`
  - Independence reminder: "Do not review tasks or bugs you implemented in this session."
  - Base-commit verification reminder (BUG-620): "Before trusting any code in your worktree, run
    Step 2b-i — `git rev-parse HEAD` + `git merge-base --is-ancestor {review_source_commit}
    HEAD` — and self-correct on mismatch. This applies even if your worktree came from the Agent
    tool's own `isolation: 'worktree'` param rather than the T170 helper; the provisioning
    mechanism is not your concern, but verifying what it handed you is."
- Each bucket reviewer runs its own Step 2c for every item in its slice (`gald3r task review-depth` / `gald3r bug review-depth`) before reviewing — this is per-item, not per-bucket, since items in the same bucket can carry very different blast radii.
- **IMPORTANT**: Each reviewer produces a **result payload** (PASS/FAIL per item + Status History rows + evidence + the computed `review_ladder_level`/`review_ladder_score` per item). Reviewers do **not** write to `TASKS.md`, `BUGS.md`, primary-checkout task/bug files, changelog/docs, generated prompts, parity outputs, or commits. The coordinator owns all final writes.

**Step R7: Collect, invoke verify verbs, and merge summary**

After all reviewers complete:
1. Read each reviewer's results (which tasks/bugs PASS, which FAIL), the per-item `review_ladder_level`/`review_ladder_score`, and any supplementary Review Note / evidence text.
2. **Invoke the verify verb for every item — mandatory (Verification Verb Gate, above). This performs the batch update; it is not a separate step from it. Every `--summary`/`--reason`/`--note` value MUST be prefixed `[ladder:{level} score={score}]` (T539 auditability requirement, same as standalone mode step 3A(e)):**
   - Tasks: `gald3r task verify <id> --pass --summary "[ladder:{level} score={score}] ..."` (PASS) or `gald3r task verify <id> --fail --reason "[ladder:{level} score={score}] {AC-NNN not met — reason}"` (FAIL), once per item. The verb appends the Status History row and resyncs the task file + `TASKS.md` automatically — do not hand-edit either. FAIL items whose Status History already has ≥3 `FAIL:` rows also get the `[🚨]` escalation per step 3A(e)(3) (no CLI verb exists for that status yet — hand-edit is the only path there).
   - Bugs: `gald3r bug resolve <id>` (PASS — append `[ladder:{level} score={score}]` to the bug's `## Notes` section separately, since `bug resolve` has no free-text field) or `gald3r bug update <id> --status open --note "[ladder:{level} score={score}] FAIL: {reason}"` (FAIL), once per item — resyncs the bug file + `BUGS.md` automatically.
   - For each FAIL task item, separately reset `implementation_sha: ''` and `implementation_branch: ''` in frontmatter (T1380) — the verb does not do this.
   - Append any additional Review Note / evidence text to the task/bug file as a supplementary edit — this augments, but never replaces, the verb call above.
3. Preserve review worktrees for failed or fix-forward items; otherwise remove them only through the T170 helper after confirming `.gald3r-worktree.json` ownership metadata:
   ```powershell
   gald3r worktree remove -TaskId {id_or_bucket} -Role review-swarm -Apply
   ```
   Omit `-Owner` here too — the same T580/BUG-612 auto-resolution used at creation resolves to the
   identical value throughout this session (the underlying env var does not change mid-session), so
   it matches automatically. For a single-review worktree, use `-Role review` with the same
   `-TaskId`. Pass `-Owner <value>` explicitly only if creation itself used an explicit override.
4. Create the review-result commit after PASS/FAIL verify-verb writes (step 2), unless one of the narrow non-commit blockers from `Review-Result Commit` applies.
5. Write unified review summary with the review-result commit SHA or the explicit non-commit blocker:

```markdown
## Swarm Review Session Summary

### Swarm Configuration
- Reviewers spawned: N
- Partition strategy: round-robin by priority
- Total items reviewed: M (tasks: X, bugs: Y)

### Reviewer Results
| Reviewer | Items Assigned | PASS | FAIL | Skipped |
|----------|---------------|------|------|---------|
| Reviewer-1 | T-014, BUG-013 | 2 | 0 | 0 |
| Reviewer-2 | T-015, T-018 | 1 | 1 | 0 |

### Reviewed PASS → [✅]
- T-014: {title}
- BUG-013: {title}

### Reviewed FAIL → back to [📋]
- T-018: {title} — {failure reason}

### Follow-Up Tasks Filed
- T{id}: {title} — {why surfaced during review}
(none surfaced — or list all filed task IDs with titles. Named-but-not-filed follow-ups are a policy violation.)

### Recommended Next Steps
- Re-implement failed tasks: @g-go-code tasks {failed_ids}
- Re-fix failed bugs: {bug_ids}
```

### Why Coordinator Owns Review Writes

Two agents updating different lines in `TASKS.md` simultaneously causes merge conflicts.
Each reviewer reports its results; the coordinator performs **one atomic batch write** after all finish.
Coordinator-owned writes also keep snapshot reviews read-only and prevent review worktrees from mutating the primary checkout accidentally.

---

## Usage Examples

```
@g-go-review
@g-go-review tasks 14 15 16
@g-go-review tasks 14
@g-go-review --swarm
@g-go-review --swarm tasks 14 15 16 17 18
```

Ready to review.

## Push offer (final review summary only)

After all verdicts are written and the review result commit is made, include a single push offer in the final summary:

```
Review complete. {N} commits on {branch} — {PASS_count} passed, {FAIL_count} failed.
Review the full diff and push when satisfied:
  git log origin/{branch}..HEAD --oneline
  git push origin {branch}
Want me to push now?
```

**Rules:** Offer push **once**, in the final review summary only. Do NOT offer push between individual task reviews. If the user replies "yes": push immediately.


## Structured output (`--json` / `--toon`) — T1381 / T1382

This command supports machine-readable output in addition to its default text/markdown:

- `--json` → structured JSON envelope via **g-skl-json-output** (`{ gald3r_version, generated_at, command, schema, data }`). For scripting, CI gates, dashboards.
- `--toon` → **g-skl-toon-output** TOON: compact, lossless, LLM-friendly (tabular arrays state keys once; ≥20% smaller than JSON). For agent handoff / context injection / vault ingestion.
- `--md` forces markdown. With no flag, AGENT_CONFIG `output_format` decides (default `markdown`, unchanged).

Output is saved to `html_output_dir` (default `docs/`) as `YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.json|.toon` per g-rl-01.


## Skill Proposal (`--propose-skill`) — T992

Optional, **off by default**. When `--propose-skill` is passed (or `propose_skills: true` in
`.gald3r/config/AGENT_CONFIG.md`), the reviewer runs **one extra evaluation step after a PASS
verdict and before the review-result commit** — it never blocks or alters the verdict.

**Step (post-PASS, pre-commit):**

1. The reviewer asks itself: *"Did this implementation solve a problem type that is NOT covered by
   any existing skill in `.gald3r_sys/skills/`? Was there a novel, generalizable multi-step
   technique that would help a future agent on a similar task?"* Answer is **No** for routine work
   — most tasks produce no proposal. This is a deliberately high bar.
2. **If yes**, draft a SKILL.md into **`.gald3r/proposed_skills/{task_id}_{slug}_draft.md`**
   (provenance in the filename) using this shape:

   ```markdown
   ---
   name: {proposed-slug}
   description: <one-line trigger summary>
   status: proposed            # NOT active until promoted
   proposed_from_task: {task_id}
   proposed_date: YYYY-MM-DD
   ---
   # {Skill Name}
   ## When to use
   - <trigger phrase 1>
   - <trigger phrase 2>
   ## What it does
   <1-2 sentence summary of the reusable pattern>
   ## Steps
   1. <generalized step>  2. ...
   ## Example
   <minimal example drawn from the implementation, redacted of project specifics>
   ```

3. Append an **IDEA_BOARD.md** entry (via `g-skl-ideas CAPTURE`) linking the draft:
   `IDEA-AUTOSKILL-{task_id}: proposed skill '{slug}' — see .gald3r/proposed_skills/{task_id}_{slug}_draft.md`.
4. Note the proposal in the review summary (one line) and the task `## Status History`.

**Hard gate — human approval required for promotion.** A draft in `proposed_skills/` is **never**
auto-promoted to `.gald3r_sys/skills/` (and therefore never synced to `.cursor/`/`.claude/`). Promotion
is a separate, human-invoked action via **`@g-skill-review`** (see that command), which routes the
polished draft through the skill-creator/writing-skills flow and then a normal parity sync. The
reviewer's job ends at writing the draft + the IDEA_BOARD link.

**Why post-PASS only:** a failed task has no validated pattern to generalize. Proposals come only
from work that actually passed verification.
