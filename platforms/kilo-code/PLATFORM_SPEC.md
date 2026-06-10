---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: kilo-code
authoring_path: update
docs_url: https://kilo.ai/docs/
docs_url_secondary:
  - https://kilo.ai/docs/customize/workflows
  - https://kilo.ai/docs/customize/custom-rules
  - https://kilo.ai/docs/customize/custom-subagents
  - https://kilo.ai/docs/customize/skills
  - https://kilo.ai/docs/customize/agents-md
  - https://kilo.ai/docs/automate/mcp/overview
  - https://github.com/Kilo-Org/kilocode/issues/5827
crawl_max_age_days: 14
vault_doc_path: research/platforms/kilo-code/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Kilo Code (VS Code / JetBrains + CLI + Cloud)

Kilo Code is an **open-source** AI coding agent (vendor Kilo-Org / kilo.ai) that ships as a VS Code
extension, a JetBrains plugin, a **CLI**, and a Cloud surface. The current extension/CLI was **rebuilt
on the OpenCode v7 codebase** and adopts a new config convention: a central **`kilo.jsonc`** (JSONC)
plus **`.kilo/`** directories — legacy **`.kilocode/`** paths are auto-migrated and remain backward
compatible. **Five of the six** gald3r-relevant mechanisms are NATIVE and well-documented (commands,
rules, agents, skills, MCP); only **lifecycle/event hooks are missing** (an open, unimplemented
feature request — GitHub Issue #5827). Critically for gald3r, Kilo natively reads **`.claude/skills/`**
and **`.agents/skills/`** (Agent Skills `agentskills.io` open standard) and uses **`AGENTS.md`**, so
gald3r's `SKILL.md` skills and `AGENTS.md` instruction blocks are **largely drop-in reusable**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://kilo.ai/docs/ (see Verification
Evidence). Overall **⚠️ strong-but-one-gap**: native commands/rules/agents/skills/MCP, **no script or
lifecycle hooks** — gald3r session-start and pre-commit automations have no native hook surface here
and must run out-of-band (git hooks / CI).

> **Instruction-file truth:** Kilo reads **`AGENTS.md`** (uppercase, project root + subdirectory
> cascade), **not** `CLAUDE.md`. The deprecated **Memory Bank** is being folded into `AGENTS.md`.
> Surface note: the full mechanism set is available in **both** the extension and the CLI; the
> permission model (allow/ask/deny, namespaced MCP keys) is shared across surfaces.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                         ← instruction file Kilo reads (root + subdir cascade)
├── kilo.jsonc                        ← central JSONC config (agent / mcp / skills keys, global rules)
└── .kilo/                            ← replaces legacy .kilocode/ (auto-migrated, backward compatible)
    ├── rules/      *.md              ← Custom Rules (loaded automatically every interaction)
    ├── commands/   <name>.md         ← Workflows / slash commands (/<name>)
    ├── agents/     <name>.md         ← Custom Subagents (isolated sessions)
    └── skills/     <name>/SKILL.md   ← Agent Skills (agentskills.io standard)
```

Global equivalents live under `~/.config/kilo/` (`commands/`, `agents/`) and `~/.kilo/skills/`, with
global config in `~/.config/kilo/kilo.jsonc`. Kilo **also** discovers `.claude/skills/` (Claude Code
compatibility) and `.agents/skills/` (open standard, loaded by default), so gald3r's `.claude/`-style
skill tree works on Kilo with **no Kilo-specific port**.

**gald3r writes**: any of the above; for maximum reuse, gald3r's `SKILL.md` skills load straight from
`.claude/skills/` or `.agents/skills/`, and `AGENTS.md` is read as-is.
**Kilo owns**: the `.kilo/` namespace, the `kilo.jsonc` schema, the built-in permission system, and
the Kilo Marketplace distribution channel.

---

## 2. AI Instruction File

Kilo reads **`AGENTS.md`** — filename must be uppercase, at project root; Kilo loads both the root and
any subdirectory `AGENTS.md`, with **subdirectory files taking precedence** on conflict (shared with
Cursor / Windsurf). It does **not** read `CLAUDE.md`. The legacy **Memory Bank** feature
(`.kilocode/rules/memory-bank/`) is **deprecated** and being migrated into `AGENTS.md`. Custom Rules in
`.kilo/rules/` (and legacy `.kilocode/rules/`) supplement the instruction layer.
Source: https://kilo.ai/docs/customize/agents-md

---

## 3. Agents Support — ✅ NATIVE

- **Custom Subagents**: run in their own **isolated sessions** with separate conversation history, each
  with custom prompts and tool access tailored to a task. Defined in `kilo.jsonc` (`agent` section), or
  as markdown in `.kilo/agents/` (project) / `~/.config/kilo/agents/` (global), or via
  `kilo agent create`.
- Invoked **automatically via the Task tool** (description matching) or **manually with `@agent-name`**.
- Per-agent config: `model` (provider/model-id), `prompt`, `permissions` (allow/ask/deny),
  `temperature`/`top_p`, `mode` (subagent/primary/all). Separately, **Custom Modes** (a.k.a. agents)
  tailor behavior per task (e.g. Documentation Writer, Test Engineer, read-only Review Mode).
- **Orchestrator Mode is deprecated** — full-tool agents (Code, Plan, Debug) now auto-delegate to
  subagents without a dedicated orchestrator.
- gald3r `g-agnt-*` definitions map directly to Kilo subagent files / `kilo.jsonc` agent entries.
- Source: https://kilo.ai/docs/customize/custom-subagents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`agentskills.io` `SKILL.md` open standard): a skill is a folder containing a
  `SKILL.md` (YAML frontmatter + Markdown; required `name` ≤64 chars, `description` ≤1024 chars).
  Stored at `.kilo/skills/` (project), `~/.kilo/skills/` (global), with **compatibility directories
  `.claude/skills/` (Claude Code) and `.agents/skills/` (open standard, loaded by default)**. Extra
  paths via `kilo.jsonc` `skills.paths` / `skills.urls`.
- Metadata is scanned at session start; the full `SKILL.md` is loaded on description match
  (progressive disclosure).
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/`.
- Source: https://kilo.ai/docs/customize/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Workflows / Slash Commands**: Markdown files stored as slash commands in `.kilo/commands/`
  (project: `[project]/.kilo/commands/`, global: `~/.config/kilo/commands/`). A file at
  `.kilo/commands/submit-pr.md` is invoked with `/submit-pr` (filename without `.md`).
- The rebuilt extension **auto-migrates** legacy `.kilocode/workflows/` to the new command format.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://kilo.ai/docs/customize/workflows

## 6. Hooks System — ❌ NOT SUPPORTED

- Kilo does **not** expose session lifecycle / event hooks. **GitHub Issue #5827** (opened 2026-02-12,
  status **OPEN**, no branches/PRs) requests exposing session lifecycle hooks for third-party tool
  integration (similar to OpenCode); the author notes "Kilo does not expose session lifecycle events to
  external tools."
- The only related capability is **`kilo export [sessionID]`** for **post-hoc** data export — not
  real-time event hooks. No `PreToolUse` / `SessionStart` / pre-commit script-hook system is documented.
- **gald3r impact**: `g-hk-*.ps1` hooks have **no native surface** here. SessionStart context injection,
  PreToolUse `.gald3r/` guards, and pre-commit gates must run **out-of-band** (native git hooks via
  `core.hooksPath`, or CI). Degrade these automations to manual/scripted invocation.
- Source: https://github.com/Kilo-Org/kilocode/issues/5827

## 7. Rules / Memory — ✅ NATIVE

- **Custom Rules** "provide a powerful way to define project-specific and global behaviors and
  constraints for the Kilo Code AI agent." Rules live in `.kilo/rules/*.md` (project) and
  `~/.config/kilo/kilo.jsonc` (global), are **loaded automatically every interaction** (global first,
  then project precedence). Legacy `.kilocode/rules/` remains backward compatible.
- The separate **Memory Bank** feature is **deprecated** in favor of `AGENTS.md`.
- gald3r `g-rl-*` map to `.kilo/rules/*.md` (always-on) and/or `AGENTS.md` blocks. Per-rule `globs:`
  path-scoping is not documented — approximate with rule-body scoping or subdirectory `AGENTS.md`.
- Source: https://kilo.ai/docs/customize/custom-rules

## 8. MCP Support — ✅ NATIVE

- Full **MCP (Model Context Protocol)** support. Servers are added under the **`mcp`** key in
  `kilo.jsonc`; each has a unique name and can be disabled via `enabled: false`. Two transports:
  **Local STDIO** (Kilo spawns the server as a child process) and **Remote HTTP/SSE** (tries
  StreamableHTTP first, falls back to SSE).
- MCP tools share the built-in **permission system** (allow/ask/deny) keyed by namespaced
  `{server}_{tool}`. Works in **both** the extension and the CLI.
- Source: https://kilo.ai/docs/automate/mcp/overview

## 9. Marketplace / Distribution — distribution channel

- The **Kilo Marketplace** (github.com/Kilo-Org/kilo-marketplace) curates **Skills, MCP Servers, and
  Modes** for the Kilo ecosystem. This is the natural publishing channel for a gald3r Kilo skill/MCP
  bundle.
- No native hooks means there is **no plugin bundle that ships hooks** — gald3r distribution covers
  skills + MCP + modes/agents + rules, with hooks handled out-of-band.

---

## Parity vs. Cursor Reference

Kilo reaches **strong-but-not-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, and MCP**. The **single material gap** is **script/lifecycle hooks**
(no `SessionStart` / `PreToolUse` / pre-commit) — Issue #5827 tracks the request but it is unimplemented
with no branches/PRs. Permission model (allow/ask/deny, per-tool, namespaced MCP keys) maps cleanly to
gald3r's verify-ladder / restricted-mode patterns.

**Reuse note (important):** because Kilo reads `AGENTS.md` and discovers `.claude/skills/` +
`.agents/skills/` trees, gald3r's **Claude-Code / open-standard skill artifacts are largely reusable on
Kilo without a separate port** — ship the gald3r `SKILL.md` tree + `AGENTS.md`, then degrade only the
hook layer.

## Hook System

- **Type**: ❌ none (no session lifecycle / event hooks exposed)
- **Config file**: n/a (no hook config surface)
- **Events available**: none (Issue #5827 OPEN — `SessionStart`/`PreToolUse`/`Stop`/etc. requested, not
  implemented)
- **Event payload format**: n/a
- **Command extensions**: n/a — only post-hoc `kilo export [sessionID]` (not real-time)
- **gald3r hook files**: `g-hk-*.ps1` do **not** wire natively; run via native git hooks
  (`core.hooksPath`) or CI instead

## Atypical Handling

- **`AGENTS.md`, not `CLAUDE.md`** — gald3r's `CLAUDE.md` is ignored; use `AGENTS.md` (root + subdir
  cascade, subdir wins).
- **Config convention**: `kilo.jsonc` (JSONC) is the central config; `.kilo/` replaces legacy
  `.kilocode/` with automatic migration + backward compatibility. Built on the **OpenCode v7** codebase.
- **Deprecations to respect**: Memory Bank → fold into `AGENTS.md`; Orchestrator Mode → auto-delegating
  full-tool agents.
- **No hooks** — the one place Kilo diverges from a high-parity platform; do not assume a hook surface.

## gald3r Integration Notes

- Ship gald3r's `SKILL.md` tree via `.claude/skills/` or `.agents/skills/` — Kilo discovers both; or use
  `.kilo/skills/`.
- Map `g-rl-*` to `.kilo/rules/*.md` (always-on) + `AGENTS.md`; map `g-agnt-*` to `.kilo/agents/` or
  `kilo.jsonc` agent entries; map `@g-*` commands to `.kilo/commands/*.md`.
- **Hooks: degrade to out-of-band** — wire `g-hk-*.ps1` through native git hooks / CI; do not expect
  `SessionStart`/`PreToolUse`.
- Publish via the **Kilo Marketplace** (Skills / MCP Servers / Modes).
- Re-verify on the next `@g-platform-scan-docs kilo-code` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://kilo.ai/docs/)

| Capability | How verified |
|---|---|
| Commands | /customize/workflows — Markdown slash commands in `.kilo/commands/` (global `~/.config/kilo/commands/`); `/submit-pr`; legacy `.kilocode/workflows/` auto-migrated |
| Rules | /customize/custom-rules — `.kilo/rules/*.md` + `~/.config/kilo/kilo.jsonc`; loaded every interaction (global→project); `.kilocode/rules/` backward compatible; Memory Bank deprecated → AGENTS.md |
| Agents | /customize/custom-subagents — isolated-session subagents in `kilo.jsonc`/`.kilo/agents/`; `@agent-name` or Task-tool auto-delegation; allow/ask/deny perms; Orchestrator Mode deprecated |
| Skills | /customize/skills — agentskills.io `SKILL.md` in `.kilo/skills/`, `~/.kilo/skills/`, `.claude/skills/`, `.agents/skills/`; metadata scanned at start, loaded on match |
| Hooks | github.com/Kilo-Org/kilocode/issues/5827 — OPEN, no PRs; lifecycle hooks NOT exposed; only post-hoc `kilo export [sessionID]`; **❌ not supported** |
| MCP | /automate/mcp/overview — `mcp` key in `kilo.jsonc`; STDIO + HTTP/SSE (StreamableHTTP→SSE fallback); namespaced `{server}_{tool}` perms; extension + CLI |
| Instruction file | /customize/agents-md — reads `AGENTS.md` (uppercase, root + subdir cascade, subdir precedence); does NOT read `CLAUDE.md` |
| Cross-compat | Kilo discovers `.claude/skills/` + `.agents/skills/` and reads `AGENTS.md` → gald3r skill + instruction artifacts reusable (hooks excepted) |
