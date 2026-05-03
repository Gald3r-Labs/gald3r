---
description: "Session start protocol — quick sync validation and context display"
globs:
alwaysApply: true
---

# Session Start Protocol

## .gald3r/ Folder Layout (v3)

**SLIM layout** (gald3r base — what g-skl-setup creates):
```
.gald3r/
├── .identity             # project_id, project_name, user_id, user_name, gald3r_version, vault_location
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
Goals: G-01: [name] | G-02: [name] (from PROJECT.md)
Plan focus: [current milestone or theme from PLAN.md]
Ideas: [N] active (from IDEA_BOARD.md)
Subsystems: [N] registered (from SUBSYSTEMS.md + subsystems/)
Specs: [N] in specifications_collection/ (newest: YYYY-MM-DD) [or "none"]
⚠️ Unreviewed: {spec_filename}  ← only if spec mtime > date of last [✅] task
🧠 Learned Facts: [N] project facts | [M] global facts  (run /g-learn review to see them)
Experiments: [summary from experiments/EXPERIMENTS.md if it has active entries]
🛡️ Constraints: [N] active — run @g-constraint-check before completing any task
```

Learned fact counts: count `-` bullet points in `.gald3r/learned-facts.md` (skip headers and empties).
Global fact count: count bullets in `{vault_location}/projects/{project_name}/memory.md` if it exists.

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

**Step 2: Task Sync**
- Compare TASKS.md entries to `.gald3r/tasks/` (v3 source of truth; sequential task IDs)
- Legacy v2: completed tasks may still be under `.gald3r/phases/phase*/` until migrated
- Phantom = in TASKS.md but no matching `tasks/task{id}_*.md` (and not found in legacy archive if applicable)
- **Re-work Surface**: for each `[📋]`/pending task, check if its `## Status History` table has a FAIL row as the last entry (a row where the `To` column is `pending` and `Message` starts with `FAIL:`). If so, surface:
  ```
  ⚠️ Re-work: Task {id} previously failed verification on {Timestamp}: {Message}
  ```
  This alerts the implementing agent that prior attempts failed and what to watch for.

**Step 3: Plan / PRD / Legacy Phase Sync**
- Verify `.gald3r/PLAN.md` and `.gald3r/features/` exist for delivery projects
- Legacy v2: if TASKS.md still has phase headers → check `phases/phaseN_*.md` exists until migrated off phases

**Step 4: SUBSYSTEMS.md Staleness**
- Collect `subsystems:` values from task files → compare to SUBSYSTEMS.md
- Missing entries → flag and offer to add stubs in `subsystems/`
- For each subsystem in SUBSYSTEMS.md, verify a spec file exists in `subsystems/`
- Spec files missing `locations:` in frontmatter → flag as incomplete

**Step 5: ACTIVE_BACKLOG.md**
- Older than 26 hours → flag as stale, offer regeneration

**Step 6: Cross-Project INBOX Check** (only when PCAC is configured)

Run this check only when the current project is a PCAC participant. PCAC is active only when `.gald3r/linking/link_topology.md` exists and declares at least one non-empty parent, child, or sibling relationship, or when `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and a local `.gald3r/linking/INBOX.md` alone do **not** make a project part of a PCAC group.

When PCAC is active, `g-hk-pcac-inbox-check.ps1` runs this check automatically at session start. Behavior (T168):

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
- Scan `.gald3r/tasks/` for any task with `cascade_depth_remaining > 0` AND `cascade_forwarded: false`
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

**Fix issues BEFORE proceeding with user request.**

## Idea Capture Triggers (IMMEDIATE, any time)
Capture to `IDEA_BOARD.md` when user says:
`"make a note"` | `"remember this"` | `"idea:"` | `"what if we"` | `"someday"` | `"for later"` | `"eventually"`
