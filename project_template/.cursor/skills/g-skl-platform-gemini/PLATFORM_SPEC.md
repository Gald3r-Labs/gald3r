---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: gemini
authoring_path: update
docs_url: https://github.com/google-gemini/gemini-cli
docs_url_secondary:
  - https://geminicli.com/docs/
  - https://geminicli.com/docs/cli/custom-commands/
  - https://geminicli.com/docs/cli/gemini-md/
  - https://geminicli.com/docs/core/subagents/
  - https://geminicli.com/docs/cli/skills/
  - https://geminicli.com/docs/hooks/
  - https://geminicli.com/docs/tools/mcp-server/
crawl_max_age_days: 7
vault_doc_path: research/platforms/gemini/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1467
---

# PLATFORM_SPEC.md — Gemini CLI (Google)

**Gemini CLI** (`gemini` command, Google / `google-gemini/gemini-cli`, Apache-2.0) is Google's
open-source terminal coding agent. As of mid-2026 it natively supports **all six** gald3r-relevant
extension primitives — custom slash commands, rules/memory, subagents, Agent Skills, lifecycle
hooks, and MCP. This is a **major upgrade** over the prior assessment, which (correctly, for its
era) marked hooks/skills/agents as missing: **subagents and an 11-event hook system were added in
2026** and are now first-class.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://github.com/google-gemini/gemini-cli
and https://geminicli.com/docs/ (see Verification Evidence). This **supersedes** the prior spec
(`last_doc_scan: never`) which marked hooks ❌, skills ❌, and agents ⚠️ — those are now all NATIVE.

> **Instruction-file convention (read carefully):** Gemini CLI's default instruction/memory file is
> **`GEMINI.md`** — it does **not** read `AGENTS.md` by default the way the AGENTS.md-ecosystem tools
> do. **However**, the context filename is **configurable** via `context.fileName` in `settings.json`
> (e.g. `["AGENTS.md", "CONTEXT.md", "GEMINI.md"]`), so AGENTS.md is **natively supportable** once
> configured. gald3r ships a thin `GEMINI.md` overlay that points at `AGENTS.md`.

> **Native config tree (`.gemini/`):** the files Gemini CLI reads are under **`.gemini/`** —
> `settings.json` (hosts hooks + `mcpServers`), `commands/*.toml`, `agents/*.md`, `skills/`. gald3r's
> primitives now map **directly** onto these native folders. Gemini CLI **also** discovers the
> `.agents/skills/` and `~/.agents/skills/` alias dirs alongside the native `.gemini/` paths, aiding
> AGENTS.md-ecosystem cross-tool portability.

> **Recency caveat (⚠️):** subagents (added ~April 2026, around Google Cloud Next) and hooks (added
> ~January 2026, enabled by default v0.26.0+ per secondary reporting) are **recent additions**.
> Verify the named events / frontmatter keys against the **installed** CLI version on next scan.

---

## 1. Folder Hierarchy

All primitives are Gemini-native (loaded from `.gemini/`). gald3r writes directly into this tree.

```
<project-root>/
├── GEMINI.md                       ← native instruction/memory file (hierarchical; see §2)
└── .gemini/
    ├── settings.json               ← hooks + mcpServers + context.fileName + model/tools
    ├── commands/    <name>.toml     ← custom slash commands (nestable → /dir:name)
    ├── agents/      *.md            ← subagents (markdown + YAML frontmatter)
    └── skills/      <name>/SKILL.md ← Agent Skills (SKILL.md standard)
~/.gemini/                          ← user-global mirror (settings.json, GEMINI.md, commands, agents, skills)
.agents/skills/  or  ~/.agents/skills/   ← alias skill dirs Gemini also discovers (cross-tool portability)
```

- **Gemini owns**: `.gemini/`, `settings.json` schema, `commands/*.toml` schema, extensions.
- **gald3r writes**: `GEMINI.md`, `.gemini/commands/*.toml`, `.gemini/agents/*.md`,
  `.gemini/skills/<name>/SKILL.md`, hooks + MCP in `.gemini/settings.json`.
- Skills are also discoverable from `.agents/skills/` (workspace) and `~/.agents/skills/` (user),
  so gald3r `g-skl-*/SKILL.md` can ship via the AGENTS.md-ecosystem alias path too.

## 2. AI Instruction File

**`GEMINI.md`** is Gemini CLI's native instruction/memory file. It is loaded **hierarchically**
(global `~/.gemini/GEMINI.md` → project-root `GEMINI.md` → `GEMINI.md` up/down the directory tree),
supports **`@file.md` imports**, and is inspectable/reloadable via `/memory show` and
`/memory refresh` (`/memory add` appends). The filename is **configurable** via `context.fileName`
in `settings.json` — set it to a list like `["AGENTS.md", "CONTEXT.md", "GEMINI.md"]` to make
`AGENTS.md` a first-class context file.

- gald3r generates / merges `GEMINI.md` as a thin overlay that `@`-imports / points at `AGENTS.md`
  (universal gald3r instructions). `GEMINI.md` is personalized per user and gitignored (`g-rl-02`).
- **Caveat (⚠️)**: `/memory add` appends to `GEMINI.md`; guard against Gemini-injected memory
  overwriting gald3r-authored sections.
- Source: https://geminicli.com/docs/cli/gemini-md/

## 3. Agents Support — ✅ NATIVE

- **Subagents**: markdown (`.md`) + YAML frontmatter in `.gemini/agents/*.md` (project) or
  `~/.gemini/agents/*.md` (user); the markdown body becomes the system prompt. Frontmatter:
  `name`, `description`, `tools`, `model`, `temperature`, `max_turns`, `kind` (local/remote).
  Built-in experts include `generalist`, `cli_help`, `codebase_investigator`. Invoked explicitly
  with **`@name`**; supports **parallel dispatch**. MCP servers can be scoped per-subagent.
- Added **~April 2026** (announced at/around Google Cloud Next).
- gald3r `g-agnt-*` definitions map directly to `.gemini/agents/*.md`.
- Source: https://geminicli.com/docs/core/subagents/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` standard): a self-contained directory packaging instructions + assets
  into a discoverable capability, defined by `SKILL.md` with YAML frontmatter (`name`, `description`).
  Names/descriptions are injected at session start; the model calls **`activate_skill`** on a match.
  Discovered from **built-in, extension, user (`~/.gemini/skills/` or `~/.agents/skills/`), and
  workspace (`.gemini/skills/` or `.agents/skills/`)** tiers. Managed via
  `/skills list|link|enable|disable|reload`.
- gald3r `g-skl-*/SKILL.md` load natively — from `.gemini/skills/` or the `.agents/skills/` alias.
- Source: https://geminicli.com/docs/cli/skills/

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: defined as **TOML** files in `.gemini/commands/` (project) or
  `~/.gemini/commands/` (user). A file at `<project>/.gemini/commands/test.toml` becomes `/test`;
  subdirectories create namespaced commands (`git/commit.toml` → `/git:commit`). The required key is
  just **`prompt`**; supports **`{{args}}`** and **shell execution**.
- **gald3r note**: Gemini commands are **TOML**, not `.md`. gald3r's `@g-*` / `/g-*` commands map to
  `.gemini/commands/g-*.toml` (the parity sync emits the TOML wrapper); the `.md` command docs are
  reference, the `.toml` files are the executable surface.
- Source: https://geminicli.com/docs/cli/custom-commands/

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** configured in **`.gemini/settings.json`** (project/user/system layers + via
  extensions). Hooks run **synchronously** as part of the agent loop — when an event fires, Gemini
  CLI **waits for all matching hooks to complete** before continuing.
- **Events (11)**: `SessionStart`, `SessionEnd`, `BeforeAgent`, `AfterAgent`, `BeforeModel`,
  `AfterModel`, `BeforeToolSelection`, `BeforeTool`, `AfterTool`, `PreCompress`, `Notification`.
- Added **~January 2026** (enabled by default v0.26.0+ per secondary reporting).
- gald3r `g-hk-*` automation (SessionStart context injection, WPAC inbox check, pre-tool `.gald3r/`
  guards, pre-commit/pre-push gates) now wires to these events — **no manual workaround required**
  the way the prior spec assumed.
- Source: https://geminicli.com/docs/hooks/

## 7. Rules / Memory — ✅ NATIVE

- Gemini's persistent-context mechanism is the hierarchical **`GEMINI.md`** memory file (§2) with
  `@file.md` imports and `/memory add|show|refresh`. There is no separate `.mdc`/`alwaysApply`/`globs`
  rules-folder primitive — "always apply" is achieved by GEMINI.md being concatenated into every
  prompt (and by `@`-importing rule files).
- gald3r `g-rl-*.md` map to GEMINI.md (inlined or `@`-imported); `alwaysApply: true` rules belong in
  the always-loaded GEMINI.md body, `description:`-scoped rules can be imported on demand.
- **Token/size note (⚠️)**: GEMINI.md is concatenated into every prompt — keep referenced rule
  content lean to avoid context bloat.
- Source: https://geminicli.com/docs/cli/gemini-md/

## 8. MCP Support — ✅ NATIVE

- MCP servers configured via the top-level **`mcpServers`** object in **`.gemini/settings.json`**
  (each server with `command`/`env`/transport), plus a global `mcp` object (`mcp.allowed`,
  `mcp.serverCommand`). Multiple transports supported; `includeTools`/`excludeTools` merge with
  **most-restrictive-wins**. MCP-backed tools surface via **`@` prefixes** (e.g. `@github`,
  `@slack`). MCP servers can also be scoped **per-subagent** (inline in agent frontmatter). Inspect
  with the built-in **`/mcp`** command.
- gald3r note: `.mcp.json` (root) is gitignored/machine-specific (`g-rl-02`); the authoritative
  native location is `.gemini/settings.json`.
- Source: https://geminicli.com/docs/tools/mcp-server/

## 9. Extensions — distribution channel

- **Gemini CLI Extensions** package **commands, MCP servers, context files, and skills** into
  installable/distributable bundles ("Extension skills" is a documented skill-discovery tier).
  Installed via `gemini extensions`. This is the natural distribution channel for a gald3r Gemini
  bundle (commands + agents + skills + hooks + MCP together).
- Docs: https://geminicli.com/docs (Tutorial Series Part 11 — Extensions).

---

## Parity vs. Cursor Reference

Gemini CLI now reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`):
native **commands, rules/memory, agents, skills, hooks, and MCP**. It is among the most
fully-featured gald3r targets. Platform-specific deltas:

- **Commands are TOML** (`.gemini/commands/*.toml`), not Cursor `.md` — parity sync emits TOML.
- **Rules = GEMINI.md memory**, not a `.mdc` folder with `alwaysApply:`/`globs:` — gald3r maps rules
  into the hierarchical context file (+ `@file.md` imports).
- **Default instruction file is `GEMINI.md`, not `AGENTS.md`** — AGENTS.md works only after setting
  `context.fileName` in settings.json.
- **Recency**: subagents (~Apr 2026) and hooks (~Jan 2026) are new — verify on the installed CLI.

**Bonus capabilities** beyond the Cursor reference: headless/non-interactive mode (CI), checkpointing
(save/resume conversation state), Google Search grounding, and the Extensions distribution system.

## Hook System

- **Type**: native (settings.json lifecycle hooks)
- **Config file**: `.gemini/settings.json` (project / user / system + extensions)
- **Events available**: `SessionStart`, `SessionEnd`, `BeforeAgent`, `AfterAgent`, `BeforeModel`,
  `AfterModel`, `BeforeToolSelection`, `BeforeTool`, `AfterTool`, `PreCompress`, `Notification` (11)
- **Execution model**: **synchronous** — the agent loop waits for all matching hooks to complete
- **gald3r hook files**: `g-hk-*` wire to these events (SessionStart injection, BeforeTool `.gald3r/`
  guards, pre-commit/pre-push gates). Added ~Jan 2026 (default v0.26.0+) — verify on installed CLI.

## Atypical Handling

- Native config is `.gemini/settings.json` (hosts both hooks and `mcpServers`) + TOML custom
  commands; `GEMINI.md` is the hierarchical memory/instruction file.
- Default instruction file is `GEMINI.md`; AGENTS.md support requires `context.fileName` config.
- MCP-backed tools and subagents are both invoked with the `@` prefix.
- Skills discoverable from both `.gemini/skills/` and the `.agents/skills/` alias dir.

## gald3r Integration Notes

- Ship gald3r primitives natively: `.gemini/commands/g-*.toml`, `.gemini/agents/g-agnt-*.md`,
  `.gemini/skills/<name>/SKILL.md`, hooks + MCP in `.gemini/settings.json`, `GEMINI.md` overlay.
- Hooks now fire natively — do NOT degrade session-start / WPAC / pre-commit to manual steps.
- Set `context.fileName` to include `AGENTS.md` if reusing the gald3r universal instruction file.
- Re-verify on the next `@g-platform-scan-docs gemini` (crawl_max_age_days: 7) — confirm subagent /
  hook event names against the installed CLI version.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ✅** — native 11-event lifecycle hooks in `.gemini/settings.json` (synchronous).
- **Rules ✅** — hierarchical `GEMINI.md` memory (`@file.md` imports; `/memory` management).
- **Skills ✅** — native Agent Skills (`SKILL.md`; `activate_skill`; `.gemini/`/`.agents/` dirs).
- **Commands ✅** — native TOML slash commands in `.gemini/commands/` (`/name`, `/dir:name`).
- **MCP ✅** — first-class `mcpServers` in `.gemini/settings.json` (`/mcp`; per-subagent scoping).
- **Docs Fresh ✅** — crawled 2026-06-02 against the GitHub repo + geminicli.com/docs.

---

## Verification Evidence (docs crawl 2026-06-02, https://github.com/google-gemini/gemini-cli + https://geminicli.com/docs/)

| Capability | How verified | source_url |
|---|---|---|
| Commands | Custom slash commands = TOML in `.gemini/commands/`; `test.toml` → `/test`, `git/commit.toml` → `/git:commit`; required key `prompt`; `{{args}}` + shell exec | https://geminicli.com/docs/cli/custom-commands/ |
| Rules / memory | Hierarchical `GEMINI.md` context files; `@file.md` imports; `context.fileName` configurable (AGENTS.md-capable); `/memory add\|show\|refresh` | https://geminicli.com/docs/cli/gemini-md/ |
| Agents | Subagents = markdown + YAML in `.gemini/agents/*.md` (`~/.gemini/agents/*.md`); frontmatter name/description/tools/model/temperature/max_turns/kind; `@name`; parallel; added ~Apr 2026 | https://geminicli.com/docs/core/subagents/ |
| Skills | Agent Skills (`SKILL.md` + YAML name/description); injected at session start; `activate_skill`; tiers built-in/extension/user/workspace; `.gemini/skills/` + `.agents/skills/`; `/skills` | https://geminicli.com/docs/cli/skills/ |
| Hooks | 11 lifecycle events (SessionStart…Notification) in `.gemini/settings.json`; synchronous (loop waits); added ~Jan 2026, default v0.26.0+ | https://geminicli.com/docs/hooks/ |
| MCP | `mcpServers` object in `.gemini/settings.json` + global `mcp` (allowed/serverCommand); multi-transport; includeTools/excludeTools most-restrictive-wins; `@`-prefixed tools; per-subagent scoping; `/mcp` | https://geminicli.com/docs/tools/mcp-server/ |
| Instruction file | `GEMINI.md` default (NOT AGENTS.md by default); `context.fileName` can add `AGENTS.md`/`CONTEXT.md`; hierarchical + `@file.md` imports | https://geminicli.com/docs/cli/gemini-md/ |
| Extensions | Bundle commands + MCP + context files + skills ("Extension skills" tier) via `gemini extensions` | https://geminicli.com/docs |
