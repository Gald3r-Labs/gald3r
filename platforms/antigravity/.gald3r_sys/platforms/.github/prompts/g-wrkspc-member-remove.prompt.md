Remove or retire a Workspace-Control member from the manifest: $ARGUMENTS

## What This Command Does

Plans or applies a registry-only member removal or retirement in `.gald3r/linking/workspace_manifest.yaml`. Delegates to `g-skl-workspace` operation `MEMBER_REMOVE_PLAN` by default, or `MEMBER_REMOVE_APPLY` only with `--apply`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run `MEMBER_REMOVE_PLAN` unless `$ARGUMENTS` includes `--apply`.
3. Confirm the repository ID exists in the manifest.
4. Block owner repository removal unless a separate approved migration task names a replacement owner.
5. Search routing references and recommend `lifecycle_status: retired` when historical tasks/bugs still name the repo.
6. In apply mode, update only manifest registry fields.

## Safety Boundaries

- Never delete repository folders, `.git/`, branches, commits, remotes, worktrees, tasks, bugs, or generated output.
- Prefer retirement over deletion when historical references exist.

## Usage Examples

```
@g-wrkspc-member-remove gald3r_template_adv --dry-run
@g-wrkspc-member-remove gald3r_template_adv --apply
```
