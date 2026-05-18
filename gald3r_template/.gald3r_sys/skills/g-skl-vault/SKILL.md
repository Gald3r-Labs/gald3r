---
name: g-skl-vault
description: Own and manage the file-first vault plus repo mirror metadata. Obsidian-compatible notes, wiki compilation, path resolution, reindexing, linting, and GitHub repo summaries.
---
# g-vault

**Files Owned**: `.gald3r/.identity` vault fields, `.gald3r/vault/`, `{vault_location}/projects/{project_name}/repos.txt`, `{vault_location}/projects/{project_name}/repo_tracker.json` (falls back to `.gald3r/repos.txt` / `.gald3r/repo_tracker.json` when no vault_location)

**Activate for**: "vault", "knowledge vault", "obsidian", "wiki", "knowledge card", "research note", "index the vault", "repo summary", "github repo tracking".

---

## Purpose

The gald3r vault is a file-first knowledge system that works in plain Markdown and opens cleanly in Obsidian.

It has two layers:

1. **Source notes** in `research/` and `projects/{project_name}/`
2. **Compiled wiki pages** in `knowledge/`

The vault is human-readable first:

- `index.md` is the Obsidian home page
- `_index.yaml` is the machine-readable catalog
- `log.md` is the chronological operations log
- `VAULT_SCHEMA.md` is the maintenance contract for agents

Raw GitHub repo downloads never enter the vault tree. They live under `repos_location` and only produce curated summary notes in `research/github/`.

---

## Path Resolution

### Vault Path

Read `vault_location=` from `.gald3r/.identity`.

- `{LOCAL}` or blank: use `.gald3r/vault/`
- absolute path: use the shared vault path
- missing in `.identity`: fallback to `.env` `GALD3R_VAULT_LOCATION=`

### Repos Path

Read `repos_location=` from `.gald3r/.identity`.

- `{LOCAL}` or blank: use `.gald3r/repos/`
- absolute path: use that raw repo mirror path
- missing in `.identity`: fallback to `.env` `GALD3R_REPOS_LOCATION=`

### Write Rules

- If `vault_location` resolves and is writable, write to that vault path only
- If the resolved vault path is unavailable, write to `.gald3r/vault/` as a local fallback
- If a shared vault is configured and `.gald3r/vault/` contains notes, treat that as a migration candidate

Do **not** dual-write the vault permanently.

---

## Vault Layout

```text
{vault}/
  _index.yaml
  index.md
  log.md
  VAULT_SCHEMA.md
  projects/
    {project_name}/
      sessions/
      decisions/
  research/
    articles/
    github/
    harvests/
    papers/
    platforms/
    videos/
  knowledge/
    cards/
    comparisons/
    concepts/
    entities/
```

### Obsidian Rules

- Use normal Markdown plus YAML frontmatter
- Use wikilinks for cross-references: `[[knowledge/entities/claude-code]]`
- Keep `index.md` readable by humans, not just agents
- Never place raw repo mirrors inside the vault tree

---

## Required Frontmatter

Every vault note needs:

- `date`
- `type`
- `ingestion_type`
- `source`
- `title`
- `tags` (Obsidian-native; use `tags:` not `topics:`)

Optional fields:

- `project_id`
- `refresh_policy`
- `refresh_after`
- `expires_after`
- `source_volatility`
- `source_notes`
- `last_compiled`
- `last_synced`
- `last_version`

See `reference/vault_enums.md` for valid values and folder mappings.

---

## Core Operations

## 1. Quick Ingest

Use when the user wants a note stored but does not need compiled wiki updates yet.

1. Resolve the vault path
2. Choose the destination folder from `type`
3. Write the source note with full frontmatter
4. Add relevant wikilinks when obvious
5. Append a log entry
6. Run `g-hk-vault-reindex.ps1`

## 2. Full Ingest

Use when the user wants the note to compound into the wiki.

1. Perform quick ingest
2. Extract entities, concepts, and comparisons from the source
3. Create or update pages in:
   - `knowledge/entities/`
   - `knowledge/concepts/`
   - `knowledge/comparisons/`
   - `knowledge/cards/`
4. Add backlinks from compiled pages to the source note
5. Add related-page wikilinks between compiled pages
6. Append a log entry with all touched files
7. Reindex

If the source is too small or low-value, prefer quick ingest.

## 3. Query

When answering from the vault:

1. Read `index.md` for the human map
2. Read `_index.yaml` for exact file paths and metadata filters
3. Open the relevant notes
4. Synthesize the answer
5. If useful, write the answer back as a knowledge card or comparison note

## 4. Lint

Structural lint checks for:

- orphan wiki pages
- broken wikilinks
- stale notes
- missing entity pages
- missing concept pages
- duplicated or weak cards
- contradictions worth human review

Log lint passes in `log.md`.

---

## Note Types

### Source Notes

- `article`
- `paper`
- `platform_doc`
- `video` / `video_analysis` (prefer `video` for new notes — see VAULT standard)
- `harvest`
- `github` (curated repo summaries in `research/github/`)
- `session`
- `decision`

### Compiled Wiki Notes

- `entity`
- `concept`
- `comparison`
- `knowledge_card`
- `correction`
- `preference`

---

## GitHub Repo Summaries

Raw repo mirrors live under `repos_location`, not inside the vault.

The vault only stores curated notes in `research/github/`.

### Repo Profile Template

```yaml
---
date: 2026-04-06
type: github_repo
ingestion_type: github_sync
source: https://github.com/owner/repo
title: "owner/repo"
topics: [github, tooling]
refresh_policy: weekly
source_volatility: medium
last_version: v1.2.3
last_synced: 2026-04-06T12:00:00Z
---
```

Body sections:

- `## Overview`
- `## Key Details`
- `## What This Repo Does`
- `## Why We Track It`
- `## Related`
- `## Update History`

### Repo Update Entry

Append to the existing note:

```markdown
## Update: v1.2.4 (2026-04-06)

- Previous: v1.2.3
- Changes: ...
- Impact: ...
```

Do not dump entire READMEs or upstream docs into the vault unless the user explicitly asks for a curated excerpt.

---

## `index.md`

`index.md` is the vault landing page for humans and Obsidian.

It should include:

- a short intro
- counts by note type
- recent updates
- grouped links by folder/type
- high-value knowledge cards

Keep it readable. It is not a raw YAML dump.

---

## `_index.yaml`

`_index.yaml` is the machine-readable catalog.

Each entry should include at least:

- `path`
- `title`
- `type`
- `ingestion_type`
- `date`
- `topics`
- `source`
- `project_id`

Optional fields:

- `refresh_policy`
- `refresh_after`
- `expires_after`
- `last_version`
- `last_synced`

Do not hand-edit `_index.yaml`. Regenerate it.

---

## `log.md`

`log.md` is append-only.

Each operation uses this heading format:

```markdown
## 2026-04-06 14:32 UTC | ingest | research/articles/2026-04-06_obsidian_wiki.md
```

Supported operation labels:

- `ingest`
- `compile`
- `lint`
- `refresh`
- `migrate`
- `repo-sync`

Each entry should capture:

- files written or updated
- why the operation happened
- any unresolved issues or conflicts

Keep entries terse and parseable.

---

## Migration-on-Detect

If a shared `vault_location` is configured and `.gald3r/vault/` contains notes, do not silently move them.

Treat this as a migration candidate and surface:

- what local files exist
- what shared path is configured
- whether the shared path is writable
- whether migration is recommended

Use `g-hk-vault-migrate.ps1` for actual migration.

Typical scenarios:

- first move from local to shared
- offline fallback notes created while the shared path was down
- copied project with inherited path settings
- changed shared path

---

## Obsidian standard (see also)

Curated vault output must follow **`VAULT_OBSIDIAN_STANDARD.md`** (shipped next to the vault or under `.gald3r/vault/`): required frontmatter, `tags:` taxonomy, hub MOC files via `scripts/gen_vault_moc.py`, UTF-8 without BOM. Repo summaries use `type: github` and `tags: [github, …]` from `scripts/github_sync.py`.

---

## Guardrails

- Docker never reads or writes vault files directly
- Do not require MCP for core vault use
- Do not store raw repo mirrors in the vault
- Prefer quick ingest unless full compilation adds real value
- Keep wikilinks relative and stable
- Preserve human readability first, agent convenience second
