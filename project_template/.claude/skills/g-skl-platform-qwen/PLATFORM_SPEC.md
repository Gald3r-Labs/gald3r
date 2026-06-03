---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: qwen
authoring_path: update
docs_url: https://qwenlm.github.io/qwen-code-docs/
docs_url_secondary:
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/sub-agents/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/
  - https://qwenlm.github.io/qwen-code-docs/en/core/memport/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/
  - https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/
crawl_max_age_days: 14
vault_doc_path: research/platforms/qwen/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1480
---

# PLATFORM_SPEC.md — Qwen Code (Alibaba CLI coding agent)

Qwen Code (`qwen` command, Alibaba / `QwenLM/qwen-code`) is an open-source terminal AI coding agent
and an **adapted fork of Google's Gemini CLI**, optimized for the Qwen3-Coder models. As of
mid-2026 it natively supports **all six** gald3r-relevant extension primitives — custom slash
commands, rules/memory, subagents, Agent Skills, lifecycle hooks, and MCP. It inherits
commands/memory/MCP from its Gemini-CLI lineage and has since added a **Claude-Code-style hooks
system (14 events)**, **Markdown subagents**, and **Anthropic-style Agent Skills (`SKILL.md`)** that
reached **GA (the `--experimental-skills` flag was removed) in the 2026-02-09 v0.9.x release**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://qwenlm.github.io/qwen-code-docs/
(see Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never` / `2026-05-20`)
which incorrectly marked hooks/skills as unsupported and agents/commands as partial — they are now all
NATIVE in Qwen Code.

> **Instruction-file truth (read carefully):** Qwen Code's default context/instruction file is
> **`QWEN.md`** (hierarchically loaded), **not `AGENTS.md`**. `context.fileName` is configurable and
> can be set to `AGENTS.md` (or an array including it), but `AGENTS.md` is **not a built-in default
> search target** — making it one is an open feature request (GitHub issue #2006). The repo itself
> ships an `AGENTS.md`, but that does not make it the CLI's auto-loaded default. `CONTEXT.md` /
> `GEMINI.md` heritage exists from the Gemini-CLI fork lineage.

---

## 1. Folder Hierarchy

```
<project-root>/
├── QWEN.md                         ← default context/memory file Qwen reads (NOT AGENTS.md)
└── .qwen/
    ├── settings.json               ← model providers, context, hooks + mcpServers config
    ├── commands/    *.md | *.toml  ← custom slash commands (Markdown+YAML; TOML back-compat)
    ├── agents/      *.md           ← subagents (markdown + YAML frontmatter)
    └── skills/      <name>/SKILL.md  ← Agent Skills (SKILL.md, model-invoked)

~/.qwen/                            ← user-global mirror (settings.json, commands/, agents/, skills/, QWEN.md)
```

Qwen Code also has a first-class **Extensions** mechanism that can bundle commands + subagents/agents
+ MCP servers + context together for one-click distribution.

**gald3r writes**: `QWEN.md` (the native context file), `.qwen/settings.json` (hooks + MCP), and the
`.qwen/commands|agents|skills` trees. **Qwen owns**: the `.qwen/` namespace, `settings.json` schema,
the context-loading rules, and the Extensions registry.

---

## 2. AI Instruction File

Qwen Code loads **context files** (the platform's term for "memory"), defaulting to **`QWEN.md`** and
configurable via the **`context.fileName`** setting (string or array). Context is loaded
**hierarchically** — `~/.qwen/QWEN.md` (global) down through the project root and ancestor
directories, with more-specific files overriding/supplementing general ones — and **injected into
every conversation**. Modular `@file.md` imports are supported (Memory Import Processor). Managed
with `/memory show` and `/memory refresh`.

No dedicated `AGENTS.md` default exists: to use gald3r's `AGENTS.md` as the source of truth, set
`context.fileName` to include it, or (recommended) keep `QWEN.md` as a thin overlay that `@AGENTS.md`
imports.

- `QWEN.md` is personalized per user and gitignored (`g-rl-02` protected files).
- **Caveat (⚠️)**: `/memory` "save to memory" appends to the context file; guard against
  Qwen-injected memory overwriting gald3r-authored sections.

---

## 3. Agents Support — ✅ NATIVE

- **Subagents**: markdown + YAML frontmatter (`name`, `description`, optional `model`
  [`inherit`|model-id], `approvalMode` [`default`|`plan`|`auto-edit`|`yolo`], `tools` allowlist,
  `disallowedTools` blocklist); body is the system prompt. Stored in `.qwen/agents/` (project,
  highest precedence), `~/.qwen/agents/` (user), and extension-provided. Managed via `/agents` (with
  an `/agents create` wizard and `/agents manage`).
- gald3r `g-agnt-*` definitions map directly to Qwen subagent files.
- Source: https://qwenlm.github.io/qwen-code-docs/en/users/features/sub-agents/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` with YAML frontmatter `name`, `description`, optional `paths`, plus
  optional supporting scripts/templates in a per-skill folder). Stored at
  `~/.qwen/skills/<skill-name>/SKILL.md` (personal) or `.qwen/skills/<skill-name>/SKILL.md`
  (project). **Model-invoked** (auto-selected by `description`). Browsed via `/skills`. Reached **GA
  (`--experimental-skills` flag removed) in the 2026-02-09 v0.9.x release** after debuting in v0.6.0.
- gald3r `g-skl-*/SKILL.md` load natively.
- Source: https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: **Markdown with optional YAML frontmatter** (TOML deprecated but kept
  for back-compat). Stored in `~/.qwen/commands/` (global) or `<project>/.qwen/commands/` (project,
  overrides global). Subdirectory path separators become `:` for namespacing (e.g. `git/commit.md`
  → `/git:commit`). Supports `{{args}}` parameter injection. File-based commands take precedence over
  built-ins on a name conflict.
- gald3r `@g-*` / `/g-*` commands map directly into `.qwen/commands/`.
- Source: https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** configured in `.qwen/settings.json` under a `"hooks"` object keyed by event,
  each with a `"matcher"` regex and a list of hooks of type **`command`** (shell/bash/**PowerShell**
  via stdin/stdout JSON) or **`http`** (POST). **14 events**: `PreToolUse`, `PostToolUse`,
  `PostToolUseFailure`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`, `Stop`, `StopFailure`,
  `SubagentStart`, `SubagentStop`, `PreCompact`, `PostCompact`, `Notification`, `PermissionRequest`.
  Supports timeouts and env vars. Because `command` hooks can invoke PowerShell, gald3r `g-hk-*.ps1`
  hooks wire **natively** (SessionStart context injection, PreToolUse `.gald3r/` guards, pre-commit
  gates, etc.).
- Source: https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/

## 7. Rules / Memory — ✅ NATIVE

- Persistent context is the hierarchical **`QWEN.md`** context file (§2), loaded
  `~/.qwen/QWEN.md` → project root → ancestor dirs, with `@file.md` modular imports. "Always apply"
  is achieved by inlining/importing into `QWEN.md`; there is no separate `.mdc`-style rules folder
  with `alwaysApply:`/`globs:` frontmatter (that semantic comes from the context file, not a rules
  directory).
- gald3r `g-rl-*` map by being imported into `QWEN.md` (e.g. `@AGENTS.md`, which itself pulls the
  rule set). `alwaysApply: true` rules become inlined/imported context; `description:`-scoped rules
  are referenced as needed.
- **Token/size note (⚠️)**: `QWEN.md` (and its imports) is concatenated into every prompt — keep
  referenced rule content lean (`token_budget: low` in the skill frontmatter).
- Source: https://qwenlm.github.io/qwen-code-docs/en/core/memport/

## 8. MCP Support — ✅ NATIVE

- MCP servers configured via the **`mcpServers`** settings object (in `.qwen/settings.json` project
  or `~/.qwen/settings.json` user); each server needs at least one of `command` (stdio), `url` (SSE),
  or `httpUrl` (HTTP) transport. **OAuth** is supported for SSE/HTTP transports (`--oauth-*` flags).
  Servers can also be added via the CLI (`qwen mcp add`). Inspect/manage with `/mcp`. MCP servers may
  additionally expose prompts as slash commands.
- gald3r note: a root `.mcp.json` (`mcpServers` → gald3r server) is the portable surface; the
  authoritative native location is `.qwen/settings.json`. (`.mcp.json` is gitignored, machine-specific
  — `g-rl-02`.)
- Source: https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/

## 9. Extensions / Distribution — distribution channel

- Qwen Code's **Extensions** mechanism bundles commands + subagents/agents + MCP servers + context
  together for distribution and one-click install. This is the natural packaging channel for a gald3r
  Qwen bundle alongside (or instead of) per-file installs.
- Headless / Dual Output / Approval Mode: non-interactive headless runs, structured dual output, and
  a tiered `approvalMode` (`default` | `plan` | `auto-edit` | `yolo`) usable globally and per-subagent.
- `/export` writes session history to Markdown, JSONL, and HTML (added 2026-02) — an adoptable
  structured-output workflow.
- Source: https://qwenlm.github.io/qwen-code-docs/en/users/extension/introduction/

---

## Parity vs. Cursor Reference

Qwen Code now reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules/memory, agents, skills, hooks, and MCP**. Caveats are minor and platform-specific:
the default context file is **`QWEN.md`, not `AGENTS.md`** (AGENTS.md only via `context.fileName`);
"always-apply" rules live in the hierarchical context file rather than a dedicated rules folder; and
subagents/hooks/GA-skills are **recent 2026 additions** (skills went GA 2026-02-09) so confirm the
installed CLI version exposes them.

**Reuse note:** because Qwen tracks Gemini CLI and adds Claude-Code-style hooks/subagents/skills,
gald3r's `SKILL.md` skills and markdown subagents are largely drop-in once placed under `.qwen/`; the
cheapest high-parity install is a `QWEN.md` overlay (`@AGENTS.md`) plus the `.qwen/`
commands/agents/skills trees and a `.qwen/settings.json` carrying hooks + MCP.

## Hook System

- **Type**: native (settings.json hooks)
- **Config file**: `.qwen/settings.json` (`"hooks"` object)
- **Events available**: PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, SessionStart,
  SessionEnd, Stop, StopFailure, SubagentStart, SubagentStop, PreCompact, PostCompact, Notification,
  PermissionRequest (14 events)
- **Event payload format**: JSON via stdin/stdout; hook types `command` (shell/bash/PowerShell) or
  `http` (POST); per-event `matcher` regex, timeouts, env vars
- **Command extensions**: any shell, including **PowerShell** — so gald3r `g-hk-*.ps1` wire natively
- **gald3r hook files**: `g-hk-*.ps1` fire via the events above (SessionStart injection, PreToolUse
  `.gald3r/` guards, pre-commit/pre-push gates)

## Atypical Handling

- Qwen Code is a **Gemini CLI fork**: config is `.qwen/settings.json` (JSON, NOT `config.yaml`),
  custom commands, and the `QWEN.md` instruction file. The legacy deploy scaffold under
  `project_template/.gald3r_sys/platforms/.qwen/` (old `config.yaml` + `instructions.md`) is wrong and
  should be regenerated to `settings.json` + `QWEN.md`.
- Default context file is **`QWEN.md`, not `AGENTS.md`** — use `context.fileName` or a `@AGENTS.md`
  overlay to reuse the gald3r instruction set.
- Hooks are settings-driven (no standalone committed hook file); subagents/skills/GA-skills are
  recent 2026 additions — verify on the installed CLI version.

## gald3r Integration Notes

- Ship a `QWEN.md` overlay that `@AGENTS.md`-imports the gald3r instruction set; install commands,
  subagents, and `SKILL.md` skills under `.qwen/`.
- Hooks fire natively (PowerShell supported); no need to degrade session-start/pre-commit to manual.
- Because Qwen tracks Gemini CLI, re-check upstream additions on the next
  `@g-platform-scan-docs qwen` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ✅** — native 14-event hooks in `.qwen/settings.json` (`command`/`http`; PowerShell supported).
- **Rules ✅** — hierarchical `QWEN.md` context/memory with `@file.md` imports (`/memory` commands).
- **Skills ✅** — Agent Skills (`SKILL.md`) in `.qwen/skills/`, model-invoked; GA 2026-02-09.
- **Commands ✅** — native slash commands (Markdown+YAML; TOML back-compat) in `.qwen/commands/`.
- **MCP ✅** — first-class `mcpServers` (stdio/SSE/HTTP, OAuth) in `.qwen/settings.json`.
- **Docs Fresh ✅** — `last_doc_scan: 2026-06-02`.

---

## Verification Evidence (docs crawl 2026-06-02, https://qwenlm.github.io/qwen-code-docs/)

| Capability | How verified |
|---|---|
| Commands | /users/features/commands/ — Markdown+YAML in `.qwen/commands/` (TOML back-compat); `git/commit.md` → `/git:commit`; `{{args}}` |
| Rules / memory | /core/memport/ — `QWEN.md` context (default; `context.fileName`-configurable) hierarchically loaded + `@file.md` imports; `/memory show`/`refresh` |
| Agents | /users/features/sub-agents/ — markdown+YAML subagents in `.qwen/agents/` (highest precedence); `/agents` + create wizard; `approvalMode`/`tools` |
| Skills | /users/features/skills/ — `SKILL.md` Agent Skills in `.qwen/skills/`, model-invoked; GA (flag removed) 2026-02-09 v0.9.x (debut v0.6.0) |
| Hooks | /users/features/hooks/ — `.qwen/settings.json` `"hooks"`; 14 events; `command` (PowerShell ok) / `http`; matcher, timeouts, env |
| MCP | /users/features/mcp/ — `mcpServers` (command/url/httpUrl; OAuth on SSE+HTTP); `qwen mcp add`; `/mcp` |
| Instruction file | /users/configuration/settings/ — default `QWEN.md` (NOT `AGENTS.md`); `AGENTS.md` only via `context.fileName` (built-in default = open issue #2006) |
| Lineage | Open-source fork of Gemini CLI for Qwen3-Coder; config/command/memory/MCP mirror Gemini CLI; hooks+subagents+skills mirror Claude Code |
