---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: replit
authoring_path: update
docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url_secondary:
  - https://docs.replit.com/replitai/skills
  - https://docs.replit.com/replitai/agent
  - https://docs.replit.com/learn/model-context-protocol
  - https://docs.replit.com/references/agent/task-lifecycle
  - https://blog.replit.com/introducing-workflows
crawl_max_age_days: 14
vault_doc_path: research/platforms/replit/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Replit (Replit Agent / cloud IDE)

**Replit Agent** is an AI coding agent built into the **Replit cloud IDE**. It builds, runs, and
deploys applications inside Replit's Nix-based, Linux containerized environment. As of the 2026
crawl it natively supports **three** of the six gald3r-relevant primitives — **Agent Skills**
(`SKILL.md` in `/.agents/skills`, the agentskills.io open standard), **rules/memory** (the
`replit.md` instruction file), and **MCP** (Agent is a first-class MCP client *and* Replit ships a
hosted MCP server). **Agents** are *partial* (user-selectable Plan/Build modes + effort tiers are
native, but there is no documented user-definable custom-agent file format). **Hooks** and
**commands** are **not** supported — there is no lifecycle-hook config and no user-authored
slash-command registry (Workflows are adjacent shell-command runners, not an agent command surface).

**Authoring path: UPDATE. Verified 2026-06-02** against https://docs.replit.com (see Verification
Evidence). This **supersedes** the prior spec (`last_doc_scan: never`/`2026-05-20`), which incorrectly
marked **skills** as unsupported and **agents** as a hard ❌ — Agent Skills shipped (~April 2026) and
are NATIVE, and Plan/Build modes + effort tiers make agents an honest ⚠️ partial.

> **Instruction-file convention:** Replit standardizes on **`replit.md`** (project root), NOT
> `AGENTS.md`/`CLAUDE.md`. Replit's own docs say "Agent automatically reads your `replit.md` file"
> and it "must be located in your project's root directory to work properly." `AGENTS.md` appears
> only in unofficial community blogs; treat `replit.md` as the canonical surface.

> **Surface split:** the on-disk, versioned gald3r surface is **Agent Skills** (`/.agents/skills`)
> + **`replit.md`**. **MCP** and the OAuth **Integrations** connectors live in the cloud UI (not a
> committed file). Modes/effort tiers are interactive UI controls. Hooks/commands have no surface
> at all. Where a feature is UI-only or cloud-constrained it is noted inline.

---

## 1. Folder Hierarchy

Replit is **cloud-IDE-first**. The only on-disk surfaces relevant to Replit + gald3r are:

```
<repl-root>/
├── replit.md                     ← Agent custom instructions + persistent memory (auto-created,
│                                   auto-read on every request, Agent may self-update it). PRIMARY
│                                   gald3r instruction surface — NOT AGENTS.md/CLAUDE.md.
├── .agents/
│   └── skills/  <name>/SKILL.md   ← Agent Skills (agentskills.io open standard; Project scope,
│                                   versioned in the repo). NATIVE, lazy-loaded by name+description.
├── .replit                       ← Repl config (TOML): run command, language, entrypoint, [nix], [deployment]
├── replit.nix                    ← Nix environment definition (system packages / toolchain)
└── .gald3r/                      ← gald3r project state (works on disk in the container; commit often — §8 caveats)
```

- **gald3r writes**: `replit.md` (task conventions + pointers); `/.agents/skills/<name>/SKILL.md`
  (the gald3r skill tree — **this is now a real native load path**); the `.gald3r/` state tree.
- **Replit owns**: the cloud IDE, the Nix container lifecycle, the `.replit`/`replit.nix` schemas,
  the **Integrations** + **MCP** panes (cloud UI), and the Agent runtime (modes/effort tiers).
  `.replit`/`replit.nix` are **environment/run config**, not AI-instruction files.

> Skills also have **User** and **Enterprise** scopes (account/org level), and the picker discovers
> extra skills in `.local/secondary_skills/`. Only the **Project** scope (`/.agents/skills`) is the
> committed, gald3r-shippable surface.

---

## 2. AI Instruction File — ✅ NATIVE (`replit.md`)

Replit Agent reads **`replit.md`** (repl root) as its Custom Agent Instructions + project memory:

- **Auto-created** on first Agent use; **auto-read** into context on every request to understand
  project architecture, conventions, preferred package managers, and coding style.
- **Self-updating**: "Agent can also update your `replit.md` file as it learns more about your
  project" — so injected gald3r conventions can be **overwritten** unless re-asserted (durability
  caveat). Replit also describes decision-time injection of guidance for reliability.
- **Root-only**: must sit at the project root to work; **Replit-scoped** — "doesn't automatically
  apply to other AI tools."
- **`AGENTS.md` is NOT the official convention** — it appears only in community blogs; Replit's docs
  standardize on `replit.md`.
- Source: https://docs.replit.com/replitai/replit-dot-md

gald3r merges task-management conventions into `replit.md`: task IDs in commits (`feat(T{id}): …`),
"tasks live in `.gald3r/TASKS.md`", "read `.gald3r/CONSTRAINTS.md` before architecture changes",
"read `.gald3r/learned-facts.md` for durable facts". Re-prime at session start (Agent rewrites it).

## 3. Agents Support — ⚠️ PARTIAL

- **Native, user-selectable**: **Plan mode** ("brainstorm … before Agent changes any code or data")
  vs **Build mode**, plus **effort/cost tiers** (Lite / Economy / Power / Turbo). These are
  first-class user controls over agent behavior.
- **Internal orchestration only**: specialized subagent ROLES (manager, editor, verifier) and
  parallel subagents exist, but are described in Replit's blog/case studies as internal
  orchestration — **NOT** a user-definable custom-agent/role file format. Agent 3 "Stacks" (create
  specialized agents/automations) is emerging but **not** documented as a config primitive on
  docs.replit.com.
- **gald3r mapping**: `g-agnt-*.md` files have **no native file load path**. Express agent roles as
  prose in `replit.md`, or (better) as **Agent Skills** (§4). Use Plan mode for review/verify gates.
- Source: https://docs.replit.com/replitai/agent

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (agentskills.io `SKILL.md` open standard): "Skills live in your project's
  **`/.agents/skills`** directory and conform to the Agent Skills specification — an open standard
  that works across agents." "A skill is a Markdown file containing instructions Agent follows."
- **Lazy-loaded**: "Agent sees the name and description of every installed skill, but only loads the
  full content when relevant." Invoked via the **"Use a skill"** picker.
- **Scopes**: **Project** (versioned in `/.agents/skills`), **User**, **Enterprise**. Agent can
  **self-author** a skill from a successful session ("ask Agent to capture what it learned"); the
  picker also discovers `.local/secondary_skills/`. Added **~April 2026**.
- **gald3r mapping**: `g-skl-*/SKILL.md` load natively from **`/.agents/skills/`** — this is the
  primary gald3r delivery surface on Replit (a real reversal from the prior ❌).
- Source: https://docs.replit.com/replitai/skills

## 5. Commands / Workflows — ❌ NOT SUPPORTED (as agent commands)

- **No user-authored agent slash-command registry.** Official docs document no `/command` authoring
  for the Agent — there is no `.cursor/commands/g-*.md` analogue and no `@g-*` invocation surface.
- **Workflows** are the closest native feature: "an easily configurable Run button that can run any
  command(s) you'd like." These are **shell-command runners** (build/test/run pipelines), **not**
  reusable agent-prompt commands — adoptable as a gald3r build/test runner only.
- **gald3r mapping**: gald3r `g-*` commands are **not** executable as commands. A user triggers a
  gald3r workflow by invoking the matching **Agent Skill** (§4) or describing intent in chat.
- Source: https://blog.replit.com/introducing-workflows

## 6. Hooks System — ❌ NOT SUPPORTED

- **No user-scriptable lifecycle hooks.** Replit documents an Agent **task lifecycle**
  (`planned → running → ready → finished`) but exposes **no** user-defined event/lifecycle hooks
  that run a script — no `session-start`, `pre-tool`, `pre-commit`, or file-watch hook authoring.
  Git-workflow hooks are an **open community feature request**, not a shipped feature.
- **Compounding constraint**: the container is **Linux** — even if hooks could be wired, gald3r's
  `g-hk-*.ps1` scripts are PowerShell and would need bash equivalents (PowerShell is **not** present
  by default in a standard Replit Nix container).
- **gald3r mapping**: session-start context injection, agent-complete, pre-commit, and shell-guard
  hooks must be replaced by `replit.md` prose (e.g. "before completing a task, re-read
  CONSTRAINTS.md") or git `core.hooksPath` bash scripts — not enforced gald3r code.
- Source: https://docs.replit.com/references/agent/task-lifecycle

## 7. Rules / Memory — ✅ NATIVE (`replit.md`)

- **Mechanism**: `replit.md` is the persistent, always-on instructions/memory surface — "Agent
  automatically reads your `replit.md` file and uses its contents to understand your project's
  architecture and conventions [and] follow your preferred coding patterns and style."
- **No granular scoping**: there is **no** `.mdc` extension, **no** `alwaysApply:`/`globs:`
  frontmatter, and **no** per-file rule auto-load like `.cursor/rules/`. gald3r rules (`g-rl-*.md`)
  collapse into a single `replit.md` instruction blob (all-or-nothing context injection).
- **Durability caveat**: because Agent **self-updates** `replit.md`, injected gald3r rules can be
  rewritten or trimmed over a session. `.gald3r/learned-facts.md` remains the authoritative fact
  store, but Agent won't auto-read it unless `replit.md` points there.
- Source: https://docs.replit.com/replitai/replit-dot-md

## 8. MCP Support — ✅ NATIVE

- **Client**: Replit Agent is an **MCP client** — "An MCP client is something like Claude, Replit
  Agent, or a command-line interface…"; users "connect a pre-listed MCP server or add a custom one
  in Replit." Servers are added through the cloud UI (Integrations / Connect-via-MCP), **not** a
  committed `mcp.json`; tools are auto-discovered.
- **Server**: Replit also ships a **hosted MCP server** — "Replit's MCP server lets external clients
  create, update, and manage full-stack applications on Replit" (e.g.
  `claude mcp add --transport http replit https://replit-mcp.com/server/mcp`), with OAuth consent on
  first connect. This enables **external orchestration** of Replit projects from another gald3r host.
- **gald3r mapping**: add the gald3r MCP server as a **custom MCP server** in the UI. The endpoint
  must be a **reachable remote URL** (the container cannot reach a different machine's `localhost`),
  stored as a Replit Secret. This is the **strongest** gald3r integration surface on Replit.
- Source: https://docs.replit.com/learn/model-context-protocol

---

## Parity vs. Cursor Reference

Replit reaches **partial parity** with the Cursor reference (`g-skl-platform-cursor`): native
**skills, rules, and MCP**; **partial agents** (Plan/Build modes + effort tiers, no custom-agent
files); and **no hooks or commands**. The big change from the prior assessment is **Agent Skills** —
gald3r's `g-skl-*/SKILL.md` tree now has a real native load path at **`/.agents/skills/`**.

**Reuse note:** ship the gald3r skill tree into **`/.agents/skills/`** (agentskills.io standard,
Project scope, versioned in the repo) and point `replit.md` at `.gald3r/` conventions. There is no
hook/command surface, so degrade those gald3r layers to `replit.md` prose + Workflows (build/test)
+ Plan mode (review gate). Native bonus: OAuth **Integrations** connectors (Notion, Dropbox, Stripe,
etc.) distinct from generic MCP.

## Hook System

- **Type**: none
- **Config file**: n/a (no lifecycle-hook config; no settings hook wiring for Agent)
- **Events available**: none — no `session-start` / `pre-tool` / `pre-commit` / file-watch. The only
  lifecycle surface is the Agent **task lifecycle** (`planned → running → ready → finished`), which is
  observational, not a script-execution hook
- **Event payload format**: none
- **Limitations**: container is **Linux** — even if wired, `g-hk-*.ps1` are PowerShell (not present
  by default in a Nix container) and would need bash equivalents; container restarts reset
  uncommitted state. Git-workflow hooks are an open community request, not shipped
- **gald3r hook files**: none auto-fire — hook behaviors must run via `replit.md` prose, git
  `core.hooksPath` bash scripts, or manual invocation

## Atypical Handling

- Cloud Linux container: PowerShell is not installed by default; gald3r `.ps1` hooks would need bash ports.
- Instruction file is **`replit.md`** (auto-created, auto-read, self-updated) — **not** AGENTS.md/CLAUDE.md.
- Skills load from **`/.agents/skills/`** (agentskills.io standard) — a real native surface.
- MCP/Integrations live in the cloud UI (not committed files); the gald3r MCP endpoint must be a
  reachable remote URL (no cross-machine `localhost`), stored as a Replit Secret.
- Container restarts reset uncommitted state — commit `.gald3r/` files frequently.

## gald3r Integration Notes

- **Ship gald3r skills to `/.agents/skills/`** — Replit Agent discovers them natively (lazy-loaded).
- Put task conventions + `.gald3r/` pointers in **`replit.md`**; re-prime at session start (Agent rewrites it).
- gald3r hooks do NOT auto-fire AND `.ps1` is not runnable in the default Nix container — treat hook
  automation as unavailable; express behaviors in `replit.md` or git `core.hooksPath` bash.
- Use **Plan mode** as the review/verify gate; **Workflows** as the build/test runner.
- Re-verify on the next `@g-platform-scan-docs replit` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.replit.com)

| Capability | How verified |
|---|---|
| Instruction file (`replit.md`) | /replitai/replit-dot-md — "Agent automatically reads your `replit.md` file"; "must be located in your project's root directory to work properly"; Agent can self-update it. NOT AGENTS.md/CLAUDE.md (community-only) |
| Rules / memory | /replitai/replit-dot-md — `replit.md` is the always-on instructions/memory blob; no `.mdc`, no `alwaysApply:`/`globs:` scoping |
| Skills | /replitai/skills — agentskills.io `SKILL.md` in **`/.agents/skills`**; lazy-loaded by name+description; Project/User/Enterprise scopes; "Use a skill" picker; ~April 2026 |
| Agents | /replitai/agent — native Plan/Build modes + effort tiers (Lite/Economy/Power/Turbo); subagent roles are internal orchestration, not a user-definable file format; Agent 3 "Stacks" undocumented as config |
| Commands / Workflows | blog.replit.com/introducing-workflows — Workflows = "Run button that can run any command(s)" (shell runners), not agent slash-commands; no `/command` authoring documented |
| Hooks | /references/agent/task-lifecycle — task lifecycle `planned→running→ready→finished` documented, but no user-defined script hooks; git hooks are an open community request; Linux/PowerShell mismatch |
| MCP | /learn/model-context-protocol — Agent is an MCP client (connect pre-listed/custom server, auto tool discovery); Replit ships a hosted MCP server (`replit-mcp.com`, OAuth on first connect) for external orchestration |
| Cloud constraints | Known-platform — Linux Nix container (no PowerShell by default), ephemeral state on restart, MCP/Integrations are cloud-UI surfaces, Replit Secrets replace `.env` |
| Install / live connection | ❓ Not install-tested in this repo; no live Replit Agent run performed |
