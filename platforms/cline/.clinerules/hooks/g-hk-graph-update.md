# Hook: g-hk-graph-update

Refreshes the gald3r_muninn codebase graph index (T1158) so `graph_impact`,
`graph_callers`, etc. return current results for the next g-go-code Step b0
Impact Scan. Companion `.md` added with the T1624 wiring (the script predates
the T1171 companion contract).

## Fires On

The **canonical `stop` event** (T1624, WS-A-1). Wired in `g_hk_core.py`
`CONCERN_CHAIN["stop"]` and registered directly on the Claude Code
(`.claude/settings.json` `hooks.Stop`) and Cursor (`.cursor/hooks.json` `stop`)
triggers, so the graph refreshes at the end of every agent turn. It remains
directly invocable as a git post-commit hook (its original T1158 role).

## What It Does

Locates the muninn indexers (`docker/gald3r/tools/plugins/muninn/indexers/`)
and runs them incrementally — the Python AST indexer via `python`, the
TypeScript indexer via `node`. Installs without the muninn plugin (the common
case) skip in milliseconds. Each indexer run is capped at 60 seconds so a
wedged indexer can never stall the host session's stop chain.

## Side Effects

- Updates the muninn graph index files under the plugin directory.
- Appends a `muninn-update | ...` line to `.gald3r/logs/muninn_updates.log`
  (only when `.gald3r/logs/` exists).
- Always exits 0 — never blocks the host session or a commit.

## Related Tasks

- T1624 (WS-A-1) — wired the logging chain into the canonical hook core.
- T1158 — muninn post-commit graph refresh (original role).
- Skill: `g-skl-muninn` (graph queries this index serves).
