---
name: g-skl-learn
description: File-only continual learning — agents self-report insights to project and vault memory notes. No JSONL scanning, no schedulers, no SentinelOne risk.
token_budget: high
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---

# g-skl-learn — Continual Learning (File-Only)

## When to Use

- `/g-learn` at the end of any chat or agent session
- User says "remember this", "make a note", "this is important"
- After a long session to capture what the next agent should know
- Periodically to review and prune stale facts

## What This Does NOT Do (by design)

- **No JSONL scanning** — Cursor transcript files contain base64-encoded tool payloads;
  reading them triggers SentinelOne/Defender ATP scanners. This skill NEVER touches them.
- **No automatic triggers** during chat — no scheduler, no N-exchange hooks
- **No semantic dedup** via embeddings — plain text scan only
- **No base64 processing** of any kind

The logging for Cursor Agent mode is handled by `g-hk-agent-complete.py` (hook-based).
This skill covers **chat-mode sessions** where hooks don't fire.

## Memory Locations

| Scope | File | Use for |
|-------|------|---------|
| Project | `.gald3r/learned-facts.md` | Project-specific facts, decisions, gotchas |
| Global | `{vault_location}/projects/{project_name}/memory.md` | Cross-project user prefs, patterns, style |
| Agent role | `{platform}/agents/{slug}/journal/YYYY-MM-DD-{task-ref}-{slug}.md` | Durable learning specific to ONE agent role (T1010) |

When an insight is **specific to a single agent role** (e.g. "the code reviewer should always check X first"), write it to that agent's journal **in addition to** `learned-facts.md` — see the `CAPTURE_JOURNAL` operation. Project-wide facts go to `learned-facts.md` only.

## Operations

### CAPTURE_SESSION

Triggered by `/g-learn` (no args). Write a 3–5 item summary of the current session.

1. Read `.gald3r/.identity` to get `project_name` and `vault_location`
2. Read `.gald3r/learned-facts.md`
3. Draft 3–5 bullet points: what was done, key decisions, gotchas for next agent
4. **Dedup check**: scan existing facts for substance overlap — if a fact is already there,
   UPDATE the existing entry (update the date, refine the wording) rather than duplicating
5. Append new facts under the appropriate section heading
6. Optionally write to `{vault_location}/projects/{project_name}/memory.md` (ask user)

**Format**:
```
- [YYYY-MM-DD] {fact} (context: {task/session reference})
```

**Sections** (append to the most appropriate one):
- `## Architecture & Conventions`
- `## Recurring Preferences`
- `## Watch-Outs & Gotchas`

### CAPTURE_INSIGHT

Triggered by `/g-learn insight` or user saying "remember this" / "make a note".

Write ONE specific fact immediately. Same dedup check. Same format.
Do not wait for end of session — write now.

If the insight is **agent-role-specific** (it changes how one role should
work, not the project at large), ALSO run `CAPTURE_JOURNAL` for that role.

### CAPTURE_JOURNAL (agent-role-specific learning, T1010)

Triggered when an insight is durable but specific to ONE agent role rather
than the whole project — e.g. a reviewer anti-pattern, a task-manager
decision rule. Writes a per-agent journal entry **in addition to** the
`learned-facts.md` bullet (the journal is the role-specific store; it does
not replace project facts).

1. Resolve the active agent slug (e.g. `g-agnt-code-reviewer`).
2. Write `{platform}/agents/{slug}/journal/YYYY-MM-DD-{task-ref}-{slug}.md`
   with the frontmatter and 3–10 line body documented in
   `{platform}/agents/JOURNAL_FORMAT.md`
   (`date`, `agent`, `task_ref`, `category`, `tags`).
3. Use `category: anti-pattern` for mistakes-to-avoid — these are surfaced
   prominently at session start by `g-rl-25`.
4. Keep it concise — brevity is the discipline. One insight per entry.

Journal entries are plain markdown: git-tracked, Obsidian-readable, no DB.

### CAPTURE_VOCAB (user shorthand / abbreviations, T1279)

When the user defines a personal abbreviation/acronym/alias — explicitly (`--vocab`, "remember
the abbreviation…", "ABBR means…") or by intent (a line shaped `ABBR = expansion — context`) —
route it to `.gald3r/vocab.md` (the vocabulary source of truth), **not** `learned-facts.md`:

1. Parse `ABBR = expansion — context` (context optional).
2. Delegate to `@g-vocab-add` (append/update the `## Active Vocabulary` table; UPPERCASE the abbr).
3. Confirm `📖 Added: ABBR → expansion` and use the expansion silently for the rest of the session.

Vocab is loaded at session start by `g-rl-25` (the `📖 Vocab:` line) and recognized whole-word,
case-insensitively. `@g-vocab-list` / `@g-vocab-search` read it back. Keep vocab (compact shorthand)
distinct from `learned-facts.md` (project knowledge) and journals (per-agent-role learning).

### REVIEW

Triggered by `/g-learn review`.

1. Read `.gald3r/learned-facts.md`
2. Read `{vault_location}/projects/{project_name}/memory.md` if it exists
3. Display all facts to the user with dates
4. Ask: any facts to prune, correct, or promote to global vault?
5. If user says "(superseded)" or "remove this", move the entry to the
   `## Superseded Facts` section (append-only — never delete)

### GLOBAL_SYNC

Triggered by `/g-learn global`.

1. Show all project facts from `.gald3r/learned-facts.md`
2. Ask user: "Which facts should also go to your global vault?"
3. For selected facts, append to `{vault_location}/projects/{project_name}/memory.md`
   (create the file with a header if it doesn't exist)

### EVOLVE

Triggered by `/g-learn evolve`.

**Purpose:** Mine task failure trajectories from Status History FAIL rows, cluster recurring patterns, and propose new micro-rules or skill amendments for human review.

**No changes are made without explicit human approval.** This operation is analysis + proposal only.

**Steps:**

1. **Collect failure data** — scan all `.gald3r/tasks/task*.md` files:
   - Read each task's `## Status History` table
   - Extract rows where the `To` column is `pending` or `failed` AND `Message` starts with `FAIL:` or `PARTIAL_PASS`
   - Build a list of failure records: `{task_id, task_type, subsystems, failure_message, timestamp}`
   - Filter to tasks with **2+ failure rows** (single failures are noise)

2. **Extract failure signal** — for each failure record:
   - `failure_type` — classify: selector_stale, scope_blocked, ac_missing, file_not_found, parity_missing, test_fail, review_rejection, other
   - `error_pattern` — extract the core error phrase (strip task-specific details: file paths, IDs)
   - `subsystem` — from task frontmatter `subsystems:` field
   - `task_type` — from task frontmatter `type:` field (feature/bug_fix/refactor)

3. **Cluster similar failures** — group by `(failure_type, error_pattern_fingerprint)`:
   - Fingerprint: lowercase, strip numbers, strip file paths → first 60 chars
   - Minimum cluster size: 2 tasks (single-task patterns are not systemic)
   - Name each cluster by its dominant failure type and pattern

4. **Synthesize proposals** — for each cluster with ≥2 members, generate a proposed patch:
   - `type: rule` — if the pattern is an enforcement issue (e.g., "parity_missing 3× in skill tasks")
   - `type: skill_amendment` — if the pattern is a missing step in a skill (e.g., "scope_blocked before checking workspace_repos")
   - `type: preflight_check` — if the failure is consistently caught at review (e.g., "add pre-review check for X")
   - Draft the proposed rule/skill text (2–5 lines, specific and actionable)

5. **Write proposals to report file** — append to `.gald3r/reports/evolve_proposals.md`:
   ```markdown
   ## EVOLVE Report — {YYYY-MM-DD}

   ### Cluster: {failure_type}/{pattern_name} ({N} tasks: T{id1}, T{id2}, ...)
   - **Pattern**: {error_pattern}
   - **Proposed type**: {rule|skill_amendment|preflight_check}
   - **Proposed patch**:
     > {2-5 line proposal text}
   - **Originating tasks**: T{id1}, T{id2}
   - **Status**: ⏳ awaiting human review

   ---
   ```

6. **Present summary to user** — list clusters found, proposal types, and ask: "Review proposals? Type `@g-learn evolve --apply CLUSTER-N` to promote a proposal to the relevant skill/rule file."

**Apply an approved proposal (`/g-learn evolve --apply CLUSTER-N`):**
1. Read the cluster entry from `evolve_proposals.md`
2. Identify target: rule file (`.cursor/rules/`) or skill file (`.cursor/skills/`)
3. Append the proposal with provenance:
   ```
   <!-- EVOLVE[T{id1},T{id2}] 2026-05-09: {proposal text} -->
   ```
4. Update `evolve_proposals.md` entry: `Status: ✅ applied to {file} on {date}`
5. Add to `DECISIONS.md` (if it exists): one-liner record with originating task IDs

**Constraints:**
- Never modify a rule/skill without the explicit `--apply CLUSTER-N` invocation
- `[🚨]` (requires-user-attention) tasks are high-value candidates — surface them first
- Maximum 10 proposals per EVOLVE run (prevent noise from low-quality clusters)

## Session Integration

At end of `g-go-code` and `g-go-review` sessions, add this to the handoff block:

```
> Run /g-learn to capture session insights for the next agent.
```

## Vault Path for Global Memory

```
{vault_location}/
└── projects/
    └── {project_name}/
        └── memory.md   ← global memory note
```

Create the directory structure if it doesn't exist.

When **creating** `memory.md` for the first time, write it with YAML frontmatter:

```yaml
---
date: {YYYY-MM-DD}
type: session
ingestion_type: manual
title: "{project_name} — Project Memory"
project: {project_name}
tags: [session, memory]
---
```

Then append fact entries under section headings below the frontmatter.
Subsequent writes append to the body without modifying the frontmatter.

> **Obsidian Compatibility**: memory.md in the vault is indexed by Obsidian. Required frontmatter: `type: session`, `tags: [session, memory]`, `title:`, `date:`. See **VAULT_OBSIDIAN_STANDARD.md** for full spec.

### Decision records (continual learning → vault)

When promoting a **standalone decision / ADR** into the vault (not the bullet list in `learned-facts.md`), create `{vault_location}/projects/{project_name}/decisions/{slug}.md` with:

```yaml
---
date: {YYYY-MM-DD}
type: decision
ingestion_type: continual_learning
title: "ADR-NNN: Short title"
tags: [decision, architecture]
---

# {title}

## Context
{why the decision was needed}

## Decision
{what was chosen}

## Consequences
{tradeoffs, follow-ups}
```

Required: `type: decision` and category tag `decision` in `tags:` per **VAULT_OBSIDIAN_STANDARD.md**. Plain `.gald3r/learned-facts.md` bullets stay file-only (no YAML).
