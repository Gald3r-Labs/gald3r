# OpenHands — gald3r Deploy Scaffold

**Config folder**: `.openhands/` (legacy) + repo-root `AGENTS.md` (primary) + `.agents/skills/` (recommended)

This directory is the gald3r deploy scaffold for **OpenHands** (All Hands AI, formerly
OpenDevin — open-source agentic dev that runs inside a Docker-sandboxed runtime). It is
registered in `.gald3r_sys/_platform_capabilities.json` and recognised by the
platform-parity sync tooling.

- **Capability spec**: **`PLATFORM_SPEC.md`** (this directory, T1471) — the honest,
  per-capability assessment of what works on OpenHands vs. what is a gap. Read it first.
- **Install + customization guide**: **`g-skl-platform-openhands`**
  (`.gald3r_sys/skills/g-skl-platform-openhands/SKILL.md`).
- **Deploy guide**: **`openhands_instructions.md`** (this directory) — folder layout,
  config files, conventions.

## Honest capability summary

Per `PLATFORM_SPEC.md` (legend: ✅ supported · ⚠️ partial · ❌ gap · ❓ untested):

| Capability | Status | Notes |
|---|---|---|
| Rules | ⚠️ | Content carries via always-on `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` (injected into system prompt); no `.mdc` per-rule glob scoping |
| MCP | ⚠️ | Skill-scoped `mcp_tools` frontmatter + global instance config (docs-verified); sandbox reaches host via `host.docker.internal`; live gald3r server block untested |
| Skills | ⚠️ | Native folder-per-skill `SKILL.md`: `.agents/skills/` (recommended) → `.openhands/skills/` (deprecated) → `.openhands/microagents/` (legacy); gald3r frontmatter tolerance untested |
| Commands | ❌ | No native command/slash surface; gald3r `g-*` workflows portable only as keyword-triggered skills |
| Agents | ⚠️/❌ | Single generalist agent (CodeActAgent); no native multi-agent roster — `g-agnt-*` content portable as skills/context only |
| Hooks | ❌ | No native lifecycle hook system; Docker sandbox blocks host `.ps1` hooks regardless |

## Key platform facts (from PLATFORM_SPEC.md)

- **Instruction file**: repo-root `AGENTS.md` is the **current primary** always-on surface
  (also `CLAUDE.md` / `GEMINI.md`). `.openhands/microagents/repo.md` still loads but is the
  **legacy** repository-microagent path — see PLATFORM_SPEC §2, §9 #5.
- **Skills**: `.agents/skills/<name>/SKILL.md` is the recommended location; `.openhands/skills/`
  is deprecated; `.openhands/microagents/` is legacy backward-compat.
- **Docker sandbox**: host file paths, host PowerShell hooks, and host-local MCP servers are
  not directly reachable from the container; MCP uses `host.docker.internal`.
- **No live install verification** — the spec is doc-citation-based
  (https://docs.openhands.dev scan 2026-05-26), not a sandbox run. Re-verify `⚠️`/`❓`
  ratings via a real `openhands` install. File corrections via the gald3r repo.

> **Status (T1471 — spec done; T1496 — scaffold adapted):** the per-platform deploy payload
> is authored. `PLATFORM_SPEC.md` is byte-identical to the skill's spec; `openhands_instructions.md`,
> `config.toml`, and `microagents/repo.md` are annotated to reflect the AGENTS.md-primary /
> `.agents/skills/`-recommended reality (microagents = legacy).
