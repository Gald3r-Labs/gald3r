# VAULT_SCHEMA

This file defines how agents maintain the gald3r vault.

## Purpose

The vault is a file-first knowledge system.

- Humans can browse it directly in Markdown or Obsidian
- Agents can use `_index.yaml` for exact routing and filtering
- `index.md` is the human home page
- `log.md` is the append-only operations record

## Root Files

- `VAULT_SCHEMA.md` - this contract
- `index.md` - human index
- `_index.yaml` - machine-readable catalog
- `log.md` - operation history

## Folder Routing

### Project-Scoped

- `projects/{project_name}/sessions/`
- `projects/{project_name}/decisions/`

### Source Notes

- `research/articles/`
- `research/github/`
- `research/harvests/`
- `research/papers/`
- `research/platforms/`
- `research/videos/`

### Compiled Wiki

- `knowledge/cards/`
- `knowledge/comparisons/`
- `knowledge/concepts/`
- `knowledge/entities/`

## Required Frontmatter

Every note must have:

- `date`
- `type`
- `ingestion_type`
- `source`
- `title`
- `tags`  ← **use `tags:` (not `topics:`)** — Obsidian's Tags panel indexes this field natively

> **Tagging Decision (2026-04-07, D021)**: The frontmatter key is `tags:` (array of strings).
> This enables native Obsidian tag indexing without any plugin. Old notes using `topics:` can
> be migrated via `migrate_topics_to_tags.py` (T039).

Example note header:
```yaml
---
date: 2026-04-07
type: platform_doc
ingestion_type: crawl
source: https://docs.cursor.com/
title: "Cursor Agent Mode Documentation"
tags: ["cursor", "agent-mode", "ide"]
---
```

## Obsidian Compatibility

This vault is designed to be opened directly in Obsidian:
- See `obsidian_setup.md` (at vault root) for the one-page setup guide
- Folder structure is meaningful and browser-friendly
- YAML frontmatter is Obsidian-compatible
- `tags:` field appears in Obsidian's Tags panel (left sidebar)
- No Obsidian-specific plugins required for basic browsing

Use the `Dataview` plugin (optional) to run queries against frontmatter fields.

Use `reference/vault_enums.md` from `g-skl-vault` as the canonical enum table.

## Ingest Workflow

### Quick Ingest

1. Resolve the active vault path
2. Choose the destination folder from `type`
3. Write the note with full frontmatter
4. Add obvious wikilinks
5. Append an operation to `log.md`
6. Rebuild `_index.yaml` and `index.md`

### Full Ingest

1. Do quick ingest
2. Extract entities, concepts, and comparisons
3. Create or update compiled pages
4. Backlink compiled pages to source notes
5. Append a log entry
6. Reindex

## Query Workflow

1. Read `index.md` for the human map
2. Read `_index.yaml` for precise routing
3. Open the relevant notes
4. Synthesize the answer
5. If the answer is durable, write it back as a compiled note

## Lint Workflow

Check:

- stale notes
- broken wikilinks
- orphan compiled pages
- missing entity pages
- missing concept pages
- duplicated or weak cards
- contradictions worth human review

Safe repairs may be applied immediately. Conflicts and contradictions should be surfaced.

## Wikilink Rules

- use vault-relative wikilinks
- prefer stable slugs
- avoid absolute host paths inside note bodies

Examples:

- `[[knowledge/entities/claude-code]]`
- `[[research/github/anthropics__claude-code]]`
- `[[projects/{project_name}/sessions/2026-04-06_abcd1234_session]]`

## GitHub Repo Rules

Raw mirrors live outside the vault in `repos_location`.

The vault only stores curated summaries in `research/github/`.

Tracked repo notes should contain:

- overview
- key details
- what the repo does
- why we track it
- related links
- update history

Do not dump raw upstream markdown into the vault.

## Migration-on-Detect

If `vault_location` points to a shared path and `.gald3r/vault/` still contains markdown notes:

- mark this as a migration candidate
- inform the user through hook context
- use `g-hk-vault-migrate.ps1` for the actual merge

## Guardrails

- Docker never reads or writes vault files directly
- the vault must work without MCP or database services
- `index.md` should stay readable
- `_index.yaml` should be regenerated, not hand-edited
- `log.md` should stay append-only
