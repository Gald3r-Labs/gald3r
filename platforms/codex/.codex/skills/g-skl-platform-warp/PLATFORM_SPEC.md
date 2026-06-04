---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: warp
authoring_path: update
docs_url: https://docs.warp.dev
docs_url_secondary:
  - https://docs.warp.dev/agent-platform/capabilities/rules/
  - https://docs.warp.dev/agent-platform/capabilities/skills/
  - https://docs.warp.dev/agent-platform/capabilities/agent-profiles-permissions/
  - https://docs.warp.dev/agent-platform/capabilities/slash-commands
  - https://docs.warp.dev/agent-platform/capabilities/mcp/
  - https://github.com/warpdotdev/warp/issues/7834
crawl_max_age_days: 14
vault_doc_path: research/platforms/warp/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1483
---

# PLATFORM_SPEC.md — Warp (AI terminal + Oz agent platform)

Warp is an **AI-native terminal** (not an IDE) whose 2026 **Agent Platform** adds a real,
first-class extensibility surface. As of mid-2026 Warp natively supports **rules, Agent Skills
(`SKILL.md`), agents (profiles + Oz subagent orchestration), and MCP**, exposes a **partial**
command surface (built-in slash commands + Warp Drive Workflows, but **no user-defined custom
slash-command syntax**), and has **no native lifecycle-hook system**. This yields a mix of genuine
parity (rules, skills, agents, MCP) and honest gaps (hooks absent; commands partial) — the correct
factual picture for a terminal-native platform, not an implementation failure.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.warp.dev (see Verification
Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which incorrectly marked
**skills and agents as hard gaps** — both are now **NATIVE** on the Warp Agent Platform. Crucially,
Warp's Skills system discovers cross-vendor `SKILL.md` trees (`.agents/skills/`, `.warp/skills/`,
**`.claude/skills/`**, `.codex/skills/`, `.cursor/skills/`, …), so gald3r's Claude-Code skill
artifacts are **largely drop-in reusable** on Warp.

> **Surface split:** Warp's primitives live across **on-disk rules/skills files** (repo root +
> standard skill dirs), **app/Warp Drive settings** (Agent Profiles, MCP, Workflows), and the
> **Oz cloud control plane** (subagent orchestration, Cloud Triggers/Schedules). There is **no
> `.warp/` tree of every gald3r primitive** — rules live in `AGENTS.md`/`WARP.md`, agents are
> app-managed profiles, and commands/Workflows are Warp Drive (cloud) objects. Where a feature is
> cloud-managed or has a caveat it is noted inline.

---

## 1. Folder Hierarchy

Warp is **not** uniformly folder-namespaced like Cursor (`.cursor/rules|skills|agents|commands|hooks`).
It reads root-level rules files and standard skill dirs on disk, and keeps agents/commands/MCP in
app settings or the cloud (Warp Drive):

```
<project-root>/
├── AGENTS.md                ← default project rules file (vendor-neutral) — gald3r writes
├── WARP.md                  ← legacy native rules file (ALL-CAPS); wins precedence if both exist — gald3r writes
├── <subdir>/AGENTS.md       ← per-subdirectory rules (best-effort inclusion) — optional
├── .agents/skills/  <name>/SKILL.md  ← Agent Skills (SKILL.md standard) — gald3r writes
├── .warp/skills/    <name>/SKILL.md  ← Warp-native skill dir — gald3r writes (optional)
└── .claude/skills/  <name>/SKILL.md  ← also discovered (Claude-Code interop) — gald3r reuse

~/ (home equivalents)        ← ~/.agents/skills, ~/.warp/skills, ~/.claude/skills, … — global skills
~/.warp/                     ← Warp local app state (themes, launch configs) — platform-owned

(App / Cloud — not a repo-installable folder tree)
├── Agent Profiles & permissions   ← named agents (base model, autonomy, tool/MCP allow-deny) — app-managed
├── MCP servers                    ← Settings > Agents > MCP servers (CLI + HTTP/SSE) — app-managed
└── Warp Drive (CLOUD)             ← Workflows, Notebooks, Prompts, Env Vars — cloud-backed
```

- **gald3r writes**: `AGENTS.md` and/or `WARP.md` (project rules); `SKILL.md` trees under
  `.agents/skills/`, `.warp/skills/`, or reuse `.claude/skills/`.
- **Warp owns**: the rules-file recognition mechanism, the Skills discovery list, Agent Profiles,
  the MCP registry (app settings), Warp Drive cloud store, and `~/.warp/` state.
- There is **no** `.warp/rules/`, `.warp/agents/`, `.warp/commands/`, or `.warp/hooks/` folder.
  Rules → root file; agents → app profiles; commands → Warp Drive Workflows; hooks → unsupported.

## 2. AI Instruction File

Warp's project-rules convention is **`AGENTS.md`** (vendor-neutral, the recommended path), with
**`WARP.md`** as the legacy native name. The filename must be **ALL-CAPS** to be recognized. **If
both `AGENTS.md` and `WARP.md` exist in the same directory, `WARP.md` takes priority.** Warp
auto-applies the file from the **repo root and the current directory**, with best-effort inclusion
of subdirectory files.

- **Note (instruction-file convention):** unlike Augment/Claude-Code platforms that read `CLAUDE.md`,
  Warp's instruction file is **`AGENTS.md` (or `WARP.md`)** — it does **not** read `CLAUDE.md` as a
  rules file. Fold gald3r enforcement into the root `AGENTS.md`/`WARP.md`.
- **Precedence** (most specific first): subdirectory rules file → repo-root rules file → Global
  Rules (app-level, all projects). gald3r enforcement belongs in the **root `AGENTS.md`/`WARP.md`**.
- Project Rules apply **automatically** when an agent operates inside the project — no manual pin.
- Source: https://docs.warp.dev/agent-platform/capabilities/rules/

## 3. Agents Support — ✅ NATIVE

- **Agent Profiles & permissions**: users create multiple named agent profiles, each with a distinct
  **base model, autonomy level, tool/command allow-deny lists, and MCP access** — *"Set up different
  profiles for different workflows (e.g., 'Safe & cautious', 'YOLO mode', etc.)."* These are
  app-managed profiles (not on-disk `g-agnt-*.md` files).
- **Oz subagent orchestration (multi-harness)**: Oz can *"orchestrate subagents automatically,
  deploying and tracking multiple agents in parallel"* (swarm, supervisor/worker, fan-out/fan-in,
  critic/verifier patterns) and run **Claude Code and Codex subagents** alongside the default Warp
  Agent harness through one control plane with shared Agent Memory. Only the default Warp Agent
  harness can orchestrate subagents.
- gald3r's agent roster maps to Agent Profiles (behavior/permission sets) rather than discoverable
  agent files; orchestration patterns (g-go swarm) map to Oz subagent orchestration.
- Source: https://docs.warp.dev/agent-platform/capabilities/agent-profiles-permissions/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills (`SKILL.md` format)**: *"Skills allow you to create reusable, shareable instructions
  that agents can invoke when performing tasks."* Each skill is a subdirectory containing a `SKILL.md`
  with YAML frontmatter (`name`, `description`) plus markdown instructions.
- **Discovery dirs** (project-scoped and `~/` global equivalents): `.agents/skills/`, `.warp/skills/`,
  **`.claude/skills/`**, `.codex/skills/`, `.cursor/skills/`, `.gemini/skills/`, `.copilot/skills/`,
  `.factory/skills/`, `.github/skills/`, `.opencode/skills/`. **Cross-vendor `SKILL.md`
  interoperability is explicit.**
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/` — so the
  Claude-Code skill tree is reusable on Warp with no Warp-specific port.
- **Recency**: the Skills docs page was last updated **2026-05-28** (recently added capability).
- Source: https://docs.warp.dev/agent-platform/capabilities/skills/

## 5. Commands / Workflows — ⚠️ PARTIAL

- **Built-in slash commands** (static): `/agent`, `/plan`, `/skills`, `/fork`, `/model`, plus
  **Agent Prompts saved in your Warp Drive** appear in the `/` menu.
- **No user-defined custom slash-command syntax** (e.g. `/my-command`) and **no file-based custom
  command definition**. Open feature request **#6857** explicitly asks Warp to add the ability to
  *"create and upload your slash commands"* like Claude Code — confirming it is **not yet supported**.
- **Warp Drive Workflows** are the closest user-authorable primitive: parameterized, named,
  searchable commands with descriptions and arguments, scopable to a **user or a git repo**,
  accessible from the Command Palette. They **partially** cover the custom-commands gap but are
  **cloud-backed Warp Drive objects, not on-disk `commands/g-*.md`** installed from the repo.
- Net: gald3r `@g-*`/`/g-*` commands cannot be installed as native custom slash commands; they map
  to manually-authored Warp Drive Workflows or are driven by the underlying shell invocation.
- Source: https://docs.warp.dev/agent-platform/capabilities/slash-commands

## 6. Hooks System — ❌ NONE

- **No lifecycle/event hook capability in official docs.** The Agent Platform Capabilities navigation
  lists **no Hooks page**. There is no `sessionStart`/`stop`/`preToolUse`/`postToolUse`/
  `beforeShellExecution` event surface and no `hooks.json` / settings hook table for user scripts.
- The only references to agent hooks are **open GitHub feature requests**: **#7834** (*"Feature
  Request: Agent Lifecycle Hooks for Observability"*, proposing `agent_tool_use_pre` etc.) and
  **#6857** (requesting *"hook-like mechanisms"*) — both **Open with no maintainer commitment**.
- **Adjacent (not equivalent):** **Cloud Triggers & Schedules** on Oz can react to Slack/Linear/GitHub
  events or run recurring tasks — an event-automation surface, **not** a hook bus that runs local
  gald3r `.ps1` scripts on session/tool lifecycle.
- **Interop caveat:** the `warpdotdev/claude-code-warp` plugin implements hooks via **Claude Code's
  own `hooks.json`** (SessionStart/Stop/Notification) — i.e. it *consumes* Claude Code's hook system
  rather than providing a native Warp one.
- Consequence for gald3r: the PowerShell session-start / inbox-check / pre-commit `g-hk-*.ps1` hooks
  that auto-fire on Cursor and Claude Code **do not fire on Warp**. They must be run manually in the
  terminal, referenced from rules text, or wired through git `core.hooksPath` (pre-commit/pre-push).
- Source: https://github.com/warpdotdev/warp/issues/7834

## 7. Rules / Memory — ✅ NATIVE

- *"Warp's Rules feature lets you create reusable guidelines that inform how agents respond."* Two
  scopes: **Global Rules** (apply across all projects) and **Project Rules** (repo-specific, stored
  in `AGENTS.md`/`WARP.md`, auto-applied from root + current dir).
- **Agent Memory (Research Preview)**: gives agents persistent, **cross-harness** memory on Oz (Warp
  Agent, Claude Code, Codex) that agents **read from and write to across conversations** — a durable
  memory effect beyond the rules file.
- **Format note vs. Cursor**: Warp rules are plain markdown in a single root file (+ optional
  per-subdir files), **not** Cursor's `.mdc` files with `alwaysApply`/`globs:` frontmatter. There is
  no per-glob rule scoping beyond the directory the rules file sits in, so gald3r's fine-grained
  `g-rl-*` set must be **flattened into `AGENTS.md`/`WARP.md`** prose. The persistent-memory *effect*
  is achieved (rules re-apply every session automatically; Agent Memory persists facts); the *file
  model* differs.
- gald3r also keeps `.gald3r/learned-facts.md` for durable project facts, but Warp only "sees" them
  if referenced from `AGENTS.md`/`WARP.md` (or captured into Agent Memory).
- Source: https://docs.warp.dev/agent-platform/capabilities/rules/

## 8. MCP Support — ✅ NATIVE

- *"Configure MCP servers in the Warp app to extend local agents with custom tools and data sources
  through a standardized interface."* Added via **Settings > Agents > MCP servers** (or the Warp Drive
  MCP page) with two types: **CLI Server** (Command, e.g. `npx`/Docker) and **Streamable HTTP/SSE
  Server** (URL).
- **Per-profile MCP access rules** and env-var/OAuth auth are supported; MCP servers are **shared
  context across local and cloud (Oz) agents**.
- For gald3r, MCP is a clean portability path: configure the server set once in the Warp app and it is
  reused across local and Oz agents.
- ⚠️ The concrete active server set is per-machine and untested in CI; the *mechanism* is verified
  from docs, not from a live install in this environment.
- Source: https://docs.warp.dev/agent-platform/capabilities/mcp/

## 9. Other Capabilities & Distribution

- **Warp Drive** is the knowledge/collaboration store (Notebooks, Workflows, Prompts, Env Vars).
  Shared context (Warp Drive, Rules, MCP) works across both **local and cloud agents**.
- **Oz cloud agents**: the cloud agent orchestration platform. **Cloud Triggers & Schedules** can
  react to Slack/Linear/GitHub events or run recurring tasks (event automation adjacent to hooks).
- **Multi-harness**: Oz runs **Warp Agent** (default, the only harness that can orchestrate
  subagents), **Claude Code**, and **Codex** through one control plane with shared Agent Memory.
- **Agent API/SDK**: Warp exposes an Agent API/SDK (`docs.warp.dev/reference/api-and-sdk/agent`) for
  programmatic agent invocation.
- **Other Capabilities pages**: Planning, Task lists, Agent notifications, Full terminal use, Computer
  use, Codebase Context, Web search.
- **Instruction-file interop**: adopting `AGENTS.md` (vendor-neutral) is the recommended path; `WARP.md`
  is the legacy native name and **wins precedence if both are present**.

---

## Parity vs. Cursor Reference

Warp now reaches **strong parity** with the Cursor reference (`g-skl-platform-cursor`) on the surfaces
that matter: native **rules, skills, agents, and MCP**. Caveats: **commands are partial** (built-in
slash commands + cloud Warp Drive Workflows; **no user-defined custom slash commands** — open RFC
#6857), and **hooks are absent** (no lifecycle-event system; open RFCs #7834 / #6857). Rules are
single-file markdown (no `.mdc`/glob scoping); agents are app-managed profiles (no on-disk
`g-agnt-*.md`). **Oz subagent orchestration** and **cross-harness Agent Memory** are Warp-native
bonuses with no direct Cursor analog.

**Reuse note (important):** because Warp's Skills system discovers `.claude/skills/` (and `.agents/`,
`.warp/`, `.cursor/`, …) `SKILL.md` trees, gald3r's **Claude-Code skill artifacts are largely
reusable on Warp without a separate port**. Rules still require flattening into `AGENTS.md`/`WARP.md`;
agents map to Agent Profiles; commands map to manual Warp Drive Workflows; hooks have no wiring point.

## Hook System

- **Type**: none
- **Config file**: n/a (no `hooks.json`; no settings hook table for user scripts)
- **Events available**: none — no `sessionStart`/`stop`/`preToolUse`/`postToolUse`/`beforeShellExecution`. Agent **lifecycle hooks** are an OPEN feature request (warpdotdev/warp **#7834**); custom slash commands + hook-like mechanisms are OPEN RFC **#6857**. Neither is shipped.
- **Event payload format**: none
- **OS limits**: n/a — there is no native hook surface on any OS (Warp is macOS/Linux/Windows, but the gap is platform-wide, not OS-specific).
- **Limitations**: nearest event-driven concept is **Oz Cloud Triggers & Schedules** (event-triggered cloud agent runs) — an agent-execution trigger, NOT a hook bus for local `.ps1`. The `warpdotdev/claude-code-warp` plugin reuses Claude Code's own `hooks.json`, not a native Warp hook system.
- **gald3r hook files**: none auto-fire — a gald3r `g-hk-*.ps1` hook can only be run manually in the terminal, referenced from `AGENTS.md`/`WARP.md` rules text, or wired via git `core.hooksPath` (pre-commit/pre-push only).

## Atypical Handling

- Instruction file is **`AGENTS.md` (or legacy `WARP.md`)**, ALL-CAPS, `WARP.md` wins if both exist —
  Warp does **not** read `CLAUDE.md` as a rules file.
- Skills are real and **cross-vendor**: ship gald3r's `.claude/skills/` (or `.agents/skills/`) tree
  and Warp discovers it.
- Agents are **app-managed Agent Profiles** (+ Oz subagent orchestration), not on-disk agent files.
- Commands are **partial**: built-in slash commands + cloud Warp Drive Workflows; no custom slash
  commands (open RFC #6857).
- No hook bus for local scripts — agent lifecycle hooks are an explicitly open feature request
  (#7834 / #6857). Oz Cloud Triggers are platform-side event triggers, not a local hook surface.

## gald3r Integration Notes

- Ship gald3r's `.claude/skills/` (or `.agents/skills/`) `SKILL.md` tree — Warp's Skills system
  discovers it natively (no Warp-specific port).
- Flatten gald3r `g-rl-*` into the root `AGENTS.md`/`WARP.md`; Warp auto-applies it every session.
- Configure MCP once in the Warp app (Settings > Agents > MCP servers) — reused across local + Oz.
- Map agent roster → Agent Profiles; map g-go swarm orchestration → Oz subagent orchestration.
- gald3r hooks do **not** fire on Warp — run them manually, reference from rules text, or use git
  `core.hooksPath`. Track warpdotdev/warp **#7834** and **#6857**; if lifecycle/agent hooks ship,
  re-verify the Hooks section before changing it from ❌.
- Re-verify on the next `@g-platform-scan-docs warp` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no lifecycle-event system, no `hooks.json`; agent lifecycle hooks are open RFCs
  (#7834 / #6857). Oz Cloud Triggers fire agent runs, not local gald3r `.ps1` hooks.
- **Rules ✅** — real native auto-applying project rules via `AGENTS.md`/`WARP.md` (+ Global Rules +
  cross-harness Agent Memory). Single-file markdown only (no `.mdc`/glob); `g-rl-*` flattened in.
- **Skills ✅** — native Agent Skills (`SKILL.md`); discovers `.agents/.warp/.claude/.cursor/…`
  skills dirs (cross-vendor). gald3r `g-skl-*/SKILL.md` reusable, including from `.claude/skills/`.
- **Commands ⚠️** — built-in slash commands + cloud Warp Drive Workflows (parameterized, repo/user
  scoped); **no user-defined custom slash commands** (open RFC #6857); not installed from repo `commands/`.
- **MCP ✅** — first-class; Settings > Agents > MCP servers (CLI + HTTP/SSE), per-profile access,
  shared across local + Oz agents.
- **Agents ✅ (bonus column)** — Agent Profiles & permissions + Oz subagent orchestration (multi-harness).
- **Docs Fresh ✅** — `last_doc_scan: 2026-06-02` against https://docs.warp.dev.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.warp.dev)

| Capability | How verified |
|---|---|
| Instruction file | /agent-platform/capabilities/rules/ — `AGENTS.md` default + legacy `WARP.md` (ALL-CAPS, `WARP.md` wins if both); auto-applied root + current dir, best-effort subdirs |
| Rules | /agent-platform/capabilities/rules/ — Global Rules + Project Rules (`AGENTS.md`/`WARP.md`); plus Agent Memory (Research Preview) cross-harness persistent memory |
| Skills | /agent-platform/capabilities/skills/ — `SKILL.md` (name/description frontmatter); discovers `.agents/.warp/.claude/.codex/.cursor/.gemini/.copilot/.factory/.github/.opencode` skills dirs (+ `~/`); cross-vendor; page updated 2026-05-28 |
| Agents | /agent-platform/capabilities/agent-profiles-permissions/ — named profiles (base model, autonomy, tool/MCP allow-deny); Oz subagent orchestration (parallel; Claude Code + Codex harnesses) |
| Commands | /agent-platform/capabilities/slash-commands — built-in `/agent /plan /skills /fork /model` + Warp Drive Agent Prompts; **no custom slash-command syntax** (open RFC #6857); Workflows are closest user-authorable primitive |
| Hooks | github.com/warpdotdev/warp/issues/7834 — no Hooks capability page; agent lifecycle hooks (#7834) + hook-like mechanisms (#6857) both Open, no commitment; `claude-code-warp` reuses Claude Code's `hooks.json` |
| MCP | /agent-platform/capabilities/mcp/ — Settings > Agents > MCP servers; CLI Server + Streamable HTTP/SSE; per-profile access; env-var/OAuth; shared local + Oz |
| Other | Warp Drive (Notebooks/Workflows/Prompts/Env); Oz Cloud Triggers & Schedules (Slack/Linear/GitHub events, recurring); multi-harness (Warp Agent/Claude Code/Codex) shared Agent Memory; Agent API/SDK |

**No live install test was run** in this environment; findings rest on the 2026-06-02 doc scan of
https://docs.warp.dev plus the cited GitHub feature requests. `status: ⚠️` reflects the honest mix:
**rules, skills, agents, and MCP are native**; **commands are partial** (no custom slash commands,
cloud-only Workflows); **hooks are an absent capability** (open RFCs #7834 / #6857). Re-confirm the
slash-command and agent-hook RFC status on the then-current Warp release at the next
`@g-platform-scan-docs warp`.
