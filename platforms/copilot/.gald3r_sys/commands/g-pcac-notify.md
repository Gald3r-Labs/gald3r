---
description: Send a lightweight [INFO] notification to one or more project INBOXes — no task created, no approval needed.
---
# /g-pcac-notify

Send a freeform FYI notification across project boundaries.

## Usage

```
/g-pcac-notify --parent "subject"
/g-pcac-notify --all-siblings "subject"
/g-pcac-notify --all-children "subject"
/g-pcac-notify --project /path/to/project "subject"
```

## Skill

Read and follow: `g-skl-pcac-notify`

## Key Points

- No task created, no approval needed
- Low priority in INBOX display (below CONFLICTS, requests, broadcasts)
- Acknowledged by marking `[DONE]` in g-pcac-read
- Staged to `pending_requests/info_[target].md` when target inaccessible
