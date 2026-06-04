Compatibility Alias for `@g-wrkspc-sync`: $ARGUMENTS

## What This Command Does

This long-form Workspace-Control command remains supported for backwards compatibility. Prefer `@g-wrkspc-sync` for day-to-day use.

## Delegates To

`g-skl-workspace` -> `SYNC_PLAN`

---

Plan a Workspace-Control sync dry-run: $ARGUMENTS

## What This Command Does

Shows how the control project and declared workspace members would be compared or aligned without writing files. Delegates to `g-skl-workspace` operation `SYNC PLAN`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `SYNC PLAN`.
3. Treat `.gald3r/linking/workspace_manifest.yaml` as the canonical registry.
4. Validate the manifest first and stop on blocking parse findings.
5. Read clean repo gates, source/template relationships, write policy, per-repo git/worktree context, and parity or tier preflight commands to report manually.
6. End with the required dry-run statement from `g-skl-workspace`.

## Required Dry-Run Behavior

Dry-run only: no files are written. Member repository writes remain disabled until a later task explicitly authorizes apply mode.

## Safety Boundaries

- Do not call copy, move, delete, git add, git commit --trailer "Made-with: Cursor", parity sync, tier sync, or export scripts from this command.
- Undeclared member repo writes are forbidden.
- Member repositories remain separate git roots with independent status, branch, remote, rollback, and worktree boundaries. Branch/worktree names must include the member repo ID for multi-repo isolation.
- Workspace-Control does not replace PCAC INBOX, order, request, or peer sync flows.

## Usage Examples

```
@g-workspace-sync --dry-run
/g-workspace-sync --dry-run
```

## Delegates To

`g-skl-workspace` -> `SYNC PLAN`