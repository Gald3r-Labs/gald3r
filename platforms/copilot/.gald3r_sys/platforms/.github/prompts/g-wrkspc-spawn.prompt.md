Spawn a new local Workspace-Control member project: $ARGUMENTS

## What This Command Does

Creates a brand-new local workspace member project and registers it in `.gald3r/linking/workspace_manifest.yaml`. This mirrors the simple shape of `@g-pcac-spawn`, but it is Workspace-Control membership only: no PCAC topology, no INBOX writes, no task delegation, and no history import.

Delegates to `g-skl-workspace` operation `SPAWN_PLAN` by default, or `SPAWN_APPLY` only when `$ARGUMENTS` includes `--apply`.

## Usage

```text
@g-wrkspc-spawn <project_name> --id <repo_id> --path <absolute_path> --dry-run
@g-wrkspc-spawn <project_name> --id <repo_id> --path <absolute_path> --apply
```

## Options

- `--description "..."` - one-line member role/mission for the manifest.
- `--template none|slim|full|adv` - future template intent only; default `none`. This command does not install gald3r templates.
- `--allow-existing-empty` - permit an existing empty target directory.
- `--role controlled_member` - default and currently the only normal spawn role.

## When To Use This

Use `@g-wrkspc-spawn` when the destination should start as a clean independent git root, such as `G:/gald3r_ecosystem/gald3r_throne`.

Use `@g-wrkspc-adopt` instead for an existing gald3r project with `.gald3r/` history that must be surfaced in the control project. Use `@g-wrkspc-member-add` instead when an existing repo only needs registry metadata.

## Workflow

1. Activate `g-skl-workspace`.
2. Run `SPAWN_PLAN` unless `$ARGUMENTS` includes `--apply`.
3. Validate the manifest, duplicate repo IDs, target path, symlink/junction status, control-project nesting, and empty-directory requirements.
4. In apply mode, require active-task authorization for the new repo ID, rerun preflight, create the target folder if needed, run `git init`, add minimal `.gitignore`/`README.md` only if absent, and update only the control project's workspace manifest.

## Safety Boundaries

- Dry-run is default.
- Apply creates only a minimal independent git root and manifest entry.
- Apply does not install gald3r, create member `.gald3r/` files, scaffold app/runtime source, set remotes, create commits, create worktrees, write PCAC topology, or import existing task/bug history.
- If the target already contains a git repo, stop and use `@g-wrkspc-member-add` or `@g-wrkspc-adopt`.

## Usage Examples

```text
@g-wrkspc-spawn gald3r_throne --id gald3r_throne --path G:/gald3r_ecosystem/gald3r_throne --description "Desktop workspace app" --dry-run
@g-wrkspc-spawn gald3r_throne --id gald3r_throne --path G:/gald3r_ecosystem/gald3r_throne --description "Desktop workspace app" --allow-existing-empty --apply
```
