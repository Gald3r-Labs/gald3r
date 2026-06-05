---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: antigravity
authoring_path: update
docs_url: https://antigravity.google/docs/home
docs_url_secondary:
  - https://antigravity.google/docs/rules-workflows
  - https://antigravity.google/docs/subagents
  - https://antigravity.google/docs/skills
  - https://antigravity.google/docs/hooks
  - https://antigravity.google/docs/mcp
  - https://antigravity.google/docs/command
  - https://codelabs.developers.google.com/getting-started-with-antigravity-skills
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1465
---

# PLATFORM_SPEC.md — Google Antigravity (agent-first IDE + CLI + SDK)

Google Antigravity (DeepMind) is an **agent-first** development platform — a desktop IDE, a CLI,
and an SDK that share **one agent harness**. As of the **Antigravity 2.0 relaunch** (agent-first;
Subagents / Hooks / Scheduled Tasks / Agent Management announced at **Google I/O 2026, May 2026**),
the IDE/CLI harness natively supports **all six** gald3r-relevant extension primitives — Workflows
(slash commands), Rules, dynamic Subagents, Agent Skills (`SKILL.md`), lifecycle Hooks, and MCP.
Critically for gald3r, Antigravity reads **`AGENTS.md`** (cross-tool) and **`GEMINI.md`**
(Antigravity-specific, higher precedence), and discovers **Anthropic-format `SKILL.md`** packages,
so gald3r's existing `AGENTS.md` + `g-skl-*/SKILL.md` artifacts are **largely drop-in reusable**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://antigravity.google/docs (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: 2026-05-28`) which
conservatively marked hooks/skills/rules as `❓`/`⚠️` — they are now confirmed **NATIVE** in the
post-2.0 IDE/CLI harness.

> **Surface split (READ THIS):** the capability ratings below reflect the **Antigravity IDE / CLI
> product** (one shared harness; docs at `antigravity.google/docs`). The hosted **Gemini API
> "Managed Agents"** surface (`ai.google.dev/gemini-api/docs/antigravity-agent`) is a **separate
> product** that currently states *custom tools / function-calling* and *subagent delegation* are
> **"not yet supported."** Do **not** conflate the two — gald3r targets the IDE/CLI harness, which
> **does** support hooks + subagents.

> **Instruction-file convention:** Antigravity reads **`AGENTS.md`** (cross-tool, shared with Cursor
> / Claude Code) and **`GEMINI.md`** (Antigravity-specific). It does **not** rely on `CLAUDE.md`.
> Precedence: **System Rules** (immutable, DeepMind) > **`GEMINI.md`** > **`AGENTS.md`**.

---

## 1. Folder Hierarchy

Antigravity 2.0 splits config between **project-local** dirs and **user-global** state under
`~/.gemini/` (shared with the Gemini CLI state tree).

```
<project-root>/
├── AGENTS.md                        ← instruction file Antigravity reads (cross-tool)
├── GEMINI.md                        ← Antigravity-specific instructions (higher precedence)
└── .agents/                         ← workspace customization root
    ├── rules/        *.md           ← Manual / Always On / Model Decision / Glob (≤12,000 chars each)
    ├── skills/       <name>/SKILL.md ← Agent Skills (Anthropic SKILL.md standard)  [path varies — see §4]
    └── hooks.json                   ← lifecycle hooks (workspace scope)
.antigravity/
    └── mcp.json                     ← project-local MCP config { "mcpServers": { ... } }

~/.gemini/                           ← user-global state (Gemini-namespaced)
├── GEMINI.md                        ← global Antigravity-specific rules
├── AGENTS.md                        ← global cross-tool rules (v1.20.3+)
├── config/                          ← global customizations (hooks.json customization dir)
└── antigravity/
    ├── skills/                      ← global Agent Skills (all workspaces)
    ├── mcp_config.json              ← global MCP config (same mcpServers shape)
    └── global_workflows/            ← saved-prompt Workflows (slash commands, /)
```

> **Path caveat (skills):** the workspace skill dir is cited across official + community sources as
> **`.agents/skills/`** AND **`.antigravity/skills/`** AND **`.agent/skills/`** (singular). Native
> skill discovery is unambiguous; the **exact canonical path should be pinned by a live install test**
> before being hard-coded into gald3r installers. Global-scope is `~/.gemini/antigravity/skills/`.

- **gald3r writes**: `AGENTS.md`, `GEMINI.md` (Antigravity-only directives), `.agents/skills/<name>/SKILL.md`, `.agents/rules/*.md`, `.agents/hooks.json`, `.antigravity/mcp.json`
- **Platform owns**: `~/.gemini/` global state, IDE settings, the Orchestrator/subagent runtime, System Rules (immutable)

---

## 2. AI Instruction File

Antigravity reads, in precedence order: **System Rules** (immutable, DeepMind) → **`GEMINI.md`**
(Antigravity-specific) → **`AGENTS.md`** (cross-tool, also read by Cursor / Claude Code). Global
variants live at `~/.gemini/GEMINI.md` and `~/.gemini/AGENTS.md` (cross-tool global, v1.20.3+). No
dedicated `ANTIGRAVITY.md` is required — gald3r's `AGENTS.md` is a first-class input. For
**Antigravity-only must-win directives**, put them in `GEMINI.md` (it wins over `AGENTS.md`).
Antigravity also has a durable **"memories"** concept (agent state) distinct from rule files.

---

## 3. Agents Support — ✅ NATIVE (platform) / ⚠️ gald3r `g-agnt-*.md` convention does NOT auto-map

- **Dynamic Subagents**: an **Orchestrator** (dispatch-only manager) decomposes the goal and spawns
  subagents **on the fly** (`start_subagent` tool) with isolated context; they run **asynchronously
  in the background** and communicate via unique agent IDs. **Agent Management** groups conversations
  by "project" with its own settings/permissions.
- **IMPORTANT gald3r nuance:** subagents are **dynamic** — there is **no documented file-based
  static-role discovery** (no honored `.agents/agents/` dir for `g-agnt-*.md`). gald3r's markdown
  agent-role files **do NOT auto-map**; fold critical agent guidance into **rules/skills** instead.
- **Orchestrator self-handoff**: tracks cumulative subagent spawn count; on hitting a limit it dumps
  state to handoff files, kills background tasks, and spawns a successor that resumes — relevant to
  gald3r long-running autonomous loops.
- **Managed Agents caveat**: the separate hosted Gemini API "Managed Agents" SDK currently states
  *subagent delegation is not yet supported* — that is the **hosted-SDK** limitation, distinct from
  the IDE/CLI harness which **does** spawn subagents.
- Source: https://antigravity.google/docs/subagents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (Anthropic **`SKILL.md`** open format, progressive disclosure): a directory-based
  package containing a definition file (`SKILL.md`) + optional supporting assets. Frontmatter: `name`
  (optional / unique / lowercase-hyphen), `description` (**mandatory** — the semantic trigger);
  markdown body. Loaded **on-demand** when the agent deems it relevant.
- **"The `SKILL.md` format is the same standard used by Claude Code, Cursor, and every other
  compatible agent."** gald3r `g-skl-*/SKILL.md` files are **directly compatible**.
- Directory path varies across official + community sources: workspace-scope cited as
  `.agents/skills/` **and** `.antigravity/skills/` **and** `.agent/skills/`; global-scope
  `~/.gemini/antigravity/skills/`. Native discovery is unambiguous; **pin the exact path via install
  test**. Same harness shared by the Antigravity CLI and IDE.
- Source: https://codelabs.developers.google.com/getting-started-with-antigravity-skills

## 5. Commands / Workflows — ✅ NATIVE

- **Workflows** (saved-prompt slash commands): markdown files invoked in Agent via a slash command
  `/<workflow-name>`. A workflow file contains a **title, description, and a series of steps**; files
  are limited to **12,000 chars**. Created via **+ Global** (all workspaces) or **+ Workspace**;
  global workflows are stored at `~/.gemini/antigravity/global_workflows/`. A dedicated `/docs/command`
  page also exists.
- gald3r `@g-*` / `/g-*` commands map directly to Workflows (the closest analogue).
- Source: https://antigravity.google/docs/rules-workflows

## 6. Hooks System — ✅ NATIVE

- **Lifecycle Hooks** (added in **Antigravity 2.0 / Google I/O 2026, May 2026**): execute custom
  **local shell scripts** at critical stages of the agent's execution cycle. Configured in
  **`hooks.json`** in the customization dir (`.agents/` workspace, or `~/.gemini/config/` global;
  **workspace precedence**). Hooks receive input via **stdin as JSON** and return output via **stdout
  as JSON**.
- **Hook points**: `before_tool_call`, `after_tool_call` (logging), `before_model_call` (inject
  system instructions), `after_model_call` (override exit rules), `on_loop_stop`, `on_error`.
- gald3r PowerShell hooks (`g-hk-*.ps1`) can be wired as the executed shell scripts:
  `before_tool_call` ~ preToolUse, `on_loop_stop` ~ stop, `before_model_call` enables
  session-start-style instruction injection.
- Source: https://antigravity.google/docs/hooks

## 7. Rules / Memory — ✅ NATIVE

- **Rules** are plain **Markdown** files of constraints. **Activation types**: **Manual**
  (at-mention), **Always On**, **Model Decision** (NL description), **Glob** (file pattern). Each rule
  file is limited to **12,000 chars**. Global rules: `~/.gemini/GEMINI.md`; workspace rules:
  `.agents/rules/` of the workspace/git root.
- **A full always-on guarantee exists** (`Always On` activation) — stronger than the partial picture
  in the prior gald3r spec. Precedence: **System Rules** (immutable, DeepMind) > **`GEMINI.md`** >
  **`AGENTS.md`**. A durable **"memories"** concept also exists.
- gald3r `g-rl-*` map to **Always On** (for `alwaysApply: true`) or **Model Decision** (for
  `description:`-scoped) rules.
- Source: https://antigravity.google/docs/rules-workflows

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol**: connect local tools, databases, and external services. Config shape
  `{ "mcpServers": { ... } }` at **`.antigravity/mcp.json`** (project) or
  **`~/.gemini/antigravity/mcp_config.json`** (global; Settings → Customizations → Open MCP Config).
  Both a **JSON-file config** and a **GUI MCP Store** ("..." dropdown → Browse & Install &
  Authenticate). Trusted/owned-workspace security gating for write-capable servers.
- gald3r MCP servers (e.g. `example_app`) integrate via the `mcpServers` JSON.
- Source: https://antigravity.google/docs/mcp

## 9. Scheduled Tasks — ✅ NATIVE (Antigravity-native bonus)

- **Scheduled Tasks** (Antigravity 2.0): define **crons** to trigger agent invocations on a schedule.
  Adoptable for gald3r heartbeat / scheduled jobs.
- Source: https://antigravity.google/docs/hooks + I/O 2026 deep-dive
  https://antigravity.google/blog/google-io-2026-feature-deep-dive

---

## Parity vs. Cursor Reference

Antigravity now reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`):
native **commands (Workflows), rules, agents (dynamic subagents), skills, hooks, and MCP**, plus an
Antigravity-native **Scheduled Tasks** bonus with no Cursor analog. The one structural caveat is that
**subagents are dynamic (Orchestrator-spawned)** — there is no file-based `g-agnt-*.md` role
discovery, so gald3r agent-role files must be folded into rules/skills rather than dropped into an
agents dir.

**Reuse note (important):** because Antigravity reads `AGENTS.md` + `GEMINI.md` and discovers
Anthropic-format `SKILL.md` packages, gald3r's **`AGENTS.md` + `g-skl-*/SKILL.md` artifacts are
largely reusable on Antigravity without a separate port**. The exact skill directory path
(`.agents/skills` vs `.antigravity/skills` vs `.agent/skills`) and the hook payload schemas should be
**pinned by a live install test** before being hard-coded into installers.

## Hook System

- **Type**: native (`hooks.json`, shell scripts, stdin/stdout JSON)
- **Config file**: `hooks.json` in the customization dir — `.agents/` (workspace) or `~/.gemini/config/` (global); **workspace precedence**
- **Events available**: `before_tool_call`, `after_tool_call`, `before_model_call`, `after_model_call`, `on_loop_stop`, `on_error`
- **Event payload format**: JSON via **stdin**; result returned as JSON via **stdout**
- **Command extensions**: local **shell scripts** (official examples are `.sh`); gald3r `g-hk-*.ps1` wired via `{ "type":"command", "command":"powershell -File …" }`
- **gald3r hook files**: `g-hk-*.ps1` map to `before_tool_call` (pre-tool guards), `on_loop_stop` (stop), `before_model_call` (session-start-style instruction injection)
- **OS note**: hooks invoke local shell — Windows wiring routes through PowerShell; **pin payload schema via install test**

## Atypical Handling

- **Two products, one name**: the **IDE/CLI harness** (full extensibility — this spec) vs the hosted
  **Gemini API "Managed Agents"** (separate; *no subagents / custom tools yet*). Do not conflate.
- **Instruction file**: `AGENTS.md` + `GEMINI.md` (NOT `CLAUDE.md`); `GEMINI.md` outranks `AGENTS.md`;
  immutable **System Rules** sit above both.
- **Dynamic subagents**: Orchestrator spawns subagents on the fly — no static `g-agnt-*.md` dir.
- **Global state** is Gemini-namespaced under `~/.gemini/` (shared with the Gemini CLI tree).
- **Skill dir path** is not yet canonical across sources — pin via install test.

## gald3r Integration Notes

- Ship gald3r's **`AGENTS.md` + `g-skl-*/SKILL.md`** — Antigravity reads/discovers them natively.
- Put **Antigravity-only must-win directives in `GEMINI.md`** (outranks `AGENTS.md`).
- Hooks fire natively (shell scripts; `.ps1` via `powershell -File`) — `before_model_call` covers
  session-start injection, `on_loop_stop` covers stop, `before_tool_call` covers `.gald3r/` guards.
- Fold `g-agnt-*` guidance into **rules/skills** (no file-based subagent discovery).
- Adopt **Scheduled Tasks** (crons) for gald3r heartbeat jobs.
- **Evidence caveat**: `antigravity.google/docs/*` is a JS SPA (WebFetch returned title only);
  capability evidence comes from search-engine extractions quoting the official pages verbatim,
  cross-checked against multiple 2026 sources + Google codelabs. **Pin skill path + hook payload
  schema via a live install test** before hard-coding.
- New, high-churn platform (relaunched ~2026-05-19) — re-verify on the next
  `@g-platform-scan-docs antigravity` (`crawl_max_age_days: 7`).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

> **Agents (6th primitive):** ✅ **native** dynamic subagents at the **platform** level; ⚠️ the gald3r
> **`g-agnt-*.md` file convention does not auto-map** (no static-role discovery) — fold into rules/skills.

---

## Verification Evidence (docs crawl 2026-06-02, https://antigravity.google/docs)

| Capability | How verified |
|---|---|
| Commands / Workflows | /docs/rules-workflows — Workflows = markdown saved-prompts, `/workflow-name`, title/description/steps, ≤12,000 chars, Global vs Workspace; also /docs/command |
| Rules | /docs/rules-workflows — Markdown rules; activation Manual / Always On / Model Decision / Glob; ≤12,000 chars; `~/.gemini/GEMINI.md` (global) + `.agents/rules/` (workspace); precedence System Rules > GEMINI.md > AGENTS.md |
| Agents | /docs/subagents — dynamic Orchestrator-spawned subagents (`start_subagent`), async/background, agent IDs, Agent Management; **no** file-based `g-agnt-*.md` discovery |
| Skills | codelabs (getting-started-with-antigravity-skills) — Anthropic `SKILL.md` standard ("same as Claude Code, Cursor"); YAML frontmatter (`name` optional, `description` mandatory); on-demand load; path `.agents`/`.antigravity`/`.agent` skills (pin via install test) |
| Hooks | /docs/hooks — `hooks.json` shell scripts, stdin/stdout JSON; events `before_tool_call` / `after_tool_call` / `before_model_call` / `after_model_call` / `on_loop_stop` / `on_error`; global + workspace (workspace precedence); added Antigravity 2.0 / I/O 2026 |
| MCP | /docs/mcp — `{ "mcpServers": {...} }` at `.antigravity/mcp.json` (project) / `~/.gemini/antigravity/mcp_config.json` (global); MCP Store GUI; owned-workspace gating |
| Instruction file | /docs/rules-workflows — `AGENTS.md` (cross-tool, also Cursor/Claude Code) applied after `GEMINI.md`; global `~/.gemini/GEMINI.md` + `~/.gemini/AGENTS.md` (v1.20.3+) |
| Scheduled Tasks | /docs/hooks + blog/google-io-2026-feature-deep-dive — cron-style agent invocations |
| Surface separation | ai.google.dev/gemini-api/docs/antigravity-agent — hosted "Managed Agents": custom tools + subagent delegation "not yet supported" → distinct from IDE/CLI harness rated here |
| Evidence method | antigravity.google/docs/* is a JS SPA (WebFetch → title only); ratings from search-engine extractions quoting official pages verbatim, cross-checked vs multiple 2026 sources + Google codelabs; confirmed pages: /docs/rules-workflows, /docs/mcp, /docs/subagents, /docs/hooks, /docs/agent, /docs/command, /docs/task-list |
