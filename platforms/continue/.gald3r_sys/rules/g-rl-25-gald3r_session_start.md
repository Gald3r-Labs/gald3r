---
description: "Session start protocol — quick sync validation and context display"
globs:
alwaysApply: true
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

# Session Start Protocol

## .gald3r/ Folder Layout (v3)

**SLIM layout** (gald3r base — what g-skl-setup creates):
```
.gald3r/
├── .identity             # project_id, project_name, project_type, user_id, user_name, gald3r_version, vault_location
├── .gitignore
├── TASKS.md, PLAN.md, PROJECT.md, CONSTRAINTS.md, BUGS.md, SUBSYSTEMS.md, IDEA_BOARD.md, FEATURES.md
├── features/       # Individual PRD files
├── bugs/       # Individual bug detail files (optional; index in BUGS.md)
├── reports/
├── logs/
├── subsystems/ # Per-subsystem spec files (subsystem_name.md)
├── specifications_collection/  # Incoming specs, PRDs, wireframes from stakeholders (README.md index)
└── tasks/      # Individual task files (sequential task IDs)
```

**FULL layout additions** (gald3r_dev only — do NOT create in slim projects):
```
├── config/      # HEARTBEAT.md, SPRINT.md, AGENT_CONFIG.md
├── experiments/ # EXPERIMENTS.md, SELF_EVOLUTION.md, HYPOTHESIS.md, EXP-NNN.md
├── linking/     # README.md, INBOX.md — cross-project coordination
│   ├── sent_orders/    # Outbound order ledger (order_*.md per dispatched task — see g-skl-pcac-order)
│   ├── pending_orders/ # Staged orders not yet delivered (target inaccessible)
│   └── peers/          # Peer capability snapshots
├── vault/       # encrypted/sensitive context
└── phases/      # Legacy v2 only — phase defs / archives
```

## Display at Session Start (when .gald3r/ exists)
```
📌 SESSION CONTEXT
Mission: [from PROJECT.md, 1 line]
Project type: software_development | github_integration: enabled/disabled  ← read project_type= from .gald3r/.identity; fallback: .gald3r/.project_type dotfile; default software_development if absent; github_integration shown only when project_type=software_development
Goals: G-01: [name] | G-02: [name] (from PROJECT.md)
Plan focus: [current milestone or theme from PLAN.md]
Ideas: [N] active (from IDEA_BOARD.md)
Subsystems: [N] registered (from SUBSYSTEMS.md + subsystems/)
Systems: [N] defined (LOGGING, MEMORY, TASK_MGMT, ...)  ← only if .gald3r/PRODUCT_SYSTEMS.md exists; abbreviate the first ~3 defined_groups: with "..." suffix
⚠️ Subsystems: [N] ungrouped — consider running @g-subsystem-audit  ← only if subsystem count > 25 AND .gald3r/PRODUCT_SYSTEMS.md does NOT exist (T1458 sprawl warning)
Specs: [N] in specifications_collection/ (newest: YYYY-MM-DD) [or "none"]
⚠️ Unreviewed: {spec_filename}  ← only if spec mtime > date of last [✅] task
🧠 Learned Facts: [N] project facts | [M] global facts  (run /g-learn review to see them)
📖 Vocab: [V] abbreviations loaded (local + parent if WPAC-linked) — expand silently, no narration  ← only if vocab.md exists with ≥1 entry
📓 Journal: [last entry date] for {active-agent-slug}  ← only when the active agent role has journal entries
⚠️ Avoid: {one-line summary}  ← only if the active agent's most recent journal entry is `category: anti-pattern`
Experiments: [summary from experiments/EXPERIMENTS.md if it has active entries]
🛡️ Constraints: [N] active — run @g-constraint-check before completing any task
⚠️ Release sync: N CHANGELOG version(s) missing release file — run @g-release-sync  ← only show when gap count > 0
🖥️ Platform status: N healthy, M need attention, K unknown (of 23) — run @g-platform-check  ← only show when .gald3r/PLATFORM_STATUS.md exists
```

Systems count (T1458): read `defined_groups:` from `.gald3r/PRODUCT_SYSTEMS.md` frontmatter; `Systems: N defined` = count of groups; show the first ~3 group names then `...`. Skip the line silently if PRODUCT_SYSTEMS.md is absent. The `⚠️ Subsystems: N ungrouped` warning is one-time per session and fires ONLY when PRODUCT_SYSTEMS.md is absent AND `subsystems/*.md` count > 25 — it directs the user to `@g-subsystem-audit` (which can scaffold grouping via `@g-system-rebuild`).
Learned fact counts: count `-` bullet points in `.gald3r/learned-facts.md` (skip headers and empties).
Global fact count: count bullets in `{vault_location}/projects/{project_name}/memory.md` if it exists.
Vocab loading (WPAC-aware):
1. Load `.gald3r/vocab.md` — count data rows in the "Active Vocabulary" table (skip header + separator rows).
2. If `.gald3r/workspace/topology.md` exists and declares a `parent:` with a resolvable local path, also load the parent's `.gald3r/vocab.md`. Merge: local entries take precedence over parent entries on name collision.
3. Total vocab count = unique abbreviations across both sources.
4. Load all entries into working context and **expand silently** when the user uses one (no "you said X, which means…" narration).
5. Skip silently if both files are absent or have no entries.
Manage with `@g-vocab-add` / `@g-vocab-list` / `@g-vocab-search`.

## Agent Journal Read (T1010 — myPKA pattern)

When acting as a specific gald3r agent role, read that role's recent journal **before starting work**:

1. Resolve the active agent slug (e.g. `g-agnt-code-reviewer`).
2. Read the last **5** entries (newest by filename date) from
   `{platform}/agents/{slug}/journal/*.md` — these are durable, offline,
   per-role learnings (format in `{platform}/agents/JOURNAL_FORMAT.md`).
3. Surface `category: anti-pattern` entries prominently (the `⚠️ Avoid:`
   line above) so prior mistakes are not repeated.
4. Skip silently when the agent has no journal directory or no entries.

Journals are plain git-tracked markdown — no Docker/DB required. They
supplement `.gald3r/learned-facts.md` with per-agent-role specificity.

## Subsystem Awareness (MANDATORY)
At session start, read `.gald3r/SUBSYSTEMS.md` for the registry and interconnection graph.
For any subsystem you're about to modify, read its spec file at `.gald3r/subsystems/{name}.md`.
This prevents architectural drift and ensures changes respect subsystem boundaries.

## Sync Validation (Run When User Mentions Tasks/Phases/Status)

**Step 0: Constraints Load**
- Read `.gald3r/CONSTRAINTS.md`
- Count active constraints from the `## Constraint Index` table (Status = active)
- **Expiry check**: for each active constraint with expiry fields (`**Expires at**:`, `**Resolved when task**:`, `**Resolved when feature**:`), evaluate conditions. If any constraints expired since last session: `⏰ N constraint(s) auto-expired: C-{ids}`. Run the CHECK expiry evaluation from `g-skl-constraints` to auto-archive expired constraints.
- Display the LIST output from `g-skl-constraints` (compact one-liner per constraint)
- If any constraint definition block is missing the `**Enforcement**:` field → flag: `⚠️ C-{ID} has no enforcement definition`

**Step 1: Goals Check**
- PROJECT.md missing goals content or has `{Goal name}` placeholders → auto-generate from PROJECT.md mission / PLAN.md

**Step 1.5: Version Check** (optional, non-blocking)
- Skip if `disable_version_check: true` in `.gald3r/config/AGENT_CONFIG.md`
- Read `gald3r_version` from `.gald3r/.identity`; attempt a 3-second fetch of the version feed (configured `version_feed_url` or `https://api.github.com/repos/gald3r/gald3r/releases/latest`)
- If fetch succeeds and installed version < latest: `💡 gald3r update available (v{current} → v{latest}) — run @g-update`
- If fetch fails or times out: skip silently (no error, no delay)

**Step 2: Task Sync**
- Compare TASKS.md entries to `.gald3r/tasks/**` (T1025 status subfolders: `open/`, `in-progress/`, `awaiting/`, `completed/YYYY/MM/`, `closed/`; v3 source of truth; sequential task IDs)
- Legacy v2: completed tasks may still be under `.gald3r/phases/phase*/` until migrated
- Phantom = in TASKS.md but no matching `tasks/task{id}_*.md` (and not found in legacy archive if applicable)
- **Auto-Triage L0 hand-off** (T1385): when phantom/orphan drift is detected, hand the finding to `g-skl-auto-triage` (kind `spec_defect`). Phase 1 is report-only for `TASKS.md`/`tasks/` — auto-triage will record `needs_attention`/`blocked_by_risk` (coordination state is never auto-edited) and write the audit row to `.gald3r/logs/triage_auto_YYYYMMDD.log`.
- **Re-work Surface**: for each `[📋]`/pending task, check if its `## Status History` table has a FAIL row as the last entry (a row where the `To` column is `pending` and `Message` starts with `FAIL:`). If so, surface:
  ```
  ⚠️ Re-work: Task {id} previously failed verification on {Timestamp}: {Message}
  ```
  This alerts the implementing agent that prior attempts failed and what to watch for.

**Step 2a: Review Branch Mismatch Warning** (BUG-095 fix, T1374)
- Check if `tasks/verification/` (or any subfolder containing `[🔍]` tasks) has task files with `implementation_branch:` set
- If any `[🔍]` tasks have `implementation_branch: <X>` where `<X>` differs from the current branch:
  ```
  ⚠️ Review branch mismatch: N task(s) awaiting review were implemented on branch '<X>'.
     You are currently on '<current_branch>'. Run `git checkout <X>` before starting g-go-review.
  ```
- Suppress when current branch already matches `implementation_branch`
- Suppress when `implementation_branch` field is absent on all `[🔍]` tasks (legacy tasks — no signal)

**Step 2b: Release Sync Check** (C-023)
- Read `CHANGELOG.md`, count all `## [x.x.x]` version headers (skip `## [Unreleased]`)
- For each, check if `.gald3r/releases/` has a file whose name contains the version (e.g., `v1-5-0` for `[1.5.0]`)
- Gap count > 0 → surface: `⚠️ N CHANGELOG version(s) missing release file — run @g-release-sync`
- Gap count == 0 → display: `✅ CHANGELOG/releases in sync`

**Step 3: Plan / PRD / Legacy Phase Sync**
- Verify `.gald3r/PLAN.md` and `.gald3r/features/` exist for delivery projects
- Legacy v2: if TASKS.md still has phase headers → check `phases/phaseN_*.md` exists until migrated off phases

**Step 4: SUBSYSTEMS.md Staleness**
- Collect `subsystems:` values from task files → compare to SUBSYSTEMS.md
- Missing entries → flag and offer to add stubs in `subsystems/`
- For each subsystem in SUBSYSTEMS.md, verify a spec file exists in `subsystems/`
- Spec files missing `locations:` in frontmatter → flag as incomplete
- **Auto-Triage L0 hand-off** (T1385): subsystem-spec drift (a spec missing `locations:` frontmatter) is a `spec_defect` candidate. Hand it to `g-skl-auto-triage` with `fix_type=schema_comment`; only the lowest-risk metadata annotation is auto-applied (`risk_score <= auto_triage_risk_threshold`), otherwise it is logged `needs_attention`.

**Step 5: ACTIVE_BACKLOG.md**
- Older than 26 hours → flag as stale, offer regeneration

**Step 6: Cross-Project INBOX Check** (only when WPAC is configured)

Run this check only when the current project is a WPAC participant. WPAC is configured only when `.gald3r/workspace/topology.md` exists and declares at least one non-empty parent, child, or sibling relationship, or when `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and a local `.gald3r/workspace/INBOX.md` alone do **not** make a project part of a WPAC group.

When WPAC is active, `g-hk-wpac-inbox-check.ps1` runs this check automatically at session start. Behavior (T168):

- **Per-item display, not just counts** — the hook surfaces each open INBOX item with a one-line summary (type, source project, subject, age in hours/days). Items are grouped by type with subheadings, sorted within each group oldest-first, and truncated at 10 per group with a "+N more" note.

- **Auto-action policy** (T168):
  - `[INFO]` notifications → auto-mark-read (rewritten to `[DONE]` with an `**Auto-actioned:**` stamp). Low risk, no action required.
  - `[SYNC]` items from siblings → auto-mark-read after surfacing. Updating the local peer snapshot is left to `@g-pcac-read` (the hook does not write `linking/peers/`).
  - `[BROADCAST]` from a parent → surface only; user must `@g-pcac-read --ack <id>` to acknowledge.
  - `[REQUEST]` from a child → surface only; user must `@g-pcac-read --accept|--decline <id>` to action.
  - `[ORDER]` from a parent → surface only; user must `@g-pcac-read --accept <id>`. Treated as blocking until accepted.
  - `[CONFLICT]` → preserve existing gate behavior — surface immediately as `⚠️ WARNING` before any other work; agents MUST resolve/defer via `@g-pcac-read` before proceeding. Conflicts gate ALL session work.

- **Audit log** — every auto-action writes a row to `.gald3r/logs/pcac_auto_actions.log`: `{timestamp ISO-8601} | {item_id} | {action}`.

- **Idempotency** — re-running the hook on an already-actioned inbox is a no-op (auto-actioned items already have `[DONE]` status; only `[OPEN]` rows are processed).

- **Auto-mark-read mechanics** — the `[OPEN]` heading is rewritten to `[DONE]` and a `**Auto-actioned:** YYYY-MM-DD by g-hk-pcac-inbox-check` line is appended directly under the heading. Items are NEVER deleted (audit trail). On first run that produces auto-actions, a `## Recently Actioned` section is appended to the bottom of INBOX.md.

- **Skip auto-actions** — pass `-NoAutoAction` to the hook to surface items only without any rewrite.

**Step 6b: Cross-Project Dependency Surface** (if `.gald3r/linking/sent_orders/` exists)

**The sent_orders ledger is the ONLY tracking surface for outbound PCAC (T167)** — no local task should mirror it. Parents/siblings waiting on a child response track the wait via this ledger, never via a "[Waiting]" or "[Broadcast tracker]" task.

- List `.gald3r/linking/sent_orders/order_*.md`
- For each: read frontmatter `status:` field
  - **Awaiting** = count of records where `status` ∈ {`sent`, `acknowledged`, `in-progress`, `blocked`}
  - **Resolved-since-last-session** = count of records where `status: completed` AND the record's most-recent Sync History row timestamp is newer than the previous session boundary (use last `[✅]` task completion date in TASKS.md as a cheap proxy when no explicit session-boundary file is available)
  - **Stale (T167)** = records where `status` ∈ {`sent`, `acknowledged`} AND no Sync History row in the last 30 days. Surface so the user can `@g-pcac-status --close <ord-id>` to formally abandon (writes `status: abandoned` + a final Sync History row). This replaces the "task that never completes" problem.
- Display: `🔗 Cross-project: {N_awaiting} awaiting, {M_resolved} resolved, {S_stale} stale`
  - If `N_awaiting > 0`: also list the awaiting orders compactly:
    ```
       ⏳ ord-{shortid} → {sent_to}: {remote_task_title} ({status}, {days_out}d)
    ```
  - If `M_resolved > 0`: also list:
    ```
       ✅ ord-{shortid} → {sent_to}: {remote_task_title} (resolved {date})
    ```
  - If `S_stale > 0`: also list:
    ```
       ⚠️ ord-{shortid} → {sent_to}: {remote_task_title} (stale {N}d, {status}) — consider @g-pcac-status --close
    ```
- Skip silently when `sent_orders/` is empty or absent.

**Step 7: Cascade Forward Check** (if `.gald3r/PROJECT.md` **Project Linking** section lists children with cascade)
- Scan `.gald3r/tasks/**` (all status subfolders) for any task with `cascade_depth_remaining > 0` AND `cascade_forwarded: false`
- If found: forward cascades to children listed in topology (follow `g-broadcast` skill pattern but using the cascade chain metadata from the task)
- Mark forwarded tasks as `cascade_forwarded: true`
- Report: `Forwarded N cascade task(s) to: [child names]`
- If no children have `cascade_forward: true` or depth is 0: skip silently

**Step 8: Experiment Staleness Check** (if `.gald3r/experiments/EXPERIMENTS.md` exists)
- Read EXPERIMENTS.md for active experiments
- For each active experiment: read EXP file, check if any stage is `[🔄]` for >48h without update
- Stale experiments → flag: `⚠️ EXP-NNN has a running stage with no update for >48h`
- Display active experiment summary: `EXP-NNN (Stage M/N — status)`

**Step 9: Documentation Staleness Check** (if vault is configured and `research/platforms/_index.yaml` exists)
- Read `.gald3r/.identity` → get `vault_location`
- Read `{vault_location}/research/platforms/_index.yaml`
- Count entries where `next_refresh` field is earlier than today's date
- If any stale entries found → display: `📚 N documentation note(s) overdue for refresh — run @g-ingest-docs REFRESH_STALE`
- Skip silently if `_index.yaml` does not exist or vault is not configured

**Step 10: Version Check** (only when MCP backend is reachable)
- Call `gald3r_check_update(project_path=<cwd>, force=false)`
- If result is cached, unreachable, or fails for any reason: skip silently (do not slow down session start)
- If `update_available: true` AND `latestVersion` is NOT in `.gald3r/.update_skips`:
  Display: `🔔 gald3r {latestVersion} available — run @g-upgrade to update`
  (single line only — do not block the session or show full release notes)
- If `update_available: false`: skip silently

**Step 10b: Schema Version Probe** (T1440 — alert only, never writes)

A lightweight read-only probe that surfaces schema drift between this project's
`.gald3r/` files and the installed gald3r system schema. It runs **after** the
gald3r update check above. It NEVER writes, modifies, or creates any file — it
only alerts. Auto-fix/migration is g-medic's job; this probe just points there.

```powershell
# Pseudocode for probe logic
$registry = ".gald3r_sys/schemas/_registry.yaml"
if (-not (Test-Path $registry)) { return }   # Case 4: schema system not installed → silent
$systemSchema = Read-RegistryCurrentVersion $registry   # e.g. "v1" for task-file
$sampleFiles  = Get-GaldSampleFiles                     # ≤5: TASKS.md, BUGS.md, 3 task files by mtime
foreach ($file in $sampleFiles) {
    $fileSchema = Read-FrontmatterField $file "schema_version"  # missing → treat as v0
    Compare-SchemaVersions $fileSchema $systemSchema
}
```

- Read the system schema version from `.gald3r_sys/schemas/_registry.yaml`
  (`current_version` of the matching `schema_id`).
- Sample **at most 5 files**: `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, and the **3
  most-recently-modified** task files under `.gald3r/tasks/**` (by modification
  time). For each, read the `schema_version` frontmatter field; a missing field
  means **v0** (pre-versioned era).

**Output cases:**

```
# Case 1: Files OLDER than system (most common right after an upgrade)
⚠️ Schema drift detected: 3 files use schema v0 (pre-versioned), current is v1
   Run @g-medic to auto-migrate and validate

# Case 2: Files MATCH system
(silent — no output)

# Case 3: Any file NEWER than system
💡 1 file uses schema v2 but installed gald3r supports v1 (schema: task-file)
   Your .gald3r files may be from a newer gald3r install. Consider: @g-update

# Case 4: _registry.yaml MISSING (schema system not installed yet)
(silent — no alert)
```

**Rules:**
- Reads **at most 5 files** (TASKS.md, BUGS.md, 3 task files sampled by modification time).
- Completes in **under 1 second** — no heavy/recursive scanning at session start.
- **Never writes, never modifies, never creates** any file.
- **Skips silently** if `.gald3r_sys/schemas/_registry.yaml` does not exist.

**Fix issues BEFORE proceeding with user request.**

## Idea Capture Triggers (IMMEDIATE, any time)
Capture to `IDEA_BOARD.md` when user says:
`"make a note"` | `"remember this"` | `"idea:"` | `"what if we"` | `"someday"` | `"for later"` | `"eventually"`
