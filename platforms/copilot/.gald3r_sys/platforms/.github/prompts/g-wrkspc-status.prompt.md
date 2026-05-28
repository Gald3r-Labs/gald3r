Show Workspace-Control status: $ARGUMENTS

## What This Command Does

Short alias for Workspace-Control status. Delegates to `g-skl-workspace` operation `STATUS`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `STATUS`.
3. Read `.gald3r/linking/workspace_manifest.yaml` as the canonical Workspace-Control registry.
4. Summarize the workspace owner, declared repositories, lifecycle states, local path reachability, git root, branch, dirty status, remotes, worktree context, and write policy.
5. Keep the report concise and do not print the full manifest unless explicitly requested.

## Usage Examples

```
@g-wrkspc-status
/g-wrkspc-status
```

## Compatibility Alias

`@g-workspace-status` remains supported.
