# Kiro IDE (Amazon) — gald3r Deploy Scaffold

**Config folder**: `.kiro/`

This directory is the gald3r deploy scaffold for **Kiro IDE (Amazon)**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity
sync tooling.

Authoritative install + customization guide: **`g-skl-platform-kiro`** (.gald3r_sys/skills/g-skl-platform-kiro/SKILL.md).

## Platform spec

Read **`PLATFORM_SPEC.md`** in this directory for the verified-from-docs capability findings
(folder hierarchy, steering, native JSON hooks, MCP) and the honest **Known Gaps** list. The
scaffold artifacts here are adapted to match that spec.

## Honest capability summary (from PLATFORM_SPEC.md, doc-verified May 2026)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ⚠️** — Kiro has a native JSON agent-hook system (`.kiro/hooks/*.json`, `when`/`then`
  schema) but its events are **file/save-driven** (`fileEdited` + glob patterns), NOT
  session/tool-lifecycle. gald3r's PowerShell lifecycle hooks do not map 1:1.
- **Rules ⚠️** — steering files (`.kiro/steering/*.md`) are always-injected persistent context;
  no per-rule `alwaysApply`/`globs` scoping.
- **Skills ❌** — no `SKILL.md` discovery mechanism on the IDE.
- **Commands ⚠️** — no `@g-*`/`/g-*` invokable command surface; partial via hooks + steering.
- **MCP ✅** — `.kiro/settings/mcp.json` (workspace) / `~/.kiro/settings/mcp.json` (global).
- **Docs Fresh ❓** — `last_doc_scan: never`; pending `@g-platform-scan-docs kiro`.
