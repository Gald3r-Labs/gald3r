# gald3r-engine

The Python engine for gald3r — a **file-first agent OS** that the existing IDE
harnesses (Claude Code, Cursor, OpenCode, …) plug into. **Mode A:** a pure,
deterministic core that reads/writes the existing `.gald3r/` markdown formats and
makes **no LLM calls**. One core, exposed through a CLI today and an MCP server
(the 34-platform unlock); an HTTP backend and a Mode-B harness reuse the same core later.

**12 file-backed systems** are built on this core — the 9 simple state systems
(tasks, goals, bugs, features, prds, ideas, vocab, constraints, subsystems) plus the
3 larger ones (vault, release, workspace). A **prompt/judgment layer**
(`src/gald3r/prompts/`) holds the reusable LLM reasoning that *can't* be code — persona,
role briefs, review rubrics, playbooks — served (never executed) via `Gald3r.prompts`,
`gald3r prompt`, and MCP. See `SYSTEMS.md` for the full coverage map and the explicit
scope boundary (what is *not* a clone of this pattern, and why).

## Quickstart (uv — no system Python required)

```bash
# 1. install uv once (no Python needed):
#    Windows:  irm https://astral.sh/uv/install.ps1 | iex
#    mac/linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. provision Python + deps + venv automatically:
uv sync                 # uv fetches the pinned Python (.python-version) if missing
uv run pytest -q        # run the test suite
uv run gald3r --version
```

## CLI

```bash
uv run gald3r task new --title "Wire up the auth flow" --type feature --priority high
uv run gald3r task list
uv run gald3r task sync          # regenerate TASKS.md from the task files
# the larger systems:
uv run gald3r vault ingest --title "Cursor agent docs" --type platform_doc \
              --source https://docs.cursor.com --tags "cursor,ide"
uv run gald3r vault reindex      # regenerate _index.yaml + index.md from note frontmatter
uv run gald3r release new --title "Spring cut" --version 1.0.0 --target-date 2026-07-01
uv run gald3r release ship R-001 --version 1.0.1   # terminal + frozen
uv run gald3r workspace status   # controller-tier; refused below that tier
uv run gald3r mcp                # MCP (stdio) server — 35 tools  (needs the `mcp` extra)
```

(Plus `goal`, `bug`, `vault list|lint`, `release list|roadmap`, `workspace validate|conflicts|inbox-add`.)
All operate on the nearest `.gald3r/` (walk-up discovery), reading and writing the **same**
markdown files the IDE-driven flow uses — so the engine and the markdown flow are interchangeable.

## Layout

```
src/gald3r/
  config.py     # project discovery + tier resolution (.gald3r/.identity)
  store.py      # ALL .gald3r/ I/O (frontmatter parse/emit, LF, BOM-safe)
  schema/task.py# canonical status vocabulary + status→folder/marker + validation
  systems/_base.py  # FolderSystem — the cloned pattern (bugs/features/prds/release)
  systems/_table.py # single-file markdown-table helper (ideas/vocab/constraints)
  systems/*.py      # the 12 systems (tasks, goals, …, vault, release, workspace)
  core.py       # Gald3r facade (the single entry object; workspace is controller-gated)
  adapters/cli.py   # `gald3r ...`
  adapters/mcp.py   # 35 MCP tools over the same core
tests/          # pytest — 65 tests (state machines + on-disk parity + MCP)
```

## Design rules (so Mode A never blocks Mode B / the backend)
- The core (`store`, `schema`, `systems`) makes **no LLM calls** and assumes nothing
  about its caller. LLM work lives only in the future `pipeline/` (Mode-B harness).
- `.gald3r/` files stay the **source of truth**; the engine is the validated way to
  touch them, never a replacement for them.
- Everything is **tier-gated** (`slim < full < controller`; `maintainer` = dev-only)
  via `.gald3r/.identity`.

See `../strategy/GALD3R_PYTHON_CENTRALIZATION.md` and `../strategy/COMPONENT_REGISTRY.md`.
