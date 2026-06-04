# OpenClaw — gald3r Deploy Scaffold

**Config folder**: `.openclaw/`
**Platform**: OpenClaw — local-first autonomous AI agent (ex *clawdbot* / *moltbot*), MIT-licensed
**Status**: WARNING — doc-supported, install-unverified (`last_doc_scan: never`)

This directory is the gald3r deploy scaffold for **OpenClaw**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity sync tooling.

## Read this first

**`PLATFORM_SPEC.md`** (in this directory) is the full platform analysis — folder hierarchy,
per-surface capability findings, Known Gaps vs. the Cursor reference, and verification evidence.
It is a byte-identical copy of the authoring skill's spec
(`.gald3r_sys/skills/g-skl-platform-openclaw/PLATFORM_SPEC.md`). **All claims in this scaffold
defer to PLATFORM_SPEC.md.**

## Capability Summary (from PLATFORM_SPEC.md)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|-------|-------|--------|----------|-----|------------|
| WARNING | NOT SUPPORTED | WARNING | WARNING | WARNING | UNTESTED |

- **Hooks**: capability exists (`HOOK.md` + `handler.ts`, TypeScript), but gald3r `.ps1` payload is non-portable.
- **Rules**: no native `rules/`/`.mdc` mechanism; fold into `SOUL.md` / `AGENTS.md`.
- **Skills**: `SKILL.md` folder-per-skill matches gald3r, but install-path-dependent (workspace `skills/`).
- **Commands**: native slash (`/new`, `/reset`) + CLI; gald3r `g-*.md` files not ingested.
- **MCP**: first-class (`mcp.servers` / `openclaw mcp set`); gald3r server set not auto-imported.
- **Docs Fresh**: `last_doc_scan: never` — run `@g-platform-scan-docs openclaw` to verify.

## Files in this scaffold

| File | Purpose |
|------|---------|
| `PLATFORM_SPEC.md` | Full platform analysis (authoritative). |
| `openclaw_instructions.md` | Deploy guide: folder layout, capability mapping, gitignore, pitfalls. |
| `SOUL.md` | gald3r persona template OpenClaw reads as the project identity document. |
| `README.md` | This index. |

Authoritative install + customization guide:
**`g-skl-platform-openclaw`** (`.gald3r_sys/skills/g-skl-platform-openclaw/SKILL.md`).
