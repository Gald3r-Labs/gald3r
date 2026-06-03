**Released:** 2026-05-25
**Version:** 1.6.0
**Type:** Minor -- new features, no breaking changes
**Previous release:** [v1.5.0](RELEASE_v1.5.0.md)

---

## Highlights

### Schema enforcement system
Every `.gald3r/` file now carries version provenance, validated against 15 versioned
schema definitions. A read-only session-start probe flags drift in under a second, and a
data-preserving migration engine (`migrate_schemas.ps1`) upgrades older files in place.
`g-medic` gained an L1 validation layer that auto-fixes common schema gaps.

### Semantic versioning and release management
New `g-skl-ship` skill and `@g-ship` command promote your CHANGELOG `[Unreleased]` section
to a real version: it bumps `VERSION`, tags the release, and can publish. Task and bug
completion now feed CHANGELOG entries automatically.

### Dedicated bug-fix pipeline
`@g-go-bugs` (and its swarm variant) is an autopilot built only for bugs: it reproduces,
fixes, writes a regression test, and runs an adversarial cold review -- working through
your backlog in severity order, critical first.

### Encoding normalization
A new pre-commit and stop-event hook normalizes line endings and BOM policy, with a
content-aware guard that leaves real binary files untouched. Shipped with a `.gitattributes`
scaffold and a one-command git-hooks installer so fresh installs are protected by default.

### Cross-project promotion lifecycle
Workspace members can now graduate from a lightweight "controlled member" to a fully
independent "autonomous child" via `@g-wpac-promote`, with a formal, dry-run-first
lifecycle instead of hand-editing files.

### Autopilot robustness
`g-go-go` gained a context-aware mode that shrinks its parallel batch size under context
pressure instead of stopping mid-run, plus a stop-detection guard that resumes a stalled
loop when it halts without an authorized reason.

---

## Notable Fixes

- Cross-platform file corruption from an early coordination transition was cleaned up
  across all framework trees, and a reusable cleanup script was added.
- Several PowerShell hook parse and compatibility issues resolved.
- Root `VERSION` file and `.gald3r/releases/` history are now created and backfilled by
  both setup and `@g-update`.
- Context Budget and Conflict Pattern hard rules restored to the core enforcement ruleset.

---

## Install / Upgrade

From v1.5.x, run in your project:

```powershell
# Recommended
@g-update --apply

# Or migrate schemas directly (idempotent, safe to re-run)
.gald3r_sys\scripts\migrate_schemas.ps1 -Apply
```

For a fresh install see [instructions_new_project.md](../instructions_new_project.md).
