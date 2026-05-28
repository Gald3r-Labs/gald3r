---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: opencode
authoring_path: update
docs_url: https://opencode.ai/docs
docs_url_secondary:
  - https://opencode.ai/docs/config
  - https://opencode.ai/docs/rules
  - https://opencode.ai/docs/skills
  - https://opencode.ai/docs/plugins
  - https://opencode.ai/docs/mcp-servers
crawl_max_age_days: 7
vault_doc_path: research/platforms/opencode/
last_doc_scan: 2026-05-26
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — OpenCode (sst/opencode)

OpenCode is an open-source, terminal-first AI coding agent from the SST team
(`opencode` binary, repo `sst/opencode`, docs https://opencode.ai/docs). It runs as a TUI with
multi-provider model support and a JSON/JSONC config (`opencode.json`). This spec compares OpenCode
against the Cursor reference (`g-skl-platform-cursor`).

> **Authoring path: UPDATE** — `g-skl-platform-opencode/SKILL.md` already ships. This spec records
> the verified findings from a doc scan of https://opencode.ai/docs on 2026-05-26 and corrects
> several stale assumptions in the prior SKILL.md (see §9).
>
> **Verification basis**: doc-citation scan of https://opencode.ai/docs (config, rules, skills,
> plugins) on 2026-05-26. NOT verified by a local install run in this repo (no `.opencode/` folder
> or `opencode.json` is present here). Capability cells that depend on observed runtime behavior are
> therefore marked ⚠️/❓ rather than ✅.

---

## 1. Folder Hierarchy

OpenCode reads a project-root `.opencode/` directory plus a root-level `opencode.json` config.
Verified subdirectory names (from docs) use **plural** names (singular still accepted for
backwards compatibility):

```
opencode.json (or opencode.jsonc)   ← ROOT config — NOT inside .opencode/
.opencode/
├── agents/        ← agent definition markdown
├── commands/      ← custom command markdown
├── skills/        ← skills, folder-per-skill (SKILL.md)
├── plugins/       ← JS/TS plugins == OpenCode's hook mechanism
├── modes/         ← agent modes (opencode concept; no gald3r analog)
├── tools/         ← custom tool definitions (opencode concept)
└── themes/        ← TUI themes

Global equivalents live under ~/.config/opencode/ (opencode.json, AGENTS.md,
skills/, plugins/, tui.json).
```

**gald3r writes** (within the gald3r convention): `.opencode/agents/`, `.opencode/commands/`,
`opencode.json`. Skills can be served from `.opencode/skills/` OR the shared `.claude/skills/`
(OpenCode reads both — see §4). gald3r does NOT currently emit `.opencode/plugins/`, `modes/`,
`tools/`, or `themes/`.
**OpenCode owns**: the `.opencode/` namespace, the `opencode.json` schema, plugin loading, skill
discovery, and the TUI.

❓ The exact set of subdirectories gald3r's parity sync writes was not re-verified against a live
install in this repo (no `.opencode/` present); the gald3r override dir currently contains only
`opencode_instructions.md`.

---

## 2. AI Instruction File

Verified: OpenCode's primary instruction file is **`AGENTS.md`** (project root), the equivalent of
Cursor's rules-as-context.

- **Project**: `AGENTS.md` at root (and traversing up to the git worktree).
- **Global**: `~/.config/opencode/AGENTS.md` (applies across all sessions).
- **Claude Code compatibility**: OpenCode falls back to `CLAUDE.md` and `~/.claude/CLAUDE.md` for
  migrating users unless disabled by env var. This is significant for gald3r, which already ships a
  personalized `CLAUDE.md`.
- **Generated via**: the OpenCode `/init` command scans the repo and writes `AGENTS.md`.
- **Additional files**: the `instructions` array in `opencode.json` references extra instruction
  files (and remote URLs, 5s timeout): `"instructions": ["CONTRIBUTING.md", "docs/guidelines.md"]`.

gald3r **generates/merges** `AGENTS.md` / `CLAUDE.md` via the setup + parity pipeline; these files
are personalized per user and gitignored (`g-rl-02`).

---

## 3. Agents Support

- **Native concept**: ✅ Yes — OpenCode has first-class agents (and "modes"). A `default_agent`
  can be set in config (`"default_agent": "plan"`).
- **Discovery**: markdown files in `.opencode/agents/` (or the `agent` config field).
- **Loading**: agents are selectable; one is the default. This differs from Cursor's `@agent-name`
  manual invocation but is conceptually compatible (markdown-defined agents).
- **gald3r mapping**: `g-agnt-*.md` → `.opencode/agents/`. ⚠️ Whether OpenCode honors the gald3r
  agent frontmatter fields verbatim (vs. its own agent schema) is untested — agent files may need a
  format shim. Marked ⚠️ partial.

---

## 4. Skills Support

- **Native concept**: ✅ Yes — OpenCode has a native skills system with a dedicated `skill` tool.
- **Discovery** (verified, multi-path): project-local `.opencode/skills/<name>/SKILL.md`,
  `.claude/skills/<name>/SKILL.md`, and `.agents/skills/<name>/SKILL.md`; global equivalents under
  `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/`. OpenCode walks up from cwd
  to the git worktree root.
- **Format**: folder-per-skill with `SKILL.md` + YAML frontmatter. Required fields: `name`
  (1–64 lowercase alphanumeric, single hyphens) and `description` (1–1024 chars). Optional:
  `license`, `compatibility`, `metadata`.
- **gald3r compatibility**: ✅ gald3r `g-skl-*` skill names satisfy the name constraint (lowercase +
  hyphens). gald3r's extra frontmatter (`subsystem_memberships`, `token_budget`, etc.) lands under
  the unvalidated/`metadata` space and should be tolerated, but this was not runtime-verified.
- **Invocation**: agents call the native `skill` tool: `skill({ name: "skill-name" })`. OpenCode
  lists available skills in that tool's description.
- **Status**: ⚠️ verified-by-docs (discovery paths, format, name rules) but not install-tested in
  this repo. The shared `.claude/skills/` path means gald3r skills are reachable WITHOUT a separate
  `.opencode/skills/` copy.

---

## 5. Commands / Workflows

- **Native concept**: ✅ Yes — custom commands via the `command` config field or markdown files in
  `.opencode/commands/`.
- **gald3r mapping**: `g-*.md` → `.opencode/commands/`.
- **Invocation**: OpenCode commands are surfaced in the TUI (slash-style); exact gald3r `@g-*` /
  `/g-*` invocation parity is ⚠️ untested. Command-body execution semantics (does OpenCode run the
  command markdown as an agent prompt?) differ from Cursor and were not install-verified.

---

## 6. Hooks System

- **Native hook system**: ✅ Yes — but it is the **plugins** system, not a JSON wiring file like
  Cursor's `hooks.json`.
- **Plugin language**: **JavaScript / TypeScript** (also npm packages). A plugin exports a function
  that receives a context object (project info, cwd, git worktree path, an SDK client, Bun's shell
  API) and returns a hooks object.
- **Location**: `.opencode/plugins/` (project) and `~/.config/opencode/plugins/` (global),
  auto-loaded at startup.
- **Lifecycle events** (verified categories): Command, File, Installation, LSP, Message,
  Permission, Server, Session, Todo, Shell, Tool, TUI. Notable events:
  `tool.execute.before` / `tool.execute.after`, `session.created` / `session.idle` /
  `session.compacted` / `session.updated`, `file.edited`, `file.watcher.updated`, `shell.env`.
- **gald3r gap**: ❌ gald3r ships hooks as **PowerShell `.ps1`** scripts wired through Cursor's
  `hooks.json`. OpenCode has NO `.ps1`/JSON hook wiring — its hooks are JS/TS plugin callbacks.
  gald3r hooks therefore do NOT run natively on OpenCode without a JS/TS plugin shim that shells out
  to the PowerShell scripts. This is the single largest parity gap (see §9). Marked ⚠️ (capability
  exists on the platform, but gald3r's hook payload is not portable as-is).

---

## 7. Rules / Memory

- **Mechanism**: rules/memory == the `AGENTS.md` instruction file (§2) plus the `instructions`
  config array. There is **no `.mdc` rule format** and **no per-file `globs:`/`alwaysApply:`
  frontmatter rule-engine** like Cursor's `.cursor/rules/*.mdc`.
- **Context injection**: the whole of `AGENTS.md` (and referenced `instructions` files) is injected
  into the LLM context. It is effectively one always-apply document, not a set of glob-scoped rules.
- **gald3r mapping**: gald3r's many `g-rl-*` rules must be consolidated/concatenated into `AGENTS.md`
  (or referenced via `instructions`), losing Cursor's per-rule glob scoping. ⚠️ partial — content
  carries over, the selective always-apply/on-demand semantics do not.
- **CLAUDE.md fallback**: because OpenCode reads `CLAUDE.md`, gald3r's existing `CLAUDE.md` already
  delivers rules content to OpenCode with no extra work (verified by docs).

---

## 8. MCP Support

- **Supported**: ✅ Yes — via the `mcp` field in `opencode.json`.
- **Config format/location**: JSON block inside `opencode.json` (root) or global
  `~/.config/opencode/opencode.json`. Supports local (stdio) and remote (sse/http) servers.
- **Variable substitution**: config supports `{env:VAR}` and `{file:path}` substitution, useful for
  injecting API keys/secrets without inlining them.
- **Status**: ⚠️ config mechanism verified by docs; the concrete gald3r MCP server block and live
  connection were not install-tested in this repo.

---

## 9. Known Gaps vs. Cursor Reference

1. **Hooks are JS/TS plugins, not PowerShell + `hooks.json`** (❌/⚠️). gald3r's entire hook suite
   (`g-hk-*.ps1`) does not run natively. A JS/TS plugin shim invoking the PowerShell scripts (via
   the plugin context's Bun shell API) would be required to wire `sessionStart`/`stop`/
   `preToolUse`-equivalents (`session.created` / `session.idle` / `tool.execute.before`). Until that
   shim exists, gald3r hook automation on OpenCode is a documented gap.
2. **No `.mdc` glob-scoped rule engine** (⚠️). Cursor's per-rule `alwaysApply`/`globs` selectivity
   collapses into a single `AGENTS.md` always-on document. Rule *content* transfers; rule *scoping*
   does not.
3. **Command execution semantics untested** (⚠️). `.opencode/commands/` exists, but whether gald3r
   `@g-*` command markdown executes equivalently (and the exact slash invocation) is not
   install-verified.
4. **Agent frontmatter schema mismatch** (⚠️). OpenCode has its own agent/mode model; gald3r
   `g-agnt-*.md` may need a format shim. Untested.
5. **No live install verification in this repo** (❓). No `.opencode/` folder or `opencode.json`
   present here; all ✅-by-docs claims await an `opencode --version` + load test.
6. **Decision-tree placement**: OpenCode's plugin (JS/TS) hook format and `opencode.json` schema are
   correctly classified **platform-specific** — they live in the OpenCode tree
   (`.gald3r_sys/platforms/.opencode/`), not common `.gald3r_sys/`. The shared `.claude/skills/`
   skill-discovery path is the one place OpenCode reuses common gald3r output directly.

**Positive parity (better than prior SKILL.md assumed):** OpenCode DOES support native skills
(`.opencode/skills/` + `.claude/skills/`), DOES have a native hook system (plugins), and DOES read
`CLAUDE.md`/`AGENTS.md` directly — so rules and skills content reach OpenCode with minimal glue.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ⚠️**: native hook system exists (plugins) but gald3r `.ps1` hooks are not portable without a JS/TS shim.
- **Rules ⚠️**: content carries via `AGENTS.md`/`CLAUDE.md`; glob scoping lost.
- **Skills ⚠️**: native + `.claude/skills/` reuse verified by docs; not install-tested.
- **Commands ⚠️**: `.opencode/commands/` exists; gald3r command execution parity untested.
- **MCP ⚠️**: `opencode.json mcp` block verified by docs; live server block untested.
- **Docs Fresh ✅**: doc scan of https://opencode.ai/docs completed 2026-05-26.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Config files / `.opencode/` layout | Doc scan https://opencode.ai/docs/config (2026-05-26): `opencode.json`/`opencode.jsonc`, root config, plural subdirs (agents/commands/skills/plugins/modes/tools/themes), global `~/.config/opencode/` |
| Instruction file | Doc scan https://opencode.ai/docs/rules: `AGENTS.md` (project + `~/.config/opencode/AGENTS.md`), `CLAUDE.md`/`~/.claude/CLAUDE.md` fallback, `/init`, `instructions` array |
| Skills | Doc scan https://opencode.ai/docs/skills: discovery from `.opencode/skills/`, `.claude/skills/`, `.agents/skills/`; SKILL.md frontmatter `name`(1–64 lowercase+hyphen)/`description`; native `skill` tool |
| Plugins / hooks | Doc scan https://opencode.ai/docs/plugins: JS/TS plugins in `.opencode/plugins/`, event categories + named events (`tool.execute.before`, `session.created`, `file.edited`, etc.) |
| MCP | Doc scan https://opencode.ai/docs/config: `mcp` field in `opencode.json`, `{env:}`/`{file:}` substitution |
| Live install | ❓ NOT verified — no `.opencode/` or `opencode.json` in this repo; no `opencode --version` run |
