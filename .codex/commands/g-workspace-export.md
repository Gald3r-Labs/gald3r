Compatibility Alias for `@g-wrkspc-export`: $ARGUMENTS

## What This Command Does

This long-form Workspace-Control command remains supported for backwards compatibility. Prefer `@g-wrkspc-export` for day-to-day use.

## Delegates To

`g-skl-workspace` -> `EXPORT_PLAN`

---

Plan a Workspace-Control export dry-run: $ARGUMENTS

## What This Command Does

Shows what a future Workspace-Control export would do without writing files. Delegates to `g-skl-workspace` operation `EXPORT PLAN`.

## Workflow

1. Activate `g-skl-workspace`.
2. Run operation `EXPORT PLAN`.
3. Treat `.gald3r/linking/workspace_manifest.yaml` as the canonical registry.
4. Validate the manifest first and stop on blocking parse findings.
5. For each controlled member, report source template path, destination local path, independent git root, branch, dirty status, remotes, worktree context, write policy, clean-repo expectations, and future apply gates.
6. For Task 184 template member bootstrap/export detail, use the control-project helper in dry-run mode:
   `.\scripts\workspace_template_export.ps1`
7. End with the required dry-run statement from `g-skl-workspace`.

## Required Dry-Run Behavior

Dry-run only: no files are written. Member repository writes remain disabled until a later task explicitly authorizes apply mode.

## Task 184 Bootstrap Export Helper

`scripts/workspace_template_export.ps1` reads the canonical manifest, plans exports from `gald3r_template_slim/`, `gald3r_template_full/`, and `gald3r_template_adv/` to `gald3r_template_slim`, `gald3r_template_full`, and `gald3r_template_adv`, and reports:

- source folders and destination member repo paths with independent git roots
- planned creates, updates, unchanged files, skipped files, and provenance output
- no-symlink/no-junction, git-root, branch, clean-status, remote, worktree-context, rollback-boundary, and hygiene gates
- apply blockers before any member repo write

Default invocation is dry-run only:

```powershell
.\scripts\workspace_template_export.ps1
```

Apply mode is intentionally gated behind explicit flags on the helper and must re-run preflight immediately before writing. Do not invoke apply mode from this command unless the active task explicitly authorizes member writes.

## Safety Boundaries

- Do not copy, move, delete, run export scripts, run parity sync, run tier sync, or stage files from this command.
- Undeclared member repo writes are forbidden.
- Member repositories remain separate git roots with independent status, branch, remote, rollback, and worktree boundaries. Branch/worktree names must include the member repo ID for multi-repo isolation.
- Generated output must name its canonical source in any future apply task.

## Usage Examples

```
@g-workspace-export --dry-run
/g-workspace-export --dry-run
```

## Delegates To

`g-skl-workspace` -> `EXPORT PLAN`