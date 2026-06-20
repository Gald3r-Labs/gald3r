---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: kiro
authoring_path: update
docs_url: https://kiro.dev/docs
docs_url_secondary:
  - https://kiro.dev/docs/cli/chat/manage-prompts/
  - https://kiro.dev/docs/chat/slash-commands/
  - https://kiro.dev/docs/steering/
  - https://kiro.dev/docs/chat/subagents/
  - https://kiro.dev/docs/skills/
  - https://kiro.dev/docs/hooks/
  - https://kiro.dev/docs/mcp/
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Kiro (Amazon)

Kiro ships in **two product lines**: an **agentic IDE** (VS Code-based) and the **Kiro CLI** (the
rebrand of Amazon Q Developer CLI). As of mid-2026 (Kiro 0.9) Kiro natively supports **all six**
gald3r-relevant extension primitives — slash commands + local prompts, steering rules, custom
subagents, **Agent Skills**, agent hooks, and MCP — with config under **`.kiro/`** (workspace) and
**`~/.kiro/`** (global). Critically for gald3r, Kiro's skills follow the **same open Agent Skills
standard** (`agentskills.io`, `SKILL.md` + `scripts/`/`references/`/`assets/`) that gald3r already
uses, so gald3r skill packages drop straight into `.kiro/skills/`. Kiro also **natively reads the
`AGENTS.md` standard** (always-included) alongside its own Steering files.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://kiro.dev/docs (see Verification
Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which incorrectly marked
skills/agents as unsupported and commands as partial — they are now all **NATIVE** in Kiro 0.9.

> **Surface split:** extension mechanisms are largely shared between the IDE and the CLI, but two
> diverge by surface. **Agents**: IDE uses markdown + YAML front matter (`.kiro/agents/*.md`); the
> CLI uses JSON config files. **Hooks**: the IDE hook engine is **file/event-trigger** driven (file
> save/create/delete, prompt submit, before/after tool, before/after spec task, manual); the CLI
> exposes classic **lifecycle hooks** (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/
> `Stop`). Where a feature is IDE- or CLI-specific it is noted inline.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                      ← instruction file Kiro reads (always-included, agents standard)
└── .kiro/
    ├── steering/    *.md          ← persistent rules/context (product.md, tech.md, structure.md + custom)
    │                                 inclusion modes: Always | Conditional/fileMatch | Manual | Auto
    ├── prompts/     *.md          ← user-defined local prompts (invoked @name)
    ├── agents/      *.md          ← custom subagents (IDE: markdown + YAML front matter)
    ├── skills/      <name>/SKILL.md  ← Agent Skills (agentskills.io standard)
    ├── specs/       {feature}/    ← spec-driven dev unit (requirements.md / design.md / tasks.md)
    ├── hooks                      ← IDE Agent Hooks (file-event triggers; authored via hook UI / config)
    └── settings/
        └── mcp.json              ← MCP server config (workspace)

~/.kiro/                          ← GLOBAL (user-wide) tree
├── steering/   *.md              ← global steering (all workspaces)
├── agents/     *.md              ← global subagents
├── skills/     <name>/SKILL.md   ← global Agent Skills
└── settings/
    └── mcp.json                  ← global MCP config (merged; workspace takes precedence)
```

CLI custom agents are **JSON** config files (not `.md`) and CLI lifecycle hooks are configured in
the **agent config file**, not a separate `hooks/` dir.

**gald3r writes**: `.kiro/skills/<name>/SKILL.md` (drop-in — same standard), `.kiro/steering/*.md`
(rules/context), `.kiro/agents/*.md` (subagents), `.kiro/prompts/*.md` (commands), `.kiro/hooks`
(IDE) / agent-config lifecycle hooks (CLI), `.kiro/settings/mcp.json` (MCP).
**Kiro owns**: the `.kiro/` namespace, the steering auto-injection engine, the spec workflow, the
hook trigger engine, and the MCP connection lifecycle.

---

## 2. AI Instruction File

Kiro **natively supports the `AGENTS.md` standard** — placed in the workspace root (or
`~/.kiro/steering/`), it is treated as markdown and is **always included** (note: `AGENTS.md` files
do **not** support steering inclusion modes — they are always on). Kiro's own native instruction
convention is **Steering files** under `.kiro/steering/` (`product.md`, `tech.md`, `structure.md`
+ custom). Kiro does **not** read `CLAUDE.md` or `GEMINI.md`. gald3r therefore ships `AGENTS.md`
(first-class) and/or a `.kiro/steering/gald3r.md` file — no `KIRO.md` root file is required.

---

## 3. Agents Support — ✅ NATIVE

- **Custom subagents**. **IDE**: define a markdown (`.md`) file with YAML front matter in
  `~/.kiro/agents` (global) or `<workspace>/.kiro/agents`. **CLI**: custom agents are JSON config
  files. Two built-in subagents ship (context-gathering + general-purpose). Subagents run in
  **parallel**, each with its **own context window** (main agent context is not polluted), and also
  appear as **slash commands** (e.g. `/code-reviewer find performance issues in my code`).
- gald3r `g-agnt-*` definitions map directly to Kiro subagent files (IDE md+YAML; CLI JSON).
- Source: https://kiro.dev/docs/chat/subagents/ ; https://kiro.dev/docs/cli/custom-agents/creating/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** following the **open Agent Skills standard** (`agentskills.io`): `SKILL.md`
  (required) plus optional `scripts/`, `references/`, `assets/` dirs. Stored in `.kiro/skills/`
  (workspace) or `~/.kiro/skills/` (global). **Progressive disclosure** — name+description loaded at
  startup, full instructions on demand. Invoked automatically or as a `/skill-name` slash command.
  Portable/importable across compatible tools. **Added in Kiro 0.9.**
- gald3r `g-skl-*/SKILL.md` load **natively and directly** — Kiro uses the **same standard**, so
  gald3r skill packages are **directly portable** into `.kiro/skills/` with no per-platform port.
- Source: https://kiro.dev/docs/skills/ ; https://kiro.dev/docs/cli/skills/

## 5. Commands / Workflows — ✅ NATIVE

- **Slash commands + user-defined local prompts**. Prompts: `/prompts create --name <name>
  [--content <content>]` creates project-specific prompts saved to `.kiro/prompts/` in the current
  workspace, invoked via the `@` prefix (e.g. `@code-review`). The `/` slash surface also unifies
  **hooks, steering files, skills, and subagents** on demand (type `/` in chat to list).
- gald3r `@g-*` / `/g-*` commands map to `.kiro/prompts/*.md` (and skills/subagents auto-register as
  slash commands too).
- Source: https://kiro.dev/docs/cli/chat/manage-prompts/ ; https://kiro.dev/docs/chat/slash-commands/

## 6. Hooks System — ✅ NATIVE

- **Agent Hooks**. **IDE** hooks trigger on **file save/create/delete**, **prompt submission**,
  **agent turn completion**, **before/after tool invocation**, **before/after spec task execution**,
  and **manual** triggers; the action is either **"Ask Kiro"** (agent prompt) or **"Run Command"**
  (shell command). **CLI lifecycle hooks**: `agentSpawn`, `userPromptSubmit`, `preToolUse`,
  `postToolUse`, `Stop` — configured in the agent config file, receive event JSON via **STDIN**,
  control flow via **exit codes** (`0` ok, `2` blocks `PreToolUse`).
- gald3r mapping: the **CLI** lifecycle events (`agentSpawn` ≈ session start, `userPromptSubmit`,
  `preToolUse`/`postToolUse`, `Stop`) line up closely with gald3r's `g-hk-*` lifecycle hooks; the
  **IDE** file-event triggers are a different (file/save-centric) model and map only where a
  `fileEdited`-style trigger fits.
- Source: https://kiro.dev/docs/hooks/ ; https://kiro.dev/docs/cli/hooks/

## 7. Rules / Memory — ✅ NATIVE

- **Steering** — persistent markdown rule/context files in `.kiro/steering/` (workspace) and
  `~/.kiro/steering/` (global), with **four inclusion modes**: **Always** (default),
  **Conditional/`fileMatch`**, **Manual** (`#file-ref`), **Auto** (description-matched). Default
  foundation files: `product.md`, `tech.md`, `structure.md`. The `AGENTS.md` standard is also read
  (always-included; no inclusion modes).
- gald3r `g-rl-*` map to steering `.md` files. Note Kiro's `.md` (no Cursor `.mdc`) — parity sync
  swaps the extension. gald3r's `alwaysApply: true` rules → **Always** mode; `description:`-scoped
  rules → **Auto** / **Conditional** (`fileMatch`) mode. This is **richer** than the prior spec's
  "no per-rule scoping" claim — Kiro *does* support conditional/auto/manual inclusion.
- Source: https://kiro.dev/docs/steering/ ; https://kiro.dev/docs/cli/steering/

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol** servers. Config in `.kiro/settings/mcp.json` (workspace) and
  `~/.kiro/settings/mcp.json` (global), **merged with workspace precedence**. Standard `mcpServers`
  object (`command`, `args`, `env`, `disabled`, `autoApprove`). Per-agent access via the
  `mcpServers` field; subagents can **scope tools with wildcards** like `@figma/*`. MCP servers can
  also expose reusable prompts.
- Transport (stdio/SSE/HTTP) was **not specified** on the config page reviewed — ❓ confirm on the
  next crawl.
- Source: https://kiro.dev/docs/mcp/ ; https://kiro.dev/docs/mcp/configuration/

## 9. Specs — Kiro's flagship workflow (adoptable seam)

- **Spec-driven development**: `requirements.md`, `design.md`, `tasks.md` generated and tracked per
  feature under `.kiro/specs/`; hooks can fire **before/after spec task execution**. This is a
  strong adoptable surface for gald3r task/PRD parity. Spec/PRD mapping (Kiro specs ↔ gald3r PRDs)
  is the natural integration seam: `requirements.md` → PRD acceptance criteria, `design.md` → PRD
  technical design, `tasks.md` ↔ gald3r task breakdown.
- Source: https://kiro.dev/docs/specs/

---

## Parity vs. Cursor Reference

Kiro now reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Caveats: agents and hooks diverge by surface
(IDE md+YAML / file-event hooks vs CLI JSON / lifecycle hooks); MCP transport types and steering
size limits were not documented on the pages crawled (❓). The **spec-driven workflow** is a
Kiro-native bonus with no Cursor analog and the best gald3r integration seam.

**Reuse note (important):** because Kiro skills follow the **identical open Agent Skills standard**
gald3r uses, gald3r `g-skl-*/SKILL.md` packages are **directly portable** into `.kiro/skills/` — the
cheapest high-parity install ships the gald3r skill tree plus `AGENTS.md` (always-read) and a
`.kiro/steering/gald3r.md` context file.

## Hook System

- **Type**: native (IDE Agent Hooks — file/event triggers; CLI lifecycle hooks)
- **Config file**: IDE — `.kiro/hooks` (authored via hook UI / config); CLI — the agent config file
- **Events available**:
  - **IDE**: file save / create / delete, prompt submission, agent turn completion, before/after
    tool invocation, before/after spec task execution, manual trigger
  - **CLI**: `agentSpawn`, `userPromptSubmit`, `preToolUse`, `postToolUse`, `Stop`
- **Event payload format**: CLI — event JSON via **STDIN**; flow control via **exit codes**
  (`0` ok, `2` blocks `PreToolUse`). IDE — action is **"Ask Kiro"** (agent prompt) or
  **"Run Command"** (shell command).
- **Command extensions**: shell `Run Command` (IDE) / shell command (CLI). PowerShell `.ps1` can be
  invoked as the shell command; a `g-hk-*.ps1` shim wires under the CLI lifecycle events.
- **gald3r hook files**: gald3r `g-hk-*.ps1` map most cleanly to the **CLI** lifecycle events
  (`agentSpawn` ≈ session start, `userPromptSubmit`, `preToolUse`/`postToolUse`, `Stop`). The IDE
  file-event model fits file-save-style hooks only.

## Atypical Handling

- Two surfaces: the **IDE** (file-event hooks, md+YAML agents) and the **CLI** (lifecycle hooks,
  JSON agents). Skills, steering, prompts, and MCP are shared.
- Steering files live under `.kiro/steering/` with four inclusion modes (Always/Conditional/Manual/
  Auto) — richer than a flat rules folder.
- `AGENTS.md` is the read instruction file (always-included); Kiro does **not** read `CLAUDE.md`.
- Specs (`requirements.md`/`design.md`/`tasks.md`) are a first-class workflow, not a gald3r artifact.

## gald3r Integration Notes

- Ship gald3r's `g-skl-*/SKILL.md` tree straight into `.kiro/skills/` — same open standard, no port.
- Wire gald3r lifecycle hooks to the **CLI** events (`agentSpawn`/`userPromptSubmit`/`preToolUse`/
  `postToolUse`/`Stop`); use the IDE hook engine only for file-save-style automation.
- Map gald3r rules to steering inclusion modes (Always for `alwaysApply: true`; Auto/Conditional for
  `description:`-scoped). Use `AGENTS.md` for top-level instructions.
- Re-verify on the next `@g-platform-scan-docs kiro` (crawl_max_age_days: 7) — confirm MCP transport
  types and any steering size limit.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ✅**: native — IDE file-event Agent Hooks + CLI lifecycle hooks (`agentSpawn`/
  `userPromptSubmit`/`preToolUse`/`postToolUse`/`Stop`); model differs by surface.
- **Rules ✅**: native Steering (`.kiro/steering/*.md`) with four inclusion modes + `AGENTS.md`.
- **Skills ✅**: native Agent Skills (agentskills.io `SKILL.md`) — same standard gald3r uses (Kiro 0.9).
- **Commands ✅**: native slash commands + local prompts (`.kiro/prompts/`, `@name`); skills/subagents
  auto-register as slash commands.
- **MCP ✅**: native — `.kiro/settings/mcp.json` (+ global, workspace precedence); per-agent scoping.
- **Docs Fresh ✅**: crawled 2026-06-02 against kiro.dev/docs.

---

## Verification Evidence (docs crawl 2026-06-02, https://kiro.dev/docs)

| Capability | How verified |
|---|---|
| Commands | /cli/chat/manage-prompts/ + /chat/slash-commands/ — `/prompts create` saves to `.kiro/prompts/`, invoked `@name`; `/` lists hooks+steering+skills+subagents |
| Rules | /steering/ + /cli/steering/ — `.kiro/steering/*.md` (product/tech/structure + custom); inclusion modes Always/Conditional(`fileMatch`)/Manual(`#file-ref`)/Auto; `AGENTS.md` always-included |
| Agents | /chat/subagents/ + /cli/custom-agents/creating/ — IDE md+YAML in `~/.kiro/agents` or `<ws>/.kiro/agents`; CLI JSON; parallel, own context window; appear as slash commands |
| Skills | /skills/ + /cli/skills/ — agentskills.io `SKILL.md`(+scripts/references/assets) in `.kiro/skills/`; progressive disclosure; importable; added Kiro 0.9 |
| Hooks | /hooks/ + /cli/hooks/ — IDE: file save/create/delete, prompt submit, agent-turn complete, before/after tool, before/after spec task, manual (Ask Kiro / Run Command); CLI: agentSpawn/userPromptSubmit/preToolUse/postToolUse/Stop via STDIN, exit codes (2 blocks PreToolUse) |
| MCP | /mcp/ + /mcp/configuration/ — `.kiro/settings/mcp.json` (+ `~/.kiro/...`), merged workspace-precedence; `mcpServers` field; subagent wildcard scoping (`@figma/*`); transport types ❓ |
| Specs | /specs/ — `requirements.md`/`design.md`/`tasks.md` per feature under `.kiro/specs/`; hooks fire before/after spec task execution |
| Instruction file | Kiro reads `AGENTS.md` (always-included, no inclusion modes) + Steering; no `CLAUDE.md`/`GEMINI.md` |
| Recency | Subagents (IDE), Agent Skills, new hook triggers shipped in **Kiro 0.9** (changelog /changelog/ide/0-9/); Skills doc last updated 2026-02-18; all six mechanisms current as of June 2026 |
