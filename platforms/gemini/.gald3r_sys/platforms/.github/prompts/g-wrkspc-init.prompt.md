Initialize Workspace-Control manifest: $ARGUMENTS

## What This Command Does

Creates or promotes `.gald3r/linking/workspace_manifest.yaml` for a control project. Delegates to `g-skl-workspace` operation `INIT_PLAN` by default, or `INIT_APPLY` only with `--apply`.

## Workflow

1. Activate `g-skl-workspace`.
2. Default to `INIT_PLAN` unless `$ARGUMENTS` includes `--apply`.
3. Validate the current project git root and `.gald3r/` structure.
4. If a manifest already exists, parse and summarize it instead of overwriting it.
5. If a seed manifest is supplied, validate it before proposing promotion.
6. In apply mode, write only `.gald3r/linking/workspace_manifest.yaml`.

## Safety Boundaries

- Dry-run is default.
- Apply requires explicit `--apply`.
- Do not create, delete, move, initialize, or edit member repository folders.
- Do not overwrite an existing manifest unless a future task explicitly authorizes replacement.

## Usage Examples

```
@g-wrkspc-init --dry-run
@g-wrkspc-init --seed docs/20260425_090100_Cursor_WORKSPACE_CONTROL_MANIFEST.yaml --dry-run
@g-wrkspc-init --seed docs/20260425_090100_Cursor_WORKSPACE_CONTROL_MANIFEST.yaml --apply
```
