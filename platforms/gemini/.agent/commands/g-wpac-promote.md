---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
Promote a controlled_member repository to a fully self-managed autonomous_child: $ARGUMENTS

## What This Command Does

Migrates an existing Workspace-Control `controlled_member` (or `migration_source`) repository
into a fully-equipped `autonomous_child`. This is the formal off-ramp for the g-rl-36 marker-only
guard (BUG-097): a `controlled_member` is intentionally restricted to a marker-only `.gald3r/`
(`.identity` + `PROJECT.md`) and `@g-skl-setup` is blocked there. PROMOTE lifts that guard by
flipping `workspace_role`, backfilling the standard framework files that postdate the original
member creation, and updating the workspace manifest.

Delegates to `g-skl-workspace` PROMOTE operation.

## Usage

```
@g-wpac-promote <member-id> --dry-run
@g-wpac-promote <member-id> --apply
```

**Arguments:**
- `member-id` — the manifest `repository.id` of the member to promote (or pass `--member-path`)

**Options:**
- `--dry-run` — preview the plan; write nothing (default)
- `--apply` — perform the promotion
- `--member-path <path>` — absolute member path (when not resolving by manifest id)
- `--controller-path <path>` — absolute controller path (defaults to manifest discovery)
- `--gald3r-version <ver>` — override the framework version written to `.identity`

## Examples

```
# Preview what promoting gald3r_agent would do
@g-wpac-promote gald3r_agent --dry-run

# Promote it for real
@g-wpac-promote gald3r_agent --apply
```

## What Happens

1. Resolves the member path, manifest entry, and `.gald3r/.identity`.
2. Classifies the current role via the g-rl-36 guard helper.
   - Already `autonomous_child` -> informational no-op.
   - Not `controlled_member`/`migration_source` -> blocked.
3. **Dry-run**: prints the plan (files to scaffold, `.identity` edits, manifest change); writes nothing.
4. **Apply**:
   - Creates only the **missing** standard files: `RELEASES.md`, `releases/`, `vocab.md`,
     `workspace/topology.md`, `workspace/inbox.md`, `FEATURES.md`, `BUGS.md`, `PLAN.md`
     (existing files are preserved, never overwritten).
   - Rewrites `.gald3r/.identity`: `workspace_role=autonomous_child`, removes
     `member_gald3r_marker_only`, bumps `gald3r_version` to the current framework version.
   - Updates **only** the named member's `workspace_role` in `workspace_manifest.yaml`.
   - Prints a promote summary with the exact files created/updated.
5. After apply, the g-rl-36 guard allows `@g-skl-setup`. Run `@g-skl-setup --upgrade-existing`
   for a full file top-up, then `@g-wrkspc-validate` to confirm.

## Underlying Script

```
.gald3r_sys/skills/g-skl-workspace/scripts/gald3r_promote_member.ps1 -MemberPath <path> [-Apply]
```

## Companion Commands

| Command | When to Use |
|---------|-------------|
| `@g-wpac-promote` | Upgrade a `controlled_member` to `autonomous_child` |
| `@g-wrkspc-spawn` | Create a brand-new empty member |
| `@g-wrkspc-adopt` | Import an existing populated gald3r project's history |
| `@g-wrkspc-member-add` | Register an existing/planned member (registry-only) |
| `@g-wrkspc-validate` | Verify manifest + roles after promotion |

## Delegates To
`g-skl-workspace`
