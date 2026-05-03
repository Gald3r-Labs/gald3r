---
name: g-skl-pcac-move
description: >
  Transfer files or folders from this project to another project in the topology
  (parent, child, or sibling) with provenance tracking, safety gates, and
  vault log entries in both projects. Use when migrating subsystems between
  repos, promoting assets to the canonical template, or extracting code that
  grew in one project but belongs in another.
---

# g-skl-pcac-move

**File Owner**: none (source project's files, destination project's `.gald3r/vault/log.md`)

**Activate for**: "move to another project", "migrate subsystem", "transfer files", "hand off to", "promote to template", "extract to", `@g-pcac-move`

---

## Pre-Flight Checks

Before doing anything:

```
□ Source path exists and is inside THIS project
□ Destination project is in topology (parent / child / sibling) — check link_topology.md
□ Destination path is accessible on filesystem
□ No open tasks reference source files (check .gald3r/tasks/ for path mentions)
```

If any check fails → stop and report with fix instructions. Do not proceed.

---

## Step-by-Step Workflow

### Step 1 — Identify what is moving

Ask (or infer from user message):
- **What**: specific file, directory, or pattern
- **Why**: reason for the move (migration, promotion, extraction, handoff)
- **Where**: destination project path + subdirectory within that project

### Step 2 — Topology validation

```
Read: .gald3r/linking/link_topology.md
Confirm destination project appears in: parent | children[] | siblings[]
If NOT in topology → warn: "Project not in topology. Add via @g-pcac-status first."
```

### Step 3 — Open task warning

```
Grep: .gald3r/tasks/*.md for source path
If found:
  "⚠️ These open tasks reference source files:
    - task007: references src/vault/sync.py
    - task012: references src/vault/sync.py
   Proceeding will leave dangling references. Continue? [yes/no/update refs first]"
```

### Step 4 — Confirm with user

Show a clear summary before touching anything:

```
MOVE PREVIEW
  From: {this_project}/{source_path}
  To:   {dest_project}/{dest_path}
  Type: {file | directory | N files}
  Why:  {reason}

This will COPY files to destination (source kept until you confirm delete).
Proceed? [yes / no / change destination]
```

### Step 5 — Copy to destination

```powershell
Copy-Item -Path {source} -Destination {dest} -Recurse -Force
```

- Do NOT delete source yet
- Do NOT modify source files

### Step 6 — Log provenance in BOTH projects

**Source project** — append to `.gald3r/vault/log.md`:
```markdown
## {YYYY-MM-DD} — Move: {source_path} → {dest_project}/{dest_path}
- moved_to: {dest_project_name}
- dest_path: {dest_path}
- reason: {reason}
- forwarding_stub: {yes | no}
- source_deleted: {pending}
```

**Destination project** — append to `{dest_project}/.gald3r/vault/log.md` (if accessible):
```markdown
## {YYYY-MM-DD} — Received: {source_path} from {this_project_name}
- moved_from: {this_project_name}
- source_path: {original_path}
- reason: {reason}
```

### Step 7 — Forwarding stub (offer)

```
Create a forwarding stub at the source location?
A stub is a small file that says "this content has moved to {dest_project}/{dest_path}".
Prevents broken references. [yes / no]
```

If yes, create:
```markdown
# MOVED

This {file | directory} has been moved to:
**Project**: {dest_project_name}
**Path**: {dest_path}
**Date**: {YYYY-MM-DD}
**Reason**: {reason}

If you see this file referenced in tasks or rules, update to the new location.
```

### Step 8 — Delete source (separate confirmation)

```
Source files are still at: {source_path}
Delete source? This cannot be undone. [yes / no / keep for now]
```

Only delete if explicit "yes". Log deletion in vault/log.md.

### Step 9 — Update references (offer)

```
Offer to search and update references in:
  □ .gald3r/SUBSYSTEMS.md
  □ .gald3r/tasks/*.md
  □ AGENTS.md, CLAUDE.md
  □ Other files (specify pattern)
[yes, update all / yes, show me each / no]
```

### Step 10 — Final report

```
✅ MOVE COMPLETE
  Copied: {N files} to {dest_project}/{dest_path}
  Stub:   {created at source | skipped}
  Source: {deleted | kept}
  Refs:   {N references updated | skipped}
  Log:    vault/log.md updated in both projects

Next: commit changes in both projects to preserve provenance in git history.
```

---

## Common Use Cases

### Subsystem migration to gald3r_mcp

```
Source:  gald3r_dev/gald3r_template_full/.cursor/skills/g-skl-websocket-sync/
Dest:    gald3r_mcp/.cursor/skills/g-skl-websocket-sync/
Reason:  This subsystem requires Docker/MCP infrastructure
```

### Promoting a skill to the canonical template

```
Source:  gald3r_dev/.cursor/skills/g-skl-new-thing/
Dest:    gald3r_dev/gald3r_template_full/.cursor/skills/g-skl-new-thing/
Reason:  Skill is stable and ready for install-time distribution
```

### Moving vault research notes between projects

```
Source:  gald3r_dev/.gald3r/vault/research/topic.md
Dest:    gald3r_vault/research/topic.md
Reason:  Consolidating research into the shared vault
```

---

## Provenance Metadata Reference

When creating task files or log entries after a move, use these fields:

| Field | Value |
|-------|-------|
| `moved_from` | source project name + original path |
| `moved_to` | destination project name + new path |
| `moved_date` | YYYY-MM-DD |
| `moved_reason` | migration \| promotion \| extraction \| handoff \| consolidation |
| `forwarding_stub` | true \| false |
| `source_deleted` | true \| false \| pending |

---

## Safety Guarantees

- **Copy-first**: source is never touched until step 8 explicit confirmation
- **Topology-gated**: destination must be in link_topology.md
- **Log-first**: vault log entries written before any deletion
- **No silent deletes**: every delete requires its own explicit confirmation
