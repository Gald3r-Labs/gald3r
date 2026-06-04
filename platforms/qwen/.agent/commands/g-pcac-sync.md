Initiate or respond to a sibling contract sync: $ARGUMENTS

## What This Command Does

Exchanges updated contract information with one or more sibling projects. Advisory only — non-blocking. Both sides update their local peer topology copies. Uses `g-skl-pcac-sync`.

## Workflow

### 1. Load Topology
Read `.gald3r/linking/link_topology.md` to get siblings list.

### 2. Choose Target Sibling(s)
- specific sibling by name
- all siblings

### 3. Determine What Changed
Review what is new or changed in your project contract:
- New/removed subsystems
- New capabilities
- Changed constraints
- Updated contact paths

### 4. Write SYNC Entry to Sibling INBOX
Append `[SYNC]` entry to `{sibling}/.gald3r/linking/INBOX.md`:
```markdown
## [SYNC] {date} — {this_project_name}
**Updated**: {what changed}
**Contract ref**: {linking/peers/{this_project_name}.md}
```

### 5. Update Local Peer Copy
Write/update `linking/peers/{sibling_name}.md` with the latest peer contract.

### 6. Report
Confirm which siblings were notified. They will action at next session.

## Usage Examples

**Sync with a specific sibling:**
```
@g-pcac-sync gald3r_mcp — we added vault-hooks-automation subsystem
```

**Sync all siblings:**
```
@g-pcac-sync all — updated subsystem registry after reintegration
```

## Delegates To
`g-skl-pcac-sync`
