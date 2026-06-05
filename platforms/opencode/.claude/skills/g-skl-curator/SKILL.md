---
name: g-skl-curator
description: >
  Autonomous skill library curator — grades every SKILL.md against a structured rubric
  (recency, clarity, scope overlap, token efficiency, last-invoked rate), proposes
  consolidations and archive-candidate tags for low-scoring or overlapping skills, and
  writes a structured audit log. Never deletes — only proposes. Safe for unattended
  scheduled runs.
type: skill
tags: [skill-management, audit, rubric, consolidation, scheduling]
safety: file-read + file-write only; no Shell, no web fetch, no destructive ops
triggers:
  - "@g-curator"
  - "curate skills"
  - "audit skill library"
  - "grade skills"
  - "skill rubric"
  - "consolidate skills"
  - "prune skills"
token_budget: high
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# g-skl-curator

**Autonomous skill library curator.** Grades every `SKILL.md` across the gald3r IDE
platforms against a five-dimension rubric, identifies overlap, proposes consolidations
and archive candidates, and writes a structured audit log. The Curator **never deletes**;
it proposes — humans approve final action.

This skill is the gald3r skill-library curator pattern. It is designed
to run unattended on a 7-day cadence (via the gald3r Tauri scheduler / HEARTBEAT.md
contract documented below) and to be safe in autonomous mode: file-read + file-write only,
no Shell, no web fetch.

---

## Objective + Safety Boundary

**Objective**: keep the gald3r skill library lean, current, non-overlapping, and
accurately scoped. As gald3r ages and accumulates skills from multiple contributors,
uncurated overlap and staleness silently degrade agent performance. The Curator is the
counter-force.

**Safety boundary** (mandatory):

- File operations only: read and write under `.cursor/skills/`, `.claude/skills/`,
  `.agent/skills/`, `.codex/skills/`, `.opencode/skills/`, and write reports to
  `.gald3r/reports/`.
- No `Shell`, no `Bash`, no `PowerShell`, no `Edit` of skill bodies.
- No web fetch, no MCP calls.
- Never modifies SKILL.md content. Output is exclusively the audit log report.
- Never deletes. Output uses `archive_candidate` and `merge_candidate` tags only.

This means the Curator is safe to run unattended, in CI, and in scheduler-triggered
sessions where no human is present to approve a destructive action.

---

## Operations (modes)

```bash
@g-curator                       # GRADE (default) — full rubric pass + audit log
@g-curator --status              # summary table of last run (read latest report)
@g-curator --consolidate         # focus on merge proposals (overlap detection)
@g-curator --prune-candidates    # focus on archive proposals (low-scoring skills)
@g-curator --rank                # ranked list only (most → least valuable)
```

All modes write to `.gald3r/reports/skill_curator_YYYYMMDD.md`. `--status` reads the
most recent report and renders a summary; it does not re-grade.

---

## Inputs

The Curator enumerates every `SKILL.md` file across all five gald3r IDE platform skill
directories:

```
.cursor/skills/*/SKILL.md
.claude/skills/*/SKILL.md
.agent/skills/*/SKILL.md
.codex/skills/*/SKILL.md
.opencode/skills/*/SKILL.md
```

Skills present in multiple platforms (gald3r-owned `g-skl-*` skills are mirrored across
all five) are graded **once per logical skill name** to avoid penalising parity. Use the
`.claude/skills/` copy as the canonical source for grading; cross-check the others for
content drift and surface drift as a clarity finding.

The Curator also reads:

- `.gald3r/config/CURATOR_PROTECTED_SKILLS.md` — the pinning list (see "Protected list" below)
- `.gald3r/TASKS.md` — invocation-rate signal (count `@g-skill-name` mentions and
  command references)
- `.gald3r/subsystems/*.md` Activity Logs — invocation-rate signal
- `.gald3r/.identity` — `gald3r_version` for recency normalisation

---

## Rubric (5 dimensions, 1–5 scoring each)

The full scoring rubric lives in `reference/curator_rubric.md`. Summary:

| Dimension          | What it measures                                                      |
|--------------------|-----------------------------------------------------------------------|
| Recency            | last_modified date and last_invoked date                              |
| Clarity            | frontmatter completeness, scope statement, trigger-phrase coverage    |
| Scope overlap      | topic-array overlap and content overlap with sibling skills           |
| Token efficiency   | SKILL.md word count vs information density (target <5k words / ~500 lines) |
| Invocation rate    | references in TASKS.md, command files, Activity Log entries           |

Each dimension scores 1 (worst) → 5 (best). Composite score = unweighted sum (max 25).
A skill with composite < 12 is flagged for review; < 8 is flagged as `archive_candidate`.

See `reference/curator_rubric.md` for explicit anchor descriptions of each tier.

---

## Overlap detection (AC4)

A skill pair (A, B) is flagged as `merge_candidate` when **both** of the following hold:

1. **Topic overlap ≥ 70%**: `|A.topics ∩ B.topics| / max(|A.topics|, |B.topics|) ≥ 0.70`,
   where `topics:` is the YAML frontmatter array. Topics are normalised to lower-case
   and stripped of trailing punctuation before comparison.
2. **Content overlap ≥ 70%**: take the first 200 words of each SKILL.md body (post-
   frontmatter, post-h1) and compute Jaccard similarity over their lower-cased word
   bags (excluding a small stopword list). `≥ 0.70` triggers the flag.

When both conditions trigger, the audit log records:

```markdown
### Merge candidate: g-skl-foo ↔ g-skl-bar
- Topic overlap: 0.83 (5/6 topics shared)
- Content overlap: 0.74
- Proposed merged title: g-skl-foo-bar (or human-chosen)
- Combined trigger phrases: [list]
- Combined operations: [list]
- Suggested merge owner: <larger-by-content skill>
```

The Curator never performs the merge. It only records the proposal.

---

## Protected list (AC6)

The Curator reads `.gald3r/config/CURATOR_PROTECTED_SKILLS.md` at the start of every
run. Each `-` bullet under `## Protected (do not modify or merge)` is a protected
skill name. Pattern entries (e.g. `g-skl-pcac-*`) match all matching skill names.

Protected skills:

- **Are graded** like any other skill (their score still appears in the rank).
- **Never receive** `archive_candidate` or `merge_candidate` tags.
- **Are flagged** in the report as `[PROTECTED]` so reviewers see the pin reason.

If `CURATOR_PROTECTED_SKILLS.md` is missing, the Curator creates it with the framework
default list at `.gald3r/config/CURATOR_PROTECTED_SKILLS.md` and continues. (This is the
only file the Curator may create outside `.gald3r/reports/`.)

---

## Audit log path and format (AC5, AC10)

```
.gald3r/reports/skill_curator_YYYYMMDD.md
```

Multiple runs on the same calendar day overwrite the daily file (last run wins).
Historical reports accumulate across days. The format is:

```markdown
# Skill Curator Audit — YYYY-MM-DD

**Project**: {project_name} | **gald3r version**: {gald3r_version}
**Skills audited**: {N} | **Protected**: {P} | **Flagged**: {F}

## Ranked Skill List (most → least valuable)

| Rank | Skill | Composite | Recency | Clarity | Overlap | Tokens | Invoc. | Tags |
|------|-------|-----------|---------|---------|---------|--------|--------|------|
| 1    | g-skl-tasks    | 25/25 | 5 | 5 | 5 | 5 | 5 | [PROTECTED] |
| 2    | g-skl-medic    | 24/25 | 5 | 5 | 5 | 4 | 5 | [PROTECTED] |
| ...  | ...            | ...   | . | . | . | . | . | ...         |
| N    | g-skl-foo      |  6/25 | 1 | 2 | 1 | 1 | 1 | [archive_candidate] |

## Proposed Merges

### Merge candidate: g-skl-foo ↔ g-skl-bar
- (per the format above)

## Archive Candidates

### g-skl-foo  (score 6/25)
- **Why low**: not invoked since gald3r v0.4.x; topic overlap with g-skl-bar 0.83
- **Last invoked**: 2025-12-14 (TASKS.md mention in T412)
- **Suggested action**: archive — covered by g-skl-bar
- **Human required**: yes (Curator never archives directly)

## Prune Candidates (subset of Archive Candidates)

(skills with score < 8 AND zero invocations in the last 90 days)

## Drift Findings

(skills whose content differs across .cursor / .claude / .agent / .codex / .opencode copies)

## Protected Skills

(list of skills exempted from archive/merge proposals, with pin reason)

## Run Metadata

- run_started: ISO-8601
- run_completed: ISO-8601
- skills_enumerated: N
- platforms_scanned: [.cursor, .claude, .agent, .codex, .opencode]
- protected_list_path: .gald3r/config/CURATOR_PROTECTED_SKILLS.md
- protected_list_count: P
```

The ranked list is the headline output for AC10 — it is the structured `curator status`
output that downstream tooling consumes.

---

## Output discipline (AC9 — never deletes)

The Curator **never** writes:

- `delete_candidate`
- `remove_immediately`
- `prune_now`
- any tag, recommendation, or wording that implies destructive action

The only sanctioned tags are:

- `archive_candidate` — move to archive on human approval
- `merge_candidate` — merge with named partner on human approval
- `[PROTECTED]` — informational marker; never paired with action tags
- `[DRIFT]` — copies across IDE platforms have diverged; informational

A human approves the final action via `@g-task-add` (to track the archive/merge as a
task) or by editing the audit log to record the decision.

---

## Manual trigger (AC7)

The `@g-curator` slash command is the manual entry point. The command file is mirrored
across all five IDE platforms (`.cursor/commands/g-curator.md`,
`.claude/commands/g-curator.md`, `.agent/commands/g-curator.md`,
`.codex/commands/g-curator.md`, `.opencode/commands/g-curator.md`) so any IDE can
invoke it. See the command file for argument details.

---

## Scheduled trigger (AC8 — HEARTBEAT.md / WAKEUP_QUEUE.md integration contract)

The Curator is designed to run unattended on a 7-day cadence. The integration contract
with the gald3r Tauri desktop scheduler is:

### `HEARTBEAT.md` contract

The Curator expects (and the scheduler should write) a `curator_last_run` field in
`.gald3r/config/HEARTBEAT.md`:

```markdown
## Curator Schedule

- curator_last_run: 2026-05-01T03:00:00Z
- curator_cadence_days: 7
- curator_next_due: 2026-05-08T03:00:00Z
- curator_last_report: .gald3r/reports/skill_curator_20260501.md
- curator_last_status: success
```

Session-start logic (in `g-rl-25-gald3r_session_start.md`) may surface
`Curator overdue: run @g-curator` when `now > curator_next_due`. The Curator itself
does NOT modify HEARTBEAT.md (HEARTBEAT.md is owned by `g-medic` / scheduler) — it only
**reads** the schedule and **writes** the audit report. The scheduler is responsible
for updating `curator_last_run` after a successful Curator pass completes.

### `WAKEUP_QUEUE.md` contract

When the Tauri scheduler fires a wakeup that includes Curator work, the queue entry
shape is:

```markdown
## WAKE: 2026-05-08T03:00:00Z
- task: run-curator
- skill: g-skl-curator
- mode: GRADE
- approval_required: false   # safe-to-run unattended
- on_completion:
  - update HEARTBEAT.md curator_last_run
  - record path of new report under curator_last_report
```

### Implementation note

This skill documents the contract. Full Tauri scheduler implementation is owned by
`g-skl-medic` (HEARTBEAT.md owner) and the desktop scheduler subsystem; that is out of
scope for this skill. AC8 is satisfied by documenting the contract — any Tauri schedule
that honours these field names can drive the Curator without further changes here.

---

## Trigger phrases (skill loader)

The skill loader should activate `g-skl-curator` when the user says any of:

- `@g-curator`
- `curate skills`
- `audit skill library`
- `grade skills`
- `skill rubric`
- `consolidate skills`
- `prune skills`
- `skill curator status`

Phrases like "delete this skill" or "remove a skill" must NOT activate the Curator —
those are explicit destructive actions and route to `g-skl-medic --curate --apply` or to
manual edits with task ownership, not to the Curator.

---

## Recommended workflow for human reviewers

1. Run `@g-curator` (or wait for the 7-day scheduled run).
2. Open the latest `skill_curator_YYYYMMDD.md` report.
3. Walk the ranked list top-to-bottom. The bottom of the list is where action is needed.
4. For each `archive_candidate`:
   - If the rationale holds, `@g-task-add type=cleanup title="Archive g-skl-foo"`.
   - If the skill is unjustly low-scored, add it to `CURATOR_PROTECTED_SKILLS.md`
     with a `# pinned because <reason>` comment.
5. For each `merge_candidate`:
   - If the merge makes sense, `@g-task-add type=feature title="Merge g-skl-foo into g-skl-bar"`.
   - If not, add the lower-priority skill to `CURATOR_PROTECTED_SKILLS.md`.
6. For each `[DRIFT]` finding:
   - Run platform parity sync (`custom_scripts/platform_parity_sync.ps1 -Sync`) to converge copies.
7. Re-run `@g-curator --status` after applied changes to confirm.

---

## Failure modes and what the Curator does NOT do

- **Does not** rewrite SKILL.md content (no auto-trim, no auto-merge, no auto-rename).
- **Does not** delete files.
- **Does not** modify HEARTBEAT.md, TASKS.md, BUGS.md, or CHANGELOG.md.
- **Does not** call any MCP tool, web service, or shell command.
- **Does not** propose actions for protected skills.
- **Does not** consider non-gald3r skills (those without a `g-skl-` or platform-managed
  YAML frontmatter) as part of the gald3r library; they are scored only for drift and
  total-token-budget telemetry.

If the Curator cannot read a SKILL.md (malformed YAML, IO error), it records the file
under `## Run Metadata → skip_reasons` with the error and continues. A failed read is
never grounds for a delete or archive proposal.

---

## Related skills

- `g-skl-knowledge-refresh` — vault audit (parallel role, scope = vault notes, not skills)
- `g-skl-learn` — memory consolidation (parallel role, scope = `learned-facts.md`)
- `g-skl-medic` — `.gald3r/` health (broader scope; Curator complements `--curate` mode by
  focusing exclusively on the skill library)
- `g-skl-subsystems` — subsystem audit (parallel role, scope = `subsystems/`)

---

## See Also

- `reference/curator_rubric.md` — full 1–5 scoring criteria for each dimension
- `.gald3r/config/CURATOR_PROTECTED_SKILLS.md` — pinning list
- `.claude/commands/g-curator.md` — manual trigger command spec
- Task 831 — original implementation task
