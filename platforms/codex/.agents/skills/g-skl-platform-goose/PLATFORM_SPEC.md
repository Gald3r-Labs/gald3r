---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: goose
authoring_path: update
docs_url: https://block.github.io/goose/docs
docs_url_secondary:
  - https://goose-docs.ai/docs
  - https://block.github.io/goose/docs/guides/recipes/
  - https://goose-docs.ai/docs/guides/context-engineering/using-skills/
  - https://goose-docs.ai/docs/guides/subagents/
  - https://goose-docs.ai/blog/2026/05/14/goose-hooks/
  - https://block.github.io/goose/docs/tutorials/memory-mcp/
  - https://block.github.io/goose/docs/getting-started/using-extensions/
crawl_max_age_days: 14
vault_doc_path: research/platforms/goose/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Goose (Block)

**Goose** (Block, Inc. / Block Open Source — fka Square) is an open-source, on-machine AI developer
agent that runs in the terminal (**goose CLI**, headless/CI-friendly) and a one-click **goose
Desktop** app. As of mid-2026 Goose natively supports **all six** gald3r-relevant extension
primitives — custom slash commands (via Recipes), rules/memory (`.goosehints` + Memory Extension),
subagents, Agent Skills (`SKILL.md` open standard), **lifecycle hooks**, and MCP. Critically for
gald3r, Goose discovers Agent Skills from **`~/.claude/skills/`** (in addition to
`~/.config/goose/skills/`), so gald3r's `SKILL.md` assets are **cross-tool reusable** between Goose
and Claude with no duplication. Goose's instruction-file convention is **`.goosehints`** (native
primary); it **also reads `AGENTS.md`** (not `CLAUDE.md`).

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://block.github.io/goose/docs and
the goose-docs.ai mirror (see Verification Evidence). This **supersedes** the prior spec
(`last_doc_scan: never`) which incorrectly marked hooks as ❌ and agents/skills/commands/rules as
⚠️ — they are now all NATIVE. The prior spec's `GOOSE.md` / `.goose/config.yaml` correction still
stands (the real conventions are `.goosehints` for instructions and `~/.config/goose/config.yaml`
for config).

> **Surface split:** the full extensibility (commands/recipes, rules, agents, skills, hooks, MCP)
> is available across both the **goose CLI** (headless automation, CI, scheduled tasks) and **goose
> Desktop** (one-click recipe launch). Goose is **global-config-first** — the primary config lives
> in `~/.config/goose/`, not the repo. **Hooks are a recent addition** (announced 2026-05-14,
> ~3 weeks before this assessment) — re-verify on the next crawl.

---

## 1. Folder Hierarchy

Goose is **global-config-first**: the primary config lives in the user's home directory; project
scope is layered via `.goosehints`, project skills, and project plugin hooks.

```
~/.config/goose/
├── config.yaml             ← GLOBAL config: provider, model, enabled extensions (MCP servers)
├── .goosehints             ← GLOBAL static always-on instructions/rules
└── skills/   <name>/SKILL.md  ← GLOBAL Agent Skills (auto-discovered at startup)

~/.claude/skills/  <name>/SKILL.md  ← ALSO discovered (cross-tool — shared with Claude)

~/.agents/plugins/<name>/hooks/hooks.json   ← USER lifecycle hooks (shell scripts)

<project-root>/
├── .goosehints             ← PROJECT static always-on instructions/rules (every line sent every request)
├── AGENTS.md               ← read/supported (Agent Context); Goose can generate one for the repo
└── .agents/plugins/<name>/hooks/hooks.json  ← PROJECT lifecycle hooks (auto-discovered at startup)
```

- **gald3r writes**: `.goosehints` (project rules), `g-skl-*/SKILL.md` into a discovered skills dir
  (`~/.config/goose/skills/` or the shared `~/.claude/skills/`), Recipe YAML for workflows,
  `hooks.json` under `.agents/plugins/<name>/hooks/` for lifecycle hooks. MCP extensions are
  declared under `extensions:` in `~/.config/goose/config.yaml` (global, machine-specific).
- **Goose owns**: the `~/.config/goose/` namespace, `config.yaml` schema, extension lifecycle, the
  Skills-discovery contract, Recipe/Subrecipe execution, and the plugin/hook auto-discovery rules.

> **Correction vs. prior SKILL.md**: there is **no** `GOOSE.md` or `.goose/config.yaml` convention.
> Instructions go in `.goosehints` (+ `AGENTS.md`); config is `~/.config/goose/config.yaml`.

---

## 2. AI Instruction File

Goose reads **`.goosehints`** as its native static instruction surface — "the project's static
context ... great for defining overarching rules, standards, and documentation that apply to all
interactions. **Every single line in your `.goosehints` file gets sent with every request.**" Both a
global file (`~/.config/goose/.goosehints`) and a per-project file are supported.

Goose **also reads `AGENTS.md`** — its Agent Context check looks for an `AGENTS.md` and can generate
one tailored to the repo (Goose's own repo ships an `AGENTS.md`). Goose does **not** read
`CLAUDE.md` as an instruction file (only Agent Skills are shared from the `~/.claude/skills/` path).

- gald3r **generates** `.goosehints` (task conventions, commit format, MCP pointer) and may also
  ship/maintain `AGENTS.md`. The legacy `GOOSE.md` text in the old SKILL.md is **not** a Goose
  convention.
- Source: https://block.github.io/goose/blog/2025/06/05/whats-in-my-goosehints-file/ ·
  https://github.com/block/goose/blob/main/AGENTS.md

---

## 3. Agents Support — ✅ NATIVE

- **Subagents**: independent goose instances spawned via **natural-language delegation** that
  "execute tasks while keeping your main conversation clean ... goose automatically decides when to
  spawn subagents and handles their lifecycle." Run **sequentially or in parallel (up to 10
  concurrent workers)** with restricted tool access; pair with **Subrecipes** for reusable,
  type-validated task definitions.
- **gald3r mapping**: gald3r `g-agnt-*` definitions are expressed as **Subrecipes** (reusable recipe
  files with typed parameters) or delegated via natural language. Note the distinction: **subagents**
  are one-off, natural-language, auto-spawned; **subrecipes** are pre-written, parameter-validated,
  parallelizable recipe files — that is the durable authoring surface for gald3r agent roles.
- Source: https://goose-docs.ai/docs/guides/subagents/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` folder open standard): "Goose **automatically discovers skills at
  startup** from `~/.config/goose/skills/` (**or `~/.claude/skills/`** ...). When you ask Goose to do
  something, it checks if any skills match ... loads the full `SKILL.md` file and follows those
  instructions." Block also runs a **Skills Marketplace** at block.github.io/goose/skills.
- **gald3r mapping**: gald3r `g-skl-*/SKILL.md` load natively. Because Goose reads the **same
  `~/.claude/skills/` location**, gald3r's Claude `SKILL.md` assets are shared with Goose **with no
  duplication** — the cheapest install path.
- **Recipes / Subrecipes** are a *second* portable workflow primitive (YAML) that overlaps with both
  skills and commands — see §5.
- Source: https://goose-docs.ai/docs/guides/context-engineering/using-skills/

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: "You can create **custom slash commands for running recipes** in goose
  Desktop or the CLI." Goose also ships built-in slash commands (`/plan`, `/mode chat`, `/prompts`,
  `/builtin`, `/clear`).
- **Recipes** are Goose's primary reusable-workflow primitive: portable YAML bundling instructions /
  system prompt + initial prompt + extensions + **typed parameters** + subrecipes; shareable with a
  team, runnable in CI, and exposed as custom slash commands. **Subrecipes** are pre-written reusable
  recipe files invoked from a parent recipe with type-safe parameter validation (can run in
  parallel).
- **gald3r mapping**: gald3r `@g-*` / `/g-*` workflows map to **Recipes** surfaced as custom slash
  commands. Unlike markdown command files on other platforms, the durable form on Goose is recipe
  YAML.
- Source: https://block.github.io/goose/docs/guides/recipes/ ·
  https://block.github.io/goose/docs/guides/recipes/sub-recipes/

## 6. Hooks System — ✅ NATIVE (recent — announced 2026-05-14)

- **Lifecycle hooks**: "goose supports lifecycle hooks that **run shell scripts** when things happen
  during a session." Configured in **`hooks.json`** at `~/.agents/plugins/<name>/hooks/hooks.json`
  (user) or `<project>/.agents/plugins/<name>/hooks/hooks.json` (project), **auto-discovered at
  startup**.
- **Events** (11): `SessionStart`, `SessionEnd`, `Stop`, `UserPromptSubmit`, `PreToolUse`,
  `PostToolUse`, `PostToolUseFailure`, `BeforeReadFile`, `AfterFileEdit`, `BeforeShellExecution`,
  `AfterShellExecution`.
- **gald3r mapping**: gald3r `g-hk-*` behaviors (SessionStart context injection, PreToolUse `.gald3r/`
  guards, pre-commit/shell guards) wire natively. Hooks run **shell scripts** — on Windows ensure the
  hook command invokes PowerShell explicitly (e.g. `pwsh -File g-hk-*.ps1`); a bare `.ps1` is not a
  POSIX shell script.
- **Recency caveat**: this feature was **announced 2026-05-14**, ~3 weeks before this assessment.
  Treat the event list and `hooks.json` schema as fresh-but-young; re-verify on the next crawl.
- Source: https://goose-docs.ai/blog/2026/05/14/goose-hooks/

## 7. Rules / Memory — ✅ NATIVE

- **Static rules**: `.goosehints` (global `~/.config/goose/.goosehints` + per-project) is the
  always-on instruction surface — "**every single line ... gets sent with every request**." This is a
  single always-apply blob: there is **no** `.mdc` extension and **no** `alwaysApply:` / `globs:`
  per-file scoping like Cursor's `.cursor/rules/`.
- **Dynamic memory**: the **Memory Extension** (MCP) stores and retrieves context on-demand via tags
  — a complementary, queryable memory beyond the always-on `.goosehints` blob.
- **gald3r mapping**: gald3r rules (`g-rl-*.md`) are concatenated/summarized into `.goosehints`
  (all-or-nothing context, no glob scoping). gald3r's own `.gald3r/learned-facts.md` remains the
  cross-session fact store; the Memory Extension can supplement it.
- Source: https://block.github.io/goose/docs/tutorials/memory-mcp/

## 8. MCP Support — ✅ NATIVE

- **Extensions ARE MCP servers**: "Goose 'Extensions' are just MCP servers ... Goose can connect to
  70+ extensions ... via the Model Context Protocol open standard." Goose was one of the earliest MCP
  adopters with one of the deepest integrations.
- **Config**: declared under `extensions:` in `~/.config/goose/config.yaml` (global,
  machine-specific) and managed interactively via `goose configure`; stdio + remote (SSE/HTTP)
  servers. A built-in **Developer** extension (plus Memory, etc.) ships enabled.
- **gald3r mapping**: the gald3r MCP server is added as a Goose extension in `config.yaml` (stdio or
  remote URL) — the strongest, longest-standing integration surface on Goose.
- Source: https://block.github.io/goose/docs/getting-started/using-extensions/

## 9. Plugins / Distribution — extensibility surface

- The **plugin system** (`~/.agents/plugins/`) is the host for **hooks** and a newer extensibility
  surface beyond MCP. **Recipes/Subrecipes** (portable YAML) are the share/CI distribution channel
  for workflows, and the **Skills Marketplace** (block.github.io/goose/skills) distributes Agent
  Skills. A gald3r Goose install ships: `.goosehints` + skills (ideally via the shared
  `~/.claude/skills/`) + recipe YAML + a `hooks.json` plugin + a `config.yaml` MCP extension entry.
- **Scheduler / Tasks**: Goose supports scheduled and headless task execution (cron-like), useful for
  unattended gald3r runs.
- Source: https://goose-docs.ai/blog/2026/05/14/goose-hooks/ ·
  https://block.github.io/goose/docs/guides/recipes/

---

## Parity vs. Cursor Reference

Goose now reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands (recipes), rules (`.goosehints` + Memory Extension), agents (subagents/subrecipes), skills
(`SKILL.md`), hooks, and MCP**. Caveats: it is **global-config-first** (`~/.config/goose/`, not the
repo); rules are a single always-on `.goosehints` blob with **no glob-scoped activation**; **hooks
are new** (2026-05-14) and run **shell scripts** (invoke PowerShell explicitly on Windows); and
Recipes (not markdown command files) are the durable command/workflow form. MCP is Goose's strongest,
oldest surface.

**Reuse note (important):** because Goose discovers Agent Skills from **`~/.claude/skills/`**,
gald3r's Claude `SKILL.md` assets are **reusable on Goose without a separate port** — the cheapest
high-parity path is to point Goose at the shared skills directory and add `.goosehints` + a recipe
bundle + an MCP extension entry.

## Hook System

- **Type**: native (plugin `hooks.json`) — **recent (announced 2026-05-14)**
- **Config file**: `~/.agents/plugins/<name>/hooks/hooks.json` (user) or
  `<project>/.agents/plugins/<name>/hooks/hooks.json` (project); auto-discovered at startup
- **Events available**: SessionStart, SessionEnd, Stop, UserPromptSubmit, PreToolUse, PostToolUse,
  PostToolUseFailure, BeforeReadFile, AfterFileEdit, BeforeShellExecution, AfterShellExecution
- **Event payload / mechanism**: hooks run **shell scripts** on the above events
- **gald3r hook files**: `g-hk-*` wire natively — on Windows invoke PowerShell explicitly
  (`pwsh -File ...`) since hooks are shell scripts, not bare `.ps1` handlers

## Atypical Handling

- **Global-config-first**: primary config + global skills + global hints live under
  `~/.config/goose/`, not the repo. Project scope layers via `.goosehints`, project skills, and
  `.agents/plugins/` hooks.
- **Skills shared with Claude**: `~/.claude/skills/` is a discovery path — reuse, do not duplicate.
- **Two reusable-workflow primitives**: Recipes (YAML, surfaced as slash commands) overlap with both
  COMMANDS and SKILLS for gald3r mapping; Subrecipes vs subagents are distinct (pre-written/typed vs
  one-off/natural-language).
- **Instruction file is `.goosehints`** (+ `AGENTS.md`), **not** `CLAUDE.md` and not the
  prior-claimed `GOOSE.md`.

## gald3r Integration Notes

- Point Goose at the shared `~/.claude/skills/` tree (or copy into `~/.config/goose/skills/`) so
  gald3r `g-skl-*` load natively.
- Ship `.goosehints` (rules), recipe YAML (commands/workflows), and an MCP `extensions:` entry in
  `~/.config/goose/config.yaml`.
- Hooks now fire natively — wire `g-hk-*` via a `hooks.json` plugin (invoke PowerShell explicitly on
  Windows). Re-verify the young hook surface on the next `@g-platform-scan-docs goose`
  (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://block.github.io/goose/docs + goose-docs.ai mirror)

| Capability | How verified |
|---|---|
| Commands | /guides/recipes — "custom slash commands for running recipes" (Desktop + CLI) + built-in `/plan`, `/mode chat`, `/prompts`, `/builtin`, `/clear` |
| Rules | /tutorials/memory-mcp + goosehints blog — `.goosehints` static always-on (global + project), "every line sent with every request"; Memory Extension for dynamic tagged memory |
| Agents | /guides/subagents — independent goose instances, auto-spawned, sequential/parallel up to 10 workers, restricted tools; pairs with Subrecipes |
| Skills | /guides/context-engineering/using-skills — auto-discovered at startup from `~/.config/goose/skills/` **or `~/.claude/skills/`**; `SKILL.md` open standard; Skills Marketplace |
| Hooks | /blog/2026/05/14/goose-hooks — lifecycle hooks run shell scripts; 11 events; `hooks.json` at `~/.agents/plugins/<name>/hooks/` (user) or project; auto-discovered. ANNOUNCED 2026-05-14 (recent) |
| MCP | /getting-started/using-extensions — extensions ARE MCP servers; 70+ extensions; `extensions:` in `~/.config/goose/config.yaml`; built-in Developer/Memory enabled |
| Instruction file | goosehints blog + github.com/block/goose/blob/main/AGENTS.md — native `.goosehints`; `AGENTS.md` also read/generated (NOT `CLAUDE.md`) |
| Recipes / Subrecipes | /guides/recipes + /guides/recipes/sub-recipes — portable YAML (instructions + prompt + extensions + typed params + subrecipes); CI-runnable; surfaced as slash commands |
| Surfaces / Scheduler | goose CLI (headless/CI) + goose Desktop (one-click); scheduled/headless cron-like task execution for unattended runs |
| Install / live connection | ❓ Not install-tested in this repo; assessment is doc/mechanism-level against official docs + mirror |
