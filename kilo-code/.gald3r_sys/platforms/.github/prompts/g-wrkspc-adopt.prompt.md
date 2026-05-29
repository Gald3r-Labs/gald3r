Adopt an existing gald3r project into Workspace-Control: $ARGUMENTS

## What This Command Does

Brings an existing gald3r-managed project (one that already has a populated `.gald3r/` folder with tasks, bugs, features, PRDs, subsystem specs, plans, constraints, and linking data) into the current Workspace-Control control project. Plans or applies the adoption; never writes the source project's `.gald3r/`. Delegates to `g-skl-workspace` operation `ADOPT` in one of three modes: discover (preflight + inventory), dry-run (writes the plan report), or apply (gated state change).

The full design lives at `docs/20260426_090736_Cursor_WORKSPACE_CONTROL_PROJECT_ADOPTION.md`.

## Adoption Mode

This command is the surface for the **`populated_gald3r_adoption`** mode — adoption of an existing full gald3r project that already manages its own active task/bug/feature/PRD history. This mode is mutually exclusive with the other three Workspace-Control adoption-shaped operations:

- `clean_member_registration` → use `@g-wrkspc-member-add`
- `spawned_member_creation` → use `@g-wrkspc-spawn`
- `marker_only_member_repair` → use `MEMBER_MARKER_BOOTSTRAP/REMEDIATE/VALIDATE`

Pick exactly one mode before any preflight runs. If the candidate path is ambiguous (e.g. `.gald3r/.identity` exists but no `TASKS.md`), this command refuses and asks the user to choose explicitly. It never silently routes a populated source through SPAWN or MEMBER_ADD.

The mode label `populated_gald3r_adoption` is recorded in:

- the dry-run plan front-matter (`adoption_mode: populated_gald3r_adoption`)
- the apply ledger
- the manifest member entry's `adoption.adoption_mode` field after apply
- the active task's frontmatter when the task drives adoption work

## Modes

- `--discover {path}` — preflight + read-only inventory; writes nothing.
- `--dry-run --source {path} --as {member_id}` — generates `.gald3r/reports/adoption_{adopt-id}.md`. Writes only the report file.
- `--apply --source {path} --as {member_id} --plan {report-path}` — gated apply. Writes only the control project's `.gald3r/` and the workspace manifest.

Dry-run is the default. Apply requires explicit `--apply`, a valid `--plan` path, plan freshness, signature match, and explicit user confirmation.

## Required Arguments

| Mode      | Required                                                          |
|-----------|-------------------------------------------------------------------|
| discover  | `--discover <path>`                                               |
| dry-run   | `--source <path>`, `--as <member_id>`                             |
| apply     | `--source <path>`, `--as <member_id>`, `--plan <report-path>`     |

Optional flags (apply mode):

- `--plan-max-age-hours N` (default 24)
- `--reuse-id` (reuse the plan's `adoption_operation_id` even if recomputed value differs — for resumes only)
- `--allow-readopt` (re-adopt a member already in `lifecycle_status: active`)

## Workflow

1. Activate `g-skl-workspace`.
2. Default to `ADOPT --dry-run` semantics unless `$ARGUMENTS` includes `--discover` or `--apply`.
3. Run preflight (Phase 1):
   - Manifest exists and parses cleanly.
   - Source `{path}` exists, is reachable, is an independent git root distinct from the control project, is not a symlink/junction, contains `.gald3r/.identity` (or `.project_id`) and `.gald3r/TASKS.md`.
   - Source path is not nested inside the control project working tree.
4. In discover mode: print inventory summary; stop.
5. In dry-run mode: write `.gald3r/reports/adoption_{adopt-id}.md`; print summary; stop.
6. In apply mode: re-run preflight + discovery; verify plan freshness and signature; verify the active task authorizes adoption work for `{member_id}`; verify manifest write policy via `ENFORCE_SCOPE`; then write provenance-tagged control-project records, archive entries (Task 204 buckets), reference stubs, manifest member update, and the apply ledger; print result.

## Adoption Operation ID Format

```text
adopt-YYYYMMDD-HHMMSS-{project_slug}
```

UTC timestamp at the start of discovery, plus a slug derived from the source `.gald3r/.identity` `project_name`.

## Provenance (every imported / control-visible record)

```yaml
adoption:
  source_project_id: ""
  source_project_name: ""
  source_project_path: ""
  source_artifact_type: ""        # task | bug | feature | prd | subsystem | constraint | plan | linking
  source_artifact_id: ""
  source_artifact_path: ""
  adopted_as_id: ""
  adoption_operation_id: ""
  adoption_class: ""              # active-control-visible | archived-reference | link-only | merge-candidate | conflict-deferred
  member_id: ""
```

Provenance fields are never stripped on subsequent edits.

## Active Index Visibility

Active imported tasks and bugs (class `active-control-visible`) appear in `.gald3r/TASKS.md` and `.gald3r/BUGS.md` with an `[adopted:{member_id}]` prefix appended to the existing emoji block. Terminal items go straight to the Task 204 archive buckets and never cross the active index.

## Archive Routing for Terminal Imports

Completed tasks and resolved bugs route through the Task 204 archive structure:

- `.gald3r/archive/archive_tasks_{range}.md` and `.gald3r/archive/archive_bugs_{range}.md` get a dedicated `## Adopted from {member_id} ({adoption_operation_id})` section per adoption.
- Bucket allocation by archive entry ordinal (T204 rule), not by original task/bug ID.
- Archived files at `.gald3r/archive/tasks/tasks_{range}/task{adopted_id}_{slug}_adopted.md` (and bug equivalent), with BOTH the standard `archive:` block AND the `adoption:` block in frontmatter.

## Manifest Member Status Update

After successful apply, the manifest member entry for `{member_id}` is updated atomically with the apply transaction. Adds `lifecycle_status: adopted`, `repo_role: external_gald3r_project`, and an `adoption:` block recording the operation ID, plan path, apply ledger path, and per-type artifact counts. The manifest update is registry-only; no member repository file is touched.

## Safety Boundaries

- Dry-run is the default; apply requires explicit `--apply` AND a valid `--plan` path.
- The source project's `.gald3r/` is opened read-only at every phase. ADOPT never writes the source.
- No silent overwrite of control-project artifacts; collisions must be resolved by an explicit plan decision.
- Member repository files are never modified by ADOPT (member-repo writes still require a separate task with explicit `workspace_repos` authorization).
- PRD freeze gate (g-rl-33) is honored: imported `released` PRDs land frozen with an `adopted: true` change-log entry.
- Apply is transactional; failure rolls back partial writes and records the rollback in the apply ledger.

## Refusals

Any of the following raise a `BLOCK` finding and abort:

**Preflight / source shape**

- `BLOCK adoption_preflight_failed`
- `BLOCK source_not_independent_git_root`
- `BLOCK source_gald3r_minimum_missing` — `.gald3r/.identity` (or legacy `.project_id`) AND `TASKS.md` are required
- `BLOCK source_gald3r_unreadable` — source `.gald3r/` exists but cannot be read (permissions, locked, antivirus)
- `BLOCK source_identity_ambiguous` — missing `project_id`/`project_name`, conflicting identity files, or project_id collision with controller without `--allow-id-collision`
- `BLOCK source_inside_control_project`
- `BLOCK source_symlink_or_junction`

**Plan / apply gate**

- `BLOCK adoption_member_already_active_no_readopt_flag`
- `BLOCK adoption_plan_missing`
- `BLOCK adoption_plan_stale`
- `BLOCK adoption_plan_signature_mismatch`
- `BLOCK adoption_apply_without_explicit_flag`
- `BLOCK adoption_destination_collision`
- `BLOCK adoption_required_field_missing`

**Repository state at apply time**

- `BLOCK source_repo_dirty_apply_mode` — uncommitted changes / merge in progress / pending worktrees on source; supply `--allow-source-dirty` or commit first
- `BLOCK control_repo_dirty_apply_mode` — controller has uncommitted changes outside the writes ADOPT itself plans, and `--require-clean-controller` was supplied
- `BLOCK pcac_conflict_gate_unresolved` — open `[CONFLICT]` in inbox; resolve via `@g-pcac-read` first

**Boundary preservation**

- `BLOCK adoption_member_repo_write_attempted`
- `BLOCK adoption_manifest_write_policy_refused`
- `BLOCK adoption_controller_manifest_unparseable`

## Usage Examples

```text
@g-wrkspc-adopt --discover G:/gald3r_ecosystem/gald3r_valhalla
@g-wrkspc-adopt --dry-run --source G:/gald3r_ecosystem/gald3r_valhalla --as gald3r_valhalla
@g-wrkspc-adopt --apply --source G:/gald3r_ecosystem/gald3r_valhalla --as gald3r_valhalla --plan .gald3r/reports/adoption_adopt-20260426-091500-gald3r_valhalla.md
```

## Cross-References

- Skill: `g-skl-workspace` operation `ADOPT` (sub-modes `ADOPT_DISCOVER`, `ADOPT_DRY_RUN`, `ADOPT_APPLY`).
- Design doc: `docs/20260426_090736_Cursor_WORKSPACE_CONTROL_PROJECT_ADOPTION.md`.
- Sample dry-run fixture: `.gald3r/reports/adoption_dryrun_sample.md`.
- Archive routing: Task 204 (`@g-task-archive`, `@g-bug-archive`).
- Manifest registry: `.gald3r/linking/workspace_manifest.yaml`.
- PCAC adoption (separate, complementary): `@g-pcac-adopt` registers parent/child topology for cross-project messaging; this command updates Workspace-Control state.
