Compatibility Alias for `@g-wrkspc-validate`: $ARGUMENTS

## What This Command Does

This long-form Workspace-Control command remains supported for backwards compatibility. Prefer `@g-wrkspc-validate` for day-to-day use.

## Delegates To

`g-skl-workspace` -> `VALIDATE`

---

Validate Workspace-Control manifest and routing metadata: $ARGUMENTS

## What This Command Does

Validates the Workspace-Control manifest shape, repository IDs, local path reachability, independent git roots, branch/dirty/remotes/worktree context, lifecycle values, touch policies, and optional routing metadata. Delegates to `g-skl-workspace` operation `VALIDATE`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `VALIDATE`.
3. Parse `.gald3r/linking/workspace_manifest.yaml` with structured YAML parsing.
4. Check required top-level keys, repository entries, controlled member IDs, touch policy values, and source-of-truth paths.
5. If task or bug routing metadata is requested, inspect only YAML frontmatter and validate `workspace_repos` plus `workspace_touch_policy` against the manifest.
6. Return `Workspace validation: PASS` only when there are no blocking findings.

## Safety Boundaries

- This command is read-only.
- Do not duplicate manifest parsing or policy logic inside this command file.
- Undeclared member repo writes are forbidden.
- Member repositories remain separate git roots with independent status, branch, remote, rollback, and worktree boundaries. Branch/worktree names must include the member repo ID for multi-repo isolation.

## Usage Examples

```
@g-workspace-validate
/g-workspace-validate
@g-workspace-validate .gald3r/tasks/task181_workspace_commands.md
```

## Delegates To

`g-skl-workspace` -> `VALIDATE`