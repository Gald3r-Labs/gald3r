# Antigravity (Google Antigravity) -- gald3r Deploy Scaffold

Authoritative install + customization guide: **`g-skl-platform-antigravity`** (.gald3r_sys/skills/g-skl-platform-antigravity/SKILL.md).

See **`PLATFORM_SPEC.md`** in this directory for verified platform capability details (Phase 1 research, T1465).
Phase 2 deploy artifact adaptation: see T1490 (antigravity) / T1492 (gemini) in TASKS.md.

## Why this scaffold is intentionally minimal (T1490)

> **VOLATILE PLATFORM -- needs SCAN_DOCS before any artifacts are added.**
> Google Antigravity 2.0 relaunched ~2026-05-19 with breaking config changes. The PLATFORM_SPEC.md
> in this directory was authored from public docs/guides, NOT a live install. Most capabilities are
> still `?` (untested). This scaffold deliberately ships **no platform config artifacts** because
> fabricating unverified config (rules dir, hooks, skill-discovery files) would be dishonest and
> would likely break on install.

What the spec confirms (the only things gald3r can rely on today):

| Capability | Status | gald3r artifact |
|---|---|---|
| AI instruction file (`AGENTS.md`) | OK -- verified | Generated at project root (shared `AGENTS.md`; no override needed here) |
| MCP (`{ "mcpServers": {...} }`) | OK -- verified | `.antigravity/mcp.json` (project-local) or `~/.gemini/antigravity/mcp_config.json` (global) |
| Commands -> workflows (`/`) | partial -- mapping untested | `~/.gemini/antigravity/global_workflows/` (format unverified) |
| Rules (always-apply dir) | partial -- only via `AGENTS.md` | none confirmed |
| Skills (`SKILL.md` discovery) | `?` untested | none confirmed |
| Agents (`g-agnt-*.md` discovery) | `?` untested | none confirmed |
| Hooks (lifecycle / `hooks.json`) | `?` untested | none confirmed |

**No Cursor-specific artifacts** (no `hooks.json`, no `.ps1` hook wiring, no `.cursor/`-style rule
files) are shipped here, because the spec has not confirmed any of those work on Antigravity
(PLATFORM_SPEC.md section 9, Known Gaps). Adding them would be Cursor copypasta.

## Next steps (before this scaffold gains real artifacts)

1. Run `@g-platform-scan-docs antigravity` (or `g-skl-platform-monitor SCAN_DOCS antigravity`) to crawl
   the current docs (https://antigravity.google/docs/home) -- `last_doc_scan` is `never`.
2. Perform a live install test to confirm the `?`/partial rows in PLATFORM_SPEC.md section 9.
3. Only after concrete evidence is recorded: add the confirmed config artifacts here (e.g. an
   `mcp.json` template), update PLATFORM_SPEC.md, and bump the PLATFORM_STATUS.md row.

If you opened this folder expecting platform config and found only docs: that is by design for a
volatile, unverified platform. File feedback via the gald3r GitHub issues.
