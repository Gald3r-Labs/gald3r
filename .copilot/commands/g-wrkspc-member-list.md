List Workspace-Control manifest members: $ARGUMENTS

## What This Command Does

Lists only repositories declared in `.gald3r/linking/workspace_manifest.yaml`. Delegates to `g-skl-workspace` operation `MEMBER_LIST`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `MEMBER_LIST`.
3. Do not discover extra members from folder names, git remotes, sibling directories, or `template_*` folders.
4. Include per-member role, lifecycle, local path reachability, git root, branch, dirty status, remotes, worktree count, inspect permission, and write permission.

## Usage Examples

```
@g-wrkspc-member-list
/g-wrkspc-member-list
@g-wrkspc-member-list --role controlled_member
```
