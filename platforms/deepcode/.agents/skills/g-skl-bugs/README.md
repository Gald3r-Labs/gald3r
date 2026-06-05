---
subsystem_memberships: [BUG_AND_QUALITY]
---
# g-skl-bugs

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this
> page is for developers browsing the skill library on GitHub.

## What it does

Owns every piece of bug data in `.gald3r/`. Mirrors `g-skl-tasks` but for defects:

- `.gald3r/BUGS.md` — active bug index.
- `.gald3r/bugs/**/*.md` — one file per bug, in `open/`, `done/YYYY/MM/`, or `closed/`.
- `.gald3r/archive/archive_bugs_*.md` and `.gald3r/archive/bugs/**` — bounded archive ledger.

If you see an error, warning, or "pre-existing issue" in any session — this is the skill that records it.

## When to use

- Filing a new bug, fixing a bug, archiving resolved bugs
- Anything mentioning `BUG-NNN`, error, warning, defect, regression
- Quality metrics review
- Post-mortems / failure autopsies

## Trigger phrases

```
@g-bug-add | @g-bug-fix | @g-bug-upd | @g-bug-del | @g-bug-archive | @g-bug-report
```

## Zero-tolerance auto-trigger

Per `g-rl-33` (Enforcement Catchall) and `g-rl-35` (Bug-Discovery Gate), this skill **must** fire whenever:

- Any response mentions `error`, `warning`, `pre-existing`, `unrelated error`, `exception`.
- A task is moved back to `[📋]` by `@g-go-review` (one bug per failing criterion).
- Code was fixed in a session without a prior bug report (retroactive filing required).

"Pre-existing" is not an exemption. Logging takes 30 seconds; debugging a mystery defect takes hours.

## Examples

### Fast-path report

```
@g-bug-add
  title: "Off-by-one in page count"
  severity: medium
  file: src/views/PaginatedList.tsx:42
```

Produces `bugs/open/bug{NNN}_off_by_one_in_page_count.md` and indexes it.

### Mark fix done

```
@g-bug-fix BUG-021 --resolved-by T1043 --commit abc123
```

Appends fix metadata to the bug file, moves it to `bugs/done/YYYY/MM/`, and updates BUGS.md.

### Archive sweep

```
@g-bug-archive --dry-run
@g-bug-archive --apply
```

Moves terminal bug history to `.gald3r/archive/archive_bugs_*.md` count buckets while keeping BUGS.md as an active index.

## File ownership boundary

Only this skill writes to:

- `.gald3r/BUGS.md`
- `.gald3r/bugs/**/*.md`
- `.gald3r/archive/archive_bugs_*.md`
- `.gald3r/archive/bugs/**`

## See also

- `g-skl-tasks` — sibling skill for the parallel task surface
- `g-rl-33` — error-mention auto-trigger rule
- `g-rl-35` — bug-discovery gate (current-task vs pre-existing bug routing)
- `g-skl-review` — code review skill that files bugs as side effects
