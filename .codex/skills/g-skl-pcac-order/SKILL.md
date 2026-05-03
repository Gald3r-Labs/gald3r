---
name: g-skl-pcac-order
description: As a parent project, push a task to one or more child projects with configurable cascade depth (1–3). Creates tasks in child .gald3r/ folders and an INBOX notification.
---
# g-skl-pcac-order

## When to Use
`@g-pcac-order` command. When a change in this project requires action in child projects.

## Steps

1. **Read `.gald3r/linking/link_topology.md`** — get children list
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

   **PCAC-priority floor (T166)**: receiving-side tasks default to `priority: high`. If the source order metadata carries an urgency flag (`urgent: true`) OR the order arrived as a `[CONFLICT]` resolution, set `priority: critical` and force `requires_verification: true`. Always write a `pcac_source:` block (audit trail — never strip on status changes). Humans MAY downgrade priority manually after creation; agents MUST NOT auto-downgrade.

   ```yaml
   ---
   id: NNN
   title: '[Broadcast] [task title]'
   type: feature
   status: pending
   priority: high                        # critical when source order is urgent or conflict-derived
   requires_verification: true           # forced true for critical/PCAC-derived
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
   pcac_source:
     type: order                         # order | ask | broadcast | sync | conflict
     source_project: [this project_id]
     inbox_ref: BCAST-XXX
   ---
   ```

   c. Append to `child/.gald3r/TASKS.md`:
   `- [PCAC][📋] **Task NNN**: [title] — broadcast from [this project]`
   - The `[PCAC]` prefix is render-only (regenerated from frontmatter `pcac_source:` block) — never hand-edit.

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
   sent_to_path: "G:/path/to/child"
   sent_at: "YYYY-MM-DD"
   local_depends: [task_id, ...]            # which LOCAL tasks/features gate on this
   remote_task_title: "[broadcast title]"
   remote_task_id: NNN                      # the child task id created in step b
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
   | YYYY-MM-DD | sent   | Order dispatched + child task created |
   ```

   - Ensure `.gald3r/linking/sent_orders/` exists; create if missing.
   - The `order_id` is the stable cross-reference used by `cross_project_ref:` on local tasks/features.
   - If any local task/feature was passed in via `--depends-on` or interactive prompt, append its ID to `local_depends:` AND write a `cross_project_ref:` entry on that local task/feature pointing back at this `order_id` (see `g-skl-tasks` and `g-skl-features` schemas).

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

   PCAC orders are tracked **exclusively** via the `.gald3r/linking/sent_orders/order_*.md` ledger written in step 5e (and step 6 fallback for staged orders). Do NOT create a local `[ ]`/`[📋]` "Broadcast tracker" task — children may never respond, and stale tracker tasks pollute the backlog forever.

   - **Outbound state lives on the ledger** — frontmatter `status:` (`sent` → `acknowledged` → `in-progress` → `completed` | `blocked` | `abandoned`) is the single source of truth.
   - **Session-start visibility** — `g-rl-25` Step 6b surfaces awaiting + resolved + stale orders at every session open. No local task is needed for the parent to see what's outstanding.
   - **Completion handling** — when a child sends a `broadcast_completion` ping, `g-skl-pcac-read` step 5 resolves the matching ledger entry (`status: completed`) and unblocks any local tasks/features whose `cross_project_ref:` points at the order_id. No tracker task to close.
   - **Stale-order policy** — orders in `sent`/`acknowledged` for >30 days with no Sync History update are flagged as stale at session start. The user can `@g-pcac-status --close <ord-id>` to formally abandon the order (writes `status: abandoned` + a final Sync History row). This replaces the "task that never completes" problem entirely.

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
