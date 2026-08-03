---
name: g-skl-drift
description: Compute a deterministic, code-computed drift score per task-claim territory and per dev from local .gald3r state, and emit it as a local report or a g-skl-json-output-compatible JSON payload. Serves D15 (territory leasing + onboarding + drift skills).
token_budget: low
subsystem_memberships: [WORKSPACE_COORDINATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

> **Score definition v1 (`drift_score_version: 1`, T195 / D15):** implemented directly in
> `scripts/drift_score.py`. The version number is bumped whenever the weights, caps, or
> formula below change, so `throne`/`world_tree` consumers can detect and handle a
> definition change instead of silently misreading old vs. new scores.

# g-skl-drift

## When to Use

Use this skill whenever you (or a coordinator, or `throne`) need a **deterministic, at-a-glance
signal of how far a claimed task/worktree has drifted** from a healthy, actively-progressing
state — no LLM judgment call, ever (the model may summarize the report's already-computed
numbers, but never assigns or adjusts the score itself).

Typical callers:
- A coordinator doing a swarm health check before deciding whether to reclaim a stale task.
- `@g-medic` triage wanting one more deterministic signal alongside its structural checks.
- A human running `drift_score.py --json` to feed a dashboard or CI gate
  (`jq '.data.summary.high_count'`).

## Territory vs. task-claim (honest scope note)

The task that seeded this skill (T195, migrated from `gald3r_templates_dev/task1614`) says
"per-territory / per-dev drift metric" and points at `g-skl-territory`. On investigation,
**`g-skl-territory`'s documented backend (`gald3r/db.py`'s `lease_territory`/`territory_leases`
SQLite table) does not exist anywhere in this repo** — grepping `src/`, `.gald3r_sys/` (absent
in this checkout), and this worktree found the API referenced only in `g-skl-territory`'s own
`SKILL.md`/`README.md`. It may live in the separate `gald3r_agent_dev` engine repo (not
reachable from this environment) or may simply not be built yet.

Rather than compute drift against a lease table that isn't callable, v1 keys "territory" off
the real, verifiable primitive that already exists in every task file: the
**`claimed_by` / `claim_expires_at`** frontmatter pair (the exact same INSERT-OR-IGNORE +
expiry-takeover *pattern* `g-skl-territory` describes, just applied to `task_claims`-shaped
data instead of a not-yet-real `territory_leases` table) plus each task's `subsystems:` list as
the territory label. **If/when `g-skl-territory`'s real backend lands**, `drift_score.py`'s
`find_worktree_marker`/claim-lookup layer is the one place to repoint at it — the scoring
math (`compute_claim_staleness`, etc.) does not need to change, only the data source.

## Score Definition v1

Three signals, each normalized to **0–100** (higher = more drift), combined into one
`drift_score` (0–100) per claimed task:

| Signal | What it measures | Source | Cap (default) |
|---|---|---|---|
| `claim_staleness` | Minutes past `claim_expires_at` with no renew, scaled to the cap | task frontmatter `claim_expires_at` | 120 min |
| `worktree_staleness` | Age of the matching `.gald3r-worktree.json` marker's `created_at`, halved if `last_checkpoint_sha != base_sha` (real progress since creation) | `.gald3r-worktree.json` (g-rl-02) | 240 min |
| `uncommitted_footprint` | `git status --porcelain` file count inside that worktree, scaled to the cap | `git status` in the worktree dir | 25 files |

```
drift_score = clamp(0, 100,
    0.5 * claim_staleness + 0.3 * worktree_staleness + 0.2 * uncommitted_footprint)
```

Bands: `low` (< 25), `medium` (25–59.9), `high` (≥ 60). A subject with **no** claim
(`claim_expires_at` unset), **no** matching worktree marker, or a **clean** worktree simply
scores 0 on that signal — absence of a signal is never treated as drift.

**Territory** = the task's `subsystems:` frontmatter (joined; `UNASSIGNED` if empty).
**Dev** = `claimed_by` (falls back to the worktree marker's `owner`, then `unclaimed`).
Per-territory and per-dev rows aggregate every task in that group's `drift_score` as both an
average and a max, banded off the max (one badly-drifted task should not be hidden by an
average).

All of this is pure, deterministic code (`drift_score.py`'s `compute_*` functions) — there is
no model call anywhere in the scoring path, satisfying the "code-computed, model only
summarizes" requirement from the original spec.

## Operation: REPORT

```bash
uv run python .claude/skills/g-skl-drift/scripts/drift_score.py \
  [--root <repo_root>] [--status in-progress ...] \
  [--claim-stale-cap-min N] [--worktree-stale-cap-min N] [--uncommitted-cap-files N] \
  [--worktree-root <dir>] [--json] [--compact]
```

- Default `--status` is `in-progress` (the only status with a live claim/worktree in
  practice); pass `--status all` or repeat `--status` for other buckets.
- Text mode (default) prints a per-task table plus by-territory/by-owner rollups and a
  summary line — a local report, no flags needed.
- `--json` wraps `data` in the standard `g-skl-json-output` envelope
  (`gald3r_version`/`generated_at`/`command: "g-skl-drift"`/`schema: "drift"`/`data`) — see
  `g-skl-json-output/SKILL.md` for the envelope contract this reuses rather than reinventing.
  `data` is `{drift_score_version, subjects[], by_territory[], by_owner[], summary, params}`.
- Exit codes: `0` = no `high`-band subject, `2` = at least one `high`-band subject (usable as
  a CI/medic gate), `1` = usage/IO error (e.g. no `.gald3r/` found).

## Consumability (local report + future event payload)

The `--json` output is intentionally the same shape whether read by a human, piped to
`jq`, or (per the original spec's forward-looking intent) later pushed by a WPAC-v2
transport to `world_tree` for `throne` to render — **that transport does not exist yet in
this repo** (see T263–T266) and building it is explicitly out of scope for this task; this
skill only guarantees the payload is ready to be forwarded once it does.

## Offline / No-DB Dependency (C-011)

Every input is a file already on disk (`.gald3r/tasks/**/*.md`, `.gald3r-worktree.json`) or a
local `git status` call scoped to one worktree directory. No SQLite/`gald3r.db` read, no
network call, no MCP dependency — fully offline-capable.

## Relationship to Existing Primitives

| Primitive | Owns | This skill |
|---|---|---|
| Task-claim frontmatter (`claimed_by`/`claim_expires_at`) | Exactly-one-claimer semantics per task (same pattern `g-skl-territory` documents) | Reads it as the v1 "territory lease" stand-in — does not mutate it |
| `.gald3r-worktree.json` (g-rl-02) | Per-worktree ownership/checkpoint metadata | Reads `created_at`/`base_sha`/`last_checkpoint_sha`/`owner`/`worktree_path` |
| `g-skl-json-output` | JSON envelope + schema conventions | Reused verbatim for `--json` output (no second envelope format invented) |
| `g-skl-territory` | Documented (not-yet-backed) territory lease API | Complementary — see "Territory vs. task-claim" above; repoint here if/when it lands |

## Example

```bash
$ uv run python .claude/skills/g-skl-drift/scripts/drift_score.py --status in-progress

=== g-skl-drift (T195 / D15) ===
  root: G:/gald3r_labs/gald3r_core_dev
  weights: claim=0.5 worktree=0.3 uncommitted=0.2
  caps: claim=120.0min worktree=240.0min uncommitted=25.0files
  statuses scanned: in-progress

  TASK    OWNER                 TERRITORY                     CLAIM     WT   UNCM   DRIFT  BAND
  T195    ggo-iter22-coordinator WORKSPACE_COORDINATION           0.0   8.3    4.0     4.7  low

  -- by territory --
  WORKSPACE_COORDINATION      tasks=1    avg=   4.7 max=   4.7 band=low

  -- by owner (dev) --
  ggo-iter22-coordinator       tasks=1    avg=   4.7 max=   4.7 band=low

  SUMMARY: 1 task(s) -- high=0 medium=0 low=1
```
