---
name: g-skl-pcac-ask
description: Child project requests parent action — writes parent INBOX.md and marks local task as blocked with cross-project metadata.
---
# g-skl-pcac-ask

## When to Use
`@g-pcac-ask` command. When this project needs a parent project to DO something before work here can proceed.

## Steps

1. **Read `.gald3r/linking/link_topology.md`** — get parent info
   - If no parent declared → "No parent in topology. Declare a parent in link_topology.md first."

2. **Select target parent** (if multiple parents):
   - Which parent is being asked?
   - Which service/area does this request relate to? (helps parent route it)

3. **Collect request details** (prompt if not provided):
   - **What do you need the parent to do?** (specific action)
   - **Why?** (context — what local work does this unblock?)
   - **Local task being unblocked?** (optional — task ID of the local work that depends on this)

4. **Write to `parent/.gald3r/linking/INBOX.md`** (if path accessible):
   ```markdown
   ## [OPEN] REQ-XXX — from: [this project_id] — YYYY-MM-DD
   **Type:** request
   **Subject:** [brief title]
   **Detail:** [full description of what's needed]
   **Context:** [why this is needed, what it unblocks]
   **Local depends:** [this project]/.gald3r/tasks/taskNNN_[name].md (if any)
   **Status:** open
   ```

5. **Create outbound order ledger record (T167)** at `.gald3r/linking/sent_orders/order_{YYYYMMDD-HHMMSS}_{parent_project_id}_ask_{slug}.md`:
   ```yaml
   ---
   order_id: "ord-{uuid-short}"
   sent_to: "{parent_project_id}"
   sent_to_path: "G:/path/to/parent"
   sent_at: "YYYY-MM-DD"
   type: ask                                # T167: type discriminator (was implicit; now explicit)
   local_depends: [task_id, ...]            # which LOCAL tasks gate on the parent acting
   remote_task_title: "[ask subject]"
   remote_task_id: null                     # parent will fill if/when they action it
   status: sent                             # sent | acknowledged | in-progress | completed | blocked | abandoned
   last_sync: "YYYY-MM-DD"
   request_id: "REQ-XXX"                    # cross-link to parent INBOX entry
   ---

   # Ask: [subject]

   **Sent to**: {parent_project_id} at {parent_path}
   **Sent at**: YYYY-MM-DD
   **Local dependents**: {local task ids}
   **Request**: REQ-XXX (see parent INBOX.md)

   ## Sync History

   | Timestamp  | Status | Notes |
   |------------|--------|-------|
   | YYYY-MM-DD | sent   | Ask dispatched to parent INBOX |
   ```

   - For each `local_depends:` task ID, write a `cross_project_ref:` entry on that local task pointing at this `order_id`.
   - **Do NOT create a separate `[Waiting]` tracker task** (T167). Outbound state lives exclusively on the sent_orders ledger.

6. **If parent path not accessible**:
   - Save request details to a local staging file: `.gald3r/linking/pending_requests/req_[parent].md`
   - Still create the sent_orders ledger record with `status: blocked` (target inaccessible)
   - Warn: "Parent path not accessible. Request staged locally. Deliver manually or retry when parent path is accessible."

7. **Report**:
   ```
   Request sent:
   - Target parent: [parent_id]
   - INBOX entry: parent/.gald3r/linking/INBOX.md (REQ-XXX) ✅
   - Outbound ledger: .gald3r/linking/sent_orders/order_{...}.md (type: ask, status: sent) ✅
   - Local depends: {task IDs given cross_project_ref linkage}

   Outbound state is tracked via the sent_orders ledger — no local "[Waiting]" tracker task is created.
   Session-start (g-rl-25 Step 6b) surfaces awaiting orders automatically.
   ```

## When Parent Completes the Request

Parent will either:
- Write `parent_action_status: completed` directly to your task file (if they have path access)
- Or notify you via your INBOX.md

When `parent_action_status: completed` is set → change local task status from `blocked` to `pending` and proceed.

## Parent-Side Receipt (T166)

The parent project does **not** create the receiving task here — they create it via `g-skl-pcac-read` when they action the request. That receiving-side task gets `priority: high` by default per the PCAC-priority floor (T166), with `pcac_source: { type: ask, source_project: <child>, inbox_ref: REQ-XXX }` written to the task frontmatter for traceability. The parent agent must NOT auto-downgrade priority; humans may manually adjust it after the task lands.
