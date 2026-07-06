---
gald3r_rel_version: "3.0.0"
schema_version: "generic-v1"
---
# gald3r Vocabulary & Abbreviations

User-defined shorthand that all agents expand silently without prompting.
Format: `ABBR | Full Expansion | Usage Context`

Add entries with `@g-vocab-add "ABBR = expansion — context"` or edit this file directly.

---

## Active Vocabulary

| Abbreviation | Full Expansion | Context |
|---|---|---|
| `CRASH` | **C**ommands, **R**ules, **A**gents, **S**kills, **H**ooks — all contents of a platform folder (`.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`, `.copilot`, etc.) | gald3r platform folder structure |

---

## Command Group Conventions

gald3r commands follow the `g-{group}-{verb}` naming pattern. Related commands share a prefix for visual grouping:

| Group Prefix | Domain |
|---|---|
| `g-learn-*` | Session memory, learned facts, wrap-up, vocab |
| `g-task-*` | Task creation, updates, archival |
| `g-bug-*` | Bug reporting, fixing, archival |
| `g-wpac-*` | Cross-project coordination (parent/child/sibling) — WPAC protocol |
| `g-wrkspc-*` | Workspace-Control manifest operations |
| `g-feat-*` | Feature staging and promotion |
| `g-prd-*` | PRD governance lifecycle |
| `g-release-*` | Release management |
| `g-recon-*` | External content ingestion (URLs, repos, YouTube, files) |
| `g-res-*` | Research review and adoption |
| `g-subsystem-*` | Subsystem registry operations |
| `g-constraint-*` | Constraint add/update/deprecate |

---

## WPAC Vocab Scope

When this project is WPAC-linked (has `.gald3r/workspace/topology.md` with a declared parent):

- **Reading**: agents load this file first, then also load the parent's `.gald3r/vocab.md` for workspace-wide terms. Local entries take precedence over parent entries on collision.
- **Writing** (`@g-vocab-add`): saves to this local file. If the entry is workspace-wide (no project-specific context), the command also propagates it to the parent's `vocab.md`.
- **Unlinked projects**: only this file is used.

---

## Notes

- Abbreviations are **case-insensitive** and matched as whole words only
- Agents expand silently — no "you said CRASH, which means..." noise
- When a phrase appears 3+ times in a session, the agent may suggest an abbreviation
- Vocab entries are loaded at session start and included in `@g-learn-wrap-up` captures
