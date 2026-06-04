Compatibility Alias for `@g-wrkspc-status`: $ARGUMENTS

## What This Command Does

This long-form Workspace-Control command remains supported for backwards compatibility. Prefer `@g-wrkspc-status` for day-to-day use.

## Delegates To

`g-skl-workspace` -> `STATUS`

---

Show Workspace-Control status: $ARGUMENTS

## What This Command Does

Displays a concise read-only Workspace-Control summary for the current project. Delegates to `g-skl-workspace` operation `STATUS`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `STATUS`.
3. Read `.gald3r/linking/workspace_manifest.yaml` as the canonical Workspace-Control registry.
4. Summarize the workspace owner, declared repositories, lifecycle states, local path reachability, git root, branch, dirty status, remotes, worktree context, and write policy.
5. Keep the report concise and do not print the full manifest unless explicitly requested.

## Safety Boundaries

- This command is report-only.
- Do not infer workspace members from folder names, git remotes, `template_*` directories, or docs artifacts.
- Undeclared member repo writes are forbidden.
- Member repositories remain separate git roots with independent status, branch, remote, rollback, and worktree boundaries. Branch/worktree names must include the member repo ID for multi-repo isolation.

## Usage Examples

```
@g-workspace-status
/g-workspace-status
```

## Delegates To

`g-skl-workspace` -> `STATUS`