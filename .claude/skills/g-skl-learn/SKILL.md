---
name: g-skl-learn
description: File-only continual learning — agents self-report insights to project and vault memory notes. No JSONL scanning, no schedulers, no SentinelOne risk.
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

The logging for Cursor Agent mode is handled by `g-hk-agent-complete.ps1` (hook-based).
This skill covers **chat-mode sessions** where hooks don't fire.

## Memory Locations

| Scope | File | Use for |
|-------|------|---------|
| Project | `.gald3r/learned-facts.md` | Project-specific facts, decisions, gotchas |
| Global | `{vault_location}/projects/{project_name}/memory.md` | Cross-project user prefs, patterns, style |

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
