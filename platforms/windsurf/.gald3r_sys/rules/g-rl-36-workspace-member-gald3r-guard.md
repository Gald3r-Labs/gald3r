---
description: "Workspace member .gald3r/ policy — autonomous_child repos own full .gald3r/; controlled_member repos keep marker-only (.identity + PROJECT.md); controller direct-write is the WPAC coordination path"
globs:
alwaysApply: true
subsystem_memberships: [WORKSPACE_COORDINATION]
---

# Workspace Member `.gald3r/` Policy (WPAC v1.6)

## Repository Role Taxonomy

| workspace_role | What it means | .gald3r/ policy |
|---|---|---|
| `controller` | Owns the ecosystem control plane (e.g. `gald3r_dev`) | Full `.gald3r/` — tasks, bugs, plans, everything |
| `autonomous_child` | Independent gald3r project, WPAC-linked to the controller | Full `.gald3r/` — self-managed; controller may also direct-write |
| `controlled_member` | Source-only repo, no independent task tracking | **Marker-only** — `.identity` + `PROJECT.md` only |
| `migration_source` | Being adopted; pre-migration state | Marker-only until migration completes |

Read `workspace_role` from `.gald3r/workspace/workspace_manifest.yaml` for each repo.

---

## autonomous_child repos — full `.gald3r/` is EXPECTED

Repos with `workspace_role: autonomous_child` (e.g. `gald3r_valhalla`, `gald3r_throne`,
`gald3r_world_tree`, `gald3r_templates`) **own and manage their own `.gald3r/`**. This is
intentional WPAC v1.6 behavior (ADR-003, ADR-013, ADR-014). Seeing full `.gald3r/` in an
`autonomous_child` repo is **correct** — do not flag it as a violation.

Autonomous children have:
- `workspace/topology.md` — parent/child wiring
- `workspace/inbox.md` — WPAC directive inbox
- `TASKS.md`, `tasks/`, `BUGS.md`, `PLAN.md`, etc. — self-managed coordination

**WPAC Controller Direct-Write Exemption (ADR-003, ADR-013)**: A controller agent (confirmed
`project_type: controller` in manifest) MAY write task files, bug files, INBOX directives, and
other WPAC-dispatched content directly into any registered member's `.gald3r/`. This is the
primary controller→child coordination mechanism. Applies to all `autonomous_child` and
`controlled_member` targets, via `@g-wpac-order`, `@g-wpac-spawn`, or controller task push.

---

## controlled_member repos — MARKER-ONLY (HARD RULE)

**`controlled_member` and `migration_source` repositories may keep ONLY a slim `.gald3r/` marker:**

- `.gald3r/.identity` — identifies the member and ties it back to the workspace controller
- `.gald3r/PROJECT.md` — describes the member's mission; cross-links to controller

**Live gald3r control-plane state is forbidden in `controlled_member` repos** unless written
by the controller via WPAC direct-write. Any of the following spontaneously appearing in a
`controlled_member`'s `.gald3r/` (without controller authority) is a hard violation:
`TASKS.md`, `tasks/`, `BUGS.md`, `bugs/`, `PLAN.md`, `FEATURES.md`, `SUBSYSTEMS.md`,
`RELEASES.md`, `CONSTRAINTS.md`, `IDEA_BOARD.md`, `PRDS.md`, `prds/`, `features/`,
`releases/`, `subsystems/`, `config/`, `workspace/`, `experiments/`, `logs/`, `reports/`,
`archive/`, `specifications_collection/`, `learned-facts.md`, or any equivalent orchestration state.

External workspace member template repos (`G:/gald3r_ecosystem/gald3r_template_slim`,
`G:/gald3r_ecosystem/gald3r_template_full`, `G:/gald3r_ecosystem/gald3r_template_adv`) are the
**only** legitimate exception: their `.gald3r/` content is intentional install template content.

This invariant fires for every workflow that may write `.gald3r/` to an arbitrary destination:
`g-skl-setup`, `g-skl-wpac-spawn`, `g-skl-wpac-adopt`, `g-skl-workspace` SPAWN_APPLY /
ADOPT_APPLY, `gald3r_install`, and any future scaffold/repair flow.

---

## Source of truth

- **Canonical rule file (edit here)**: `G:/gald3r_ecosystem/gald3r_templates/gald3r_template/.gald3r_sys/rules/g-rl-36-workspace-member-gald3r-guard.md`
- **Propagate**: `G:/gald3r_ecosystem/gald3r_templates/custom_scripts/platform_parity_sync.ps1 -SyncGaldSys -Sync` → `gald3r_dev/.gald3r_sys/`, `gald3r_template_{slim,full,adv}/gald3r_template/.gald3r_sys/`, `gald3r/gald3r_template/.gald3r_sys/`
- **Do NOT edit for framework changes**: `gald3r_dev/.gald3r_sys/` (sync target only; preserves `.understand-anything/` on controller)
- **ADR-003**: WPAC Controller Direct-Write Authority (supersedes BUG-021 marker-only-only stance)
- **ADR-013**: autonomous_child workspace_role definition
- **ADR-014**: Ecosystem v1.6 redesign
- **Bug**: `BUG-021` — original marker-only violation; now scoped to `controlled_member` only
- **Task**: `T1395` — WPAC v1.6 epic; `T1413` — this rule update (task tracked in `gald3r_dev/.gald3r/`)
- **Manifest**: `.gald3r/workspace/workspace_manifest.yaml` → each repo's `workspace_role`
- **Helper scripts** (under canonical `.gald3r_sys/`, synced to consumers):
  - `skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1` — marker-aware preflight (autonomous_child aware)
  - `skills/g-skl-workspace/scripts/bootstrap_member_gald3r_marker.ps1` — sanctioned writer of `controlled_member` markers
  - `skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.ps1` — cleanup of `controlled_member` violations
  - `skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1` — workspace-wide compliance audit

---

## Guard call contract

Before any code path writes a `.gald3r/` file inside a **`controlled_member`** repository,
call the guard:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1 `
    -TargetPath "<absolute_member_repo_path>" `
    -DotGald3rPath "<relative_path_inside_dot_gald3r>"
$exit = $LASTEXITCODE
```

| Mode | What it answers |
|---|---|
| `-DotGald3rPath ".identity"` or `-DotGald3rPath "PROJECT.md"` | ALLOW (marker-safe) |
| `-DotGald3rPath "TASKS.md"` (or any control-plane path) | BLOCK for `controlled_member`; ALLOW for `autonomous_child` |
| `-AllowMarkerInit` (no path) | ALLOW (caller asserts marker bootstrap intent) |
| Default (no path, no flags) | BLOCK on `controlled_member` targets; ALLOW on `autonomous_child` |

Exit codes: `0` ALLOW, `1` BLOCK, `2` ERROR. Optional flags: `-WarnOnly`, `-Json`, `-ManifestPath`.

> **autonomous_child repos do not need guard calls** — they self-manage `.gald3r/`. The guard
> is only meaningful for `controlled_member` targets.

---

## Bootstrap call contract (`controlled_member` only)

When a `controlled_member` is added, adopted, or spawned:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/bootstrap_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -MemberId "<manifest_repo_id>" `
    -ControllerPath "<absolute_controller_path>" `
    -Apply
```

The bootstrap helper:

1. Confirms `workspace_role: controlled_member` in the manifest (skips `autonomous_child`).
2. Refuses if existing `.gald3r/` contains forbidden content — directs to remediate first.
3. Creates `.gald3r/.identity` and `.gald3r/PROJECT.md` if absent.
4. Refuses to write any other path.

For `autonomous_child` repos, use `g-skl-wpac-spawn` or the full gald3r setup flow instead.

---

## Remediation call contract (`controlled_member` violations only)

```powershell
# Dry-run first
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>"

# Apply (quarantines forbidden entries to `.gald3r-quarantine/<timestamp>/`)
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -Apply
```

Remediation **never deletes**. Do NOT run remediation against `autonomous_child` repos — their
full `.gald3r/` is intentional.

---

## Promotion off-ramp (`controlled_member` -> `autonomous_child`) (BUG-097 / T1435)

The marker-only guard is intentional, but it is **not** a permanent freeze. When a
`controlled_member` needs to become independent, use the formal promotion path instead of
hand-editing `.gald3r/` or `.gitignore`:

```powershell
# Dry-run (default)
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/gald3r_promote_member.ps1 `
    -MemberPath "<absolute_member_repo_path>"

# Apply
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/gald3r_promote_member.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -Apply
```

Command surface: `@g-wpac-promote <member-id> --dry-run|--apply` (delegates to `g-skl-workspace`
PROMOTE). Apply scaffolds the standard `autonomous_child` files (`RELEASES.md`, `releases/`,
`vocab.md`, `workspace/topology.md`, `workspace/inbox.md`, `FEATURES.md`, `BUGS.md`, `PLAN.md`),
rewrites `.identity` (`workspace_role=autonomous_child`, removes `member_gald3r_marker_only`, bumps
`gald3r_version`), and updates the manifest `workspace_role`. After promotion the guard ALLOWS
`@g-skl-setup` on the repo — run `@g-skl-setup --upgrade-existing` for a full top-up.

---

## Skill / command preflight requirements

- **`g-skl-setup`** — check manifest `workspace_role`. `controlled_member` → BLOCK (marker-only via bootstrap). `autonomous_child` → ALLOW full setup.
- **`g-skl-wpac-spawn`** — spawning into a `controlled_member` path is forbidden. Spawning a new `autonomous_child` is ALLOW.
- **`g-skl-wpac-adopt`** — when adopting a `controlled_member`, guard `.gald3r/workspace/` writes. `autonomous_child` adoption proceeds without the guard.
- **`gald3r_install`** — check manifest before writing `.gald3r/` files. `controlled_member` → refuse and direct to bootstrap. `autonomous_child` → allow install.

---

## Rationalization table

| Rationalization | Reality |
|---|---|
| "This autonomous_child has a full .gald3r/, that's a violation" | No. `autonomous_child` repos own their own .gald3r/. Check `workspace_role` first. |
| "I see TASKS.md in gald3r_valhalla, that must be wrong" | Correct and expected — `gald3r_valhalla` is `autonomous_child`. |
| "A controlled_member needs its own task tracker" | The controller IS the tracker for `controlled_member` repos. Use `autonomous_child` if the repo needs independence. |
| "I'll just put a small TASKS.md in this controlled_member" | Still a violation. If the repo needs tasks, promote it to `autonomous_child` via T1395 process. |
| "The manifest says write_allowed: true so it's fine" | `write_allowed` covers source code writes. The `.gald3r/` policy is set by `workspace_role`, not `write_allowed`. |
| "I'll edit gald3r_dev/.gald3r_sys/ directly" | Edit canonical under `gald3r_templates/gald3r_template/.gald3r_sys/` then run `-SyncGaldSys -Sync`. |

---

## Template directory exception (mandatory honor)

Paths matching `**/template_(slim|full|adv)/**` carry deliberate `.gald3r/` template content.
The guard helper returns ALLOW with reason `template_directory_exception`. Do **not** add
additional carve-outs.
