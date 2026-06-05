---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: codex
authoring_path: update
docs_url: https://developers.openai.com/codex
docs_url_secondary:
  - https://developers.openai.com/codex/guides/agents-md
  - https://developers.openai.com/codex/cli/slash-commands
  - https://developers.openai.com/codex/subagents
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/codex/hooks
  - https://developers.openai.com/codex/mcp
  - https://developers.openai.com/codex/plugins
  - https://developers.openai.com/codex/config-reference
crawl_max_age_days: 7
vault_doc_path: research/platforms/openai/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1464
---

# PLATFORM_SPEC.md — OpenAI Codex (CLI / IDE / app)

OpenAI Codex ships as the **`codex` CLI**, an IDE integration, and a hosted app, all driven by a
single schema-validated **`config.toml`**. As of mid-2026 Codex natively supports **all six**
gald3r-relevant extension primitives — custom slash commands, rules/memory, subagents, Agent
Skills, lifecycle hooks, and MCP. Critically for gald3r, Codex reads **`AGENTS.md`** (NOT
`CLAUDE.md`) as its instruction file, and discovers skills from the **open Agent Skills standard**
(`.agents/skills/`), so gald3r's `SKILL.md` artifacts are **directly portable** onto Codex.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://developers.openai.com/codex (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which incorrectly
marked hooks/commands as unsupported and rules/skills/MCP as partial — they are now all NATIVE in
Codex. The legacy `codex.config.json` + `suggest`/`auto-edit`/`full-auto` naming is also superseded by
`config.toml` + `approval_policy`/`sandbox_mode`.

> **Surface split:** the full extensibility (commands/rules/agents/skills/hooks/MCP/plugins) is driven
> by **`config.toml`** + filesystem directories, available to the **`codex` CLI**. The IDE/app exposes
> the same config plus an MCP settings panel; where a feature is CLI-centric or has an IDE caveat it is
> noted inline. **OS note:** managed (enterprise) hooks run automatically; non-managed hooks require
> per-user trust before they fire.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                     ← instruction file Codex reads (NOT CLAUDE.md)
├── AGENTS.override.md            ← higher-precedence override (optional)
├── TEAM_GUIDE.md / .agents.md    ← lower-precedence instruction fallbacks
├── .agents/
│   └── skills/   <name>/SKILL.md ← Agent Skills (open standard, shared w/ Claude/others)
└── .codex/
    ├── config.toml               ← model, sandbox/approval, [mcp_servers.*], [hooks], [[skills.config]]
    ├── hooks.json                ← lifecycle hooks (or inline [hooks] in config.toml)
    ├── agents/    *.toml         ← subagents (standalone TOML files)
    └── prompts/   *.md           ← Custom Prompts → slash commands (DEPRECATED; use skills)

~/.codex/                         ← personal/global tree (merged below project; less specific loses)
├── AGENTS.md                     ← global instruction file
├── config.toml                   ← global config
├── agents/    *.toml             ← personal subagents
├── memories/                     ← persistent Memories injected into future sessions
└── prompts/   *.md               ← personal Custom Prompts (DEPRECATED)

$HOME/.agents/skills/             ← personal Agent Skills
```

Codex resolves config and instructions **most-specific-wins** (project `.codex/` over `~/.codex/`;
nested `AGENTS.md` over repo root over global). gald3r's open-standard `.agents/skills/SKILL.md`
load on Codex with **no Codex-specific port**.

**gald3r writes**: `AGENTS.md`, `.agents/skills/g-skl-*/`, `.codex/config.toml`,
`.codex/hooks.json` (or inline `[hooks]`), `.codex/agents/*.toml`.
**Codex owns**: the `config.toml`/`hooks.json` schemas, `~/.codex/` global state, sandbox internals,
auth/session state, and the `execpolicy` hard allow/block layer.

---

## 2. AI Instruction File

Codex reads **`AGENTS.md`** automatically at session start before any work begins. Per-directory
lookup order is `AGENTS.override.md` → `AGENTS.md` → `TEAM_GUIDE.md` → `.agents.md`. Resolution
walks global `~/.codex/AGENTS.md` → repo root `AGENTS.md` → nested directory `AGENTS.md`, with
**more specific winning**. No `CODEX.md` is required and **`CLAUDE.md` is NOT read** — gald3r's
`AGENTS.md` is the first-class, always-apply instruction surface. Source:
https://developers.openai.com/codex/guides/agents-md

---

## 3. Agents Support — ✅ NATIVE

- **Subagents / custom agents**: standalone **TOML** files under `.codex/agents/` (project) or
  `~/.codex/agents/` (personal). Required keys: `name`, `description`, `developer_instructions`;
  optional `model`, `sandbox_mode`, `mcp_servers`, `skills.config`. Built-in agents: `default`,
  `worker`, `explorer`. Managed via the `/agent` slash command.
- Codex spawns specialized agents **in parallel** and collects results into one response — but
  subagents are **NOT auto-spawned**: they run only on explicit user request (natural language or
  `/agent`).
- gald3r `g-agnt-*` definitions map to Codex `.codex/agents/*.toml` files (TOML, not the markdown+YAML
  used elsewhere — parity sync emits the TOML form).
- Source: https://developers.openai.com/codex/subagents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (open `SKILL.md` standard) discovered in **`.agents/skills/`** from CWD up to repo
  root, plus user/admin/system locations and **`$HOME/.agents/skills/`** (personal). A skill is a
  directory with a `SKILL.md` plus optional scripts/references. Frontmatter requires `name` and
  `description`.
- Invoked **explicitly** (`/skills` or a `$`-mention) or **implicitly** when a task matches the skill
  description.
- Uses the **same open Agent Skills standard shared with Claude and other tools** — gald3r
  `g-skl-*/SKILL.md` load natively, directly from `.agents/skills/`, with no Codex-specific port.
- Source: https://developers.openai.com/codex/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Built-in slash commands**: ~40 ship with the CLI (e.g. `/init`, `/review`, `/agent`, `/skills`,
  `/mcp`, `/plugins`, `/apps`), typed via `/`.
- **User-defined commands**: historically authored as **Custom Prompts** (`~/.codex/prompts/*.md` or
  `.codex/prompts/*.md`, invoked as slash commands with `$1..$9` and named placeholders). **Custom
  Prompts are DEPRECATED** — OpenAI directs reusable invocable workflows to **skills** instead.
- gald3r `@g-*` / `/g-*` workflows map to skills (preferred) and/or built-in slash commands; the
  legacy prompts path still works but should not be the target.
- Source: https://developers.openai.com/codex/cli/slash-commands

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** inject custom scripts into the agentic loop, configured via **`hooks.json`** or
  inline **`[hooks]`** tables in `config.toml` (under `~/.codex/` or project `.codex/`). Each hook
  declares an event type, an optional **regex matcher**, and command handlers.
- **Ten events**: `SessionStart`, `SubagentStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`,
  `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`. This is a notably **deep**
  hook surface — well beyond typical competitor sets — covering session lifecycle, pre/post tool,
  permission, compaction, prompt submit, and subagent lifecycle.
- **Trust model**: managed (enterprise) hooks run automatically; non-managed hooks require explicit
  user trust before firing.
- gald3r `g-hk-*.ps1` hooks wire natively — `SessionStart` context injection, `PreToolUse` `.gald3r/`
  guards, `Stop`/`PostToolUse` checks, etc. (Handler invocation is via the configured `command`;
  ensure the handler shells `pwsh`/`powershell` for `.ps1` on the host OS.)
- Source: https://developers.openai.com/codex/hooks

## 7. Rules / Memory — ✅ NATIVE

- **AGENTS.md instruction hierarchy** carries always-on rules (test commands, paths to avoid, commit
  conventions) and is read automatically at session start.
- **Memories**: persistent context under `~/.codex/memories/`, injected into future sessions
  (`memories.use_memories`).
- **execpolicy**: rule files defining **enforced** hard allow/block policies for commands — the hard
  guardrail layer beneath the prose instructions.
- gald3r `g-rl-*` always-apply rules fold into `AGENTS.md`; hard `.gald3r/`/secret guards can also be
  expressed as `execpolicy` rules and/or `PreToolUse` hooks.
- Source: https://developers.openai.com/codex/guides/agents-md

## 8. MCP Support — ✅ NATIVE

- MCP servers configured via **`[mcp_servers.<name>]`** tables in `config.toml`. Supports **stdio**
  (`command`, `args`, `env_vars`) and **HTTP** (`bearer_token_env_var`, `http_headers`) servers, plus
  `default_tools_approval_mode` (`auto`/`prompt`/`approve`) and per-tool `approval_mode` overrides.
- Managed via **`codex mcp add`** (or editing `~/.codex/config.toml`); the IDE exposes an MCP settings
  panel; **`/mcp`** lists servers.
- Source: https://developers.openai.com/codex/mcp

## 9. Plugins / Apps — distribution channels

- **Codex Plugins**: a documented plugin system for packaging extensions, managed via the
  **`/plugins`** slash command (overview + build guide). The natural distribution channel for a
  bundled gald3r Codex extension. Source: https://developers.openai.com/codex/plugins
- **Codex Apps**: installable apps surfaced via **`/apps`**, an extensibility surface alongside
  plugins and MCP. Source: https://developers.openai.com/codex/cli/slash-commands

---

## Parity vs. Cursor Reference

Codex reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP** — a 1:1 map onto every gald3r extension primitive.
Codex's hook surface (10 lifecycle events) is **deeper** than Cursor's, and `execpolicy` adds an
enforced hard allow/block layer with no direct Cursor analog. Caveats: subagents are **not
auto-spawned** (explicit `/agent`/NL only), agents are authored as **TOML** (not markdown+YAML), and
**Custom Prompts are deprecated** in favor of skills for user-defined commands.

**Reuse note (important):** Codex skills use the **same open Agent Skills `SKILL.md` standard** and
`.agents/skills/` directory as Claude and other tools, so gald3r's skill artifacts are directly
portable. The instruction file is **`AGENTS.md` (not `CLAUDE.md`)** — ship the `AGENTS.md` form.

## Hook System

- **Type**: native (`hooks.json` or inline `[hooks]` in `config.toml`)
- **Config file**: `.codex/hooks.json` or `[hooks]` in `~/.codex/config.toml` / `.codex/config.toml`
- **Events available**: SessionStart, SubagentStart, PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop (10)
- **Event payload format**: event type + optional regex matcher routes to command handlers
- **Command extensions**: any executable command (shell `pwsh`/`powershell` for `g-hk-*.ps1`)
- **Trust model**: managed/enterprise hooks auto-run; non-managed hooks require user trust
- **gald3r hook files**: `g-hk-*.ps1` wire natively via the events above (SessionStart, PreToolUse, Stop, etc.)

## Atypical Handling

- Two-tier config: project `.codex/config.toml` merges below `~/.codex/config.toml` (most-specific-wins).
- Instruction file is **`AGENTS.md`, not `CLAUDE.md`** — plus `AGENTS.override.md` / `TEAM_GUIDE.md` / `.agents.md` fallbacks and a global `~/.codex/AGENTS.md`.
- Subagents are authored as standalone **TOML** files and are **explicit-spawn only** (never auto-spawned).
- User-defined commands via **Custom Prompts are DEPRECATED** — use skills for reusable invocable workflows.
- Shell execution is additionally gated by `approval_policy` + `sandbox_mode` and the `execpolicy` hard layer, alongside `PreToolUse`/`PermissionRequest` hooks.

## gald3r Integration Notes

- Ship gald3r's open-standard `.agents/skills/g-skl-*/SKILL.md` tree — Codex discovers it natively.
- Author the instruction surface as **`AGENTS.md`** (not `CLAUDE.md`); fold `g-rl-*` always-apply rules in.
- Map `g-agnt-*` to `.codex/agents/*.toml`; remember subagents need explicit `/agent`/NL invocation.
- Hooks fire natively (`g-hk-*.ps1` via configured command handlers across the 10 events); no need to degrade session-start/pre-commit to manual.
- Prefer skills over Custom Prompts for user-defined `@g-*` workflows (prompts are deprecated).
- Re-verify on the next `@g-platform-scan-docs codex` (crawl_max_age_days: 7).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://developers.openai.com/codex)

| Capability | How verified |
|---|---|
| Instruction file | /codex/guides/agents-md — reads `AGENTS.md` (not `CLAUDE.md`); order AGENTS.override.md/AGENTS.md/TEAM_GUIDE.md/.agents.md; global `~/.codex/AGENTS.md`, most-specific-wins |
| Commands | /codex/cli/slash-commands — ~40 built-in slash commands; Custom Prompts (`~/.codex/prompts/`) deprecated → skills |
| Rules | /codex/guides/agents-md — AGENTS.md always-on rules + Memories (`~/.codex/memories/`) + execpolicy hard allow/block |
| Agents | /codex/subagents — standalone TOML in `.codex/agents/` (`name`/`description`/`developer_instructions`); parallel; explicit-spawn only; `/agent` |
| Skills | /codex/skills — open Agent Skills `SKILL.md` in `.agents/skills/` (repo) + `$HOME/.agents/skills/`; `/skills` or `$`-mention; shared standard |
| Hooks | /codex/hooks — `hooks.json` or inline `[hooks]`; 10 events (SessionStart…Stop); regex matchers; managed auto / non-managed trust |
| MCP | /codex/mcp — `[mcp_servers.<name>]` in config.toml (stdio + HTTP); `codex mcp add`; `/mcp`; approval modes |
| Plugins / Apps | /codex/plugins + /codex/cli/slash-commands — `/plugins` packaging system; `/apps` installable apps |
| Config | /codex/config-reference — central `config.toml` (global `~/.codex/` + project `.codex/`) governs model, sandbox/approval, MCP, hooks, agent overrides |
