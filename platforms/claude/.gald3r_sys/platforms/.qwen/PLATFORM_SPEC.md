---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: qwen
authoring_path: update
docs_url: https://qwenlm.github.io/qwen-code-docs/
docs_url_secondary:
  - https://github.com/QwenLM/qwen-code
  - https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/
crawl_max_age_days: 14
vault_doc_path: research/platforms/qwen/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1480
---

# PLATFORM_SPEC — qwen (Qwen Code CLI)

Authoring path: **UPDATE** existing `g-skl-platform-qwen/SKILL.md`.

**Qwen Code** (`qwen` command, Alibaba / `QwenLM/qwen-code`) is Alibaba's open-source terminal
coding agent. It is an **adapted fork of Google's Gemini CLI**, so its config surface is nearly
identical to Gemini CLI (see `g-skl-platform-gemini/PLATFORM_SPEC.md`, T1467) — only the folder
name (`.qwen/`), the instruction filename (`QWEN.md`), and the default models differ. Like Gemini
CLI, it is an **instruction-file + JSON-settings** platform, not a rules/skills/hooks platform like
Cursor:

- Its native context mechanism is the hierarchical **`QWEN.md`** memory/context file
  (configurable via `context.fileName` in settings), not a folder of always-apply rule files.
- Its native config is **`.qwen/settings.json`** (project) and `~/.qwen/settings.json`
  (user), which also hosts the **`mcpServers`** block.
- It has **native custom commands** under **`.qwen/commands/`** (Gemini-CLI lineage). Historically
  these are **TOML** files invoked as `/namespace:command`; newer versions accept **Markdown +
  optional YAML frontmatter**, with TOML deprecated-but-still-supported for backward compatibility.
- It has **no native always-apply rules folder**, **no skills concept**, **no sub-agent file
  system**, and **no lifecycle hook/event system** comparable to Cursor's `hooks.json`.

> **Two folder names in play — read carefully (honesty note):**
> - **`.qwen/`** is what *Qwen Code itself reads* for `settings.json` and `commands/`.
> - **`.agent/`** is the folder **gald3r installs into** for this platform (rules/skills/agents/
>   commands as `.md`). Qwen Code does **not** auto-discover `.agent/` content — gald3r's
>   `g-rl-*`, `g-skl-*`, and `g-agnt-*` markdown is surfaced to Qwen only by being **referenced
>   from `QWEN.md`**, not by native folder loading. This is the central parity gap (§9).

This repo (`gald3r_templates`) has **no installed `.qwen/` runtime tree** at spec time — only the
gald3r deploy scaffold under `gald3r_template/.gald3r_sys/platforms/.qwen/`, which currently
carries a **stale `config.yaml` + `instructions.md`** pair that does not match Qwen Code's actual
config surface (`settings.json` + `QWEN.md`). All claims below are **doc-derived (❓ / ⚠️)** and not
install-verified. `last_doc_scan: never` — no SCAN_DOCS crawl has been run.

---

## 1. Folder Hierarchy

Two distinct trees. The first is Qwen-native; the second is the gald3r install target.

**Qwen Code native config (what `qwen` reads):**
```
.qwen/                           ← Qwen Code project config (Qwen owns this)
├── settings.json                ← model providers, env, security.auth, context, mcpServers
├── commands/                    ← custom slash commands, nestable for namespacing
│   └── <name>.toml | <name>.md  ← invoked as /<name> (or /<dir>:<name>)
└── (env / API key via environment, not committed)
QWEN.md                          ← root context/memory file (hierarchical; see §2)
~/.qwen/settings.json            ← user-global settings (modelProviders, auth, mcpServers)
~/.qwen/commands/                ← user-global custom commands
```

**gald3r install target (what the parity sync writes):**
```
.agent/                          ← gald3r canonical install folder for Qwen
├── rules/g-rl-*.md              ← gald3r rules (NOT natively loaded by Qwen — see §7/§9)
├── skills/<name>/SKILL.md       ← gald3r skills (NOT natively loaded — see §4/§9)
├── agents/g-agnt-*.md           ← gald3r agent defs (NOT natively loaded — see §3/§9)
└── commands/g-*.md              ← gald3r command docs in .md (NOT Qwen's commands/ format — §5/§9)
QWEN.md                          ← gald3r-generated; the ONLY file Qwen natively reads as context
.mcp.json (root) and/or .qwen/settings.json → mcpServers
```

- **Qwen owns**: `.qwen/`, `settings.json` schema, `commands/` schema, the context-loading rules.
- **gald3r writes**: `.agent/` (rules/skills/agents/commands as `.md`), `QWEN.md`, MCP config.
- **Honesty**: the `.agent/` tree is gald3r's portable layout; Qwen Code does not scan it. Only
  `QWEN.md` (and `.qwen/`) are read natively. The legacy deploy scaffold at
  `platforms/.qwen/config.yaml` + `instructions.md` is **incorrect** and should be replaced with a
  `settings.json` + `QWEN.md` pair to match the real platform (flagged in §9).

## 2. AI Instruction File

**`QWEN.md`** is Qwen Code's native instruction/memory ("context") file. Its filename is
configurable via **`context.fileName`** in `settings.json` (default `QWEN.md`). Like Gemini CLI,
it is loaded **hierarchically** (global `~/.qwen/`, project root, and ancestor/sub directories,
concatenated into the prompt) and supports **modular imports** with the `@path/to/file.md` syntax —
which is the natural hook for pulling gald3r markdown into context. The active context is
inspectable/reloadable with the built-in `/memory` command family (`/memory show`, `/memory refresh`).

- gald3r **generates / merges** `QWEN.md` via the setup + parity pipeline. In the gald3r ecosystem
  the universal instructions live in **`AGENTS.md`**, and `QWEN.md` is a thin Qwen-specific overlay
  that points at `AGENTS.md` (mirroring the `GEMINI.md` overlay pattern).
- `QWEN.md` is personalized per user and gitignored (`g-rl-02` protected files).
- **Caveat (⚠️)**: `/memory add` "save to memory" appends to the context file; guard against
  Qwen-injected memory overwriting gald3r-authored sections.

## 3. Agents Support

- **Native concept**: ❌ Qwen Code has **no sub-agent / agent-file system** equivalent to Cursor's
  `.cursor/agents/`. There is no native discovery of `g-agnt-*.md`.
- **gald3r approach**: `g-agnt-*.md` files are installed under `.agent/agents/` for portability,
  but are surfaced to Qwen only by being **referenced from `QWEN.md`/`AGENTS.md`** and invoked
  conversationally (e.g. "act as @g-agnt-task-manager"). There is no platform-level "select agent"
  affordance.
- **Status**: ⚠️ partial (works via instruction-file reference; not a native primitive). ❓ untested.

## 4. Skills Support

- **Native concept**: ❌ Qwen Code has **no skills system**. `SKILL.md` folders are not
  auto-discovered or model-selected the way Cursor loads `g-skl-*`.
- **gald3r approach**: skills are installed under `.agent/skills/<name>/SKILL.md` for portability
  and are reachable only when their content is pulled in via `QWEN.md` references
  (`@path/to/SKILL.md` import) or pasted into context. Qwen's nearest native analogues are **custom
  commands** and **MCP-provided prompts**, which are a different shape than gald3r skills.
- **Status**: ❌ no native skills loading / ⚠️ usable only via instruction-file reference. ❓ untested.

## 5. Commands / Workflows

- **Native commands**: ✅ Qwen Code supports **custom slash commands** defined as files in
  **`.qwen/commands/`** (project) or `~/.qwen/commands/` (user). The command name derives from the
  file path relative to the commands dir; subdirectories namespace via `:` (e.g.
  `refactor/pure.toml` → `/refactor:pure`). **Format**: historically **TOML** (Gemini-CLI lineage —
  a `prompt` field plus optional `description`); newer Qwen Code accepts **Markdown with optional
  YAML frontmatter**, and **TOML is deprecated but still supported** for backward compatibility.
  Built-in commands (`/memory`, `/tools`, `/mcp`, `/chat`, `/help`, etc.) are also slash-invoked.
  File-based commands take precedence over built-ins on name conflict.
- **gald3r gap**: gald3r ships its commands as `.md` under `.agent/commands/g-*.md`, which is
  **NOT** placed in the native `.qwen/commands/` directory in the executable command format. So
  gald3r commands are documentation, not executable Qwen slash commands, unless a `commands/`
  emitter is generated (not currently produced).
- **Workflows**: there is no separate "workflow YAML" primitive in Qwen Code itself.
- **Status**: ⚠️ native custom commands exist but gald3r's `g-*` commands are not emitted into
  `.qwen/commands/` → not executable as slash commands. ❓ untested.

## 6. Hooks System

- **Native concept**: ❌ Qwen Code has **no lifecycle hook / event system** — there is no
  `hooks.json`, no `sessionStart` / `stop` / `preToolUse` / `beforeShellExecution` wiring (it
  inherits Gemini CLI's lack of a hook surface).
- **gald3r approach**: session automation that other platforms get from `g-hk-*` hooks must be done
  manually (run scripts by hand) or be triggered via instruction-file conventions in `QWEN.md`. The
  PCAC inbox check, session-start context injection, and pre-commit/pre-push gates have **no
  automatic firing surface** on Qwen.
- **Status**: ❌ not supported. (Closest related capability is **MCP servers** for adding tools,
  which is not an event/lifecycle hook.) ❓ workaround untested.

## 7. Rules / Memory

- **Native concept**: ❌ no always-apply **rules folder**. Qwen's persistent-context mechanism is
  the hierarchical **`QWEN.md`** context file (§2), not a directory of `.mdc`/`.md` rule files with
  `alwaysApply`/`globs` frontmatter.
- **gald3r approach**: `g-rl-*.md` rules are installed under `.agent/rules/` as plain **`.md`** (the
  parity sync maps Cursor's `.mdc` → `.md`). They are **only effective if referenced from `QWEN.md`**
  (e.g. via `@.agent/rules/g-rl-00-always.md` imports) — Qwen will not auto-load `.agent/rules/`.
  There is no native `globs:` scoping or `alwaysApply:` enforcement; "always apply" is achieved by
  inlining/importing into `QWEN.md`.
- **Token/size note (⚠️)**: `QWEN.md` (and its imports) is concatenated into every prompt, so keep
  referenced rule content lean to avoid context bloat (`token_budget: low` in the skill frontmatter).
- **Status**: ⚠️ partial — memory via `QWEN.md` works; folder-based always-apply rules do not.

## 8. MCP Support

- **Supported**: ✅ Yes. Qwen Code has first-class MCP support (inherited from Gemini CLI).
- **Config format/location**: an **`mcpServers`** block inside **`.qwen/settings.json`** (project)
  or `~/.qwen/settings.json` (user). Each entry supports `command`/`args`/`env` (stdio) or
  url-based (SSE/HTTP) transports, plus timeout/trust and tool include/exclude filters. MCP servers
  may additionally **expose prompts as slash commands** (loaded dynamically by the MCP prompt
  loader). Inspect/manage with the built-in **`/mcp`** command.
- **gald3r note**: a root **`.mcp.json`** (`mcpServers` → gald3r server URL) is the portable
  surface; the authoritative native location is `.qwen/settings.json`. (`.mcp.json` is gitignored,
  machine-specific — `g-rl-02`.)
- **Status**: ✅ mechanism verified by docs; ❓ concrete server set untested in this repo (no
  `.qwen/settings.json` present).

## 9. Known Gaps vs. Cursor Reference

Honest list of Cursor-reference features that do **not** work, are non-native, or are untested on
Qwen Code. This feeds `PLATFORM_STATUS.md` and the capability matrix. Because Qwen Code is a Gemini
CLI fork, this list closely mirrors the Gemini spec (T1467).

1. **No native hook/event system (❌)** — Cursor's `.cursor/hooks.json` (sessionStart, stop,
   preToolUse, beforeShellExecution) has no Qwen equivalent. All hook-driven automation (PCAC inbox
   check, session-start injection, pre-commit/push gates) is manual. **Decision tree: documented
   gap** (no platform config can supply this today).
2. **No native rules folder (❌→⚠️)** — `.agent/rules/g-rl-*.md` is not auto-loaded. Always-apply
   behavior must be inlined/imported from `QWEN.md` (`@path` import). No `alwaysApply:`/`globs:`
   semantics. **Platform-specific**: rule effectiveness depends on `QWEN.md` references.
3. **No native skills loading (❌→⚠️)** — `.agent/skills/<name>/SKILL.md` is not model-discovered.
   Skills reachable only via `QWEN.md` reference/import. Qwen's native analogues are **custom
   commands** and **MCP prompts**, which differ in shape. **Documented gap.**
4. **No native agent files (❌→⚠️)** — no `.cursor/agents/`-style discovery. `g-agnt-*.md` works
   only as conversational instruction-file references. **Documented gap.**
5. **Command format/placement mismatch (⚠️)** — Qwen's native custom commands live in
   `.qwen/commands/` (TOML, or Markdown+YAML in newer versions), invoked as `/name` or `/dir:name`.
   gald3r emits `.md` under `.agent/commands/g-*.md`, which are **not** placed in `.qwen/commands/`
   and so are **not executable** as Qwen slash commands. An emitter for `g-*` commands into
   `.qwen/commands/` does not exist yet. **Platform-specific config gap.**
6. **`.qwen/` vs `.agent/` split (⚠️)** — the only files Qwen natively reads are `QWEN.md` and
   `.qwen/`. The entire `.agent/` install tree is portability scaffolding, not native input.
7. **Stale deploy scaffold (⚠️)** — `gald3r_template/.gald3r_sys/platforms/.qwen/` ships a
   `config.yaml` (`model: qwen-max`, `instructions: .qwen/instructions.md`) + `instructions.md`,
   which **does not match** Qwen Code's real config (`settings.json` + `QWEN.md`). This scaffold
   should be regenerated to `settings.json` + `QWEN.md`. **Cleanup follow-up.**
8. **SCAN_DOCS not yet run (❓)** — `last_doc_scan: never`. Doc-derived claims (exact `settings.json`
   `modelProviders`/`mcpServers` keys, current built-in slash-command list, the TOML→Markdown
   command-format migration state) should be confirmed by `@g-platform-scan-docs qwen` against
   https://qwenlm.github.io/qwen-code-docs/ and the QwenLM/qwen-code repo.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no native hook/event system (Gemini-CLI lineage).
- **Rules ⚠️** — only via `QWEN.md` memory/import; no folder-based always-apply.
- **Skills ❌** — no native skills discovery (instruction-file reference only).
- **Commands ⚠️** — native custom commands exist in `.qwen/commands/`, but gald3r `g-*` are `.md`
  under `.agent/commands/` and not emitted into the executable command directory.
- **MCP ✅** — first-class `mcpServers` in `.qwen/settings.json` (mechanism doc-verified).
- **Docs Fresh ❓** — `last_doc_scan: never`; flip to ✅ after first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Folder hierarchy | Doc-derived (Qwen Code configuration docs: `.qwen/settings.json` project + `~/.qwen/settings.json` user). No runtime `.qwen/` present in this repo — ❓ install-untested |
| AI instruction file | `QWEN.md` context file (default; `context.fileName`-configurable) with `@path` imports + hierarchical load documented in Qwen Code docs (Gemini-CLI lineage) |
| Agents | No native agent system in Qwen Code docs — ❌ native; ⚠️ via instruction reference |
| Skills | No native skills system in Qwen Code docs — ❌ native |
| Commands | Native custom commands = files in `.qwen/commands/` (TOML, or Markdown+YAML in newer versions; TOML deprecated-but-supported), namespaced via `:` (Qwen Code commands docs); gald3r emits `.md` under `.agent/commands/` → ⚠️ mismatch |
| Hooks | No hook/event system in Qwen Code docs (Gemini-CLI fork has none) — ❌ |
| Rules / memory | `QWEN.md` + `/memory` documented; no rules-folder primitive — ⚠️ |
| MCP | `mcpServers` in `.qwen/settings.json` + `/mcp` command + MCP prompt-as-command loader documented — ✅ mechanism; ❓ server set untested |
| Docs freshness | Not verified — `last_doc_scan: never`; pending `@g-platform-scan-docs qwen` |

Sources: [Qwen Code Configuration / settings](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/) · [Qwen Code Commands](https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/) · [QwenLM/qwen-code (GitHub)](https://github.com/QwenLM/qwen-code)
