---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: aider
authoring_path: update
docs_url: https://aider.chat/docs
docs_url_secondary:
  - https://aider.chat/docs/usage/conventions.html
  - https://aider.chat/docs/usage/commands.html
  - https://aider.chat/docs/usage/modes.html
  - https://aider.chat/docs/usage/lint-test.html
  - https://aider.chat/docs/config/options.html
  - https://github.com/Aider-AI/aider/issues/4506
crawl_max_age_days: 14
vault_doc_path: research/platforms/aider/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Aider (AI pair programming in your terminal)

Aider is a minimal terminal-based AI pair programmer that edits files in your local git repo and
**auto-commits** each accepted change. As of mid-2026 its extensibility surface is **narrow**: of the
six gald3r-relevant primitives only **rules** is genuinely native (the read-only `CONVENTIONS.md`
convention). **Commands**, **agents**, and **hooks** are **partial** — a rich built-in slash-command
set but no user-authored commands; four fixed chat modes (incl. the architect/editor two-LLM split)
but no user-definable sub-agents; an auto-lint/auto-test post-edit trigger but no general event-hook
bus. **Skills** and **MCP** are **not native** at all (community package / open feature request only).

Critically for gald3r, aider has **no `AGENTS.md`/`CLAUDE.md` auto-discovery** — instruction files
reach it only by pointing `--read` / `.aider.conf.yml` `read:` at an arbitrary markdown file
(`CONVENTIONS.md` is the documented default). gald3r's Claude-Code artifacts are therefore **NOT
drop-in reusable**; the install must fold guidance into a pinned read-only convention file.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://aider.chat/docs (see Verification
Evidence). This **supersedes** the prior spec (`last_doc_scan: never`): commands/agents/hooks are
correctly re-graded **⚠️ partial** (not ❌) to reflect aider's real built-in command surface, fixed
chat modes, and narrow lint/test post-edit trigger, while skills and MCP remain ❌.

> **Surface split:** the **core aider CLI** is the gald3r target. **AiderDesk** (the GUI wrapper) and
> third-party bridges (`mcpm-aider`, the `aider-skills` PyPI package) add MCP / skill loading
> externally — those are **not core aider** and are out of scope for a portable gald3r install.

---

## 1. Folder Hierarchy

```
<project-root>/
├── CONVENTIONS.md           ← documented default instruction file (read-only, pinned via config)
├── .aider.conf.yml          ← YAML config (model roles, read:, auto-lint/test, auto-commits)
├── .aider.model.settings.yml / .aider.model.metadata.json  ← custom model definitions
├── .env                     ← API keys
└── .aiderignore             ← excludes paths from aider's context (gitignore syntax)
```

There is **no `.aider/` extension tree** — aider discovers no `commands/`, `agents/`, `skills/`, or
`hooks/` directories. The only persistent gald3r-writable surface is a markdown convention file
referenced from `read:`, plus the YAML config.

**gald3r writes**: `CONVENTIONS.md` (folded guidance) + `.aider.conf.yml` (`read:` pins, model roles,
`auto-commits: false`, optional `auto-lint`/`auto-test`).
**Aider owns**: the repo map (semantic file index — aider-managed, not a gald3r-writable surface),
the git auto-commit pipeline, and the built-in slash-command set.

---

## 2. AI Instruction File

Aider has **no auto-discovered instruction file** — it does **not** read `AGENTS.md` or `CLAUDE.md`
(no native auto-discovery; a request to recommend `AGENTS.md` as standard is GitHub issue #4363, and
because aider already accepts arbitrary filenames the maintainers note "no code changes needed"). The
documented convention is **`CONVENTIONS.md`**, loaded read-only via `aider --read CONVENTIONS.md`
(per session) or persisted via `.aider.conf.yml` → `read: CONVENTIONS.md` (also accepts a list). The
filename is arbitrary; pointing `--read`/`read:` at `AGENTS.md` works, but only because it is an
explicit read target, not native discovery. Pinned `read:` files are cached when prompt caching is
enabled and consume the context budget every turn — pin selectively.

## 3. Agents Support — ⚠️ PARTIAL

- **Chat modes** (`code` / `architect` / `ask` / `help`) are the only multi-role behavior.
  **Architect mode** = an architect model proposes changes and an **editor model** (`--editor-model`)
  translates them into specific file edits — a fixed two-LLM workflow.
- These are **fixed built-in modes, NOT user-definable specialized sub-agents.** There are **no
  agent-definition files** and no agent roster; gald3r `g-agnt-*` definitions have no runtime home.
- Source: https://aider.chat/docs/usage/modes.html

## 4. Skills Support — ❌ NOT NATIVE

- Official aider docs describe **no `SKILL.md` / Agent Skills feature** and no skill
  discovery/activation engine. A community **`aider-skills`** PyPI package injects skills "with zero
  aider changes" (bolted on externally, not a core capability); one marketplace's "partial" rating
  refers to that external loader, not core aider.
- gald3r `g-skl-*/SKILL.md` do **not** load. A skill's instructions reach aider only if its markdown
  is copied into a `read:` convention file — there is no activation/discovery engine.
- Source: https://libraries.io/pypi/aider-skills

## 5. Commands / Workflows — ⚠️ PARTIAL

- **40+ built-in slash commands** (`/add`, `/architect`, `/ask`, `/run`, `/test`, `/lint`, `/load`,
  `/read-only`, `/web`, `/voice`, …). `/load` "Load and execute commands from a file" batches/replays
  **existing built-in** commands from a file.
- The docs describe **no way for users to DEFINE custom commands or aliases.** `/load` only replays
  built-ins; gald3r `@g-*` / `/g-*` commands cannot be registered natively.
- Source: https://aider.chat/docs/usage/commands.html

## 6. Hooks System — ⚠️ PARTIAL

- **Auto-lint / auto-test post-edit triggers**: `--auto-lint` + `--lint-cmd` and `--auto-test` +
  `--test-cmd` make aider "automatically lint and test your code every time it makes changes" — a real
  post-edit lifecycle trigger, but narrowly scoped to lint/test commands. Git **auto-commit** fires
  after each accepted edit; git `pre-commit` hooks fire only via normal git, not an aider extension
  point.
- **No general session-start / pre-tool / arbitrary-event hook system** — general pre/post-prompt
  script hooks are an **open feature request (#2045)** ("no general mechanism for running arbitrary
  scripts on events"). gald3r `g-hk-*.ps1` have **no native event bus**; they run manually (e.g. via
  `/run`), as `CONVENTIONS.md` guidance text, or via git `core.hooksPath` (pre-commit/pre-push only).
- Source: https://aider.chat/docs/usage/lint-test.html

## 7. Rules / Memory — ✅ NATIVE

- **Coding conventions file** (`CONVENTIONS.md`) is a genuine always-on instruction mechanism:
  "Tell aider to follow your coding conventions when it works on your code." Load with
  `aider --read CONVENTIONS.md` (marked read-only, cached if prompt caching enabled) or persist via
  `.aider.conf.yml` → `read: CONVENTIONS.md` (single value or list).
- The filename is **arbitrary** (`CONVENTIONS.md` is the documented convention); there is **no rules
  folder** (`.mdc`/`.md` always-apply) and **no `AGENTS.md`/`CLAUDE.md` auto-discovery**. gald3r
  `g-rl-*` content must be **folded into the pinned convention file** — that is the only persistent
  always-apply surface.
- Source: https://aider.chat/docs/usage/conventions.html

## 8. MCP Support — ❌ NOT NATIVE

- Core aider CLI has **no built-in MCP client or server.** Issue **#4506** ("Add native MCP server and
  Agent Mode support to Aider CLI (as in AiderDesk)", opened 2025-09-09) is **OPEN with no maintainer
  acceptance/roadmap.** The community `mcpm-aider` bridge calls itself "an experiment … until native
  MCP support becomes available."
- **AiderDesk** (the GUI wrapper) and external bridges add MCP, but that is **not core aider** — gald3r
  MCP tools/servers cannot be consumed natively. Substitutes within core aider: `/web` (scrape a URL
  into chat), `/run` (shell), `/read-only` (pin context).
- Source: https://github.com/Aider-AI/aider/issues/4506

## 9. Other Extensibility — config & scripting

- **Config files**: `.aider.conf.yml` (YAML project/home config), `.env` (API keys),
  `.aider.model.settings.yml` / `.aider.model.metadata.json` (custom model definitions).
- **Model roles**: `--model` / `--editor-model` / `--weak-model` assign different models to the main,
  editor (architect mode), and commit-message/summary roles.
- **Scripting**: a **Python scripting API** (`import aider`, programmatic `Coder`) plus command-line
  scripting; `/load` replays built-in commands from a file.
- **Watch files**: `--watch-files` watches source files for `AI!` / `AI?` comment triggers — a
  lightweight file-watch behavior (not a general hook bus).
- **Input sources**: `/voice` (speech-to-text) and `/web` (scrape a URL into chat).
- Source: https://aider.chat/docs/config/options.html

---

## Parity vs. Cursor Reference

Aider reaches only **partial parity** with the Cursor reference (`g-skl-platform-cursor`): native
**rules** (via `CONVENTIONS.md`); partial **commands** (built-ins only, no custom registration),
**agents** (fixed chat modes / architect-editor split, no sub-agent files), and **hooks** (auto-lint/
test post-edit trigger only). **Skills** and **MCP** are not native. The **repo map** (semantic file
index) is an aider-native bonus with no Cursor analog — retrieval, not a writable store.

**Reuse note (important):** because aider does **NOT** read `CLAUDE.md`/`AGENTS.md` and discovers no
`.claude/` / `.agents/` trees, gald3r's Claude-Code platform artifacts are **NOT reusable** on aider.
The only portable install path is to **fold gald3r guidance into a pinned read-only `CONVENTIONS.md`**
(plus `.gald3r/PROJECT.md` / `CONSTRAINTS.md` pinned via `read:`) and set `auto-commits: false` to
defer to gald3r's task-scoped commit discipline.

## Hook System

- **Type**: partial (no general event bus; narrow lint/test post-edit trigger only)
- **Config file**: `.aider.conf.yml` (`auto-lint` + `lint-cmd`, `auto-test` + `test-cmd`); git
  `core.hooksPath` for pre-commit/pre-push
- **Events available**: post-edit auto-lint, post-edit auto-test, post-edit git auto-commit — **NO**
  SessionStart / SessionEnd / PreToolUse / Stop / arbitrary-event hooks
- **Event payload format**: none (lint/test invoke configured shell commands; no stdin JSON payload)
- **Command extensions**: any shell command via `lint-cmd`/`test-cmd`/`/run`; `.ps1` runs only when
  invoked explicitly (e.g. `pwsh -File g-hk-*.ps1`), not auto-fired on lifecycle events
- **gald3r hook files**: `g-hk-*.ps1` have **no native event home** — run them manually via `/run`,
  encode their intent as `CONVENTIONS.md` guidance, or wire pre-commit/pre-push via git
  `core.hooksPath`. General pre/post-prompt hooks are open feature request #2045.

## Atypical Handling

- **No `AGENTS.md`/`CLAUDE.md` auto-read** (issue #4363) — fold enforcement into `CONVENTIONS.md` +
  `read:` pins; arbitrary filenames work only as explicit `--read` targets.
- **Auto-commit collision**: aider auto-commits each accepted edit — set `auto-commits: false` to
  defer to gald3r's task-scoped commit discipline, or audit commits after the fact.
- **Core vs. AiderDesk split**: MCP and external skill loading exist only in AiderDesk / third-party
  bridges, never core aider. Target the core CLI for a portable gald3r install.

## gald3r Integration Notes

- Ship `CONVENTIONS.md` (folded `g-rl-*` guidance) + pin `.gald3r/PROJECT.md` / `CONSTRAINTS.md` via
  `.aider.conf.yml` `read:`; set `auto-commits: false`.
- Skills/agents/custom-commands/MCP have **no runtime home** — do not expect `.claude/` reuse.
- Optionally wire `lint-cmd`/`test-cmd` to a gald3r verification script for a post-edit gate; route
  pre-commit/pre-push `g-hk-*.ps1` via git `core.hooksPath`.
- Re-verify on the next `@g-platform-scan-docs aider` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ✅ | ❌ | ⚠️ | ❌ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://aider.chat/docs)

| Capability | How verified |
|---|---|
| Commands | /usage/commands.html — 40+ built-in slash commands; `/load` replays built-ins from a file; **no** user-defined custom commands/aliases → ⚠️ |
| Rules | /usage/conventions.html — `CONVENTIONS.md` read-only via `--read` / `.aider.conf.yml read:`; arbitrary filename; no rules folder, no AGENTS.md auto-discovery → ✅ |
| Agents | /usage/modes.html — fixed chat modes (code/architect/ask/help); architect = architect-model + `--editor-model`; no user-definable sub-agents, no agent files → ⚠️ |
| Skills | libraries.io/pypi/aider-skills — no native SKILL.md/Agent Skills; community `aider-skills` injects "with zero aider changes" externally → ❌ |
| Hooks | /usage/lint-test.html — `--auto-lint`/`--lint-cmd` + `--auto-test`/`--test-cmd` post-edit trigger + git auto-commit; general event hooks = open FR #2045 → ⚠️ |
| MCP | github.com/Aider-AI/aider/issues/4506 — OPEN, no maintainer roadmap; only AiderDesk / `mcpm-aider` bridges (experimental); core CLI has none → ❌ |
| Instruction file | /usage/conventions.html + issue #4363 — no AGENTS.md/CLAUDE.md auto-discovery; `CONVENTIONS.md` is documented default, any filename works via explicit `--read`/`read:` |
| Other extensibility | /config/options.html — `.aider.conf.yml`, model roles (`--model`/`--editor-model`/`--weak-model`), Python scripting API, `--watch-files` (AI!/AI? triggers), `/voice`, `/web` |
| Cross-compat | aider does NOT read `.claude/`/`.agents/` or `CLAUDE.md`/`AGENTS.md` → gald3r Claude artifacts NOT reusable; fold into pinned `CONVENTIONS.md` |
