# Cross-Project Coordination (PCAC) — Linking Directory

This directory holds the file-first foundation for cross-project coordination (PCAC = Project Command And Control).

## Files In This Directory

| File | Purpose |
|------|---------|
| `link_topology.md` | This project's position in the ecosystem (parent, children, siblings) |
| `INBOX.md` | Incoming project-linking-and-coordination items — conflicts, requests, broadcasts, syncs |
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

## INBOX.md Format

```markdown
# INBOX — {project_name}

## [CONFLICT] — Items That Block Work
<!-- Surfaced by g-hk-pcac-inbox-check.ps1 at session start — must resolve before any other work -->

## [REQUEST] — Incoming Asks From Children
<!-- Child projects asking this project to take action -->

## [BROADCAST] — Orders From Parent
<!-- Tasks pushed down from parent via g-skl-pcac-order -->

## [SYNC] — Peer Contract Updates From Siblings
<!-- Advisory topology/contract updates from sibling projects -->
```

Each item uses a one-line `- [ ] YYYY-MM-DD | {from_project} | {summary}` format.

---

## Workflow Overview

| Skill | Trigger | What It Does |
|-------|---------|-------------|
| `g-skl-pcac-order` | Parent project | Pushes a task to one or more children |
| `g-skl-pcac-ask` | Child project | Writes to parent's INBOX + marks local task blocked |
| `g-skl-pcac-sync` | Either sibling | Updates local copy of peer topology file |
| `g-skl-pcac-read` | Any project | Reviews and actions all INBOX items |
| `g-skl-pcac-move` | Any project | Transfers files/folders to another project |

`g-hk-pcac-inbox-check.ps1` runs at every session start and surfaces CONFLICT items before any other work.

---

## Tracking Decisions

- `linking/` contents are **source-controlled** (config, not secrets)
- `peers/` files are local advisory copies — update them via `g-skl-pcac-sync`
- INBOX.md items are never auto-deleted; archive resolved items under a `## [RESOLVED]` section
