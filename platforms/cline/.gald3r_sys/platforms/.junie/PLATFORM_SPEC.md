---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: junie
authoring_path: update
docs_url: https://junie.jetbrains.com/docs
docs_url_secondary:
  - https://junie.jetbrains.com/docs/guidelines-and-memory.html
  - https://www.jetbrains.com/help/junie/model-context-protocol-mcp.html
  - https://junie.jetbrains.com/docs/junie-plugin-mcp-settings.html
  - https://junie.jetbrains.com/docs/action-allowlist.html
crawl_max_age_days: 14
vault_doc_path: research/platforms/junie/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1476
---

# PLATFORM_SPEC — junie (JetBrains Junie)

Authoring path: **UPDATE** existing `g-skl-platform-junie/SKILL.md`.

**JetBrains Junie** is JetBrains' agentic AI coding assistant. It runs as a **plugin inside the
IntelliJ platform** (IntelliJ IDEA, PyCharm, WebStorm, GoLand, RubyMine, Rider, etc.) and also has
a **terminal/CLI mode**. Unlike Cursor or Cline it is **not** a VS Code fork: it is hosted by the
JetBrains IDE and uses the IDE's code-intelligence (PSI) index for context. It requires a JetBrains
AI subscription.

Junie's persistent project context is delivered through **guidelines** (the AGENTS.md / `.junie/`
mechanism), and it has **first-class MCP support** via `.junie/mcp/mcp.json`. Beyond those two,
Junie has **no Cursor-style primitives**: no `.mdc` rules folder, no `SKILL.md` skill-discovery, no
agent-definition files, no slash-command framework, and **no lifecycle-hook system**. Approval
governance is handled by an **Action Allowlist** (which commands/tools Junie may run without
confirmation) — that is a safety gate, **not** a hook bus and cannot run gald3r `.ps1` hooks.

This spec corrects the prior SKILL.md, which named only `.junie/guidelines.md`. Current Junie
prefers **`.junie/AGENTS.md`** (or root `AGENTS.md`); `.junie/guidelines.md` / `.junie/guidelines/`
is the **legacy** format and is still supported. The many honest `❌` marks below are the correct,
factual assessment of an IDE-hosted agent with a narrow extension surface — not an implementation
failure.

---

## 1. Folder Hierarchy

Junie is **not** broadly folder-namespaced the way Cursor is (no `.junie/rules/`, `.junie/skills/`,
`.junie/agents/`, `.junie/commands/`, or `.junie/hooks/`). The `.junie/` directory holds guidelines
and MCP config only:

```
<project-root>/
├── .junie/
│   ├── AGENTS.md             ← preferred guidelines file (auto-injected) — gald3r writes
│   ├── guidelines.md         ← LEGACY guidelines (still supported); folder form .junie/guidelines/ also legacy
│   └── mcp/
│       └── mcp.json          ← project-level MCP server config (commit & share) — gald3r may write
├── AGENTS.md                 ← root AGENTS.md is also honored (search-order fallback)
└── …                         ← project source (Junie uses IDE PSI index for context)

(IDE / user scope, platform-owned)
~/.junie/                     ← user-level / global config, including global MCP — Junie-owned
IDE settings                  ← custom guidelines path, Action Allowlist, subscription — Junie-owned
```

- **gald3r writes**: `.junie/AGENTS.md` (preferred) and/or `.junie/guidelines.md` (legacy
  compatibility), and optionally `.junie/mcp/mcp.json`.
- **Junie owns**: the guidelines search-order, PSI/index mechanism, Action Allowlist storage, the
  IDE-settings custom-path, and user-scope `~/.junie/`.
- There is **no** rules/skills/agents/commands/hooks directory tree under `.junie/`. Every gald3r
  primitive that relies on those directories has no native home here.

## 2. AI Instruction File

- **Primary instruction surface: guidelines.** Junie searches, in order:
  1. a **custom path** configured in IDE settings (if set),
  2. **`.junie/AGENTS.md`** — the preferred/standard location,
  3. **`AGENTS.md`** in the project root,
  4. **legacy** `.junie/guidelines.md` (or the `.junie/guidelines/` folder).
- The file is plain markdown (open `AGENTS.md` format) and Junie **adds its content to every
  task's prompt context** — this is the always-apply / persistent-memory analogue.
- gald3r **generates** the guidelines content. For maximum compatibility gald3r should write
  **`.junie/AGENTS.md`** as the canonical surface and may also keep `.junie/guidelines.md` for
  older Junie builds. Junie does **not** natively read `CLAUDE.md` or `GEMINI.md`; it does honor
  root `AGENTS.md`.

## 3. Agents Support

- **No native agent-definition concept. ❌** Junie has no `g-agnt-*.md` discovery, no agent-mode
  roster loaded from files, and no multi-agent orchestration. It is a single agentic assistant
  ("Junie") that runs multi-step tasks inside the IDE.
- gald3r's agent roster (task-manager, planner, qa-engineer, code-reviewer, …) cannot be selected
  as discrete, file-defined agents. Their *behaviors* can only be approximated by describing the
  roles inside the guidelines file (`.junie/AGENTS.md`).

## 4. Skills Support

- **No skill discovery / loading / invocation. ❌** Junie has no `SKILL.md` mechanism, no
  folder-per-skill scan, and no "load skill when relevant" model-driven activation.
- gald3r skills (`g-skl-*`) have no runtime home on Junie. A skill's instructions only reach Junie
  if folded into the guidelines file, which does not scale to the full skill set.
- This is a hard gap, not a config oversight. (Junie's extensibility goes through MCP tools, not a
  skill registry — see §8.)

## 5. Commands / Workflows

- **No custom slash-command framework. ❌/⚠️** Junie has no `commands/` folder and no way to
  register `@g-*` / `/g-*` palette commands. Interaction is conversational (chat panel in the IDE,
  or prompts in the terminal/CLI mode).
- The closest "do something repeatable" primitives are **MCP tools** (executable functionality
  exposed by configured MCP servers, see §8) and the IDE's own run configurations, which Junie can
  trigger. gald3r workflows cannot be installed as Junie commands; they must be driven via the
  guidelines + MCP tools + conversational prompts.

## 6. Hooks System

- **No hook / lifecycle-event system. ❌** Junie exposes no `sessionStart`, `stop`, `preToolUse`,
  `postToolUse`, or `beforeShellExecution` events, and no `hooks.json` / settings hook table.
- Consequence for gald3r: the PowerShell session-start / inbox-check / pre-commit hooks that
  auto-fire on Cursor and Claude Code **do not fire on Junie**. There is no wiring point.
- Junie's **Action Allowlist** governs *which* commands/MCP tools Junie may run **without user
  confirmation**. It is an approval/safety gate, **not** a hook bus — it cannot invoke gald3r `.ps1`
  lifecycle hooks. The only way to run a gald3r hook script is for the user (or Junie, if the
  command is allowlisted) to invoke it as a shell command.

## 7. Rules / Memory

- **No native rules directory. ❌** No `.junie/rules/`, no `.md`/`.mdc` rule-file discovery, no
  `alwaysApply`/`globs` frontmatter mechanism.
- Persistent "always-apply" guidance lives in the **guidelines file** (`.junie/AGENTS.md`, with
  legacy `.junie/guidelines.md`), which Junie injects into every task. That is Junie's only
  persistent-rules / memory analogue (⚠️ partial parity, single-file rather than a glob-scoped
  rule set).
- Junie also maintains task/session **memory** within the IDE; the file-backed, version-controllable
  surface gald3r can author is the guidelines file.

## 8. MCP Support

- **Natively supported. ✅ (mechanism)** Junie connects to **Model Context Protocol** servers to
  expose executable functionality (filesystem, tools, databases, etc.).
- **Config format/location**: `.junie/mcp/mcp.json` at the project root (commit & share across the
  team), and a global/user-scope config (`~/.junie/` / IDE settings) for personal servers. There is
  also an in-IDE **MCP Settings** panel.
- **Action Allowlist interaction**: adding an MCP-rule allowlist item authorizes Junie to run MCP
  tools without per-call confirmation. (Note: as documented, you cannot yet scope the allowlist to
  *specific* MCP servers/tools — it is an all-MCP grant.)
- gald3r marks MCP **✅ for the mechanism**; the concrete server set is machine/team-specific
  (no `mcp.json` is committed in this template), so end-to-end server behavior is ❓ untested in CI.

## 9. Known Gaps vs. Cursor Reference

Per the decision tree in `g-skl-platform-cursor/SKILL.md` — a capability either (a) lives in common
`.gald3r_sys/`, (b) needs platform-specific config in `.gald3r_sys/platforms/.junie/`, or (c) is a
documented gap:

| Cursor-reference capability | Junie status | Disposition |
|---|---|---|
| `.cursor/rules/*.mdc` always-apply rules | ❌ no rules dir | (c) gap → folded into `.junie/AGENTS.md` guidelines |
| `agents/g-agnt-*.md` file discovery | ❌ no agent concept | (c) hard gap → single assistant; roles described in guidelines |
| `skills/g-skl-*/SKILL.md` discovery + auto-load | ❌ no skill mechanism | (c) hard gap → no runtime home; extend via MCP instead |
| `commands/` slash-command palette (`@g-*`) | ❌ no custom command framework | (c) gap → conversational + MCP tools |
| Lifecycle hooks (`hooks.json`, sessionStart, …) | ❌ none | (c) hard gap → Action Allowlist is approval gating, not a hook bus |
| MCP servers | ✅ native (`.junie/mcp/mcp.json`) | (a)/(b) strong fit — project-level, commit-shareable MCP config |
| Persistent guidelines / memory | ⚠️ single guidelines file (`.junie/AGENTS.md`) | (a)/(b) the other strong fit — always injected into every task |
| IDE PSI context / run configurations | ✅ native (IDE-hosted) | platform-native; not a gald3r-authored surface |

**Strong fits: MCP (`.junie/mcp/mcp.json`) and persistent guidelines (`.junie/AGENTS.md`).**
**Hard gaps (not achievable on Junie today): a rules folder, file-defined agents, skill discovery,
an extensible command framework, and lifecycle hooks.**

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ❌ | ✅ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no lifecycle-event system, no `hooks.json`; the Action Allowlist is approval
  gating, not a hook bus, and cannot run gald3r `.ps1` hooks.
- **Rules ⚠️** — no rules folder, BUT always-apply enforcement IS deliverable via `.junie/AGENTS.md`
  guidelines (legacy `.junie/guidelines.md`), injected into every task (single-file partial parity).
- **Skills ❌** — no `SKILL.md` discovery/loading/invocation; extensibility is via MCP tools, not skills.
- **Commands ❌** — no custom slash-command framework; conversational + MCP tools only.
- **MCP ✅** — native, project-level `.junie/mcp/mcp.json` (commit-shareable) + global config + IDE
  MCP Settings panel; concrete server set is per-machine (❓ in CI).
- **Docs Fresh ❌** — `last_doc_scan: never`; `@g-platform-scan-docs junie` not yet run.

---

## Verification Evidence

| Capability | How verified | Confidence |
|---|---|---|
| Guidelines search order: custom path → `.junie/AGENTS.md` → root `AGENTS.md` → legacy `.junie/guidelines.md` / `.junie/guidelines/` | JetBrains Junie "Guidelines and memory" docs + Junie CLI guidelines doc (WebSearch 2026-05-26) | High |
| Guidelines auto-injected into every task | JetBrains Junie docs; existing SKILL.md (WebSearch) | High |
| MCP native via `.junie/mcp/mcp.json` (project) + global config + MCP Settings panel | JetBrains Junie MCP docs (`model-context-protocol-mcp.html`, `junie-plugin-mcp-settings.html`, `junie-cli-mcp-configuration.html`) (WebSearch) | High |
| Action Allowlist is approval gating (incl. all-MCP grant), not a hook bus | JetBrains Junie "Action Allowlist" doc (WebSearch) | High |
| No rules folder / no file-defined agents / no skill discovery / no custom command framework / no lifecycle hooks | Absence of any such mechanism in Junie docs; Junie is an IDE-hosted single agent extended via MCP | High (negative finding) |
| JetBrains IDE plugin + terminal/CLI mode; uses PSI index; requires JetBrains AI subscription | JetBrains Junie IDE-plugin & CLI usage docs; existing SKILL.md §1/§5 (WebSearch) | High |

**No live install test was run** in this environment; findings rest on the existing gald3r SKILL.md
plus a 2026-05-26 doc scan of https://junie.jetbrains.com/docs and the JetBrains help pages. A
formal `@g-platform-scan-docs junie` crawl is required to set `last_doc_scan` and to re-confirm the
guidelines search-order and Action-Allowlist/MCP scoping on the then-current Junie release. Until
then `status: ⚠️` (MCP + guidelines work; rules are single-file partial; agents/skills/commands/hooks
are documented hard gaps).
