---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# /g-curator

Activate the **g-skl-curator** skill — autonomous skill library audit.

The Curator grades every `SKILL.md` across all five gald3r IDE platform skill
directories against a five-dimension rubric (recency, clarity, scope overlap, token
efficiency, invocation rate), identifies overlap, proposes consolidations and archive
candidates, and writes a structured audit log. It is safe to run unattended — file IO
only, no Shell, no web fetch.

## Modes

- `@g-curator` (default GRADE) — grade all skills against the rubric, write audit log
  to `.gald3r/reports/skill_curator_YYYYMMDD.md`
- `@g-curator --status` — summary table of the most recent run (read-only; does not
  re-grade)
- `@g-curator --consolidate` — focus on merge proposals (overlap detection)
- `@g-curator --prune-candidates` — focus on archive proposals (low-scoring skills)
- `@g-curator --rank` — ranked skills list only (most → least valuable)

## Output

A daily audit log at `.gald3r/reports/skill_curator_YYYYMMDD.md` containing:

1. Ranked skill list (most → least valuable)
2. Proposed merges (overlap ≥ 70% on both topics and content)
3. Archive candidates (composite score < 8, not protected)
4. Prune candidates (subset: archive candidates with zero invocations in 90 days)
5. Drift findings (cross-platform copy divergence)
6. Protected skills (informational)
7. Run metadata

## Output discipline

The Curator **NEVER deletes**. It only proposes via `archive_candidate` and
`merge_candidate` tags. Humans approve final action.

Skills listed in `.gald3r/config/CURATOR_PROTECTED_SKILLS.md` are graded but never
proposed for archive or merge.

## Scheduled use

The Curator is designed to run unattended on a 7-day cadence via the gald3r Tauri
desktop scheduler. See the `HEARTBEAT.md` / `WAKEUP_QUEUE.md` integration contract in
the `g-skl-curator` SKILL.md for field shapes.

## Trigger phrases

`@g-curator` | `curate skills` | `audit skill library` | `grade skills` | `skill rubric`
| `consolidate skills` | `prune skills`
