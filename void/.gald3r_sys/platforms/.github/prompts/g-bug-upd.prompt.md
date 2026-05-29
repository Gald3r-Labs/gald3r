Update a bug record. Activates **g-skl-bugs** → UPDATE BUG operation.

```
@g-bug-upd BUG-NNN status resolved
@g-bug-upd BUG-NNN severity critical
@g-bug-upd BUG-NNN add-note "Found root cause: null guard missing"
```

Updates bug file fields and BUGS.md index row. Appends to Status History.

Workspace-Control updates: `@g-bug-upd BUG-NNN workspace-repos gald3r_dev,gald3r_template_full` and `@g-bug-upd BUG-NNN workspace-touch-policy generated_output` must validate IDs/policies against `.gald3r/linking/workspace_manifest.yaml` when present. Unknown member IDs are invalid. Widening from current-repo-only to member repos, or to `generated_output`/`multi_repo`, requires Status History context or equivalent explicit instruction before writing the update.
