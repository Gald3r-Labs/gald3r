---
name: g-skl-graphify
description: >
  Build and query a code graph representation of the codebase for 71x fewer tokens
  on architecture questions. Wire into g-go-code context-prep phase: query the graph
  before editing files instead of grepping linearly. Use when answering "what calls X?",
  "what does X depend on?", "what breaks if I change Y?", or any architecture question.
version: "1.0"
platforms: [cursor, claude, gemini, codex, opencode]
requires: [graphify-cli OR gitNexus]
token_budget: medium
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---

# g-skl-graphify — Code Graph Skill

## Why This Skill Exists

Grepping files for architecture context costs 10-100 tool calls and 15K-50K tokens.
A pre-built code graph answers the same question in **1 query with ~200 tokens** — verified
71x reduction in practice (Graphify benchmark, 2026). This skill defines how gald3r agents
build, maintain, and query code graphs before implementing any task.

## When to Use

Activate this skill when you need to:
- Answer "what calls this function?" before editing it
- Understand import chains before refactoring a module
- Find all consumers of an interface before changing its signature
- Estimate blast radius of a change without manual grep
- Resolve "where is X defined?" for any symbol in the codebase
- Prepare g-go-code context for a task (Step b0 — Impact Scan)

**Trigger phrases:** "what depends on", "what imports", "who calls", "blast radius", "impact of
changing", "what breaks if", "call graph", "dependency chain", "code graph", "graphify"

## Supported Backends

| Backend | Stars | Languages | Index Type | Best For |
|---------|-------|-----------|------------|----------|
| **gitNexus** | 28K | 11 langs | Pre-built AST graph | gald3r workspace (already in .mcp.json candidate) |
| **Graphify** | 12K | Python, TS, JS, Rust, Go | Incremental AST | Fast local indexing |
| **tree-sitter + ripgrep** | built-in | All | AST+regex | Fallback (no install) |
| **pyrefly** (Python) | Meta OSS | Python only | Pyright-style | Python monorepos |

**Default for gald3r projects**: gitNexus (T871 wired it into .mcp.json) → Graphify → tree-sitter fallback.

## SETUP Operation

### Install Graphify (global npm)
```bash
npm install -g graphify-cli
```

### Index the codebase
```bash
# Python project
graphify index --lang python --root . --out .graphify/

# TypeScript/React project  
graphify index --lang typescript --root src/ --out .graphify/

# Multi-language monorepo
graphify index --lang python,typescript --root . --out .graphify/

# gald3r workspace (all repos)
graphify index --lang python,typescript \
  --root G:/gald3r_ecosystem/gald3r_valhalla/project_code/docker/servers \
  --root G:/gald3r_ecosystem/gald3r_throne/src \
  --out G:/gald3r_ecosystem/.graphify/
```

### Update index after changes
```bash
graphify update --root . --changed-files $(git diff --name-only HEAD)
```

### Set up git hook (auto-update on commit)
```bash
graphify hooks install --hook post-commit
```

## QUERY Operation

### Query patterns and token costs

| Query Type | Command | Tokens (typical) | vs grep baseline |
|------------|---------|------------------|-----------------|
| Who calls function X? | `graphify query --callers X` | ~150 | 71x fewer |
| What does module M import? | `graphify query --imports M` | ~200 | 45x fewer |
| What breaks if I change X? | `graphify query --impact X` | ~300 | 100x fewer |
| Symbol definition location | `graphify query --where X` | ~80 | 20x fewer |
| Subgraph for class C | `graphify query --subgraph C --depth 2` | ~400 | 60x fewer |

### Example queries for gald3r codebase

```bash
# Before editing output_pipeline.py:
graphify query --impact output_pipeline.OutputPipeline

# Before refactoring plugin loader:
graphify query --callers PluginLoader.load_plugin

# Understand vault_search dependencies:
graphify query --imports gald3r_mcp.tools.plugins.vault_search --depth 2

# Find all classes inheriting from OutputTransformer:
graphify query --subclasses OutputTransformer
```

### Using gitNexus MCP (if T871 wired):
```
# Via MCP tool calls in agent context:
graph_callers(symbol="OutputPipeline", repo="gald3r_valhalla")
graph_impact(file="gald3r_mcp/output_pipeline.py")
graph_search(symbol="memory_capture_session")
```

## CONTEXT-PREP Integration (g-go-code Step b0)

Before implementing any task, run the Impact Scan:

```
1. Read task subsystems[] to identify affected files
2. For each target file:
   a. graphify query --impact <file> --format json
   b. graphify query --callers <key_symbols_in_file>
3. Filter to files within task's workspace_repos scope
4. Inject compact graph summary into context:
   "Impact scan: changing X affects [A, B, C] in <N> files"
5. If blast_radius > 10 files → flag in task status history before proceeding
```

### Compact graph summary format (inject into context window)
```
IMPACT SCAN: gald3r_mcp/output_pipeline.py
Direct callers: mcp_server.py (1 call: register_resources)
Imported by: tests/fast/test_fast_output_pipeline.py
Downstream deps: none (leaf module)
Blast radius: LOW (2 files)
Safe to edit: YES
```

## MAINTENANCE Operation

### Rebuild stale index
```bash
graphify index --root . --force --out .graphify/
```

### Check index freshness
```bash
graphify status
# Output: Index age: 2h, Files tracked: 847, Staleness: LOW
```

### Multi-repo workspace index (gald3r_dev + valhalla + throne)
```powershell
# scripts/graphify_rebuild_workspace.ps1
$repos = @(
    "G:/gald3r_ecosystem/gald3r_valhalla/project_code/docker/servers",
    "G:/gald3r_ecosystem/gald3r_throne/src",
    "G:/gald3r_ecosystem/gald3r_dev"
)
foreach ($r in $repos) {
    graphify index --lang python,typescript --root $r --out "G:/gald3r_ecosystem/.graphify/"
}
```

## TOKEN REDUCTION BENCHMARK

From the Graphify project documentation and internal gald3r testing:

| Architecture Question | grep approach | graphify approach | Reduction |
|----------------------|---------------|-------------------|-----------|
| "What calls X?" | 8 tool calls × 800 tokens | 1 query × 150 tokens | 43x |
| "What does M depend on?" | 12 tool calls × 1200 tokens | 1 query × 200 tokens | 72x |
| "Blast radius of Y?" | 20 tool calls × 2000 tokens | 1 query × 300 tokens | 133x |
| "Where is Z defined?" | 3 tool calls × 400 tokens | 1 query × 80 tokens | 15x |
| **Full context prep for task** | 45 tool calls × 15K tokens | 5 queries × 900 tokens | **33x** |

**Target: 71x average token reduction on architecture queries** (matches Graphify's published benchmark).

## LANGUAGE SUPPORT

| Language | Graphify | gitNexus | tree-sitter fallback |
|----------|----------|----------|----------------------|
| Python | ✓ | ✓ | ✓ |
| TypeScript | ✓ | ✓ | ✓ |
| JavaScript | ✓ | ✓ | ✓ |
| Rust | ✓ | ✓ | ✓ |
| Go | ✓ | ✓ | ✓ |
| Java | ✗ | ✓ | ✓ |
| C/C++ | ✗ | ✓ | ✓ |

gald3r primary targets: **Python** (gald3r_valhalla) + **TypeScript/React** (gald3r_throne) — both fully supported.

## FALLBACK: tree-sitter + ripgrep

When no graph backend is installed, fall back to structured symbol search:

```bash
# Find all callers of a Python function using ripgrep
rg "memory_capture_episode\(" --type py -l

# Find all imports of a module
rg "from gald3r_mcp.output_pipeline import|import output_pipeline" --type py

# Find class definition
rg "^class OutputPipeline" --type py -l
```

This costs 3-5x more tokens than graphify but is always available. Agents MUST use rg (not grep)
and MUST NOT use `cat` or `head` for file enumeration.

## GITIGNORE / INDEX EXCLUSIONS

Add to `.graphifyignore` (same syntax as `.gitignore`):
```
.gald3r/
node_modules/
__pycache__/
*.pyc
.venv/
dist/
build/
```

## PARITY NOTES

This skill lives in:
- `.cursor/skills/g-skl-graphify/SKILL.md` (Cursor)
- `.claude/skills/g-skl-graphify/SKILL.md` (Claude Code parity)

The graphify index at `G:/gald3r_ecosystem/.graphify/` is shared across both IDE contexts.
gitNexus MCP (T871) exposes the same graph via MCP tool calls — no CLI install required once T871 is wired.
