# Qwen Code (Qwen Code CLI) -- gald3r Deploy Scaffold

Authoritative install + customization guide: **`g-skl-platform-qwen`** (.gald3r_sys/skills/g-skl-platform-qwen/SKILL.md).

See **`PLATFORM_SPEC.md`** in this directory for verified platform capability details (Phase 1 research, T1480).
Phase 2 deploy artifact adaptation: T1505.

## What this scaffold is (and is not) (T1505)

> **Qwen Code is an instruction-file + JSON-settings platform, NOT a rules/skills/hooks platform.**
> Qwen Code is an adapted fork of Google's Gemini CLI, so its config surface mirrors Gemini CLI
> (see `g-skl-platform-gemini`). The only files Qwen Code reads natively are **`QWEN.md`**
> (hierarchical memory/context) and the **`.qwen/`** config tree (`settings.json`, `commands/`).
> The gald3r `.agent/` install tree (rules/skills/agents/commands as `.md`) is portability
> scaffolding -- Qwen does **not** auto-discover it. gald3r content reaches Qwen only by being
> referenced from `QWEN.md`/`AGENTS.md`.

> **Two folder names in play (do not conflate):**
> - **`.qwen/`** -- what Qwen Code itself reads (`settings.json`, `commands/`).
> - **`.agent/`** -- where gald3r installs its portable `.md` layout. Not natively loaded by Qwen.

## Honest capability table (from PLATFORM_SPEC.md section 9)

| Capability | Status | gald3r artifact / reality on Qwen |
|---|---|---|
| AI instruction file (`QWEN.md`) | OK -- verified (doc) | Generated as a thin overlay pointing at `AGENTS.md`; hierarchical memory; `context.fileName`-configurable; `/memory show` / `/memory refresh` |
| MCP (`mcpServers`) | OK -- verified (doc) | First-class via `.qwen/settings.json` `mcpServers` block (or root `.mcp.json`); manage with `/mcp`; MCP prompts can load as slash commands |
| Commands (slash) | partial -- format mismatch | Qwen native commands live in `.qwen/commands/` (TOML, or Markdown+YAML in newer versions; TOML deprecated-but-supported), invoked `/name` or `/dir:name`. gald3r ships `g-*` as `.md` under `.agent/commands/` -- **documentation, not executable** slash commands (no emitter yet) |
| Rules (always-apply dir) | partial -- only via `QWEN.md` | `.agent/rules/g-rl-*.md` is **not auto-loaded**. No `alwaysApply:`/`globs:` semantics. Effective only when referenced/inlined from `QWEN.md` |
| Skills (`SKILL.md` discovery) | not supported | No native skills system. `.agent/skills/<name>/SKILL.md` reachable only via `QWEN.md` reference. Native analogues are custom commands + MCP prompts (different shape) |
| Agents (`g-agnt-*.md` discovery) | not supported | No sub-agent file system. `g-agnt-*.md` works only as conversational instruction-file references |
| Hooks (lifecycle / `hooks.json`) | not supported | No hook/event system (Gemini-CLI lineage). PCAC inbox check, session-start injection, pre-commit/push gates have no automatic firing surface -- run manually |
| Docs freshness | untested | `last_doc_scan: never` -- run `@g-platform-scan-docs qwen` |

Legend: OK = doc-verified mechanism, partial = works only via a non-native path, not supported = no native primitive, untested = not yet crawled/installed.

## No Cursor-specific artifacts shipped here (AC5)

This scaffold contains **no** `hooks.json`, no `.ps1` hook wiring, and no `.cursor/`-style
always-apply rule files, because PLATFORM_SPEC.md section 9 confirms Qwen Code has **no native
hook, rules-folder, skills, or agent-file system**. Shipping those would be Cursor copypasta and
would mislead users into expecting auto-loaded behavior that Qwen does not provide.

The previously-shipped `config.yaml` (`model: qwen-max`, `instructions: .qwen/instructions.md`) +
`instructions.md` pair was **removed** (T1505): it described a config surface Qwen Code does not
use. Qwen Code reads JSON `.qwen/settings.json` (not YAML `config.yaml`) and a root `QWEN.md`
context file (not `.qwen/instructions.md`). See PLATFORM_SPEC.md section 9, gaps 5 and 7.

The MCP mechanism IS confirmed (doc-verified), but the concrete server set is install-untested in
this repo (no `.qwen/settings.json` present at spec time), so no `settings.json`/`mcp.json`
template is fabricated here -- the canonical MCP wiring is documented in the `g-skl-platform-qwen`
skill.

## Next steps (before this scaffold gains real config artifacts)

1. Run `@g-platform-scan-docs qwen` (or `g-skl-platform-monitor SCAN_DOCS qwen`) to crawl the
   current Qwen Code docs (https://qwenlm.github.io/qwen-code-docs/, https://github.com/QwenLM/qwen-code)
   -- `last_doc_scan` is `never`.
2. Confirm the `partial`/`untested` rows in PLATFORM_SPEC.md section 9 against a live install
   (exact `settings.json` `modelProviders`/`mcpServers` keys, built-in slash-command list, the
   TOML -> Markdown command-format migration state).
3. Only after concrete evidence is recorded: add confirmed config artifacts here (e.g. a
   `.qwen/settings.json` MCP template, or a `g-*` -> `.qwen/commands/` emitter), update
   PLATFORM_SPEC.md, and bump the PLATFORM_STATUS.md row.

If you opened this folder expecting auto-loaded rules/skills/hooks and found only docs: that is by
design -- Qwen Code does not support those natively. File feedback via the gald3r GitHub issues.
