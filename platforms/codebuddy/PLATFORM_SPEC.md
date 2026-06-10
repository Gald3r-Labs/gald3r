---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: codebuddy
authoring_path: create
docs_url: https://www.codebuddy.ai/docs/ide/Introduction
docs_url_secondary:
  - https://www.codebuddy.ai/docs/cli/slash-commands
  - https://www.codebuddy.ai/docs/cli/memory
  - https://www.codebuddy.ai/docs/cli/sub-agents
  - https://www.codebuddy.ai/docs/cli/skills
  - https://www.codebuddy.ai/docs/cli/hooks
  - https://www.codebuddy.ai/docs/cli/mcp
  - https://www.codebuddy.ai/docs/cli/plugins-reference
crawl_max_age_days: 14
vault_doc_path: research/platforms/codebuddy/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — CodeBuddy Code (Tencent Cloud Code Assistant)

CodeBuddy is a **Tencent Cloud** AI coding product spanning an **IDE/editor**, **IDE plugins**, and
the **`CodeBuddy Code` CLI/agent**. The CLI (released **Sep 2025**; **v2.0 Jan 2026** added Skills,
plan mode, ACP compatibility, an open SDK, and sandboxed execution) is **architecturally aligned with
Claude Code** and natively supports **all six** gald3r-relevant extension primitives — custom slash
commands, a `CODEBUDDY.md` + `.codebuddy/rules/` memory/rules system, Markdown sub-agents, an
Agent-Skills `SKILL.md` system, a rich lifecycle hooks system (**27+ events**), and full MCP
(stdio/SSE/HTTP). A **plugin** system bundles all of these together.

**Authoring path**: CREATE. **Verified 2026-06-02** against https://www.codebuddy.ai/docs (see
Verification Evidence). Because the `.codebuddy/` folder layout mirrors `.claude/` (settings.json
hooks, `SKILL.md` skills, Markdown sub-agents, `.mcp.json`), gald3r's **Claude-Code primitives are
highly portable** to CodeBuddy.

> **Surface split:** the full extensibility (commands/rules/agents/skills/hooks/MCP/plugins) lives in
> the **CodeBuddy Code CLI/agent**. The **IDE/editor and IDE plugins** expose a narrower surface
> (code-understanding/review with `@workspace` / `#Codebase`, MCP). Where a feature is CLI-only or has
> an IDE caveat it is noted inline.

> **Instruction-file divergence (important):** CodeBuddy reads **`CODEBUDDY.md`**, NOT `CLAUDE.md`.
> `AGENTS.md` is supported only as a **legacy fallback** when no `CODEBUDDY.md` exists. gald3r must
> ship a `CODEBUDDY.md` (or rely on the `AGENTS.md` fallback) — `CLAUDE.md` is not read.

> **Windows OS limit (important):** hooks are **"executed using the user's default shell on
> macOS/Linux, and Git Bash is enforced on Windows."** gald3r's PowerShell hooks (`g-hk-*.ps1`)
> therefore do NOT fire natively on Windows — they must be invoked through a Git Bash shim
> (`pwsh -File …`), or ported to POSIX shell. This is the single biggest porting caveat vs. Claude Code.

---

## 1. Folder Hierarchy

```
<project-root>/
├── CODEBUDDY.md                      ← instruction file CodeBuddy reads (NOT CLAUDE.md)
├── CODEBUDDY.local.md                ← personal overrides (auto-gitignored)
├── AGENTS.md                         ← legacy fallback (used only if no CODEBUDDY.md)
├── .mcp.json                         ← project MCP servers (JSONC: comments + trailing commas)
└── .codebuddy/
    ├── CODEBUDDY.md                  ← alt project-memory location
    ├── rules/      *.md              ← modular project rules (split CODEBUDDY.md)
    ├── commands/   *.md              ← custom slash commands (subdirs → /ns:cmd)
    ├── agents/     *.md              ← sub-agents (Markdown + YAML frontmatter)
    ├── skills/     <name>/SKILL.md   ← Agent Skills (model-invoked)
    ├── settings.json                 ← hooks (project scope)
    └── settings.local.json           ← local hook overrides
```

User scope mirrors this under `~/.codebuddy/` (`commands/`, `agents/`, `skills/`, `rules/`,
`memories/`, `settings.json`, `.mcp.json`, `CODEBUDDY.md`).

**gald3r writes**: `.codebuddy/commands/`, `.codebuddy/agents/`, `.codebuddy/skills/<name>/SKILL.md`,
`.codebuddy/rules/`, `.codebuddy/settings.json` (hooks), `.mcp.json`, and `CODEBUDDY.md`.
**CodeBuddy owns**: the `.codebuddy/` namespace, `settings.json` schema, the plan-mode / sandbox
runtime, and the IDE's code-understanding index (not a gald3r-writable surface).

---

## 2. AI Instruction File

CodeBuddy loads memory files into context at startup in hierarchical order. Project memory uses
**`CODEBUDDY.md`** if present; otherwise it falls back to **`AGENTS.md`**. Locations: `./CODEBUDDY.md`,
`./.codebuddy/CODEBUDDY.md`, `./CODEBUDDY.local.md` (auto-gitignored), and user scope
`~/.codebuddy/CODEBUDDY.md`, `~/.codebuddy/rules/`, `~/.codebuddy/memories/`. `CODEBUDDY.md` supports
**`@path/to/import`** to pull in additional files. New projects are recommended to use `CODEBUDDY.md`.
There is **no `CLAUDE.md` support** — gald3r ships `CODEBUDDY.md`.

---

## 3. Agents Support — ✅ NATIVE

- **Sub-Agents**: Markdown files with YAML frontmatter in `.codebuddy/agents/` (project, highest
  priority) and `~/.codebuddy/agents/` (user). Each runs in its **own context window** with a custom
  system prompt (the Markdown body). Frontmatter: `name`, `description`, `tools`, `model`
  (`inherit` supported), `permissionMode`, `skills` (auto-load). Plugin agents add `effort`,
  `maxTurns`, `disallowedTools`, `memory`, `background`, `isolation`. **Background agents** run
  sub-agent tasks without blocking the main conversation.
- gald3r `g-agnt-*` definitions map directly to CodeBuddy sub-agent files.
- Source: https://www.codebuddy.ai/docs/cli/sub-agents

## 4. Skills Support — ✅ NATIVE

- **CodeBuddy Code Skills (Agent Skills)**: a directory containing `SKILL.md` at
  `.codebuddy/skills/<name>/SKILL.md` (project) and `~/.codebuddy/skills/<name>/SKILL.md` (user).
  **Model-invoked** ("automatically identified and invoked by the AI model" based on task
  requirements) vs. user-initiated slash commands. Frontmatter: `name`, `description`,
  `allowed-tools`, `hooks`, `context` (set to `fork` to run in an isolated subagent context without
  conversation history), `user-invocable`. Also packageable in plugins.
- gald3r `g-skl-*/SKILL.md` load natively. **Skills were introduced in CodeBuddy Code v2.0
  (January 2026)** — older installs lack the feature.
- Source: https://www.codebuddy.ai/docs/cli/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: `.codebuddy/commands/*.md` (project) and `~/.codebuddy/commands/*.md`
  (global). A `test.md` file auto-registers as `/test`; **subdirectories become colon-namespaced**
  (e.g. `/frontend:build`). Supports YAML frontmatter (`description`, `argument-hint`,
  `allowed-tools`, `model`), `$1`/`$2`/`$ARGUMENTS` args, ``!`shell` `` execution, and `@file`
  references.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://www.codebuddy.ai/docs/cli/slash-commands

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks (27+ events)** configured in `.codebuddy/settings.json` (project),
  `~/.codebuddy/settings.json` (user), `.codebuddy/settings.local.json` (local overrides), plugin
  `hooks/hooks.json`, and inline in agent/skill `SKILL.md` frontmatter. Hooks **run shell commands or
  LLM prompts** to automate validation, bootstrap environments, run compliance checks, etc. Events
  include **PreToolUse, PostToolUse, PostToolUseFailure, SessionStart, SessionEnd,
  SubagentStart/SubagentStop, Stop, UserPromptSubmit, Notification,
  PermissionRequest/PermissionDenied, PreCompact/PostCompact, InstructionsLoaded, ConfigChange,
  TaskCreated/TaskCompleted, FileChanged, CwdChanged, WorktreeCreate/WorktreeRemove, Setup.**
  Commands receive **JSON via stdin** and respond via **exit codes / JSON output**.
- **OS limit:** hooks run under the user's default shell on macOS/Linux, but **Git Bash is enforced on
  Windows.** gald3r `g-hk-*.ps1` hooks do **not** fire natively on Windows — wire them via a Git Bash
  shim (`pwsh -NoProfile -File …`) or port to POSIX shell. The event coverage itself is a superset of
  Claude Code's, so the SessionStart context-injection / PreToolUse `.gald3r/` guard / pre-commit gate
  patterns all map once the shell-invocation shim is in place.
- Source: https://www.codebuddy.ai/docs/cli/hooks

## 7. Rules / Memory — ✅ NATIVE

- **Memory + Rules**: `CODEBUDDY.md` (legacy `AGENTS.md` fallback) plus modular
  `.codebuddy/rules/*.md`, at project (`./CODEBUDDY.md`, `./.codebuddy/CODEBUDDY.md`,
  `./CODEBUDDY.local.md`) and user (`~/.codebuddy/CODEBUDDY.md`, `~/.codebuddy/rules/`,
  `~/.codebuddy/memories/`) scopes. **All memory files are automatically loaded into context at
  startup** in hierarchical order. `.codebuddy/rules/` lets teams split instructions into focused
  files instead of one large `CODEBUDDY.md`; `CODEBUDDY.md` supports `@path` imports.
- gald3r `g-rl-*` map to `.codebuddy/rules/*.md` (always-loaded) or sections of `CODEBUDDY.md`.
- Source: https://www.codebuddy.ai/docs/cli/memory

## 8. MCP Support — ✅ NATIVE

- **MCP (Model Context Protocol)** servers via `.mcp.json` (user `~/.codebuddy/.mcp.json`, project
  `<root>/.mcp.json`, local scope under the user config `projects` field) and CLI commands
  (`codebuddy mcp add` / `mcp add-json`); also bundled in plugins (`.mcp.json` under plugin root or
  inline in `plugin.json`). **Three transports**: STDIO (local), SSE (remote), HTTP (remote
  streaming). Config is **JSONC** (comments + trailing commas). Sub-agents inherit all main-thread MCP
  tools when `tools` is omitted; skills access MCP via `allowed-tools`.
- Source: https://www.codebuddy.ai/docs/cli/mcp

## 9. Plugins / Other Extensibility — distribution channel

- **Plugin system** — a self-contained component directory bundling **Skills, Agents, Hooks, MCP
  servers, and LSP servers**. Plugin hooks live in `hooks/hooks.json` or inline in `plugin.json`;
  plugin MCP in `.mcp.json` or inline in `plugin.json`. **This is the natural distribution channel for
  a gald3r CodeBuddy plugin.**
  Source: https://www.codebuddy.ai/docs/cli/plugins-reference
- **Output styles / formats**, **`@workspace` / `#Codebase` / `@file` context references** (IDE +
  CLI), **LSP servers** (via plugins), and **ACP protocol compatibility + open SDK + plan mode +
  isolated sandbox execution** (all v2.0, Jan 2026) round out the surface.
  Sources: https://www.codebuddy.ai/docs/cli/best-practices ·
  https://www.codebuddy.ai/docs/ide/release-notes/release-notes

---

## Parity vs. Cursor Reference

CodeBuddy reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Caveats: the full surface is **CLI-only** (the
IDE/editor + plugins are narrower); the instruction file is **`CODEBUDDY.md`** (not `CLAUDE.md`); and
on **Windows hooks are forced under Git Bash** (PowerShell hooks need a shim). The plan-mode, open
SDK, ACP compatibility, and sandboxed execution are CodeBuddy-native bonuses with no Cursor analog.

**Reuse note (important):** because `.codebuddy/` mirrors `.claude/` (settings.json hooks, `SKILL.md`
skills, Markdown sub-agents, `.mcp.json`), gald3r's **Claude-Code platform artifacts are largely
portable to CodeBuddy** — the cheapest high-parity install copies the gald3r `.claude/` tree into
`.codebuddy/`, renames the instruction file to `CODEBUDDY.md`, and shims `.ps1` hooks for Git Bash on
Windows.

## Hook System

- **Type**: native (settings.json hooks — Claude-Code-aligned, superset event set)
- **Config file**: `.codebuddy/settings.json` (+ `settings.local.json`, user `~/.codebuddy/settings.json`)
- **Events available**: 27+ — PreToolUse, PostToolUse, PostToolUseFailure, SessionStart, SessionEnd,
  SubagentStart/SubagentStop, Stop, UserPromptSubmit, Notification,
  PermissionRequest/PermissionDenied, PreCompact/PostCompact, InstructionsLoaded, ConfigChange,
  TaskCreated/TaskCompleted, FileChanged, CwdChanged, WorktreeCreate/WorktreeRemove, Setup
- **Event payload format**: JSON via stdin; result via exit codes / JSON output
- **Command extensions**: shell commands (default shell on macOS/Linux); **Git Bash enforced on
  Windows** — `g-hk-*.ps1` must be invoked via a `pwsh -File …` Git Bash shim, not run natively

## Atypical Handling

- Three surfaces: the **CodeBuddy Code CLI** (full extensibility), the **IDE/editor**, and **IDE
  plugins** (both narrower — code understanding/review + MCP). Target the CLI for full gald3r parity.
- Instruction file is **`CODEBUDDY.md`** (legacy `AGENTS.md` fallback) — **not** `CLAUDE.md`.
- **Windows hooks run under Git Bash only** — the chief divergence from Claude Code.
- Skills require **CodeBuddy Code v2.0+** (Jan 2026). Also note **WorkBuddy** (Tencent desktop agent)
  is a separate, beta product — not covered by this CLI-focused spec.

## gald3r Integration Notes

- Copy gald3r's `.claude/`-format tree into `.codebuddy/` (commands/skills/agents) — directory
  conventions match; CodeBuddy discovers it.
- Ship `CODEBUDDY.md` (do not rely on a `CLAUDE.md` — it is not read).
- Wire hooks in `.codebuddy/settings.json`; on Windows shim `.ps1` via Git Bash (`pwsh -File`).
- Re-verify on the next `@g-platform-scan-docs codebuddy` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://www.codebuddy.ai/docs)

| Capability | How verified |
|---|---|
| Commands | /cli/slash-commands — `.codebuddy/commands/*.md` (+ `~/.codebuddy/`); subdirs → `/ns:cmd`; frontmatter + `$ARGUMENTS` + ``!`shell` `` + `@file` |
| Rules | /cli/memory — `CODEBUDDY.md` (legacy `AGENTS.md` fallback) + `.codebuddy/rules/*.md`; auto-loaded at startup; `@path` imports |
| Agents | /cli/sub-agents — `.codebuddy/agents/` md+YAML; own context window; `model: inherit`; background agents; plugin agents |
| Skills | /cli/skills — `.codebuddy/skills/<name>/SKILL.md`; model-invoked; `context: fork`; introduced v2.0 (Jan 2026) |
| Hooks | /cli/hooks — `.codebuddy/settings.json`; 27+ events; JSON stdin / exit-code output; **Git Bash enforced on Windows** |
| MCP | /cli/mcp — `.mcp.json` (user/project/local) + `codebuddy mcp add`/`add-json`; STDIO/SSE/HTTP; JSONC |
| Plugins | /cli/plugins-reference — self-contained bundle of Skills + Agents + Hooks + MCP + LSP servers |
| Instruction file | /cli/memory — reads **`CODEBUDDY.md`**, not `CLAUDE.md`; `AGENTS.md` legacy fallback only |
| Recency / SDK | /ide/release-notes — CLI released Sep 2025; v2.0 (Jan 2026) added Skills, plan mode, ACP, open SDK, sandbox |
