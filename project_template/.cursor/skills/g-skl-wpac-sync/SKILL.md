---
name: g-skl-wpac-sync
description: Initiate or respond to sibling contract sync — advisory only, non-blocking. Both sides update local peer topology copies.
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

> **Multi-agent framework (T1094):** Negotiation — advisory sibling contract sync (net-positive, non-blocking).
# g-skl-wpac-sync

## When to Use
`@g-wpac-sync` command. When a shared contract with a sibling needs updating, or when responding to a SYNC item in INBOX.md.

## Key Principle
**Peer syncs are advisory.** Neither sibling has authority over the other. Work in this project proceeds regardless. The sync surfaces as an advisory in `@g-status` until resolved.

## Transport layer (WPAC-v2 — T1608)

**Step 0-T — transport verdict (code decides, never the model — g-rl-38).** When
initiating a sync, attempt an event publish before the file steps (T1609 shim
underneath):

```
gald3r workspace outbox send --verb event --payload-file <payload.json>
```

Payload = `PublishEventRequest` (`{"type": …, "project_id": …, "payload": {…}}`). The
world_tree event catalog is CLOSED; peer contract-sync has no catalogued type yet, so
the transport short-circuits to the `fallback` verdict client-side — the file steps
below are the delivery path today. When a catalogued type applies (e.g.
`release.published` for a released contract version), publish it.

| Verdict | Action |
|---|---|
| `ok` | Published to the org coordination log — siblings on realtime see it; STILL update the local peer copy (step 3–4). The sibling INBOX/task writes (steps 5–6) may be skipped. |
| `fallback` | Not catalogued — perform ALL file steps below (expected today). |
| `offline` / `error` | File steps below; queued entry reconciled by `gald3r workspace outbox flush` on reconnect. |
| `auth_required` / `upgrade_required` | File steps below (+ `gald3r login` hint / upgrade line). Entry parked (not retried). |

Everything below this section is the **OFFLINE / FILE FALLBACK transport** — the verb
surface (name + arguments) is unchanged.

## Steps

### Initiating a Sync (I changed a contract)

1. **Read `.gald3r/linking/link_topology.md`** — get siblings list
2. **Select target sibling and contract**
3. **Update local peer copy** at `.gald3r/linking/_peers/{sibling_name}.md`:
   - Bump version number
   - Update content (the spec that changed)
   - Update `last_synced` date
   - Set `sync_status: current` on your copy
4. **Include capabilities snapshot** — also copy this project's `capabilities.md` to sibling's `.gald3r/linking/_peers/{this_project_slug}_capabilities.md`:
   - Read `.gald3r/linking/capabilities.md`
   - Write a copy to `sibling/.gald3r/linking/_peers/{this_slug}_capabilities.md`
   - If sibling path not accessible: note in the INBOX notification that capabilities are attached
5. **Write to `sibling/.gald3r/linking/INBOX.md`** (if path accessible):
   ```markdown
   ## [OPEN] SYNC-XXX — from: [this project] — YYYY-MM-DD
   **Type:** peer_sync
   **Contract:** [contract_name]
   **Version:** [old] → [new]
   **Change:** [brief description of what changed and why]
   **Capabilities snapshot:** .gald3r/linking/_peers/[this_slug]_capabilities.md (written)
   **Your action:** Update your copy at `.gald3r/linking/_peers/[name].md`
   **Canonical spec path:** [this project]/.gald3r/linking/_peers/[name].md
   **Status:** action_needed
   ```
6. **Create task in sibling's `.gald3r/`** (if path accessible):
   ```yaml
   title: '[Peer Sync] Update [contract_name] from [this project] — v[new]'
   delegation_type: peer_sync
   peer_sync_partner: [this project_id]
   peer_sync_status: action_needed
   priority: high                            # T166: WPAC-derived priority floor
   wpac_source:
     type: sync
     source_project: [this project_id]
     inbox_ref: SYNC-XXX
   ```
   - The sibling-side task gets the WPAC-derived priority floor (T166) — `high` by default.

7. **No local sender-side tracker task (T167)**:

   The sender does NOT create a `[Peer Sync] Notified ... — awaiting ack` task. Outbound sync is fire-and-forget at the task level. Optionally record a sync-specific entry in the sent_orders ledger for traceability (`type: sync`, `status: sent`); but if you skip even that, the sibling's INBOX entry plus the local peer copy are sufficient audit trail. There is no project-side wait task.

8. **If sibling path not accessible**: stage the notification at `.gald3r/linking/pending_requests/sync_[sibling].md`

### Responding to a Sync (Sibling notified me)

1. **Read INBOX item** (`SYNC-XXX` in INBOX.md) or check the created task
2. **Read their updated contract** (if path accessible) at `sibling/.gald3r/linking/_peers/{name}.md`
3. **Check for capabilities snapshot** — if `sibling/.gald3r/linking/_peers/{this_slug}_capabilities.md` was written (or attached in INBOX), read it and confirm our local peer snapshot is current
4. **Update local peer copy** at `.gald3r/linking/_peers/{sibling_name}.md`:
   - Match their version number
   - Update content to match canonical
   - Set `sync_status: current`
5. **Close the local peer_sync task**: status → completed
6. **Mark INBOX item** `[DONE]`
7. **If sibling path accessible**: update their INBOX entry to note your sync is complete

### Report (both directions)
```
Peer sync complete:
- Contract: [name] — v[new]
- Local peer copy updated: .gald3r/linking/_peers/[sibling_name].md ✅
- Sibling notified/confirmed: [sibling_id] ✅
- Tasks created/closed ✅
```
