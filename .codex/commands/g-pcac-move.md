Transfer files or folders to another project in the topology: $ARGUMENTS

## What This Command Does

Safely moves files or entire subsystems from this project to a parent, child, or sibling project. Includes provenance tracking, safety gates, vault log entries in both projects, and forwarding stubs. Uses `g-skl-pcac-move`.

## Workflow

### 1. Pre-flight Checks
- Source path exists inside this project
- Destination project is in topology (`link_topology.md`)
- No open tasks reference source files

### 2. Preview
```
MOVE PREVIEW
  From: {this_project}/{source_path}
  To:   {dest_project}/{dest_path}
  Type: {file | directory | N files}
  Why:  {reason}

This will COPY files to destination (source kept until you confirm delete).
Proceed? [yes / no / change destination]
```

### 3. Copy to Destination
```powershell
Copy-Item -Path {source} -Destination {dest} -Recurse -Force
```

### 4. Log Provenance in Both Projects
- Source: append to `.gald3r/vault/log.md`
- Destination: append to `{dest}/.gald3r/vault/log.md`

### 5. Forwarding Stub (optional)
Create a stub file at source noting the new location.

### 6. Delete Source (separate confirmation)
Only deletes if you explicitly say "yes, delete".

### 7. Update References (optional)
Search and update `SUBSYSTEMS.md`, `tasks/*.md`, `AGENTS.md`.

## Usage Examples

**Migrate a subsystem:**
```
@g-pcac-move gald3r_template_full/.cursor/skills/g-skl-websocket-sync → gald3r_mcp
```

**Promote a skill to canonical template:**
```
@g-pcac-move .cursor/skills/g-skl-new-thing → gald3r_template_full
```

**Move vault research:**
```
@g-pcac-move .gald3r/vault/research/topic.md → gald3r_vault
```

## Delegates To
`g-skl-pcac-move`
