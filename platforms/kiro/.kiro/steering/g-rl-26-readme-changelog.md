---
description: Agents must update CHANGELOG.md and README.md when completing user-facing feature tasks
globs: ["**/*.md", "**/*.mdc", "**/*.ps1", "**/*.json"]
alwaysApply: true
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

# Rule: Update Documentation at Feature Boundary

When completing any task that **adds, removes, or changes user-facing behavior** — skills, commands,
hooks, agents, rules, conventions, or any element visible to end-users — the completing agent MUST:

## 1. Append to CHANGELOG.md

Add an entry under the `[Unreleased]` section using Keep a Changelog format:

```markdown
### Added
- Feature description with relevant command/file names

### Changed
- What changed and what it replaces

### Removed
- What was deprecated or removed
```

- Place the entry in the appropriate subsection (`Added`, `Changed`, `Removed`)
- Be specific: include command names, file paths, or skill names
- One entry per logical change (not one per file)

## 2. Update README.md (If Relevant Section Exists)

If the completed task changes something that has a section in `README.md`:
- Update the relevant section to reflect the new state
- Update counts in the "What's Included" table if agents/skills/commands count changed
- Update command names if they were renamed

## What Qualifies as "User-Facing"

**YES — must update docs:**
- New command, skill, agent, hook, or rule
- Renamed/deprecated command, skill, agent
- Changed behavior of an existing command
- New convention that agents must follow
- New configuration option

**NO — can skip:**
- Internal refactor with no behavior change
- Task file updates (TASKS.md, individual task specs)
- Bug fix with no interface change
- Code comments or inline documentation

## Where to Update

| Project type | CHANGELOG.md | README.md |
|-------------|--------------|-----------|
| <gald3r_source> (this repo) | `gald3r_core/CHANGELOG.md` (the file the release pipeline promotes — see note below) | `README.md` at root (contributor view) |
| <ECOSYSTEM_ROOT>/<template_full> | `<ECOSYSTEM_ROOT>/<template_full>/CHANGELOG.md` | `<ECOSYSTEM_ROOT>/<template_full>/README.md` (end-user view) |
| Installed gald3r project | `CHANGELOG.md` at project root | `README.md` at project root |

> **Canonical changelog for this repo (BUG-185).** The release pipeline (`Forge().publish` / `Forge().ship`) reads and promotes **`gald3r_core/CHANGELOG.md`** — `PublishSystem._finalize_release_notes` renames its `[Unreleased]` block to `[X.Y.Z]`, and the ship pre-flight audit (`ShipSystem._audit_unreleased_nonempty`) refuses to cut a release when that same file's `[Unreleased]` is empty. Framework-facing changes to this repo MUST land in `gald3r_core/CHANGELOG.md` `[Unreleased]`, not the root `CHANGELOG.md`. Logging into the root file instead is exactly what left `gald3r_core`'s `[Unreleased]` empty at ship time (BUG-185). The root `CHANGELOG.md` stays a human contributor-facing summary of the distribution pipeline; it is NOT what the release pipeline promotes.

## Timing

- Update docs **before** marking the task `[🔍]` (awaiting verification)
- Docs check is part of the `g-go` and `g-go-code` post-task checklist

## 3. Golden-Fixture Baseline Refresh (T446 — `neutral_source/` content changes)

If the completed task edits **any** of:
- `src/gald3r_core/platform/pipeline/neutral_source/**` (skills, hooks, commands, rules content)
- `src/gald3r_core/platform/layout_map.yaml`
- `.gald3r/PLATFORM_CAPABILITY_MATRIX.md`

then, **before** marking the task `[🔍]`, re-run **both** refresh scripts and stage the
regenerated JSON in the same commit:

```
.venv/Scripts/python.exe tests/fixtures/platform_golden/refresh_baseline_hashes.py
.venv/Scripts/python.exe tests/fixtures/embedded_overlay_snapshot/refresh_baseline_hashes.py
```

Never hand-edit either `baseline_hashes.json`. This is the exact drift pattern that recurred
THREE times (BUG-386, BUG-400, and a third live recurrence found during T446 itself,
commit `0faea7c0`/T445) before a deterministic gate existed. T446 landed
`scripts/check_golden_fixture_baseline_freshness.py`, wired into **both**:

- `.github/workflows/ci.yml`'s `lint` job (MANDATORY — runs unconditionally on every push to
  `main` and every PR, independent of any local git-hook opt-in)
- `.githooks/pre-commit` Stage 3 (best-effort local feedback for anyone who has run
  `git config core.hooksPath .githooks`)

This rule is the **documentation-side companion** to that gate (agents should refresh
proactively, not just react to the gate failing), not a substitute for it — see the
script's own module docstring for the full mechanism-choice rationale (why a deterministic
hash-comparison gate was chosen over a documentation-only rule or a periodic CI job alone).
