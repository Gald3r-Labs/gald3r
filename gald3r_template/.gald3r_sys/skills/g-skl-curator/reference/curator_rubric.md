# Curator Rubric — Five-Dimension Scoring Reference

Each `SKILL.md` is scored 1 (worst) → 5 (best) on each of the five rubric dimensions.
Composite score = unweighted sum, max 25. The Curator uses these anchor descriptions
verbatim — do not infer or adjust scores beyond what the anchors describe.

---

## Dimension 1: Recency

Measures how current the skill is relative to recent gald3r evolution. Two signals:

- **last_modified**: file mtime of the SKILL.md
- **last_invoked**: most recent reference in `.gald3r/TASKS.md` history, command files,
  or `.gald3r/subsystems/*.md` Activity Logs

| Score | Anchor                                                                                  |
|-------|-----------------------------------------------------------------------------------------|
| 5     | last_modified within 30 days OR last_invoked within 30 days                             |
| 4     | last_modified within 90 days OR last_invoked within 90 days                             |
| 3     | last_modified within 180 days; last_invoked within 180 days                             |
| 2     | last_modified within 365 days; last_invoked within 365 days                             |
| 1     | not modified or invoked in >365 days; references only the deprecated phase/v2 layout    |

Tie-breaker: if `last_invoked` and `last_modified` produce different scores, use the
**higher** of the two.

---

## Dimension 2: Clarity

Measures how readable, complete, and discoverable the skill is. Inspect:

- YAML frontmatter — required fields: `name`, `description`, plus at least one of
  `topics`, `triggers`
- A scope statement in the body (one or two sentences explaining when to use this skill)
- Trigger-phrase coverage in either `triggers:` frontmatter or a "When to Use" section
- Section headings (`## Operations`, `## Inputs`, `## Output`, `## See Also`) — at
  least three of these conventional sections present
- No broken Markdown (unbalanced fences, missing closing brackets)

| Score | Anchor                                                                                  |
|-------|-----------------------------------------------------------------------------------------|
| 5     | Full frontmatter; clear scope; ≥5 trigger phrases; ≥4 conventional sections; no Markdown errors |
| 4     | Full frontmatter; clear scope; ≥3 trigger phrases; ≥3 conventional sections             |
| 3     | Frontmatter present but missing one optional field; scope statement implicit; ≥1 section |
| 2     | Frontmatter incomplete OR scope unclear OR no trigger phrases                           |
| 1     | No frontmatter OR no scope OR Markdown is broken OR body is a stub <50 lines            |

---

## Dimension 3: Scope overlap

Measures how much the skill duplicates or overlaps with siblings. Computed pairwise:

- **Topic overlap**: `|A.topics ∩ B.topics| / max(|A.topics|, |B.topics|)` (set ratio
  on the YAML `topics:` array, lower-cased)
- **Content overlap**: Jaccard similarity over the first 200 words of body text, lower-
  cased, stopwords removed

For each skill, take its **maximum overlap** against any other (non-protected) skill.

| Score | Anchor                                                                                  |
|-------|-----------------------------------------------------------------------------------------|
| 5     | Max overlap < 0.30 (clearly distinct scope)                                             |
| 4     | Max overlap 0.30–0.49                                                                   |
| 3     | Max overlap 0.50–0.59                                                                   |
| 2     | Max overlap 0.60–0.69 (close call; report but no merge tag)                             |
| 1     | Max overlap ≥ 0.70 (auto-flag as `merge_candidate`)                                     |

A score of 1 here triggers the `merge_candidate` tag in the audit log; the partner skill
with the highest overlap becomes the proposed merge target.

---

## Dimension 4: Token efficiency

Measures how much information density the skill delivers per byte. The skill-creator
contract caps SKILL.md at ~5000 words / ~500 lines (entry #23 in CLAUDE.md learned
facts). Reference content beyond that belongs in `reference/` files.

Compute:

- **word_count**: words in SKILL.md body (post-frontmatter)
- **info_density**: number of distinct operations, trigger phrases, and section headings
  per 1000 words

| Score | Anchor                                                                                  |
|-------|-----------------------------------------------------------------------------------------|
| 5     | 200–500 lines AND ≥6 operations/sections per 1000 words (lean and dense)                |
| 4     | 500–800 lines OR 4–5 operations/sections per 1000 words                                 |
| 3     | 200–1000 lines, average density (3 operations/sections per 1000 words)                  |
| 2     | <100 lines (stub) OR 1000–1500 lines (bloated)                                          |
| 1     | <50 lines (placeholder) OR >1500 lines (egregious bloat — should be split into reference/) |

A skill scoring 1 or 2 here often pairs with a low Clarity score and is a candidate for
either a content rewrite (high-overlap stubs → merge) or a content split
(>1500-line bloat → move encyclopedic content to `reference/`).

---

## Dimension 5: Invocation rate

Measures how much the skill is actually used. Signals:

- Mentions of the skill name (`g-skl-foo` or its `@g-foo` command) in `.gald3r/TASKS.md`
- References from command files (`.cursor/commands/`, `.claude/commands/`, etc.)
- Mentions in `.gald3r/subsystems/*.md` Activity Log rows
- Mentions in other SKILL.md `## See Also` sections

Count distinct mentions across all sources. Time-weight: mentions in the last 90 days
count double; mentions older than 365 days count half.

| Score | Anchor                                                                                  |
|-------|-----------------------------------------------------------------------------------------|
| 5     | ≥10 weighted mentions in the last 365 days; ≥3 in the last 90 days                      |
| 4     | 5–9 weighted mentions in the last 365 days                                              |
| 3     | 2–4 weighted mentions in the last 365 days                                              |
| 2     | 1 weighted mention in the last 365 days                                                 |
| 1     | Zero mentions in the last 365 days (truly inert)                                        |

**Important**: protected skills (e.g. `g-skl-tasks`, `g-skl-medic`) routinely score 5
here because they are core. New skills (added in the last 30 days) get a grace floor of
3 — they have not had time to accumulate invocations.

---

## Composite score interpretation

Composite = sum of all five dimension scores. Range: 5 (worst) to 25 (best).

| Composite | Bucket                                            | Action                                          |
|-----------|---------------------------------------------------|-------------------------------------------------|
| 22–25     | Healthy                                           | None (informational rank only)                  |
| 17–21     | Acceptable                                        | None                                            |
| 12–16     | Watch                                             | Surface in report; no auto-tag                  |
| 8–11      | Flagged                                           | Tag `archive_candidate` UNLESS protected        |
| 5–7       | Critical                                          | Tag `archive_candidate`; log as prune candidate UNLESS protected |

A skill that is in the protected list bypasses tag assignment but still receives the
composite score and bucket label. The `[PROTECTED]` marker appears in the rank table
beside the score.

---

## Examples (illustrative — not actual gald3r skill scores)

```
g-skl-tasks         | 5 + 5 + 5 + 5 + 5 = 25 (Healthy, [PROTECTED])
g-skl-medic         | 5 + 5 + 5 + 4 + 5 = 24 (Healthy, [PROTECTED])
g-skl-cli-opencode  | 4 + 3 + 4 + 5 + 1 = 17 (Acceptable; new, low invocations)
g-skl-foo-stub      | 1 + 1 + 1 + 1 + 1 = 5  (Critical, archive_candidate)
g-skl-bar-overlap   | 4 + 3 + 1 + 4 + 3 = 15 (Watch; high overlap → merge_candidate)
```

---

## Notes for the Curator agent

- Always score every dimension. Never abstain. If a signal is unavailable (e.g. no
  TASKS.md), default the affected dimension to **3** (neutral) and record the reason
  under `## Run Metadata → assumptions`.
- Round all overlap ratios to 2 decimal places.
- Do not invent thresholds outside this table. If a score feels wrong, surface it as a
  rubric-tuning suggestion in the audit log's `## Run Metadata` section, not as an
  ad-hoc score adjustment.
- Protected skills are never `archive_candidate` or `merge_candidate`, regardless of
  composite. Always honour the protected list (see `.gald3r/config/CURATOR_PROTECTED_SKILLS.md`).
