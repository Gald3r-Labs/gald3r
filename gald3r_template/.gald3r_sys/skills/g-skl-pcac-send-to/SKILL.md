---
name: g-skl-pcac-send-to
description: >
  Send files, features, specs, ideas, or code from the current project to any
  related project in the topology (parent, sibling, or child). Handles file copying,
  INBOX notification, vault provenance logging, and optional source cleanup.
  Lighter-weight than g-skl-pcac-move (which requires topology pre-registration);
  this skill also works when the destination is a recently-spawned project.
---

# g-skl-pcac-send-to

**File Owner**: none (operates across projects; updates source vault/log.md and destination INBOX.md)

**Activate for**: "send this to", "transfer to another project", "push features to", "hand off to",
"move these files to", "copy to sibling/parent/child", `@g-pcac-send-to`

---

## When to Use

When you have identified content in the current project that belongs in (or should be shared with)
another project in the ecosystem:

- **Features / specs** that should seed a newly spawned project
- **Code folders** that have grown into a separate concern
- **Ideas or bugs** worth forwarding to a related project
- **Documentation** that should live in a central or specialized project

Difference from `g-skl-pcac-move`:
- `g-skl-pcac-move` requires the destination to already be in topology and enforces strict pre-flight
- `g-skl-pcac-send-to` is more flexible: works with freshly spawned projects, supports partial sends,
  and provides richer "what type of content are you sending?" framing

---

## Command Syntax

```
@g-pcac-send-to --parent|--sibling|--child <project_name> [options]

Options:
  --what <path>           File or folder to send (relative to current project root)
  --type features|code|ideas|bugs|docs|spec   Content type (affects destination path defaults)
  --dest-path <path>      Override destination subdirectory (default: auto from --type)
  --message "..."         Message to include in destination INBOX.md
  --delete-source         Delete source after confirmed copy (default: keep)
  --dry-run               Preview only, no file operations
```

**Examples**:
```
@g-pcac-send-to --sibling gald3r_valhalla --what .gald3r/features/gald3r_backend --type features
@g-pcac-send-to --child gald3r_payments --what src/payments/ --type code --message "Payment subsystem ready for extraction"
@g-pcac-send-to --parent gald3r_dev --what .gald3r/features/feat-012_auth.md --type features --message "This feature should live in the template"
@g-pcac-send-to --sibling gald3r_vault --what research/articles/topic.md --type docs
```

---

## Content Type → Default Destination Path

| `--type` | Default destination path |
|----------|--------------------------|
| `features` | `.gald3r/features/` |
| `code` | mirror source structure (e.g. `src/foo/` → `<dest>/src/foo/`) |
| `ideas` | `.gald3r/IDEA_BOARD.md` (append) |
| `bugs` | `.gald3r/BUGS.md` (append summary) + `.gald3r/bugs/` (copy files) |
| `docs` | `docs/` |
| `spec` | `.gald3r/specifications_collection/` |

Override any default with `--dest-path`.

---

## Pre-Flight Checks

```
□ Current project has .gald3r/.identity
□ --what path exists in current project
□ --parent/--sibling/--child is specified
□ <project_name> exists on filesystem OR is in topology
  (if neither: stop "Project not found at <path> and not in topology")
□ Destination path is accessible
```

If `--dry-run`: print full preview and stop.

---

## Steps

### Step 1 — Resolve destination project

```
Check .gald3r/linking/link_topology.md for <project_name> in:
  parent | children[] | siblings[]

If found: use recorded project_path
If NOT found: attempt to resolve as <ecosystem_root>/<project_name>
  If that path exists and has .gald3r/.identity → treat as accessible, warn "not yet in topology"
  If path doesn't exist → stop: "Project <project_name> not found"
```

### Step 2 — Show send preview

```
SEND PREVIEW
  From : <current_project>/<what>
  To   : <dest_project>/<dest_path>
  Type : <content_type>
  Size : <file count> files / <N KB>
  Note : <--message if provided>

After copy: source will be KEPT (add --delete-source to remove after)
Proceed? [yes / no / change destination]
```

### Step 3 — Copy files to destination

**For type = features, docs, spec, code**:
```powershell
# Single file
Copy-Item -Path "<source>" -Destination "<dest_project>/<dest_path>/" -Force

# Folder
Copy-Item -Path "<source>/*" -Destination "<dest_project>/<dest_path>/" -Recurse -Force
```

**For type = ideas**:
- Parse `.gald3r/IDEA_BOARD.md` entries that match `--what` (if a file path is given)
  OR read the file if `--what` is a raw ideas .md file
- Append each idea as a new entry to `<dest_project>/.gald3r/IDEA_BOARD.md`:
  ```markdown
  ## IDEA — [title] (received from <source_project> — <YYYY-MM-DD>)
  > Forwarded via @g-pcac-send-to
  [original idea content]
  ```

**For type = bugs**:
- Copy bug files to `<dest_project>/.gald3r/bugs/`
- Append summary lines to `<dest_project>/.gald3r/BUGS.md`

### Step 4 — Update FEATURES.md in destination (if type = features)

Scan the newly copied feature files in `<dest_project>/.gald3r/features/`:
- Parse YAML frontmatter (id, title, status, goal)
- Append entries to `<dest_project>/.gald3r/FEATURES.md` index table
- Update `Next feat ID` in FEATURES.md if needed

### Step 5 — Write INBOX notification in destination

Append to `<dest_project>/.gald3r/linking/INBOX.md` (create file if missing):

```markdown
## [OPEN] SEND-<YYYYMMDD>-<slug> — from: <source_project> — <YYYY-MM-DD>
**Type:** send
**Content-type:** <features | code | ideas | bugs | docs | spec>
**From path:** <source_project>/<source_path>
**Delivered to:** <dest_path>
**Message:** <--message value or "none">
**File count:** N
**Source status:** kept | deleted
**Action needed:** Review received content and integrate as appropriate.
```

If `<dest_project>/.gald3r/linking/INBOX.md` doesn't exist, create it with a standard header first.

### Step 6 — Log provenance in source project

Append to `<current_project>/.gald3r/vault/log.md` (create if missing):

```markdown
## <YYYY-MM-DD> — Sent: <source_path> → <dest_project>/<dest_path>
- dest_project: <project_name>
- dest_path: <dest_path>
- content_type: <type>
- file_count: N
- message: <message or none>
- source_deleted: <pending | false>
```

### Step 7 — Delete source (if --delete-source or confirmed)

If `--delete-source` flag was set:
```
About to delete: <source_path>
Files: N
This cannot be undone. Confirm delete? [yes / no]
```

Only delete on explicit "yes". Log deletion:
```markdown
- source_deleted: true
- deleted_at: <YYYY-MM-DD HH:MM>
```

If `--delete-source` was NOT set, prompt:
```
Source is still at: <source_path>
Delete now? [yes / no / later]
"later" = add a reminder task to .gald3r/tasks/
```

### Step 8 — Update source FEATURES.md (if type = features + source deleted)

If features were deleted from source:
- Remove or stub transferred feat-NNN entries in source `FEATURES.md`
- Add note: `> [transferred to <dest_project> — <YYYY-MM-DD>]`
- Update feature counts

### Step 9 — Final report

```
✅ SEND COMPLETE
  Sent    : <N files> from <source_path>
  To      : <dest_project>/<dest_path>
  INBOX   : entry written at <dest_project>/.gald3r/linking/INBOX.md
  Source  : kept | deleted
  Log     : vault/log.md updated

Next: open <dest_project> and run @g-pcac-read to review the incoming content.
```

---

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Destination not in topology | Warn "not in topology" but proceed if path accessible; offer to add to topology after |
| Destination has no .gald3r/ | Warn: "Destination has no gald3r setup. Files will be copied but no INBOX entry written." |
| Feature IDs conflict with destination | Warn: "feat-NNN already exists in destination. Copy will overwrite — confirm?" |
| --what is a glob pattern | Expand glob, show file list in preview before proceeding |
| Source path not found | Stop: "Path not found: <path>" |
| Large transfer (>50 files) | Require explicit confirmation: "Sending N files. This is a large transfer. Continue?" |

---

## Relationship to Other PCAC Skills

| When to use this skill | When to use other skills |
|------------------------|--------------------------|
| Transferring content to an existing or newly spawned project | `g-skl-pcac-move` for strict topology-gated migrations with full pre-flight |
| Forwarding features/ideas/bugs | `g-skl-pcac-order` for pushing tasks (not content) |
| Seeding a new project after spawn | `g-skl-pcac-spawn --features` handles this at spawn time |
| Notifying without sending files | `g-skl-pcac-notify` for FYI-only messages |
