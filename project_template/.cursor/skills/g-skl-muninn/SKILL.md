---
name: g-skl-muninn
description: >
  gald3r_muninn MCP — query the local codebase knowledge graph for impact
  analysis, caller chains, dependencies, and symbol search. Clean-room
  rewrite (T1147 epic, T1153-T1158) of the GitNexus integration; auto-loaded
  by the example_app MCP server from docker/gald3r/tools/plugins/muninn/.
  Wire into g-go-code Step b0 Impact Scan before any implementation.
version: "1.0"
platforms: [cursor, claude, gemini, codex, opencode]
mcp_server: example_app
mcp_entry: ".mcp.json → gald3r_muninn entry (auto-loaded into example_app)"
related_tasks: [T1147, T1153, T1154, T1155, T1156, T1157, T1158, T921]
token_budget: medium
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---

# g-skl-muninn — Codebase Knowledge Graph via gald3r_muninn

## Why This Skill Exists

`gald3r_muninn` is the clean-room rewrite of the codebase-graph capability that
formerly used GitNexus. It indexes Python and TypeScript source into a local
SQLite graph store (`.gald3r/muninn/muninn.db` (per-project)) and exposes six MCP tools — agents
query the graph before editing to get architectural context in one MCP call
instead of many grep/read calls.

Key motivations for the rewrite (see T1147):
- GitNexus is PolyForm Noncommercial 1.0.0 — incompatible with gald3r's
  ecosystem.
- GitNexus 1.6.3 crashes on Windows native (`exit -1073741819`, tree-sitter
  native addon segfault) on some Python files.
- Owning the implementation lets gald3r control schema, language support,
  performance characteristics, and platform parity.

gald3r wires `graph_impact` into the **g-go-code Step b0 Impact Scan** so every
implementation task starts with graph-backed blast-radius analysis — not manual
estimates.

## MCP Configuration

`gald3r_muninn` is loaded as a plugin **inside** the `example_app` MCP
server. The `.mcp.json` entry documents the migration; the actual transport
is the existing example_app HTTP endpoint:

```json
"gald3r_muninn": {
  "_comment": "muninn graph_* tools auto-loaded by example_app",
  "type": "http",
  "url": "http://localhost:8090/mcp"
}
```

The plugin lives at `docker/gald3r/tools/plugins/muninn/` and is auto-discovered
by `docker/gald3r/plugin_loader.py`. Tool names: `graph_impact`,
`graph_callers`, `graph_callees`, `graph_deps`, `graph_status`, `graph_search`.

## First-Time Setup

The graph store needs to be populated before tools return useful data:

```powershell
# Python AST indexer (T1154)
python -m docker.gald3r.tools.plugins.muninn.indexers.python_indexer --root .

# TypeScript indexer (T1155) — requires Node.js
node docker/gald3r/tools/plugins/muninn/indexers/ts_indexer.js --root .
```

The store is created on first use at `.gald3r/muninn/muninn.db` (per-project) (override with
`MUNINN_DB_PATH`). Subsequent post-commit hooks refresh changed files only.

## Available MCP Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `graph_impact` | Files that transitively depend on the target file (importers + name-matched callers). Backs g-go-code Step b0. | "What breaks if I change this file?" |
| `graph_callers` | Functions that call the given symbol. | "Who calls X?" |
| `graph_callees` | Functions called by the given symbol. | "What does X call?" |
| `graph_deps` | Import dependency graph for a file. | "What does this module import?" |
| `graph_status` | Index freshness, file count, last-update timestamp. `stale: true` when index >24h old. | Verify the graph is current before relying on results. |
| `graph_search` | Symbol search (filename/function/class match). | "Find things named X" |

Tool contracts: see `docker/gald3r/tools/plugins/muninn/SPEC.md` §4. Error
envelope shape: `{error, message}` for `invalid_argument` /
`index_missing` / `internal_error`.

## IMPACT SCAN: g-go-code Step b0

Before implementing any task, run this sequence (via `.claude/skills/g-skl-muninn/scripts/graph_impact.ps1`
or a direct MCP call):

```
1. Identify target files from task's subsystems[] and workspace_repos[]
2. For each target file: graph_impact(file_path=<path>)
3. Parse response: { files: [{path, relation}], count, warning? }
4. If count > 3 transitively dependent files, add them to the context window
5. Use graph_callers(<key_functions>) to find what will break if signatures change
```

### Example: before editing `output_pipeline.py`

```jsonc
// graph_impact response
{
  "files": [
    {"path": "mcp_server.py", "relation": "imports"},
    {"path": "tests/fast/test_fast_output_pipeline.py", "relation": "imports"}
  ],
  "count": 2
}
```

### Blast-radius thresholds (advisory)

| Files affected | Risk | Action |
|---------------|------|--------|
| 0-3 | LOW | Proceed normally |
| 4-10 | MEDIUM | Note in Status History, extra test coverage |
| 11-25 | HIGH | Flag before claiming; get explicit confirmation |
| 26+ | CRITICAL | Must split task or get explicit scope authorization |

## PowerShell Wrapper

`.claude/skills/g-skl-muninn/scripts/graph_impact.ps1` is the PowerShell entry point used by Step b0 and
the post-commit hook. It:

1. Loads `docker/gald3r/tools/plugins/muninn/plugin.py` in-process via Python
   (no MCP server required for the local code path).
2. Falls back to the running example_app MCP server (`-Backend mcp`) when
   in-process Python is unavailable.
3. Falls back to ripgrep-based import scanning when neither is reachable
   (falls back to ripgrep import scanning when muninn is unavailable).

```powershell
.\scripts\graph_impact.ps1 -File "docker/gald3r/tools/plugins/search.py"
.\scripts\graph_impact.ps1 -File "src/lib/agentActivity/index.ts" -Json
.\scripts\graph_impact.ps1 -File "..." -Backend mcp
```

## Index Maintenance

The post-commit hook `.cursor/hooks/g-hk-graph-update.ps1` (parity copy in
`.claude/hooks/`) refreshes the index after each commit. Non-blocking: if
indexing fails or the muninn plugin is unavailable, the hook exits 0 and the
commit proceeds.

```bash
# Wire as a git post-commit hook (optional)
echo 'powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/g-hk-graph-update.ps1' > .git/hooks/post-commit
```

## Language Support

v1 (T1153-T1158): **Python** + **TypeScript / JavaScript**. Additional
languages (Rust, Go) are tracked under the T1147 epic follow-ups.

## PARITY NOTES

This skill lives in (canonical + IDE mirrors):
- `skills/g-skl-muninn/SKILL.md` (canonical)
- `.cursor/skills/g-skl-muninn/SKILL.md`
- `.claude/skills/g-skl-muninn/SKILL.md`
- `.agent/skills/g-skl-muninn/SKILL.md`
- `.codex/skills/g-skl-muninn/SKILL.md`
- `.opencode/skills/g-skl-muninn/SKILL.md`

MCP entry under key `"gald3r_muninn"` in `.mcp.json` documents the migration —
actual transport is the existing `example_app` HTTP endpoint.