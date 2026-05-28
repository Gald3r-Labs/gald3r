---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: gemini
authoring_path: update
docs_url: https://github.com/google-gemini/gemini-cli
docs_url_secondary:
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/commands.md
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
crawl_max_age_days: 7
vault_doc_path: research/platforms/gemini/
last_doc_scan: 2026-05-27
reference: g-skl-platform-cursor
status: ⚠️
task: T1467
superseded_by_platform: antigravity   # see "Antigravity 2.0 migration" note below (T1512)
sunset_date: 2026-06-18               # Gemini CLI stops serving Pro/Ultra/free after this date
---

# PLATFORM_SPEC — gemini (Gemini CLI)

Authoring path: **UPDATE** existing `g-skl-platform-gemini/SKILL.md`.

> ## ⚠️ Antigravity 2.0 migration note (T1512, scanned 2026-05-27)
>
> **Google is sunsetting Gemini CLI.** At Google I/O 2026 (**2026-05-19**) Google launched
> **Antigravity 2.0** and announced that **Gemini CLI is being replaced by the Antigravity CLI**.
> The Gemini CLI repo (`google-gemini/gemini-cli`) is **NOT archived** and remains Apache-2.0 open
> source, but on **2026-06-18** the `gemini` binary **stops serving requests** for Google AI Pro,
> Ultra, and free-tier accounts; only paid Gemini Code Assist Standard/Enterprise + paid API keys
> keep working. For practical gald3r purposes, the consumer/free Gemini CLI is **end-of-life**.
>
> **What the successor (Antigravity CLI) changes for gald3r** — see the dedicated spec
> `gald3r_template/.gald3r_sys/platforms/.antigravity/PLATFORM_SPEC.md` (also updated by T1512):
>
> | Aspect | Old Gemini CLI | New Antigravity CLI |
> |---|---|---|
> | Command | `gemini` | **`agy`** (Go, closed-source) ❓ |
> | Instruction file | `GEMINI.md` | **`AGENTS.md`** — `GEMINI.md` **still works**, no rename needed ✅ |
> | Workspace config dir | `.gemini/` | **`.agents/`** (skills: `mv .gemini/skills/ .agents/skills/`) |
> | Skills | ❌ none | **`.agents/skills/`** (per-workspace) + `~/.gemini/skills/<name>/SKILL.md` (global) — surfaced as slash commands ✅ |
> | Hooks | ❌ none | **JSON lifecycle hooks** (before-tool-call / after-file-edit / session-start) ✅ |
> | Subagents | ❌ none | **dynamic subagents** (`/agent`) ✅ |
> | MCP config | `.gemini/settings.json` → `mcpServers` | **`mcp_config.json`** (global `~/.gemini/config/mcp_config.json` ❓); remote field `url` → **`serverUrl`** |
> | Custom commands | `.gemini/commands/*.toml` | superseded by Agent Skills (`.md`) → slash commands; TOML status ❓ |
>
> **Net effect**: the three biggest historical Gemini parity gaps (skills ❌, hooks ❌, agents ❌)
> are **closed** by Antigravity CLI. Antigravity is therefore a *better* gald3r target than Gemini
> CLI was. Source URLs + access dates are in **Verification Evidence** at the bottom.
>
> **Decision (T1512): KEEP the `gemini` platform key as-is for now; do NOT rename it to
> `antigravity`.** Rationale:
> 1. A separate `antigravity` platform key + spec already exists (T1465) and the post-T1511
>    installer already has distinct `gemini`, `agent`, and `antigravity` keys. Renaming `gemini` →
>    `antigravity` would collide with the existing `antigravity` key and is unnecessary.
> 2. Gemini CLI is not archived and paid/enterprise users still have it until/after the cutover, so
>    the `gemini` key is not yet dead — keep it documented with this sunset note.
> 3. The real follow-up work is on the **`antigravity`** spec/skill (promote ❓→✅ now that skills/
>    hooks/subagents are confirmed), **not** on renaming `gemini`.
>
> **Installer follow-up (recommendation only — NOT done here, T1511 is verified):** the installer's
> `gemini` entry currently uses prefix `.gemini` with `cats=@()`. That is still correct for the
> legacy Gemini CLI surface and needs **no immediate change**. A *future* task should decide whether
> the Antigravity CLI install target should write to `.agents/` (its real config dir) under the
> `antigravity` key rather than `.gemini`. Recommended follow-up task title:
> **"Align installer antigravity entry to Antigravity CLI `.agents/` config dir + promote antigravity spec"**.

---

> **State-of-this-spec (post-T1512):** sections 1–9 below describe the **legacy Gemini CLI** (the
> `gemini` binary). They remain accurate for that EOL product. For the successor, read the migration
> note above and the `.antigravity/PLATFORM_SPEC.md`. `last_doc_scan` flipped to **2026-05-27**
> (this T1512 web scan); items still unconfirmed against a live install stay marked `❓`.

**Gemini CLI** (`gemini` command, Google / `google-gemini/gemini-cli`) is Google's open-source
terminal coding agent (Apache-2.0). It is an **instruction-file + JSON-settings** platform, not a
rules/skills/hooks platform like Cursor:

- Its native context mechanism is the hierarchical **`GEMINI.md`** memory file
  (root + `.gemini/` + nested directories), not a folder of always-apply rule files.
- Its native config is **`.gemini/settings.json`** (project) and `~/.gemini/settings.json`
  (user), which also hosts the **`mcpServers`** block.
- It has **native custom commands** via **`.gemini/commands/*.toml`** (TOML files invoked as
  `/namespace:command`), and an **extensions** system (`gemini extensions`).
- It has **no native always-apply rules folder**, **no skills concept**, **no sub-agent file
  system**, and **no lifecycle hook/event system** comparable to Cursor's `hooks.json`.

> **Two folder names in play — read carefully (honesty note):**
> - **`.gemini/`** is what *Gemini CLI itself reads* for `settings.json` and `commands/*.toml`.
> - **`.agent/`** is the folder **gald3r installs into** for this platform (rules/skills/agents/
>   commands as `.md`). Gemini CLI does **not** auto-discover `.agent/` content — gald3r's
>   `g-rl-*`, `g-skl-*`, and `g-agnt-*` markdown is surfaced to Gemini only by being **referenced
>   from `GEMINI.md`**, not by native folder loading. This is the central parity gap (§9).

This repo (`gald3r_templates`) has **no `.gemini/` folder** and no installed `.agent/` Gemini
tree at spec time, so all claims below are **doc-derived (❓ / ⚠️)** and not install-verified.
`last_doc_scan: never` — no SCAN_DOCS crawl has been run.

---

## 1. Folder Hierarchy

Two distinct trees. The first is Gemini-native; the second is the gald3r install target.

**Gemini CLI native config (what `gemini` reads):**
```
.gemini/                         ← Gemini CLI project config (Gemini owns this)
├── settings.json                ← model, tools, theme, mcpServers, context settings
├── commands/                    ← custom slash commands (TOML), nestable for namespacing
│   └── <name>.toml              ← invoked as /<name> (or /<dir>:<name>)
└── (extensions installed via `gemini extensions install`)
GEMINI.md                        ← root context/memory file (hierarchical; see §2)
~/.gemini/settings.json          ← user-global settings (mcpServers, auth)
```

**gald3r install target (what the parity sync writes):**
```
.agent/                          ← gald3r canonical install folder for Gemini
├── rules/g-rl-*.md              ← gald3r rules (NOT natively loaded by Gemini — see §7/§9)
├── skills/<name>/SKILL.md       ← gald3r skills (NOT natively loaded — see §4/§9)
├── agents/g-agnt-*.md           ← gald3r agent defs (NOT natively loaded — see §3/§9)
└── commands/g-*.md              ← gald3r command docs in .md (NOT Gemini's .toml format — §5/§9)
GEMINI.md                        ← gald3r-generated; the ONLY file Gemini natively reads
.mcp.json (root) and/or .gemini/settings.json → mcpServers
```

- **Gemini owns**: `.gemini/`, `settings.json` schema, `commands/*.toml` schema, extensions.
- **gald3r writes**: `.agent/` (rules/skills/agents/commands as `.md`), `GEMINI.md`, MCP config.
- **Honesty**: the `.agent/` tree is gald3r's portable layout; Gemini CLI does not scan it. Only
  `GEMINI.md` (and `.gemini/`) are read natively. Note: Gemini docs/community also reference
  `.agents/` in some contexts; gald3r standardizes on `.agent/` and does not create both.

## 2. AI Instruction File

**`GEMINI.md`** is Gemini CLI's native instruction/memory file (configurable name via
`contextFileName` in `settings.json`). It is loaded **hierarchically**: global `~/.gemini/GEMINI.md`,
then the project root `GEMINI.md`, then `GEMINI.md` in ancestor/sub directories of the file in
context — concatenated into the prompt. The active context is inspectable with `/memory show` and
reloadable with `/memory refresh`.

- gald3r **generates / merges** `GEMINI.md` via the setup + parity pipeline. In the gald3r
  ecosystem the universal instructions live in **`AGENTS.md`**, and `GEMINI.md` is a thin
  Gemini-specific overlay that points at `AGENTS.md` (see
  `gald3r_template/.gald3r_sys/platforms/GEMINI.md`).
- `GEMINI.md` is personalized per user and gitignored (`g-rl-02` protected files).
- **Caveat (⚠️)**: Gemini's `/memory add` "save to memory" feature appends to `GEMINI.md`; guard
  against Gemini-injected memory overwriting gald3r-authored sections.

## 3. Agents Support

- **Native concept**: ❌ Gemini CLI has **no sub-agent / agent-file system** equivalent to
  Cursor's `.cursor/agents/`. There is no native discovery of `g-agnt-*.md`.
- **gald3r approach**: `g-agnt-*.md` files are installed under `.agent/agents/` for portability,
  but are surfaced to Gemini only by being **referenced from `GEMINI.md`/`AGENTS.md`** and invoked
  conversationally (e.g. "act as @g-agnt-task-manager"). There is no platform-level "select agent"
  affordance.
- **Status**: ⚠️ partial (works via instruction-file reference; not a native primitive). ❓ untested.

## 4. Skills Support

- **Native concept**: ❌ Gemini CLI has **no skills system**. `SKILL.md` folders are not
  auto-discovered or model-selected the way Cursor loads `g-skl-*`.
- **gald3r approach**: skills are installed under `.agent/skills/<name>/SKILL.md` for portability
  and are reachable only when their content is pulled in via `GEMINI.md` references or pasted into
  context. Gemini's nearest native analogue is **extensions** (`gemini extensions`) and **custom
  commands**, which are a different shape than gald3r skills.
- **Status**: ❌ no native skills loading / ⚠️ usable only via instruction-file reference. ❓ untested.

## 5. Commands / Workflows

- **Native commands**: ✅ Gemini CLI supports **custom slash commands** defined as **TOML** files
  in `.gemini/commands/` (project) or `~/.gemini/commands/` (user). Each `<name>.toml` defines a
  `prompt` (and optional `description`); the file path sets the invocation, e.g.
  `git/commit.toml` → `/git:commit`. Built-in commands (`/memory`, `/tools`, `/mcp`, `/chat`,
  `/help`, etc.) are also slash-invoked.
- **gald3r gap**: gald3r ships its commands as `.md` under `.agent/commands/g-*.md`, which is
  **NOT** the native `.gemini/commands/*.toml` format. So gald3r commands are documentation, not
  executable Gemini slash commands, unless a TOML wrapper is generated (not currently produced).
- **Workflows**: there is no separate "workflow YAML" primitive in Gemini CLI itself (Google
  Antigravity, a related Google IDE, has a workflows concept — out of scope here).
- **Status**: ⚠️ native TOML commands exist but gald3r's `g-*` commands are not emitted in that
  format → not executable as slash commands. ❓ untested.

## 6. Hooks System

- **Native concept**: ❌ Gemini CLI has **no lifecycle hook / event system** — there is no
  `hooks.json`, no `sessionStart` / `stop` / `preToolUse` / `beforeShellExecution` wiring.
- **gald3r approach**: session automation that other platforms get from `g-hk-*` hooks must be
  done manually (run scripts by hand) or be triggered via instruction-file conventions in
  `GEMINI.md`. The PCAC inbox check, session-start context injection, and pre-commit/pre-push
  gates have **no automatic firing surface** on Gemini.
- **Status**: ❌ not supported. (Closest related capability is **extensions** for adding tools,
  which is not an event/lifecycle hook.) ❓ extension-based workaround untested.

## 7. Rules / Memory

- **Native concept**: ❌ no always-apply **rules folder**. Gemini's persistent-context mechanism
  is the hierarchical **`GEMINI.md`** memory file (§2), not a directory of `.mdc`/`.md` rule files
  with `alwaysApply`/`globs` frontmatter.
- **gald3r approach**: `g-rl-*.md` rules are installed under `.agent/rules/` as plain **`.md`**
  (the parity sync maps Cursor's `.mdc` → `.md`). They are **only effective if referenced from
  `GEMINI.md`** — Gemini will not auto-load `.agent/rules/`. There is no native `globs:` scoping
  or `alwaysApply:` enforcement; "always apply" is achieved by inlining/linking into `GEMINI.md`.
- **Token/size note (⚠️)**: `GEMINI.md` is concatenated into every prompt, so keep referenced
  rule content lean to avoid context bloat (existing SKILL.md guidance: ~300 lines/rule).
- **Status**: ⚠️ partial — memory via `GEMINI.md` works; folder-based always-apply rules do not.

## 8. MCP Support

- **Supported**: ✅ Yes. Gemini CLI has first-class MCP support.
- **Config format/location**: an **`mcpServers`** block inside **`.gemini/settings.json`** (project)
  or `~/.gemini/settings.json` (user). Each entry supports `command`/`args`/`env` (stdio) or
  `url`/`httpUrl` (SSE/HTTP) transports, plus `timeout`, `trust`, and tool include/exclude filters.
  Inspect/manage with the built-in **`/mcp`** command.
- **gald3r note**: the gald3r `platforms/GEMINI.md` template documents MCP via a root **`.mcp.json`**
  (`mcpServers` → gald3r server URL). Both surfaces target the same `mcpServers` shape; the
  authoritative native location is `.gemini/settings.json`. (`.mcp.json` is gitignored, machine-
  specific — `g-rl-02`.)
- **Status**: ✅ mechanism verified by docs; ❓ concrete server set untested in this repo (no
  `.gemini/settings.json` present).

## 9. Known Gaps vs. Cursor Reference

Honest list of Cursor-reference features that do **not** work, are non-native, or are untested on
Gemini CLI. This feeds `PLATFORM_STATUS.md` and the capability matrix.

1. **No native hook/event system (❌)** — Cursor's `.cursor/hooks.json` (sessionStart, stop,
   preToolUse, beforeShellExecution) has no Gemini equivalent. All hook-driven automation
   (PCAC inbox check, session-start injection, pre-commit/push gates) is manual. **Decision tree:
   documented gap** (no platform config can supply this today).
2. **No native rules folder (❌→⚠️)** — `.agent/rules/g-rl-*.md` is not auto-loaded. Always-apply
   behavior must be inlined/linked from `GEMINI.md`. No `alwaysApply:`/`globs:` semantics.
   **Platform-specific**: rule effectiveness depends on `GEMINI.md` references.
3. **No native skills loading (❌→⚠️)** — `.agent/skills/<name>/SKILL.md` is not model-discovered.
   Skills reachable only via `GEMINI.md` reference. Gemini's native analogues are **extensions**
   and **custom commands**, which differ in shape. **Documented gap.**
4. **No native agent files (❌→⚠️)** — no `.cursor/agents/`-style discovery. `g-agnt-*.md` works
   only as conversational instruction-file references. **Documented gap.**
5. **Command format mismatch (⚠️)** — Gemini's native custom commands are **TOML** in
   `.gemini/commands/`, invoked as `/name` or `/dir:name`. gald3r emits `.md` under
   `.agent/commands/g-*.md`, which are **not executable** as Gemini slash commands. A TOML emitter
   for `g-*` commands does not exist yet. **Platform-specific config gap.**
6. **`.gemini/` vs `.agent/` split (⚠️)** — the only files Gemini natively reads are `GEMINI.md`
   and `.gemini/`. The entire `.agent/` install tree is portability scaffolding, not native input.
7. **SCAN_DOCS not yet run (❓)** — `last_doc_scan: never`. Doc-derived claims (exact
   `settings.json` MCP/command keys, current built-in slash-command list, extension API) should be
   confirmed by `@g-platform-scan-docs gemini` against the GitHub docs.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no native hook/event system.
- **Rules ⚠️** — only via `GEMINI.md` memory; no folder-based always-apply.
- **Skills ❌** — no native skills discovery (instruction-file reference only).
- **Commands ⚠️** — native TOML slash commands exist, but gald3r `g-*` are `.md`, not executable.
- **MCP ✅** — first-class `mcpServers` in `.gemini/settings.json` (mechanism doc-verified).
- **Docs Fresh ❓** — `last_doc_scan: never`; flip to ✅ after first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Folder hierarchy | Doc-derived (Gemini CLI configuration docs) + gald3r `.agent/` parity convention. No `.gemini/` present in this repo — ❓ install-untested |
| AI instruction file | `GEMINI.md` hierarchical memory documented in Gemini CLI docs; gald3r template at `platforms/GEMINI.md` confirms overlay pattern |
| Agents | No native agent system in Gemini CLI docs — ❌ native; ⚠️ via instruction reference |
| Skills | No native skills system in Gemini CLI docs — ❌ native |
| Commands | Native custom commands = TOML in `.gemini/commands/` (Gemini commands docs); gald3r emits `.md` → ⚠️ mismatch |
| Hooks | No hook/event system in Gemini CLI docs — ❌ |
| Rules / memory | `GEMINI.md` + `/memory` documented; no rules-folder primitive — ⚠️ |
| MCP | `mcpServers` in `settings.json` + `/mcp` command documented (Gemini MCP docs) — ✅ mechanism; ❓ server set untested |
| Docs freshness | Web-scanned 2026-05-27 (T1512) for migration status; legacy CLI capability cells not re-crawled against a live install |

### T1512 migration sources (accessed 2026-05-27)
- https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/ — official Gemini CLI → Antigravity CLI transition
- https://github.com/google-gemini/gemini-cli/discussions/27274 — "Transitioning Gemini CLI to Antigravity CLI" discussion (repo NOT archived, still Apache-2.0)
- https://www.theregister.com/ai-ml/2026/05/20/bye-bye-gemini-cli-google-nudges-devs-toward-antigravity/5243605 — closed-source successor, June 18 2026 cutover
- https://techcrunch.com/2026/05/19/google-launches-antigravity-2-0-with-an-updated-desktop-app-and-cli-tool-at-io-2026/ — Antigravity 2.0 launch (desktop IDE + CLI)
- https://www.aimadetools.com/blog/migrate-gemini-cli-to-antigravity-cli/ — `.gemini/skills/`→`.agents/skills/`, GEMINI.md/AGENTS.md both work, June 18 deadline
- https://dev.to/arindam_1729/antigravity-cli-a-hands-on-guide-to-googles-terminal-coding-agent-5bc7 — `agy` command, skills/hooks/subagents, mcp_config.json
