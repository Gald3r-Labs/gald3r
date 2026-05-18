---
name: g-skl-pcac-claim
description: Register another project as the parent of the current project. Creates or updates linking/link_topology.md on both sides when the parent is locally accessible.
---
# g-skl-pcac-claim

## When to Use
`@g-pcac-claim` command. When you want to establish a child→parent relationship from
this project up to another. Run from the **child** project. Mirror of `g-skl-pcac-adopt`.

## Arguments
```
@g-pcac-claim <parent_project_path> [--one-way]
```
- `parent_project_path` — absolute path to the parent project (e.g. `G:\gald3r_ecosystem\gald3r_master_control`)
- `--one-way` — update only THIS project's topology; skip writing to the parent (use when parent is remote or read-only)

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

### 5. Set parent in current project's topology

```yaml
parent:
  project_name: "<parent_project_name>"
  project_path: "<parent_project_path>"
  project_id: "<parent_project_id>"
role: "child"
```

Write updated `link_topology.md`.

### 6. Write peer copy
Write `peers/<parent_project_name>.md` in current project's `linking/peers/`:
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

g) Write `<parent_path>/.gald3r/linking/peers/<current_project_name>.md`:
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

Run @g-pcac-status to verify the full topology.
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
siblings: []          # populated by g-skl-pcac-sync
last_updated: "<YYYY-MM-DD>"
---
```

## Typical Usage Pattern

```
# In gald3r_dev (child project):
@g-pcac-claim G:\gald3r_ecosystem\gald3r_master_control

# This will:
#  1. Set gald3r_master_control as parent in gald3r_dev's topology ✓
#  2. Add gald3r_dev to gald3r_master_control's children[] ✓
#  3. Write peer copies in both projects ✓
```