---
name: g-skl-wpac-claim
description: Register another project as the parent of the current project. Creates or updates linking/link_topology.md on both sides when the parent is locally accessible.
token_budget: low
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

> **Multi-agent framework (T1094):** Topology registration — registers a parent; enables receiving Delegation/Broadcast.
# g-skl-wpac-claim

## When to Use
`@g-wpac-claim` command. When you want to establish a child→parent relationship from
this project up to another. Run from the **child** project. Mirror of `g-skl-wpac-adopt`.

## Arguments
```
@g-wpac-claim <parent_project_path> [--one-way]
```
- `parent_project_path` — absolute path to the parent project (e.g. `<workspace>\<master_control>`)
- `--one-way` — update only THIS project's topology; skip writing to the parent (use when parent is remote or read-only)

## Transport layer (WPAC-v2 — T1608)

**Step 0-T — register the edge in the world_tree linking registry (T1625; code decides,
never the model — g-rl-38).** After reading both identities (steps 1–2), when BOTH
projects carry a registered `project_id` UUID in `.gald3r/.identity`, run:

```
gald3r workspace outbox send --verb link \
    --project-uuid <this_project_id> \
    --payload '{"target_project_id": "<parent_project_id>", "relation": "parent"}'
```

| Verdict | Action |
|---|---|
| `ok` | Edge registered server-side (`POST /api/v1/projects/{id}/links`) — the registry is the online source of truth. **T255: `gald3r workspace outbox send --verb link` now auto-refreshes the D7 linking mirror (`.gald3r/linking/link_topology.md` / `link_registry.json`) itself on `ok`** by chaining a `gald3r workspace pull` immediately after the edge is accepted — no separate manual pull needed for this edge. Note `transport: world_tree` in the confirm output. |
| `error` with HTTP 409 | Edge/parent already registered server-side — treat as the "Already claimed" idempotent case; continue the WPAC-v1 file-topology writes below. |
| `offline` / other `error` | Local file topology (below) is authoritative offline; the queued entry is reconciled by `gald3r workspace outbox flush` on reconnect. |
| `auth_required` / `upgrade_required` | File topology below (+ `gald3r login` hint / upgrade line — server linking is paid-Team gated; file topology stays free). Entry parked (not retried). |

The local `link_topology.md` / peers writes below ALWAYS run — this is the
legacy WPAC-v1 file topology (prose-driven, no Python backing), a distinct,
older write path from the **D7 linking mirror** (`.gald3r/linking/link_topology.md`
as refreshed by `gald3r workspace pull|status` / `g-skl-linking` — see that
skill's "Relationship to other skills" table). Reserve the term "linking
mirror" for that D7 surface only; do not call the WPAC-v1 steps below "a
mirror" (T261 — avoids the naming collision found during T255). The verb
surface (name + arguments) is unchanged. **T255 canonical path**:
`wpac_transport`'s `link` verb is the ONE way to register an edge
server-side; `linking_mirror`'s `pull`/`status` (reused automatically above
on `ok`, and directly via `gald3r workspace pull` at any other time) is the
ONE way the D7 linking mirror gets written. Neither is deprecated — they own
disjoint state and this skill chains them.

## Steps

### 1. Read current project identity
Read `.gald3r/.identity`:
- `project_id`, `project_name`, `project_path`

If `.gald3r/.identity` not found → stop: "No .gald3r/ found. Run @g-setup first."

### 2. Read parent project identity
Read `<parent_path>/.gald3r/.identity`:
- `project_id`, `project_name`

If parent `.identity` not found:
- If `--one-way` NOT set → stop: "Parent has no .gald3r/.identity. Ensure parent has gald3r installed, or use --one-way."
- If `--one-way` → prompt for parent `project_name` and `project_id` manually, continue

### 3. Ensure linking/ exists in current project
```
.gald3r/linking/
  link_topology.md  ← create if missing
  INBOX.md             ← create if missing
  README.md            ← create if missing
  peers/               ← create if missing
```

If `link_topology.md` already exists: read it, parse YAML frontmatter.
If missing: initialize with current project's identity, role=child.

### 4. Check for existing parent (conflict guard)

If `parent` is already set in current topology AND differs from the new parent:
```
⚠️  This project already has a parent: <existing_parent_name> (<existing_parent_path>)
    Overwrite with: <new_parent_name>? (y/n)
```
Wait for confirmation before proceeding.

### 5. Set parent in current project's topology (BUG-231/T445 -- prefer the CLI verb)

**Preferred: `gald3r workspace topology write` (T445).** Atomically writes `link_topology.md`
AND `workspace_manifest.yaml`'s `wpac_relationship:` block AND `.gald3r/.identity`'s
`wpac_role=` line from ONE JSON payload, in a single call -- this is the CLI wiring of
`gald3r_core.server_bridge.wpac_claim.linking_mirror.write_local_topology()`, so BUG-231's
two-files-two-stories drift is code-enforced, not prose-enforced. Read the CURRENT
`children[]`/`siblings[]` from `link_topology.md` first (if it exists) and include them verbatim
-- this call is a full write, not a merge:

```powershell
gald3r workspace topology write --payload '{
  "role": "child",
  "project_id": "<current_project_id>",
  "project_name": "<current_project_name>",
  "project_path": "<current_project_path>",
  "parent": {
    "project_name": "<parent_project_name>",
    "project_path": "<parent_project_path>",
    "project_id": "<parent_project_id>"
  }
}'
```

Use `--project-root <path>` if not run from the current project's own root, `--payload-file
<path>` for a larger/pre-built JSON file, and `--json` for a machine-readable verdict. Pass
through any existing `children`/`siblings` fields unchanged (omit a field to default it to
`[]`).

**Manual fallback (only if the CLI verb is unavailable).** Set `parent` and `role: "child"`
directly in `link_topology.md`:

```yaml
parent:
  project_name: "<parent_project_name>"
  project_path: "<parent_project_path>"
  project_id: "<parent_project_id>"
role: "child"
```

Write updated `link_topology.md`, then proceed to Step 5.5 to sync `workspace_manifest.yaml` by
hand -- the manual path is two separate writes and does not carry the CLI verb's atomicity
guarantee.

### 5.5. Sync current project's workspace_manifest.yaml -- manual-fallback path only (BUG-231)

Skip this step entirely when Step 5 used `gald3r workspace topology write` -- that call already
wrote this file (and `.gald3r/.identity`) in the same atomic operation. This step exists only for
the manual fallback: if `<current_project_path>/.gald3r/linking/workspace_manifest.yaml` exists,
update its `wpac_relationship:` block to match what the manual Step 5 write just wrote — same
`role`, same `parent` (`project_name`/`project_path`/`project_id`), leaving every other manifest
section (`repositories:`, `routing_policy:`, etc.) untouched:

```yaml
wpac_relationship:
  role: "child"
  parent:
    project_name: "<parent_project_name>"
    project_path: "<parent_project_path>"
    project_id: "<parent_project_id>"
  children: []       # preserve existing children[] verbatim
  siblings: []        # preserve existing siblings[] verbatim
```

If the manifest does not exist, skip silently (not every project is a Workspace-Control
controller).

### 6. Write peer copy
Write `_peers/<parent_project_name>.md` in current project's `linking/_peers/`:
```markdown
# Peer: <parent_project_name>
relationship: parent
project_path: <parent_project_path>
project_id: <parent_project_id>
claimed: <today_date>
```

### 7. Update parent project's topology (bidirectional, skip if --one-way)

If parent path is accessible:

a) Create `<parent_path>/.gald3r/linking/` if missing (+ INBOX.md, README.md, peers/)

b) Read or initialize `<parent_path>/.gald3r/linking/link_topology.md`

c) Check if current project already in parent's `children[]`. If yes → skip.

d) Add to parent's `children[]`:
```yaml
children:
  - project_name: "<current_project_name>"
    project_path: "<current_project_path>"
    project_id: "<current_project_id>"
```

e) If parent has no `role` set → set `role: "parent"`.

f) Write updated parent topology.

f.5) Sync parent's `workspace_manifest.yaml` (BUG-231, same rule as Step 5.5): if
`<parent_path>/.gald3r/linking/workspace_manifest.yaml` exists, update its `wpac_relationship:`
block's `children[]` (and `role`, if it changed in step e) to match what step f just wrote.
Skip silently if the parent has no manifest. Same preference as Step 5: `gald3r workspace
topology write --project-root <parent_path> --payload '{"role": "parent", "children": [...]}'`
performs steps d/e/f/f.5 atomically in one call when the parent is locally reachable; the manual
per-file edits above remain the fallback.

g) Write `<parent_path>/.gald3r/linking/_peers/<current_project_name>.md`:
```markdown
# Peer: <current_project_name>
relationship: child
project_path: <current_project_path>
project_id: <current_project_id>
claimed: <today_date>
```

### 8. Offer ecosystem-wide constraint sync

After topology link is established, offer to sync `ecosystem-wide` constraints from the parent:

1. Read `ecosystem-wide` and `inheritable` constraints from parent project's `CONSTRAINTS.md`
2. If parent has constraints current project lacks:
   ```
   Parent <parent_project_name> has N constraints eligible for propagation:
     C-001 [file-first-vault] (ecosystem-wide)
     C-007 [no-secrets] (ecosystem-wide)
     C-003 [path-via-identity] (inheritable)
   Inherit these N constraints? [y/n/select]
   ```
3. If **y**: copy constraints to current project's `CONSTRAINTS.md` with `**Inherited from**: <parent_name> (propagated <date>)`
4. `ecosystem-wide` constraints are pre-selected; `inheritable` are offered but not pre-selected
5. **Skip silently** if parent's `CONSTRAINTS.md` has no `**Scope**:` fields (backward compatible)

### 9. Confirm
```
CLAIMED ✓
  Child   : <current_project_name> (<current_project_path>)
  Parent  : <parent_project_name> (<parent_project_path>)
  Updated : <current_project_path>/.gald3r/linking/link_topology.md
  Updated : <parent_project_path>/.gald3r/linking/link_topology.md  [or "skipped (--one-way)"]

Run @g-wpac-status to verify the full topology.
```

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Parent already set (same) | Print "Already claimed — no changes made" |
| Parent already set (different) | Warn and prompt for confirmation |
| Parent has no `.gald3r/` | Stop with instructions (unless `--one-way`) |
| Parent path doesn't exist | Stop: "Path not found: <path>" |
| Parent already has this project as a child | Silently skip the children[] update (idempotent) |
| Running from a project already a parent | Note: "This project has children. You are creating a grandparent relationship." |

## Topology File Format Reference

```yaml
---
project_id: "<uuid or slug>"
project_name: "<name>"
project_path: "<absolute path>"
role: "child"         # parent | child | root | standalone
description: "<one line>"
parent:
  project_name: "<name>"
  project_path: "<path>"
  project_id: "<id>"
children: []
siblings: []          # populated by g-skl-wpac-sync
last_updated: "<YYYY-MM-DD>"
---
```

## Typical Usage Pattern

```
# In <gald3r_source> (child project):
@g-wpac-claim <workspace>\<master_control>

# This will:
#  1. Set <master_control> as parent in <gald3r_source>'s topology ✓
#  2. Add <gald3r_source> to <master_control>'s children[] ✓
#  3. Write peer copies in both projects ✓
```