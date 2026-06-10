---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: continue
authoring_path: update
docs_url: https://docs.continue.dev
docs_url_secondary:
  - https://docs.continue.dev/customize/deep-dives/rules
  - https://docs.continue.dev/customize/deep-dives/prompts
  - https://docs.continue.dev/customize/deep-dives/mcp
  - https://docs.continue.dev/ide-extensions/agent/how-to-customize
  - https://github.com/continuedev/skills
  - https://github.com/continuedev/continue/issues/11678
  - https://github.com/continuedev/continue/issues/6716
crawl_max_age_days: 14
vault_doc_path: research/platforms/continue/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Continue (continue.dev)

Continue is an **open-source** AI coding assistant shipping in three surfaces: **IDE extensions**
(VS Code + JetBrains), a **CLI/TUI (`cn`)** with a headless mode for CI, and **Continue Cloud /
Background (async) Agents** that run long-running tasks (reviews, migrations, refactors) on a remote
devbox. Customization is **file-based** under a `.continue/` directory plus a **`config.yaml`**
assistant spec. Of the six gald3r-relevant mechanisms, **four are NATIVE** (commands/prompts, rules,
hooks, MCP) and **two are PARTIAL** (skills, agents) — see per-mechanism evidence below.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.continue.dev (see
Verification Evidence). Overall status is **⚠️ near-full** (not ✅) because **skills** and
**sub-agents** are not yet documented first-class `.continue/` runtime primitives.

> **Surface split:** the IDE extensions, the `cn` CLI/TUI, and Cloud/Background Agents share the
> `config.yaml` spec and the `.continue/` tree, **but not every mechanism spans every surface**.
> Hooks ship **CLI-only**; prompts/rules/MCP work across IDE + CLI + headless. Where a feature is
> surface-bound or doc-lagging it is noted inline.

> **Instruction-file truth (read this first):** Continue has **NO native single-file instruction
> convention** — it does **NOT** read `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`. Its persistent
> instruction layer is the **`.continue/rules/*.md`** folder (`alwaysApply: true`). gald3r's
> `AGENTS.md`/`CLAUDE.md` install layer must be **remapped to `.continue/rules/`**. AGENTS.md
> support is only an open community proposal (GitHub #6716).

---

## 1. Folder Hierarchy

```
<project-root>/
├── config.yaml                    ← canonical assistant/config spec (models, rules, prompts, docs, mcpServers, data)
├── config.json                    ← legacy (still works for some features; config.yaml is current)
└── .continue/
    ├── rules/        *.md          ← always-on / glob-scoped instructions (alwaysApply frontmatter)
    ├── prompts/      *.md          ← invokable slash commands (invokable: true)
    ├── mcpServers/   *.yaml|json   ← per-server MCP config (alt to config.yaml mcpServers block)
    └── checks/       *.md          ← AI PR reviewers → surface as GitHub status checks (CI primitive)
```

**gald3r writes**: `.continue/rules/*.md` (instruction layer + memory), `.continue/prompts/*.md`
(commands), `config.yaml` / `.continue/mcpServers/` (MCP). Skills and sub-agents have **no
first-class `.continue/` drop-in target** (see §3 / §4).
**Continue owns**: the `config.yaml` schema, context providers (`@codebase`, `@docs`, `@file`…),
and the Cloud/Background Agent runtime.

---

## 2. AI Instruction File — `.continue/rules/`, NOT a root file

Continue's native instruction convention is the **`.continue/rules/` folder** of markdown rule files
(loaded lexicographically). A rule with `alwaysApply: true` is concatenated into the system message
for **Agent, Chat, and Edit**; `globs:` scopes a rule to matching files. **There is no root
`AGENTS.md`/`CLAUDE.md`/`CONTINUE.md` read.** Adopting the AGENTS.md standard is an open proposal
(#6716) that would map AGENTS.md to an implicit `alwaysApply: true` rule with `globs: ['**/*']`.

- gald3r install: write `AGENTS.md`/`CLAUDE.md` content into `.continue/rules/` (e.g.
  `00-gald3r-always.md` with `alwaysApply: true`).
- Source: https://github.com/continuedev/continue/issues/6716

---

## 3. Agents Support — ⚠️ PARTIAL

- **Modes** (built-in, not user-defined roles): **Chat** (no tools), **Plan** (read-only tools),
  **Agent** (all tools). System prompts overridable via `baseAgentSystemMessage` /
  `basePlanSystemMessage`.
- **Continue "Agents" bundle**: an assistant defined in `config.yaml` — "composed of models, rules,
  and tools (MCP servers)." This is a config bundle, **not** a per-role sub-agent file.
- **True user-defined sub-agents are experimental/internal-only**: per GitHub issue #9550,
  "Sub-agents currently need to be configured in config.yaml (internal only for now while testing)",
  and the `config.yaml` reference does **not** yet expose a top-level `agents:` block.
- **Cloud / Background Agents**: async agents on a remote devbox for long tasks.
- gald3r `g-agnt-*` definitions have **no documented native sub-agent target** — classified PARTIAL.
- Source: https://docs.continue.dev/ide-extensions/agent/how-to-customize

## 4. Skills Support — ⚠️ PARTIAL

- Continue maintains a **`SKILL.md` skills repo** (`continuedev/skills`; skills: `check`,
  `writing-checks`, `all-green`, `scan`) using the **open SKILL.md standard**.
- **Distribution is package-based** — installed via `npx skills add continuedev/skills --skill <name>`
  and oriented at the **agent/checks** workflow, **not** a documented native `.continue/skills`
  runtime loader inside the IDE. The official docs (rules/prompts/reference) describe **no first-class
  in-IDE skills primitive**.
- gald3r `g-skl-*/SKILL.md` packs have **no first-class `.continue/skills` runtime loader to drop
  into** — classified PARTIAL. (Best gald3r mapping today: ship behavior as `.continue/rules/` +
  `.continue/prompts/`.)
- Source: https://github.com/continuedev/skills

## 5. Commands / Prompts — ✅ NATIVE

- **Prompts (invokable markdown)** live in `.continue/prompts/*.md` (markdown + YAML frontmatter).
  "By setting `invokable` to true, you make the markdown file a prompt, which will be available when
  you type `/` in Chat, Plan, and Agent mode." Built-ins: `/edit`, `/comment`, `/test`. Custom
  HTTP-endpoint slash commands also supported (legacy `config.json`).
- gald3r `@g-*` / `/g-*` commands map directly to `.continue/prompts/*.md` with `invokable: true`.
- Source: https://docs.continue.dev/customize/deep-dives/prompts

## 6. Hooks System — ✅ NATIVE (CLI-only; docs lagging)

- **Continue CLI hooks** shipped ~early-2026 — `command` and `mcp_tool` handlers fire on lifecycle
  events. **17 event types**: PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest,
  UserPromptSubmit, SessionStart, SessionEnd, Stop, Notification, SubagentStart, SubagentStop,
  PreCompact, ConfigChange, WorktreeCreate, WorktreeRemove, TaskCompleted.
  "SessionStart runs when Continue starts a new session or resumes an existing session… Only
  `type: command` and `type: mcp_tool` hooks are supported."
- **CAVEATS (load-bearing):** (1) hooks are **CLI-only** — **not** a `config.yaml` top-level block;
  (2) the dedicated docs page is **not yet published** (`/cli/hooks` 404s; tracking issue
  continuedev/continue#11678 open). Functionally native in the CLI; documentation is lagging.
- gald3r `g-hk-*.ps1` wire via `type: command` hooks on SessionStart / PreToolUse / Stop **in the
  CLI surface only** (no IDE-extension hook surface).
- Source: https://github.com/continuedev/continue/issues/11678

## 7. Rules / Memory — ✅ NATIVE

- `.continue/rules/*.md` (markdown + YAML frontmatter: `name`, `globs`, `alwaysApply`). Create the
  folder at the workspace top level: "Create a folder called `.continue/rules` at the top level of
  your workspace." `alwaysApply: true` ⇒ always-on instructions concatenated into the system message
  for Agent, Chat, and Edit; `globs:` scopes a rule to matching files. Rules are Continue's
  persistent memory/instruction layer. Also declarable inline under `config.yaml` `rules:`.
- gald3r `g-rl-*` map to `alwaysApply: true` (for `alwaysApply: true` rules) or `globs:`-scoped
  files (for path-scoped rules).
- Source: https://docs.continue.dev/customize/deep-dives/rules

## 8. MCP Support — ✅ NATIVE

- **MCP servers** configured via a `mcpServers` block in `config.yaml` **or** per-server files in
  `.continue/mcpServers/*.yaml|json`. "Currently custom tools can be configured using the Model
  Context Protocol standard to unify prompts, context, and tool use." Transports: **stdio, sse,
  streamable-http**. MCP tools surface to **Agent mode**.
- Source: https://docs.continue.dev/customize/deep-dives/mcp

## 9. Checks / Context Providers — Continue-native bonuses

- **Checks**: AI PR reviewers defined as markdown in `.continue/checks/` (YAML frontmatter + prompt)
  that surface as **GitHub status checks** — a distinctive CI/workflow extensibility primitive beyond
  the six core mechanisms.
- **Context providers** (`@`-mentions: `@codebase`, `@docs`, `@file`, …) are a pluggable
  context-injection mechanism; `@docs` indexes external documentation sets. Retrieval, not a
  gald3r-writable store.

---

## Parity vs. Cursor Reference

Continue reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands (prompts), rules, hooks, and MCP**. Two genuine gaps keep it at **⚠️**, not ✅:

1. **Skills are not a native in-IDE primitive** — SKILL.md is distributed externally via
   `npx skills add` and tied to the checks/agent workflow; there is no `.continue/skills` runtime
   loader. (⚠️)
2. **User-defined sub-agents are experimental/internal-only** (#9550); no top-level `agents:` block
   in `config.yaml` yet. (⚠️)

Additional caveats: **hooks are CLI-only** and **undocumented** (#11678); and Continue reads **no
single-file instruction convention** (no `AGENTS.md`/`CLAUDE.md`) — gald3r's instruction layer must
be remapped to `.continue/rules/`. Continue-native bonuses with no Cursor analog: **Checks**
(GitHub status-check PR reviewers) and **context providers** (`@docs` indexing).

**Install note (important):** the cheapest high-parity Continue install ships gald3r's instruction
content as `.continue/rules/*.md` (`alwaysApply: true`), gald3r commands as `.continue/prompts/*.md`
(`invokable: true`), and MCP via `config.yaml` / `.continue/mcpServers/`. Hooks wire in the **CLI**
surface only; skills/sub-agents have **no native target** and degrade to rules + prompts.

## Hook System

- **Type**: native (Continue CLI hooks) — **CLI-only**, docs not yet published (#11678)
- **Config surface**: Continue CLI hooks config (NOT a `config.yaml` top-level block)
- **Events available**: PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest,
  UserPromptSubmit, SessionStart, SessionEnd, Stop, Notification, SubagentStart, SubagentStop,
  PreCompact, ConfigChange, WorktreeCreate, WorktreeRemove, TaskCompleted (17)
- **Handler types**: `type: command` and `type: mcp_tool` (only these two supported)
- **gald3r hook files**: `g-hk-*.ps1` via `type: command` on SessionStart/PreToolUse/Stop (CLI only)
- **OS note**: no documented Windows/OS restriction on the `command` handler; PowerShell hooks
  invoke as ordinary commands from the CLI.

## Atypical Handling

- **Three surfaces** — IDE extensions (VS Code + JetBrains), `cn` CLI/TUI (+ headless), and
  Cloud/Background async agents. The CLI carries hooks; prompts/rules/MCP span all surfaces.
- **No single-file instruction file** — `.continue/rules/` IS the instruction layer; AGENTS.md is a
  proposal only (#6716).
- **`config.yaml` is canonical** — documented top-level blocks: `name`, `version`, `schema`,
  `models`, `context`, `rules`, `prompts`, `docs`, `mcpServers`, `data`. Notably **absent**:
  `agents` (experimental/internal) and `hooks` (CLI-only). Legacy `config.json` still works for some
  features (older HTTP-endpoint slash commands).

## gald3r Integration Notes

- Ship gald3r instructions as `.continue/rules/*.md` (`alwaysApply: true`) — there is no AGENTS.md
  to write.
- Map gald3r commands to `.continue/prompts/*.md` (`invokable: true`); MCP via `config.yaml` or
  `.continue/mcpServers/`.
- Hooks: wire `g-hk-*.ps1` as `type: command` CLI hooks — **CLI surface only**, and the API is
  undocumented (#11678), so treat as a moving target.
- Skills + sub-agents have **no native target** — do not claim ✅; degrade to rules + prompts and
  re-verify on the next scan.
- Re-verify on the next `@g-platform-scan-docs continue` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

(Agents — not in the 5-cell row — are ⚠️ PARTIAL: experimental/internal sub-agents only.)

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.continue.dev)

| Capability | Support | How verified |
|---|---|---|
| Commands | ✅ native | /customize/deep-dives/prompts — `.continue/prompts/*.md`; `invokable: true` ⇒ `/` in Chat/Plan/Agent; built-ins /edit /comment /test |
| Rules | ✅ native | /customize/deep-dives/rules — `.continue/rules/*.md` (`name`/`globs`/`alwaysApply`); `alwaysApply:true` ⇒ system message for Agent/Chat/Edit |
| Hooks | ✅ native (CLI-only) | continuedev/continue#11678 — CLI hooks, 17 events, `command`/`mcp_tool` only; docs page unpublished (`/cli/hooks` 404) |
| MCP | ✅ native | /customize/deep-dives/mcp — `config.yaml` `mcpServers` or `.continue/mcpServers/`; stdio/sse/streamable-http; surfaces to Agent mode |
| Agents | ⚠️ partial | /ide-extensions/agent/how-to-customize + issue #9550 — modes (Chat/Plan/Agent) + config.yaml bundle; user sub-agents internal-only; no top-level `agents:` block |
| Skills | ⚠️ partial | github.com/continuedev/skills — SKILL.md repo installed via `npx skills add`; checks/agent-oriented; no native `.continue/skills` loader |
| Instruction file | NOT a root file | issue #6716 — `.continue/rules/` is the instruction layer; AGENTS.md/CLAUDE.md NOT read (proposal only) |
| Checks (bonus) | ✅ native | `.continue/checks/*.md` AI PR reviewers → GitHub status checks (CI primitive beyond the six) |
