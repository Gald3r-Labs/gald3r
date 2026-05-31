---
name: g-skl-platform-kiro-cli
description: Authoritative reference for Kiro CLI (Amazon's terminal agent, the Q Developer CLI rebrand) customization in gald3r projects. Covers .kiro/steering/, JSON custom agents, lifecycle hooks, slash commands, MCP, and gald3r install verification. Distinct from Kiro IDE (g-skl-platform-kiro).
crawl_max_age_days: 14
vault_doc_path: research/platforms/kiro-cli/
vault_docs_url: https://kiro.dev/docs/cli
docs_url: https://kiro.dev/docs/cli
capability_status:
  hooks: ⚠️       # native lifecycle hooks (agentSpawn/userPromptSubmit/preToolUse/postToolUse/stop) in agent JSON; per-agent wiring + STDIN payload differ from Cursor
  rules: ⚠️       # steering files (.kiro/steering/*.md), no per-rule glob scoping
  skills: ❌       # no SKILL.md discovery mechanism
  commands: ⚠️    # built-in slash commands exist; no confirmed gald3r command-file surface
  mcp: ✅          # .kiro/settings/mcp.json (Q Developer CLI lineage), doc-verified
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-kiro-cli

Activate for: setting up gald3r with Kiro CLI (terminal variant), configuring CLI steering, understanding differences from Kiro IDE, or verifying Kiro-CLI gald3r integration.

---

## 1. Platform Overview

**Kiro CLI** is the terminal agent in Amazon's Kiro family — the **rebrand of the Amazon Q
Developer CLI** (`q` / `q chat`). Kiro CLI became available 2025-11-17; on 2025-11-24 the Q
Developer CLI auto-updated to Kiro CLI for users with auto-update enabled. The `q` and `q chat`
entry points are preserved for backward compatibility. It shares the `.kiro/` directory and
**steering** context mechanism with the Kiro IDE, but has a **richer agent/hook/command surface**
than the IDE (see Known Gaps and `PLATFORM_SPEC.md`).

- **Steering**: `.kiro/steering/*.md` — shared with Kiro IDE; always-loaded passive context
- **Custom agents**: ✅ JSON configs (`/agent create`, `kiro-cli agent create`) — the IDE lacks this
- **Lifecycle hooks**: ✅ declared in agent config — `agentSpawn`, `userPromptSubmit`, `preToolUse`,
  `postToolUse`, `stop` (Cursor-like taxonomy; the IDE uses `fileEdited` JSON hooks instead)
- **Slash commands**: ✅ built-ins (`/agent`, `/context`, `/model`, `/prompts`, `/guide`, `/settings`)
- **MCP**: ✅ `.kiro/settings/mcp.json` (migrated from `~/.aws/amazonq/mcp.json`)
- **AWS integration**: Amazon Q / Bedrock model access via AWS credentials

**Migration note**: on install, MCP servers, agents, rules, and prompts are auto-copied from
`~/.aws/amazonq/` into `~/.kiro/` (rules → `~/.kiro/steering/`). When both `.kiro/` and `.amazonq/`
exist in a project, **`.kiro/` wins**.

**gald3r target tier**: CLI agent. Shares `.kiro/` dir + steering with Kiro IDE; agent/hook/command
config is CLI-specific and NOT interchangeable with the IDE skill.

> **Full capability assessment**: see `PLATFORM_SPEC.md` (9 sections, doc-verified May 2026,
> not install-tested — `last_doc_scan: never`).

---

## 2. Config File Layout

```
<project-root>/
└── .kiro/
    ├── steering/                   ← Injected into all Kiro sessions (IDE + CLI)
    │   ├── gald3r.md               ← gald3r task management context
    │   └── product.md              ← Product context
    ├── specs/                      ← Feature specs (shared with IDE)
    └── hooks/                      ← Automation hooks
```

**Same directory as Kiro IDE** — if you have `g-skl-platform-kiro` set up, Kiro-CLI shares the same config.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only kiro-cli
```

Creates `.kiro/steering/gald3r.md` (same file as Kiro IDE install; idempotent).

### CLI-Specific Usage

> ⚠️ **Correction**: prior versions of this skill documented `kiro run --steering …` /
> `kiro --no-interactive --spec …`. Those flags were **not found in current Kiro CLI docs** and
> appear to have been invented. The documented entry points are `kiro-cli` and the preserved
> `q` / `q chat`. Steering files are auto-loaded from `.kiro/steering/` — you do not pass them
> per-invocation. ❓ The exact non-interactive/headless flag set is unverified — confirm via
> `@g-platform-scan-docs kiro-cli` before scripting CI.

```bash
# Interactive chat (steering auto-loaded from .kiro/steering/)
kiro-cli
# or the preserved Q Developer CLI entry points:
q chat

# Manage/switch custom agents and inspect loaded context
/agent          # list / switch custom agents (in-session slash command)
/context        # show what steering/context is loaded
```

### CI Integration

❓ Headless/non-interactive invocation for CI is **not yet verified** for the current Kiro CLI.
Do not copy a `kiro run` recipe. Confirm the correct non-interactive flags from
https://kiro.dev/docs/cli/reference/cli-commands/ before wiring a workflow.

---

## 4. Verification

```powershell
kiro-cli --version    # or: q --version  (preserved Q Developer CLI entry point)
Test-Path .kiro/steering/gald3r.md
node bin/install.js --list --target .
```

❓ The exact `--version` flag and debug-output flags are unverified for the current Kiro CLI —
confirm against https://kiro.dev/docs/cli/reference/cli-commands/.

---

## 5. Common Pitfalls

- Kiro CLI and Kiro IDE share `.kiro/steering/` and `.kiro/settings/mcp.json` — installing steering
  for one benefits the other. But **agent/hook/command config is CLI-specific** (JSON agent configs,
  lifecycle hooks) and is NOT the same as the IDE's `.kiro/hooks/*.json` file-event hooks.
- When a project has both `.kiro/` and a legacy `.amazonq/`, **`.kiro/` wins** — config is loaded
  from `.kiro/`.
- On migration from Q Developer CLI, `~/.aws/amazonq/rules/*` files are copied to `~/.kiro/steering/`
  with the same names; check for duplicates if you also author gald3r steering.
- CLI requires AWS credentials for Amazon Q / Bedrock model access.

---

## 6. Known Gaps (vs. Cursor reference, and vs. Kiro IDE)

Honest status — see `PLATFORM_SPEC.md` §9 for full detail. Legend: ✅ working · ⚠️ partial · ❌ absent · ❓ untested.

**Differences from Kiro IDE (`g-skl-platform-kiro`, T1472) — do not conflate the two:**

| Capability | Kiro IDE | Kiro CLI |
|---|---|---|
| Custom agents | ❌ none | ✅ JSON configs (`/agent create`) |
| Hooks | ⚠️ `fileEdited` JSON files in `.kiro/hooks/` | ✅ lifecycle hooks in agent config (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`) |
| Slash commands | ❌ none (spec workflow) | ✅ built-in slash commands |
| Steering / MCP | ✅ shared | ✅ shared |

**Gaps vs. Cursor reference:**

1. **Skills ❌** — no `g-skl-*/SKILL.md` folder-per-skill auto-load. Fold skill knowledge into steering / agent `resources`.
2. **Commands ⚠️** — built-in slash commands exist, but no confirmed user-authored `/g-*` command-file surface; gald3r commands live in steering or as `/prompts`. ❓ verify a custom slash-command path.
3. **Agents ⚠️** — native custom agents are **JSON**, not gald3r `.md`; `g-agnt-*.md` need translation, not a file drop.
4. **Hooks ⚠️** — lifecycle taxonomy maps to Cursor, but hooks are declared **per-agent-config JSON** and receive **JSON via STDIN** (not the PowerShell envelope); adapter required; deny semantics ❓.
5. **Rules ⚠️** — steering has no `alwaysApply`/`globs` per-rule scoping; `.mdc` rules degrade to whole-file always-injected steering.
6. **No top-level instruction file** — uses steering, not `AGENTS.md`/`CLAUDE.md`; gald3r writes `.kiro/steering/gald3r.md`.
7. **SCAN_DOCS not run (❓)** — `last_doc_scan: never`. Confirm exact agent-config dir paths, custom slash-command mechanism, hook field names + deny semantics, MCP timeout, and non-interactive flags via `@g-platform-scan-docs kiro-cli`.

**MCP ✅** is the strongest area (Q Developer CLI lineage; `.kiro/settings/mcp.json` doc-verified).
