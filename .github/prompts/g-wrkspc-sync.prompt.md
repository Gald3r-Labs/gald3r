Plan a Workspace-Control sync dry-run: $ARGUMENTS

## What This Command Does

Short alias for Workspace-Control sync planning. Delegates to `g-skl-workspace` operation `SYNC_PLAN`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `SYNC_PLAN`.
3. Treat `.gald3r/linking/workspace_manifest.yaml` as the canonical registry.
4. Validate the manifest first and stop on blocking parse findings.
5. Report intended alignment/comparison without copy, move, delete, git, parity sync, tier sync, or export side effects.

## Required Dry-Run Behavior

Dry-run only: no files are written. Member repository writes remain disabled until a later task explicitly authorizes apply mode.

## Usage Examples

```
@g-wrkspc-sync --dry-run
/g-wrkspc-sync --dry-run
```

## Compatibility Alias

`@g-workspace-sync --dry-run` remains supported.

## gald3r_dev Self-Hosting Note

When a task in `gald3r_dev` changes reusable platform/framework files, this command should report the self-hosting parity path: run `scripts/platform_parity_sync.ps1 -SelfHostingRootSource` for dry-run evidence, then `scripts/platform_parity_sync.ps1 -SelfHostingRootSource -Sync` when the active task authorizes propagation. That flow syncs root platform folders, updates `gald3r_template_adv/`, and delegates to `tier_sync.ps1` for `gald3r_template_full/` and `gald3r_template_slim/`.

Dirty repositories are evaluated by overlap with planned writes. Unrelated dirty or untracked paths are warnings; overlapping target paths remain blockers unless explicitly authorized.
