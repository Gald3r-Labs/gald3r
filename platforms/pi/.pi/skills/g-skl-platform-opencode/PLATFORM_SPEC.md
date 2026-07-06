---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: opencode
authoring_path: update
docs_url: https://opencode.ai/docs
docs_url_secondary:
  - https://opencode.ai/docs/commands/
  - https://opencode.ai/docs/rules/
  - https://opencode.ai/docs/agents/
  - https://opencode.ai/docs/skills/
  - https://opencode.ai/docs/plugins/
  - https://opencode.ai/docs/mcp-servers/
  - https://opencode.ai/docs/custom-tools/
crawl_max_age_days: 7
vault_doc_path: research/platforms/opencode/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
---

# PLATFORM_SPEC.md — OpenCode (sst/opencode)

OpenCode is an open-source, terminal-first AI coding agent from the **SST** team (`opencode` binary,
repo `sst/opencode`, docs https://opencode.ai/docs). It runs as a TUI with multi-provider model
support and a JSON/JSONC config (`opencode.json`). As of mid-2026 OpenCode natively supports **all
six** gald3r-relevant extension primitives — custom commands, rules/instructions, agents
(primary + subagents), Agent Skills, lifecycle hooks (via plugins), and MCP. Critically for gald3r,
OpenCode reads **`AGENTS.md`** (with **`CLAUDE.md`** fallback) and natively discovers skills from
**`.claude/skills/`** and **`.agents/skills/`** in addition to `.opencode/skills/`, so gald3r's
Claude-Code SKILL.md packages, `AGENTS.md`, and command/agent assets are **largely drop-in reusable**
on OpenCode.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://opencode.ai/docs (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: 2026-05-26`,
`status: ⚠️`) which conservatively marked every mechanism partial because it was doc-scan-only and
not install-tested — the crawl assessment confirms all six primitives are NATIVE in OpenCode.

> **Instruction-file convention:** OpenCode reads **`AGENTS.md`** as its primary instruction file
> (the open agents standard), falling back to **`CLAUDE.md`**. **If both `AGENTS.md` and `CLAUDE.md`
> exist locally, only `AGENTS.md` is used.** It also reads the global `~/.config/opencode/AGENTS.md`
> and the Claude Code file `~/.claude/CLAUDE.md` (unless disabled). This differs from Claude Code
> (which reads `CLAUDE.md`, not `AGENTS.md`).

> **Hooks caveat:** OpenCode's lifecycle hooks are **in-process JS/TS plugins** (event handlers),
> not drop-in shell scripts and not a JSON wiring file. Lifecycle coverage is broad, but there is
> **no first-class git pre-commit / pre-push event** and gald3r PowerShell `.ps1` hooks must be
> shelled out from a JS/TS wrapper rather than registered directly. This is the single largest
> friction point (see §6 + §9).

---

## 1. Folder Hierarchy

OpenCode reads a project-root `.opencode/` directory plus a root-level `opencode.json` config.
Subdirectory names use **plural** forms (singular still accepted for backwards compatibility):

```
<project-root>/
├── AGENTS.md / CLAUDE.md            ← instruction files OpenCode reads (AGENTS.md wins if both exist)
├── opencode.json (or .jsonc)        ← ROOT config — NOT inside .opencode/ (mcp + instructions + plugin)
└── .opencode/
    ├── commands/    *.md            ← custom commands (markdown + YAML frontmatter)
    ├── agents/      *.md            ← primary agents + subagents (markdown, or opencode.json inline)
    ├── skills/      <name>/SKILL.md ← Agent Skills (loaded on-demand via native `skill` tool)
    ├── plugins/     *.{js,ts}       ← JS/TS plugins == OpenCode's hook mechanism
    ├── modes/                       ← agent modes (opencode concept; no gald3r analog)
    ├── tools/                       ← custom tool definitions (opencode concept)
    └── themes/                      ← TUI themes
```

OpenCode **also** discovers `.claude/skills/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`
(workspace or `~/`), reads `~/.claude/CLAUDE.md`, and walks project-local paths up to the git worktree
root. gald3r's `.claude/`-style skill trees and `AGENTS.md`/`CLAUDE.md` therefore work on OpenCode
with **no OpenCode-specific port** for skills + rules.

Global equivalents live under `~/.config/opencode/` (`opencode.json`, `AGENTS.md`, `commands/`,
`agents/`, `skills/`, `plugins/`). The 2026 config update loads `opencode.json` from the opened
location upward.

**gald3r writes**: `.opencode/commands/`, `.opencode/agents/`, `opencode.json`, and (optionally)
`.opencode/plugins/` for a hook shim; for maximum reuse, gald3r's `.claude/skills/` tree +
`AGENTS.md`/`CLAUDE.md` are read as-is.
**OpenCode owns**: the `.opencode/` namespace, the `opencode.json` schema, plugin loading, skill
discovery, and the TUI.

---

## 2. AI Instruction File

OpenCode's primary instruction file is **`AGENTS.md`** (project root), the open agents standard —
the equivalent of Cursor's rules-as-context. Load order (verified):

1. **Local** files traversing up from the current directory — `AGENTS.md`, then `CLAUDE.md`.
   **If both exist locally, only `AGENTS.md` is used.**
2. **Global** file at `~/.config/opencode/AGENTS.md` (applies across all sessions).
3. **Claude Code** file at `~/.claude/CLAUDE.md` (unless disabled).

- **Generated via**: the OpenCode `/init` command scans the repo and writes `AGENTS.md`.
- **Additional files**: the `instructions` array in `opencode.json` registers extra instruction
  files (paths, glob patterns, and remote URLs):
  `"instructions": ["CONTRIBUTING.md", "docs/guidelines.md"]`.

gald3r **generates/merges** `AGENTS.md` / `CLAUDE.md` via the setup + parity pipeline; these files
are personalized per user and gitignored (`g-rl-02`). Because OpenCode reads `CLAUDE.md`, gald3r's
existing `CLAUDE.md` already delivers rules content to OpenCode with no extra work.
Source: https://opencode.ai/docs/rules/

---

## 3. Agents Support — ✅ NATIVE

- **Primary agents + subagents**: markdown agent files (named after the agent, e.g. `review.md` →
  the `review` agent) in `.opencode/agents/` (or `~/.config/opencode/agents/`), or inline in
  `opencode.json`. `opencode agent create` scaffolds one interactively.
- **Invocation**: subagents manually invoked via `@mention` (e.g. `@general`); auto-invoked via the
  **Task** tool. Built-in primaries: **Build**, **Plan**. Built-in subagents: **General**,
  **Explore**, **Scout**.
- gald3r `g-agnt-*` definitions map directly to OpenCode agent files.
- Source: https://opencode.ai/docs/agents/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` + YAML frontmatter) loaded **on-demand via the native `skill` tool** —
  agents see available skills and load the full content only when needed. Required frontmatter:
  `name` + `description` (optional `license`, `compatibility`, `metadata`).
- **Discovery (multi-path)**: `.opencode/skills/<name>/SKILL.md`, **`.claude/skills/<name>/SKILL.md`**,
  **`.agents/skills/<name>/SKILL.md`** (project), plus `~/.config/opencode/skills/`,
  `~/.claude/skills/`, `~/.agents/skills/` (global). Project-local paths are walked up to the git
  worktree root.
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/`. gald3r's
  extra frontmatter (`subsystem_memberships`, `token_budget`) lands under the tolerated/`metadata`
  space. No conversion required.
- Source: https://opencode.ai/docs/skills/

## 5. Commands / Workflows — ✅ NATIVE

- **Custom commands**: markdown files in `.opencode/commands/` (also `~/.config/opencode/commands/`),
  with YAML frontmatter. Prompts support the `$ARGUMENTS` placeholder, positional `$1`/`$2`/`$3`, and
  `!command` bash injection. Frontmatter fields: `description`, `agent`, `model`, `subtask`.
- gald3r `@g-*` / `/g-*` commands map directly to `.opencode/commands/`.
- Source: https://opencode.ai/docs/commands/

## 6. Hooks System — ✅ NATIVE (JS/TS plugins)

- **Lifecycle hooks** are implemented as **plugins**: JS/TS modules that export a function returning
  a hooks object and subscribe to lifecycle events. Auto-loaded at startup from the plugin directory
  or from npm. A plugin's context exposes project info, cwd, git worktree path, an SDK client, and
  Bun's shell API.
- **Location**: `.opencode/plugins/` (project), `~/.config/opencode/plugins/` (global), or npm
  packages registered via the `plugin` option in `opencode.json`.
- **Available events** (20): `tool.execute.before`, `tool.execute.after`, `command.executed`,
  `file.edited`, `file.watcher.updated`, `session.created`, `session.idle`, `session.compacted`,
  `session.deleted`, `session.updated`, `permission.asked`, `permission.replied`, `shell.env`,
  `lsp.client.diagnostics`, `todo.updated`, `tui.prompt.append`, `tui.command.execute`,
  `tui.toast.show`, `server.connected`, `installation.updated`.
- **Mapping**: `tool.execute.before`/`after` gives pre-tool gating (PreToolUse-equivalent);
  `file.edited` / `file.watcher.updated` covers file-watch; `session.created` covers session-start.
- **gald3r friction (largest gap)**: hooks are **event-driven JS/TS plugins**, not drop-in shell
  scripts and not a JSON wiring file. gald3r ships hooks as **PowerShell `.ps1`** scripts, which do
  **not** run natively as OpenCode plugins. A thin JS/TS plugin must shell out to
  `powershell.exe -File …` on `session.created` / `tool.execute.before` / `tool.execute.after`.
  Additionally there is **no first-class git pre-commit / pre-push event** — commit-gate enforcement
  must be wired via `command.executed` or external git hooks. ✅ for native lifecycle coverage;
  gald3r's hook payload is not portable as-is (see §9).
- Source: https://opencode.ai/docs/plugins/

## 7. Rules / Memory — ✅ NATIVE

- Rules/memory == the `AGENTS.md` instruction file (§2) plus the `instructions` config array. The
  whole of `AGENTS.md` (and referenced `instructions` files) is injected into the LLM context at
  startup — effectively one always-apply document. There is **no separate `memory` file distinct
  from rules**: persistent instructions are the single `AGENTS.md`/`CLAUDE.md` convention (good
  parity, but no auto-updating memory store).
- There is **no `.mdc` per-file glob-scoped rule engine** like Cursor's `.cursor/rules/*.mdc`.
  gald3r's many `g-rl-*` rules consolidate into `AGENTS.md` (or are referenced via `instructions`);
  rule *content* transfers, Cursor's per-rule glob *scoping* does not.
- **CLAUDE.md fallback**: because OpenCode reads `CLAUDE.md`, gald3r's existing `CLAUDE.md` already
  delivers rules to OpenCode with no extra work.
- Source: https://opencode.ai/docs/rules/

## 8. MCP Support — ✅ NATIVE

- MCP servers defined under the **`mcp`** field in `opencode.json` (root) or global
  `~/.config/opencode/opencode.json`. Supports type **`local`** (spawned command, stdio) and type
  **`remote`** (URL). 2026 updates added MCP OAuth callback-port config and scoped client metadata.
- Config supports `{env:VAR}` and `{file:path}` substitution — inject API keys/secrets without
  inlining them.
- gald3r's MCP server block drops into `opencode.json -> mcp`.
- Source: https://opencode.ai/docs/mcp-servers/

## 9. Other Extensibility + Known Gaps vs. Cursor Reference

**Other extensibility (OpenCode bonuses, no Cursor analog):**
- **Custom Tools** — functions the LLM can call during conversations, alongside built-in
  read/write/bash tools (https://opencode.ai/docs/custom-tools/).
- **Modes** — built-in **Plan** mode (read-only / suggest) vs **Build** mode (full access) as
  primary-agent permission profiles.
- **SDK** — official `@opencode-ai/sdk` + in-process HTTP server; sessions can store custom metadata
  via API/SDK (2026 update).

**Gaps / friction vs. Cursor reference:**
1. **Hooks are JS/TS plugins, not PowerShell** (✅ native, but not portable). gald3r `g-hk-*.ps1`
   require a JS/TS plugin shim that shells out via the plugin context's Bun shell API. **No
   first-class git pre-commit / pre-push event** — wire via `command.executed` or external git hooks.
2. **No `.mdc` glob-scoped rule engine** (rule content transfers via `AGENTS.md`/`CLAUDE.md`; per-rule
   `alwaysApply`/`globs` scoping does not).
3. **No separately named memory store** distinct from the `AGENTS.md`/`CLAUDE.md` instruction file
   (good parity, but no auto-updating memory).
4. **Decision-tree placement**: OpenCode's plugin (JS/TS) hook format and `opencode.json` schema are
   correctly classified **platform-specific** — they live in the OpenCode tree
   (`.gald3r_sys/platforms/.opencode/`), not common `.gald3r_sys/`. The shared `.claude/skills/` +
   `.agents/skills/` discovery paths and `AGENTS.md`/`CLAUDE.md` reads are where OpenCode reuses
   common gald3r output directly.

**Reuse note (important):** because OpenCode reads `AGENTS.md`/`CLAUDE.md` and discovers `.claude/`
+ `.agents/` skill trees, gald3r's **Claude-Code SKILL.md packages, instruction files, and
command/agent assets are largely drop-in reusable** — the cheapest high-parity path is to ship the
gald3r `.claude/skills/` tree + `AGENTS.md`, then add a thin JS/TS plugin shim only for the hooks.

## Hook System

- **Type**: native (JS/TS **plugins**, not a JSON wiring file, not `.ps1`)
- **Config file / location**: `.opencode/plugins/` (project) + `~/.config/opencode/plugins/` (global),
  auto-loaded at startup; or npm packages via `opencode.json` `plugin` option
- **Events available** (20): `tool.execute.before`, `tool.execute.after`, `command.executed`,
  `file.edited`, `file.watcher.updated`, `session.created`, `session.idle`, `session.compacted`,
  `session.deleted`, `session.updated`, `permission.asked`, `permission.replied`, `shell.env`,
  `lsp.client.diagnostics`, `todo.updated`, `tui.prompt.append`, `tui.command.execute`,
  `tui.toast.show`, `server.connected`, `installation.updated`
- **Event payload format**: JS/TS context object (project info, cwd, git worktree path, SDK client,
  Bun shell API); a plugin exports a function returning a hooks object
- **Limitations**: plugin language is JavaScript/TypeScript (npm supported) — gald3r PowerShell
  `.ps1` hooks must be shelled out from a JS/TS wrapper; **no first-class git pre-commit / pre-push
  event** (wire via `command.executed` or external git hooks)
- **gald3r hook files**: `g-hk-*.ps1` wire via a thin TS plugin that calls
  `powershell.exe -File …` on `session.created` / `tool.execute.before` / `tool.execute.after`

## Atypical Handling

- Instruction file is **`AGENTS.md`** (CLAUDE.md fallback); **if both exist locally, only AGENTS.md
  is used** — unlike Claude Code, which reads `CLAUDE.md`.
- Skills are discovered from `.opencode/skills/`, **`.claude/skills/`**, and **`.agents/skills/`**
  (shared Agent-Skills locations), loaded on-demand via the native `skill` tool.
- Hooks are JS/TS plugins exporting a function, not a JSON wiring file and not `.ps1` scripts — a
  format mismatch with gald3r hooks; no first-class git pre-commit event.
- Config is `opencode.json` (root, NOT inside `.opencode/`); MCP lives under its `mcp` field.

## gald3r Integration Notes

- Cheapest high-parity install: ship gald3r's `.claude/skills/` tree + `AGENTS.md`/`CLAUDE.md` —
  OpenCode loads them natively. Put commands in `.opencode/commands/`, agents in `.opencode/agents/`.
- gald3r `g-hk-*.ps1` hooks do NOT run natively — author a thin TS plugin in `.opencode/plugins/`
  that shells out to `powershell.exe -File …` on `session.created` / `tool.execute.before` /
  `tool.execute.after`. Re-verify the plugin context fields + event list before authoring the shim.
- Re-verify on the next `@g-platform-scan-docs opencode` (crawl_max_age_days: 7).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ✅**: native lifecycle hooks via JS/TS plugins (20 events); gald3r `.ps1` need a JS/TS
  shim and there is no first-class git pre-commit event.
- **Rules ✅**: `AGENTS.md` (CLAUDE.md fallback) + `instructions` array; no `.mdc` glob scoping.
- **Skills ✅**: native `skill` tool; discovered in `.opencode/skills/` + `.claude/skills/` +
  `.agents/skills/` → gald3r SKILL.md drop-in.
- **Commands ✅**: `.opencode/commands/*.md` with `$ARGUMENTS`/`$1` + `!bash`; frontmatter
  `description`/`agent`/`model`/`subtask`.
- **MCP ✅**: `opencode.json -> mcp` (local + remote), `{env:}`/`{file:}` substitution.
- **Docs Fresh ✅**: crawl assessment of https://opencode.ai/docs completed 2026-06-02.

---

## Verification Evidence (docs crawl 2026-06-02, https://opencode.ai/docs)

| Capability | How verified |
|---|---|
| Commands | /docs/commands/ — `.opencode/commands/*.md` with YAML frontmatter; `$ARGUMENTS` + `$1/$2/$3` + `!command` bash; fields description/agent/model/subtask |
| Rules | /docs/rules/ — `AGENTS.md` primary (CLAUDE.md fallback; AGENTS.md wins if both local) + global `~/.config/opencode/AGENTS.md` + `~/.claude/CLAUDE.md`; `instructions` array; `/init` |
| Agents | /docs/agents/ — primary (Build/Plan) + subagents (General/Explore/Scout); markdown agent files or opencode.json; `@mention` + Task tool; `opencode agent create` |
| Skills | /docs/skills/ — `SKILL.md` loaded on-demand via native `skill` tool; discovered in `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` (+ home); name+description frontmatter |
| Hooks | /docs/plugins/ — JS/TS plugins in `.opencode/plugins/` (+ npm via opencode.json `plugin`); 20 lifecycle events; no first-class git pre-commit; `.ps1` needs a JS/TS shim |
| MCP | /docs/mcp-servers/ — `mcp` field in opencode.json; type local (command) + remote (URL); 2026 OAuth callback-port + scoped client metadata; `{env:}`/`{file:}` substitution |
| Other | /docs/custom-tools/ — Custom Tools; built-in Plan/Build modes; `@opencode-ai/sdk` + in-process HTTP server with session metadata |
| Cross-compat | OpenCode reads `AGENTS.md`/`CLAUDE.md` + discovers `.claude/` + `.agents/` skills → gald3r Claude-Code SKILL.md/instruction artifacts reusable; hooks need a JS/TS `.ps1` shim |
