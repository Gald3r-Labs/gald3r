Validate Workspace-Control manifest and routing metadata: $ARGUMENTS

## What This Command Does

Short alias for Workspace-Control validation. Delegates to `g-skl-workspace` operation `VALIDATE`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `VALIDATE`.
3. Parse `.gald3r/linking/workspace_manifest.yaml` with structured YAML parsing.
4. Check required top-level keys, repository entries, controlled member IDs, touch policy values, independent git roots, and routing metadata.
5. Return `Workspace validation: PASS` only when there are no blocking findings.

## Usage Examples

```
@g-wrkspc-validate
/g-wrkspc-validate
@g-wrkspc-validate .gald3r/tasks/task203_short_workspace_control_commands.md
```

## Compatibility Alias

`@g-workspace-validate` remains supported.
