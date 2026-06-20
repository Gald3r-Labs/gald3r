---
name: g-skl-platform-kiro-cli
description: Authoritative reference for Kiro CLI (Amazon's terminal agent, the Q Developer CLI rebrand) customization in gald3r projects. Covers .kiro/steering/ + AGENTS.md, Agent Skills (SKILL.md), JSON custom agents + subagents, lifecycle hooks, slash commands, MCP, and gald3r install verification. Distinct from Kiro IDE (g-skl-platform-kiro).
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro-cli/
vault_docs_url: https://kiro.dev/docs/cli
docs_url: https://kiro.dev/docs/cli
docs_url_secondary:
  - https://kiro.dev/docs/cli/skills/
  - https://kiro.dev/docs/cli/steering/
  - https://kiro.dev/docs/cli/custom-agents/configuration-reference/
  - https://kiro.dev/docs/cli/hooks/
  - https://kiro.dev/docs/cli/mcp/
  - https://kiro.dev/docs/cli/reference/slash-commands/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in agent JSON config (agentSpawn/userPromptSubmit/preToolUse/postToolUse/stop; STDIN-JSON; exit 2 blocks PreToolUse)"
  rules: "✅ steering files .kiro/steering/*.md (product/tech/structure auto-loaded) + reads AGENTS.md"
  skills: "✅ Agent Skills (SKILL.md) auto-loaded from .kiro/skills/ + ~/.kiro/skills/; also /skill-name"
  commands: "✅ Skills-as-slash-commands (/skill-name) + /prompts create; no standalone command-file format"
  agents: "✅ native JSON custom agents (filename=name) + subagents (isolated context, up to 4)"
  mcp: "✅ native — mcpServers JSON at .kiro/settings/mcp.json + ~/.kiro/settings/mcp.json"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-kiro-cli

Activate for: setting up gald3r with Kiro CLI (terminal variant), authoring steering/skills/agents/hooks, understanding differences from Kiro IDE, or verifying the Kiro CLI gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Kiro CLI natively supports commands, rules, agents, skills, hooks, and MCP, reads
> `AGENTS.md` (not `CLAUDE.md`), and auto-discovers `SKILL.md` under `.kiro/skills/`, so gald3r's
> `AGENTS.md` + `SKILL.md` artifacts are drop-in reusable. (Verified 2026-06-02 against
> https://kiro.dev/docs/cli.) Caveats are *format* not *capability*: agents are JSON-only, commands
> route through skills/prompts, and hooks wire per-agent-JSON via STDIN.

## 1. Platform Overview

**Kiro CLI** is Amazon's **terminal agentic coding assistant** — the **rebrand/successor of the
Amazon Q Developer CLI** (`q` / `q chat` entry points preserved). It is spec-driven and
agent-centric, with the full extensibility surface under **`.kiro/`**. It shares the `.kiro/`
directory and **steering** context mechanism with the **Kiro IDE**, but has a **richer
agent/hook/command/skills surface** than the IDE (see `g-skl-platform-kiro`, T1472).

- **Instruction file**: `.kiro/steering/*.md` (foundation files auto-loaded) + **`AGENTS.md`**
  standard — **no `CLAUDE.md`/`GEMINI.md`**
- **Skills**: ✅ Agent Skills `SKILL.md` auto-loaded from `.kiro/skills/` + `~/.kiro/skills/`; each
  also exposed as a `/skill-name` slash command (v2.1, 2026-04-24)
- **Custom agents**: ✅ **JSON** configs (filename without `.json` = agent name; `/agent create`) +
  **subagents** (isolated context, up to 4 at once) — the IDE lacks this
- **Lifecycle hooks**: ✅ in agent config — `agentSpawn`, `userPromptSubmit`, `preToolUse`,
  `postToolUse`, `stop` (Cursor-like taxonomy; the IDE uses `fileEdited` hooks instead)
- **Commands**: ✅ Skills-as-slash-commands + `/prompts`; built-ins (`/agent`, `/context`, `/model`,
  `/guide`, `/settings`)
- **MCP**: ✅ `mcpServers` JSON at `.kiro/settings/mcp.json` (migrated from `~/.aws/amazonq/mcp.json`)
- **AWS integration**: Amazon Q / Bedrock model access via AWS credentials

> **Full capability assessment**: see `PLATFORM_SPEC.md` (9 sections, doc-verified 2026-06-02).

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                       ← read by Kiro CLI (AGENTS.md standard; NOT CLAUDE.md)
└── .kiro/
    ├── steering/  *.md             ← always-on context (product/tech/structure auto-loaded)
    ├── skills/    <name>/SKILL.md  ← Agent Skills (YAML: name, description)
    ├── settings/
    │   └── mcp.json                ← mcpServers object
    └── (custom-agent JSON configs — filename without .json = agent name)
```

Global mirror under `~/.kiro/` (`steering/`, `skills/`, `settings/mcp.json`). Workspace skills
override identically-named global skills. **Same `.kiro/` directory as Kiro IDE** — steering + MCP
are shared, but agent/hook/command/skills config is CLI-specific.

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `AGENTS.md` (+ `g-skl-*/SKILL.md` under
`.kiro/skills/`)** — Kiro CLI reads `AGENTS.md` and auto-discovers `SKILL.md` (each also becomes
`/skill-name`). Add gald3r rules as `.kiro/steering/*.md`, a gald3r custom-agent JSON, and
`.kiro/settings/mcp.json` for MCP servers.

### Verify
```powershell
Test-Path AGENTS.md                                   # instruction file Kiro CLI reads
Test-Path .kiro/steering                              # always-on context
Test-Path .kiro/skills                                # Agent Skills (SKILL.md)
Test-Path .kiro/settings/mcp.json                     # MCP config
kiro-cli --version    # or: q --version  (preserved Q Developer CLI entry point)
```

❓ The exact `--version`/headless flags for the current Kiro CLI are unverified — confirm against
https://kiro.dev/docs/cli/reference/slash-commands/ before scripting CI.

## 4. Common Pitfalls

- **Reads `AGENTS.md`, NOT `CLAUDE.md`** — gald3r's instruction content must live in `AGENTS.md`
  (or `.kiro/steering/`), not a `CLAUDE.md` root file.
- **No standalone command-file format** — custom commands are expressed as **Skills** (`/skill-name`)
  or local **prompts** (`/prompts create`); a gald3r command-per-file model maps onto skills.
- **Custom agents are JSON, not markdown** — `g-agnt-*.md` need markdown→JSON translation (pin
  steering via `resources`), not a file drop.
- **Hooks wire per-agent JSON, STDIN payload** — hooks live in each agent's `hooks` field (not a
  central `hooks.json`); cross-agent automation is replicated per agent; gald3r `.ps1` hooks must
  read `$input`/stdin (not `$env:*`); exit code `2` blocks (PreToolUse only).
- **No per-rule glob scoping** — steering has no `alwaysApply`/`globs`; foundation files are always
  on, others scope via an agent `resources` glob.
- **Shared `.kiro/` with Kiro IDE** — installing steering/MCP for one benefits the other, but the
  CLI's agent/hook/command/skills config is **not** the IDE's (`fileEdited` hooks, no custom agents).

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | agent JSON `hooks`; `agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`; STDIN-JSON; exit `2` blocks (PreToolUse); per-agent wiring |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Agent Skills auto-loaded from `.kiro/skills/` + `~/.kiro/skills/`; also `/skill-name` (v2.1) |
| Agents (`g-agnt-*.md`) | ✅ | native **JSON** custom agents (filename=name) + subagents (isolated, up to 4); markdown→JSON translation |
| Commands (`@g-*`) | ✅ | Skills-as-slash-commands (`/skill-name`) + `/prompts create`; no standalone command-file format |
| Rules (`g-rl-*`) | ✅ | `.kiro/steering/*.md` (product/tech/structure auto-loaded) + reads `AGENTS.md`; no per-rule glob scoping |
| MCP | ✅ | `mcpServers` JSON at `.kiro/settings/mcp.json` + `~/.kiro/settings/mcp.json` |

**Differences from Kiro IDE (`g-skl-platform-kiro`, T1472) — do not conflate the two:**

| Capability | Kiro IDE | Kiro CLI |
|---|---|---|
| Custom agents | ❌ none | ✅ JSON configs (`/agent create`) + subagents |
| Hooks | ⚠️ `fileEdited` JSON files in `.kiro/hooks/` | ✅ lifecycle hooks in agent config (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`) |
| Slash commands | ❌ none (spec workflow) | ✅ Skills-as-slash-commands + `/prompts` + built-ins |
| Skills | (IDE: see kiro spec) | ✅ Agent Skills `SKILL.md` auto-loaded |
| Steering / MCP | ✅ shared | ✅ shared |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs kiro-cli` (crawl_max_age_days: 7).
