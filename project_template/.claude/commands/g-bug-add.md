---
subsystem_memberships: [BUG_AND_QUALITY]
---
Report a new bug. Activates **g-skl-bugs** → REPORT BUG operation.

```
@g-bug-add "Description of the bug"
@g-bug-add "Description" --severity high --file path/to/file.py --line 42
```

Zero-tolerance: pre-existing and unrelated bugs still get logged. Describe the bug and the skill handles BUG-NNN ID assignment, file creation, BUGS.md index entry.

> **Active agent run → inbox routing (T585):** during a `g-go-go` / `g-go-code` / swarm run (marker `.gald3r/logs/ggo_run_state.json` `active: true`, or env `GALD3R_AGENT_RUN=1`), the skill/engine writes the new bug to `bugs/inbox/` as an **id-less draft**; the hot-inbox intake assigns the real BUG-NNN id atomically at the next iteration boundary, so concurrent agents never collide on the next id. Display: *"Agent run detected — bug queued to inbox for safe ID assignment."* No active run → direct create, unchanged.

> **Alias**: `@g-bug-report` also works (deprecated; use `@g-bug-add` for new work).

Workspace-Control optional flags/fields: when a bug involves workspace members, include `workspace_repos` and `workspace_touch_policy`. Validate repo IDs and touch policies against `.gald3r/linking/workspace_manifest.yaml` when present; unknown IDs are invalid. Omit both fields for current-repo-only bugs. Member repo fixes require explicit member IDs, compatible policy, bug/task authorization, and manifest write permission.
