# gald3r v2.0.0 — The Engine Release

**Date:** 2026-06-04

gald3r 2.0 adds a bundled, file-first **Python engine** that backs every system
deterministically — while keeping everything plain markdown on disk. The engine is **additive**:
existing installs keep working, and every slimmed component ships a no-engine fallback.

## Headline

- **Bundled gald3r engine** (`.gald3r_sys/engine/`) — pure Mode-A state backend for tasks, bugs,
  features, goals, prds, ideas, vocab, constraints, subsystems, vault, release, workspace, inbox.
  No LLM, no network, no Docker. One prerequisite: [`uv`](https://docs.astral.sh/uv/).
- **`gald3r` CLI + MCP server** — drive every system from the shell or via ~20 MCP tools
  (`gald3r task new`, `gald3r bug new`, `gald3r vault ingest`, `gald3r prompt get …`).
- **`gald3r doctor`** — read-only health check + CI gate (`--fail-below`).
- **Five maintenance scripts absorbed** into engine verbs (`inbox`, `doctor`, `platform status`,
  `tier`, `sync`/`parity`), each keeping its `.ps1` as a no-engine fallback.
- **Judgment/prompt layer** — 15 reasoning assets served by the engine, authored once.

## Notable fixes

- Windows PowerShell 5.1 parse crash from BOM-less `.ps1` (1,055 files BOM-protected; installer
  ASCII-cleaned; `gald3r doctor` now guards it).
- Duplicate component names removed (per-agent `*.full.md`; deprecated `g-skl-medkit`).
- `doctor`/`bug sync` `Next ID` mis-parse fixed (anchored to the counter heading).

## Upgrade notes

- Run the installer or copy `project_template/` as usual; the engine provisions on first
  `uv run --project .gald3r_sys/engine gald3r …`.
- `task_file.v1.schema.yaml` now mirrors the engine's enforced status vocabulary.

See [CHANGELOG.md](../CHANGELOG.md) for the full list.
