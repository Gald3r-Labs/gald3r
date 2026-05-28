Plan a Workspace-Control export dry-run: $ARGUMENTS

## What This Command Does

Short alias for Workspace-Control export planning. Delegates to `g-skl-workspace` operation `EXPORT_PLAN`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `EXPORT_PLAN`.
3. Treat `.gald3r/linking/workspace_manifest.yaml` as the canonical registry.
4. Validate the manifest first and stop on blocking parse findings.
5. Report source/destination pairs, per-member git context, write policy, clean-repo expectations, and future apply gates.

## Required Dry-Run Behavior

Dry-run only: no files are written. Member repository writes remain disabled until a later task explicitly authorizes apply mode.

## Usage Examples

```
@g-wrkspc-export --dry-run
/g-wrkspc-export --dry-run
```

## Compatibility Alias

`@g-workspace-export --dry-run` remains supported.
