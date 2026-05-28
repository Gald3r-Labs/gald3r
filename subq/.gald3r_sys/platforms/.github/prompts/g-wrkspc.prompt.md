Workspace-Control dispatcher: $ARGUMENTS

## What This Command Does

Short entry point for Workspace-Control operations. Prefer the explicit subcommands below for clarity.

## Supported Operations

- `@g-wrkspc-status` -> `g-skl-workspace` STATUS
- `@g-wrkspc-validate` -> VALIDATE
- `@g-wrkspc-member-list` -> MEMBER_LIST
- `@g-wrkspc-init --dry-run|--apply` -> INIT PLAN/APPLY
- `@g-wrkspc-member-add <path> --id <repo_id> --role <role> --dry-run|--apply` -> MEMBER ADD PLAN/APPLY
- `@g-wrkspc-member-remove <repo_id> --dry-run|--apply` -> MEMBER REMOVE PLAN/APPLY
- `@g-wrkspc-spawn <project_name> --id <repo_id> --path <path> --dry-run|--apply` -> SPAWN PLAN/APPLY
- `@g-wrkspc-export --dry-run` -> EXPORT PLAN
- `@g-wrkspc-sync --dry-run` -> SYNC PLAN

## Safety Boundaries

- Dry-run is the default for lifecycle operations.
- Apply mode may update only `.gald3r/linking/workspace_manifest.yaml` unless a lifecycle command explicitly documents narrower member writes.
- `g-wrkspc-spawn --apply` may create a new empty independent git root plus minimal `.gitignore`/`README.md`; it does not scaffold app code, install gald3r, or write PCAC topology.
- Never delete member repository folders, `.git/`, branches, commits, remotes, or worktrees.

## Delegates To

`g-skl-workspace`
