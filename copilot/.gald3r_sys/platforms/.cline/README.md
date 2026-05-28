# Cline — gald3r Deploy Scaffold

**Config folder**: `.cline/`

This directory is the gald3r deploy scaffold for **Cline** (VS Code extension, agentic).
It is registered in `.gald3r_sys/_platform_capabilities.json` and recognised by the
platform-parity sync tooling.

- **Capability spec**: **`PLATFORM_SPEC.md`** (this directory, T1468) — the honest,
  per-capability assessment of what works on Cline vs. what is a gap. Read it first.
- **Install + customization guide**: **`g-skl-platform-cline`**
  (`.gald3r_sys/skills/g-skl-platform-cline/SKILL.md`).
- **Deploy guide**: **`cline_instructions.md`** (this directory) — folder layout, config
  files, conventions.

## Honest capability summary

Per `PLATFORM_SPEC.md` (legend: ✅ supported · ⚠️ partial · ❌ gap):

| Capability | Status | Notes |
|---|---|---|
| Rules | ✅ | `.clinerules/` directory (or legacy `.clinerules` file), auto-injected; no per-rule glob scoping |
| MCP | ✅ | strong — in-editor MCP Marketplace, stdio + remote servers (Cline's standout strength) |
| Commands | ⚠️ | Workflows (`/<name>` from `.clinerules/workflows/*.md`) — manual port of a curated subset only |
| Skills | ❌ | no skills primitive; gald3r `SKILL.md` files are not auto-discovered |
| Agents | ❌ | single agent, no persona registry |
| Hooks | ❌ | no lifecycle hook system; hook-driven behavior must become rules text |

> **Verification caveat**: `last_doc_scan: never`. The spec is authored from prior Cline
> knowledge and the existing skill, not a fresh `@g-platform-scan-docs cline` crawl.
> Re-verify `❓`/`⚠️` ratings before promoting them. File issues / corrections via the
> gald3r repo.
