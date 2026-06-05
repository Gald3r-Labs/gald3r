---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: openhands
authoring_path: update
docs_url: https://docs.openhands.dev
docs_url_secondary:
  - https://docs.openhands.dev/sdk/guides/plugins
  - https://docs.openhands.dev/sdk/guides/skill.md
  - https://docs.openhands.dev/sdk/guides/agent-file-based.md
  - https://docs.openhands.dev/openhands/usage/customization/hooks
  - https://docs.openhands.dev/openhands/usage/settings/mcp-settings
  - https://docs.openhands.dev/overview/skills/repo.md
crawl_max_age_days: 14
vault_doc_path: research/platforms/openhands/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — OpenHands (All Hands AI, formerly OpenDevin)

OpenHands ships as a composable **Software Agent SDK (V1)** plus **CLI / GUI / Cloud / Enterprise**
surfaces, all driven by the same file-based extension config. As of mid-2026 OpenHands natively
supports **all six** gald3r-relevant extension primitives — custom slash commands, rules/context,
agents/subagents, Agent Skills, lifecycle hooks, and MCP — and bundles them through a single
redistributable **Plugin** unit. Critically for gald3r, OpenHands uses **`AGENTS.md`** as the
always-on instruction file (it does **not** require a `CLAUDE.md`, though `CLAUDE.md` / `GEMINI.md`
are recognized as variants), follows the **extended AgentSkills `SKILL.md` standard**, and accepts
gald3r's `.claude/skills/` tree under its compatibility notes — so gald3r's Agent-Skills artifacts
are **largely drop-in reusable**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.openhands.dev (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: 2026-05-26`, which
incorrectly marked hooks/commands as ❌ and skills/rules/MCP as ⚠️ on a Docker-sandbox framing) —
every mechanism is now confirmed **NATIVE** on OpenHands V1.

> **Surface split:** the same extension config (`.agents/` tree, `.openhands/hooks.json`,
> `config.toml [mcp]`, plugins) applies uniformly across **CLI, local GUI, Cloud, and Enterprise**.
> OpenHands is also exposed as an **ACP agent** (Zed) and is delegatable from other agents (e.g.
> Hermes). The deepest extensibility (programmatic `register_agent()` factories, custom tools and
> visualizers, the `AgentFactory` registry) is **SDK/Python-level** rather than file-declarative —
> noted inline where a capability is code-only.

> **Directory migration (important):** OpenHands is mid-migration from the legacy `.openhands/`
> tree to the modern **`.agents/`** tree. `.agents/` is the **recommended** target;
> `.openhands/skills/` and `.openhands/microagents/` are **deprecated** but still honored by older
> OpenHands versions in the wild. gald3r installs should write the **new `.agents/` tree**.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                        ← always-on instruction file OpenHands reads (NOT CLAUDE.md)
│                                       (CLAUDE.md / GEMINI.md recognized as variants)
├── config.toml                      ← [mcp] sse_servers / shttp_servers (+ stdio)
├── .agents/                         ← RECOMMENDED modern tree
│   ├── skills/   <name>/SKILL.md    ← Agent Skills (extended AgentSkills standard)
│   └── agents/   *.md               ← File-Based Agents (markdown + YAML frontmatter)
├── .openhands/                      ← legacy / config-side tree (still honored)
│   ├── hooks.json                   ← lifecycle event hooks
│   ├── skills/                      ← DEPRECATED skills location
│   ├── agents/                      ← agents (priority 2, after .agents/agents/)
│   └── microagents/  repo.md        ← DEPRECATED always-on rules (legacy)
└── .plugin/
    └── plugin.json                  ← Plugin manifest — bundles skills/hooks/agents/commands/MCP
```

User-level mirrors exist at `~/.agents/` and `~/.openhands/`; **project scope takes precedence over
user scope**.

**gald3r writes**: the `.agents/` tree (`skills/`, `agents/`), `AGENTS.md`, `.openhands/hooks.json`,
and `config.toml [mcp]` — or a single **Plugin** bundle carrying all of them.
**OpenHands owns**: the `.openhands/` legacy namespace, the `config.toml` schema, and the
SDK-level `AgentFactory` / custom-tool registry (a code surface, not a gald3r-writable file store).

---

## 2. AI Instruction File

OpenHands reads a repository-root **`AGENTS.md`** as **always-on context injected into the system
prompt at conversation start** — the preferred file for repository-wide, always-on instructions.
**`GEMINI.md` and `CLAUDE.md` are recognized as model-specific variants.** The legacy
`.openhands/microagents/repo.md` serves the same always-on role (deprecated). "General Skills"
(no-frontmatter / `trigger=None`) are also loaded continuously as part of context.

> gald3r note: write **`AGENTS.md`** as the canonical instruction file. Unlike Augment, OpenHands
> does **not** require a `CLAUDE.md` — `AGENTS.md` is first-class and is the documented default.

---

## 3. Agents Support — ✅ NATIVE

- **File-Based Agents**: markdown + YAML frontmatter (`name`, `description`, `tools`,
  `model: inherit`) loaded from `{project}/.agents/agents/*.md` (priority 1) or
  `.openhands/agents/*.md` (priority 2); registered via `register_file_agents()`. Closest analog to
  Claude Code subagents.
- **Sub-Agent Delegation**: hierarchical parallel sub-agents spawned via `DelegateTool`
  (`{"command": "spawn", "ids": [...]}`); roles such as research / implementation / testing. A
  built-in **`explore`** subagent exists.
- **Code path (SDK)**: programmatic `register_agent()` factories via the `AgentFactory` registry —
  required for advanced multi-agent orchestration beyond the declarative markdown files.
- gald3r `g-agnt-*` definitions map directly to File-Based Agent files (`.agents/agents/*.md`).
- Source: https://docs.openhands.dev/sdk/guides/agent-file-based.md

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** on the **extended AgentSkills standard**: `<name>/SKILL.md` with a `scripts/` +
  `references/` + `assets/` layout, recommended under **`.agents/skills/`**. Frontmatter: `name`,
  `description`, `triggers`, `license`, `compatibility`, `metadata`.
- **Three invocation modes**: keyword `triggers:` (frontmatter), agent-mediated `invoke_skill()`,
  and always-on (`trigger=None` / no frontmatter). Every skill is also invocable as a slash command
  (`/skill-name`).
- **Loading priority**: `.agents/skills/` (recommended) > `.openhands/skills/` (deprecated) >
  `.openhands/microagents/` (deprecated). **`.claude/skills/` is also accepted** per plugin/skill
  compatibility notes.
- gald3r `g-skl-*/SKILL.md` load natively — the directory layout already matches the AgentSkills
  convention, giving strong cross-tool portability (TRAE, CodeBuddy, etc.).
- Source: https://docs.openhands.dev/sdk/guides/skill.md

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands** ship two ways: (1) **Plugin `commands/<name>.md`** files, and
  (2) **Agent Skills exposed as `/skill-name`** (e.g. a skill named `random-number` is invocable as
  `/random-number`). A **slash-command menu** listing skills and commands was added to the chat
  input (May 2026 product update).
- The CLI command-reference page documents only **built-in** commands (`/help`, `/new`, `/skills`,
  etc.) and does **not** define a standalone per-repo custom-command file — so the user-defined path
  is primarily **Skills + Plugins**, not a first-class `.commands/` directory.
- gald3r `@g-*` / `/g-*` commands map via skills-as-commands and/or a Plugin `commands/` bundle.
- Source: https://docs.openhands.dev/sdk/guides/plugins

## 6. Hooks System — ✅ NATIVE

- **Lifecycle event hooks** configured per-repo in **`.openhands/hooks.json`** (also bundleable via
  a Plugin's `hooks/hooks.json`). **Six event types**: **PreToolUse, PostToolUse, UserPromptSubmit,
  Stop, SessionStart, SessionEnd**. Each hook runs a **shell command** with a `timeout` and a
  `matcher` (tool name or `*`).
- **Event payload**: JSON on **stdin** (`event_type`, `tool_name`, `tool_input`, `session_id`,
  `working_dir`); a hook can **block** by returning `{"decision": "deny", "reason",
  "additionalContext"}`.
- Works across **Cloud, CLI, and local GUI** — a true deterministic control layer comparable to
  Claude Code hooks (block dangerous commands on PreToolUse, enforce tests/lint before Stop, inject
  context on SessionStart). gald3r `g-hk-*` hooks wire natively; invoke a `.ps1` via a shell wrapper
  (e.g. `pwsh -File ...`) since hooks are shell-command based.
- Source: https://docs.openhands.dev/openhands/usage/customization/hooks

## 7. Rules / Context — ✅ NATIVE

- Always-on context is **`AGENTS.md`** (repo root, injected at conversation start) plus
  **"General Skills"** — no-frontmatter / `trigger=None` microagents loaded continuously.
  `GEMINI.md` / `CLAUDE.md` variants are recognized; legacy `.openhands/microagents/repo.md` serves
  the same role (deprecated).
- gald3r `g-rl-*` always-apply rules map to `AGENTS.md` content (or to General Skills for modular,
  always-loaded rule fragments). No `.mdc` per-rule `globs:` engine exists — the split is binary:
  always-on (`AGENTS.md` / General Skills) vs. keyword-triggered (`triggers:` skills).
- Source: https://docs.openhands.dev/overview/skills/repo.md

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol** with **three transports — stdio, SSE, and SHTTP (Streamable HTTP)** —
  configured via `config.toml` `[mcp]` (`sse_servers = [...]`, `shttp_servers = [...]`), the
  **Settings > MCP** UI, or a Plugin's `.mcp.json`. Entries may be string URLs or objects with
  `url` / `api_key` / `timeout`.
- **Per-tool timeouts** (1–3600s), **API-key and OAuth** auth (OAuth-protected servers such as
  Notion via the FastMCP library). A proxy (e.g. **SuperGateway**) is recommended over direct stdio
  for reliability.
- Source: https://docs.openhands.dev/openhands/usage/settings/mcp-settings

## 9. Plugins / Extensions Registry — distribution channel

- **Plugins are the headline distribution unit**: one bundle carries **skills + hooks + MCP servers
  + agents + commands** together. Layout: `.plugin/plugin.json` (required), `skills/<name>/SKILL.md`,
  `hooks/hooks.json`, `agents/<name>.md`, `commands/<name>.md`, `.mcp.json`, `README.md`. A public
  **extensions registry** (`github.com/OpenHands/extensions`) and a **Cloud Plugin Launcher** exist.
- This single mechanism is the **ideal gald3r packaging target** — one OpenHands Plugin can ship the
  entire gald3r primitive set.
- Source: https://docs.openhands.dev/sdk/guides/plugins

---

## Parity vs. Cursor Reference

OpenHands reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Caveats: (1) user-defined slash commands have
**no first-class standalone file** outside Plugins/Skills (`/skill-name` + Plugin `commands/` cover
it, and the slash-menu surfacing only landed May 2026); (2) the **richer agent capabilities**
(programmatic `register_agent()`, `DelegateTool` parallel orchestration, custom tools/visualizers)
are **SDK/Python-level**, not file-declarative; (3) directory conventions are **mid-migration**
(`.agents/` recommended vs deprecated `.openhands/skills|microagents`).

**Reuse note (important):** OpenHands reads `AGENTS.md`, follows the AgentSkills `SKILL.md`
standard, and accepts `.claude/skills/` — so gald3r's Agent-Skills artifacts are **largely reusable
without a separate port**. The cheapest high-parity install is to write the `.agents/` tree (skills
+ agents) + `AGENTS.md` + `.openhands/hooks.json` + `config.toml [mcp]`, or ship a single Plugin
bundle.

## Hook System

- **Type**: native (lifecycle event hooks)
- **Config file**: `.openhands/hooks.json` (or Plugin `hooks/hooks.json`)
- **Events available**: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SessionStart, SessionEnd
- **Event payload format**: JSON via **stdin** (`event_type`, `tool_name`, `tool_input`,
  `session_id`, `working_dir`); block via `{"decision": "deny", "reason", "additionalContext"}`
- **Command extensions**: shell command + `timeout` + `matcher`; gald3r `.ps1` runs via a shell
  wrapper (`pwsh -File ...`)
- **Surfaces**: Cloud, CLI, local GUI

## Atypical Handling

- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** — write `AGENTS.md` as canonical;
  `CLAUDE.md` / `GEMINI.md` are recognized variants, not requirements.
- **Directory migration**: target the modern **`.agents/`** tree; `.openhands/skills/` and
  `.openhands/microagents/` are deprecated (still honored by older versions).
- **Commands are not a first-class file** — deliver via Skills-as-commands (`/skill-name`) and/or a
  Plugin `commands/` directory.
- **Advanced agents are code-only** — file-based agents cover the basics; multi-agent roles via
  `DelegateTool` / `register_agent()` require Python.
- **Hooks are shell-command based** — JSON config, stdin payload; wrap `.ps1` hooks in `pwsh`.

## gald3r Integration Notes

- Ship the **`.agents/`** tree (skills + agents) + **`AGENTS.md`** — OpenHands discovers it; or
  package a single **Plugin** bundle (skills + hooks + agents + commands + MCP) for the registry /
  Cloud Plugin Launcher.
- Skills load natively (AgentSkills `SKILL.md`); `.claude/skills/` is accepted per compatibility
  notes, so gald3r's Agent-Skills are largely reusable.
- Hooks fire natively via `.openhands/hooks.json` (stdin JSON, deny decisions) — wire SessionStart
  context injection, PreToolUse `.gald3r/` guards, and pre-Stop test/lint gates.
- Re-verify on the next `@g-platform-scan-docs openhands` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.openhands.dev)

| Capability | How verified |
|---|---|
| Commands | /sdk/guides/plugins — Plugin `commands/<name>.md`; Agent Skills invocable as `/skill-name`; slash-command menu added May 2026. No standalone per-repo command-file format (CLI ref lists built-ins only) |
| Rules | /overview/skills/repo.md — `AGENTS.md` always-on (injected at conversation start); General Skills loaded continuously; `GEMINI.md` / `CLAUDE.md` variants; legacy `.openhands/microagents/repo.md` |
| Agents | /sdk/guides/agent-file-based.md — File-Based Agents (`name`/`description`/`tools`/`model: inherit`) in `.agents/agents/*.md` (priority 1) / `.openhands/agents/*.md`; `DelegateTool` spawn; built-in `explore`; code `register_agent()` |
| Skills | /sdk/guides/skill.md — extended AgentSkills `SKILL.md` in `.agents/skills/` (> deprecated `.openhands/skills` / `microagents`); triggers / `invoke_skill()` / always-on modes; `.claude/skills/` accepted |
| Hooks | /openhands/usage/customization/hooks — `.openhands/hooks.json`; PreToolUse/PostToolUse/UserPromptSubmit/Stop/SessionStart/SessionEnd; stdin JSON payload; `{"decision":"deny"}` block; Cloud/CLI/GUI |
| MCP | /openhands/usage/settings/mcp-settings — `config.toml [mcp]` sse/shttp + stdio; per-tool timeout (1–3600s); API-key + OAuth (FastMCP); SuperGateway proxy |
| Plugins | /sdk/guides/plugins — `.plugin/plugin.json` bundles skills+hooks+MCP+agents+commands; OpenHands/extensions registry + Cloud Plugin Launcher |
| Instruction file | `AGENTS.md` is the canonical always-on file (NOT CLAUDE.md); `CLAUDE.md` / `GEMINI.md` recognized as variants → gald3r writes `AGENTS.md` |
