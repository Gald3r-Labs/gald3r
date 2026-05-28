# Warp AI terminal — gald3r Deploy Scaffold

**Config folder**: `.warp/`

This directory is the gald3r deploy scaffold for **Warp AI terminal**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity
sync tooling.

Authoritative install + customization guide: **`g-skl-platform-warp`** (.gald3r_sys/skills/g-skl-platform-warp/SKILL.md).

## Platform findings — read first

**`PLATFORM_SPEC.md`** (in this directory) is the authoritative, T1483-verified
capability picture for Warp: what works (project Rules via `AGENTS.md`/`WARP.md`,
first-class MCP auto-discovery), what is partial (Warp Drive Workflows as the commands
analogue), and the honest hard gaps (no on-disk skills, agents, or lifecycle hooks).
Read it before trusting any summary.

> **Status (T1483/T1508 — adapted 2026-05-27):** the deploy payload is authored and
> corrected against `PLATFORM_SPEC.md`. The prior "no project-level rules file" claim
> was stale and has been fixed — Warp auto-applies `AGENTS.md`/`WARP.md`. See
> **`warp_instructions.md`** for the full deploy guide (folder layout, the Rules / MCP /
> Commands capability map, and the T1277 AC6 gitignore decision). The Warp Drive
> Workflow stubs this platform consumes are shipped alongside it.
