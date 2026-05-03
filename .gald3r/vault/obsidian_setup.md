# Obsidian Vault Setup Guide

This vault is designed to work as an Obsidian vault out of the box. No plugins required for basic browsing.

---

## Quick Setup

1. Open Obsidian
2. Click **Open folder as vault**
3. Select your `vault_location` folder (e.g. `G:\gald3r_ecosystem\gald3r_vault`)
4. Done — all notes are immediately browsable

---

## Folder Structure Tour

```
{vault_location}/
├── index.md                     ← Vault home page, start here
├── log.md                       ← Ingest operations log
├── obsidian_setup.md            ← This file
├── research/
│   ├── github/                  ← GitHub repo summaries
│   ├── platforms/               ← AI platform documentation
│   │   ├── cursor/
│   │   ├── claude-code/
│   │   ├── gemini/
│   │   └── opencode/
│   ├── articles/                ← One-time URL ingests
│   └── videos/                  ← YouTube transcript notes
├── knowledge/
│   ├── concepts/                ← Standalone concept pages
│   ├── entities/                ← People, companies, projects
│   └── comparisons/             ← Side-by-side comparisons
├── projects/
│   └── {project_name}/
│       ├── repos.txt            ← GitHub repos tracked for this project
│       ├── repo_tracker.json    ← Sync state
│       └── memory.md            ← Agent-captured cross-session facts
└── _index.yaml                  ← Machine-readable index (used by ingest scripts)
```

---

## Tags

Notes use `tags:` in YAML frontmatter — Obsidian indexes these natively in the Tags panel.

```yaml
tags: ["cursor", "agent-mode", "ide"]
```

Browse by tag in the **Tags** panel (left sidebar, looks like a hashtag icon).

**Old notes** may use `topics:` instead of `tags:`. These won't appear in the Tags panel until migrated.
To migrate: run `g-skl-vault/scripts/migrate_topics_to_tags.py` (see T039).

---

## Recommended Plugins (Optional)

| Plugin | What it adds |
|--------|-------------|
| **Dataview** | Query notes like a database: `TABLE tags FROM "research/"` |
| **Templater** | Auto-fill frontmatter for new notes |
| **Calendar** | Browse notes by date in a calendar view |

None of these are required. The vault works without any plugins.

---

## How `_index.yaml` Relates to Obsidian Search

`_index.yaml` is a machine-readable index used by gald3r ingest scripts to:
- Prevent duplicate ingests
- Track staleness for periodic refresh
- Speed up `@g-vault-search` commands

It is NOT used by Obsidian. Obsidian's own search indexes the same files independently.
Think of `_index.yaml` as the AI agent's card catalog, and Obsidian search as the library's full-text search.

---

## Wikilinks

Notes don't use `[[wikilinks]]` by default but Obsidian will resolve them if you add them manually.
The graph view becomes more useful as you add cross-references between notes.
Auto-generated `_INDEX.md` files (created by `scripts/gen_vault_moc.py`) provide hub-and-spoke
wikilinks for all platform doc directories — run `@g-vault-reindex` to regenerate them.

For the full compatibility standard: see **[[VAULT_OBSIDIAN_STANDARD]]**.

---

## Closing Obsidian During Bulk Operations

When running ingest scripts (`@g-ingest-docs`, `@g-ingest-url`, `migrate_topics_to_tags.py`, etc.),
close Obsidian or pause indexing to avoid file conflicts. Obsidian will re-index automatically on reopen.
