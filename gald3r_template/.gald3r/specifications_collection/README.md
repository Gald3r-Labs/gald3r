# Specifications Collection

Index of incoming requirement documents, PRDs, spec sheets, wireframes, contracts, and other
input documents provided to this project before or during development.

Agents: scan this directory at session start. If any spec is newer than the last completed task,
surface it as `⚠️ Unreviewed spec: {filename}`.

---

## Index

| File | Date Received | Source | Topic | Reviewed? |
|------|--------------|--------|-------|-----------|
| *(add entries here when new specs arrive)* | | | | |

---

## Naming Convention

Files should follow: `YYYY-MM-DD_{topic_slug}.md`

Examples:
- `2026-04-06_requirements_phase1.md`
- `2026-04-06_api_contract_v2.md`
- `2026-04-06_wireframes_checkout_flow.md`

For non-Markdown files (PDFs, images): add an entry to the index above and link to the file.

## Notes

- This directory is git-tracked — specs are version-controlled alongside tasks
- Agents do not modify spec files; they reference them during implementation
- When a spec is fully implemented, mark it `Reviewed? = yes` in the index above
