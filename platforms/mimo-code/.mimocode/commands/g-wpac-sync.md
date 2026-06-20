---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
Initiate or respond to a sibling contract sync: $ARGUMENTS

## What This Command Does

Exchanges updated contract information with one or more sibling projects. Advisory only — non-blocking. Both sides update their local peer topology copies. Uses `g-skl-wpac-sync`.

## Workflow

### 1. Load Topology
Read `.gald3r/workspace/topology.md` to get siblings list.

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
Append `[SYNC]` entry to `{sibling}/.gald3r/workspace/inbox.md`:
```markdown
## [SYNC] {date} — {this_project_name}
**Updated**: {what changed}
**Contract ref**: {workspace/peers/{this_project_name}.md}
```

### 5. Update Local Peer Copy
Write/update `workspace/peers/{sibling_name}.md` with the latest peer contract.

### 6. Report
Confirm which siblings were notified. They will action at next session.

## Usage Examples

**Sync with a specific sibling:**
```
@g-wpac-sync example_mcp — we added vault-hooks-automation subsystem
```

**Sync all siblings:**
```
@g-wpac-sync all — updated subsystem registry after reintegration
```

## Delegates To
`g-skl-wpac-sync`
