---
name: g-skl-wpac-adopt
description: Register another project as a child of the current project. Creates or updates linking/link_topology.md on both sides when the target is locally accessible.
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

## Transport layer (WPAC-v2 — T1608)

**Step 0-T — register the edge in the world_tree linking registry (T1625; code decides,
never the model — g-rl-38).** After reading both identities (steps 1–2), when BOTH
projects carry a registered `project_id` UUID in `.gald3r/.identity`, run:

```
gald3r workspace outbox send --verb link \
    --project-uuid <target_project_id> \
    --payload '{"target_project_id": "<current_project_id>", "relation": "parent"}'
```

(The registry edge is subject → parent: the CHILD is the subject, this project the
target — mirror of `g-skl-wpac-claim`.)

| Verdict | Action |
|---|---|
| `ok` | Edge registered server-side (`POST /api/v1/projects/{id}/links`) — the registry is the online source of truth. **T255: `gald3r workspace outbox send --verb link` now auto-refreshes the D7 linking mirror (`.gald3r/linking/link_topology.md` / `link_registry.json`) itself on `ok`** by chaining a `gald3r workspace pull` immediately after the edge is accepted — no separate manual pull needed for this edge. Note `transport: world_tree` in the confirm output. |
| `error` with HTTP 409 | Edge/parent already registered server-side — treat as the "Already adopted" idempotent case; continue the WPAC-v1 file-topology writes below. |
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
- `project_id`, `project_name`, `project_path` (use `cwd` if path not in .identity)

If `.gald3r/.identity` not found → stop: "No .gald3r/ found. Run @g-setup first."

### 2. Read target project identity
Read `<target_path>/.gald3r/.identity`:
- `project_id`, `project_name`

If target `.identity` not found:
- If `--one-way` NOT set → stop: "Target has no .gald3r/.identity. Ensure target has gald3r installed, or use --one-way."
- If `--one-way` → prompt for target `project_name` and `project_id` manually, continue

### 2.5 Workspace-Control member-repo guard (BUG-021 / Task 213 v1.1 / g-rl-36)

`g-wpac-adopt` writes to `<target_path>/.gald3r/linking/` when the target is locally accessible (Step 6 below). `linking/` is forbidden in Workspace-Control member `.gald3r/` — only `.identity` and `PROJECT.md` are marker-safe. If the target is a Workspace-Control controlled_member or migration_source registered in any ancestor `workspace_manifest.yaml`, the target write must be skipped.

Run the guard helper against the target path **before** any write into the target's `.gald3r/`. Use `-DotGald3rPath linking/` to evaluate the specific path WPAC adopt would write:

```powershell
gald3r workspace member guard --target-path "<target_project_path>" --dot-gald3r-path "linking/"
```

- exit `0` — target is not a member (or is the control project / outside workspace / template); bidirectional adoption proceeds normally.
- exit `1` — target is a member; `workspace/` is control plane and forbidden. Switch to `--one-way` automatically and skip Step 6 (target write). Record `BLOCK wpac_adopt_member_repo_gald3r_guard_block` in the session summary, plus the matched repo id/role. Suggest `@g-wrkspc-adopt` for Workspace-Control adoption, which routes coordination through the workspace controller's manifest instead of writing WPAC topology into the member.
- exit `2` — stop with `BLOCK wpac_adopt_member_repo_gald3r_guard_error` and direct the user to fix the manifest.

The current project's own `.gald3r/linking/` updates (Steps 3-5 below) are unaffected; the guard applies only to the target write.

### 3. Ensure linking/ exists in current project
```
.gald3r/linking/
  link_topology.md  ← create if missing
  INBOX.md             ← create if missing
  README.md            ← create if missing
  peers/               ← create if missing
```

If `link_topology.md` already exists: read it, parse YAML frontmatter.
If missing: initialize with current project's identity, role=parent, children=[], siblings=[].

### 4. Add child entry to current project's topology (BUG-231/T445 -- prefer the CLI verb)

Check if target is already listed in `children[]`. If yes → print "Already adopted" and skip to
Step 5.

**Preferred: `gald3r workspace topology write` (T445).** Atomically writes `link_topology.md`
AND `workspace_manifest.yaml`'s `wpac_relationship:` block AND `.gald3r/.identity`'s
`wpac_role=` line from ONE JSON payload, in a single call -- this is the CLI wiring of
`gald3r_core.server_bridge.wpac_claim.linking_mirror.write_local_topology()`, so BUG-231's
two-files-two-stories drift is code-enforced, not prose-enforced. Read the CURRENT
`children[]`/`parent`/`siblings[]` from `link_topology.md` first (if it exists) and include them
verbatim alongside the new child -- this call is a full write, not a merge:

```powershell
gald3r workspace topology write --payload '{
  "role": "parent",
  "project_id": "<current_project_id>",
  "project_name": "<current_project_name>",
  "project_path": "<current_project_path>",
  "children": [
    {"project_name": "<target_project_name>", "project_path": "<target_project_path>", "project_id": "<target_project_id>"}
  ]
}'
```

Use `--project-root <path>` if not run from the current project's own root, `--payload-file
<path>` for a larger/pre-built JSON file, and `--json` for a machine-readable verdict. Set
`role: "parent"` (or `"root"` if no parent is set); pass through any existing `parent`/
`siblings` fields unchanged (omit a field to default it to `null`/`[]`).

**Manual fallback (only if the CLI verb is unavailable).** Add to `children[]` and set
`role: "parent"` (if not already set; `"root"` if no parent defined) directly in
`link_topology.md`:

```yaml
children:
  - project_name: "<target_project_name>"
    project_path: "<target_project_path>"
    project_id: "<target_project_id>"
```

Write updated `link_topology.md`, then proceed to Step 4.5 to sync `workspace_manifest.yaml` by
hand -- the manual path is two separate writes and does not carry the CLI verb's atomicity
guarantee.

### 4.5 Sync current project's workspace_manifest.yaml -- manual-fallback path only (BUG-231)

Skip this step entirely when Step 4 used `gald3r workspace topology write` -- that call already
wrote this file (and `.gald3r/.identity`) in the same atomic operation. This step exists only for
the manual fallback: if `<current_project_path>/.gald3r/linking/workspace_manifest.yaml` exists,
update its `wpac_relationship:` block to match what the manual Step 4 write just wrote — same
`role`, same `children[]` (preserve `parent`/`siblings` verbatim):

```yaml
wpac_relationship:
  role: "parent"
  parent: null          # preserve existing value verbatim
  children:
    - project_name: "<target_project_name>"
      project_path: "<target_project_path>"
      project_id: "<target_project_id>"
  siblings: []          # preserve existing siblings[] verbatim
```

If the manifest does not exist, skip silently (not every project is a Workspace-Control
controller).

### 5. Write peer copy
Write `_peers/<target_project_name>.md` in current project's `linking/_peers/` folder:
```markdown
# Peer: <target_project_name>
relationship: child
project_path: <target_project_path>
project_id: <target_project_id>
adopted: <today_date>
```

### 6. Update target project's topology (bidirectional, skip if --one-way)

If target path is accessible:

a) Create `<target_path>/.gald3r/linking/` if missing (+ INBOX.md, README.md, peers/)

b) Read or initialize `<target_path>/.gald3r/linking/link_topology.md`

c) Set `parent` in target's topology:
```yaml
parent:
  project_name: "<current_project_name>"
  project_path: "<current_project_path>"
  project_id: "<current_project_id>"
```

d) Set `role: "child"` in target's topology.

e) Write updated topology.

e.5) Sync target's `workspace_manifest.yaml` (BUG-231, same rule as Step 4.5): if
`<target_path>/.gald3r/linking/workspace_manifest.yaml` exists, update its `wpac_relationship:`
block's `role`/`parent` to match what step e just wrote. Skip silently if the target has no
manifest. Same preference as Step 4: `gald3r workspace topology write --project-root
<target_path> --payload '{"role": "child", "parent": {...}}'` performs steps c/d/e/e.5 atomically
in one call when the target is locally reachable; the manual per-file edits above remain the
fallback.

f) Write `<target_path>/.gald3r/linking/_peers/<current_project_name>.md`:
```markdown
# Peer: <current_project_name>
relationship: parent
project_path: <current_project_path>
project_id: <current_project_id>
adopted: <today_date>
```

### 6.5 Deploy full framework when target is an autonomous_child (T1452)

If the adopted target is an `autonomous_child` (independent gald3r project, not a marker-only
`controlled_member`), it MUST have the **complete** gald3r framework, not just `.gald3r/`. `.gald3r_sys/`
is NOT part of that postcondition — it is permanently retired (D016/D017/T335/T274) and no verb
writes it. When the target is missing any of `.claude/`, `.cursor/`, or its platform's root docs
(a subset of `CLAUDE.md`/`AGENTS.md`/`GALD3R.md`, per-platform filtering, T357/BUG-341/T408), run
(or instruct the user to run) the full installer on the target path:

```powershell
# $targetPath = <target_project_path>
gald3r platform install cursor --into $targetPath --generated
gald3r platform install claude --into $targetPath --generated
```

- `gald3r platform install <platform> --into <dir> --generated` is a self-contained `gald3r`
  engine CLI verb (T177) — it reads the neutral component set embedded in the engine binary, no
  `<template_adv>` checkout required; run it once per platform (ensure the `gald3r` engine binary
  is installed via `g-install-agent` first).
- Match the platforms the parent project uses (read from the parent's installed IDE dirs).
- Skip this step for `controlled_member` targets -- they stay marker-only (`.identity` + `PROJECT.md`).
  Use Workspace-Control `@g-wrkspc-adopt` for member adoption; promote first via `@g-wpac-promote`
  if the member should become an `autonomous_child`.
- Verify before confirming: `Test-Path` `.claude/` and `.cursor/` on the target (`platform install` writes the IDE overlay plus that platform's root docs, T357; `.gald3r_sys/` is intentionally never produced, see BUG-189).

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
Write to: `<existing_child_path>/.gald3r/linking/_peers/<new_child_project_name>.md`

Also write in the new child's peers/:
```markdown
# Peer: <existing_child_project_name>
relationship: sibling
project_path: <existing_child_project_path>
project_id: <existing_child_project_id>
registered: <today_date>
```
Write to: `<new_child_path>/.gald3r/linking/_peers/<existing_child_project_name>.md`

**b) Update existing child's link_topology.md** siblings section:
- Add new_child row to the `siblings[]` table (create the array if missing)

**c) Update new child's link_topology.md** siblings section:
- Add all existing children to its `siblings[]` array

**d) Post SYNC INBOX message** to each existing child's INBOX.md:
```markdown
## [SYNC] - New sibling registered - <today_date>
- **<new_child_project_name>** adopted under <current_project_name> on <today_date>
- Peer snapshot written to `linking/_peers/<new_child_project_name>.md`
- Run `@g-wpac-sync` to review and acknowledge
```

Skip this step if the existing child's path is inaccessible — log the skip in the confirm output.

### 8. Check for staged orders

Before confirming, check if `pending_orders/` contains any orders staged for the newly adopted child:

- Scan `.gald3r/linking/pending_orders/` for files matching `order_[new_child_project_name]_*.md`
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
  Updated : <current_project_path>/.gald3r/linking/link_topology.md
  Updated : <target_project_path>/.gald3r/linking/link_topology.md  [or "skipped (--one-way)"]
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