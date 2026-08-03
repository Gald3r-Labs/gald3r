---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
# g-skl-drift
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for
> developers browsing the skill library.

## What it does

Computes a deterministic, code-only "how drifted is this claimed task/worktree" score
(0-100, banded low/medium/high) per task, then rolls it up **by territory**
(`subsystems:` frontmatter) and **by dev** (`claimed_by`). Emits either a text report or a
`g-skl-json-output`-compatible JSON envelope. Serves D15 — territory leasing + onboarding +
drift skills.

## When to use

- Before reclaiming a task that looks stale, to confirm it actually is (past-expiry claim,
  aging worktree with no checkpoint progress, growing uncommitted footprint).
- As one more deterministic signal in a `@g-medic` triage pass.
- Feeding a dashboard/CI gate via `--json` (`data.summary.high_count`, exit code `2` on any
  high-band subject).
- See the **When to Use** / **Score Definition v1** sections of `SKILL.md` for the
  authoritative formula and the honest scope note on why this does NOT key off
  `g-skl-territory`'s documented (but unbacked-in-this-repo) lease table.

## Backing implementation

- `scripts/drift_score.py` — pure-stdlib, no `yaml`/network/DB dependency. Optionally reuses
  `gald3r_core.project.gald3r_integration.local_ops_parsing.parse_frontmatter` and
  `gald3r_core.core.worktree.manifest.read_metadata` when importable (g-rl-04 DRY), with a
  dependency-light fallback parser so the script still runs standalone.
- Tests: `tests/platform/pipeline/test_drift_score.py` (loads the script by file path, same
  pattern as `tests/platform/pipeline/test_recon_yt_fetch_transcript.py`).

## Related skills

- `g-skl-territory` — the aspirational per-territory lease primitive this skill's "territory"
  grouping stands in for until that backend exists; see `SKILL.md`'s scope note.
- `g-skl-json-output` — the envelope/schema convention this skill's `--json` output reuses
  rather than inventing a second one.
- `g-skl-medic` — a natural caller of this skill's `high`-band signal during triage.
- See the gald3r skill index for the full list.
