Send a request to the parent project: $ARGUMENTS

## What This Command Does

Writes a REQUEST entry to the parent project's INBOX and marks the specified local task as blocked pending parent action. Uses `g-skl-pcac-ask`.

## Workflow

### 1. Load Topology
Read `.gald3r/linking/link_topology.md` to get parent path.

### 2. Collect Request Details
- **What is needed**: specific action or decision from parent
- **Which local task is blocked**: task ID or title
- **Why**: reasoning for the request

### 3. Write to Parent INBOX
Append a `[REQUEST]` entry to `{parent}/.gald3r/linking/INBOX.md`:
```markdown
## [REQUEST] {date} — {this_project_name}
**Needs**: {what is needed}
**Blocking**: {local_task_id} — {local_task_title}
**Why**: {reasoning}
```

### 4. Mark Local Task as Blocked
Update local task file with:
- `parent_request_sent: true`
- `parent_request_date: {date}`
- Status → `⏳` (blocked)

### 5. Confirm
Report the request was written and which task is now blocked.

## Usage Examples

**Request a decision:**
```
@g-pcac-ask We need architecture approval for the new vault schema before task 012 can proceed.
```

**Request a resource:**
```
@g-pcac-ask gald3r_mcp needs to expose the oracle connection pool API for our task 015.
```

## Delegates To
`g-skl-pcac-ask`
