---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: amp
authoring_path: rewrite
docs_url: https://ampcode.com/manual
docs_url_secondary:
  - https://ampcode.com/manual/plugin-api
  - https://ampcode.com/news/agent-skills
  - https://ampcode.com/news/hooks
  - https://ampcode.com/news/slashing-custom-commands
crawl_max_age_days: 14
vault_doc_path: research/platforms/amp/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Amp (Amp Code, Sourcegraph)

Amp (Sourcegraph) is a highly extensible coding agent shipped as a CLI plus VS Code / JetBrains
editor integrations. As of mid-2026 it natively supports **five of the six** gald3r-relevant
extension primitives — custom slash commands, rules/memory via **`AGENTS.md`**, native Agent Skills
(`SKILL.md`), MCP servers, and lifecycle hooks — and supports the sixth (subagents) only
**partially**: users cannot author a stand-alone subagent definition file the way Claude Code /
Cursor can. The main agent **auto-spawns** subagents, and plugins can *simulate* custom agents/modes
via an experimental API. Critically for gald3r, Amp reads **`AGENTS.md`** (primary) and also discovers
Skills from **`.claude/skills/`** in addition to `.agents/skills/`, so gald3r's Claude-Code skill
trees are **partly drop-in reusable** on Amp.

**Authoring path**: REWRITE. **Verified 2026-06-02** against https://ampcode.com/manual (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which incorrectly
marked **hooks as ❌ unsupported** and **agents as ✅ fully native** — hooks are now NATIVE (two
surfaces) and agents are only PARTIAL (no declarative subagent file).

> **Surface split:** the full extensibility (commands/rules/skills/hooks/MCP/plugins) lives in the
> **Amp CLI**. The editor integrations (VS Code / JetBrains) share the same `AGENTS.md` + `.agents/`
> config and add the MCP-config UI (`amp.mcpServers` in editor `settings.json`). Where a feature is
> CLI-only or has an editor caveat it is noted inline.

> **Instruction-file convention (important):** Amp reads **`AGENTS.md`** as the primary instruction
> file (NOT a dedicated `AMP.md`). `AGENT.md` (project root) and legacy **`CLAUDE.md`** are also read
> for compatibility. This is the inverse of Claude Code (`CLAUDE.md`-first) — gald3r should ship
> `AGENTS.md` for Amp.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md / AGENT.md / CLAUDE.md   ← instruction files Amp reads (AGENTS.md primary)
└── .agents/
    ├── commands/  <name>.md           ← custom slash commands (file-based; DEPRECATING → Skills)
    ├── skills/    <name>/SKILL.md      ← Agent Skills (YAML frontmatter: name, description)
    └── checks/    *.md                 ← code-review Checks (review criteria + YAML frontmatter)
```

Amp **also** discovers `.claude/skills/` and `~/.claude/skills/` (compatibility). User-scope skills
live in `~/.config/agents/skills/`. Hooks and MCP are **settings-driven** (the `amp.hooks` array and
`amp.mcpServers` object in an Amp settings file / editor `settings.json`), not standalone committed
files. Skills may bundle an `mcp.json` and a `scripts/` subdir.

**gald3r writes**: `AGENTS.md` + `.agents/skills/<name>/SKILL.md` (and may reuse `.claude/skills/`);
hooks + MCP go into the Amp settings file.
**Amp owns**: the `.agents/` namespace, the settings-file `amp.*` schema, the Plugin API runtime, and
**Sourcegraph code-intelligence** indexing (cross-repo search / dependency analysis — Amp-managed,
not a gald3r-writable surface).

---

## 2. AI Instruction File

Amp reads, in a **hierarchical/cascading** lookup: cwd → parent dirs → subtrees (loaded when the
agent reads files there) → user config (`~/.config/amp/`) → system-wide. The primary file is
**`AGENTS.md`**; `AGENT.md` (project root) and **`CLAUDE.md`** are read for compatibility. YAML
frontmatter **`globs`** allow file-pattern-scoped instructions. No dedicated `AMP.md` is required —
gald3r's `AGENTS.md` is the first-class input (and an existing `CLAUDE.md` is still honored).

---

## 3. Agents Support — ⚠️ PARTIAL

- **No declarative user-authored subagent file.** Unlike Claude Code / Cursor (where a subagent role
  is a stand-alone definition file), Amp users **cannot define a subagent directly**.
- Amp **auto-spawns** subagents for suitable tasks (mostly **smart** mode); you can *encourage* their
  use by mentioning subagents in the prompt ("While you can't define a subagent in Amp, you can
  directly tell Amp to spawn a subagent.").
- Built-in modes: **deep / smart / rush**. Plugins **can** create custom agents and expose them as
  custom modes via the **experimental** API
  (`amp.experimental.createAgent()` / `amp.experimental.registerAgentMode()`).
- gald3r `g-agnt-*` definitions do **not** map to a native Amp subagent file — they would require a
  plugin (experimental API) or be reduced to prompt-time guidance / Skills.
- Source: https://ampcode.com/manual/plugin-api

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` directories) discovered in **`.agents/skills/`** (workspace),
  **`~/.config/agents/skills/`** (user), and — for compatibility — **`.claude/skills/`** /
  `~/.claude/skills/`. Frontmatter: **`name`**, **`description`**. Skills may bundle an `mcp.json`
  and a `scripts/` subdir.
- Skills let the agent lazily-load specific tool instructions in a very context-efficient way.
  Announced **2025-12-10**; now the **recommended** extensibility path (commands and the old
  toolbox mechanism are being migrated into Skills).
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/`.
- Source: https://ampcode.com/news/agent-skills

## 5. Commands / Workflows — ✅ NATIVE (deprecating → Skills)

- **Custom slash commands**: markdown in **`.agents/commands/<name>.md`** → creates `/<name>`; the
  file contents are inserted into the prompt input. **Executable** files with a `#!` shebang also
  become slash commands. Plugins additionally register command-palette commands via
  `amp.registerCommand()`.
- **RECENCY:** Amp announced **"removing custom commands in favor of skills" (2026-01-29)**. File-based
  commands still work but are being **folded into Skills** — migration guidance: convert a command
  script into a `SKILL.md` + `scripts/` subdir. gald3r `@g-*` / `/g-*` command portability should
  therefore prefer Skills (or plugin `registerCommand`).
- Source: https://ampcode.com/news/slashing-custom-commands

## 6. Hooks System — ✅ NATIVE (two surfaces; settings-array is Preview)

- **TWO surfaces:**
  1. **Settings-file `amp.hooks` array** — event + action pairs. Events e.g. **`tool:pre-execute`**,
     **`tool:post-execute`**; actions e.g. **`send-user-message`**, **`redact-tool-input`**, with
     `tool` / input-pattern conditions. (Shipped as **Preview**, 2025-05-13.)
  2. **Plugin API lifecycle events** via **`amp.on(...)`** — **`session.start`**, **`agent.start`**,
     **`tool.call`** (request event; return action `allow` | `reject-and-continue` | `modify` |
     `synthesize`), **`tool.result`**, **`agent.end`** (action `continue`).
- Hooks deterministically override Amp's behavior when `AGENTS.md` is not sufficient (e.g. prevent
  writing deprecated APIs, nudge running individual tests).
- **gald3r caveat:** gald3r `g-hk-*.ps1` hooks fire via **commands/events**, but Amp does **not**
  document a single uniform, stable, file-based hook contract (e.g. a `SessionStart` shell script the
  way Augment/Claude do). The settings-array form is **Preview**, and the richest control
  (`tool.call` allow/reject) is **Plugin-API-only** — so gald3r session-start / pre-commit hooks need
  to be expressed as an `amp.hooks` entry or a plugin `amp.on('session.start', …)`, not a drop-in
  `.ps1` file. (OS note: Amp's hook commands are not documented as Windows-PowerShell-specific the way
  Augment's `.ps1` support is — treat shell choice as platform-default.)
- Source: https://ampcode.com/news/hooks

## 7. Rules / Memory — ✅ NATIVE

- **`AGENTS.md`** (primary) + `AGENT.md` + legacy **`CLAUDE.md`**, with **hierarchical** lookup
  (cwd, parent dirs, subtrees, `~/.config/amp/`, system-wide). YAML frontmatter **`globs`** provide
  file-pattern-scoped guidance — the closest analog to Cursor's per-rule scoping.
- gald3r `g-rl-*` content maps into `AGENTS.md` (always-on guidance) or glob-scoped sections.
- Source: https://ampcode.com/manual

## 8. MCP Support — ✅ NATIVE

- MCP servers via the **`amp.mcpServers`** config object + the **`amp mcp add`** CLI. Supports
  **local** (`command` / `args` / `env`) and **remote** (`url` / `headers`) servers, **OAuth**
  (`amp mcp oauth login`), and **per-skill bundling** via a skill's `mcp.json`.
  e.g. `amp mcp add context7 -- npx -y @upstash/context7-mcp` or
  `amp mcp add linear https://mcp.linear.app/sse`.
- Editor integrations expose `amp.mcpServers` in `settings.json`.
- Source: https://ampcode.com/manual

## 9. Plugins / Code-Review Checks — distribution + extensibility channel

- The **Plugin API** is the most powerful (and increasingly primary) surface:
  `amp.registerCommand` (palette commands), `amp.registerTool` (custom tools exposed to the model),
  `amp.on` (lifecycle events / hooks), and `amp.experimental.createAgent` +
  `registerAgentMode` (custom agents/modes). This is the natural channel for a gald3r Amp plugin and
  the **only** way to approximate declarative subagents.
- **Code-review Checks**: user-defined review criteria as Markdown files with YAML frontmatter in
  **`.agents/checks/`**, scoped to parts of the codebase (codify team conventions / security
  invariants).
- **Toolboxes** (UNIX-style executable tool dirs, formerly `AMP_TOOLBOX`) are **NO LONGER SUPPORTED**
  — superseded by Skills + Plugins.
- Curated community extensions: `github.com/ampcode/amp-contrib` and
  `sourcegraph/amp-examples-and-guides`.
- Source: https://ampcode.com/manual/plugin-api

---

## Parity vs. Cursor Reference

Amp reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, skills, hooks, and MCP**. The one gap is **agents** — there is **no declarative
subagent file** (auto-spawn + experimental-plugin API only), so it stays **⚠️ partial**. Two further
caveats: (1) file-based custom slash commands are being **deprecated in favor of Skills** (2026-01-29),
so command portability should target Skills; (2) the settings-array hook form is **Preview** and the
richest hook control is **Plugin-API-only**. The **Sourcegraph code-intelligence** index (cross-repo
search / dependency analysis) is an Amp-native bonus with no Cursor analog — retrieval, not a writable
store.

**Reuse note:** because Amp reads `AGENTS.md` and discovers `.claude/skills/`, gald3r's instruction
file and Skills are **largely reusable** — but gald3r **agents** and **file-based commands** do
**not** port cleanly (agents need a plugin; commands should become Skills). The cheapest high-parity
Amp install is: ship `AGENTS.md` + `.agents/skills/` (or reuse `.claude/skills/`), express
gald3r commands as Skills, and wire hooks via `amp.hooks` / a plugin.

## Hook System

- **Type**: native — **two surfaces** (settings-file `amp.hooks` array [Preview] + Plugin API `amp.on`)
- **Config file**: Amp settings file (`amp.hooks` array) / editor `settings.json`; Plugin API for `amp.on`
- **Events available**: settings-array: `tool:pre-execute`, `tool:post-execute` (+ `tool`/input-pattern conditions); Plugin API: `session.start`, `agent.start`, `tool.call`, `tool.result`, `agent.end`
- **Actions**: `send-user-message`, `redact-tool-input` (array); `allow` / `reject-and-continue` / `modify` / `synthesize` (tool.call) / `continue` (agent.end)
- **Event payload format**: in-process event objects (Plugin API); action/condition fields in the settings array
- **Command extensions**: shell commands / executable scripts (no documented Windows-PowerShell-specific contract — platform default)
- **gald3r hook files**: `g-hk-*.ps1` do **not** drop in as files — re-express as an `amp.hooks` entry or a plugin `amp.on('session.start', …)`

## Atypical Handling

- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** (though `CLAUDE.md` is read for compat) — ship
  `AGENTS.md` for Amp.
- **No declarative subagents** — the main agent auto-spawns them; custom agents require an
  experimental plugin API.
- **Commands are deprecating into Skills** (2026-01-29) — prefer Skills for portability.
- **Hooks split across two surfaces**; the settings-array form is Preview.
- **Sourcegraph code-intelligence** augments Skills/agents (cross-repo consumer tracing) but is not a
  gald3r-writable surface.

## gald3r Integration Notes

- Ship `AGENTS.md` (primary instruction file) + `.agents/skills/<name>/SKILL.md`; gald3r Skills also
  load from `.claude/skills/`.
- Convert gald3r commands to **Skills** (file-based `.agents/commands/` is deprecating).
- Express hooks as `amp.hooks` entries or a plugin `amp.on(...)` — not drop-in `.ps1`.
- gald3r agents need a **plugin** (experimental `createAgent`/`registerAgentMode`) or degrade to
  Skills / prompt guidance.
- Re-verify on the next `@g-platform-scan-docs amp` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

(Agents: ⚠️ partial — no declarative subagent file; auto-spawn + experimental plugin API only.)

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://ampcode.com/manual)

| Capability | How verified |
|---|---|
| Commands | /news/slashing-custom-commands — `.agents/commands/<name>.md` → `/<name>`; shebang executables; plugin `amp.registerCommand`. NOTE: "removing custom commands in favor of skills" (2026-01-29) |
| Rules | /manual — `AGENTS.md` (primary) + `AGENT.md` + legacy `CLAUDE.md`; hierarchical (cwd/parents/subtrees/`~/.config/amp/`/system); YAML `globs` for file-scoped guidance |
| Agents | /manual/plugin-api — ⚠️ no declarative subagent file; auto-spawned (smart); built-in deep/smart/rush; plugins via experimental `createAgent`/`registerAgentMode` |
| Skills | /news/agent-skills — `SKILL.md` in `.agents/skills/` + `~/.config/agents/skills/` + `.claude/skills/` (compat); frontmatter name/description; announced 2025-12-10; recommended path |
| Hooks | /news/hooks — settings-file `amp.hooks` array (`tool:pre-execute`/`tool:post-execute`, send-user-message/redact-tool-input) [Preview 2025-05-13] + Plugin API `amp.on(session.start/agent.start/tool.call/tool.result/agent.end)` |
| MCP | /manual — `amp.mcpServers` config + `amp mcp add`; local (command/args/env) & remote (url/headers); OAuth `amp mcp oauth login`; per-skill `mcp.json` |
| Checks | /manual — `.agents/checks/*.md` review criteria with YAML frontmatter, codebase-scoped |
| Cross-compat | Amp reads `AGENTS.md`/`CLAUDE.md` and discovers `.claude/skills/` → gald3r instruction file + Skills reusable; agents/commands do NOT port cleanly |
