# Release v1.6.0 — WPAC v1.6, Schema System, Ship Skill, Encoding Normalization

> **Released**: 2026-05-25
> **Previous release**: [v1.5.0](RELEASE_v1.5.0.md)

---

## Highlights

- **WPAC v1.6 Phase 4**: `controlled_member` → `autonomous_child` promotion lifecycle, version reconciliation in `.gald3r/.identity` on every sync
- **Schema Enforcement System**: 15 versioned schema definitions, session-start probe, migration engine (`migrate_schemas.ps1`)
- **g-ship Semantic Versioning**: `g-skl-ship` skill + `@g-ship` command — promotes `[Unreleased]` → versioned release, bumps `VERSION`, tags
- **Encoding Normalization**: `g-hk-encoding-normalize` hook, `.gitattributes` scaffold, content-aware binary guard
- **g-go-bugs pipeline**: Dedicated bug-fix autopilot — reproduces, fixes, regression-tests, adversarially reviews in severity order
- **Swarm file-lock manifests**: Prevents overlapping bucket file edits in parallel `g-go --swarm` runs
- **Profile-aware core skills**: `g-go`, `g-go-code`, `g-go-review` read `workflow_profile` instead of hardcoded status strings

---

## Full Changelog

### Added

- **T1444** — `g-hk-ggo-stop-detect` stop hook + `g-go-go --context-aware` flag. Re-invokes stalled autopilot loops when no authorized hard-stop row is present; `--context-aware` shrinks bucket count N under context pressure rather than stopping.
- **`@g-go-bugs` / `@g-go-bugs-swarm`** — Dedicated bug-fix pipeline: reproduce → fix → regression test → adversarial review; processes bugs in severity order (critical → high → medium → low).
- **T1437** — `platform_parity_sync.ps1 -SyncGaldSys` now reconciles `gald3r_version=` in every consumer `.gald3r/.identity` via `Update-GaldIdentityVersion` helper. Resolves BUG-102.
- **T1435** — `@g-wpac-promote` command + `g-skl-workspace` PROMOTE_PLAN/PROMOTE_APPLY — formal `controlled_member` → `autonomous_child` lifecycle with `gald3r_promote_member.ps1`. g-rl-36 gains "Promotion off-ramp".
- **T1428** — Encoding-normalization system: `g-hk-encoding-normalize` hook (stop/PreCommit/Scan modes), `.gitattributes` scaffold (`eol=lf`, `.ps1 working-tree-encoding=UTF-8`), `core.hooksPath` pre-commit shim, `install_git_hooks.ps1`. Content-aware binary guard (NUL-byte detection) prevents silent UTF-8 substitution.
- **T1438** — `@g-update` upgrade path ensures root `VERSION` file, release-file backfill via `backfill_release_files.ps1`, and inheritable-constraint propagation; `--dry-run` previews all three.
- **T1059** — `g-go --swarm` parallel file-lock manifests; `gald3r_worktree.ps1` gains `-BucketId`/`-LockFiles`/`-BucketTtlMinutes`/`LockReport` action; `LOCK_CONFLICT` raised on overlapping bucket paths.
- **T1106** — `g-hk-pre-tool-call` shell-output compression hook (PreToolUse/preToolUse, Bash|Shell matcher); configurable via `pre_tool_call_compress_lines` in AGENT_CONFIG.md.
- **T1210** — `g-skl-ship` semantic versioning skill + `@g-ship` command + `gald3r_semver.ps1` engine + `gald3r_release.ps1` maintainer tool. CHANGELOG entry hooks in `g-skl-tasks` and `g-skl-bugs`.
- **T1439** — Schema enforcement system: versioned schema definitions under `.gald3r_sys/schemas/` (`_registry.yaml`, `_version_rules.yaml`, 15 `*.v1.schema.yaml` files). All `.gald3r/` files carry `gald3r_rel_version` + `schema_version` provenance.
- **T1440** — `g-medic` L1 schema validation layer (auto-fix via `_fix_mappings.yaml`, missing-folder creation, schema report block) + g-rl-25 session-start Step 10b schema version probe (read-only, ≤5 files, <1s).
- **T1441** — Schema upgrade migration engine: `migrate_schemas.ps1` (dry-run default, `-Apply` to write; idempotent; data-preserving) + `platform_parity_sync.ps1 -MigrateSchemas`.
- **T1442** — Pristine canonical `.gald3r/` template at `.gald3r_sys/template_verification/` (66 files, T1439 frontmatter) as local restore/diff target; refreshed by `-SyncGaldSys` before propagation.
- **T1445** — `framework_inheritable_constraints.md` — full definition blocks for C-013 through C-023, ready for `@g-update` propagation to consumer `CONSTRAINTS.md`.
- **T1118** — Opt-in `@g-go --shared-sandbox` Phase 12 handoff: reviewer reuses implementer's worktree; `gald3r_worktree.ps1` gains `-Action Keep`/`-KeepHours` + cleanup protection.
- **T1239** — Profile-aware core skills: `g-go`/`g-go-code`/`g-go-review`/`g-status`/`g-skl-tasks`/`g-skl-status` read `workflow_profile` via `load_profile.ps1` instead of hardcoded status strings.

### Changed

- **BUG-107** (partial mitigation): `g-go-go` spec hardened — relabeling a context-pressure halt as a "session checkpoint" / "handing off cleanly" now explicitly named as the forbidden CONTEXT WINDOW PANIC violation.
- **T1437**: `@g-update --apply` gains version-reconciliation step for `gald3r_version` in consumer `.identity`.
- `.gitignore`: `/.gald3r_sys` root-anchored entry added (root is a junction; canonical tracked under `gald3r_template/.gald3r_sys`).
- PCAC → WPAC rename propagated across g-go* command suite (`.claude/commands/`, `.cursor/commands/`, canonical `gald3r_template/.gald3r_sys/`).

### Fixed

- **BUG-113** (Critical): Systematic truncated-name file corruption in `.claude/` and `.cursor/` trees across all ecosystem repos. Root cause: imperfect spawn during early WPAC v1.6 transition. Canonical-only allowlist cleanup applied to all 6 repos (skills, commands, agents, hooks, rules); `cleanup_platform_dirs.ps1` added to `custom_scripts/` for future use.
- **BUG-100** (High): `g-hk-session-start.ps1` here-string switched to single-quoted form — eliminates PS7 Unicode escape parse errors.
- **BUG-101** (Low): `gald3r_post_write_lint.ps1` PS5.1-safe color assignment + `Parser::ParseFile` for structural syntax errors.
- **BUG-102** (Low): `gald3r_version` in consumer `.gald3r/.identity` now updated on parity sync / `@g-update`.
- **BUG-103** (Medium): Root `VERSION` file created by both setup and `@g-update`.
- **BUG-104** (Medium): `@g-update` now backfills `.gald3r/releases/` from CHANGELOG versions.
- **BUG-106** (Low): `setup_gald3r_project.ps1` `$cat:` disambiguated to `${cat}`.
- **BUG-097** (High): `controlled_member` → `autonomous_child` promotion lifecycle now exists via T1435.
- **BUG-110** (High): Context Budget Gate + Conflict Pattern Gate HARD RULES restored to canonical `g-rl-33`.
- **BUG-111** (Medium): `regenerate_tasks_md.ps1` Linux-style path guard — auto-converts `/g/...` to `G:\...`.
- **BUG-093** (Low): TOON size-reduction docs ASCII `~` restored.

---

## Upgrade Instructions

From v1.5.x, run in your project:

```powershell
# Option A — via @g-update (recommended)
@g-update --apply

# Option B — manual migration
.gald3r_sys\scripts\migrate_schemas.ps1 -Apply
```

The migration engine is idempotent and safe to re-run.
