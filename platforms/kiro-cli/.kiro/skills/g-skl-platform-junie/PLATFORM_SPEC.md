---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: junie
authoring_path: update
docs_url: https://junie.jetbrains.com/docs
docs_url_secondary:
  - https://junie.jetbrains.com/docs/custom-slash-commands.html
  - https://junie.jetbrains.com/docs/guidelines-and-memory.html
  - https://junie.jetbrains.com/docs/junie-cli-subagents.html
  - https://junie.jetbrains.com/docs/agent-skills.html
  - https://junie.jetbrains.com/docs/junie-cli-hooks.html
  - https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
  - https://junie.jetbrains.com/docs/junie-cli-extensions.html
  - https://junie.jetbrains.com/docs/junie-cli-configuration.html
crawl_max_age_days: 14
vault_doc_path: research/platforms/junie/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1476
---

# PLATFORM_SPEC.md — JetBrains Junie (IDE plugin + Junie CLI)

JetBrains Junie ships as **two delivery surfaces**: a **Junie IDE plugin** (IntelliJ IDEA, PyCharm,
WebStorm, GoLand, RubyMine, Rider, etc.) and a **standalone Junie CLI** (cross-platform —
Linux/macOS/Windows — BYO-LLM / model-agnostic). The **CLI is where the rich extensibility surface
lives**: it natively supports **custom slash commands, always-on guidelines/memory,
automatically-delegated custom subagents, open-standard Agent Skills (`SKILL.md`), and MCP servers**.
Lifecycle hooks also exist but only as an **Early Access** feature limited to the **SessionStart**
event — so hooks are **PARTIAL**, not full-native. The IDE plugin supports the **`AGENTS.md`**
guidelines convention, **Agent Skills**, and **MCP**, but the commands/subagents/hooks primitives are
CLI-centric.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://junie.jetbrains.com/docs (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never` / `2026-05-20`),
which incorrectly marked commands/rules/agents/skills as unsupported — the Junie CLI now makes all of
them **NATIVE**, and hooks moved from "none" to **PARTIAL** (SessionStart-only, EAP).

> **Surface split:** the full extensibility (commands/guidelines/subagents/skills/MCP/EAP-hooks) lives
> in the **Junie CLI**. The IDE plugin exposes a narrower surface (`AGENTS.md` guidelines + Agent
> Skills + MCP). Subagents, custom slash commands, and hooks are documented as **CLI features**. Where
> a feature is CLI-only it is noted inline.

> **Instruction-file convention:** Junie reads **`AGENTS.md`** (the cross-tool standard), NOT
> `CLAUDE.md` or `GEMINI.md`. Project `AGENTS.md` always takes precedence over global
> `~/.junie/AGENTS.md`. Legacy `.junie/guidelines.md` is deprecated but still read.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                       ← root guidelines (always-on; honored by CLI + IDE) — gald3r writes
└── .junie/
    ├── AGENTS.md                   ← preferred project guidelines location — gald3r writes
    ├── guidelines.md               ← LEGACY guidelines (deprecated, still read); .junie/guidelines/ also legacy
    ├── commands/    *.md           ← custom slash commands (md + YAML frontmatter)
    ├── agents/      *.md           ← custom subagents (md + YAML; .agents/ also discovered)
    ├── skills/      <name>/SKILL.md  ← Agent Skills (agentskills.io open standard)
    ├── mcp/
    │   └── mcp.json                ← project MCP server config (shared CLI + IDE format)
    └── config.json                 ← Junie CLI settings (model/provider, *-locations, hooks block)

(user / global scope, Junie-owned)
~/.junie/AGENTS.md                  ← global guidelines (project AGENTS.md wins on collision)
~/.junie/commands/  ~/.junie/agents/  ~/.junie/skills/  ~/.junie/mcp/mcp.json  ~/.junie/config.json
```

- **gald3r writes**: `AGENTS.md` / `.junie/AGENTS.md` (guidelines), `.junie/commands/*.md`,
  `.junie/agents/*.md` (or `.agents/`), `.junie/skills/<name>/SKILL.md`, `.junie/mcp/mcp.json`, and
  hooks via the `hooks` block in `~/.junie/config.json` (see §6 — **project** `config.json` hooks are
  ignored for safety).
- **Junie owns**: the guidelines search order, the IDE PSI/index mechanism, user-scope `~/.junie/`,
  and the `config.json` schema.

## 2. AI Instruction File

- **Convention: `AGENTS.md`** (cross-tool standard). Junie CLI reads guidelines from `AGENTS.md` and
  adds that context to **every task** it works on — this is the always-on / persistent-memory analogue.
- **Precedence**: project `.junie/AGENTS.md` (or root `AGENTS.md`) **always takes precedence** over
  global `~/.junie/AGENTS.md`. The legacy `.junie/guidelines.md` (and `.junie/guidelines/` folder) is
  **deprecated but still read** for backward compatibility. The IDE plugin uses the same `AGENTS.md`
  convention.
- Junie does **not** natively read `CLAUDE.md` or `GEMINI.md`. gald3r should write **`AGENTS.md`** as
  the canonical surface; gald3r's existing `AGENTS.md` is a first-class input.
- Source: https://junie.jetbrains.com/docs/guidelines-and-memory.html

## 3. Agents Support — ✅ NATIVE (CLI)

- **Custom subagents**: markdown + YAML frontmatter in `.junie/agents/` (or `.agents/`) and
  `~/.junie/agents/`. Frontmatter fields: `name`, `description` (required), `tools` (allowlist),
  `disallowedTools`, `model`, `skills`, `allowPromptArgument` (`$prompt`).
- **Automatic delegation**: when the Junie CLI runs across a task that matches a subagent's name and
  description, it delegates to that subagent, which works **independently in its own context** and
  returns the result. Delegation is **automatic only** — subagents **cannot** be invoked manually via
  slash commands.
- gald3r `g-agnt-*` role definitions map directly to Junie subagent files.
- Source: https://junie.jetbrains.com/docs/junie-cli-subagents.html

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** following the **open Agent Skills format** (`agentskills.io/specification`),
  portable across agents. The Junie CLI scans `.junie/skills/` at **user and project** levels and
  selects skills relevant to the current task via **progressive disclosure** (loaded only when
  relevant).
- A skill is a folder `.junie/skills/<skill-name>/` (or `~/.junie/skills/<skill-name>/`) containing a
  `SKILL.md` (markdown + YAML; required `name`, optional `description`) plus templates / scripts /
  reference materials.
- **Supported across all JetBrains IDEs** (IntelliJ, WebStorm, PyCharm, etc.) **and the CLI**.
- gald3r `g-skl-*/SKILL.md` load natively.
- Source: https://junie.jetbrains.com/docs/agent-skills.html

## 5. Commands / Workflows — ✅ NATIVE (CLI)

- **Custom slash commands**: markdown files with YAML frontmatter in `.junie/commands/` (project) or
  `~/.junie/commands/` (user); invoked `/<name>` with `$argumentName` named arguments. **Filename =
  command name** (e.g. `explain.md` → `/explain`).
- Built-in slash commands are accessed by typing `/` in the prompt; custom ones are created via
  `/commands` → **Create New Command**. Project commands can be committed to version control.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://junie.jetbrains.com/docs/custom-slash-commands.html

## 6. Hooks System — ⚠️ PARTIAL (SessionStart-only, Early Access, CLI)

- **Mechanism**: a `hooks` block in `config.json`:
  `{ SessionStart: [ { matcher, hooks: [ { type: "command", command: "..." } ] } ] }`. Lets you run a
  shell command automatically when the Junie CLI starts.
- **`matcher`** is an optional regex over the session source (`startup` = fresh session, `resume` =
  resumed; omit to run on every source).
- **Safety**: hooks from the **default PROJECT config are ignored** — personal hooks must live in
  **`~/.junie/config.json`** or be passed via `--config-location`.
- **Why PARTIAL** (two reasons):
  1. **Only the `SessionStart` event is supported** — there is **no** `PreToolUse` / `PostToolUse` /
     `UserPromptSubmit` / `Stop` / pre-commit / file-watch.
  2. It is **Early Access (EAP)**, not GA.
- Notably, Junie's **extension** packaging concept (see §9) does **NOT** include hooks.
- A YouTrack request **JUNIE-1961** ("Add Event Hooks / Lifecycle Callbacks for Agent Execution")
  tracks broader hook coverage.
- **gald3r consequence**: SessionStart context injection (e.g. a `g-hk-*.ps1` that loads `.gald3r/`
  context) **is feasible now** via the personal `~/.junie/config.json` hooks block. PreToolUse
  `.gald3r/` guards, pre-commit gates, and file-watch automations are **not yet supported** — degrade
  those to git `core.hooksPath` or manual invocation. The IDE plugin has no hook surface.
- Source: https://junie.jetbrains.com/docs/junie-cli-hooks.html

## 7. Rules / Memory — ✅ NATIVE

- **Guidelines/memory via `AGENTS.md`** (see §2): project `.junie/AGENTS.md` / root `AGENTS.md` >
  global `~/.junie/AGENTS.md`; legacy `.junie/guidelines.md` still read. The guidelines content is
  **injected into every task automatically** — Junie's always-apply / persistent-rules surface.
- This is single-file guidelines rather than a glob-scoped per-rule directory; gald3r `g-rl-*` content
  is consolidated into `AGENTS.md`.
- Source: https://junie.jetbrains.com/docs/guidelines-and-memory.html

## 8. MCP Support — ✅ NATIVE

- **MCP servers (Model Context Protocol)**: the Junie CLI uses the **same MCP JSON configuration as
  Junie in JetBrains IDEs**, supporting both **local** (Docker / npx / binary) and **remote**
  (HTTP/HTTPS) servers.
- **Config**: `mcp.json` at `.junie/mcp/mcp.json` (project) or `~/.junie/mcp/mcp.json` (user) — shared
  format between CLI and IDE plugin. An **MCP Installation Assistant** AI helper streamlines adding
  servers from a registry or from scratch.
- MCP support was added to Junie in 2025 (announced alongside a ~30% agent speedup).
- gald3r marks MCP **✅ for the mechanism**; the concrete server set is machine/team-specific (no
  `mcp.json` is committed in this template), so end-to-end server behavior is ❓ untested in CI.
- Source: https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html

## 9. Extensions / Distribution — first-class bundle

- Junie has a first-class **"extension"** concept: a single extension can package **any combination of
  Agent Skills, MCP servers, Subagents, Custom slash commands, and Guidelines** — making team
  distribution easy. **Notably the extension component list does NOT include hooks.**
- This is the **ideal single-artifact distribution mechanism** for a gald3r Junie pack (skills +
  subagents + commands + guidelines + MCP in one bundle).
- **Config files**: the CLI loads settings from JSON `config.json` (plus CLI flags and env vars) with
  keys including `model`/`provider`, `mcp-locations`, `skill-locations`, `command-locations`,
  `agent-locations`, `guidelines-location`, `byok`, proxies, and `hooks`.
- **CI/CD**: Junie also runs in CI/CD via a **Junie GitHub Action** (`junie-on-github`), enabling
  agentic tasks in pipelines.
- **BYO-LLM caveat**: the CLI is model-agnostic; **switching models mid-session can reset accumulated
  agent context/memory**.
- Sources: https://junie.jetbrains.com/docs/junie-cli-extensions.html ·
  https://junie.jetbrains.com/docs/junie-cli-configuration.html

---

## Parity vs. Cursor Reference

Junie reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules (`AGENTS.md`), agents (subagents), skills (Agent Skills), and MCP**. The single gap
is **hooks**, which are **PARTIAL** — SessionStart-only and Early Access, with no PreToolUse /
PostToolUse / pre-commit / file-watch events, and the extension bundle deliberately excludes hooks.

**Surface caveats**: subagents, custom slash commands, and hooks are **CLI-only**; the IDE plugin
exposes `AGENTS.md` guidelines + Agent Skills + MCP. Instruction convention is **`AGENTS.md`** (not
`CLAUDE.md`). The **"extension"** bundle (skills + subagents + commands + guidelines + MCP) is the
natural single-artifact distribution channel for a gald3r Junie install.

## Hook System

- **Type**: partial (Early Access; CLI `config.json` `hooks` block)
- **Config file**: `~/.junie/config.json` (personal) or via `--config-location` — **project**
  `config.json` hooks are **ignored** for safety
- **Events available**: **`SessionStart` only** (matcher regex over session source: `startup` /
  `resume`) — NO PreToolUse / PostToolUse / UserPromptSubmit / Stop / pre-commit / file-watch
- **Event payload format**: shell `command` execution (`{ type: "command", command: "..." }`)
- **Limitations**: SessionStart-only **and** Early Access (not GA); the **extension** packaging
  concept excludes hooks; broader coverage tracked in YouTrack **JUNIE-1961**. IDE plugin has no hook
  surface.
- **gald3r hook files**: a SessionStart `g-hk-*` (context injection) wires now via personal
  `~/.junie/config.json`; PreToolUse `.gald3r/` guards / pre-commit gates must degrade to git
  `core.hooksPath` or manual invocation.

## Atypical Handling

- **Instruction convention is `AGENTS.md`** — Junie does NOT read `CLAUDE.md` / `GEMINI.md`. Project
  `AGENTS.md` wins over global `~/.junie/AGENTS.md`; legacy `.junie/guidelines.md` still read.
- **Two surfaces**: full primitive set in the **Junie CLI**; the **IDE plugin** is narrower
  (guidelines + skills + MCP). Subagents / slash commands / hooks are CLI features.
- **Subagents are auto-delegated only** — no manual `/subagent` invocation.
- **Hooks are EAP + SessionStart-only**, and personal-config-only (project hooks ignored).

## gald3r Integration Notes

- **Cheapest high-parity install**: ship gald3r's `.junie/` tree (commands + agents + skills + MCP) +
  `AGENTS.md`, or bundle them as a single Junie **extension** for team distribution.
- Subagent delegation is automatic — author `g-agnt-*` files with strong `description:` fields so
  Junie picks them up.
- Wire a **SessionStart** `g-hk-*` via `~/.junie/config.json` for `.gald3r/` context injection;
  degrade pre-commit/pre-tool hooks to git `core.hooksPath` or manual runs (EAP, SessionStart-only).
- Re-verify on the next `@g-platform-scan-docs junie` (crawl_max_age_days: 14) — confirm whether hooks
  exit EAP / gain new events (track JUNIE-1961).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ⚠️** — `config.json` `hooks` block, but **SessionStart-only** and **Early Access**; no
  PreToolUse/PostToolUse/pre-commit/file-watch; project hooks ignored (personal `~/.junie/config.json`
  only); excluded from the extension bundle (JUNIE-1961 tracks more).
- **Rules ✅** — guidelines/memory via **`AGENTS.md`** (project > global; legacy `.junie/guidelines.md`
  still read), injected into every task.
- **Skills ✅** — native **Agent Skills** (agentskills.io `SKILL.md`) in `.junie/skills/` at user +
  project scope; progressive disclosure; works across JetBrains IDEs + CLI.
- **Commands ✅** — native custom slash commands `.junie/commands/*.md` (`/name`, `$arg` named args).
- **MCP ✅** — native `.junie/mcp/mcp.json` (shared CLI + IDE format), local + remote servers, MCP
  Installation Assistant; concrete server set per-machine (❓ in CI).
- **Docs Fresh ✅** — `last_doc_scan: 2026-06-02` against https://junie.jetbrains.com/docs.

---

## Verification Evidence (docs crawl 2026-06-02, https://junie.jetbrains.com/docs)

| Capability | How verified |
|---|---|
| Commands | /docs/custom-slash-commands.html — `.junie/commands/` + `~/.junie/commands/`; `/name` with `$argumentName`; filename = command name; `/commands` → Create New Command |
| Rules | /docs/guidelines-and-memory.html — `AGENTS.md` guidelines added to every task; project `.junie/AGENTS.md` > global `~/.junie/AGENTS.md`; legacy `.junie/guidelines.md` still read |
| Agents | /docs/junie-cli-subagents.html — `.junie/agents/` (and `.agents/`) md+YAML; auto-delegated by name/description; own context; no manual slash invocation |
| Skills | /docs/agent-skills.html — open Agent Skills format (agentskills.io); `.junie/skills/<name>/SKILL.md` user+project; progressive disclosure; all JetBrains IDEs + CLI |
| Hooks | /docs/junie-cli-hooks.html — `config.json` `hooks` SessionStart-only (matcher startup/resume); EAP; project hooks ignored (personal `~/.junie/config.json`); JUNIE-1961 tracks more events |
| MCP | /docs/junie-cli-mcp-configuration.html — `.junie/mcp/mcp.json` (shared CLI + IDE), local + remote servers, MCP Installation Assistant |
| Extensions | /docs/junie-cli-extensions.html — single bundle packages skills + MCP + subagents + slash commands + guidelines (NOT hooks) |
| Config | /docs/junie-cli-configuration.html — `config.json` keys: model/provider, mcp/skill/command/agent-locations, guidelines-location, byok, proxies, hooks |
| Surfaces | IDE plugin (AGENTS.md + skills + MCP) vs CLI (full set: commands/guidelines/subagents/skills/MCP/EAP-hooks); CLI is BYO-LLM / model-agnostic; CI/CD via junie-on-github GitHub Action |
