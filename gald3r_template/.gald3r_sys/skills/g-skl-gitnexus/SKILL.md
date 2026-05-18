---
name: g-skl-gitnexus
description: >
  DEPRECATED (T1158) — see g-skl-muninn. The codebase knowledge graph
  capability has moved from GitNexus (external, PolyForm Noncommercial,
  broken on Windows native) to gald3r_muninn (clean-room rewrite, owned
  in-tree). This skill is retained as a redirect for any agent or
  documentation still referencing the old name.
version: "1.1-deprecated"
status: deprecated
deprecated_by: g-skl-muninn
related_tasks: [T1147, T1158]
---

# g-skl-gitnexus — DEPRECATED, see g-skl-muninn

> **This skill has been superseded by `g-skl-muninn` as of T1158.**
> All new work should use the muninn `graph_*` MCP tools and the
> `scripts/graph_impact.ps1` PowerShell wrapper. This page is preserved
> only so agents that still recall the old name route to the new one.

## Why the migration

| Concern | GitNexus (old) | gald3r_muninn (new) |
|--------|----------------|---------------------|
| License | PolyForm Noncommercial 1.0.0 | gald3r-owned, MIT-compatible |
| Platform support | Crashes on Windows native (tree-sitter segfault) | Pure Python + Node.js indexers, cross-platform |
| Ownership | External upstream | In-tree at `docker/gald3r/tools/plugins/muninn/` |
| MCP server | Separate `npx gitnexus mcp` process | Auto-loaded into `gald3r_valhalla` |

## Tool name mapping

| Old gitnexus name | New muninn name |
|-------------------|-----------------|
| `gitnexus_blast_radius` | `graph_impact` |
| `gitnexus_query_callers` | `graph_callers` |
| `gitnexus_query_callees` | `graph_callees` |
| `gitnexus_query_imports` | `graph_deps` |
| `gitnexus_search_symbol` | `graph_search` |
| `gitnexus_status` | `graph_status` |
| `scripts/gitnexus_impact.ps1` | `scripts/graph_impact.ps1` |
| `.cursor/hooks/g-hk-gitnexus-update.ps1` | `.cursor/hooks/g-hk-graph-update.ps1` |

The deprecated `gitnexus_impact.ps1` automatically forwards to
`graph_impact.ps1` when the new script is present, so existing callers do
not break mid-migration.

## What to read instead

- `skills/g-skl-muninn/SKILL.md` — full reference for the new tooling.
- `.gald3r/subsystems/codebase-graph.md` — subsystem spec.
- `docker/gald3r/tools/plugins/muninn/SPEC.md` — MCP tool contracts.
- Task `T1147` (epic) and `T1158` (this migration) — design rationale.

## Removal timeline

This shim will be removed after one release cycle following T1158
verification. Until then it exists to catch stragglers; treat any new
usage as a parity bug to file against T1158.
