---
description: "Workspace-Control member-repository .gald3r/ marker-only invariant — slim marker (.identity + PROJECT.md) is the only legal member content; live control plane lives only in the controller"
globs:
alwaysApply: true
---

# Workspace-Control Member `.gald3r/` Marker-Only Guard (HARD RULE)

**Workspace-Control controlled_member and migration_source repositories may keep ONLY a slim `.gald3r/` marker:**

- `.gald3r/.identity` — identifies the member and ties it back to the workspace controller
- `.gald3r/PROJECT.md` — copied / parity-maintained from the controller; describes the member's mission

**Live gald3r control-plane state is forbidden in member repositories.** Any of the following inside a member's `.gald3r/` is a hard violation: `TASKS.md`, `tasks/`, `BUGS.md`, `bugs/`, `PLAN.md`, `FEATURES.md`, `SUBSYSTEMS.md`, `RELEASES.md`, `CONSTRAINTS.md`, `IDEA_BOARD.md`, `PRDS.md`, `prds/`, `features/`, `releases/`, `subsystems/`, `config/`, `linking/`, `experiments/`, `logs/`, `reports/`, `archive/`, `specifications_collection/`, `learned-facts.md`, or any equivalent orchestration state.

The workspace controller (e.g. `gald3r_dev`) is the source of truth for live tasks, bugs, plans, features, releases, subsystems, constraints, ideas, PRDs, and cross-project orchestration. Members are independent git roots that hold source code, packaging, and history — but never live project task state.

Template directories under `gald3r_template_slim/`, `gald3r_template_full/`, `gald3r_template_adv/` are the **only** legitimate exception: their `.gald3r/` content is intentional install template content.

This invariant fires for every workflow that may write `.gald3r/` to an arbitrary destination: `g-skl-setup`, `g-skl-pcac-spawn`, `g-skl-pcac-adopt`, `g-skl-workspace` SPAWN_APPLY / ADOPT_APPLY, `gald3r_install`, and any future scaffold/repair flow.

## Source of truth

- **Bug**: `BUG-021` (Critical) — Workspace-Control scaffold/setup can create live `.gald3r/` control planes inside member repositories.
- **Task**: `Task 213` (spec v1.1) — defines the marker-only policy and its enforcement layers.
- **Manifest**: `.gald3r/linking/workspace_manifest.yaml` → `routing_policy.member_gald3r_invariant`.
- **Helper scripts** (gald3r_dev root + `gald3r_template_full/scripts/` for installed projects):
  - `scripts/check_member_repo_gald3r_guard.ps1` — marker-aware preflight
  - `scripts/bootstrap_member_gald3r_marker.ps1` — only sanctioned writer of member `.gald3r/`
  - `scripts/remediate_member_gald3r_marker.ps1` — non-destructive cleanup of forbidden member content
  - `scripts/validate_workspace_members_gald3r.ps1` — workspace-wide marker compliance audit

## Guard call contract

Before any code path writes a `.gald3r/` file inside a member repository, call the guard:

```powershell
# Per-path check (preferred — most precise)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_member_repo_gald3r_guard.ps1 `
    -TargetPath "<absolute_member_repo_path>" `
    -DotGald3rPath "<relative_path_inside_dot_gald3r>"
$exit = $LASTEXITCODE
```

| Mode | What it answers |
|------|-----------------|
| `-DotGald3rPath ".identity"` or `-DotGald3rPath "PROJECT.md"` | ALLOW (marker-safe) |
| `-DotGald3rPath "TASKS.md"` (or any control-plane path) | BLOCK |
| `-AllowMarkerInit` (no path) | ALLOW (caller asserts marker bootstrap intent; bootstrap helper enforces actual filesystem allowlist) |
| Default (no path, no flags) | BLOCK on member targets — caller must specify intent |

Exit codes: `0` ALLOW, `1` BLOCK, `2` ERROR. Optional flags: `-WarnOnly`, `-Json`, `-ManifestPath`.

## Bootstrap call contract (the only legal `.gald3r/` writer for members)

When a member is added, adopted, or spawned, create the marker via:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -MemberId "<manifest_repo_id>" `
    -ControllerPath "<absolute_controller_path>" `   # optional: defaults to upward manifest discovery
    -Apply                                            # omit for dry-run
```

The bootstrap helper:

1. Confirms membership via the guard (`-AllowMarkerInit` mode).
2. Refuses to proceed if existing `.gald3r/` already contains forbidden content — directs the user to remediate first.
3. Creates `.gald3r/.identity` (if absent) tying the member back to the controller (member project_id, member project_name, controller project_id, controller path, `member_gald3r_marker_only=true`).
4. Creates `.gald3r/PROJECT.md` (if absent) as a member-stub identifying the member + cross-linking to the controller.
5. Preserves any pre-existing `.identity` or `PROJECT.md`.
6. Refuses to write any other path.

## Remediation call contract (existing violation cleanup)

When a member already contains live control-plane content, remediate it:

```powershell
# Dry-run first
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>"

# Apply (quarantines forbidden entries to `.gald3r-quarantine/<timestamp>/`)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -Apply
```

Remediation **never deletes**; it quarantines forbidden entries to `<member>/.gald3r-quarantine/<timestamp>/` (or to an explicit `-BackupTo` path). The marker pair (`.identity` + `PROJECT.md`) is preserved in place. The user controls final disposition of the quarantine folder.

## Validation call contract

Audit all manifest members at any time:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_workspace_members_gald3r.ps1
```

Reports per-member compliance: `clean` / `marker_missing` / `has_violations` / `not_yet_created`. Exit `0` if all clean, `1` if any have violations (use `-WarnOnly` for advisory mode). Required as part of pre-adoption preflight before any new member (e.g. `gald3r_valhalla`) is added.

## Skill / command preflight requirements

The following surfaces MUST call the guard before writing live `.gald3r/` content, and MUST call the bootstrap helper as the sanctioned writer:

- **`g-skl-workspace`**:
  - `SPAWN_APPLY` — after creating directory + git init + minimal `.gitignore`/`README.md`, call bootstrap with `-Apply` to create the marker pair.
  - `ADOPT_APPLY` — refuse if target's `.gald3r/` already contains live control plane (require remediation first); then call bootstrap to ensure marker is present.
  - `MEMBER_ADD_APPLY` — when path exists, call bootstrap; when path is planned, defer to first SPAWN/ADOPT.
  - New ops: `MEMBER_MARKER_BOOTSTRAP`, `MEMBER_MARKER_REMEDIATE`, `MEMBER_MARKER_VALIDATE`.
- **`g-skl-setup`** — Step 0 calls the guard. If target is a controlled_member, BLOCK setup (members get marker-only via `g-wrkspc-spawn` / `g-wrkspc-adopt`, not full setup).
- **`g-skl-pcac-spawn`** — Pre-Flight Checks call the guard. PCAC-spawning a project INTO a controlled member path is forbidden (PCAC spawn = new standalone project, not a workspace member; use `g-wrkspc-spawn` for workspace members).
- **`g-skl-pcac-adopt`** — Step 2.5 calls the guard for `.gald3r/linking/` writes against the target. If target is a workspace member, switch to `--one-way` automatically (skip the target write) and direct user to `@g-wrkspc-adopt` for full Workspace-Control adoption.
- **`gald3r_install` MCP tool** — before writing `.gald3r/.project_id`, `.gald3r/.vault_location`, `.gald3r/.user_id`, call the guard. If member match, refuse and direct to bootstrap helper instead.
- **Future workflows** (`@g-wrkspc-init`, scaffold/repair tools) that materialize `.gald3r/` files at an arbitrary path.

## Pre-adoption preflight (gald3r_valhalla and any future populated member)

Before adopting an existing populated gald3r project (e.g. `gald3r_valhalla`) as a Workspace-Control member, the operator MUST:

1. Run `scripts/validate_workspace_members_gald3r.ps1` to baseline current workspace marker compliance.
2. Run `scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <candidate>` to confirm the candidate would be classified as a member after adoption.
3. Inspect the candidate's existing `.gald3r/` for live control plane.
4. If live control plane is present, do NOT silently overwrite. Either:
   - **Adopt the project's history** via the upcoming Workspace-Control populated-gald3r adoption flow (Tasks 214–217). The flow imports active items into the controller with provenance, archives terminal items, and reduces the candidate's `.gald3r/` to the marker pair via remediation.
   - **Defer adoption** until cleanup/migration is complete.
5. Pass marker bootstrap only after preflight + remediation + history import are all complete.

The adoption preflight refuses to overwrite an existing real `.gald3r/` control plane. It reports the required migration or cleanup steps instead of mutating it.

## Existing-violation handling (e.g. gald3r_throne)

If a member repository already contains a live control plane (the historical `gald3r_throne` case), the agent MUST:

1. Surface the violation explicitly in the session summary.
2. Refuse any new write that would touch the existing live state without explicit remediation.
3. Recommend the user run `remediate_member_gald3r_marker.ps1` (dry-run, then `-Apply`) followed by `bootstrap_member_gald3r_marker.ps1 -Apply` to land on the marker-only shape. Both helpers are non-destructive (the remediator quarantines, never deletes).
4. Cleanup is never bundled with prevention work — it gets its own task with explicit user authorization.

## Rationalization table

| Rationalization | Reality |
|---|---|
| "It's just a small TASKS.md stub" | A stub is still live control plane. Member `.gald3r/` is marker-only. |
| "The member needs its own task tracker" | The controller IS the task tracker. Members don't have parallel state. |
| "I'll mark it gitignored" | Gitignored is not the boundary. The bug is the existence of live state. |
| "But T197 created `.gald3r/TASKS.md` and it shipped" | That violated the policy. T213 v1.1 + remediate fix it; bootstrap creates the correct marker. |
| "The manifest has `write_allowed: true` for gald3r_throne" | `write_allowed: true` does not extend to `.gald3r/` control plane. See `member_gald3r_invariant.marker_allowlist` and `disallowed_paths` in the manifest. |
| "I just need a quick `.gald3r/PLAN.md` for this member" | No. PLAN.md is controller-only. The member's mission goes in `PROJECT.md`. |

## Template directory exception (mandatory honor)

Paths matching `**/template_(slim|full|adv)/**` carry deliberate `.gald3r/` template content. The guard helper recognizes these paths and returns ALLOW with reason `template_directory_exception`. Do **not** add additional carve-outs — the only legitimate `.gald3r/` writes outside the control project are template content under those three directories.
