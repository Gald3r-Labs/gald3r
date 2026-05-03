---
name: g-skl-pcac-read
description: Review and action all incoming cross-project coordination items — conflicts (block planning), requests from children, broadcasts from parents, and peer syncs from siblings.
---
# g-skl-pcac-read

## When to Use
`@g-pcac-read` command. Session start when INBOX items exist. After receiving a cross-project task. After `g-hk-pcac-inbox-check.ps1` reports items.

## Steps

1. **Read `.gald3r/linking/INBOX.md`**
   - If empty or not exists → "INBOX clear — no cross-project items pending"
   - Categorize items: CONFLICT | request | broadcast | peer_sync | info

2. **Display grouped by urgency**:
   ```
   INBOX — [project_id]

   ⚠️  CONFLICTS (gate all work until resolved): N
   📨 REQUESTS from children needing parent action: N
   📢 BROADCASTS from parents (tasks already created): N
   🔄 PEER SYNCS from siblings (contract updates): N
   ℹ️  INFO (no action required): N
   ✅ DONE (recent, audit trail): N
   ```

3. **Handle CONFLICTS first** (⚠️ — these gate ALL work):
   - Show both conflicting instructions side by side
   - Show which subsystem is affected
   - Prompt human: "How to resolve? Options: Follow A / Follow B / Follow both / Ignore both / Custom"
   - Record resolution in INBOX.md: `**Resolution:** [human's answer]` + `**Resolved by:** [date]`
   - Change status from `[CONFLICT]` to `[DONE]`
   - If task was created for conflicted subsystem: update it with the resolution

4. **Handle REQUESTS** (child needs parent to act):
   - Show: who is asking, what they need, which task is blocking them
   - Offer: `Action (create task here) / Defer (keep open) / Reject (close with note)`
   - If actioned: create task in `.gald3r/tasks/` with reference to child's blocking task
     - **PCAC-priority floor (T166)**: tasks spawned from PCAC items default to `priority: high`. If the source INBOX item is `[CONFLICT]` or carries an explicit urgency flag (e.g., `urgent: true`), default to `priority: critical`. Pass `pcac_source: { type: order|ask|broadcast|sync|conflict, source_project: <name>, inbox_ref: <id> }` to `g-skl-tasks` CREATE TASK so the audit trail is preserved in the task frontmatter and TASKS.md gets the `[PCAC]` tag prefix. Critical (CONFLICT-derived) tasks must also force `requires_verification: true` — never skip verification on cross-project work. Humans MAY downgrade priority manually after creation; agents MUST NOT auto-downgrade.
   - If accessible: write `parent_action_status: completed` to child's task file
   - Mark INBOX entry `[DONE]`

5. **Handle BROADCASTS** (parent sent work):
   - Confirm the task created by `@g-pcac-order` exists in `.gald3r/tasks/`
   - If task missing: create it now from the INBOX entry details
   - Show task status and offer to start work
   - Check for `broadcast_completion` INFO subtypes: display alongside broadcasts as "✅ {title} completed [child_name]"
   - If `broadcast_completion` received:
     - Offer to mark the parent's tracker task `[✅]`
     - **Resolve the outbound order ledger record** (Layer 3 of cross-project dependency tracking):
       1. Search `.gald3r/linking/sent_orders/order_*.md` for a record where `sent_to:` matches the sending child project AND (`remote_task_id:` matches the child's source task id from the completion ping, OR `remote_task_title:` matches the original broadcast title — exact string match preferred, fuzzy match as fallback)
       2. If a matching record is found:
          - Update its frontmatter: `status: completed`, `last_sync: YYYY-MM-DD`
          - Append Sync History row: `| YYYY-MM-DD | completed | Completion ping received from {child_project_id} |`
          - Read the record's `local_depends:` array — for each local task/feature ID:
            - Open `.gald3r/tasks/task{id}_*.md` (or `.gald3r/features/feat{id}_*.md`)
            - Find the `cross_project_ref:` block where `order_id:` matches; update its `status: completed` and `last_synced: YYYY-MM-DD`
          - Surface to the user:
            ```
            🔗 Cross-project order resolved: ord-{shortid} ({child_project_id}: {remote_task_title})
               Local tasks/features now unblocked: {list of local IDs}
            ```
       3. If no matching record is found (legacy completion ping — order was sent before this feature existed): note it in the report and skip silently — no error.

6. **Handle PEER SYNCS** (sibling contract changed):
   - Show: which sibling, which contract, what changed
   - Confirm task exists (created when peer_sync arrived)
   - Open the peer copy for review: `.gald3r/linking/peers/{sibling_name}.md`
   - After human updates the contract: mark task complete, update INBOX to `[DONE]`
   - If sibling path accessible: write completion notice to sibling's INBOX.md

7. **Handle INFO items** (ℹ️ — no action required):
   - Display each INFO item with sender, subject, and detail
   - For `capability_update` subtypes: show the capability delta prominently:
     ```
     📡 Peer capability update from {sender}:
        {capability_name}: {old_status} → {new_status}
        Reason: {reason}
        Peer snapshot written to: .gald3r/linking/peers/{sender}_capabilities.md
     ```
   - No task to create, no approval needed
   - Ask: "Acknowledge and mark done? [y/n]" (default: yes)
   - On acknowledgment: change `[OPEN]` to `[DONE]` in INBOX.md
   - Staging: after INBOX processing, report any pending staged info entries:
     "⚠️ N staged INFO notification(s) in pending_requests/ for [project] — not yet delivered"
   - Also check `pending_orders/` and surface count: "⚠️ N broadcast(s) staged in pending_orders/ for [project] — not yet accessible"

8. **Show peer capabilities summary** (after INBOX processing):
   - Read all files matching `.gald3r/linking/peers/*_capabilities.md`
   - If any exist, display a compact table:
     ```
     Peer Capabilities (last received snapshots):
     ┌─────────────────────┬────────────────────────────────┬──────────────┐
     │ Project             │ Ready Capabilities              │ Last Updated │
     ├─────────────────────┼────────────────────────────────┼──────────────┤
     │ gald3r_valhalla      │ docker-backend, project-registry│ 2026-04-18   │
     └─────────────────────┴────────────────────────────────┴──────────────┘
     ```
   - If no peer snapshots exist: skip silently

9. **Update INBOX.md** — change reviewed items to `[DONE]`, add resolution notes

10. **Report**:
   ```
   INBOX processed:
   - 1 conflict resolved ✅
   - 2 requests actioned (tasks created) ✅
   - 1 peer sync completed ✅
   - 0 broadcasts pending
   - 3 INFO items acknowledged ✅
   INBOX clear ✅
   ```
