---
project_id: "{project_id}"
project_name: "{project_name}"
project_path: "{project_path}"
role: "child"
description: "{One sentence describing what this project does.}"
parent:
  project_name: "{parent_project_name}"
  project_path: "{parent_project_path}"
  project_id: "{parent_project_id}"
children: []
siblings: []
last_updated: "{YYYY-MM-DD}"
---

# Topology — {project_name}

## Ecosystem Role

This project is a **child** of `{parent_project_name}`. Update `role` to `parent`, `child`, `standalone`, or `sibling-only` as appropriate.

## Relationship Notes

*(Document any contracts, shared conventions, or important coordination notes with linked projects here.)*

## Inbox Location

`{project_path}/.gald3r/linking/INBOX.md`

## Peer Copies

Sibling topology copies live in `peers/{sibling_name}.md`. Keep them fresh with `@g-pcac-sync`.
