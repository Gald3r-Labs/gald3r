Report a new bug. Activates **g-skl-bugs** → REPORT BUG operation.

```
@g-bug-add "Description of the bug"
@g-bug-add "Description" --severity high --file path/to/file.py --line 42
```

Zero-tolerance: pre-existing and unrelated bugs still get logged. Describe the bug and the skill handles BUG-NNN ID assignment, file creation, BUGS.md index entry.

> **Alias**: `@g-bug-report` also works (deprecated; use `@g-bug-add` for new work).

Workspace-Control optional flags/fields: when a bug involves workspace members, include `workspace_repos` and `workspace_touch_policy`. Validate repo IDs and touch policies against `.gald3r/linking/workspace_manifest.yaml` when present; unknown IDs are invalid. Omit both fields for current-repo-only bugs. Member repo fixes require explicit member IDs, compatible policy, bug/task authorization, and manifest write permission.
