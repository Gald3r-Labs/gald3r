---
description: Send a lightweight [INFO] notification to one or more project INBOXes — no task created, no approval needed.
subsystem_memberships: [WORKSPACE_COORDINATION]
---
# /g-wpac-notify

Send a freeform FYI notification across project boundaries.

## Usage

```
/g-wpac-notify --parent "subject"
/g-wpac-notify --all-siblings "subject"
/g-wpac-notify --all-children "subject"
/g-wpac-notify --project /path/to/project "subject"
```

## Skill

Read and follow: `g-skl-wpac-notify`

## Key Points

- No task created, no approval needed
- Low priority in INBOX display (below CONFLICTS, requests, broadcasts)
- Acknowledged by marking `[DONE]` in g-wpac-read
- Staged to `pending_requests/info_[target].md` when target inaccessible
