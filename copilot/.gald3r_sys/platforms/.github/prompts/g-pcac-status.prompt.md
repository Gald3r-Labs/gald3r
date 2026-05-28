Show cross-project coordination status: $ARGUMENTS

## What This Command Does

Displays the full PCAC (Project Command and Control) status: this project's topology role, linked project health, open INBOX summary, and constraint overlap with peers. Delegates to `g-agnt-pcac-coordinator`.

## Output Format

```
PCAC STATUS — {project_name}
────────────────────────────────────────
Role: {parent | child | sibling | standalone}
Project: {project_path}

Parent: {name} at {path} [accessible ✅ | inaccessible ⚠️ | none]

Children ({N}):
  - {name} at {path} [accessible ✅ | inaccessible ⚠️]

Siblings ({N}):
  - {name} at {path} [accessible ✅ | inaccessible ⚠️]

────────────────────────────────────────
INBOX: {N open items}
  {c} conflicts  ⚠️  (BLOCKS all other coordination work)
  {r} requests
  {b} broadcasts
  {s} syncs

────────────────────────────────────────
LOCAL CAPABILITIES
  Responsibilities: {N ready}
  Capabilities: {N ready}, {N planned}, {N deprecated}
  (Full manifest: .gald3r/linking/capabilities.md)

PEER CAPABILITIES (last received snapshots)
  {peer_name}: {N ready capabilities} — last updated {date}
  {peer_name}: no snapshot yet ⚠️

────────────────────────────────────────
CROSS-PROJECT DEPENDENCIES

### Awaiting (parent waiting on child)
| Order ID   | Sent To        | Remote Task                  | Status      | Days Out |
|------------|----------------|------------------------------|-------------|----------|
| ord-abc123 | gald3r_valhalla | Implement JWT auth endpoint  | in-progress | 3        |

### Blocking (this project has received orders blocking a parent)
| Order ID   | From Parent   | Our Local Task        | Status      |
|------------|---------------|-----------------------|-------------|
| ord-xyz789 | gald3r_dev    | vault-sync endpoint   | in-progress |

────────────────────────────────────────
CONSTRAINT OVERLAP
  This project: {N total} ({N ecosystem-wide}, {N inheritable})
  Parent has: {N ecosystem-wide constraints} — {N missing from this project} ⚠️ [or "— in sync ✅"]
  Inherited constraints: {N} (from {source_project})
  Action: [none needed | run @g-pcac-sync to inherit N missing constraints]
────────────────────────────────────────
```

## Workflow

### 1. Load Topology
Read `.gald3r/linking/link_topology.md`.

If missing → "Topology not configured. Complete task007 to set up the linking/ directory."

### 2. Check Project Accessibility
For each linked project, check if path is accessible on the current machine.

### 3. Read INBOX
Read `.gald3r/linking/INBOX.md` and count items by type.

### 4. Read Local Capabilities
Read `.gald3r/linking/capabilities.md` if it exists. Count ready responsibilities, ready/planned/deprecated capabilities.
If missing → "(capabilities.md not found — run @g-pcac-read or create it)"

### 5. Read Peer Capability Snapshots
Read all files matching `.gald3r/linking/peers/*_capabilities.md`. For each: extract project slug, count ready capabilities, get last_updated date.

### 6. Cross-Project Dependencies Check

**Awaiting** (this project has dispatched orders to children/peers):
1. List `.gald3r/linking/sent_orders/order_*.md`
2. For each: read frontmatter — extract `order_id`, `sent_to`, `remote_task_title`, `status`, `sent_at`, `last_sync`
3. Filter to records where `status` ∈ {`sent`, `acknowledged`, `in-progress`, `blocked`} (i.e., not `completed` or `timed-out`)
4. Compute `days_out` = today − `sent_at`
5. If non-empty: render the **Awaiting** table; otherwise display: `(no awaiting cross-project dependencies)`

**Blocking** (this project has accepted orders from a parent that have local tasks gating on them):
1. Scan `.gald3r/tasks/task*.md` and `.gald3r/features/feat*.md` for any file with a `cross_project_ref:` array
2. For each entry where `status ≠ completed`: extract `order_id`, `project` (the parent that sent the order), the local task/feature title, and the cached `status`
3. Render the **Blocking** table; otherwise display: `(no blocking cross-project dependencies)`

Skip silently when both folders are empty / no `cross_project_ref:` fields exist.

### 7. Constraint Overlap Check
1. Read local `CONSTRAINTS.md` — count ecosystem-wide and inheritable constraints
2. If parent is accessible: read parent's `CONSTRAINTS.md` — find ecosystem-wide constraints not present in local file
3. Count constraints with `**Inherited from**:` field (already propagated from peers)
4. If any parent ecosystem-wide constraints are missing locally: show count + recommendation

Skip silently if parent is inaccessible or CONSTRAINTS.md has no `**Scope**:` fields.

### 8. Report
Display the full status block above. If CONFLICTs exist, recommend running `@g-pcac-read` immediately.

## Usage Examples

```
@g-pcac-status
```

## Delegates To
`g-agnt-pcac-coordinator`
