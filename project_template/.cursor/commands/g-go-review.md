---
subsystem_memberships: [TASK_MANAGEMENT]
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

---


### Step 0 — Workspace Member Clean-Status Preflight (T1431)

Before the WPAC gate / review-queue build / claim / review-worktree creation, run the **read-only**
workspace member clean-status preflight: scan `.gald3r/workspace/workspace_manifest.yaml`, run
`git -C <path> status --short` on each `autonomous_child` member, and either print
`Workspace clean -- N members checked` (proceed) or a per-repo dirty-status table asking the user
to commit/stash first. Never auto-commits or writes. `--skip-member-clean-check` bypasses with a
printed warning. Additive to the Housekeeping Commit Gate. **Full authoritative algorithm: see
`g-go.md` Step 0.**

---

### WPAC inbox Gate (Only When WPAC is configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a WPAC participant. WPAC is configured only when `.gald3r/workspace/topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a WPAC group member.

If WPAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.ps1", ".claude\hooks\g-hk-wpac-inbox-check.ps1", ".agent\hooks\g-hk-wpac-inbox-check.ps1", ".codex\hooks\g-hk-wpac-inbox-check.ps1", ".opencode\hooks\g-hk-wpac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-wpac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If WPAC is not configured, skip this gate and report `WPAC: not configured / skipped`.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the WPAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -TaskId <id-when-known> -Json
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

2. **`gald3r_worktree.ps1 -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/workspace/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

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
gald3r_worktree.ps1 -Action Create -Branch <implementation_branch> -Role review
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
- **Active workflow profile (T1239)** — load once via `load_profile.ps1` (active
  skill folder; see g-skl-tasks "Reading the active profile"). The review-gate
  status (the `[🔍]`-equivalent), the PASS target, and the FAIL target come from
  the profile's `review_gate` + `task_statuses[]` rather than hardcoded strings
  (AC1). For `software_dev` these resolve to `awaiting-verification` → PASS `done`
  / FAIL `pending` exactly as before; a `content_creation` project reviews
  `in_review` → PASS `rendering`/`published` per its DAG order. Absent
  `.gald3r/config/workflow_profiles/` → built-in `software_dev` lifecycle.

> If a task has no `## Handoff Report` section, note "No Handoff Report" in your review summary and proceed to read the implementation files listed in acceptance criteria directly.

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
**b3) Security pass (inline OWASP/STRIDE)** — for tasks that touch web/API/auth/data/integration code, apply the OWASP Top 10 checklist from `g-skl-code-review` Step 2 to changed files. For tasks adding new services, cross-process boundaries, or significant architectural changes, apply STRIDE. Security findings are rated **Critical / High / Medium / Low**. Report each finding with OWASP/STRIDE category, file:line, and recommended fix. Code annotated with `# nosec: <justification>` or `# security-exempt: <reason>` is waived. Any Critical or High finding → flag as unmet criterion (FAIL).

**Step S — Two-phase security scan (T1167)** — runs **after** b3 inline security pass and **before** the `[🔍] → [✅]` write at step (e). Invokes `g-skl-security-scan` in **Two-Phase Mode** when the candidate review source has any changed files outside of `*.md` / `docs/**` / `CHANGELOG.md` / `README.md` / `LICENSE`.

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

**Step E — Encoding CI scan (T1448, optional/non-blocking)** — after Step S and before (c), reviewers MAY run the encoding-normalize hook in scan mode as a lightweight CI encoding check over the candidate's changed files:

```powershell
# Reports (exit 1) if any changed text file needs encoding normalization; writes nothing.
.claude/hooks/g-hk-encoding-normalize.ps1 -Scan
```

This surfaces stray BOMs / CRLF / UTF-16 drift before they reach the integration branch. It is **advisory by default** — a non-clean scan is recorded in the review note (`Step E: N file(s) need encoding normalization`) and is informational, not an automatic FAIL (the pre-commit hook fixes these on commit). Projects that want it enforced can treat a non-zero scan as a FAIL via `encoding_scan_enforced: true` in `AGENT_CONFIG.md`.

**c) Score PASS or FAIL per criterion**
**d) Bug check during review** — if you encounter a bug not covered by the task's ACs:
  - Determine: introduced by this task? → flag as unmet criterion → task FAIL
  - Pre-existing? → log BUG entry via `g-skl-bugs`, add `BUG[BUG-{id}]` comment, note in session summary — does NOT fail this task (see `g-rl-35`)
**e) Overall result:**
  - All criteria PASS → mark `[✅]` from `[🕵️]` + append verification note to task file + **run docs check (step 3f)**
  - Any criterion FAIL → **before changing status**:
    1. Append a row to `## Status History` at the bottom of the task file (add section if missing):
       ```
       | YYYY-MM-DD | verification-in-progress | pending | FAIL: {AC-NNN, AC-NNN} not met — {brief reason}; impl_sha/branch cleared |
       ```
    2. **Clear stale provenance (T1380)** — reset `implementation_sha: ''` and `implementation_branch: ''` in the task file YAML frontmatter. This prevents the next implementer from inheriting a SHA that points at a failed attempt. (PASS path: leave sha/branch unchanged — they are correct provenance for completed work.)
    3. **🚨 STUCK LOOP CHECK** — count all rows in the task's `## Status History` where the Message column contains `FAIL:`:
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
    4. Document specific failure reason in task file (Review Note section)
    - The Status History row message must name which ACs failed and why. `FAIL` alone is not acceptable.
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
- **IMPORTANT**: Each reviewer produces a **result payload** (PASS/FAIL per item + Status History rows + evidence). Reviewers do **not** write to `TASKS.md`, `BUGS.md`, primary-checkout task/bug files, changelog/docs, generated prompts, parity outputs, or commits. The coordinator owns all final writes.

**Step R7: Collect, batch-update TASKS.md, and merge summary**

After all reviewers complete:
1. Read each reviewer's results (which tasks/bugs PASS, which FAIL)
2. **Batch-update individual task/bug files** with review notes and Status History rows from reviewer payloads. For each FAIL item: also reset `implementation_sha: ''` and `implementation_branch: ''` in frontmatter (T1380).
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
