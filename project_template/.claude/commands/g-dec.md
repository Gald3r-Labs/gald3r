---
description: 'Present the outstanding OWNER decisions — each with context, options, and a recommendation — grouped by how much of the owner''s time they need'
argument-hint: '[all|quick|<topic filter>]'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
---
Outstanding owner-decision stack: $ARGUMENTS

## What This Command Does

Aggregates every decision currently **waiting on the owner** from across the
project's coordination state and presents them as one numbered stack the owner
can answer in a single reply. This exists because agent sessions repeatedly
rediscover and re-summarize the same pending decisions by hand (T548 filed it
as a command after the owner asked for exactly this brief twice in one day).

This is a **read-only presentation command**: no `.gald3r/` writes, no status
changes, no task creation. Acting on the owner's answers afterwards routes
through the normal agents/verbs (`g-task-upd`, `gald3r bug resolve`,
DECISIONS.md via `g-infrastructure`, etc.).

## Sources to Scan (all deterministic; skip any that don't exist)

1. **`.gald3r/DECISIONS.md`** — any ruling row whose text contains
   `PENDING OWNER RATIFICATION`, `pending ratification`, or an explicitly
   unanswered question.
2. **Owner-gated tasks and bugs** — every open/pending task or bug whose
   frontmatter, Description, Note, or deferral text matches (case-insensitive):
   `owner-gated`, `owner ratification`, `needs owner`, `owner decision`,
   `maintainer decision`, `human review`, `supervised`, `GATED`, or names a
   decision the owner must make. Query the DB (`gald3r task ready --json`,
   `gald3r bug list --json`) and read only the matching records' files.
3. **The autopilot run-state marker** (`.gald3r/logs/ggo_run_state.json`) —
   `deferred_task_reasons` entries whose reason text matches the same markers.
4. **The newest shift-handover doc** (`docs/*SHIFT_HANDOVER*.md`, newest by
   filename timestamp) — its open-decision / "owner conversation" section, when
   one exists.
5. **Session knowledge** — decisions raised in the current conversation that are
   not yet filed anywhere (flag these `[unfiled]` so the owner knows they have
   no durable record yet).

Deduplicate across sources (the same decision often appears in 2-3 of them);
cite every ID it appears under.

## Output Format

Group by the owner's cost to answer, in this order:

```markdown
# 🗳️ Outstanding Owner Decisions — {date}

## 🔴 One-word confirmations (answer inline)
1. **{ID(s)} — {title}** — {1-2 sentence context}
   → Recommend: **{rec}**. Reply `1 yes` / `1 no`.

## 🟡 Decision bundles (a few minutes each)
2. **{ID(s)} — {title}**
   {2-4 sentence context; why it is stuck on the owner}
   Options: (a) {...} (b) {...} (c) {...}
   → Recommend: **{letter}** — {one-line why}. Reply `2a`/`2b`/...

## 🟢 Needs a scheduled session with you
3. **{ID} — {title}** — {what the session is and rough duration}

## 🔵 Needs a read first
4. **{ID} — {title}** — {the doc to read, then what to answer}
```

End with: `Answer in one reply, e.g.: "1 yes, 2a, 3 saturday, 4 later"` — and
after the owner answers, ACT on each answer through the proper agent/verb and
record ratifications in DECISIONS.md.

## Arguments

- *(none)* / `all` — the full stack (default)
- `quick` — only the 🔴 one-word group
- any other token — filter: only decisions whose title/context matches it
  (e.g. `/g-dec release`)

## Notes

- Never manufacture a decision: if a task is merely hard, it is not
  owner-gated. Only include items whose OWN text or ruling genuinely requires
  the owner.
- A compiled retrieval verb for this data is the natural follow-up once this
  command's shape settles — the same compiled-retrieval pattern `gald3r status`
  gives `g-status` (T494). No such verb exists yet; see T548.
