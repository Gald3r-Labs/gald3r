# JetBrains Junie — gald3r Deploy Scaffold

**Config folder**: `.junie/` · **Instruction file**: `.junie/AGENTS.md` (preferred), `.junie/guidelines.md` (legacy)

This directory is the gald3r deploy scaffold for **JetBrains Junie**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity sync tooling.

## Read These First

- **`PLATFORM_SPEC.md`** (this folder) — verified per-platform capability findings, including
  the **Known Gaps** section (no rules folder, no file-defined agents, no skill discovery, no
  custom command framework, no lifecycle hooks; MCP native via `.junie/mcp/mcp.json`; persistent
  guidelines via `.junie/AGENTS.md`; Action Allowlist = approval gate, not a hook bus).
- **`junie_instructions.md`** — deploy guide (folder layout, guidelines surface, MCP wiring,
  gitignore decision, common pitfalls).
- Authoritative install + customization guide: **`g-skl-platform-junie`**
  (`.gald3r_sys/skills/g-skl-platform-junie/SKILL.md`).

## Files in This Scaffold

| File | Purpose |
|------|---------|
| `AGENTS.md` | PREFERRED gald3r guidelines — auto-injected into every Junie task (task context, commit format, bug protocol, role notes, MCP pointer). |
| `guidelines.md` | LEGACY guidelines mirror for older Junie builds (still supported; kept in sync with `AGENTS.md`). |
| `mcp/mcp.json` | REFERENCE TEMPLATE for project-level MCP servers (`.junie/mcp/mcp.json`). Edit before use — no server is wired by default. |
| `PLATFORM_SPEC.md` | Verified capability findings (read first). |
| `junie_instructions.md` | Deploy/configuration guide. |

## Capability Summary

Legend: ✅ verified · ⚠️ partial · ❌ not supported · ❓ untested.

| Hooks | Rules | Skills | Commands | MCP |
|---|---|---|---|---|
| ❌ | ⚠️ (single-file `AGENTS.md`) | ❌ | ❌ | ✅ (`.junie/mcp/mcp.json`) |

> **Corrections applied (T1501):** the scaffold previously named only the legacy
> `.junie/guidelines.md` and shipped no MCP config. Per `PLATFORM_SPEC.md`, the preferred
> guidelines surface is now `.junie/AGENTS.md` (legacy `guidelines.md` retained and annotated),
> and MCP is a native strong fit — a reference `mcp/mcp.json` template was added.
> `junie_instructions.md` was corrected (docs URL `junie.jetbrains.com/docs`, AGENTS.md-primary
> layout, honest no-rules/agents/skills/commands/hooks facts). No fabricated files were present
> to remove. No Cursor-specific artifacts (`hooks.json`, `.ps1`, `.mdc`) are in this scaffold.
