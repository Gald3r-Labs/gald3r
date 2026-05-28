# Kiro CLI — gald3r Deploy Scaffold

**Platform**: Kiro CLI — the terminal agent that is the rebrand of the **Amazon Q Developer CLI**
(`q` / `q chat`, preserved for backward compatibility).
**Config namespace**: shared `.kiro/` (steering + MCP shared with Kiro IDE).

This directory is the gald3r deploy scaffold for **Kiro CLI**. It is distinct from Kiro IDE
(`g-skl-platform-kiro` / T1472): the CLI has a richer agent/hook/command surface.

## Read first

- **`PLATFORM_SPEC.md`** (this directory) — verified-from-docs capability matrix, folder layout,
  and Known Gaps. This is the source of truth for what works on Kiro CLI.
- **`kiro-cli_instructions.md`** (this directory) — the deploy/customization guide.
- **`g-skl-platform-kiro-cli/SKILL.md`** — the authoritative install + customization skill.

## Capability summary (from PLATFORM_SPEC.md)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| partial | partial | none | partial | works | untested |

- **Hooks** — native lifecycle hooks (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`)
  declared per-agent JSON, payload via STDIN (adapter required).
- **Rules** — steering `.kiro/steering/*.md` provides persistent context; no per-rule glob scoping.
- **Skills** — no SKILL.md discovery mechanism.
- **Commands** — built-in slash commands exist; no confirmed gald3r command-file surface.
- **MCP** — `.kiro/settings/mcp.json` (doc-verified, Q Developer CLI lineage).
- **Docs Fresh** — `last_doc_scan: never`; flip to verified after the first SCAN_DOCS crawl.

> Status is doc-verified (May 2026), not install-tested. See `PLATFORM_SPEC.md` Known Gaps for the
> unverified (?) items.
