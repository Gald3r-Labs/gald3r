---
name: g-skl-wpac-adopt
description: Register another project as a child of the current project. Creates or updates workspace/topology.md on both sides when the target is locally accessible.
token_budget: low
subsystem_memberships: [WORKSPACE_COORDINATION]
---

> **Multi-agent framework (T1094):** Topology registration — registers a child; enables Delegation/Broadcast to it.
# g-skl-wpac-adopt

## When to Use
`@g-wpac-adopt` command. When you want to establish a parent→child relationship between
this project and another. Run from the **parent** project. Mirror of `g-skl-wpac-claim`.

## Arguments
```
@g-wpac-adopt <target_project_path> [--one-way]
```
- `target_project_path` — absolute path to the child project (e.g. `<workspace>\child_project`)
- `--one-way` — update only THIS project's topology; skip writing to the target (use when target is remote or read-only)

## Steps

### 1. Read current project identity
Read `.gald3r/.identity`:
- `project_id`, `project_name`, `project_path` (use `cwd` if path not in .identity)

If `.gald3r/.identity` not found → stop: "No .gald3r/ found. Run @g-setup first."

### 2. Read target project identity
Read `<target_path>/.gald3r/.identity`:
- `project_id`, `project_name`

If target `.identity` not found:
- If `--one-way` NOT set → stop: "Target has no .gald3r/.identity. Ensure target has gald3r installed, or use --one-way."
- If `--one-way` → prompt for target `project_name` and `project_id` manually, continue

### 2.5 Workspace-Control member-repo guard (BUG-021 / Task 213 v1.1 / g-rl-36)

`g-wpac-adopt` writes to `<target_path>/.gald3r/workspace/` when the target is locally accessible (Step 6 below). `workspace/` is forbidden in Workspace-Control member `.gald3r/` — only `.identity` and `PROJECT.md` are marker-safe. If the target is a Workspace-Control controlled_member or migration_source registered in any ancestor `workspace_manifest.yaml`, the target write must be skipped.

Run the guard helper against the target path **before** any write into the target's `.gald3r/`. Use `-DotGald3rPath linking/` to evaluate the specific path WPAC adopt would write:

```powershell
gald3r workspace member guard --target-path "<target_project_path>" --dot-gald3r-path "linking/"
```

- exit `0` — target is not a member (or is the control project / outside workspace / template); bidirectional adoption proceeds normally.
- exit `1` — target is a member; `workspace/` is control plane and forbidden. Switch to `--one-way` automatically and skip Step 6 (target write). Record `BLOCK wpac_adopt_member_repo_gald3r_guard_block` in the session summary, plus the matched repo id/role. Suggest `@g-wrkspc-adopt` for Workspace-Control adoption, which routes coordination through the workspace controller's manifest instead of writing WPAC topology into the member.
- exit `2` — stop with `BLOCK wpac_adopt_member_repo_gald3r_guard_error` and direct the user to fix the manifest.

The current project's own `.gald3r/workspace/` updates (Steps 3-5 below) are unaffected; the guard applies only to the target write.

### 3. Ensure linking/ exists in current project
```
.gald3r/workspace/
  link_topology.md  ← create if missing
  INBOX.md             ← create if missing
  README.md            ← create if missing
  peers/               ← create if missing
```

If `link_topology.md` already exists: read it, parse YAML frontmatter.
If missing: initialize with current project's identity, role=parent, children=[], siblings=[].

### 4. Add child entry to current project's topology

Check if target is already listed in `children[]`. If yes → print "Already adopted" and skip.

Add to `children[]`:
```yaml
children:
  - project_name: "<target_project_name>"
    project_path: "<target_project_path>"
    project_id: "<target_project_id>"
```

Set `role: "parent"` if not already set (or `role: "root"` if no parent defined).

Write updated `link_topology.md`.

### 5. Write peer copy
Write `peers/<target_project_name>.md` in current project's `workspace/peers/` folder:
```markdown
# Peer: <target_project_name>
relationship: child
project_path: <target_project_path>
project_id: <target_project_id>
adopted: <today_date>
```

### 6. Update target project's topology (bidirectional, skip if --one-way)

If target path is accessible:

a) Create `<target_path>/.gald3r/workspace/` if missing (+ INBOX.md, README.md, peers/)

b) Read or initialize `<target_path>/.gald3r/workspace/topology.md`

c) Set `parent` in target's topology:
```yaml
parent:
  project_name: "<current_project_name>"
  project_path: "<current_project_path>"
  project_id: "<current_project_id>"
```

d) Set `role: "child"` in target's topology.

e) Write updated topology.

f) Write `<target_path>/.gald3r/workspace/peers/<current_project_name>.md`:
```markdown
# Peer: <current_project_name>
relationship: parent
project_path: <current_project_path>
project_id: <current_project_id>
adopted: <today_date>
```

### 6.5 Deploy full framework when target is an autonomous_child (T1452)

If the adopted target is an `autonomous_child` (independent gald3r project, not a marker-only
`controlled_member`), it MUST have the **complete** gald3r framework, not just `.gald3r/`. When the
target is missing any of `.claude/`, `.cursor/`, `.gald3r_sys/`, or root docs (`CLAUDE.md`,
`AGENTS.md`, `WORKFLOW.md`, `GUARDRAILS.md`), run (or instruct the user to run) the full installer
on the target path:

```powershell
# $targetPath = <target_project_path>
& "<<template_adv>_root>\setup_gald3r_project.ps1" -TargetPath $targetPath -Platforms cursor,claude
```

- `setup_gald3r_project.ps1` lives at the root of any `<template_adv>` install
  (`<template_adv_root>\setup_gald3r_project.ps1`); if this project was installed from an adv
  template the same script is already present at this project's root -- reuse it.
- Match the platforms the parent project uses (read from the parent's installed IDE dirs).
- Skip this step for `controlled_member` targets -- they stay marker-only (`.identity` + `PROJECT.md`).
  Use Workspace-Control `@g-wrkspc-adopt` for member adoption; promote first via `@g-wpac-promote`
  if the member should become an `autonomous_child`.
- Verify before confirming: `Test-Path` `.claude/`, `.cursor/`, `.gald3r_sys/`, `CLAUDE.md` on the target.

### 7. Notify existing siblings (skip if no existing children)

After the main adoption is complete, update all **other existing children** of the current parent
so they know about the new sibling:

For each existing child in `children[]` (excluding the newly adopted child):

**a) Write new sibling peer snapshot** in the existing child's peers/:
```markdown
# Peer: <new_child_project_name>
relationship: sibling
project_path: <new_child_project_path>
project_id: <new_child_project_id>
registered: <today_date>
```
Write to: `<existing_child_path>/.gald3r/workspace/peers/<new_child_project_name>.md`

Also write in the new child's peers/:
```markdown
# Peer: <existing_child_project_name>
relationship: sibling
project_path: <existing_child_project_path>
project_id: <existing_child_project_id>
registered: <today_date>
```
Write to: `<new_child_path>/.gald3r/workspace/peers/<existing_child_project_name>.md`

**b) Update existing child's link_topology.md** siblings section:
- Add new_child row to the `siblings[]` table (create the array if missing)

**c) Update new child's link_topology.md** siblings section:
- Add all existing children to its `siblings[]` array

**d) Post SYNC INBOX message** to each existing child's INBOX.md:
```markdown
## [SYNC] - New sibling registered - <today_date>
- **<new_child_project_name>** adopted under <current_project_name> on <today_date>
- Peer snapshot written to `workspace/peers/<new_child_project_name>.md`
- Run `@g-wpac-sync` to review and acknowledge
```

Skip this step if the existing child's path is inaccessible — log the skip in the confirm output.

### 8. Check for staged orders

Before confirming, check if `pending_orders/` contains any orders staged for the newly adopted child:

- Scan `.gald3r/workspace/pending_orders/` for files matching `order_[new_child_project_name]_*.md`
- If found: "📦 N staged order(s) found for [new_child_name]. Deliver now? [y/n]"
- If yes: deliver each staged order (create task + append INBOX) and move to `pending_orders/delivered/`
- If no: leave staged; `g-skl-wpac-order` will deliver at next run

### 9. Offer ecosystem-wide constraint sync

After topology link is established, offer to sync `ecosystem-wide` constraints bidirectionally:

1. Read `ecosystem-wide` constraints from current project's `CONSTRAINTS.md`
2. Read `ecosystem-wide` constraints from target project's `CONSTRAINTS.md` (skip if `--one-way`)
3. If there are constraints in scope that the target lacks:
   ```
   Current project has N ecosystem-wide constraints the child doesn't have yet:
     C-001 [file-first-vault] (ecosystem-wide)
     C-007 [no-secrets] (ecosystem-wide)
   Propagate these to <target_project_name>? [y/n]
   ```
4. If **y**: copy constraints to target's `CONSTRAINTS.md` with `**Inherited from**:` field
5. Reverse check: if target has `ecosystem-wide` constraints current project lacks, offer to sync those too
6. **Skip silently** if both projects are missing `**Scope**:` fields (backward compatible)

### 10. Confirm
```
ADOPTED ✓
  Parent  : <current_project_name> (<current_project_path>)
  Child   : <target_project_name> (<target_project_path>)
  Updated : <current_project_path>/.gald3r/workspace/topology.md
  Updated : <target_project_path>/.gald3r/workspace/topology.md  [or "skipped (--one-way)"]
  Siblings notified: <list of existing child names> [or "none — first child"]

Run @g-wpac-status to verify the full topology.
```

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Child already in topology | Print "Already adopted — no changes made" |
| Target has no `.gald3r/` | Stop with instructions (unless `--one-way`) |
| Target path doesn't exist | Stop: "Path not found: <path>" |
| Current project has no parent set | Set `role: "parent"` (or leave as-is if role already defined) |
| Target already has a different parent | Warn: "Target already has parent: <existing_parent>. Overwrite? (y/n)" — wait for confirmation |
| Running from a child project | Note: "This project is currently a child. You are creating a grandchild relationship." |

## Topology File Format Reference

```yaml
---
project_id: "<uuid or slug>"
project_name: "<name>"
project_path: "<absolute path>"
role: "parent"        # parent | child | root | standalone
description: "<one line>"
parent: null          # or { project_name, project_path, project_id }
children:
  - project_name: "<name>"
    project_path: "<path>"
    project_id: "<id>"
siblings: []          # populated by g-skl-wpac-sync
last_updated: "<YYYY-MM-DD>"
---
```