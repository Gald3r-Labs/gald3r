---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: aider
authoring_path: update
docs_url: https://aider.chat/docs
docs_url_secondary:
  - https://aider.chat/docs/config/aider_conf.html
  - https://aider.chat/docs/usage/conventions.html
  - https://aider.chat/docs/config/options.html
crawl_max_age_days: 14
vault_doc_path: research/platforms/aider/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1473
---

# PLATFORM_SPEC — aider (terminal pair-programmer)

Authoring path: **UPDATE** existing `g-skl-platform-aider/SKILL.md`.

**Aider** (`aider` command) is an open-source terminal-based AI pair-programmer that edits files
in your local git repo and **auto-commits** each accepted change. It is the most **minimal** of
the gald3r target platforms: a single YAML config file (`.aider.conf.yml`), a project conventions
file (`CONVENTIONS.md`), a `.aiderignore`, and a set of in-session **in-chat `/commands`** (typed
inside the running aider REPL — not a discoverable slash-command framework).

Aider has **no concept of agents, no skill discovery, no rules folder, and no lifecycle-hook
system**. It builds a **repo map** (a tree-sitter–derived summary of the codebase) to give the
model project context, and lets you pin additional context files as **read-only**. Behavioral
enforcement for gald3r is delivered almost entirely through `CONVENTIONS.md` + read-only
`.gald3r/` context files. This produces many honest `❌` capability marks below — that is the
correct, factual assessment for a minimal CLI, not an implementation failure.

This spec corrects stale assumptions in the prior SKILL.md (e.g. an outdated default model string
and the implication of richer integration than aider actually provides).

---

## 1. Folder Hierarchy

Aider is **not** folder-namespaced like Cursor/Claude. There is no `.aider/` directory tree of
rules/skills/agents/commands/hooks. Aider reads a flat set of root-level files:

```
<project-root>/
├── .aider.conf.yml          ← Aider config (model, auto-commits, read:, etc.) — gald3r writes
├── CONVENTIONS.md           ← project conventions; loaded as read-only context — gald3r writes
├── .aiderignore             ← files excluded from aider's context (gitignore syntax) — gald3r writes
├── .aider.model.settings.yml ← optional per-model setting overrides (aider-owned format)
├── .aider.model.metadata.json ← optional model metadata/pricing overrides (aider-owned)
├── .aider.chat.history.md   ← aider-generated chat transcript (NOT gald3r; should be ignored)
└── .aider.input.history     ← aider-generated input history (NOT gald3r; should be ignored)

~/.aider.conf.yml            ← optional user-level global config (aider merges global + project)
~/.aider/                    ← aider's own cache/state (analytics, etc.) — platform-owned
```

- **gald3r writes**: `.aider.conf.yml`, `CONVENTIONS.md`, `.aiderignore`.
- **Aider owns**: config-key schema, the repo-map mechanism, model-settings file formats, chat
  history files, `~/.aider/` state.
- There is **no** `.aider/rules/`, `.aider/skills/`, `.aider/agents/`, `.aider/commands/`, or
  `.aider/hooks/`. All gald3r primitives that rely on those directories have no native home here.

## 2. AI Instruction File

- **Primary instruction surface: `CONVENTIONS.md`** (project root). Aider does NOT auto-discover
  it by filename — you must point aider at it. Either pin it in `.aider.conf.yml`:
  ```yaml
  read:
    - CONVENTIONS.md
    - .gald3r/PROJECT.md
    - .gald3r/CONSTRAINTS.md
  ```
  or load it interactively with `/read-only CONVENTIONS.md`, or at launch with
  `aider --read CONVENTIONS.md`. Loading it via `read:`/`/read-only` marks it read-only and (when
  prompt caching is on) caches it.
- Aider does **not** read `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` natively. gald3r's behavioral
  enforcement must therefore be folded into `CONVENTIONS.md` (and/or other files added to `read:`),
  since that is the only always-present instruction surface aider honors.
- gald3r **generates** `CONVENTIONS.md` and the `read:` list during install.

## 3. Agents Support

- **No native agent concept. ❌** Aider has no `g-agnt-*.md` discovery, no agent-mode roster, and
  no multi-agent orchestration. There is a single conversational assistant.
- gald3r's agent roster (task-manager, planner, qa-engineer, code-reviewer, …) cannot be selected
  as discrete agents. The closest analogue is aider's **chat modes** (`/chat-mode code|ask|help`,
  plus `architect` mode which pairs a planning model with an editing model) — these are *modes*,
  not gald3r agents, and do not load agent definition files.
- Agent *behaviors* can only be approximated by describing them inside `CONVENTIONS.md`.

## 4. Skills Support

- **No skill discovery / loading / invocation. ❌** Aider has no `SKILL.md` mechanism, no
  folder-per-skill scan, and no "load skill when relevant" model-driven activation.
- gald3r skills (`g-skl-*`) have no runtime home on aider. The *instructions* a skill encodes can
  only reach aider if copied into a file that is added to the `read:` context (e.g. into
  `CONVENTIONS.md`), which does not scale to the full skill set.
- This is a hard gap, not a config oversight.

## 5. Commands / Workflows

- **In-chat `/commands` only — NOT a discoverable command framework. ⚠️/❌**
  Aider ships built-in REPL commands typed into the running session, e.g. `/add`, `/read-only`,
  `/drop`, `/diff`, `/undo`, `/commit`, `/run <shell>`, `/test`, `/web <url>`, `/ask`, `/code`,
  `/architect`, `/chat-mode`, `/model`, `/map` (show repo map), `/help`, `/ok`.
- These are **fixed built-ins** — there is no mechanism to register custom `g-*` commands, no
  `commands/` folder, and no `@g-*` / `/g-*` palette equivalent. gald3r commands cannot be
  installed as aider commands.
- The closest "do something" primitives are `/run` (run an arbitrary shell command and optionally
  feed output back to the model) and `/web` (scrape a URL into context). A gald3r workflow would
  have to be driven manually by the user invoking these built-ins.

## 6. Hooks System

- **No hook / lifecycle-event system. ❌** Aider exposes no `sessionStart`, `stop`, `preToolUse`,
  `postToolUse`, or `beforeShellExecution` events, and no `hooks.json` / settings hook table.
- Consequence for gald3r: the PowerShell session-start / inbox-check / pre-commit hooks that
  auto-fire on Cursor and Claude Code **do not fire on aider**. There is no wiring point.
- Aider does have **auto-commit** (it commits after each accepted edit) and supports `--commit`,
  `lint-cmd`, and `test-cmd` config keys that run a linter/test command after edits — these are
  edit-cycle automations, **not** a general hook bus and cannot run gald3r `.ps1` lifecycle hooks.
  The only way to run a gald3r hook script is to invoke it manually via `/run`.

## 7. Rules / Memory

- **No native rules directory. ❌** No `.aider/rules/`, no `.md`/`.mdc` rule-file discovery, no
  `alwaysApply`/`globs` frontmatter mechanism.
- Persistent "always-apply" guidance lives in **`CONVENTIONS.md`** (and any other file listed in
  `read:`), which aider re-loads as read-only context each session. That is aider's only
  persistent-memory analogue.
- Practical limit: every read-only file consumes the context/token budget on every turn, so the
  amount of "rules" you can keep resident is bounded by the model's context window — be selective
  (the existing SKILL.md pitfall about not pinning a large `TASKS.md` is correct).

## 8. MCP Support

- **Not natively supported. ❌** As of the aider releases verified here (≈v0.86.x, mid-2026),
  aider does **not** ship a Model Context Protocol client. There is an open RFC (issue #4506) and a
  closed exploratory PR (#3937), but no shipped, documented MCP integration. ❓ A future release
  could add it — re-confirm at the next doc scan.
- Closest native equivalents for "pull external context / call a tool": `/web <url>` (scrape a
  page into context), `/run <cmd>` (run a shell tool and feed back output), and `/read-only`
  (pin file context). These are manual and not an MCP server registry.

## 9. Known Gaps vs. Cursor Reference

Per the decision tree in `g-skl-platform-cursor/SKILL.md` — a capability either (a) lives in
common `.gald3r_sys/`, (b) needs platform-specific config in `.gald3r_sys/platforms/.aider/`, or
(c) is a documented gap:

| Cursor-reference capability | Aider status | Disposition |
|---|---|---|
| `.cursor/rules/*.mdc` always-apply rules | ❌ no rules dir | (c) gap → folded into `CONVENTIONS.md` read-only context |
| `agents/g-agnt-*.md` file discovery | ❌ no agent concept | (c) hard gap → chat modes only; behaviors described in `CONVENTIONS.md` |
| `skills/g-skl-*/SKILL.md` discovery + auto-load | ❌ no skill mechanism | (c) hard gap → no runtime home |
| `commands/` slash-command palette (`@g-*`) | ❌ built-in `/commands` only, not extensible | (c) gap → manual `/run`, `/web` |
| Lifecycle hooks (`hooks.json`, sessionStart, …) | ❌ none | (c) hard gap → manual via `/run`; auto-commit/lint-cmd/test-cmd are not a hook bus |
| MCP servers | ❌ not native (RFC open) | (c) gap → `/web`, `/run` substitutes |
| Read-only context / repo map | ✅ native (`read:`, `/read-only`, repo map) | (a)/(b) the one strong fit — gald3r context files pinned read-only |
| Auto-commit discipline | ⚠️ aider auto-commits; conflicts with task-scoped commits | (b) set `auto-commits: false` to defer to gald3r commit discipline |

**Hard gaps (not achievable on aider today): agents, skills, rules folder, extensible commands,
lifecycle hooks, native MCP.** The one capability that maps cleanly is **read-only context
pinning** — gald3r delivers `CONVENTIONS.md` + pinned `.gald3r/` files, which is aider's intended
project-context mechanism.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no lifecycle-event system, no `hooks.json`; `lint-cmd`/`test-cmd`/auto-commit are
  edit-cycle automations, not a hook bus.
- **Rules ⚠️** — no rules folder, BUT always-apply enforcement IS deliverable via `CONVENTIONS.md`
  pinned read-only (partial parity, the one place aider can hold persistent guidance).
- **Skills ❌** — no `SKILL.md` discovery/loading/invocation mechanism.
- **Commands ❌** — fixed built-in `/commands` only; no extensible `g-*` command registration.
- **MCP ❌** — not natively supported (RFC #4506 open, no shipped client as of ~v0.86.x).
- **Docs Fresh ❌** — `last_doc_scan: never`; `@g-platform-scan-docs aider` not yet run.

---

## Verification Evidence

| Capability | How verified | Confidence |
|---|---|---|
| `.aider.conf.yml` + `read:` for read-only context | Existing SKILL.md + aider.chat YAML config / conventions docs (WebSearch 2026-05-26) | High |
| `CONVENTIONS.md` loaded via `read:` / `/read-only`, not auto-discovered by name | aider.chat conventions doc (WebSearch) | High |
| In-chat `/commands` are fixed built-ins (`/add`, `/read-only`, `/run`, `/web`, `/chat-mode`, `/map`, …) | aider docs + DeployHQ guide (WebSearch); cross-checked against known aider REPL | Medium-High |
| No agents / skills / rules folder / hooks | Absence of any such mechanism in aider docs; aider is a single-assistant REPL | High (negative finding) |
| MCP not native (RFC open) | aider FAQ/history + RFC #4506 / PR #3937 references (WebSearch) | Medium-High |
| Repo map mechanism (`aider --show-repo-map`, `/map`) | aider docs (WebSearch) | High |
| Auto-commit conflict with gald3r commit discipline | Existing SKILL.md §5 pitfall; aider auto-commit is documented default | High |

**No live install test was run** in this environment; findings rest on the existing gald3r SKILL.md
plus a 2026-05-26 doc scan of https://aider.chat/docs. A formal `@g-platform-scan-docs aider`
crawl is required to set `last_doc_scan` and to re-confirm MCP status on the then-current aider
release. Until then `status: ⚠️` (the read-only-context path works; everything else is a documented
hard gap).
