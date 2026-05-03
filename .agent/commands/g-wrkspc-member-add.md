Add a Workspace-Control member to the manifest: $ARGUMENTS

## What This Command Does

Plans or applies a registry-only member addition in `.gald3r/linking/workspace_manifest.yaml`. Delegates to `g-skl-workspace` operation `MEMBER_ADD_PLAN` by default, or `MEMBER_ADD_APPLY` only with `--apply`.

## Required Arguments

- `<path>` or `--path <path>`
- `--id <repo_id>`
- `--role <control_project|controlled_member|migration_source>`

## Workflow

1. Activate `g-skl-workspace`.
2. Run `MEMBER_ADD_PLAN` unless `$ARGUMENTS` includes `--apply`.
3. Validate repo ID pattern, duplicate IDs, local path, symlink/junction state, git root, branch, dirty status, remotes, and worktree context.
4. If path is inside the control project, require `--role migration_source` or block.
5. In apply mode, update only the manifest registry.

## Safety Boundaries

- Dry-run is default.
- Apply does not create folders, initialize git, set remotes, copy files, or write into the member path.
- Controlled members default to write-blocked until a later task explicitly authorizes writes.

## Usage Examples

```
@g-wrkspc-member-add G:/gald3r_ecosystem/gald3r_template_full --id gald3r_template_full --role controlled_member --dry-run
@g-wrkspc-member-add G:/gald3r_ecosystem/gald3r_template_full --id gald3r_template_full --role controlled_member --apply
```
