# Gemini (Gemini CLI) -- gald3r Deploy Scaffold

Authoritative install + customization guide: **`g-skl-platform-gemini`** (.gald3r_sys/skills/g-skl-platform-gemini/SKILL.md).

See **`PLATFORM_SPEC.md`** in this directory for verified platform capability details (Phase 1 research, T1467).
Phase 2 deploy artifact adaptation: see T1490 (antigravity) / T1492 (gemini) in TASKS.md.

## What this scaffold is (and is not) (T1492)

> **Gemini CLI is an instruction-file + JSON-settings platform, NOT a rules/skills/hooks platform.**
> The only files Gemini CLI reads natively are **`GEMINI.md`** (hierarchical memory) and the
> **`.gemini/`** config tree (`settings.json`, `commands/*.toml`). The gald3r `.agent/` install tree
> (rules/skills/agents/commands as `.md`) is portability scaffolding -- Gemini does **not**
> auto-discover it. gald3r content reaches Gemini only by being referenced from `GEMINI.md`/`AGENTS.md`.

> **Two folder names in play (do not conflate):**
> - **`.gemini/`** -- what Gemini CLI itself reads (`settings.json`, `commands/*.toml`).
> - **`.agent/`** -- where gald3r installs its portable `.md` layout. Not natively loaded by Gemini.

## Honest capability table (from PLATFORM_SPEC.md section 9)

| Capability | Status | gald3r artifact / reality on Gemini |
|---|---|---|
| AI instruction file (`GEMINI.md`) | OK -- verified (doc) | Generated as a thin overlay pointing at `AGENTS.md`; hierarchical memory; `/memory show` / `/memory refresh` |
| MCP (`mcpServers`) | OK -- verified (doc) | First-class via `.gemini/settings.json` `mcpServers` block (or root `.mcp.json`); manage with `/mcp` |
| Commands (slash) | partial -- format mismatch | Gemini native commands are **TOML** in `.gemini/commands/*.toml` (`/name` or `/dir:name`). gald3r ships `g-*` as `.md` under `.agent/commands/` -- **documentation, not executable** slash commands (no TOML emitter yet) |
| Rules (always-apply dir) | partial -- only via `GEMINI.md` | `.agent/rules/g-rl-*.md` is **not auto-loaded**. No `alwaysApply:`/`globs:` semantics. Effective only when referenced/inlined from `GEMINI.md` |
| Skills (`SKILL.md` discovery) | not supported | No native skills system. `.agent/skills/<name>/SKILL.md` reachable only via `GEMINI.md` reference. Native analogues are extensions + custom commands (different shape) |
| Agents (`g-agnt-*.md` discovery) | not supported | No sub-agent file system. `g-agnt-*.md` works only as conversational instruction-file references |
| Hooks (lifecycle / `hooks.json`) | not supported | No hook/event system. PCAC inbox check, session-start injection, pre-commit/push gates have no automatic firing surface -- run manually |
| Docs freshness | untested | `last_doc_scan: never` -- run `@g-platform-scan-docs gemini` |

Legend: OK = doc-verified mechanism, partial = works only via a non-native path, not supported = no native primitive, untested = not yet crawled/installed.

## No Cursor-specific artifacts shipped here (AC5)

This scaffold contains **no** `hooks.json`, no `.ps1` hook wiring, and no `.cursor/`-style
always-apply rule files, because PLATFORM_SPEC.md section 9 confirms Gemini CLI has **no native
hook, rules-folder, skills, or agent-file system**. Shipping those would be Cursor copypasta and
would mislead users into expecting auto-loaded behavior that Gemini does not provide.

The MCP mechanism IS confirmed (doc-verified), but the concrete server set is install-untested in
this repo (no `.gemini/settings.json` present at spec time), so no `settings.json`/`mcp.json`
template is fabricated here -- the canonical MCP wiring is documented in
`gald3r_template/.gald3r_sys/platforms/GEMINI.md` and the `g-skl-platform-gemini` skill.

## Next steps (before this scaffold gains real config artifacts)

1. Run `@g-platform-scan-docs gemini` (or `g-skl-platform-monitor SCAN_DOCS gemini`) to crawl the
   current Gemini CLI docs (https://github.com/google-gemini/gemini-cli) -- `last_doc_scan` is `never`.
2. Confirm the `partial`/`untested` rows in PLATFORM_SPEC.md section 9 against a live install
   (exact `settings.json` `mcpServers` keys, built-in slash-command list, `commands/*.toml` schema).
3. Only after concrete evidence is recorded: add confirmed config artifacts here (e.g. a
   `.gemini/settings.json` MCP template, or a `g-*` -> `.gemini/commands/*.toml` emitter), update
   PLATFORM_SPEC.md, and bump the PLATFORM_STATUS.md row.

If you opened this folder expecting auto-loaded rules/skills/hooks and found only docs: that is by
design -- Gemini CLI does not support those natively. File feedback via the gald3r GitHub issues.
