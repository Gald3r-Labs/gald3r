---
name: g-skl-wpac-order
description: As a parent project, push a task to one or more child projects with configurable cascade depth (1–3). Creates tasks in child .gald3r/ folders and an INBOX notification.
token_budget: medium
subsystem_memberships: [WORKSPACE_COORDINATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

> **Multi-agent framework (T1094):** Delegation + Broadcast — parent pushes task(s) to child project(s).
# g-skl-wpac-order

## When to Use
`@g-wpac-order` command. When a change in this project requires action in child projects.

## Transport layer (WPAC-v2 — T1608)

**Step 0-T — transport verdict (code decides, never the model — g-rl-38).** Before the
file steps below, for EACH target child build the delegation-intake payload (the live
`world_tree` `TaskIntakeRequest` contract: `title`, `description`, `task_type`,
`priority`, `project_id`, `subsystems[]`, `dependencies[]`, `acceptance_criteria[]`,
`source_project` = this project) and run the shared transport (T1609 shim underneath):

```
gald3r workspace outbox send --verb order --payload-file <payload.json>
```

| Verdict | Action |
|---|---|
| `ok` | Delivered via `POST /api/v1/tasks/delegation/intake` — the target wakes via inbox auto-wake (world_tree T494), replacing the WPAC ORDER file-drop and the session-start poll. SKIP the cross-repo direct-write (steps 5a–5d) for that child; STILL write the LOCAL sent_orders ledger (step 5e) with `transport: world_tree` and `task_uuid: "<TaskIntakeResponse.task.id>"` as proper frontmatter fields (T263 — queryable by `gald3r valk order-status`, not just noted in a Sync History row) plus a Sync History row recording the same UUID for the human-readable audit trail. |
| `offline` / `error` | Perform ALL file steps below exactly as today (behavior identical to WPAC-v1). The message was write-aheaded to `.gald3r/linking/outbox/` BEFORE any network I/O, so nothing is lost — `gald3r workspace outbox flush` reconciles it on reconnect. |
| `auth_required` | File steps below + tell the user to run `gald3r login`. Entry parked (not retried). |
| `upgrade_required` | File steps below + print the shim's upgrade line (online transport is paid-Team gated per T633/T641; the file transport stays free). Entry parked (not retried). |

Everything below this section is the **OFFLINE / FILE FALLBACK transport** — the verb
surface (name + arguments) is unchanged.

## WPAC Direct-Write Authority (ADR-003, ADR-013)

**Core mechanic**: When the controller runs `@g-wpac-order`, it writes task files DIRECTLY into the child repo's `.gald3r/` — no inbox wait. The inbox entry is written as an audit trail only.

### Decision: Direct-Write vs Inbox-Only Fallback

```
1. Resolve child local_path from workspace_manifest.yaml
2. Test-Path: does the directory exist on this filesystem?
   YES → Direct-Write path (below)
   NO  → Inbox-only fallback (write to INBOX only; no task file created)
3. Check ancestry: is current controller a registered ancestor of the target?
   Resolve via workspace_manifest.yaml repositories[target].wpac_role or topology.md
   NOT ancestor → warn + abort (no authority)
```

### Direct-Write Path (local repo accessible)

Steps `5a-5e` in the main flow write directly to `<child_local_path>/.gald3r/`:
- Task file → `<child_local_path>/.gald3r/tasks/open/taskNNN_*.md`
- TASKS.md row → appended to `<child_local_path>/.gald3r/TASKS.md`
- Inbox entry → `<child_local_path>/.gald3r/linking/INBOX.md` (audit trail only)
- Sent-orders record → controller's `.gald3r/linking/sent_orders/` (as before)

**Transitive authority (ADR-013)**: A controller can write to grandchildren (depth-2) and deeper through the parent-child tree. Each hop: confirm the intermediate parent is also in the manifest and accessible.

### Inbox-Only Fallback (remote or missing repo)

When the child's `local_path` is not on disk: write ONLY to the local sent-orders ledger and note `write_mode: inbox_pending`. The child will see the order in its inbox when next accessible.

### UUID generation

When direct-writing a task, generate a UUIDv4 for the `uuid:` frontmatter field. In PowerShell: `[System.Guid]::NewGuid().ToString()`.


   - If no children declared → warn: "No children in topology. Declare children in link_topology.md first."

2. **Determine target children**:
   - All children (default)
   - Children that `consumes` a specific service (e.g., "all oracle consumers")
   - Specific named children (user specifies)

3. **Collect broadcast details** (prompt if not provided):
   - **Title**: What needs to be done in child projects?
   - **Why**: Context — why is this needed? (critical for child sessions that won't have this context)
   - **Subsystems**: Which subsystems are affected?
   - **Cascade depth**: 1 (children only) | 2 (children + grandchildren) | 3 (three generations)
   - **Source task**: Task ID in this project that triggered the order (if exists)

4. **Conflict check before creating tasks**:
   - For each target child: check if an open broadcast for the same subsystem already exists
   - If conflict detected: create `[CONFLICT]` in child INBOX.md instead of a task
   - Warn user: "Conflict detected in [child-id] — added to their INBOX instead"
   - **NOTE**: `[INFO]` messages in the child INBOX do NOT trigger conflict detection
     (INFO is advisory only; only broadcast/request types are checked for conflicts)

5. **For each accessible target child**:

   a. Read `child/.gald3r/TASKS.md` to determine next available task ID

   b. Create task file at `child/.gald3r/tasks/taskNNN_[descriptive_name].md`:

   **WPAC-priority floor (T166)**: receiving-side tasks default to `priority: high`. If the source order metadata carries an urgency flag (`urgent: true`) OR the order arrived as a `[CONFLICT]` resolution, set `priority: critical` and force `requires_verification: true`. Always write a `wpac_source:` block (audit trail — never strip on status changes). Humans MAY downgrade priority manually after creation; agents MUST NOT auto-downgrade.

   ```yaml
   ---
   id: NNN
   title: '[Broadcast] [task title]'
   type: feature
   status: pending
   priority: high                        # critical when source order is urgent or conflict-derived
   requires_verification: true           # forced true for critical/WPAC-derived
   subsystems: [affected subsystems]
   project_context: '[Why this was broadcast from parent project]'
   depends_on: []
   created: 'YYYY-MM-DD'
   task_source: [this project_id]
   source_task_id: [source task id or null]
   delegation_type: broadcast
   cascade_depth_original: [depth]
   cascade_depth_remaining: [depth - 1]
   cascade_chain: [[this project_id]]
   cascade_forwarded: false
   wpac_source:
     type: order                         # order | ask | broadcast | sync | conflict
     source_project: [this project_id]
     inbox_ref: BCAST-XXX
   ---
   ```

   c. Append to `child/.gald3r/TASKS.md`:
   `- [WPAC][📋] **Task NNN**: [title] — broadcast from [this project]`
   - The `[WPAC]` prefix is render-only (regenerated from frontmatter `wpac_source:` block) — never hand-edit.

   d. Append to `child/.gald3r/linking/INBOX.md`:
   ```markdown
   ## [OPEN] BCAST-XXX — from: [this project] — YYYY-MM-DD
   **Type:** broadcast
   **Subject:** [title]
   **Why:** [context]
   **Task created:** taskNNN_[name].md
   **Cascade depth remaining:** [depth - 1]
   **Status:** task_created
   ```

   e. **Create local outbound order ledger record** at `.gald3r/linking/sent_orders/order_{YYYYMMDD-HHMMSS}_{child_project_id}_{task_slug}.md`:
   ```markdown
   ---
   order_id: "ord-{uuid-short}"            # 8-char uuid suffix is fine
   sent_to: "{child_project_id}"
   sent_to_path: "<path>/to/child"
   sent_at: "YYYY-MM-DD"
   local_depends: [task_id, ...]            # which LOCAL tasks/features gate on this
   remote_task_title: "[broadcast title]"
   remote_task_id: NNN                      # the child task id created in step b (direct-write) or the world_tree-assigned id (online)
   transport: file                          # file | world_tree — which delivery path actually ran (Step 0-T)
   task_uuid: ""                            # world_tree TaskIntakeResponse.task.id (T263) — ONLY set when transport: world_tree; "" for file-transport-only sends. Required for `gald3r valk order-status` to live-refresh this order — leave blank rather than guessing.
   status: sent                             # sent | acknowledged | in-progress | completed | blocked | timed-out | abandoned
   last_sync: "YYYY-MM-DD"
   broadcast_id: "BCAST-XXX"                # cross-link to INBOX entry
   ---

   # Order: [broadcast title]

   **Sent to**: {child_project_id} at {child_path}
   **Sent at**: YYYY-MM-DD
   **Remote task**: child task NNN — taskNNN_{slug}.md
   **Local dependents**: {task_ids that referenced this order via cross_project_ref}
   **Broadcast**: BCAST-XXX (see child INBOX.md)

   ## Sync History

   | Timestamp  | Status | Notes |
   |------------|--------|-------|
   | YYYY-MM-DD | sent   | Order dispatched + child task created (task_uuid: <uuid> when transport: world_tree) |
   ```

   - Ensure `.gald3r/linking/sent_orders/` exists; create if missing.
   - The `order_id` is the stable cross-reference used by `cross_project_ref:` on local tasks/features.
   - If any local task/feature was passed in via `--depends-on` or interactive prompt, append its ID to `local_depends:` AND write a `cross_project_ref:` entry on that local task/feature pointing back at this `order_id` (see `g-skl-tasks` and `g-skl-features` schemas).
   - **`task_uuid:` (T263)** — when Step 0-T's transport verdict was `ok`, set this to the exact `task.id` string from the `POST /api/v1/tasks/delegation/intake` response body (`TaskIntakeResponse.task.id`). This is what lets `gald3r valk order-status <order_id>` resolve a live `GET /api/v1/tasks/delegation/{task_id}` status instead of only ever reading this file's own cached `status:` field. Leave `task_uuid: ""` for file-transport-only sends (`offline`/`error`/`auth_required`/`upgrade_required` verdicts) — there is no world_tree-assigned id to record in that case, and `valk order-status` correctly falls back to this ledger's cached `status:` when the field is empty.

6. **If child path not accessible**: stage the order locally instead of dropping it
   - Write to `.gald3r/linking/pending_orders/order_[child_project_name]_[date].md`:
   ```markdown
   ---
   type: pending_order
   target_project: [child project name]
   target_path: [child path]
   created: YYYY-MM-DD
   broadcast_id: BCAST-XXX
   cascade_depth_remaining: N
   ---

   # Pending Order: [title]

   **Target**: [child_project_name] at [child_path]
   **Broadcast ID**: BCAST-XXX
   **Subject**: [title]
   **Why**: [context]
   **Cascade depth remaining**: N
   **Status**: pending_delivery

   ## Task to Create in Target

   [full task YAML that would have been written to child/.gald3r/tasks/]

   ## INBOX Entry to Append

   [full INBOX markdown that would have been appended to child INBOX.md]
   ```
   - Report: "📦 [child-project]: order staged in pending_orders/ — will deliver when accessible"
   - **Also create the outbound order ledger record** at `.gald3r/linking/sent_orders/order_{YYYYMMDD-HHMMSS}_{child_project_id}_{task_slug}.md` with the same frontmatter described in step 5e, but with:
     - `status: blocked` (target inaccessible — not yet delivered)
     - `remote_task_id: null` (will be filled when the staged order delivers and the child task ID is known)
     - Add a Sync History row: `| YYYY-MM-DD | blocked | Target path inaccessible — staged in pending_orders/ |`
   - When the staged order is later delivered (via Step 0 pre-flight), the same `sent_orders/` record is updated: `status: sent`, `remote_task_id: NNN` is filled in, and a new Sync History row is appended.

**Step 0 (pre-flight — runs before steps 1-6 above)**:
   - Check `.gald3r/linking/pending_orders/` for any staged orders with `Status: pending_delivery`
   - For each staged order where the target path is NOW accessible:
     - Deliver: create the task + append INBOX entry as described in step 5
     - Move staged file to `.gald3r/linking/pending_orders/delivered/`
     - **Update the matching `.gald3r/linking/sent_orders/` record**: set `status: sent`, fill `remote_task_id: NNN` (the child task ID just created), update `last_sync:`, append Sync History row `| YYYY-MM-DD | sent | Delivered from pending_orders staging |`
     - Report: "📨 Delivered staged order to [child_project]: [title]"
   - Check for duplicate: if BCAST ID already exists in child INBOX.md, skip (idempotent)

7. **No local tracking task** (T167 — was: "create local broadcast tracker task"):

   WPAC orders are tracked **exclusively** via the `.gald3r/linking/sent_orders/order_*.md` ledger written in step 5e (and step 6 fallback for staged orders). Do NOT create a local `[ ]`/`[📋]` "Broadcast tracker" task — children may never respond, and stale tracker tasks pollute the backlog forever.

   - **Outbound state lives on the ledger** — frontmatter `status:` (`sent` → `acknowledged` → `in-progress` → `completed` | `blocked` | `abandoned`) is the single source of truth.
   - **Session-start visibility** — `g-rl-25` Step 6b surfaces awaiting + resolved + stale orders at every session open. No local task is needed for the parent to see what's outstanding.
   - **Completion handling** — when a child sends a `broadcast_completion` ping, `g-skl-wpac-read` step 5 resolves the matching ledger entry (`status: completed`) and unblocks any local tasks/features whose `cross_project_ref:` points at the order_id. No tracker task to close.
   - **Stale-order policy** — orders in `sent`/`acknowledged` for >30 days with no Sync History update are flagged as stale at session start. The user can `@g-wpac-status --close <ord-id>` to formally abandon the order (writes `status: abandoned` + a final Sync History row). This replaces the "task that never completes" problem entirely.

   **The send itself is immediate** — calling this skill is a single atomic operation: write the ledger record, write the child task (if accessible) or stage to `pending_orders/`, append the INBOX entry, return. There is no queued-send task in this project.

8. **Report**:
   ```
   Order sent (cascade depth: N):
   ✅ [child-project]: taskNNN_[name] created
   ✅ [child-project]: taskNNN_[name] created
   ⚠️  [child-project]: path not accessible — manual delivery needed
   ⚠️  [child-project]: CONFLICT detected — added to INBOX instead

   Cascade: children will forward to grandchildren at next session open if depth > 1
   ```
