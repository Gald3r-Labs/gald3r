---
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# Agent Journals — Format & Convention (T1010)

Each gald3r agent has a private, git-tracked journal at
`{platform}/agents/{slug}/journal/` for durable, **offline** cross-session
learning. Journals supplement `.gald3r/learned-facts.md` with
per-agent-role specificity. No Docker, no database — plain markdown.

## When entries are written

- **`g-go-code`** writes one entry after completing a task **iff** a novel
  pattern, decision rule, or anti-pattern was encountered (not every task).
- **`g-skl-learn`** writes here (in addition to `learned-facts.md`) when an
  insight is specific to one agent role rather than the whole project.
- Any session may write an entry explicitly.

## Entry filename

```
YYYY-MM-DD-{task-ref}-{slug}.md
```

e.g. `2026-05-20-T1010-g-agnt-code-reviewer.md`

## Entry frontmatter

```yaml
---
date: 2026-05-20
agent: g-agnt-code-reviewer
task_ref: T1010
category: anti-pattern   # anti-pattern | decision-rule | pattern | lesson
tags: [parity, gald3r_sys]
---
```

Body: **3–10 lines max.** Brevity is the discipline — capture the durable
insight, not a transcript.

## How entries are read

At session start (`g-rl-25`), the last 5 journal entries for the **active
agent role** are read and injected into the session context block. Entries
with `category: anti-pattern` are surfaced prominently so past mistakes are
not repeated.

## Categories

| Category | Use for |
|---|---|
| `anti-pattern` | A mistake to avoid; surfaced prominently at session start. |
| `decision-rule` | A reusable "if X then Y" rule discovered while working. |
| `pattern` | A reusable approach that worked well. |
| `lesson` | A general takeaway that does not fit the above. |

## Canonical source & deployment

Author journal scaffolding under `.claude/agents/{slug}/journal/`
(C-031 canonical source). `.cursor/agents/` and `.claude/agents/` mirror it.
Journal **content** is local agent learning and is not template content —
only the empty scaffolding (`.gitkeep` + this doc) ships.
