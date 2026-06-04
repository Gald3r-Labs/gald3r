---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: kiro-cli
authoring_path: update
docs_url: https://kiro.dev/docs/cli
docs_url_secondary:
  - https://kiro.dev/docs/cli/custom-agents/configuration-reference/
  - https://kiro.dev/docs/cli/hooks/
  - https://kiro.dev/docs/cli/reference/slash-commands/
  - https://kiro.dev/docs/cli/migrating-from-q/
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro-cli/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Kiro CLI (Amazon Q Developer CLI lineage)

Kiro CLI is the **terminal/CLI agent** in the Kiro family. It is the rebrand of the **Amazon Q
Developer CLI** (`q` / `q chat`): Kiro CLI became available 2025-11-17, and on 2025-11-24 the
Q Developer CLI was auto-updated to Kiro CLI for users with auto-update enabled. The `q` and
`q chat` entry points are preserved for backward compatibility. This spec documents Kiro CLI's
actual primitives against the Cursor reference, and **clearly distinguishes it from the Kiro IDE**
(covered by T1472 / `g-skl-platform-kiro`).

> **Authoring path: UPDATE** — `g-skl-platform-kiro-cli/SKILL.md` already ships. This spec records
> the verified-from-docs findings (kiro.dev/docs/cli, May 2026). Install/runtime claims not
> exercised on a live Kiro CLI install remain `❓`.

> **Doc-verified (May 2026), not install-tested.** Folder/format facts below are from the official
> Kiro CLI docs (see Verification Evidence). They have NOT been confirmed by a gald3r install on a
> live Kiro CLI; `last_doc_scan: never` for the formal SCAN_DOCS crawl.

## Kiro CLI vs. Kiro IDE — read this first

Kiro CLI and Kiro IDE share the `.kiro/` namespace and the **steering** context mechanism, but the
CLI has a **richer agent/hook/command surface** than the IDE. Do **not** copy the IDE spec's
"no agents / no commands / file-event hooks" conclusions onto the CLI — they are wrong for the CLI.

| Capability | Kiro IDE (T1472) | Kiro CLI (this spec) |
|---|---|---|
| Custom agents | ❌ no user agent-file mechanism | ✅ JSON custom-agent configs (`/agent`, `kiro-cli agent create`) |
| Slash commands | ❌ no `/g-*` surface (spec workflow only) | ✅ native built-in slash commands (`/agent`, `/context`, `/model`, `/prompts`…) |
| Hooks | ⚠️ file-event JSON hooks (`fileEdited`) | ✅ **lifecycle** hooks in agent config (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`) |
| Steering / rules | ✅ `.kiro/steering/*.md` | ✅ `.kiro/steering/*.md` (shared) |
| MCP | ✅ `.kiro/settings/mcp.json` | ✅ `.kiro/settings/mcp.json` (migrated from `~/.aws/amazonq/mcp.json`) |

The CLI's hook taxonomy (`agentSpawn`, `userPromptSubmit`, `preToolUse`, `postToolUse`, `stop`) is
**much closer to Cursor's lifecycle model** than the IDE's `fileEdited` model — this is the single
most important correction vs. the prior CLI SKILL.md text.

---

## 1. Folder Hierarchy

Kiro CLI reads project-scope config under repo-root `.kiro/`, and user-scope config under
`~/.kiro/`. When both `.kiro/` and a legacy `.amazonq/` exist, **`.kiro/` wins** (config loaded
from `.kiro`). Doc-verified layout:

```
<project-root>/
└── .kiro/
    ├── steering/                   ← always-injected context (markdown), shared with Kiro IDE
    │   ├── product.md
    │   ├── structure.md
    │   ├── tech.md
    │   ├── custom.md               ← auto-loaded custom steering
    │   └── gald3r.md               ← gald3r-authored steering (task-management context)
    ├── settings/
    │   └── mcp.json                ← workspace-scope MCP config
    └── (agent configs may also be project-scoped — see §3)

~/.kiro/                            ← USER/GLOBAL tree (migrated from ~/.aws/amazonq/)
├── steering/                       ← global steering (.md), applies to all projects
├── settings/
│   └── mcp.json                    ← global MCP config (from ~/.aws/amazonq/mcp.json)
└── cli-agents/ (or agent config dir) ← global custom-agent JSON configs ❓ exact dir not verified

<legacy, pre-migration>
~/.aws/amazonq/                     ← OLD Q Developer CLI tree; auto-copied into ~/.kiro/ on install
├── mcp.json
├── rules/                          ← copied to ~/.kiro/steering/ with same names on migration
├── agents/
└── prompts/
```

**Migration fact (doc-verified):** on install, MCP servers, agents, rules, and prompts are
auto-copied from `~/.aws/amazonq/` to the matching `~/.kiro/` locations; `~/.aws/amazonq/rules/*`
land in `~/.kiro/steering/` with the same filenames.

**gald3r writes**: `.kiro/steering/gald3r.md` (context injection); optionally a gald3r custom-agent
JSON config (§3) and `.kiro/settings/mcp.json` (§8).
**Kiro CLI owns**: the `.kiro/` namespace, steering auto-injection, the agent-config schema, the
hook trigger engine, slash-command resolution, and MCP connection lifecycle.

**Correction vs. prior SKILL.md text**: there is no `kiro run --steering` / `--no-interactive`
invocation documented for the current Kiro CLI; the entry points are `kiro-cli` (and the preserved
`q` / `q chat`). The prior SKILL.md's `kiro run …` commands appear to be invented and are flagged
in Known Gaps. ❓ exact non-interactive flag set not verified here.

---

## 2. AI Instruction File

Kiro CLI has **no single top-level instruction file** like `AGENTS.md`/`CLAUDE.md` as its primary
source. Persistent instruction is delivered through **steering files** in `.kiro/steering/*.md`
(§7), auto-loaded into every conversation. gald3r therefore writes `.kiro/steering/gald3r.md`
rather than a `KIRO.md` root file. A custom-agent config can additionally pin specific steering
files via `resources` (e.g. `file://.kiro/steering/**/*.md`). ❓ whether a root `AGENTS.md` is read
by Kiro CLI was not verified (the IDE does not treat it as primary; assume the same for CLI until
confirmed).

---

## 3. Agents Support

- **Native concept (CLI)**: ✅ Kiro CLI **does** support user-authored **custom agents**, defined
  as **JSON configuration files**. Created via the `/agent create` slash command or the
  `kiro-cli agent create` CLI command (the two share some flags; others are slash-only).
- **Config fields (doc-verified)**: `name`, `description`, `tools`, `allowedTools`, `resources`
  (e.g. `"file://.kiro/steering/**/*.md"`), and a `hooks` field (see §6).
- **Discovery/loading**: agents are selected by name (`/agent` to list/switch). ❓ the exact
  project-vs-global agent config directory paths were not exhaustively verified in this pass.
- **gald3r mapping**: gald3r's `g-agnt-*.md` markdown agents are **not** directly portable — Kiro
  CLI agents are JSON, not the Cursor `.md` agent format. A gald3r adapter would translate role
  intent into a Kiro CLI agent JSON (pinning steering via `resources`) rather than dropping `.md`
  files. This is a real native mechanism (better than IDE), but **not a drop-in** for `g-agnt-*.md`.
- **Status**: ✅ native custom-agent mechanism exists (JSON); ⚠️ format differs from gald3r `.md`
  agents (translation required).

---

## 4. Skills Support

- **Native concept**: ❌ Kiro CLI has no `g-skl-*/SKILL.md` folder-per-skill auto-load mechanism
  equivalent to Cursor's `.cursor/skills/`. No documented "skills" primitive was found for the CLI.
- **Nearest analog**: an agent's `resources` field can pin reference markdown (including steering),
  and `/prompts` provides reusable prompt snippets — but neither is a model-driven skill-relevance
  loader.
- **gald3r mapping**: skill *knowledge* that must be active is folded into steering files; skill
  *procedures* are referenced from steering / agent resources, not auto-loaded as SKILL.md.
- **Status**: ❌ no native SKILL.md discovery.

---

## 5. Commands / Workflows

- **Native concept**: ✅ Kiro CLI has a real **slash-command** surface. Doc-verified built-ins
  include `/agent`, `/model`, `/guide`, `/prompts`, `/context`, `/settings` (and `/agent create`).
- **Custom command files**: ❓ the prior SKILL.md and the Cursor model assume a
  `.cursor/commands/g-*.md`-style user-authored command-file directory. No equivalent
  **user-defined slash-command file** mechanism (a folder where gald3r drops `/g-*` definitions)
  was confirmed for Kiro CLI in this pass — built-in slash commands exist, but a gald3r-authored
  command-file surface is unverified. `/prompts` is the closest reusable-invocation analog.
- **gald3r mapping**: gald3r `g-*` commands do **not** propagate as invokable Kiro CLI slash
  commands today. They are documented in steering for the human to drive, or expressed as `/prompts`
  entries / agent resources. ❓ pending confirmation of a custom slash-command file path.
- **Status**: ⚠️ native built-in slash commands exist (strength), but no confirmed gald3r
  command-file surface — partial parity.

---

## 6. Hooks System

Kiro CLI has a **native lifecycle hook system** — defined in the **agent configuration file**
(not standalone `.kiro/hooks/*.json` IDE files). This is the closest CLI parity to Cursor's
`hooks.json`. Doc-verified hook trigger points:

| Hook type | Fires |
|---|---|
| `agentSpawn` | when an agent session starts (≈ Cursor `sessionStart`) |
| `userPromptSubmit` | when the user submits a prompt |
| `preToolUse` | before a tool runs (≈ Cursor `preToolUse`) |
| `postToolUse` | after a tool runs |
| `stop` | when the agent session ends (≈ Cursor `stop`) |

- **Format**: hooks are an array under the `hooks` field of an agent JSON config. Each hook
  specifies a command to run at a trigger point. (Full syntax: Agent Configuration Reference.)
- **Event payload (doc-verified)**: hooks receive the event as **JSON via STDIN**, with fields
  including `hook_event_name`, `cwd`, and `session_id`. This is a different transport from Cursor's
  PowerShell `{ continue = true }` envelope, but the **lifecycle taxonomy maps well**.
- **gald3r mapping**: gald3r's PowerShell lifecycle hooks have **strong conceptual mapping** here:
  `g-hk-session-start` → `agentSpawn`; `g-hk-agent-complete`/`g-hk-session-end` → `stop`;
  preToolUse guards → `preToolUse`. The hook scripts themselves are reusable (they read STDIN /
  env), but **wiring is per-agent-config JSON**, not a central `hooks.json`, and the STDIN JSON
  shape differs — adapter work required. ❓ exact `command`/matcher field names and the blocking
  semantics (how a hook denies a tool) not verified in this pass.
- **Status**: ⚠️ native lifecycle hook system present with a Cursor-like event taxonomy — much
  stronger than the Kiro IDE, but wiring/transport differs (per-agent JSON, STDIN payload), so it
  is partial, not drop-in.

---

## 7. Rules / Memory

- **Mechanism**: **steering files** — markdown in `.kiro/steering/` (project) and
  `~/.kiro/steering/` (global), auto-loaded as passive context into every conversation. Migrated
  `~/.aws/amazonq/rules/*` files land here.
- **Extension**: plain **`.md`** (no `.mdc`).
- **Conventional steering**: `product.md`, `structure.md`, `tech.md`, `custom.md` auto-load.
- **Always-apply vs. scoped**: steering is described as always-injected passive context. ❓ no
  per-rule `alwaysApply`/`globs` frontmatter scoping like Cursor's `.mdc` was found; an agent's
  `resources` glob (`file://.kiro/steering/**/*.md`) is the nearest scoping lever (per-agent, not
  per-rule).
- **gald3r mapping**: gald3r `g-rl-*.mdc` rules do not propagate as individually scoped rules.
  Their content must be consolidated into steering `.md` file(s). Lossy (no per-rule glob scoping).
- **Status**: ✅ native persistent-context mechanism (steering); ⚠️ no per-rule scoping.

---

## 8. MCP Support

- **Supported**: ✅ Yes (doc-verified). Kiro CLI carries forward the full Q Developer CLI MCP
  capability (agent mode, MCP, steering, custom agents).
- **Config format/location**: JSON `mcpServers` object at `.kiro/settings/mcp.json` (workspace) and
  `~/.kiro/settings/mcp.json` (global). On migration, `~/.aws/amazonq/mcp.json` is copied to
  `~/.kiro/settings/mcp.json`.
- **Server discovery**: read on startup; servers can also be managed via slash/CLI commands. AWS
  also publishes MCP governance controls for Q Developer (org-level allow/deny).
- **Timeout behavior**: ❓ not documented in the pages crawled.
- **Status**: ✅ verified (config format from docs); active server set / runtime untested on a live
  install.

---

## 9. Known Gaps vs. Cursor Reference (and vs. Kiro IDE)

Honest list of Cursor-reference features that do NOT work, are partial, or are untested on Kiro CLI:

1. **No SKILL.md discovery (❌)** — no `.cursor/skills/`-style folder-per-skill auto-load. Skill
   knowledge must be folded into steering / agent `resources`.
2. **No confirmed gald3r command-file surface (⚠️)** — built-in slash commands exist (`/agent`,
   `/context`, `/model`, `/prompts`, …), but a user-authored `/g-*` command-file directory was not
   confirmed. gald3r commands are documented in steering or expressed as `/prompts`. ❓ verify a
   custom slash-command file path on the next crawl.
3. **Agents are JSON, not `.md` (⚠️)** — Kiro CLI custom agents exist (a CLI strength the IDE
   lacks) but use a JSON schema; gald3r `g-agnt-*.md` files require translation, not a file drop.
4. **Hook wiring/transport differs (⚠️)** — lifecycle taxonomy (`agentSpawn`/`userPromptSubmit`/
   `preToolUse`/`postToolUse`/`stop`) maps well to Cursor, but hooks are declared **per-agent-config
   JSON** (not a central `hooks.json`) and receive **JSON via STDIN** (not the PowerShell envelope).
   Adapter required; blocking/deny semantics ❓ unverified.
5. **No per-rule scoping (⚠️)** — steering has no `alwaysApply`/`globs` frontmatter; gald3r `.mdc`
   per-rule glob scoping degrades to whole-file always-injected steering content.
6. **No top-level instruction file** — Kiro CLI uses steering, not `AGENTS.md`/`CLAUDE.md`; gald3r
   writes `.kiro/steering/gald3r.md`.
7. **Differs from Kiro IDE (T1472)** — the CLI has **more** native surface than the IDE: the IDE
   has no custom agents and uses `fileEdited` JSON hooks under `.kiro/hooks/`; the CLI has JSON
   custom agents and **lifecycle** hooks declared in agent config. Steering + MCP are shared. The
   `.kiro/` directory is shared (`.kiro/` wins over legacy `.amazonq/`), but the agent/hook/command
   conclusions are NOT interchangeable between the two skills.
8. **Prior SKILL.md invented `kiro run …` commands (⚠️)** — the documented entry points are
   `kiro-cli` and the preserved `q` / `q chat`; `kiro run --steering` / `--no-interactive` /
   `--spec` were not found in current docs and are flagged for correction.
9. **SCAN_DOCS not yet run (❓)** — `last_doc_scan: never`. Folder/format claims are from a
   May-2026 manual doc read of kiro.dev/docs/cli, not the formal `@g-platform-scan-docs kiro-cli`
   crawl. Confirm: exact agent-config directory paths, custom slash-command file mechanism (if any),
   hook field names + deny semantics, MCP timeout, and non-interactive flag set.
10. **Decision-tree placement** — Kiro CLI's JSON agent/hook schema and steering format are
    correctly classified as **platform-specific** (live in the `.kiro/` tree / a
    `.gald3r_sys/platforms/.kiro-cli/` adapter), not common `.gald3r_sys/`.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ⚠️**: native **lifecycle** hooks (`agentSpawn`/`userPromptSubmit`/`preToolUse`/
  `postToolUse`/`stop`) — Cursor-like taxonomy, but per-agent-JSON wiring + STDIN payload (adapter).
- **Rules ⚠️**: steering provides persistent context but no per-rule glob scoping.
- **Skills ❌**: no SKILL.md discovery mechanism.
- **Commands ⚠️**: built-in slash commands exist; no confirmed gald3r command-file surface.
- **MCP ✅**: `.kiro/settings/mcp.json` format doc-verified (Q Developer CLI lineage).
- **Docs Fresh ❓**: `last_doc_scan: never` — flip to ✅ after the first SCAN_DOCS crawl.

> Note vs. Kiro IDE row: CLI Hooks/Commands are also ⚠️ but for **opposite reasons** — the CLI is
> *stronger* (lifecycle hooks, custom agents, built-in slash commands) yet still partial for gald3r
> due to JSON/format translation, whereas the IDE is partial due to *missing* primitives.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Q Developer CLI → Kiro CLI rebrand (dates, `q`/`q chat` preserved) | kiro.dev/docs/cli/migrating-from-q + AWS DevOps blog — May 2026 doc read |
| Migration auto-copy (`~/.aws/amazonq/` → `~/.kiro/`; rules → steering; mcp.json → settings/mcp.json) | kiro.dev/docs/cli/migrating-from-q — doc-verified |
| `.kiro/` wins over `.amazonq/` when both present | kiro.dev/docs/cli/migrating-from-q — doc-verified |
| Custom agents = JSON config (`name`/`tools`/`allowedTools`/`resources`/`hooks`); `/agent create` | kiro.dev/docs/cli/custom-agents (creating + configuration-reference) — doc-verified |
| Hook lifecycle types (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`); JSON via STDIN (`hook_event_name`/`cwd`/`session_id`) | kiro.dev/docs/cli/hooks + configuration-reference — doc-verified |
| Built-in slash commands (`/agent`/`/model`/`/guide`/`/prompts`/`/context`/`/settings`) | kiro.dev/docs/cli/reference/slash-commands — doc-verified |
| Steering files (`.kiro/steering/*.md`, product/structure/tech/custom auto-load) | kiro.dev/docs/cli + paulsnider.net features guide — doc-verified |
| MCP (`.kiro/settings/mcp.json`, Q Developer lineage, governance) | docs.aws.amazon.com Q Developer MCP governance + migration docs — doc-verified |
| Custom slash-command file surface / exact agent-config dir paths | ❓ NOT confirmed — pending SCAN_DOCS crawl |
| Install / runtime behavior (`node bin/install.js --only kiro-cli`) | ❓ NOT exercised on a live Kiro CLI install |
| Docs freshness | Not formally crawled — `last_doc_scan: never`; pending `@g-platform-scan-docs kiro-cli` |
