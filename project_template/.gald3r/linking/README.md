---
gald3r_rel_version: "2.1.1"
schema_version: "generic-v1"
---
# Cross-Project Coordination (WPAC) — Linking Directory

This directory holds the file-first foundation for cross-project coordination (WPAC = Project Command And Control).

## Files In This Directory

| File | Purpose |
|------|---------|
| `link_topology.md` | This project's position in the ecosystem (parent, children, siblings) |
| `INBOX.md` | Lightweight **index** of incoming coordination items — conflicts, requests, broadcasts, syncs (one row per message) |
| `messages/msg_{id}_{type}_{source}.md` | One file per message: YAML frontmatter + full body |
| `messages/archive/` | Archived `[DONE]` messages + `archive_index.md` (moved here by `@g-wpac-archive-inbox`) |
| `peers/{project_name}.md` | Local copies of sibling topology files (advisory, non-blocking) |

---

## link_topology.md Schema

Each project has exactly one `link_topology.md`. Format:

```yaml
---
project_id: <uuid or slug>
project_name: <human name>
project_path: <absolute path on this machine>
role: parent | child | standalone
description: <one sentence>
parent:
  project_name: <name>
  project_path: <path>
  project_id: <id>
children:
  - project_name: <name>
    project_path: <path>
    project_id: <id>
siblings:
  - project_name: <name>
    project_path: <path>
    project_id: <id>
last_updated: <ISO date>
---
```

Body can contain free-form notes about the relationship (contracts, shared conventions).

---

## INBOX.md Format (index — T428)

`INBOX.md` is a lightweight index table (marked `<!-- WPAC-INDEX-V1 -->`). One row
per message; message bodies live in `messages/`:

```markdown
<!-- WPAC-INDEX-V1 -->
# INBOX — {project_name}

| Status | ID | Type | Source | Subject | Age | File |
|---|---|---|---|---|---|---|
| [DONE] | msg-001 | INFO | gald3r_dev | Project spawned | 7d | [msg_001_info_gald3r_dev.md](messages/msg_001_info_gald3r_dev.md) |
```

Each message file under `messages/` carries YAML frontmatter:

```markdown
---
id: msg-001
type: INFO
source_project: gald3r_dev
subject: 'Project spawned from gald3r_dev'
status: done
created_at: '2026-05-23'
actioned_at: '2026-05-23'
---

# [INFO] Project spawned from gald3r_dev
... full body ...
```

**Migration:** a legacy flat `INBOX.md` (inline `## [STATUS] ... ` bodies) is
auto-migrated to this layout on demand by `gald3r_wpac_inbox.ps1 -Migrate` (or its
`.py` twin), idempotently. **Archiving:** `@g-wpac-archive-inbox` moves `[DONE]`
messages older than a threshold (default 30 days) to `messages/archive/` and prunes
their index rows. The session-start inbox check prompts to archive when the active
index exceeds 50 `[DONE]` rows.

---

## Workflow Overview

| Skill | Trigger | What It Does |
|-------|---------|-------------|
| `g-skl-wpac-order` | Parent project | Pushes a task to one or more children |
| `g-skl-wpac-ask` | Child project | Writes to parent's INBOX + marks local task blocked |
| `g-skl-wpac-sync` | Either sibling | Updates local copy of peer topology file |
| `g-skl-wpac-read` | Any project | Reviews and actions all INBOX items |
| `g-skl-wpac-move` | Any project | Transfers files/folders to another project |

`g-hk-wpac-inbox-check.ps1` runs at every session start and surfaces CONFLICT items before any other work.

---

## Tracking Decisions

- `linking/` contents are **source-controlled** (config, not secrets)
- `peers/` files are local advisory copies — update them via `g-skl-wpac-sync`
- INBOX.md items are never auto-deleted; archive resolved items under a `## [RESOLVED]` section
