---
name: g-skl-knowledge-refresh
description: Audit vault freshness and structure. Check stale notes, rebuild compiled pages, detect broken links, missing pages, and contradictions worth review.
---
# g-knowledge-refresh

Use this skill to keep the vault healthy over time.

It extends classic freshness checks with structural lint for the Obsidian-compatible wiki layer.

---

## When to Use

- user asks to refresh the vault
- user asks to rebuild knowledge cards
- user asks to check stale notes
- user asks for vault lint or health
- after major source ingestion
- during maintenance reviews

---

## Inputs

Read these first:

1. `index.md`
2. `_index.yaml`
3. `log.md`
4. `VAULT_SCHEMA.md`

Then open the notes that are actually implicated by the audit.

---

## Audit Modes

## 1. Freshness Audit

Check:

- notes with `refresh_after` in the past
- notes with `expires_after` in the past
- notes whose `refresh_policy` cadence has elapsed
- high-volatility notes older than their expected review window

Suggested actions:

- refresh source note
- rebuild dependent knowledge cards
- mark as stale pending review
- do nothing if source is stable and still useful

## 2. Structural Lint

Check:

- broken wikilinks
- orphan compiled pages with no incoming or outgoing useful links
- missing entity pages for repeated names across source notes
- missing concept pages for repeated patterns across source notes
- comparison opportunities where similar tools or ideas recur
- duplicate cards that should be merged

## 3. Contradiction Review

Flag, do not silently resolve:

- source notes that disagree on facts
- compiled pages whose summaries conflict with their cited sources
- stale cards masking newer evidence

The output should distinguish:

- `safe_to_fix_now`
- `needs_user_review`

---

## Knowledge Card Rebuild Rules

Rebuild a card when:

- 3+ relevant source notes exist and no card covers them
- any `source_notes` entry changed since `last_compiled`
- the user asks for consolidation
- a lint pass finds duplicate or weak cards

When rebuilding:

1. open every source note in `source_notes`
2. update summary, key facts, and related links
3. preserve stable wikilinks where possible
4. update `last_compiled`
5. update `date` if the rewrite is substantial
6. append a `refresh` or `compile` entry to `log.md`

---

## Broken Link Policy

For each broken link:

1. check whether the target was renamed
2. check whether the target should exist but was never created
3. either repair the link or note the missing target in the lint report

Do not invent missing content unless the user asked for a rebuild or full lint repair.

---

## Missing Entity / Concept Detection

Suggest an entity or concept page when the same item appears in multiple source notes and is central to the topic.

Heuristics:

- entity mentioned in 3+ notes
- concept appears in 3+ titles, summaries, or topic lists
- comparison requested by repeated adjacent entities or concepts

Suggested outputs:

- `knowledge/entities/{slug}.md`
- `knowledge/concepts/{slug}.md`
- `knowledge/comparisons/{slug}.md`

---

## Lint Report Format

```markdown
# Vault Health Report

## Freshness
- stale: 2
- due soon: 4

## Broken Links
- [[knowledge/entities/foo]] in knowledge/cards/bar.md

## Missing Pages
- entity: claude-code
- concept: compiled-wiki

## Contradictions
- research/articles/a.md vs research/articles/b.md on repo update policy

## Recommended Actions
1. rebuild knowledge/cards/obsidian-memory.md
2. create knowledge/entities/claude-code.md
3. repair broken wikilink in knowledge/cards/bar.md
```

Keep the report actionable. Separate safe fixes from decisions that need the user.

---

## `log.md` Entries

Use:

- `refresh` for source-note updates
- `compile` for rebuilt compiled pages
- `lint` for audits

Heading format:

```markdown
## 2026-04-06 15:10 UTC | lint | vault
```

Capture:

- what was checked
- what was changed
- what still needs review

---

## Guardrails

- do not require Docker or MCP
- prefer file reads and reindexing only
- do not rewrite source notes unless the refresh actually changes content
- do not hide contradictions; surface them
- compiled pages should stay human-readable and source-backed
