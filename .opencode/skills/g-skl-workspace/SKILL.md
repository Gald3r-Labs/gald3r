---
name: g-skl-workspace
description: Workspace-Control Mode skill. Reads .gald3r/linking/workspace_manifest.yaml as the canonical registry and provides STATUS, VALIDATE, MEMBER LIST, SPAWN, ADOPT, EXPORT/SYNC dry-run planning, and member `.gald3r/` marker bootstrap/remediate/validate operations for manifest-declared repositories.
operations: [STATUS, VALIDATE, MEMBER_LIST, INIT_PLAN, INIT_APPLY, MEMBER_ADD_PLAN, MEMBER_ADD_APPLY, MEMBER_REMOVE_PLAN, MEMBER_REMOVE_APPLY, SPAWN_PLAN, SPAWN_APPLY, EXPORT_PLAN, SYNC_PLAN, PARSE_MANIFEST, ENFORCE_SCOPE, ADOPT_DISCOVER, ADOPT_DRY_RUN, ADOPT_APPLY, MEMBER_MARKER_BOOTSTRAP, MEMBER_MARKER_REMEDIATE, MEMBER_MARKER_VALIDATE]
min_tier: slim
---
# g-skl-workspace

**Files Read**: `.gald3r/linking/workspace_manifest.yaml`, task/bug frontmatter when validating routing metadata, repository paths named by the manifest, and per-repository git status/worktree metadata.

**Files Written**: none by default. This skill is read-only for member repositories except for the explicit `SPAWN_APPLY` lifecycle operation, which may create a new minimal independent git root and update the control project's workspace manifest when an active task authorizes it. It may only update `.gald3r/` task status when the active gald3r task workflow explicitly requires it.

**Activate for**: "workspace status", "workspace validate", "workspace manifest", "member list", "workspace export dry-run", "workspace sync dry-run", "workspace spawn", "spawn workspace member", "workspace adopt", "adopt gald3r project", `@g-wrkspc`, `@g-wrkspc-status`, `@g-wrkspc-validate`, `@g-wrkspc-member-list`, `@g-wrkspc-init --dry-run`, `@g-wrkspc-member-add --dry-run`, `@g-wrkspc-member-remove --dry-run`, `@g-wrkspc-spawn --dry-run`, `@g-wrkspc-spawn --apply`, `@g-wrkspc-export --dry-run`, `@g-wrkspc-sync --dry-run`, `@g-wrkspc-adopt --discover`, `@g-wrkspc-adopt --dry-run`, `@g-wrkspc-adopt --apply`, plus backwards-compatible `@g-workspace-*` aliases.

**Canonical Registry**: `.gald3r/linking/workspace_manifest.yaml`

Do not infer workspace members from sibling folder names, inferred `gald3r_template_*` siblings, git remotes, or docs artifacts. The Task 174 docs seed manifest is provenance only. The Task 179 YAML registry is the parseable source of truth.

---

## Purpose

`g-skl-workspace` is the read-only Workspace-Control Mode entry point. It lets agents inspect a configured workspace, validate the manifest and routing metadata, list controlled members, and explain export/sync plans before any future task authorizes writes. Every manifest repository is treated as an independent git root with its own status, branch, remote, rollback, and worktree context.

Task 170 defines the shared worktree primitive for those git boundaries. When a workflow needs isolation, it must call the Gald3r worktree helper per repository, not once at the workspace root. In gald3r_dev the helper is `scripts/gald3r_worktree.ps1`; installed templates carry the same helper in the `g-skl-git-commit/scripts/` skill directory for each IDE target. Worktree root defaults to `$env:GALD3R_WORKTREE_ROOT` or `<repo-parent>/.gald3r-worktrees/<repo-name>`, branch names use `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}`, and cleanup may only remove directories that contain `.gald3r-worktree.json` ownership metadata.

### g-go blast-radius clean gates (T495 / T496)

`g-rl-33` **Clean Controller** and **Pre-Reconciliation** gates apply per **git root** in the computed **touch set**: always the orchestration checkout; plus manifest-resolved roots for task/bug `workspace_repos:` (v1); optionally `extended_touch_repos:`, swarm coordinator `touch_repos:`, and subsystem spec `locations:` entries that are **absolute filesystem paths** (v2). Each included root gets the same `git status --short` + explicit coordinator allowlist discipline described elsewhere in this skill for export/adopt/member-write preflights. Use **this skill** and `workspace_manifest.yaml` as the authoritative map from `repository.id` → `local_path`; report planned-missing members per lifecycle rules **without** expanding the touch set until paths exist.

Workspace-Control differs from PCAC:

- PCAC coordinates independent projects through topology, INBOX messages, orders, requests, dependencies, and peer snapshots.
- Workspace-Control routes local agent scope across an explicit member allow-list owned by one control project.
- PCAC state is not a filesystem write allow-list.
- Workspace-Control does not create member-local tasks or mutate member repositories unless a lifecycle operation such as `SPAWN_APPLY` is explicitly requested and authorized by the active task.

---

## Required Inputs

### Manifest Path

Always look for:

```text
.gald3r/linking/workspace_manifest.yaml
```

If the file is absent, report quietly:

```text
Workspace-Control: inactive (no .gald3r/linking/workspace_manifest.yaml)
Scope: current repository only
```

Then stop unless the user explicitly asked for troubleshooting.

---

## Operation: INIT PLAN / INIT APPLY

**Usage**: `@g-wrkspc-init --dry-run` or `@g-wrkspc-init --apply`

Initializes Workspace-Control in the current project by creating or promoting `.gald3r/linking/workspace_manifest.yaml` as the canonical registry.

### INIT PLAN Steps

1. Confirm the current project has `.gald3r/` and is a git root.
2. If `.gald3r/linking/workspace_manifest.yaml` exists, parse it and report that Workspace-Control is already active.
3. If the canonical manifest is absent, look for an explicitly supplied seed file argument or a docs seed manifest such as `docs/*WORKSPACE_CONTROL_MANIFEST.yaml`.
4. Validate the seed with PARSE_MANIFEST rules before proposing promotion.
5. Report planned creates/updates only. Do not write files in plan mode.

### INIT APPLY Gate

Only write when the user supplies `--apply` and all of these are true:

- The active task explicitly authorizes Workspace-Control initialization.
- `.gald3r/linking/` exists or can be created inside the current project.
- The manifest parses successfully or the generated minimal manifest has owner repository data.
- Existing `.gald3r/linking/workspace_manifest.yaml` is not overwritten unless `--replace` is explicitly supplied and the prior manifest is summarized first.
- The command writes only `.gald3r/linking/workspace_manifest.yaml`; it never creates, deletes, moves, or edits member repository files.

Required apply output:

```text
Workspace init applied: .gald3r/linking/workspace_manifest.yaml
Member repositories were not modified.
```

## Operation: MEMBER ADD PLAN / MEMBER ADD APPLY

**Usage**: `@g-wrkspc-member-add <path> --id <repo_id> --role <role> --dry-run|--apply`

Adds a repository entry to the Workspace-Control manifest. The path may be absent, but apply mode must make that explicit in the lifecycle state.

### Required Arguments

- `--id <repo_id>`: stable manifest routing key, matching `schema.parse_contract.repository_id_pattern` or `^[a-z][a-z0-9_]*$`.
- `--path <path>` or first positional `<path>`: local repository path.
- `--role <control_project|controlled_member|migration_source>`: workspace role.
- `--repo-role <freeform_role>`: optional public role label; default from `--role`.

### MEMBER ADD PLAN Checks

1. Run PARSE_MANIFEST; if inactive, tell the user to run `@g-wrkspc-init --dry-run` first.
2. Reject duplicate repository IDs.
3. Normalize the path for parser stability; do not infer IDs from folder names when `--id` is absent.
4. If the path exists, report symlink/junction status, git root, branch, dirty count, remotes, and worktree context.
5. If the path is inside the control project, require `--role migration_source` or block.
6. Report the manifest fields that would be added, including `allowed_write_policy.default_policy` and `workspace_role`.
7. Default controlled members to `write_allowed: false` unless the active task explicitly authorizes a write-enabled member.

### MEMBER ADD APPLY Gate

Apply may update only `.gald3r/linking/workspace_manifest.yaml`. It must not initialize git, create folders, copy files, set remotes, or write into the member path. If the member path is missing, record `lifecycle_status: planned_clean_member` and keep writes blocked.

## Operation: SPAWN PLAN / SPAWN APPLY

**Usage**: `@g-wrkspc-spawn <project_name> --id <repo_id> --path <path> --dry-run|--apply`

Creates and registers a new local Workspace-Control member project. This mirrors the simplicity of `@g-pcac-spawn`, but it is strictly local workspace membership, not PCAC topology.

Use SPAWN when the destination folder is new or intentionally empty and the control project needs a clean independent git root for future work, such as `gald3r_throne`. Do not use SPAWN for existing gald3r projects with task/bug history; use `@g-wrkspc-adopt`. Do not use SPAWN for an already-created repo that only needs registry metadata; use `@g-wrkspc-member-add`.

### Required Arguments

- `<project_name>`: folder/display slug for the new member project.
- `--id <repo_id>`: stable manifest routing key, matching `schema.parse_contract.repository_id_pattern` or `^[a-z][a-z0-9_]*$`.
- `--path <path>`: absolute local path for the new independent repository.

Optional arguments:

- `--description "..."`: one-line role/mission stored in the manifest description fields.
- `--template none|slim|full|adv`: optional future gald3r template intent. Default `none`; this operation does not install gald3r templates unless a later task explicitly extends it.
- `--allow-existing-empty`: permit an existing empty target directory.
- `--role controlled_member`: default and currently the only non-owner role SPAWN should create.

### SPAWN PLAN Checks

1. Run PARSE_MANIFEST; if inactive, tell the user to run `@g-wrkspc-init --dry-run` first.
2. Reject duplicate repository IDs.
3. Normalize `--path` and verify it is outside the control project working tree.
4. Refuse symlink or junction targets.
5. If the path exists, require it to be an empty directory unless `--allow-existing-empty` is supplied; if it contains `.git/`, use MEMBER_ADD or ADOPT instead.
6. If the path is absent, report the exact folder that would be created.
7. Report the manifest entry that would be added:

```yaml
- id: <repo_id>
  display_name: <project_name>
  local_path: <path>
  workspace_role: controlled_member
  repo_role: workspace_member
  lifecycle_status: planned_clean_member
  canonical_source_status: empty_member_repo
  allowed_write_policy:
    default_policy: no_direct_writes_until_task_authorized
    inspect_allowed: true
    write_allowed: false
```

8. Report that no app runtime, generated template output, PCAC topology, remotes, tasks, bugs, PRDs, or source files will be created by SPAWN.

### SPAWN APPLY Gate

SPAWN_APPLY may run only when all gates pass:

1. The user supplied explicit `--apply`.
2. The active task explicitly authorizes workspace spawning for `<repo_id>`.
3. PARSE_MANIFEST and SPAWN PLAN checks pass at apply time.
4. The target path is absent or is an existing empty directory with `--allow-existing-empty`.
5. The destination is not inside the control project and is not a symlink/junction.
6. The control project's manifest is cleanly writable and ENFORCE_SCOPE permits the manifest update.
7. **Member `.gald3r/` marker-only guard (BUG-021 / Task 213 v1.1 / g-rl-36)**: run the guard helper in marker-init mode, then create the marker pair via the bootstrap helper.

   ```powershell
   # Confirm member-init is allowed
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_member_repo_gald3r_guard.ps1 -TargetPath "<absolute_target_path>" -AllowMarkerInit
   # Bootstrap .gald3r/.identity and .gald3r/PROJECT.md
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_member_gald3r_marker.ps1 -MemberPath "<absolute_target_path>" -MemberId "<repo_id>" -Apply
   ```

   The guard at exit `1` (BLOCK) refuses apply with `BLOCK spawn_member_repo_gald3r_guard_block`. Exit `2` (ERROR) refuses with `BLOCK spawn_member_repo_gald3r_guard_error`. Bootstrap may itself BLOCK with `BLOCK spawn_member_gald3r_has_control_plane` when the existing `.gald3r/` already contains forbidden content — in that case point the user to `scripts/remediate_member_gald3r_marker.ps1` first. Only the combination of guard ALLOW + bootstrap success completes SPAWN_APPLY.

Allowed apply writes:

- Create the target directory when absent.
- Run `git init` inside the target directory.
- Write a minimal `.gitignore` that blocks common secrets and local tooling output when no `.gitignore` exists.
- Write a minimal `README.md` with the project name and workspace provenance when no `README.md` exists.
- Update only `.gald3r/linking/workspace_manifest.yaml` in the control project.

Forbidden apply writes:

- Do not install gald3r into the member repo.
- Do not create member `.gald3r/` task, bug, feature, PRD, subsystem, or linking files.
- Do not copy app scaffolds or runtime source.
- Do not create remotes, branches beyond the default initial branch, tags, commits, or worktrees.
- Do not write PCAC topology/INBOX/order files.
- Do not import/adopt existing history; ADOPT owns that flow.

Required apply output:

```text
Workspace member spawned: <repo_id> at <path>
Created independent git root: yes
Manifest updated: .gald3r/linking/workspace_manifest.yaml
Member source/app files were not scaffolded.
PCAC topology was not modified.
```

### Refusals

SPAWN raises any of the following BLOCK findings with a single-line remediation:

- `BLOCK workspace_manifest_inactive`
- `BLOCK spawn_repo_id_duplicate`
- `BLOCK spawn_path_inside_control_project`
- `BLOCK spawn_path_symlink_or_junction`
- `BLOCK spawn_path_non_empty`
- `BLOCK spawn_existing_git_root_use_member_add_or_adopt`
- `BLOCK spawn_apply_without_explicit_flag`
- `BLOCK spawn_active_task_not_authorized`
- `BLOCK spawn_manifest_write_policy_refused`
- `BLOCK spawn_member_repo_gald3r_guard_block` — `scripts/check_member_repo_gald3r_guard.ps1` returned exit 1 for the target path (member repos cannot receive live control plane; only `.identity` + `PROJECT.md` are allowed)
- `BLOCK spawn_member_repo_gald3r_guard_error` — guard helper returned exit 2 (manifest unparseable or other error); resolve before retrying
- `BLOCK spawn_member_gald3r_has_control_plane` — bootstrap helper refused because the existing `.gald3r/` already contains forbidden content; run `scripts/remediate_member_gald3r_marker.ps1` (dry-run, then `-Apply`) first

## Operation: MEMBER REMOVE PLAN / MEMBER REMOVE APPLY

**Usage**: `@g-wrkspc-member-remove <repo_id> --dry-run|--apply`

Removes or deactivates a repository entry in the manifest. This is registry-only and never deletes files.

### MEMBER REMOVE PLAN Checks

1. Run PARSE_MANIFEST.
2. Confirm the repository ID exists.
3. Block removal of `workspace.owner_repository_id` unless a replacement owner is explicitly part of a separate approved migration task.
4. Report affected fields: `repositories[]`, `controlled_members.repository_ids`, `expected_count`, source/export relationships, and any task/bug routing references that still name the repository.
5. Recommend `lifecycle_status: retired` when historical routing references exist; recommend removal only when no references exist.

### MEMBER REMOVE APPLY Gate

Apply may update only manifest registry fields. It must not delete the repository folder, `.git/`, branches, remotes, worktrees, tasks, bugs, or generated output. Output must include:

```text
Member registry updated. No repository files were deleted.
```

### Structured Parsing

Use a structured YAML parser when reading the manifest. Do not parse YAML by splitting lines, matching indentation manually, or scanning folder names.

Required top-level keys come from the manifest itself:

```yaml
schema:
  parse_contract:
    required_top_level_keys:
      - schema
      - workspace
      - repositories
      - controlled_members
      - routing_policy
      - pcac_relationship
```

If `schema.parse_contract.required_top_level_keys` is missing, fall back to the six keys above and report that the parse contract was missing.

---

## Operation: PARSE_MANIFEST

**Usage**: internal helper operation for all other operations.

1. Load `.gald3r/linking/workspace_manifest.yaml` with a YAML parser.
2. Confirm the parsed value is a mapping/object.
3. Read `schema.parse_contract.required_top_level_keys`.
4. Build a repository map keyed by `repositories[].id`.
5. Build a controlled member set from `controlled_members.repository_ids`.
6. Build valid touch-policy values from `routing_policy.workspace_touch_policy_values`.
7. Return:

```yaml
manifest_path: .gald3r/linking/workspace_manifest.yaml
workspace_id: <workspace.id>
workspace_lifecycle_status: <workspace.lifecycle_status>
owner_repository_id: <workspace.owner_repository_id>
repositories_by_id: <map>
controlled_member_ids: <list>
valid_touch_policies: <list>
parse_findings: <list>
```

### Parse Rejection Conditions

Reject the manifest for Workspace-Control use when any of these are true:

- The file cannot be parsed as YAML.
- The root value is not a mapping/object.
- Any required top-level key is missing.
- `repositories` is absent or is not a list.
- A repository entry lacks `id`, `local_path`, `workspace_role`, `lifecycle_status`, or `allowed_write_policy`.
- Two repository entries use the same `id`.
- `workspace.owner_repository_id` is not present in the repository map.
- A `controlled_members.repository_ids` entry is not present in the repository map.

Use actionable findings: name the key, repository ID, and expected shape.

---

## Operation: STATUS

**Usage**: `@g-wrkspc-status` or `@g-workspace-status`

STATUS gives a compact read-only summary of the configured workspace.

### Steps

1. Run PARSE_MANIFEST.
2. If inactive, return the quiet current-repo-only message.
3. Display workspace identity:
   - `workspace.id`
   - `workspace.display_name`
   - `workspace.lifecycle_status`
   - `workspace.feature_id`
   - `workspace.owner_repository_id`
   - manifest path
4. Display member repositories:
   - `id`
   - `display_name`
   - `workspace_role`
   - `repo_role`
   - `lifecycle_status`
   - `canonical_source_status`
   - `local_path`
   - path reachability (`present` or `missing`)
   - independent git root status (`git rev-parse --show-toplevel`)
   - branch or detached state
   - dirty entry count from `git status --short`
   - remote count or names
   - worktree context from `git worktree list --porcelain` when reachable
   - rollback boundary (this repo only; no shared commit assumption)
   - `allowed_write_policy.default_policy`
   - `allowed_write_policy.write_allowed`
5. Display clean-repo expectations from each repository.
6. Display a concise boundary reminder:

```text
Write boundary: this skill is report-only. Member writes require a later task with explicit workspace_repos, workspace_touch_policy, apply-mode authorization, and independently reviewed git status for each member repo.
```

### Suggested Output

```text
Workspace: gald3r_dev Workspace-Control Bootstrap (active_bootstrap)
Manifest: .gald3r/linking/workspace_manifest.yaml
Owner: gald3r_dev

Repositories:
- gald3r_dev: active, control_project, path present, git root present, branch main, dirty N, remotes N, writes allowed by source_only_control_project
- gald3r_template_slim: planned_clean_member, controlled_member, path missing, git root missing (planned gap), writes blocked by no_direct_writes_during_bootstrap
- gald3r_template_full: planned_clean_member, controlled_member, path missing, git root missing (planned gap), writes blocked by no_direct_writes_during_bootstrap
- gald3r_template_adv: planned_clean_member, controlled_member, path missing, git root missing (planned gap), writes blocked by no_direct_writes_during_bootstrap
```

Keep STATUS concise. Do not print full manifest contents unless the user asks for detail.

---

## Operation: MEMBER LIST

**Usage**: `@g-wrkspc-member-list`

Lists only repositories declared in `repositories[]`. Never discover extra members by scanning directories.

Render each manifest repository ID exactly once. Do not repeat a member block in the main table, detail section, or boundary reminder; if a rendering mistake is noticed, correct the output before returning it.

### Output Fields

For each repository:

- `id`
- `display_name`
- `workspace_role`
- `repo_role`
- `local_path`
- `lifecycle_status`
- `canonical_source_status`
- path reachability
- git root path
- branch/detached state
- dirty entry count
- remote count
- worktree count
- `inspect_allowed`
- `write_allowed`

### Filters

If command arguments are available later, support these report-only filters:

- `--role control_project`
- `--role controlled_member`
- `--lifecycle active`
- `--lifecycle active_member`
- `--lifecycle adopted`
- `--lifecycle planned_clean_member`
- `--writes allowed|blocked`

Unknown filters should be rejected with the supported list.

---

## Operation: VALIDATE

**Usage**: `@g-wrkspc-validate` or `@g-workspace-validate`

VALIDATE checks manifest shape, routing metadata, and local path reachability without changing files.

### Manifest Checks

Run all PARSE_MANIFEST checks, plus:

1. Repository IDs match `schema.parse_contract.repository_id_pattern` or `^[a-z][a-z0-9_]*$`.
2. No duplicate repository IDs.
3. Every `repositories[].local_path` is non-empty.
4. Every `repositories[].lifecycle_status` is one of:
   - `active`
   - `active_bootstrap`
   - `active_member`
   - `adopted`
   - `planned_clean_member`
   - `migration_source`
   - `deprecated`
   - `retired`
5. Every `allowed_write_policy.default_policy` is present.
6. Every `allowed_write_policy.allowed_touch_policies` value appears in `routing_policy.workspace_touch_policy_values`.
7. Every `allowed_write_policy.allowed_future_policies` value appears in `routing_policy.workspace_touch_policy_values`.
8. `controlled_members.expected_count` equals the number of controlled member IDs.
9. `controlled_members.repository_ids` contains only repositories whose `workspace_role` is `controlled_member`.
10. `workspace.bootstrap_member_ids` contains the owner repository and every controlled member.
11. `workspace.source_of_truth.canonical_machine_registry` equals `.gald3r/linking/workspace_manifest.yaml`.
12. `workspace.source_of_truth.seed_manifest_artifact` may point to docs, but must not be treated as canonical.

### Local Path Checks

For each repository:

- Report whether `local_path` exists.
- If it exists, reject symlink or junction paths unless the active task explicitly treats the path as a migration source for read-only inspection.
- If it exists, run `git rev-parse --show-toplevel` from that path and verify the returned root equals `repository.local_path`. A nested checkout inside `gald3r_dev` is a blocking member-boundary finding unless `lifecycle_status: migration_source`.
- If it exists, report branch or detached state, `git status --short` dirty count, remotes, and `git worktree list --porcelain` count for that repository only.
- If it is a controlled member and missing, report as a planned/bootstrap gap, not a failure, when `lifecycle_status` is `planned_clean_member`.
- If it is a controlled member and present but not an independent git root, block validation for member-write readiness.
- If it is the owner repository and missing or not an independent git root, reject the manifest for workspace use.

### Routing Metadata Checks

When validating tasks or bugs, inspect only YAML frontmatter in `.gald3r/tasks/*.md` and `.gald3r/bugs/*.md` if the user asks for routing validation or a task/bug path is supplied. Use the canonical manifest repository map and touch-policy set from PARSE_MANIFEST; do not use hardcoded bootstrap IDs when the manifest exists.

Check:

- If `.gald3r/linking/workspace_manifest.yaml` is absent, Workspace-Control is inactive and omitted metadata means current repository only.
- If the manifest exists, every `workspace_repos` value must exist in `repositories[].id`; unknown member IDs are blocking findings.
- `workspace_touch_policy`, when present, must be one of `routing_policy.workspace_touch_policy_values`.
- Omitted `workspace_repos` means the owner/current repository only; it does not authorize sibling or controlled-member inspection or writes.
- Omitted `workspace_touch_policy` on current-repo-only work defaults to normal source work; any task or bug naming a controlled member must set it explicitly.
- Multiple repository IDs require an explicit `workspace_touch_policy`; controlled member IDs also require explicit task/bug authorization and cannot rely on legacy omitted metadata.
- `docs_only` permits documentation, `.gald3r/` planning metadata, task/bug records, manifest metadata, README, and CHANGELOG changes only; source, generated-output, and member-repo writes are outside scope.
- `source_only` permits hand-maintained source changes only in declared repos whose manifest policy allows writes for the active task.
- `generated_output` permits generated member output only in a future apply mode with canonical-source provenance and member clean-repo preflight.
- `multi_repo` requires every inspected or modified repository to be listed and treats each git root as an independent boundary.

### Operation: ENFORCE_SCOPE

**Usage**: internal gate reused by task, bug, implementation, review, and git sanity workflows. It checks a proposed or actual file-change set against the active task/bug routing metadata and `.gald3r/linking/workspace_manifest.yaml`.

Inputs:

```yaml
item_type: task | bug | ad_hoc
item_path: .gald3r/tasks/taskNNN_name.md
workspace_repos: []      # optional from item frontmatter
workspace_touch_policy: null
changed_paths: []        # repo-relative or absolute paths from planned edits, git diff, or staged files
status_history_note: null
```

Algorithm:

1. Run PARSE_MANIFEST. If inactive, allow only current-repository paths and treat workspace metadata as advisory no-op.
2. Resolve the owner repository from `workspace.owner_repository_id`. Treat omitted `workspace_repos` as `[owner_repository_id]`.
3. Validate all listed repository IDs against the manifest map. Any ID absent from `repositories[].id` is `BLOCK`.
4. Validate `workspace_touch_policy` against `routing_policy.workspace_touch_policy_values` when present. Member repos or multiple repos without an explicit policy are `BLOCK`.
5. Map each changed path to a manifest repository by `repository.local_path` when absolute, or to the owner repository when repo-relative. Paths that resolve into a manifest repo not listed in `workspace_repos` are `BLOCK`.
6. For controlled-member writes, require all of: member ID listed, explicit compatible policy, task/bug text authorizes member writes or generated output, manifest `allowed_write_policy.write_allowed: true` or a task-specific override, and member git status reviewed independently from the owner repo. During bootstrap, planned clean members with `write_allowed: false` remain blocked.
7. Enforce policy class:
   - `docs_only`: changed paths must be docs or metadata (`docs/`, `.gald3r/`, `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, command/skill documentation when the task is documentation-only).
   - `source_only`: changed paths must be hand-maintained source/config/docs in declared repos, not generated member output.
   - `generated_output`: require canonical source/provenance fields in the task/bug body and reject direct writes if member policy blocks them.
   - `multi_repo`: require every touched repo to be declared and report per-repo git boundaries; never assume a single commit spans repos; branch/worktree names must include the member repository ID when Tasks 170-172 worktree mode is used.
8. If an update widens scope from omitted/current-only to a member repo, adds any controlled-member ID, or changes policy to `generated_output`/`multi_repo`, require a Status History note or equivalent explicit instruction explaining why the scope widened. Without that note, return `BLOCK`.

Output findings use `PASS`, `WARN`, or `BLOCK`. Any `BLOCK` prevents task creation/update, bug creation/update, implementation handoff to `[🔍]`, review pass, or commit preparation until resolved.

### Git and Worktree Boundary Rules

- Resolve git roots per `repositories[].local_path`; never derive a member repo root by walking upward from `gald3r_dev`.
- Dirty/clean checks, branch checks, remotes, rollback instructions, and worktree metadata are per repository.
- Tasks 170-172 own the shared worktree primitive and coding/review integration. Workspace-Control only requires those primitives to run per manifest repository, with branch and worktree names that include the member ID for multi-repo work.
- Commit preparation must describe separate commits per member repository unless a later orchestration task explicitly coordinates a multi-repo release.
- A path nested inside the control project is a migration source folder, not a controlled member repo, unless the manifest explicitly marks it `lifecycle_status: migration_source`.

### Stale Routing Metadata References

Report stale references when:

- A task or bug names a repository ID that is not in the manifest.
- A task or bug uses a touch policy absent from manifest routing policy.
- A source-of-truth artifact path in the manifest no longer exists inside the control project.
- A repository `migration_source_path` points to a missing path while the repository is marked ready for export.
- A member repo is marked `active` but the local path is absent.

### Validation Result Format

```text
Workspace validation: PASS|FAIL
Manifest: .gald3r/linking/workspace_manifest.yaml
Findings:
- [PASS] required top-level keys present
- [FAIL] repositories[2].id duplicates gald3r_template_full
- [INFO] gald3r_template_slim path missing; allowed while lifecycle_status=planned_clean_member
```

Use `PASS` only when there are no blocking findings. Informational findings do not block.

### Malformed Manifest Sample

This sample must be rejected because it has no repository list and cannot route member IDs:

```yaml
schema:
  name: gald3r_workspace_control_manifest
workspace:
  id: broken_workspace
controlled_members:
  repository_ids:
    - gald3r_template_full
```

Expected findings:

```text
Workspace validation: FAIL
- [FAIL] missing required top-level key: repositories
- [FAIL] missing required top-level key: routing_policy
- [FAIL] missing required top-level key: pcac_relationship
```

---

## Operation: EXPORT PLAN

**Usage**: `@g-wrkspc-export --dry-run` or `@g-workspace-export --dry-run`

EXPORT PLAN describes what an export would do. It never writes files.

### Steps

1. Run VALIDATE.
2. Stop if manifest parsing has blocking findings.
3. For each controlled member repository:
   - Read `source_template_relationship.migration_source_path`.
   - Read destination `local_path`.
   - Read `allowed_write_policy.write_allowed` and `default_policy`.
   - Read clean-repo expectations.
   - Report independent git root, branch, dirty status, remotes, and worktree context for each reachable destination.
4. Report source and destination pairs.
5. Report planned action class:
   - `inspect only`
   - `would create generated output`
   - `blocked until apply task exists`
6. Report preflight gates that a future apply task must satisfy.

### Required Dry-Run Language

Every EXPORT PLAN must include:

```text
Dry-run only: no files were written. Member repository writes remain disabled until a later task explicitly authorizes apply mode.
```

### Future Apply Gate Checklist

A future apply task must prove all of these before writing a member repo:

- The active task names the member ID in `workspace_repos`.
- The active task has a compatible `workspace_touch_policy`.
- The manifest `allowed_write_policy.write_allowed` allows the operation or the task explicitly overrides it.
- The member repo path exists or creation is explicitly authorized.
- The member repo git status, branch, remotes, rollback boundary, and worktree context have been reviewed independently from `gald3r_dev`.
- No `.env`, vault data, `.git/`, local-only personality assets, private backend state, caches, or logs are staged for output.
- Generated output names its canonical source and generation task.
- Parity/tier checks have been run when IDE template content is involved.

### Task 184 Bootstrap/Export Helper

For `gald3r_dev` maintainers implementing Task 184, the concrete dry-run/apply helper is:

```powershell
.\scripts\workspace_template_export.ps1
```

The helper uses `uv run python scripts/workspace_template_export.py` to parse the canonical manifest with PyYAML, then plans or applies exports from:

- `gald3r_template_slim/` -> `gald3r_template_slim`
- `gald3r_template_full/` -> `gald3r_template_full`
- `gald3r_template_adv/` -> `gald3r_template_adv`

Default invocation is dry-run only. It reports source folders, destination member repo paths, planned creates/updates, unchanged files, skipped files, provenance output, symlink/junction checks, git-root, branch, clean-status, remote, worktree-context, rollback-boundary checks, hygiene findings, and apply blockers.

Apply mode exists only behind explicit helper flags and must rerun preflight immediately before writing. It never deletes destination files. Missing destination directories are initialized only with `--create-missing`; existing destinations must already be independent git roots with clean status. Manifest `write_allowed: false` remains a blocker unless a future task explicitly authorizes and passes `--allow-manifest-write-policy-override`.

---

## Operation: ADOPT (Existing Gald3r Project Adoption)

**Usage**:

- `@g-wrkspc-adopt --discover {path}` — preflight + read-only inventory; writes nothing.
- `@g-wrkspc-adopt --dry-run --source {path} --as {member_id}` — generates `.gald3r/reports/adoption_{adopt-id}.md`.
- `@g-wrkspc-adopt --apply --source {path} --as {member_id} --plan {report-path}` — gated apply that writes only the control project's `.gald3r/` and the manifest.

ADOPT brings an existing gald3r-managed project (one that already has a populated `.gald3r/` folder with tasks, bugs, features, PRDs, subsystem specs, plans, constraints, and linking data) into a Workspace-Control control project. It is the Workspace-Control mode operation for projects like `gald3r_valhalla` that pre-date adoption and must remain independent git roots with their own ongoing work.

ADOPT is not PCAC. It is not a task delegation. It does not write the source `.gald3r/`. It does not write member repository files. It only updates control-project state and the workspace manifest.

For the full design, see `docs/20260426_090736_Cursor_WORKSPACE_CONTROL_PROJECT_ADOPTION.md`.

### Adoption Modes (Named — Mutually Exclusive)

ADOPT distinguishes four mutually-exclusive named modes so agents and reviewers can route a candidate path to the correct command surface without ambiguity. Pick exactly one before any preflight runs:

| Mode                          | Surface                          | When to choose                                                                                  | Key invariant                                                                                  |
|-------------------------------|----------------------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `clean_member_registration`   | `@g-wrkspc-member-add`           | Path exists or is planned, contains no `.gald3r/` control plane, no app source to import         | Registry-only; never writes inside the member                                                  |
| `spawned_member_creation`     | `@g-wrkspc-spawn`                | Path is absent or is an existing empty directory; needs a fresh independent git root            | Creates the folder + `git init` + minimal `.gitignore`/`README.md` + member marker; no history |
| `marker_only_member_repair`   | `MEMBER_MARKER_BOOTSTRAP/REMEDIATE/VALIDATE` | Path exists, may have legacy `.gald3r/` content, must end in marker-only shape       | Bootstrap writes only `.identity` + `PROJECT.md`; remediation quarantines forbidden content    |
| **`populated_gald3r_adoption`** | `@g-wrkspc-adopt --discover/--dry-run/--apply` | Path is an existing **full** gald3r project with active `.gald3r/` task/bug/feature history (e.g. `gald3r_valhalla`) — never empty, never just a marker | Source `.gald3r/` is read-only at every phase; controller imports active items + archives terminal items + leaves source independent |

When a candidate path looks ambiguous (e.g. has `.gald3r/.identity` but no `TASKS.md`), default to refusing the operation and ask the user to choose explicitly. Do not silently route a populated source through SPAWN or MEMBER_ADD; doing so loses task/bug/feature/PRD history and breaks Task 213 / BUG-021 boundary policy.

The remaining ADOPT phases below all describe the `populated_gald3r_adoption` mode in detail. The other three modes are documented in their own sections.

### Mode: `populated_gald3r_adoption` — Existing Full Gald3r Project Adoption

This is the only ADOPT submode at present. It is the canonical path for adopting mature standalone gald3r projects (the prototype target is `G:/gald3r_ecosystem/gald3r_valhalla`) that already manage their own tasks, bugs, features, PRDs, releases, constraints, subsystems, plans, and PCAC linking data.

The mode name `populated_gald3r_adoption` is a stable identifier and may appear in:

- task/bug frontmatter as `adoption_mode: populated_gald3r_adoption`
- the dry-run plan front-matter as `adoption_mode: populated_gald3r_adoption`
- the manifest member entry's `adoption.adoption_mode` field after apply
- the apply ledger and any adoption-related session-summary lines

**Core invariants** (re-asserted from BUG-021 / Task 213 / g-rl-36):

- Source `.gald3r/` is opened **read-only** at every phase. ADOPT never writes the source — not in discovery, not in dry-run, not in apply.
- The source remains an **independent git root** owning its own commits, branches, remotes, and worktrees. ADOPT never pushes to the source remote, never rebases the source branch, never copies source git history into the controller.
- Adoption may produce **controller-visible mirrors and imports** (active task/bug rows, archived terminal records, reference stubs) while the source continues to own its own source code and packaging.
- Final apply lands the source in **marker-only** shape (`.identity` + `PROJECT.md`) only after explicit remediation + bootstrap helpers run with user confirmation. Apply must not silently quarantine forbidden content; remediation is its own gated step.

#### Discovery Inventory (Phase 2 — Read-Only)

`ADOPT_DISCOVER` MUST inventory every section of the source `.gald3r/` so the dry-run report and apply plan are complete. The inventory is read-only — no file is opened in write mode at any point. The minimum inventory list:

| Area                                | What discovery records                                                                                          |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------|
| Identity                            | `.gald3r/.identity` (or `.project_id` legacy file): project_id, project_name, gald3r_version, vault_location, user_id |
| Tasks                               | `.gald3r/TASKS.md` index + every `.gald3r/tasks/task*.md`: count, ID range, statuses, priorities, dependencies   |
| Bugs                                | `.gald3r/BUGS.md` index + every `.gald3r/bugs/bug*.md`: count, ID range, severity, statuses                       |
| Features                            | `.gald3r/FEATURES.md` index + every `.gald3r/features/feat*.md`: staging lifecycle status, harvest sources         |
| PRDs                                | `.gald3r/PRDS.md` index + every `.gald3r/prds/prd*.md`: governance lifecycle, supersedes-chain, freeze status     |
| Releases                            | `.gald3r/RELEASES.md` index + every `.gald3r/releases/release*.md`: target dates, assigned tasks                  |
| Constraints                         | `.gald3r/CONSTRAINTS.md` index + definition blocks: scope, expiry fields                                          |
| Subsystems                          | `.gald3r/SUBSYSTEMS.md` index + every `.gald3r/subsystems/*.md`: name, dependencies, locations, activity log size |
| Plans                               | `.gald3r/PLAN.md` headings + linked feature references                                                            |
| Project / mission                   | `.gald3r/PROJECT.md`: mission, goals, project linking section                                                     |
| Ideas                               | `.gald3r/IDEA_BOARD.md`: count, age distribution                                                                  |
| Linking / PCAC                      | `.gald3r/linking/INBOX.md`, `link_topology.md`, `sent_orders/*.md`, `pending_orders/*.md`, `peers/*`, capabilities |
| Reports                             | `.gald3r/reports/*.md`: count, kinds (heartbeats, SWOTs, SPRINT, KPI, prior adoption ledgers if any)              |
| Logs                                | `.gald3r/logs/*.log`: presence + sizes (never copied; flagged as transient)                                       |
| Experiments                         | `.gald3r/experiments/EXPERIMENTS.md`, `SELF_EVOLUTION.md`, `EXP-NNN.md`: active stages, autopsies                  |
| Archive buckets                     | `.gald3r/archive/archive_tasks_*.md`, `archive_bugs_*.md`, `archive/tasks/`, `archive/bugs/`: bucket count + entry ordinals |
| Specifications collection           | `.gald3r/specifications_collection/*.md`: count, mtimes                                                          |
| Learned facts                       | `.gald3r/learned-facts.md`: bullet count                                                                          |
| Unknown / custom folders            | Any other folder or file under `.gald3r/` not listed above: enumerated verbatim with sizes; never silently skipped |

If discovery encounters a folder it does not recognize, it MUST list it in the dry-run report under "Unknown areas" rather than failing or silently ignoring it. The user decides whether the area is in-scope for adoption.

#### Source Git Status Report (Phase 1 / Phase 4)

Discovery and apply both produce an **independent** git status report for the source repository. They never derive source state from the controller's git status. The report records:

- `git rev-parse --show-toplevel` — confirms independent root
- current branch or detached state
- ahead/behind count vs default upstream when available
- `git status --short` dirty entry count
- list of untracked paths (truncated)
- remote count + names
- `git worktree list --porcelain` count + the absolute path of each worktree
- rollback boundary: most recent commit SHA on the current branch
- whether the working tree contains any `.git/MERGE_HEAD`, `.git/REBASE_HEAD`, or other in-progress operation

A dirty source repository is **not** an automatic block in discovery or dry-run, but it IS a block in apply unless the user supplies `--allow-source-dirty` and the dry-run report explicitly carries the dirty state forward. See refusals below.

#### Controller Manifest State Check (Phase 1)

Before any phase touches source data, ADOPT confirms controller manifest readiness:

1. `.gald3r/linking/workspace_manifest.yaml` exists and parses cleanly via `PARSE_MANIFEST`.
2. The candidate `--as {member_id}` does not collide with an existing repository ID unless `--allow-readopt` is supplied.
3. The controller's git working tree is reviewed independently from the source. Apply requires the controller's `.gald3r/`, manifest, and report-output paths to be writable; a dirty controller working tree is not an automatic block but is recorded for review and may be blocked by `--require-clean-controller`.
4. PCAC inbox conflict gate: `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` is a hard prerequisite; an unresolved `[CONFLICT]` blocks apply (and is recorded as an advisory finding in discovery/dry-run).

#### Lifecycle State: `planned_adopting_member`

The manifest `lifecycle_status` vocabulary gains a new value, **`planned_adopting_member`**, for the in-flight state between the moment a candidate is registered (or earmarked) for populated adoption and the moment apply commits a final state. It is additive to the existing vocabulary and is recognized by `VALIDATE`.

Semantics:

- A repository may be entered into the manifest at `lifecycle_status: planned_adopting_member` so VALIDATE and STATUS can surface it without authorizing any source-side write.
- `allowed_write_policy.write_allowed` MUST be `false` while in this state.
- The manifest entry SHOULD include a placeholder `adoption:` block with `adoption_mode: populated_gald3r_adoption` and `adoption_operation_id` left blank until discovery runs.
- ADOPT_DISCOVER and ADOPT_DRY_RUN may run against a member in `planned_adopting_member` without any further manifest mutation.
- Successful ADOPT_APPLY transitions the member from `planned_adopting_member` → `adopted` atomically with the rest of the apply transaction. A failed apply leaves the member at `planned_adopting_member`; partial writes roll back per the existing apply ledger discipline.

This state exists specifically so the manifest can model "adoption is in progress, dry-run report exists, user has not yet authorized apply" without requiring writes into the source member repository. Workflows using this state must never treat it as authorization to modify the source.

#### Decision Gate Between Discovery and Apply

`ADOPT_DRY_RUN` is the user's review checkpoint. After dry-run writes `.gald3r/reports/adoption_{adopt-id}.md`, **all** of the following remain blocked until the user explicitly authorizes apply:

- controller `.gald3r/tasks/*` import writes
- controller `.gald3r/bugs/*` import writes
- controller archive bucket writes (Task 204)
- controller `TASKS.md` / `BUGS.md` row insertions
- manifest member entry transition from `planned_adopting_member` → `adopted`
- any source-side cleanup (`remediate_member_gald3r_marker.ps1 -Apply`)
- any source-side marker bootstrap (`bootstrap_member_gald3r_marker.ps1 -Apply`)

The decision gate is "user supplies `--apply` AND `--plan {report-path}` AND the plan is fresh AND its signature matches a re-run discovery". Anything weaker is refused; see the existing `BLOCK adoption_apply_without_explicit_flag` and `BLOCK adoption_plan_signature_mismatch` refusals below.

### Adoption Operation ID

Every ADOPT run produces a stable identifier:

```text
adopt-YYYYMMDD-HHMMSS-{project_slug}
```

- `YYYYMMDD-HHMMSS` is the UTC timestamp at the start of discovery.
- `{project_slug}` is derived from the source `.gald3r/.identity` `project_name` field, lowercased, non-alphanumerics replaced by `_`. Falls back to source folder basename when `.identity` is missing.

The `adoption_operation_id` is written to the dry-run plan, the apply ledger, every imported/control-visible record's frontmatter, the per-adoption ID-map index, and the manifest member's `adoption:` block.

### Provenance Metadata (every imported or control-visible record)

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

### Per-Artifact Adoption Plan (Five Classes)

| Class                    | Meaning                                                                                | Default for                                                                  |
|--------------------------|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `active-control-visible` | Full record copied; row appears in control TASKS.md/BUGS.md with `[adopted:{member_id}]` prefix | Active tasks/bugs                                                  |
| `archived-reference`     | Routed through Task 204 archive buckets; archived file body copied to bucket subfolder | Terminal tasks/bugs (`completed`/`failed`/`cancelled`/`resolved`/`closed`/`wont-fix`) |
| `link-only`              | Reference stub only; original lives in source repo; no file copy                       | Subsystems, plans, linking artifacts                                         |
| `merge-candidate`        | Surfaced for human decision; never auto-applied                                        | Active features/PRDs/constraints/subsystems with content overlap to local artifacts |
| `conflict-deferred`      | Listed in conflicts section; apply refuses to write until conflict-resolution flag is supplied | Subsystem name exact-match collisions, two-sided `released` PRD collisions |

### ID Mapping & Provenance Schema (T215)

The full ID-mapping, collision-handling, provenance, and frontmatter-upgrade schema lives in `docs/20260428_161456_Claude_GALD3R_ADOPTION_ID_MAPPING_PROVENANCE_SCHEMA.md`. The summary below is the operational quick-reference. Apply MUST conform to the schema doc; any divergence is a bug in this skill.

Per-artifact mapping (default classes; reviewer may override per-record at dry-run):

| Source type                                  | Default class                                  | Controller representation                                                                              | ID rule                                                                                  |
|----------------------------------------------|------------------------------------------------|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| Active task                                  | active-control-visible                          | `.gald3r/tasks/task{controller_id}_{slug}_adopted.md`                                                    | Allocate next sequential controller task ID                                              |
| Active subtask (`084-1`)                     | active-control-visible                          | `.gald3r/tasks/task{controller_id}-{suffix}_{slug}_adopted.md`                                            | Next controller parent ID; **dotted suffix preserved verbatim**                          |
| Terminal task                                | archived-reference                              | `.gald3r/archive/tasks/tasks_{range}/task{controller_id}_{slug}_adopted.md`                                | T204 ordinal slot; original ID in `archive.original_task_id`                             |
| Active bug                                   | active-control-visible                          | `.gald3r/bugs/bug{controller_id}_{slug}_adopted.md`                                                       | Allocate next `BUG-NNN`                                                                  |
| Terminal bug                                 | archived-reference                              | `.gald3r/archive/bugs/bugs_{range}/bug{controller_id}_{slug}_adopted.md`                                   | T204 ordinal slot; original `BUG-NNN` in `archive.original_bug_id`                       |
| Feature                                      | active-control-visible / archived-reference / merge-candidate | `.gald3r/features/feat{controller_id}_{slug}_adopted_{member_id}.md`                                | Allocate next `feat-NNN`; slug suffixed `_adopted_{member_id}_{source_id}`               |
| PRD (draft / review / approved / in-implementation) | active-control-visible                  | `.gald3r/prds/prd{controller_id}_{slug}_adopted_{member_id}.md`                                            | Next `prd-NNN`; supersedes-chain rewritten via per-adoption ID map                       |
| PRD (released / superseded)                   | conflict-deferred                               | Refused without `--resolve-conflict prd-{source_id}=mirror\|skip`                                       | Frozen status preserved verbatim                                                          |
| Release (active)                              | active-control-visible                          | `.gald3r/releases/release{controller_id}_{slug}_adopted_{member_id}.md`                                    | Next `release-NNN`; `assigned_tasks` rewritten via ID map                                 |
| Release (shipped / cancelled)                 | archived-reference                              | `.gald3r/archive/adopted/{member_id}/releases/release-{source_id}.md`                                       | Same                                                                                      |
| Constraint                                    | active-control-visible / archived-reference     | Definition block in `CONSTRAINTS.md` + index row                                                         | Next `C-NNN`; title suffixed `(adopted from {member_id})`; T120 `scope:` preserved        |
| Subsystem (no name overlap)                   | link-only                                        | `.gald3r/adopted/{member_id}/subsystems/{name}.md.ref`                                                    | Namespaced as `{name}-{member_id}`; never renumbered                                     |
| Subsystem (name exact match)                  | conflict-deferred                                | Refused without `--resolve-conflict subsystem-name={name}=keep-source\|keep-controller\|merge\|skip`   | See collision #6                                                                          |
| Plan / mission / project identity             | link-only                                        | `.gald3r/adopted/{member_id}/{filename}.ref`                                                              | Source canonical; controller never copies mission/plan body                              |
| Idea (`IDEA_BOARD.md`)                        | active-control-visible (open) / archived-reference (closed) | Section in controller `IDEA_BOARD.md`                                                       | Synthetic `idea-{member_id}-{seq}` ID for ID-map only                                    |
| Linking / PCAC                                | link-only                                        | `.gald3r/adopted/{member_id}/linking/{filename}.ref`                                                      | Source canonical                                                                          |
| Report                                        | link-only (default) / archived-reference (`--copy-reports`) | Stub or copy at `.gald3r/archive/adopted/{member_id}/reports/`                              | Never an active queue item (T215 AC9)                                                    |
| Log                                           | link-only (always)                                | `.gald3r/adopted/{member_id}/logs/{filename}.ref`                                                         | Bytes never copied                                                                        |
| Experiment (active)                           | merge-candidate                                  | `.gald3r/experiments/exp{controller_id}_{slug}_adopted_{member_id}.md`                                    | Next `EXP-NNN` after merge accept                                                         |
| Experiment (terminal)                          | archived-reference                              | `.gald3r/archive/adopted/{member_id}/experiments/EXP-{source_id}.md`                                      | Source ID preserved verbatim                                                              |
| Archive bucket (existing source)              | archived-reference                               | `.gald3r/archive/adopted/{member_id}/{tasks\|bugs}/{source_range}/`                                        | Source ranges preserved as a member-scoped sub-tree (collision #9)                        |
| Specifications collection                     | link-only                                        | `.gald3r/adopted/{member_id}/specifications_collection/{filename}.ref`                                     | Source canonical                                                                          |
| Learned facts                                 | link-only                                        | `.gald3r/adopted/{member_id}/learned-facts.ref`                                                            | Source canonical                                                                          |
| Unknown / custom folders                      | merge-candidate                                  | Refused without `--accept-unknown {pattern} as {class}`                                                   | Apply never silently routes unknown areas                                                 |

Bidirectional record:

1. Per-record frontmatter (`source_artifact_id`, `source_artifact_path`, `adopted_as_id`, `controller_artifact_id`, `controller_artifact_path`).
2. Per-adoption ID-map index at `.gald3r/reports/adoption_{adopt-id}_id_map.md` with **both** forward (source → controller) and reverse (controller → source) tables.
3. Optional verbatim source-frontmatter snapshots at `.gald3r/reports/adoption_{adopt-id}_snapshots/{source_artifact_id}.yaml` (apply only).

### Collision Matrix Summary (T215 §2)

13 deterministic collision types cover numeric ID, slug, title, `project_id`, duplicate-source-IDs, subsystem name (exact + fuzzy), release ID, archive bucket overlap, frozen-PRD adoption, member-id collision, source dirty, and plan-signature mismatch. Each has a fixed default decision (APPLY / WARN / BLOCK) and a documented override flag. The full table is in `docs/20260428_161456_Claude_GALD3R_ADOPTION_ID_MAPPING_PROVENANCE_SCHEMA.md` §2.

### Frontmatter Upgrade Rules Summary (T215 §6)

Source artifacts are **never rewritten in the first adoption pass** (T215 AC7). Controller-side copies gain the following synthesized fields when missing on the source:

| Field                       | Default when missing                                                                              |
|-----------------------------|----------------------------------------------------------------------------------------------------|
| `blast_radius`              | `medium`                                                                                           |
| `requires_verification`     | `true` for tasks; `true` for bugs of severity ≥ `high`; otherwise default                         |
| `ai_safe`                   | `true`                                                                                             |
| `spec_version`              | `"1.0"`                                                                                            |
| `execution_cost`            | `medium`                                                                                           |
| `workspace_repos`           | `[{member_id}]`                                                                                    |
| `workspace_touch_policy`    | `docs_only` (conservative; widens manually)                                                        |
| Status History (table)      | Synthesized 2-row table from `created_date` / `completed_date` with `Imported via adoption {adopt-id}` message |

Every synthesis is logged in the ID-map's "Frontmatter Upgrade Report" (schema doc §6).

### Logs & Reports Policy (T215 §8)

Logs and reports **must not** become active queue items in the controller. Logs are always `link-only`. Reports are `link-only` by default; `--copy-reports {pattern}` opts selected report patterns into `archived-reference` for compliance-grade SWOT/KPI capture only.

### Import Policy: Active vs Terminal Artifact Classification (T216)

The full lifecycle classification + import policy matrix lives in `docs/20260428_165201_Claude_GALD3R_ADOPTION_IMPORT_POLICY.md`. The summary below is the operational quick-reference. Apply MUST conform to the policy doc; any divergence is a bug in this skill.

**Per-artifact-type lifecycle classification** — every source artifact maps to exactly one of five adoption classes based on its source status:

| Source artifact type | Active status → class | Terminal status → class | Notes |
|---------------------|----------------------|------------------------|-------|
| Tasks | active-control-visible | archived-reference | Subtasks inherit parent class unless parent terminal + subtask active (orphan rendering). |
| Bugs | active-control-visible | archived-reference | Severity inferred when missing; `requires_verification: true` forced for severity ≥ High. |
| Features | active-control-visible (staging/specced) / merge-candidate (committed) | archived-reference | `committed` features need `--accept-merge feature={id}` because controller may have overlapping work. |
| PRDs | active-control-visible (draft/review/approved/in-implementation) | conflict-deferred (released/superseded) / archived-reference (archived) | C-019 freeze: released/superseded require `--resolve-conflict prd-{id}=mirror\|link\|skip`. |
| Releases | active-control-visible (planned/in-progress) | archived-reference (shipped/cancelled) | `assigned_tasks` rewritten via T215 ID map; roadmap_visibility preserved. |
| Constraints | merge-candidate (active, no controller coverage) / archived-reference (auto-expired) | archived-reference | T120 `scope:` preserved; title suffixed `(adopted from {member_id})`. |
| Subsystems | link-only (no name overlap) / merge-candidate (fuzzy match) | conflict-deferred (exact name match) | Namespaced as `{name}-{member_id}`; adopted task `subsystems:` field rewritten. |
| Plan / mission / identity | link-only | n/a | Source-anchored; controller never absorbs project mission. |
| Ideas (per row) | active-control-visible | archived-reference | Synthetic `idea-{member_id}-{seq}` ID assigned at dry-run. |
| Linking / PCAC | link-only | n/a | Source's controller status (if any) → conflict-deferred unless `--accept-source-controller-as-data-only`. |
| Reports | link-only | link-only | Opt-in `--copy-reports {pattern}` upgrades to archived-reference. |
| Logs | link-only (always) | link-only | Cannot be promoted; bytes never copied. |
| Experiments | merge-candidate | archived-reference | Chain parents rewritten when both accepted. |
| Source archive sub-trees | n/a | archived-reference (preserved sub-tree) | NOT re-bucketed into controller ordinals; lives at `.gald3r/archive/adopted/{member_id}/`. |
| Specifications collection | link-only | n/a | Reviewer may PROMOTE individuals at dry-run. |
| Learned facts | link-only | n/a | Source's continual-learning belongs to source. |
| Unknown / custom folders | conflict-deferred | conflict-deferred | Apply REFUSES until `--accept-unknown {pattern} as {class}` or `--reject-unknown {pattern}`. |

**Active index rendering** (controller `TASKS.md` / `BUGS.md` / `FEATURES.md` / `RELEASES.md` / `PRDS.md` / `CONSTRAINTS.md` / `IDEA_BOARD.md`):

1. Rows carry an `[adopted:{member_id}]` prefix appended to existing emoji block; regenerated from frontmatter `adoption.member_id`, never hand-edited.
2. PCAC + adoption stack: `[PCAC] [adopted:{member_id}] {title}` when source task carries `pcac_source` block.
3. Subsystems lists are rewritten through the per-adoption subsystem ID map (link-only = `{name}-{member_id}`; keep-controller resolved = unprefixed).
4. Every adopted active file gets a markdown-comment provenance footer (`<!-- ADOPTION PROVENANCE ... -->`) so plain markdown viewers can trace lineage without parsing frontmatter.

**Dependency remapping** (T216 §3) introduces two new frontmatter fields on adopted active tasks/features/PRDs:

| Field | Meaning |
|-------|---------|
| `source_dependencies: [N, M, ...]` | Original source IDs preserved verbatim; full source dependency list always recoverable. |
| `unresolved_source_dependencies: [K, ...]` | Source dependencies with no controller mapping (target was link-only / conflict-deferred-skip / unknown-rejected). Surfaced in dry-run as advisory. |

Three-way mapping: active-active deps render as standard controller IDs; active-archived deps satisfy `requires_verified_dependencies: true` (T212 — archived = passed verification); missing deps drop from `dependencies:` and surface in `unresolved_source_dependencies`.

**Terminal routing through T204 archives** (T216 §4):
- Adopted terminal artifacts use **controller's** ordinal bucket sequence (T204 rule unchanged); source numeric ID preserved in `archive.original_task_id` / `archive.original_bug_id`.
- Source's *own* archive sub-tree preserved verbatim under `.gald3r/archive/adopted/{member_id}/{tasks|bugs}/{source_range}/`. Two parallel ordinal sequences; never re-bucketed.
- Archive pointer rows in `archive_{tasks|bugs}_{range}.md` gain an `Adopted From` column (`{member_id}:source-task-NNN`); empty (`—`) for non-adoption archives.

**Conflict resolution vocabulary** (T216 §5) — every `conflict-deferred` item requires an explicit decision; no silent defaults:

| Decision | Effect |
|----------|--------|
| `keep-source` | Replace controller artifact with source; existing controller version moved to `.gald3r/{kind}/{name}.controller-orig.md`. |
| `keep-controller` | Skip source artifact; record `link-only` reference. |
| `merge` | Held for human merge editor at `.gald3r/{kind}/{name}.merged.md`; apply REFUSES until merge file lands. |
| `skip` | Record skip in adoption ledger; no source content lands. |
| `mirror` (PRD released only) | Copy as `archived-reference`; frozen status preserved verbatim. |
| `link` (PRD released/superseded only) | Link-only stub; no body copy. |

Apply CLI extends `@g-wrkspc-adopt --apply --plan {report-path}` with: `--resolve-conflict {kind}-{id}={decision}`, `--accept-unknown {pattern} as {class}`, `--reject-unknown {pattern}`, `--accept-merge {kind}={id} as {class}`, `--skip-merge {kind}={id}`, `--copy-reports {pattern}`, `--shipped-features-as-link-only`, `--accept-source-controller-as-data-only`.

The full 39-row import policy matrix (artifact-type × source-status × default class × required provenance × apply gate) and 7 worked examples are in `docs/20260428_165201_Claude_GALD3R_ADOPTION_IMPORT_POLICY.md` §6 and §8.

### Active Index Visibility

Active imported tasks and bugs MUST appear in `.gald3r/TASKS.md` and `.gald3r/BUGS.md` so agents see open imported work without leaving the control project. Three rules prevent index bloat:

1. Each adopted active row uses an `[adopted:{member_id}]` prefix appended to the existing emoji block.
2. Only `active-control-visible` items appear in the active indexes. Terminal items go straight to Task 204 archive buckets and never cross the active index.
3. Adopted rows are regenerated from per-record frontmatter, never hand-edited.

### Archive Routing for Terminal Imports

Terminal items are written directly to the Task 204 archive structure:

- Bucket allocation by archive entry ordinal (T204 rule), not by original task/bug ID.
- A dedicated section heading per adoption operation:

```markdown
## Adopted from {member_id} ({adoption_operation_id})

| Archive Slot | Task | Title | Final Status | Completed/Closed | Source Project | Workspace Repos | Archived File |
|--------------|------|-------|--------------|------------------|----------------|-----------------|---------------|
```

- Archived task/bug files live at `.gald3r/archive/tasks/tasks_{range}/task{adopted_id}_{slug}_adopted.md` (and the bug equivalent), with BOTH the standard `archive:` block AND the `adoption:` block in frontmatter.

### Manifest Member Status Update

After successful apply, the manifest member entry for `{member_id}` is updated atomically with the apply transaction. New fields:

```yaml
- id: {member_id}
  lifecycle_status: adopted
  canonical_source_status: external_gald3r_project_managed_independently
  adoption:
    adopted_at: "YYYY-MM-DDTHH:MM:SSZ"
    adoption_operation_id: adopt-YYYYMMDD-HHMMSS-{project_slug}
    adoption_plan_path: ".gald3r/reports/adoption_{adopt-id}.md"
    adoption_apply_ledger: ".gald3r/reports/adoption_{adopt-id}_apply.md"
    artifacts_imported:
      tasks_active: N
      tasks_archived: N
      bugs_active: N
      bugs_archived: N
      features_referenced: N
      prds_referenced: N
      subsystems_linked: N
      constraints_referenced: N
    artifacts_deferred:
      merge_candidates: N
      conflicts: N
  allowed_write_policy:
    default_policy: no_direct_writes_during_adoption
    inspect_allowed: true
    write_allowed: false
```

`adopted` is a new value in the validated `lifecycle_status` vocabulary. `external_gald3r_project` is recognized for `repo_role`. `no_direct_writes_during_adoption` is recognized for `allowed_write_policy.default_policy`. These are additive, backward compatible.

The manifest update is registry-only; no member repository file is touched.

### Phase 1 — Preflight (ADOPT_DISCOVER prerequisite)

All must pass before discovery:

1. Control project's `.gald3r/linking/workspace_manifest.yaml` exists and parses cleanly via PARSE_MANIFEST.
2. Source `{path}` exists and is reachable.
3. Source `{path}` is an independent git root distinct from the control project root.
4. Source `{path}` is not a symlink or junction.
5. Source `{path}/.gald3r/` exists and contains at minimum `.identity` (or `.project_id`) AND `TASKS.md`.
6. Source path is not nested inside the control project working tree.
7. If `{path}` is already a manifest member with `lifecycle_status: active`, refuse without `--allow-readopt`.

### Phase 2 — ADOPT_DISCOVER

Reads source `.gald3r/` read-only. Builds inventory: source identity, per-type counts and ID ranges, first-pass per-artifact class assignment, draft ID mapping, draft conflict list. Writes nothing. Returns inventory and prints a compact summary.

### Phase 3 — ADOPT_DRY_RUN

Re-runs discovery and writes a single Markdown report at `.gald3r/reports/adoption_{adopt-id}.md`. The report sections (fixed headings, parseable):

1. Source Identity
2. Artifact Counts by Type
3. ID Collision Plan
4. Active/Open Imports (active-control-visible)
5. Completed/Closed Archive Imports (archived-reference)
6. Merge Candidates
7. Conflicts (`_No conflicts detected._` when empty)
8. Reference Stubs (link-only)
9. Manifest Member Status Delta
10. Apply Decision Summary
11. Provenance

The report is the single artifact a future apply consumes.

### Phase 4 — ADOPT_APPLY (Gated)

Apply runs only when all gates pass; any failure aborts with no partial writes:

1. Active task explicitly authorizes adoption work for `{member_id}`.
2. `--plan` path exists, parses, and is fresh (mtime within `--plan-max-age-hours`, default 24h).
3. Plan's `adoption_operation_id` matches the recomputed ID for `(source path, member_id)` or the user supplied `--reuse-id`.
4. Preflight (Phase 1) passes again at apply time.
5. Discovery re-runs and matches the plan's artifact count and ID-mapping signature; any drift refuses with `BLOCK adoption_plan_signature_mismatch`.
6. The user supplied explicit `--apply` (no implicit apply).
7. Manifest `allowed_write_policy` permits the manifest update for the active task (re-checked via ENFORCE_SCOPE).
8. **Member `.gald3r/` marker-only guard (BUG-021 / Task 213 v1.1 / g-rl-36)**: ADOPT writes go to the control project, never to the member's live control plane. Apply must:

   a. Run the validate helper against the source/member path: `scripts/validate_workspace_members_gald3r.ps1`. If the member entry shows `has_violations`, refuse with `BLOCK adoption_member_repo_live_control_plane` and direct the user to `scripts/remediate_member_gald3r_marker.ps1` followed by re-adoption.

   b. After the controller's `.gald3r/` is updated and the member's history has been imported into the controller (per the populated-gald3r adoption flow), call `scripts/bootstrap_member_gald3r_marker.ps1 -MemberPath {source_path} -MemberId {member_id} -Apply` to ensure the member ends in the marker-only shape (`.identity` + `PROJECT.md` present, control plane absent).

   c. Refuse with `BLOCK adoption_member_repo_gald3r_guard_error` if either helper returns exit `2`.

Apply writes (in order, transactional):

- Provenance-tagged active task records under `.gald3r/tasks/`.
- Provenance-tagged active bug records under `.gald3r/bugs/`.
- One `[adopted:{member_id}]` row per active import in `.gald3r/TASKS.md` and `.gald3r/BUGS.md`.
- Archive entries for terminal items routed through Task 204 buckets (Section 7 of the design doc).
- Reference stubs for `link-only`/`archived-reference` items at `.gald3r/adopted/{member_id}/{type}/{source_id}.md`.
- Manifest member entry update for `{member_id}` (Section 8 of the design doc).
- Apply ledger at `.gald3r/reports/adoption_{adopt-id}_apply.md`.

Apply never:

- Writes to the source `.gald3r/`.
- Deletes any existing control-project artifact (silent overwrite is forbidden; conflicts must be resolved by an explicit `--plan` decision).
- Modifies any member repository file.
- Pushes git commits.

### Refusals (BLOCK Findings)

ADOPT raises any of the following BLOCK findings with an actionable single-line remediation:

**Preflight / source shape**

- `BLOCK adoption_preflight_failed`
- `BLOCK source_not_independent_git_root`
- `BLOCK source_gald3r_minimum_missing` — `.gald3r/.identity` (or legacy `.project_id`) AND `TASKS.md` are required
- `BLOCK source_gald3r_unreadable` — source `.gald3r/` exists but cannot be read (permissions, locked, antivirus quarantine); discovery cannot inventory
- `BLOCK source_identity_ambiguous` — `.gald3r/.identity` is missing required `project_id`/`project_name`, or two identity files disagree, or the source's project_id collides with an existing controller project_id without `--allow-id-collision`
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

- `BLOCK source_repo_dirty_apply_mode` — source has uncommitted changes, in-progress merge/rebase, or pending worktrees, and `--allow-source-dirty` was not supplied; resolve or commit source state first
- `BLOCK control_repo_dirty_apply_mode` — controller has uncommitted changes outside the writes ADOPT itself plans, and `--require-clean-controller` was supplied; commit or stash unrelated controller changes first
- `BLOCK pcac_conflict_gate_unresolved` — `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` reports an open `[CONFLICT]`; resolve via `@g-pcac-read` before re-running apply

**Boundary preservation**

- `BLOCK adoption_member_repo_write_attempted` — apply attempted to write inside the source `.gald3r/` outside the sanctioned bootstrap/remediate helpers
- `BLOCK adoption_manifest_write_policy_refused`
- `BLOCK adoption_controller_manifest_unparseable` — `PARSE_MANIFEST` fails on the controller's own manifest; fix the manifest before adopting another project

### VALIDATE Vocabulary Additions

ADOPT adds the following allowed values to existing VALIDATE vocabularies. They are additive and backward compatible:

- `lifecycle_status`: `adopted`
- `lifecycle_status`: `planned_adopting_member` — in-flight state between manifest registration and successful apply for `populated_gald3r_adoption`; while in this state `allowed_write_policy.write_allowed` MUST remain `false`
- `repo_role`: `external_gald3r_project`
- `allowed_write_policy.default_policy`: `no_direct_writes_during_adoption`
- `adoption.adoption_mode`: `populated_gald3r_adoption` — recognized by `VALIDATE` as the only currently-supported ADOPT mode; future modes (clean import, partial import, etc.) MUST be added here before introducing new submodes

### Verification Fixture

A synthetic offline sample dry-run report at `.gald3r/reports/adoption_dryrun_sample.md` demonstrates the format defined in Section 9 of the design doc. The verifier compares the sample against the format spec; no real project is scanned.

### Coexistence with Other Operations

- **vs. PARSE_MANIFEST / VALIDATE**: ADOPT calls PARSE_MANIFEST in preflight and re-runs VALIDATE additions before any manifest update.
- **vs. SPAWN**: SPAWN creates a brand-new minimal independent git root and registers it in the manifest; ADOPT consumes an existing gald3r project with history; MEMBER_ADD only registers an existing or planned path.
- **vs. MEMBER_ADD**: MEMBER_ADD plans/applies a registry-only entry for a new member without creating the directory or git root; ADOPT plans/applies a full adoption that also touches control-project task/bug/feature/PRD/subsystem state.
- **vs. EXPORT_PLAN / SYNC_PLAN**: those are template-export/sync planning surfaces; ADOPT is a project-adoption surface. They do not overlap.
- **vs. PCAC**: PCAC `@g-pcac-adopt` registers a parent/child topology relationship for cross-project messaging; Workspace-Control ADOPT updates manifest membership and imports artifact state for routing/visibility. Both can be run for the same external project independently.

---

## Operations: MEMBER_MARKER_BOOTSTRAP / MEMBER_MARKER_REMEDIATE / MEMBER_MARKER_VALIDATE (BUG-021 / Task 213 v1.1 / g-rl-36)

Workspace-Control member repositories may keep ONLY a slim `.gald3r/` marker — `.identity` plus a parity-maintained `PROJECT.md`. Live gald3r control-plane content (TASKS.md, BUGS.md, PLAN.md, FEATURES.md, SUBSYSTEMS.md, RELEASES.md, CONSTRAINTS.md, IDEA_BOARD.md, PRDS.md, prds/, features/, releases/, subsystems/, config/, linking/, experiments/, logs/, reports/, archive/, specifications_collection/, learned-facts.md, etc.) is forbidden inside member `.gald3r/`. The workspace controller (e.g. `gald3r_dev`) is the source of truth for live state.

Three companion helpers ship in `scripts/` (and `gald3r_template_full/scripts/` for installed projects):

### MEMBER_MARKER_BOOTSTRAP — only sanctioned writer of member `.gald3r/`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_path>" `
    -MemberId "<manifest_repo_id>" `
    [-ControllerPath "<absolute_controller_path>"] `   # optional; defaults to upward manifest discovery
    [-Apply]                                            # omit for dry-run
```

Behavior:

1. Confirms membership via `check_member_repo_gald3r_guard.ps1 -AllowMarkerInit`.
2. Refuses with `BLOCK member_gald3r_has_control_plane` if existing `.gald3r/` already contains forbidden content — directs the user to MEMBER_MARKER_REMEDIATE first.
3. Creates `.gald3r/.identity` (if absent) tying the member back to the controller (`workspace_role=controlled_member`, `workspace_controller_id`, `workspace_controller_project_id`, `workspace_controller_path`, `member_gald3r_marker_only=true`).
4. Creates `.gald3r/PROJECT.md` (if absent) as a member-stub naming the member, role, controller, and crosslink.
5. Preserves any pre-existing `.identity` or `PROJECT.md` (idempotent).

Called by: SPAWN_APPLY (after git init + minimal `.gitignore`/`README.md`), MEMBER_ADD_APPLY (when path exists), and ADOPT_APPLY (after history import + remediation).

### MEMBER_MARKER_REMEDIATE — non-destructive cleanup

```powershell
# Dry-run
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_path>"

# Apply (quarantines forbidden entries; never deletes)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_path>" `
    -Apply
```

Behavior: scans the member's `.gald3r/`, categorises each entry as marker-safe (`.identity`, `PROJECT.md`) or forbidden control plane, and on `-Apply` moves forbidden entries to `<member>/.gald3r-quarantine/<timestamp>/` (or `-BackupTo <path>`). Marker entries are preserved in place. Nothing is permanently deleted; the user controls final disposition of the quarantine folder.

Used for: cleaning up historical violations (e.g. `gald3r_throne` / Task 197), pre-adoption preflight before adopting populated gald3r projects (e.g. `gald3r_valhalla`).

### MEMBER_MARKER_VALIDATE — workspace-wide audit

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_workspace_members_gald3r.ps1
```

Scans every controlled_member and migration_source from the manifest and reports per-member compliance: `clean` / `marker_missing` / `marker_incomplete` / `has_violations` / `not_yet_created`. Exit `0` if all clean, `1` if any has_violations (use `-WarnOnly` for advisory mode, `-Json` for machine-readable output). Required as part of pre-adoption preflight before any new member is added.

### Pre-adoption preflight gate

Before adopting an existing populated gald3r project as a Workspace-Control member, the operator MUST:

1. Run MEMBER_MARKER_VALIDATE to baseline current marker compliance.
2. Run guard against the candidate path to confirm membership classification post-adoption.
3. If candidate's existing `.gald3r/` contains live control plane, refuse silent overwrite — either route through the Workspace-Control populated-gald3r adoption flow (Tasks 214-217: history import + provenance + active/terminal classification + remediation), or defer adoption until cleanup is complete.

---

## Operation: SYNC PLAN

**Usage**: `@g-wrkspc-sync --dry-run` or `@g-workspace-sync --dry-run`

SYNC PLAN explains intended alignment between the control project and member repositories without changing files.

### Steps

1. Run VALIDATE.
2. Read `routing_policy.clean_repo_gate.before_member_write`.
3. Read each member's `source_template_relationship`.
4. Identify whether the sync would be:
   - control project to generated member output
   - member handoff readiness inspection
   - docs-only metadata alignment
   - no action, because member repositories are still planned
5. Report per-member planned comparisons:
   - source path
   - destination path
   - write policy
   - clean-repo expectations
   - parity/tier preflight commands to run manually
   - independent git root, branch, dirty status, remotes, and worktree context
6. End with the required dry-run language from EXPORT PLAN.

Do not call copy, move, delete, git add, git commit --trailer "Made-with: Cursor", parity sync, tier sync, or export scripts from this operation. It is a plan/report only.

---

## Routing Examples

### Current Repository Only

Omitted metadata means current repo only:

```yaml
subsystems: [ai-skills-library]
```

Agent behavior:

```text
Scope: current repository only. Do not inspect or write sibling workspace members.
```

### Docs Only

```yaml
workspace_repos:
  - gald3r_dev
workspace_touch_policy: docs_only
```

Agent behavior:

```text
Allowed: docs, .gald3r planning metadata, changelog, task notes.
Blocked: source changes, member repo writes, generated output.
```

### Generated Output

```yaml
workspace_repos:
  - gald3r_template_slim
workspace_touch_policy: generated_output
canonical_source: gald3r_dev/gald3r_template_slim
```

Agent behavior:

```text
Allowed only in future apply mode with explicit task authorization, clean member preflight, provenance label, and reviewed member git status.
```

### Multi-Repo

```yaml
workspace_repos:
  - gald3r_dev
  - gald3r_template_full
workspace_touch_policy: multi_repo
```

Agent behavior:

```text
Each repo is a separate git boundary. Report status, branch, remotes, rollback, and worktree context per repo. Do not make one commit that assumes shared history; worktree and branch names must include the member repo ID when isolation mode is used.
```

---

## Coexistence With Other gald3r Skills

### `g-skl-pcac-*`

PCAC owns topology, INBOX, orders, requests, peer snapshots, and cross-project dependency messages. `g-skl-workspace` owns manifest-backed local workspace scope reporting. Do not replace PCAC order/request flows with workspace manifest entries.

### `g-skl-tasks`

`g-skl-tasks` owns task creation, status transitions, and task sync. `g-skl-workspace` may validate `workspace_repos` and `workspace_touch_policy`, but it does not create tasks or widen task scope by itself.

### `g-skl-bugs`

`g-skl-bugs` owns bug records and bug fix workflows. `g-skl-workspace` may validate bug frontmatter routing when asked, but it does not report or fix bugs.

### `g-skl-git-commit`

`g-skl-git-commit` owns commits. Workspace-Control requires per-repository git boundaries; a future workspace-aware commit flow must commit separately inside each repo and must not stage a single cross-repo commit from the control project. This skill does not commit.

### `g-skl-status` / `g-status` / `g-report`

Status and report surfaces may embed a compact Workspace-Control snapshot by reusing this skill's STATUS and VALIDATE semantics. They should:

- Stay quiet when `.gald3r/linking/workspace_manifest.yaml` is absent, unless the user explicitly asks for workspace detail.
- Show manifest path, workspace identity, owner ID, controlled member count/IDs, member lifecycle status, path reachability, write policy summary, and per-member git root/branch/dirty/remotes/worktree context when paths are reachable.
- Show active task/bug `workspace_repos` and `workspace_touch_policy` metadata when present; omitted metadata means current repository only.
- Distinguish PCAC topology/INBOX/order/request state from Workspace-Control member registry state.
- Cite Task 177 boundaries when users might expect backend, UI, Docker/Kubernetes/MCP, `gald3r_valhalla`, `yggdrasil`, dashboards, or control-plane status. Those systems are deferred and should not be treated as missing bootstrap components.

### Template Parity Tooling

`platform_parity_sync.ps1`, `platform_parity_check.ps1`, `tier_sync.ps1`, `g-skl-tier-setup`, and `g-skl-template-export` remain the existing parity/export surfaces. `g-skl-workspace` reports how those tools would interact with member repos; it does not change propagation semantics or run scripts.

For the `gald3r_dev` source repository only, edits to core gald3r framework/platform surfaces are self-hosting changes. If a task changes reusable files under `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `.copilot/`, `.github/prompts/`, shared rules, skills, commands, agents, hooks, or generated Copilot instructions, completion requires one of:

- Run `scripts/platform_parity_sync.ps1 -SelfHostingRootSource` and, when approved, `scripts/platform_parity_sync.ps1 -SelfHostingRootSource -Sync`. This uses the root `.cursor/` tree as the maintainer source, syncs root platform folders and `gald3r_template_adv/`, then runs `tier_sync.ps1` so `gald3r_template_full/` and `gald3r_template_slim/` receive tier-filtered content.
- Record an explicit root-only exception, e.g. `g-gald3r-export` maintainer tooling, proprietary local skills, or personality content intentionally shipped through `personality_packs/` instead of templates.

`gald3r_dev-only` command wording means the command is executed only from the source/control repository; it does not by itself exempt reusable framework edits from template parity.

### Scoped Dirty-State Handling

Workspace-Control dirty checks are path-scoped. A dirty repository is a hard blocker only when dirty paths overlap planned writes, protected control files, or a requested member write. Unrelated dirty or untracked paths are advisory and must be reported, not used as a blanket stop sign. Examples:

- `gald3r_template_full/temp_docs/` is unrelated to a planned command/skill parity write: warn, do not block.
- A dirty `.cursor/skills/g-skl-workspace/SKILL.md` in a target template overlaps a planned parity write: block unless the active task explicitly authorizes merging that path.
- A dirty `.gald3r/linking/workspace_manifest.yaml` overlaps control-plane writes: block or require an explicit controller-write decision.

#### T225 Dirty-State Taxonomy (5-class)

`scripts/workspace_template_export.py` and any future Workspace-Control dirty-state surface classify every dirty entry into one of five canonical classes. The literal strings are stable so tasks/bugs that depend on this surface can `grep` and reference them directly:

| Class | Definition | Disposition |
|-------|------------|-------------|
| `overlapping-target` | Modified or staged path that overlaps a planned write. | **Block** apply. |
| `unrelated-dirty` | Modified or staged path that does NOT overlap planned writes. | Advisory warning; apply may proceed. |
| `untracked-target` | Untracked file (`?? path` in `git status --short`) inside a planned-write path. | **Block** apply (treated identically to `overlapping-target`). |
| `untracked-unrelated` | Untracked file outside any planned-write path. | Advisory warning. |
| `protected-path` | Path matching `DEFAULT_EXCLUDES`, `SUSPICIOUS_PATH_PARTS`, the secret-shaped literal scan, or a reparse-point/symlink. | Skipped from the export plan; surfaced via `plan.skipped` / `plan.hygiene_findings`. |

`overlapping-target` and `untracked-target` share the same overlap pipeline — `parse_status_paths` deliberately includes `?? path` lines so `paths_overlap` / `overlapping_status_paths` treat untracked-on-target as a hard block. `unrelated-dirty` and `untracked-unrelated` fail the overlap test and land in the advisory warning bucket. `protected-path` is enforced earlier, at exclude/hygiene scan time, before overlap evaluation.

#### Path-overlap normalization (case + separator)

`paths_overlap` normalizes both inputs before comparing:

- Replaces `\` with `/` so backslash-emitting tooling on Windows still aligns with `git status` output.
- Strips leading and trailing `/`.
- Lower-cases on Windows only (`os.name == "nt"`), because the default Windows file system is case-insensitive and `core.ignorecase=true` is the standard git config (BUG-030). On Linux/macOS the comparison stays case-sensitive so genuinely distinct files (e.g. `Foo.py` vs `foo.py`) are treated as separate paths.

Worktrees reduce branch and checkout collisions, but they do not remove per-repository dirty state. Always evaluate dirtiness against the operation's planned path set before blocking.

---

## Safety Rules

- Use `g-wrkspc-*` as the short primary command family; keep `g-workspace-*` as compatibility aliases.
- Lifecycle apply operations update only `.gald3r/linking/workspace_manifest.yaml` by default.
- SPAWN_APPLY is the only workspace lifecycle operation allowed to create a new member repository, and it may create only the folder, git root, minimal `.gitignore`, minimal `README.md`, and control-project manifest entry.
- Member removal is registry-only; never delete member folders, `.git/`, branches, remotes, commits, or worktrees.
- Treat manifest repository IDs as the only stable routing keys.
- Treat `repository.local_path` as inspection scope, not write permission.
- Treat `workspace_repos` as an allow-list, not proof of permission.
- Treat `workspace_touch_policy` as maximum allowed touch type, not proof that every change is safe.
- Refuse ad hoc workspace member inference from folder names alone.
- Refuse nested member-repo assumptions: inferred `gald3r_template_*` sibling folders are not manifest members unless declared in `repositories[]`.
- Never write existing, adopted, planned, or registered member repos from this skill. The only exception is SPAWN_APPLY creating the new empty repo described above.
- Never write the source project's `.gald3r/` from ADOPT; adoption is non-destructive on the source side by default.
- Never silently overwrite a control-project artifact during ADOPT apply; collisions must be resolved by an explicit plan decision.
- Never apply ADOPT without a fresh `--plan` whose `adoption_operation_id` and artifact-count signature match the re-run discovery.
- Never use SPAWN for an existing gald3r project; use ADOPT so task/bug/history provenance is preserved.
- Never strip `adoption:` provenance fields from a record once present.
- Never build desktop UI, Valhalla/Yggdrasil backend behavior, Docker/Kubernetes/MCP services, queues, sockets, database tables, or dashboards from this skill.
- Keep non-workspace projects quiet and current-repo-only by default.

---

## Completion Checklist For Agents

Before claiming Workspace-Control work is ready for review:

- STATUS can read the canonical manifest and summarize owner plus members, including per-repo git root/branch/dirty/remotes/worktree context when reachable.
- VALIDATE checks shape, duplicate IDs, local paths, lifecycle values, touch policies, independent git roots, nested member assumptions, reparse paths, and stale routing references.
- MEMBER LIST shows only manifest-declared repositories.
- SPAWN PLAN reports the exact path, manifest entry, and no-scaffold/no-PCAC boundaries; SPAWN APPLY creates only a minimal independent git root and the control-project manifest update.
- EXPORT PLAN and SYNC PLAN state source/destination intent and no-write dry-run behavior.
- The response names `.gald3r/linking/workspace_manifest.yaml` as canonical and does not rely on the docs seed manifest.
- INIT/MEMBER ADD/MEMBER REMOVE dry-runs produce explicit no-write plans and apply modes write only the manifest registry.
- Any user-facing docs/changelog updates required by the active task are complete.

---

## License posture awareness (C-020)

`workspace_manifest.yaml` repository entries carry a `license:` field whose allowed values are:

| Value | Use |
|-------|-----|
| `FSL-1.1-Apache` | Public repos under Fair Source License 1.1 + Apache 2.0 future grant. Canonical template: `scripts/license_templates/LICENSE_FSL_TEMPLATE.txt` (controller repo). |
| `Proprietary` | Private repos under all-rights-reserved proprietary terms. Canonical template: `scripts/license_templates/LICENSE_PROPRIETARY_TEMPLATE.txt`. |

`STATUS`, `VALIDATE`, and `MEMBER LIST` operations surface each member's posture and any drift (LICENSE missing, content does not match canonical template, manifest entry missing the `license:` key). License drift is a hard `g-wrkspc-validate` failure unless `-WarnOnly` is passed.

The authoritative posture map is `g:\gald3r_ecosystem\LICENSING_STRATEGY.md` and `.gald3r/CONSTRAINTS.md` C-020. License posture changes require updating all three: strategy doc, manifest entries, and per-repo `LICENSE`/`NOTICE` files in a single coordinated task. Bare LICENSE edits without a manifest update violate C-020.

The license check is implemented inside `scripts/validate_workspace_members_gald3r.ps1` (alongside the existing T213 marker check). Pass `-SkipLicenseCheck` to suppress the license sweep when only marker diagnostics are wanted.

