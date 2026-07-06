---
name: g-skl-wpac-read
description: Review and action all incoming cross-project coordination items — conflicts (block planning), requests from children, broadcasts from parents, and peer syncs from siblings.
token_budget: medium
subsystem_memberships: [WORKSPACE_COORDINATION]
---

> **Multi-agent framework (T1094):** Inbound handler — actions all inbound frameworks (delegation/broadcast/negotiation/conflict).
# g-skl-wpac-read

## When to Use
`@g-wpac-read` command. Session start when INBOX items exist. After receiving a cross-project task. After `g-hk-wpac-inbox-check.ps1` reports items.

## Inbox layout (T428)

The inbox is a lightweight **index** at `.gald3r/linking/INBOX.md` (marked `<!-- WPAC-INDEX-V1 -->`) backed by one file per message under `.gald3r/linking/messages/msg_{id}_{type}_{source}.md`. Each message file has YAML frontmatter (`id`, `type`, `source_project`, `subject`, `status`, `created_at`, `actioned_at`) plus the full body. Resolved messages are archived to `.gald3r/linking/messages/archive/` via `@g-wpac-archive-inbox`.

- **Read the index** for the row list (Status, ID, Type, Source, Subject, Age, File).
- **Open the linked message file** for full body when actioning an item.
- **Ack/update** = set the message file's `status:`/`actioned_at:` frontmatter AND flip the index row's status cell `[OPEN]` -> `[DONE]` in place.
- **Backward-compat (`--legacy`)**: if `INBOX.md` is still the legacy flat-body format (no `WPAC-INDEX-V1` marker), run `@g-wpac-archive-inbox` (which auto-migrates first) or `gald3r workspace inbox migrate` to convert it, then proceed. If `messages/` is absent, the inbox-check hook creates it silently.

## Steps

1. **Read `.gald3r/linking/INBOX.md`** (the index)
   - If empty or not exists → "INBOX clear — no cross-project items pending"
   - If still legacy flat-body format → migrate first (see Inbox layout above), then re-read
   - Categorize rows by Type: CONFLICT | request | broadcast | peer_sync | info

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
   - Record resolution in the message file body: `**Resolution:** [human's answer]` + `**Resolved by:** [date]`, and set its frontmatter `status: done` + `actioned_at`
   - Change the index row status cell from `[CONFLICT]` to `[DONE]`
   - If task was created for conflicted subsystem: update it with the resolution

4. **Handle REQUESTS** (child needs parent to act):
   - Show: who is asking, what they need, which task is blocking them
   - Offer: `Action (create task here) / Defer (keep open) / Reject (close with note)`
   - If actioned: create task in `.gald3r/tasks/` with reference to child's blocking task
     - **WPAC-priority floor (T166)**: tasks spawned from WPAC items default to `priority: high`. If the source INBOX item is `[CONFLICT]` or carries an explicit urgency flag (e.g., `urgent: true`), default to `priority: critical`. Pass `wpac_source: { type: order|ask|broadcast|sync|conflict, source_project: <name>, inbox_ref: <id> }` to `g-skl-tasks` CREATE TASK so the audit trail is preserved in the task frontmatter and TASKS.md gets the `[WPAC]` tag prefix. Critical (CONFLICT-derived) tasks must also force `requires_verification: true` — never skip verification on cross-project work. Humans MAY downgrade priority manually after creation; agents MUST NOT auto-downgrade.
   - If accessible: write `parent_action_status: completed` to child's task file
   - Mark INBOX entry `[DONE]`

5. **Handle BROADCASTS** (parent sent work):
   - Confirm the task created by `@g-wpac-order` exists in `.gald3r/tasks/`
   - If task missing: create it now from the INBOX entry details
   - Show task status and offer to start work
   - Check for `broadcast_completion` INFO subtypes: display alongside broadcasts as "✅ {title} completed [child_name]"
   - If `broadcast_completion` received:
     - Offer to mark the parent's tracker task `[✅]`
     - **Resolve the outbound order ledger record** (Layer 3 of cross-project dependency tracking):
       1. Search `.gald3r/workspace/sent_orders/order_*.md` for a record where `sent_to:` matches the sending child project AND (`remote_task_id:` matches the child's source task id from the completion ping, OR `remote_task_title:` matches the original broadcast title — exact string match preferred, fuzzy match as fallback)
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
   - Open the peer copy for review: `.gald3r/workspace/peers/{sibling_name}.md`
   - After human updates the contract: mark task complete, update INBOX to `[DONE]`
   - If sibling path accessible: write completion notice to sibling's INBOX.md

7. **Handle INFO items** (ℹ️ — no action required):
   - Display each INFO item with sender, subject, and detail
   - For `capability_update` subtypes: show the capability delta prominently:
     ```
     📡 Peer capability update from {sender}:
        {capability_name}: {old_status} → {new_status}
        Reason: {reason}
        Peer snapshot written to: .gald3r/workspace/peers/{sender}_capabilities.md
     ```
   - No task to create, no approval needed
   - Ask: "Acknowledge and mark done? [y/n]" (default: yes)
   - On acknowledgment: set the message file `status: done` + `actioned_at`, and flip the index row `[OPEN]` -> `[DONE]` (INFO/SYNC are also auto-actioned this way by the inbox-check hook)
   - Staging: after INBOX processing, report any pending staged info entries:
     "⚠️ N staged INFO notification(s) in pending_requests/ for [project] — not yet delivered"
   - Also check `pending_orders/` and surface count: "⚠️ N broadcast(s) staged in pending_orders/ for [project] — not yet accessible"

8. **Show peer capabilities summary** (after INBOX processing):
   - Read all files matching `.gald3r/workspace/peers/*_capabilities.md`
   - If any exist, display a compact table:
     ```
     Peer Capabilities (last received snapshots):
     ┌─────────────────────┬────────────────────────────────┬──────────────┐
     │ Project             │ Ready Capabilities              │ Last Updated │
     ├─────────────────────┼────────────────────────────────┼──────────────┤
     │ example_app      │ docker-backend, project-registry│ 2026-04-18   │
     └─────────────────────┴────────────────────────────────┴──────────────┘
     ```
   - If no peer snapshots exist: skip silently

9. **Update the index + message files** — set each reviewed message file's `status: done` + `actioned_at`, add resolution notes to its body, and flip the matching index row to `[DONE]`. When the active index carries more than 50 `[DONE]` rows, run `@g-wpac-archive-inbox` to keep it lean.

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
