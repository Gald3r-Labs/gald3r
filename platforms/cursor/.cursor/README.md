# Cursor IDE — gald3r Deploy Scaffold (Reference Platform)

**Config folder**: `.cursor/`

This directory is the gald3r deploy scaffold for **Cursor IDE**. Cursor is the
**reference platform** for gald3r: every gald3r primitive originates in the `.cursor/`
tree and propagates to all other platforms via
`custom_scripts/platform_parity_sync.ps1`.

## Platform Specification

See **`PLATFORM_SPEC.md`** in this directory for the verified capability status
(folder hierarchy, AI instruction file, agents, skills, commands, hooks, rules, MCP),
the Known Gaps baseline (§9), and the verification evidence. The spec is the
straight copy of the authoritative source at
`.gald3r_sys/skills/g-skl-platform-cursor/PLATFORM_SPEC.md` — do not edit the copy
directly; update the skill source and re-run parity sync.

Authoritative install + customization guide: **`g-skl-platform-cursor`**
(`.gald3r_sys/skills/g-skl-platform-cursor/SKILL.md`).

## Deploy Artifacts in This Folder

| File | Purpose |
|---|---|
| `PLATFORM_SPEC.md` | Verified capability spec (copy of skill source) |
| `cursor_instructions.md` | Cursor-scoped maintainer/config guide |
| `hooks.json` | Top-level Cursor hook wiring (at `.cursor/hooks.json`) |
| `hooks.json.example.disabled` | Disabled reference variant |

> **Capability status (PLATFORM_SPEC.md §9 / Capability Summary):** Hooks ✅,
> Rules ✅, Skills ✅, Commands ✅, MCP ✅, Docs Fresh ❓ (`last_doc_scan: never` —
> pending a future `@g-platform-scan-docs cursor` crawl). Because Cursor is the
> reference, the scaffold IS the gold standard — no platform-adaptation deletions
> are warranted; the only outstanding items are the deferred T600 HTTP-hook parity
> and the SCAN_DOCS confirmation noted in the spec.
