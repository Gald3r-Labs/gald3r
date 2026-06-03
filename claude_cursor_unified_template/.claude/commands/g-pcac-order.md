Push a task or directive to child projects: $ARGUMENTS

## What This Command Does

Broadcasts a task order from this parent project to one or more child projects using the PCAC (Project Command and Control) topology. Uses `g-skl-pcac-order`.

## Workflow

### 1. Load Topology
Read `.gald3r/linking/link_topology.md` to identify children.

### 2. Determine Target
```
- all children
- specific children (provide names)
- by subsystem filter
```

### 3. Collect Order Details
- **Title**: what needs to be done
- **Why**: context and reasoning
- **Subsystems**: which areas are affected
- **Cascade depth**: 1 = direct children only, 2 = children + grandchildren, 3 = full subtree

### 4. Conflict Check
Before writing, check each target child's INBOX.md for existing CONFLICTs.

### 5. Dispatch
For each accessible child:
- Create task file in `{child}/.gald3r/tasks/`
- Update `{child}/.gald3r/TASKS.md`
- Append `[BROADCAST]` entry to `{child}/.gald3r/linking/INBOX.md`

### 6. Report
Show results: ✅ created / ⚠️ conflict / ❌ inaccessible

## Usage Examples

**Order to all children:**
```
@g-pcac-order update vault schema to v2
```

**Order to specific child:**
```
@g-pcac-order gald3r_mcp: add oracle connection pool task
```

**With cascade:**
```
@g-pcac-order cascade:2 update AGENTS.md format
```

## Delegates To
`g-skl-pcac-order`
