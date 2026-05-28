# Kiro CLI Platform — gald3r Configuration Guide

**Platform**: Kiro CLI (terminal agent; rebrand of the Amazon Q Developer CLI `q` / `q chat`)
**Config Folder**: shared `.kiro/` namespace (steering + MCP shared with Kiro IDE)
**gald3r Version**: 1.0.0
**Official Docs**: https://kiro.dev/docs/cli
**Authoritative skill**: `g-skl-platform-kiro-cli`
**Full platform spec**: `PLATFORM_SPEC.md` (this directory) — read it for the verified capability matrix and Known Gaps.

> **Doc-verified (May 2026), not install-tested.** Folder/format facts below come from the
> official Kiro CLI docs (kiro.dev/docs/cli). They have NOT been confirmed against a live Kiro CLI
> install. Items marked (?) are unverified pending a SCAN_DOCS crawl. See `PLATFORM_SPEC.md`.

---

## Kiro CLI is NOT Kiro IDE

Kiro CLI and Kiro IDE share the `.kiro/` namespace and the **steering** context mechanism, but
the CLI has a **richer** agent/hook/command surface. Do NOT copy IDE conclusions onto the CLI.

| Capability | Kiro IDE | Kiro CLI |
|---|---|---|
| Custom agents | none | JSON custom-agent configs (`/agent`, `kiro-cli agent create`) |
| Slash commands | none (spec workflow only) | native built-in slash commands (`/agent`, `/context`, `/model`, `/prompts`, ...) |
| Hooks | file-event JSON (`fileEdited`) | lifecycle hooks in agent config (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`) |
| Steering / rules | `.kiro/steering/*.md` | `.kiro/steering/*.md` (shared) |
| MCP | `.kiro/settings/mcp.json` | `.kiro/settings/mcp.json` (shared) |

---

## Folder Layout

Kiro CLI reads project-scope config under repo-root `.kiro/` and user-scope config under
`~/.kiro/`. When both `.kiro/` and a legacy `.amazonq/` exist, `.kiro/` wins.

```
<project-root>/
.kiro/
  steering/                 # always-injected markdown context (shared with Kiro IDE)
    product.md
    structure.md
    tech.md
    gald3r.md               # gald3r task-management context (gald3r-authored)
  settings/
    mcp.json                # workspace-scope MCP config

~/.kiro/                    # user/global tree (migrated from ~/.aws/amazonq/)
  steering/                 # global steering (.md), applies to all projects
  settings/mcp.json         # global MCP config
```

> The canonical steering content is authored once and shared via the `.kiro/` namespace — Kiro CLI
> reads the same `.kiro/steering/` files as Kiro IDE. This `.kiro-cli/` scaffold carries the
> CLI-specific guidance only; it does NOT duplicate steering files.

**Migration (doc-verified):** on install, MCP servers, agents, rules, and prompts are auto-copied
from `~/.aws/amazonq/` into the matching `~/.kiro/` locations; `~/.aws/amazonq/rules/*` land in
`~/.kiro/steering/` with the same filenames.

---

## How gald3r maps onto Kiro CLI

| gald3r component | Kiro CLI surface | Status |
|---|---|---|
| Instructions | `.kiro/steering/gald3r.md` (no top-level `KIRO.md`/`AGENTS.md` primary) | works |
| Rules (`g-rl-*`) | consolidated into steering `.md` (no per-rule glob scoping) | partial |
| Agents (`g-agnt-*.md`) | JSON custom-agent configs — translation required, not a `.md` file drop | partial |
| Hooks | lifecycle hooks declared per-agent-config JSON; payload is JSON via STDIN | partial (adapter) |
| Skills (`g-skl-*/SKILL.md`) | no SKILL.md discovery; fold knowledge into steering / agent `resources` | not supported |
| Commands (`g-*`) | no confirmed user-authored slash-command file surface; document in steering or `/prompts` (?) | partial |
| MCP | `.kiro/settings/mcp.json` (`mcpServers` object) | works |

---

## Entry Points (doc-verified)

```bash
kiro-cli                 # primary entry point
q                        # preserved for backward compatibility (Q Developer CLI lineage)
q chat                   # preserved chat entry point
```

> The prior version of this guide documented `kiro run --steering` / `--no-interactive` / `--spec`
> commands. Those were NOT found in the current Kiro CLI docs and appear to have been invented;
> they have been removed. The exact non-interactive flag set is unverified (?) pending SCAN_DOCS.

Built-in slash commands (doc-verified): `/agent` (and `/agent create`), `/model`, `/guide`,
`/prompts`, `/context`, `/settings`.

---

## Hooks (lifecycle, declared in agent config)

Kiro CLI hooks are an array under the `hooks` field of an agent JSON config (NOT standalone
`.kiro/hooks/*.json` IDE files). Trigger points: `agentSpawn`, `userPromptSubmit`, `preToolUse`,
`postToolUse`, `stop`. Hooks receive the event as JSON via STDIN (fields include
`hook_event_name`, `cwd`, `session_id`).

> gald3r PowerShell lifecycle hooks map conceptually (session-start -> `agentSpawn`;
> session-end -> `stop`; preToolUse guard -> `preToolUse`) but require an adapter: wiring is
> per-agent JSON and the STDIN payload differs from the Cursor envelope. Exact `command`/matcher
> field names and tool-deny semantics are unverified (?).

---

## MCP

JSON `mcpServers` object at `.kiro/settings/mcp.json` (workspace) and `~/.kiro/settings/mcp.json`
(global). On migration, `~/.aws/amazonq/mcp.json` is copied to `~/.kiro/settings/mcp.json`.

---

## gitignore Decision

`.kiro/steering/*.md` are **source** — keep them tracked. Any agent-config JSON or
`.kiro/settings/mcp.json` that carries gald3r intent is also source. No generated project output
directory needs gitignoring for the CLI.

---

## Verification

```powershell
kiro-cli --version       # or: q --version (preserved alias)
Test-Path .kiro/steering
Test-Path .kiro/settings/mcp.json
```

---

## Common Pitfalls

- Kiro CLI and Kiro IDE share the `.kiro/` namespace, but their agent/hook/command conclusions are
  NOT interchangeable — the CLI is richer (custom agents, lifecycle hooks, built-in slash commands).
- gald3r `g-agnt-*.md` agents are not portable as-is — Kiro CLI agents are JSON; translation needed.
- There is no SKILL.md discovery — skill knowledge must be folded into steering.
- `kiro run ...` commands from older guides do not exist; use `kiro-cli` / `q` / `q chat`.
