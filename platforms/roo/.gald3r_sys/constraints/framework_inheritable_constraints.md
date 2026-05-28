---
gald3r_rel_version: "1.6.0"
schema_version: "CONSTRAINTS-md-v1"
source: framework
---
# Framework Inheritable Constraints

This file is the **canonical, shipped source** of gald3r framework constraints whose
`**Scope**:` is `inheritable`. It is consumed by `@g-update` (Gap C, BUG-105), which merges
each constraint block below into a consumer project's `.gald3r/CONSTRAINTS.md` — skipping any
constraint ID that already exists locally so project-local customizations are never overwritten.

This is the propagation mechanism that makes the `inheritable` flag functional instead of
documentation-only. Before T1438 the flag described intent but nothing copied the constraints
into child projects.

## How `@g-update` uses this file

1. Read every `### C-{ID}: {Name}` block below.
2. For each block whose `**Scope**:` is `inheritable`, check the consumer's
   `.gald3r/CONSTRAINTS.md`:
   - **Already present** (matching `C-{ID}` heading) -> skip (never overwrite).
   - **Absent** -> append the full block to the `## Constraint Definitions` section,
     add an index row to the `## Constraint Index` table, and append an `**Inherited from**:`
     line marking it framework-sourced.
3. Inherited constraint blocks gain:
   ```markdown
   **Inherited from**: gald3r-framework (propagated YYYY-MM-DD)
   ```
   making them read-only locally (changes coordinate through the framework).

## Authoring note (maintainers)

C-013..C-017 and C-019 originated in `gald3r_master_control` (now archived). Their index-row
summaries survived in `gald3r_dev/.gald3r/CONSTRAINTS.md` but the full definition blocks were
never authored there — only one-line table entries exist. The definitions below were authored
from those index summaries + enforcement context from `g-skl-test` and `g-rl-33` (T1445).
C-020 is copied verbatim from `gald3r_dev/.gald3r/CONSTRAINTS.md`. C-023 is framework-native.

---

## Constraint Definitions

### C-013: test-plan-maintenance

**Status**: active
**Established**: 2026-04-16
**Scope**: inheritable
**Rationale**: Without a required test plan for every active subsystem, subsystems ship without
coverage and regressions accumulate silently. The L1/L2/L3 ladder ensures at minimum a fast
smoke gate (L1) and a comprehensive gate (L2) exist before any verified task can close.

**Applies to**: All active subsystems declared in `.gald3r/SUBSYSTEMS.md`; every task marked
`[🔍]` awaiting verification.

**In practice**:
- Each active subsystem has a corresponding L1, L2, and L3 test plan file in `.gald3r/` or
  the project's test directory.
- No task may reach `[🔍]` without the subsystem it touches having an L1 plan present.
- `g-skl-test` scaffolds missing plans; `@g-test` runs them.

**Violation examples**:
- A subsystem listed in SUBSYSTEMS.md with no test plan files.
- Marking a task `[🔍]` without verifying the touched subsystem has an L1 plan.

**Enforcement**: `g-go-review` checks L1 plan existence before passing verification; `g-skl-test`
flags missing plans; session start Sync Validation Step 4 checks subsystem completeness.

---

### C-014: fast-test-verification-gate

**Status**: active
**Established**: 2026-04-16
**Scope**: inheritable
**Rationale**: The L1 fast test plan is the minimum bar for declaring implementation complete.
Without it a task can reach `[🔍]` with zero verified coverage — undermining the entire
verification gate.

**Applies to**: Every task being moved to `awaiting-verification` (`[🔍]`) status.

**In practice**:
- Before marking any task `[🔍]`, the L1 (fast) test plan for each touched subsystem must pass.
- L1 plans run in under 60 seconds. Failures block the status transition.
- `@g-test L1` is the command; `g-go-review` enforces this gate.

**Violation examples**:
- Setting a task to `[🔍]` without running the L1 plan.
- L1 plan failing but marking the task complete anyway.

**Enforcement**: `g-go-review` Phase 2 runs L1 before issuing a PASS verdict; `g-rl-33`
blocks any response that marks a task `[🔍]` without noting L1 results.

---

### C-015: release-requires-full-testing

**Status**: active
**Established**: 2026-04-16
**Scope**: inheritable
**Rationale**: A release or version bump without full L2 + L3 coverage risks shipping regressions
that only appear in integration or real-world conditions. L1 alone is insufficient for release
gates.

**Applies to**: Any version bump (CHANGELOG promotion, git tag, release file creation).

**In practice**:
- L2 (comprehensive) and L3 (regression) test plans must pass before any `## [X.Y.Z]`
  CHANGELOG entry is promoted, a git tag is created, or a release file is written.
- `@g-test L2` and `@g-test L3` are the commands.
- `g-skl-ship` and `@g-release-sync` enforce this gate before writing release artifacts.

**Violation examples**:
- Tagging a release without L2/L3 results on record.
- Promoting `[Unreleased]` to a version while L2 is failing.

**Enforcement**: `g-skl-ship` pre-flight checks; `g-go-review` release-result commit gate.

---

### C-016: project-code-folder-structure

**Status**: active
**Established**: 2026-04-16
**Scope**: inheritable
**Rationale**: Keeping all coding artifacts inside `<project_name>/` prevents the repo root from
becoming a dumping ground and ensures the gald3r system files (`.gald3r/`, `.gald3r_sys/`,
`.cursor/`, `.claude/`) remain structurally separate from project deliverables.

**Applies to**: All source files, build outputs, and project-specific assets in any gald3r repo.

**In practice**:
- Application code, scripts, configs, and assets live under a named project folder
  (e.g. `src/`, `app/`, `<project_name>/`).
- The repo root is reserved for: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`,
  `LICENSE`, `ROADMAP.md`, `VERSION`, and gald3r system directories.
- No raw `.py`, `.ts`, `.js`, `.ps1`, or other code files at root unless they are
  framework tooling explicitly scoped to root.

**Violation examples**:
- Placing a `main.py` or `index.ts` directly at the repo root.
- Storing build outputs in root alongside `.gald3r/`.

**Enforcement**: `g-go-code` AC gate surfaces this; `g-medic L1` flags root-level code files.

---

### C-017: three-level-test-mandate

**Status**: active
**Established**: 2026-04-16
**Scope**: inheritable
**Rationale**: A single test tier is insufficient for production-quality gald3r projects. The
three-level model (L1 fast / L2 comprehensive / L3 regression) ensures coverage at every
stage: quick dev feedback (L1), full integration (L2), and historical non-regression (L3).

**Applies to**: All projects with active subsystems.

**In practice**:
- Every project implements or inherits L1, L2, and L3 test plans via `g-skl-test`.
- Skipping any level requires a documented justification in the subsystem spec or CONSTRAINTS.md.
- `@g-test` commands dispatch by level; `g-go-review` enforces level by task phase.

**Violation examples**:
- A project with only unit tests and no L2/L3 plans.
- Declaring a subsystem active without any test tier.

**Enforcement**: `g-skl-test` scaffolding; `g-go-review` level checks; `g-medic L2` diagnosis.

---

### C-019: prd-frozen-when-released

**Status**: active
**Established**: 2026-04-25
**Scope**: inheritable
**Rationale**: PRDs in `released` or `superseded` status are the audit-of-record for delivered
features. Any post-release edit — even a typo fix — silently corrupts the governance trail.
The revise path (`@g-prd-revise`) creates a new sequential PRD and atomically updates the
supersedes-chain, preserving full history.

**Applies to**: All `.gald3r/prds/prdNNN_*.md` files with `status: released` or
`status: superseded`.

**In practice**:
- Once a PRD reaches `released`, its body and YAML (except `superseded_by:` and the
  Change Log append during revise) are immutable.
- The only path to change a frozen PRD is `@g-prd-revise prd-NNN`, which creates a new PRD
  and updates the chain atomically.
- The `## Change Log` section is appendable exactly once: to record the supersede event.

**Violation examples**:
- Editing a typo directly in a `released` PRD body.
- Using `@g-prd-upd` on a frozen PRD instead of `@g-prd-revise`.
- Changing the YAML `status:` of a `released` PRD without the revise workflow.

**Enforcement**: `g-rl-33` PRD Freeze Gate (hard rule); `g-hk-pre-tool-call-prd-freeze.ps1`
hook blocks direct file writes to frozen PRDs; `g-skl-prds` governance lifecycle.

---

### C-020: license-posture-per-workspace-member

**Status**: active
**Established**: 2026-05-03
**Scope**: ecosystem-wide
**Enforcement**: `.gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1`, `g-skl-workspace VALIDATE`, `@g-wrkspc-validate`, agent rules

**Definition**: Every workspace member repository declared in `.gald3r/linking/workspace_manifest.yaml` MUST carry exactly one `LICENSE` file at its repository root, and that file MUST match the per-repo posture declared in the manifest under the `license:` key. The authoritative posture map is `g:\gald3r_ecosystem\LICENSING_STRATEGY.md`. Two posture values are recognized:

- `FSL-1.1-Apache` — public repos use the Fair Source License 1.1 with Apache 2.0 future grant. Canonical source: `.gald3r_sys/licenses/LICENSE_FSL_TEMPLATE.txt` (byte-identical across repos). Companion `NOTICE` from `.gald3r_sys/licenses/NOTICE_FSL_TEMPLATE.txt`.
- `Proprietary` — private repos use the strict all-rights-reserved template. Canonical source: `.gald3r_sys/licenses/LICENSE_PROPRIETARY_TEMPLATE.txt`. Companion `NOTICE` from `.gald3r_sys/licenses/NOTICE_PROPRIETARY_TEMPLATE.txt`.

**Rationale**: Without a centrally enforced license-posture invariant, any one repo can drift to MIT, Apache, or no license at all. That is exactly the trap LICENSING_STRATEGY.md was written to prevent: under MIT, any well-funded competitor can take a public gald3r repo and resell it. The proprietary template protects private repos from accidental disclosure / silent re-use if a misconfiguration ever made them public. The constraint also locks in the correct copyright holder string for future entity-formation copyright assignment.

**Posture map (current)**:
- Public + FSL-1.1-Apache: `gald3r`, `gald3r_throne`, `gald3r_template_slim`, `gald3r_template_full`, `gald3r_template_adv`
- Private + Proprietary: `gald3r_dev`, `gald3r_agent`, `gald3r_discord`, `gald3r_forge`, `gald3r_terminal`, `gald3r_valhalla`, `gald3r_vault`, `gald3r_web`, `gald3r_world_tree`

**In practice**:
- Every entry in `repositories:` in `workspace_manifest.yaml` carries a top-level `license:` field set to either `FSL-1.1-Apache` or `Proprietary`.
- `.gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1` reads each member's `LICENSE` file and asserts it matches the canonical template content for the declared posture (first 200 chars compared verbatim).
- `g-skl-workspace VALIDATE` and `@g-wrkspc-validate` surface license drift as a hard validation failure.
- License changes require updating `LICENSING_STRATEGY.md`, the manifest entry, this constraint's posture map, and all per-repo LICENSE/NOTICE files in a single coordinated task.

**Violation examples**:
- A public repo with no LICENSE file or with an MIT/Apache LICENSE
- A private repo with an FSL or open-source LICENSE
- A manifest entry missing the `license:` key
- A LICENSE file that does not match the canonical template content (silent edit drift)

---

### C-023: Release Sync Integrity

**Status**: active
**Established**: 2026-05-24
**Scope**: inheritable
**Rationale**: Every versioned `## [X.Y.Z]` entry in `CHANGELOG.md` must have a matching release
record under `.gald3r/releases/`. Without it the release history is split between two sources of
truth, and the session-start sync check (g-rl-25 Step 2b) cannot verify completeness. This
constraint was previously enforced by rule text only and appeared in no constraint index
(phantom constraint) until T1438.

**Applies to**: `CHANGELOG.md`, `.gald3r/releases/release{NNN}_*.md`, `.gald3r/RELEASES.md`

**In practice**:
- Each `## [X.Y.Z]` CHANGELOG header has a corresponding `.gald3r/releases/` file whose name
  contains the version (e.g. `release001_v1-5-0.md` for `[1.5.0]`).
- Run `@g-release-sync` (or `backfill_release_files.ps1`) to reconcile gaps; `@g-update`
  backfills automatically on upgrade.
- Do not hand-create release files that do not correspond to a real CHANGELOG version.

**Violation examples**:
- Adding a `## [1.6.0]` CHANGELOG entry but never creating `.gald3r/releases/release*_v1-6-0.md`.
- Deleting a release file while its CHANGELOG version header still exists.

**Enforcement**: Session start (g-rl-25 Step 2b) surfaces
`N CHANGELOG version(s) missing release file - run @g-release-sync`. `@g-update` runs the
release backfill on the upgrade path. `g-medic --heal-c023` (T1436) remediates structurally.

