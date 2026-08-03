---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: pi
authoring_path: new
docs_url: https://pi.dev/docs/latest/usage
docs_url_secondary:
  - https://pi.dev/docs/latest/skills
  - https://pi.dev/docs/latest/prompt-templates
  - https://pi.dev/docs/latest/extensions
  - https://pi.dev/docs/latest/settings
  - https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md
crawl_max_age_days: 14
vault_doc_path: research/platforms/pi/
last_doc_scan: 2026-07-03
reference: g-skl-platform-cursor
status: ⚠️
task: platform-Pi (badlogic/pi-mono coding harness)
---

# PLATFORM_SPEC.md — Pi (badlogic/pi-mono coding harness)

**Pi** (`badlogic/pi-mono`, package `packages/coding-agent`) is a minimal, open-source terminal
coding-agent harness — "AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI"
(67.5k+ GitHub stars at verification time). It is a bare CLI/TUI, not an IDE or GUI app: no
Settings panels, no marketplace — everything is files-on-disk plus TypeScript extensions.

**Authoring path**: NEW. **Verified 2026-07-03** against https://pi.dev/docs/latest/usage,
/skills, /prompt-templates, /extensions, /settings, and the pi-mono `coding-agent` README (see
Verification Evidence). No prior gald3r spec existed for this platform.

> **Instruction-file truth (read carefully):** Pi reads **`AGENTS.md`** (or `CLAUDE.md` as an
> alias) via **true hierarchical directory-walk concatenation** — global `~/.pi/agent/AGENTS.md`,
> then every matching file found walking **up from the current working directory to the
> project/global roots**, all concatenated together. This is closer to Cursor/Qwen/Gemini's
> hierarchical model than to ZCode's flat two-scope append. Pi additionally supports a full
> **system-prompt override** (`SYSTEM.md` replaces the default system prompt; `APPEND_SYSTEM.md`
> appends to it) at both global (`~/.pi/agent/`) and project (`.pi/`) scope — a capability none of
> gald3r's other AGENTS.md-native platforms expose as a first-class file.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                        ← project instructions (CLAUDE.md also accepted as alias)
└── .pi/
    ├── SYSTEM.md                    ← optional: REPLACES the default system prompt (project scope)
    ├── APPEND_SYSTEM.md             ← optional: APPENDS to the system prompt (project scope)
    ├── skills/   <name>/SKILL.md    ← Agent Skills (project scope; agentskills.io standard)
    ├── prompts/  <name>.md          ← prompt templates == custom slash commands (project scope)
    ├── extensions/ <name>.ts        ← TypeScript extensions: tools, commands, hooks, UI (project)
    │   or <name>/index.ts
    └── settings.json                ← project settings (merges over global; `extensions:` array)

~/.pi/agent/                         ← global config root (override via $PI_CODING_AGENT_DIR)
├── AGENTS.md                        ← global instructions (read first in the walk-up concat)
├── SYSTEM.md / APPEND_SYSTEM.md     ← global system-prompt override/append
├── skills/   <name>/SKILL.md        ← global Agent Skills
├── prompts/  <name>.md              ← global prompt templates
├── extensions/ <name>.ts            ← global TypeScript extensions
└── settings.json                    ← global settings

~/.agents/skills/                    ← ALSO discovered (cross-tool shared skills location)
```

**gald3r writes**: project-root `AGENTS.md`, `.pi/skills/<name>/SKILL.md`, `.pi/prompts/<name>.md`,
and a single `.pi/extensions/gald3r-hooks.ts` lifecycle-hook extension. **Pi owns**: the `.pi/`
namespace mechanics (settings merge order, extension loading/trust gating, skill scan order).

---

## 2. AI Instruction File

Pi reads **`AGENTS.md`** (or **`CLAUDE.md`** as an accepted alias — the docs state these are
treated equivalently) via genuine **hierarchical concatenation**:

1. `~/.pi/agent/AGENTS.md` (global)
2. Every `AGENTS.md`/`CLAUDE.md` found walking **up** from the current working directory
3. The current directory's own file

"All matching files are concatenated." Loading can be disabled entirely with `--no-context-files`
/ `-nc`. This is a closer match to gald3r's `AGENTS.md`-hierarchy platforms (Cursor, Qwen, Gemini)
than to ZCode's flat two-scope append — gald3r's rule content can be split across directory levels
if useful, but a single project-root `AGENTS.md` is the simplest, most portable install target.

- Pi **also** supports full system-prompt control distinct from `AGENTS.md`: `.pi/SYSTEM.md`
  (project) or `~/.pi/agent/SYSTEM.md` (global) **replaces** the default system prompt outright;
  `APPEND_SYSTEM.md` at either scope **appends** to it instead. gald3r does not need this for a
  standard install (`AGENTS.md` is sufficient) but it is documented here because a future
  persona/system-prompt override skill could target it.
- Source: https://pi.dev/docs/latest/usage

---

## 3. Agents Support — ❌ NOT SUPPORTED (no native subagent-roster file)

- Pi has **no documented `agents/<name>.md`-style subagent roster** the way Claude Code, Cursor,
  Goose, or Mistral Vibe do. The TypeScript extension API exposes session-control primitives
  (`ctx.newSession()`, `ctx.fork()`, `pi.sendMessage()`) that a **custom extension** could use to
  spawn or fork sub-sessions programmatically, but that is imperative extension code, not a
  declarative per-agent file gald3r can drop in.
- **gald3r gap**: gald3r's `g-agnt-*.md` set has no project-scoped landing zone on Pi today. Do not
  fabricate an `agents/*.md` folder that Pi does not read — this mirrors the ZCode precedent
  (`g-skl-platform-zcode` §3) of documenting the gap honestly rather than inventing a file format.
- Source: absence confirmed against https://pi.dev/docs/latest/extensions (ExtensionAPI surface)
  and https://pi.dev/docs/latest/usage (no agents/subagents section in either).

## 4. Skills Support — ✅ NATIVE

- **Agent Skills**: implements "the Agent Skills standard" — a `SKILL.md` file per skill directory
  with YAML frontmatter (`name`: lowercase alphanumeric + hyphens, 1-64 chars; `description`: max
  1024 chars; optional `license`, `compatibility`, `metadata`, `allowed-tools`,
  `disable-model-invocation`) plus a Markdown body.
- **Locations** (all scanned, merged): `~/.pi/agent/skills/` (global), `~/.agents/skills/` (shared
  cross-tool location), `.pi/skills/` (project), `.agents/skills/` (project — searched from cwd up
  through parent directories), and skills bundled inside Pi packages.
- **Discovery/invocation**: at startup Pi scans all skill locations and extracts metadata; the
  system prompt lists available skills in XML. Skills load on-demand via **`/skill:name`** (e.g.
  `/skill:pdf-tools extract`) or automatically when a task matches the skill's `description`.
- **Leniency note**: "Pi allows skill names to differ from their parent directory even though the
  standard disallows it" (for cross-harness compatibility) — gald3r's `g-skl-*` directory-name ==
  frontmatter-`name` convention is already standard-compliant, so no adaptation is needed.
- **gald3r mapping**: `g-skl-*/SKILL.md` files are **drop-in compatible** at `.pi/skills/<name>/` —
  same frontmatter shape as agentskills.io, identical to how gald3r already ships for
  Claude/Cursor/ZCode.
- Source: https://pi.dev/docs/latest/skills

## 5. Commands / Prompt Templates — ✅ NATIVE

- **Prompt templates**: Markdown files that "expand from slash commands", stored at
  `~/.pi/agent/prompts/` (global), `.pi/prompts/` (project), or bundled in Pi packages. Invoked as
  **`/templatename`**.
- Built-in slash commands (not gald3r's concern, but confirms the command surface is real and
  populated): `/login`, `/logout`, `/model`, `/scoped-models`, `/settings`, `/resume`, `/new`,
  `/name`, `/session`, `/tree`, `/trust`, `/fork`, `/clone`, `/compact`, `/copy`, `/export`,
  `/import`, `/share`, `/reload`, `/hotkeys`, `/changelog`, `/quit`.
- **gald3r mapping**: gald3r's `@g-*` / `/g-*` command files map to `.pi/prompts/<name>.md` as
  simple prompt-body files, invoked `/name` (no `g-` prefix stripping needed — the filename **is**
  the command name).
- Source: https://pi.dev/docs/latest/prompt-templates, https://pi.dev/docs/latest/usage

## 6. Hooks / Extensions — ✅ NATIVE (via TypeScript, not JSON config)

- Pi has **no `hooks.json`-style declarative config**. Instead, **TypeScript extensions** register
  event handlers programmatically via `pi.on(eventName, handler)` on an `ExtensionAPI` object
  passed to the extension's default export.
- **Extension locations**: `~/.pi/agent/extensions/*.ts` or `*/index.ts` (global), `.pi/extensions/
  *.ts` or `*/index.ts` (project — **loads only after the project is trusted**), plus package-based
  extensions and paths/npm-packages/git-repos declared in `settings.json`'s `extensions:` array.
- **Real lifecycle events available** (confirmed, not fabricated): `session_start`,
  `session_shutdown`, `before_agent_start`, `agent_start`, `agent_end`, `tool_call`, `tool_result`,
  `message_start`, `message_update`, `message_end`, `input`, `model_select`,
  `thinking_level_select`, and the trust-gate event `project_trust` (fires before project-local
  extensions load, so global/CLI-`-e` extensions can observe the trust decision).
- **gald3r mapping**: a single `.pi/extensions/gald3r-hooks.ts` extension registers
  `pi.on("session_start", ...)`, `pi.on("session_shutdown", ...)`, `pi.on("tool_call", ...)`, and
  `pi.on("tool_result", ...)` handlers that shell out to the **same shared canonical hook core**
  gald3r already uses for Goose (`g_hk_core.dispatch(<canonical-event>)`), passing the event
  payload as JSON on stdin — the identical contract `_hook_common.read_stdin_json()` already
  parses. This is the "TypeScript extensions" surface named in the platform brief.
- Source: https://pi.dev/docs/latest/extensions, https://pi.dev/docs/latest/usage

## 7. Rules / Memory — ✅ NATIVE (hierarchical `AGENTS.md`, no glob-scoped rule files)

- See §2. There is **no** `.mdc`-equivalent scoped/glob rule system (no `alwaysApply:`/`globs:`
  frontmatter semantics like Cursor's `.cursor/rules/`) — `AGENTS.md` is a single concatenated
  instruction body per directory level.
- gald3r `g-rl-*` rules are concatenated into the project-root `AGENTS.md` body (the same pattern
  used for every other `AGENTS.md`-native platform gald3r ships).
- Source: https://pi.dev/docs/latest/usage

## 8. MCP Support — ❌ NOT SUPPORTED (explicitly, by design)

- The `coding-agent` README states plainly: **"No MCP. Build CLI tools with READMEs (see Skills),
  or build an extension that adds MCP support."** This is an explicit design choice, not a gap —
  do not fabricate an `mcp.json`/`.mcp.json` file for Pi.
- **gald3r mapping**: no MCP surface to wire. Any gald3r MCP server integration would require a
  bespoke TypeScript extension bridging to an MCP client — out of scope for a template-source
  install.
- Source: https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md

## 9. Settings / Distribution

- **`settings.json`** at `~/.pi/agent/settings.json` (global) and `.pi/settings.json` (project);
  project settings merge over global (nested objects merge, not replace). The `extensions:` array
  accepts local paths, npm package names, or git repository URLs — this is Pi's closest analog to
  a plugin/marketplace distribution channel, though there is no built-in marketplace UI (it is a
  bare-CLI/TUI harness).
- Source: https://pi.dev/docs/latest/settings

---

## Known Gaps vs. Cursor Reference

| # | Gap | Severity |
|---|---|---|
| 1 | **No MCP** — explicit design choice ("No MCP" per the README); no `.mcp.json`/`mcp_servers` surface exists to wire gald3r's MCP server into. (§8) | High |
| 2 | **No project-level agents** — no `agents/<name>.md` roster convention; gald3r's `g-agnt-*.md` set has no declarative landing zone (session-spawning is imperative-extension-only). (§3) | High |
| 3 | **Hooks require authoring TypeScript**, not dropping in a JSON/shell config — the gald3r hook surface must ship as a compiled/interpretable `.ts` extension file rather than a data file. (§6) | Medium |
| 4 | **Flat rule model within `AGENTS.md`** — no `.mdc`-equivalent glob-scoped rule loading; gald3r's `g-rl-*` set is concatenated into one body per directory level (same limitation as most AGENTS.md-native platforms). (§7) | Low |

**Strongest parity points** (not gaps): Skills (§4) are a byte-for-byte drop-in match for gald3r's
`SKILL.md` convention (same standard used for Claude/Cursor/ZCode). Commands (§5) map cleanly to
simple prompt-template files. Rules (§2/§7) use genuine hierarchical `AGENTS.md` concatenation,
which is actually a *closer* fit to gald3r's typical rule-authoring pattern than ZCode's flat
two-scope append.

## Hook System

- **Type**: native, via TypeScript extension event handlers (not a declarative `hooks.json`) ✅
- **Config file**: none — hooks are code. Extension file: `.pi/extensions/gald3r-hooks.ts`
  (project) or `~/.pi/agent/extensions/gald3r-hooks.ts` (global), auto-loaded at startup (project
  scope gated on project trust).
- **Events available**: `session_start`, `session_shutdown`, `before_agent_start`, `agent_start`,
  `agent_end`, `tool_call`, `tool_result`, `message_start`, `message_update`, `message_end`,
  `input`, `model_select`, `thinking_level_select`, `project_trust`.
- **Event payload format**: handler signature `pi.on(event, async (event, ctx) => {...})`; gald3r's
  extension shells out to the shared Python dispatcher with the event payload serialized as JSON on
  stdin, matching the existing Goose/Claude Code hook contract (`_hook_common.read_stdin_json()`).
- **gald3r hook files**: `g-hk-on-session-start.py`, `g-hk-on-session-end.py`,
  `g-hk-on-tool-start.py`, `g-hk-on-tool-end.py` — invoked via a `node`/`bun`-spawned Python
  subprocess from the single `gald3r-hooks.ts` extension, not one file per hook (Pi has one
  extension file registering multiple `pi.on(...)` calls, unlike Goose's per-event `hooks.json`
  entries).

## Atypical Handling

- **Hierarchical `AGENTS.md`, not flat two-scope** — unlike `g-skl-platform-zcode`, Pi's
  `AGENTS.md`/`CLAUDE.md` walk genuinely merges up the directory tree; do not apply the ZCode
  "inline everything into one workspace file" caveat as strictly (though a single project-root
  file remains the simplest install).
- **Hooks are TypeScript code, not JSON** — gald3r's usual `hooks.json`-style data file has no
  Pi analog; the install surface is a single `.ts` extension file.
- **No MCP by design** — do not fabricate an MCP config surface (see Mistral/ZCode precedent of
  honestly documenting explicit absence vs. undocumented-but-possibly-present).
- **CLI/TUI only, no GUI** — unlike ZCode (a desktop app with Settings panels), Pi has zero UI
  surface beyond the terminal; all configuration is files-on-disk plus `--flag` CLI overrides.

## gald3r Integration Notes

- Ship gald3r's rule content in the project-root `AGENTS.md` (hierarchical concat is compatible
  with gald3r's usual single-file install).
- gald3r skills (`g-skl-*/SKILL.md`) load natively under `.pi/skills/`; no adaptation needed —
  identical frontmatter shape to the Claude/Cursor/ZCode ports already shipped.
- gald3r commands (`@g-*`) map to `.pi/prompts/<name>.md` as simple prompt-body Markdown files.
- Ship the lifecycle-hook surface as a single `.pi/extensions/gald3r-hooks.ts` TypeScript extension
  (see `.pi/extensions/gald3r-hooks.ts` in this overlay) rather than fabricating a JSON hook config.
- Do not ship a project-level `agents/` folder or an `.mcp.json`/MCP config — neither has a
  documented landing zone on Pi today.
- Re-check on the next `@g-platform-scan-docs pi` (crawl_max_age_days: 14) — Pi is an actively
  developed OSS project (67.5k+ stars) with frequent releases; re-verify MCP absence and any new
  agents/subagents documentation.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ✅** — native TypeScript extension event handlers (`pi.on(...)`); no JSON config, code
  IS the hook.
- **Rules ✅** — hierarchical `AGENTS.md`/`CLAUDE.md` concatenation (global then walk-up); flat body
  per level, no glob-scoped rule files.
- **Skills ✅** — native Agent Skills (`SKILL.md`, `name`/`description` frontmatter) in
  `.pi/skills/`, agentskills.io-compatible, same standard as Claude/Cursor/ZCode.
- **Commands ✅** — native prompt templates (`.md` files) at `.pi/prompts/`, invoked `/name`.
- **MCP ❌** — explicitly unsupported by design ("No MCP" per README); would require a bespoke
  extension bridge.
- **Docs Fresh ✅** — `last_doc_scan: 2026-07-03`.

(Agents are ❌ and not one of the 5 summary columns tracked in `PLATFORM_STATUS.md`, consistent
with how ZCode's Beta-agents gap is handled outside the table.)

---

## Verification Evidence (docs crawl 2026-07-03, https://pi.dev/docs/latest/* + github.com/badlogic/pi-mono)

| Capability | How verified |
|---|---|
| Global config dir + override env var | /usage — `~/.pi/agent/` global config directory, overridable via `PI_CODING_AGENT_DIR` |
| `AGENTS.md`/`CLAUDE.md` hierarchical concat | /usage — "Pi loads AGENTS.md or CLAUDE.md at startup from: `~/.pi/agent/AGENTS.md` (global), parent directories walking upward from cwd, current directory. All matching files are concatenated."; disable via `--no-context-files`/`-nc` |
| `SYSTEM.md` / `APPEND_SYSTEM.md` | /usage — `.pi/SYSTEM.md` (project) or `~/.pi/agent/SYSTEM.md` (global) replaces the default system prompt; `APPEND_SYSTEM.md` at either scope appends instead |
| Skills (`SKILL.md`, Agent Skills standard, `/skill:name`) | /skills — locations `~/.pi/agent/skills/`, `~/.agents/skills/`, `.pi/skills/`, `.agents/skills/` (cwd-upward), package skills; frontmatter `name`/`description` + optional fields; "Pi allows skill names to differ from their parent directory even though the standard disallows it" |
| Prompt templates (`/templatename`) | /prompt-templates — Markdown files at `~/.pi/agent/prompts/`, `.pi/prompts/`, package prompts; "reusable prompts that expand from slash commands" |
| Built-in slash commands | /usage — `/login`, `/logout`, `/model`, `/scoped-models`, `/settings`, `/resume`, `/new`, `/name`, `/session`, `/tree`, `/trust`, `/fork`, `/clone`, `/compact`, `/copy`, `/export`, `/import`, `/share`, `/reload`, `/hotkeys`, `/changelog`, `/quit` |
| TypeScript extensions + `pi.on(...)` events | /extensions — `~/.pi/agent/extensions/*.ts` (global), `.pi/extensions/*.ts` (project, trust-gated); `ExtensionAPI` with `on()`, `registerTool()`, `registerCommand()`, `sendMessage()`, etc.; events `session_start`, `session_shutdown`, `before_agent_start`, `agent_start`, `agent_end`, `tool_call`, `tool_result`, `message_start`, `message_update`, `message_end`, `input`, `model_select`, `thinking_level_select` |
| `project_trust` event / trust gating | /usage + /extensions — "Before the trust decision, pi loads only context files, user/global extensions, and CLI `-e` extensions so they can handle the `project_trust` event"; project-local `.pi/extensions` load only after trust |
| `settings.json` two-tier config | /settings — `~/.pi/agent/settings.json` (global), `.pi/settings.json` (project); project overrides global, nested objects merge; `extensions:` array accepts local paths/npm packages/git repos |
| No MCP (explicit) | github.com/badlogic/pi-mono coding-agent README — "No MCP. Build CLI tools with READMEs (see Skills), or build an extension that adds MCP support." |
| No hooks.json / no agents roster file | absence confirmed against full doc set (/usage, /skills, /prompt-templates, /extensions, /settings) — no dedicated hooks-config page, no agents/subagents page |
| Star count / project scale | `gh repo view badlogic/pi-mono` — 67,526 stars at verification time (2026-07-03); description "AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI" |
