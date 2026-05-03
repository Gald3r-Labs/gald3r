Verification-only backlog review: $ARGUMENTS

## Mode: REVIEW ONLY

> ⚠️  **Run this in a NEW agent session** — different window, different invocation.
> If you implemented any of these tasks in this session, **skip them** (leave `[🔍]`).
> Self-review defeats the purpose of this gate.

---


### PCAC Inbox Gate (Only When PCAC Is Configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a PCAC participant. PCAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a PCAC group member.

If PCAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If PCAC is not configured, skip this gate and report `PCAC: not configured / skipped`.


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

## Execution Protocol

### 1. Load Context

Read in this order:
- `.gald3r/TASKS.md` — identify all `[🔍]` (Awaiting Review) tasks and skip non-expired `[🕵️]` verification claims
- `.gald3r/BUGS.md` — identify all bugs with `[🔍]` status in the index table and skip non-expired `[🕵️]` verification claims
- Individual task files for each `[🔍]` task item — read acceptance criteria
- Individual bug files (`.gald3r/bugs/bug*.md`) for each `[🔍]` bug — read fix description and affected file/line
- `git log --oneline -10` — understand what was recently implemented
- `.gald3r/CONSTRAINTS.md` — guardrails

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
3. Append Status History: `awaiting-verification -> verification-in-progress`.
4. If reclaiming a stale `[🕵️]` item, the Status History message must name the previous `verifier_owner` and claim expiry.
5. Never review an item currently claimed by a different non-expired verifier.

### 2b. Establish Review Isolation

After claiming and before inspecting implementation details, isolate the review source.

**Default: review worktree from checkpoint commit.** Use the shared T170 helper when the review source is branch-addressable. Normal `g-go-code` / `g-go --swarm` handoff provides a code-complete checkpoint branch and commit SHA; prefer that source over dirty snapshot inspection.

```powershell
.\scripts\gald3r_worktree.ps1 -Action Create -TaskId {id_or_bucket} -Role review -Owner {platform_or_agent_slug} -BaseBranch {review_source_branch_or_HEAD} -Json
```

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

**Standalone vs coordinator-managed writes.**
- Standalone `@g-go-review` may write the claimed task/bug status files and indexes directly, then creates the review-result commit after those writes.
- When spawned by `g-go` Phase 2 or `g-go-review --swarm`, reviewers run in coordinator-managed mode: return PASS/FAIL payloads, Status History rows, evidence, and authorized fix-forward patches only. The coordinator owns all task/bug file, `TASKS.md`, `BUGS.md`, changelog/docs, generated prompt, parity sync, final staging, and review-result commit writes.

### 3. Review Each Item

#### 3A. Review Each Task

For each `[🕵️]` task claimed by this verifier:

**a) Read task spec** — list all acceptance criteria
**b) Check each criterion against actual files/code**
  - If `review_isolation_mode: worktree`, inspect files under `review_worktree_path`.
  - If `review_isolation_mode: snapshot`, inspect files under `review_snapshot_path` read-only.
**b2) Workspace boundary check** — run `g-skl-workspace` ENFORCE_SCOPE against changed paths and the task/bug routing metadata; unknown manifest repo IDs, undeclared member writes, docs-only source changes, or member writes without manifest permission fail the item.
**c) Score PASS or FAIL per criterion**
**d) Bug check during review** — if you encounter a bug not covered by the task's ACs:
  - Determine: introduced by this task? → flag as unmet criterion → task FAIL
  - Pre-existing? → log BUG entry via `g-skl-bugs`, add `BUG[BUG-{id}]` comment, note in session summary — does NOT fail this task (see `g-rl-35`)
**e) Overall result:**
  - All criteria PASS → mark `[✅]` from `[🕵️]` + append verification note to task file + **run docs check (step 3f)**
  - Any criterion FAIL → **before changing status**:
    1. Append a row to `## Status History` at the bottom of the task file (add section if missing):
       ```
       | YYYY-MM-DD | verification-in-progress | pending | FAIL: {AC-NNN, AC-NNN} not met — {brief reason} |
       ```
    2. **🚨 STUCK LOOP CHECK** — count all rows in the task's `## Status History` where the Message column contains `FAIL:`:
       - **Count < 3** → mark back to `[📋]` (pending) in task file YAML and TASKS.md
       - **Count ≥ 3** → mark `[🚨]` (requires-user-attention) in task file YAML and TASKS.md; append a `## [🚨] Requires User Attention` block to the task file:
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
    3. Document specific failure reason in task file (Review Note section)
    - The Status History row message must name which ACs failed and why. `FAIL` alone is not acceptable.
    - **Agents must NEVER autonomously reset `[🚨]` back to `[📋]` — only a human can do this.**

**f) Docs check** (PASS tasks only — fires at true completion):
  - Does this task add/remove/change user-facing behavior? (skills, commands, agents, hooks, rules, conventions)
  - **YES** → append entry to `CHANGELOG.md` under `[Unreleased]`; update `README.md` if a relevant section exists
  - **NO** (internal refactor, task file edits, bug fixes with no interface change) → skip
  - Refer to `g-rl-26-readme-changelog.mdc` for what qualifies and where to update

**Per-task output format:**
```
REVIEW: Task 014 — g-go role separation
  ✅ g-go-code.md created in gald3r_template_full/.cursor/commands/
  ✅ g-go-review.md created with NEW-SESSION warning
  ❌ g-go.md not updated — self-review banner missing
  → RESULT: FAIL — moved back to [📋] — reason recorded in task file
```

#### 3B. Review Each Bug

For each `[🕵️]` bug claimed by this verifier:

**a) Read bug file** — note: title, affected file/line, fix description in Status History
**b) Verify the fix is present** — check the referenced file/line; confirm the bug no longer exists as described
**c) Regression check** — scan surrounding code for obvious regressions introduced by the fix
**d) Overall result:**
  - Fix confirmed present + no regression → mark `[✅]` from `[🕵️]` in BUGS.md index + set bug file `status: completed` + append verification note to bug file Status History
  - Fix absent or regression found → mark back to `[📋]` (open) from `[🕵️]` in BUGS.md + set bug file `status: open` + append FAIL row to bug file Status History with specific reason

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


### PCAC Inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the PCAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-pcac-read` before continuing.

### Coordinator-Only Shared Writes

In `g-go-review --swarm`, reviewers are evidence producers. They must not write shared ledgers or repository-wide generated surfaces. Return:

- PASS/FAIL payloads and criteria evidence.
- Proposed Status History rows.
- Any bug/task follow-up requests.
- Fix-forward patch bundles only when the user explicitly authorized fix-forward review.

The coordinator alone performs `.gald3r` status writes, `TASKS.md`/`BUGS.md` updates, changelog/docs updates, generated prompt regeneration, parity sync, final staging, and review-result commit operations.

### Review-Result Commit

After PASS or FAIL status writes are complete, create a coordinator-owned review-result commit by default. This applies whether all items PASS, all items FAIL, or the review result is mixed. The commit is the audit point for the review verdict, not an optional follow-up offer.

Required flow:
1. Stage only review-owned paths by explicit allowlist, such as the touched task/bug files, `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, review-owned docs/changelog updates, and regenerated review prompt surfaces.
2. Never use `git add .`; exclude `.gald3r-worktree.json`, terminal transcripts, local logs, unrelated files, and other non-deliverable artifacts.
3. Commit with a message that names the reviewed task/bug IDs and whether the result was PASS, FAIL, or mixed.
4. Include the commit SHA in the final review summary.

Allowed reasons not to create the review-result commit are limited to: unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit. If one of these blockers applies, state the blocker explicitly and leave the review status writes uncommitted for human resolution.

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
- **IMPORTANT**: Each reviewer produces a **result payload** (PASS/FAIL per item + Status History rows + evidence). Reviewers do **not** write to `TASKS.md`, `BUGS.md`, primary-checkout task/bug files, changelog/docs, generated prompts, parity outputs, or commits. The coordinator owns all final writes.

**Step R7: Collect, batch-update TASKS.md, and merge summary**

After all reviewers complete:
1. Read each reviewer's results (which tasks/bugs PASS, which FAIL)
2. **Batch-update individual task/bug files** with review notes and Status History rows from reviewer payloads.
3. **Batch-update TASKS.md** in a single write:
   - Task PASS items: `[🕵️]` → `[✅]`
   - Task FAIL items: `[🕵️]` → `[📋]` (back to pending)
4. **Batch-update BUGS.md** in a single write:
   - Bug PASS items: `[🕵️]` → `[✅]`
   - Bug FAIL items: `[🕵️]` → `[📋]` (back to open)
5. Preserve review worktrees for failed or fix-forward items; otherwise remove them only through the T170 helper after confirming `.gald3r-worktree.json` ownership metadata:
   ```powershell
   .\scripts\gald3r_worktree.ps1 -Action Remove -TaskId {id_or_bucket} -Role review-swarm -Owner {platform_or_agent_slug} -Apply
   ```
   For a single-review worktree, use `-Role review` with the same `-TaskId` and `-Owner` used at creation.
6. Create the review-result commit after PASS/FAIL status writes, unless one of the narrow non-commit blockers from `Review-Result Commit` applies.
7. Write unified review summary with the review-result commit SHA or the explicit non-commit blocker:

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
