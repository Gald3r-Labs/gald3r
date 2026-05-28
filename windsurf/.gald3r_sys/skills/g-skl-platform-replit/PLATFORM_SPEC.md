---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: replit
authoring_path: update
docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url_secondary:
  - https://docs.replit.com/replitai/agent
  - https://docs.replit.com/replitai/mcp/overview
  - https://docs.replit.com/programming-ide/configuring-repl
crawl_max_age_days: 14
vault_doc_path: research/platforms/replit/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Replit (Replit Agent / cloud IDE)

**Replit Agent** is an AI coding agent built into the **Replit cloud IDE**. It builds, runs, and
deploys applications inside Replit's Nix-based, Linux containerized environment. It is fundamentally
**not a local config-file IDE** like Cursor: there is no on-disk `.replit-agent/` rules tree, no
lifecycle-hook config file, and no user-authored slash-command registry. gald3r maps onto Replit
through exactly **three** real surfaces: the **`replit.md`** instruction/memory file (the primary
one), the **`.replit` / `replit.nix`** environment config, and **MCP** (Replit Agent is a
first-class MCP client). Everything else in the Cursor reference (`.mdc` rules, `hooks.json`,
`g-agnt-*.md` agents, `g-*` commands, folder-per-skill discovery) has **no native load path** on
Replit and is documented as a gap.

> **Authoring path: UPDATE** — `g-skl-platform-replit/SKILL.md` already ships. This spec records
> the doc-confirmed findings and corrects stale content in that skill: the prior skill treated
> `.replit` as the AI-instruction surface and omitted `replit.md` entirely, and it claimed "MCP
> requires an external URL / can't connect to localhost" as a blanket limitation. The actual
> convention is `replit.md` for Agent instructions/memory, and MCP is **supported and first-class**
> (servers added via the Integrations pane with one-click install + automatic tool discovery).

---

## 1. Folder Hierarchy

Replit is **cloud-IDE-first**. There is no repo-root gald3r config tree analogous to `.cursor/`.
The only on-disk files relevant to Replit + gald3r are:

```
<repl-root>/
├── replit.md            ← Agent custom instructions + persistent memory (auto-created, auto-read,
│                          Agent may self-update it). PRIMARY gald3r instruction surface.
├── AGENTS.md            ← also honored by Replit Agent (cross-tool instruction file convention).
├── .replit              ← Repl config (TOML): run command, language, entrypoint, [nix], [deployment]
├── replit.nix           ← Nix environment definition (system packages / toolchain)
└── .gald3r/             ← gald3r project state (works on disk in the container, but see §6/§9 caveats)
```

- **gald3r writes**: `replit.md` (and/or `AGENTS.md`) with task conventions; the `.gald3r/` state
  tree. It does NOT write a `.cursor/`-style platform config folder — Replit has none.
- **Replit owns**: the cloud IDE, the Nix container lifecycle, the `.replit`/`replit.nix` schemas,
  the Integrations pane (where MCP servers live), and the Agent runtime. `.replit` is **not** an
  AI-instruction file — it is environment/run config; the run-command machinery is Replit's, not
  gald3r's, to author.

> **Correction vs. prior SKILL.md**: the old skill listed `.replit`, `replit.nix`, `.env` as the
> layout and treated `.replit` as the Agent's instruction surface. The actual Agent instruction
> surface is **`replit.md`** (a Markdown file Replit Agent auto-creates and reads on every request).

---

## 2. AI Instruction File

Replit Agent reads **`replit.md`** as its Custom Agent Instructions + project memory:

- **Auto-created**: when you first use Agent, it generates `replit.md` at the repl root with
  best-practice defaults for the detected project type.
- **Auto-read**: Agent includes `replit.md` contents in context on every request to understand
  project architecture, conventions, preferred package managers, and coding style.
- **Self-updating**: Agent may update `replit.md` as it learns about the project — so gald3r's
  injected conventions can be **overwritten** by Agent unless re-asserted (a real durability caveat).
- **`AGENTS.md`** is also honored (the cross-tool AGENTS.md convention works in Replit/Lovable).
- **Format**: Markdown (Replit explicitly chose Markdown because it sits well in model training
  distribution).

gald3r **generates/merges** task-management conventions into `replit.md` (and/or `AGENTS.md`):
task IDs in commits (`feat(T{id}): …`), "tasks live in `.gald3r/TASKS.md`", "read
`.gald3r/CONSTRAINTS.md` before architecture changes". Because Agent can rewrite `replit.md`,
re-priming is recommended at session start.

---

## 3. Agents Support

- **Native concept**: Replit has a single managed Agent (with Assistant / "Agent 3" iterations).
  There is **no** user-authored agent-definition file format equivalent to Cursor's
  `.cursor/agents/g-agnt-*.md`, and no manual agent registry.
- **Discovery of gald3r agents**: ❌ No native load path. `g-agnt-*.md` files have no Replit
  ingestion mechanism. The closest fit is to describe agent roles/behaviors inside `replit.md`
  as prose instructions, which Agent reads as context.
- **Status**: ❌ not supported as files — gald3r's agent layer does not map; degrade to `replit.md`
  prose.

---

## 4. Skills Support

- **Native concept**: ❌ Replit has **no** `SKILL.md` folder-per-skill discovery mechanism. There is
  no `.replit/skills/` or equivalent tree that Agent scans.
- **Discovery of gald3r skills**: no auto-load path. `g-skl-*/SKILL.md` files can sit in `.gald3r/`
  on disk but Agent will not auto-discover or invoke them; they are reference-only prose a user can
  point Agent at by describing the intent.
- **Status**: ❌ not supported. gald3r's skill auto-load model has no Replit equivalent.

---

## 5. Commands / Workflows

- **No user-authored slash-command registry.** There is no `.cursor/commands/g-*.md` analogue and no
  `@g-*` / `/g-*` invocation surface that gald3r can populate.
- **Native "slash commands"** that DO exist are Replit's own — e.g. selecting connections/integrations
  for your app inside the Agent chat; these are platform-defined, not user-authored, and cannot host
  gald3r commands.
- **Workflows**: the `.replit` file declares run/deploy commands ("Workflows" in the Replit UI), but
  these are build/run pipelines, not gald3r command definitions.
- **gald3r mapping**: gald3r `g-*` commands are **not** executable on Replit as-is. A user runs them
  by describing the intent to Agent in natural language; Agent reads `replit.md` for the convention.
- **Status**: ❌ not supported (no user command registry). Native slash commands are platform-owned.

---

## 6. Hooks System

- **No native lifecycle-hook config file.** Replit does **not** expose a Cursor-style `hooks.json`
  with `sessionStart` / `stop` / `preToolUse` / `beforeShellExecution` events, nor a settings-based
  hook wiring for Agent. gald3r's PowerShell hooks (`g-hk-*.ps1`) have **no auto-firing mechanism**.
- **Compounding constraint**: the container is **Linux** — even if hooks could be wired, the
  `g-hk-*.ps1` scripts are PowerShell and would need bash equivalents (PowerShell is not present by
  default in a standard Replit Nix container).
- **Container lifecycle**: the only "lifecycle" surface is the `.replit` run/deployment commands,
  which run the app, not gald3r session hooks. Container restarts reset uncommitted state.
- **gald3r impact**: session-start context injection, agent-complete, pre-commit, and shell-guard
  hooks must be replaced by `replit.md` prose instructions (e.g. "before completing a task, re-read
  CONSTRAINTS.md") rather than enforced code.
- **Status**: ❌ not supported (no native hook events + Linux/PowerShell mismatch).

---

## 7. Rules / Memory

- **Mechanism**: `replit.md` is the **only** persistent-rules/memory surface. There is **no** `.mdc`
  extension, **no** `alwaysApply:` / `globs:` frontmatter scoping, and **no** per-file rule auto-load
  like `.cursor/rules/`.
- **gald3r mapping**: gald3r rules (`g-rl-*.md`) collapse into a single `replit.md` instruction blob
  (all-or-nothing context injection) — no glob-scoped activation. The blob also competes with
  Agent's own self-authored content in the same file.
- **Durability caveat**: because Agent **self-updates** `replit.md`, injected gald3r rules can be
  rewritten or trimmed by the Agent over a session. gald3r's `.gald3r/learned-facts.md` remains the
  authoritative fact store, but Agent won't auto-read it unless `replit.md` points there.
- **Status**: ⚠️ partial — a single instruction blob works, but the granular always-apply /
  glob-scoped rule model does not exist, and the blob is not tamper-stable (Agent edits it).

---

## 8. MCP Support

- **Supported**: ✅ **Yes — first-class.** Replit Agent is an **MCP client**. It connects to external
  tools/data via the Model Context Protocol; each server installs with a single click and Agent
  automatically loads its tools and uses them when appropriate.
- **Config format/location**: MCP servers are added through the Replit **Integrations pane** (UI),
  not a committed `mcp.json` file. A curated catalog of servers is offered, plus a "Add a custom MCP
  server" path for servers not in the catalog, with automatic tool discovery and security scanning
  of MCP traffic.
- **Server discovery**: one-click install from the Integrations pane → automatic tool discovery.
- **gald3r mapping**: the gald3r MCP server is added as a **custom MCP server** via the Integrations
  pane (remote URL — the container cannot reach `localhost` of a different machine, so the gald3r
  MCP endpoint must be a reachable URL/Secret). This is the **strongest** gald3r integration surface
  on Replit.
- **Status**: ✅ verified at the doc/mechanism level (Replit's own MCP overview + 2025 custom-MCP
  announcement); ❓ active gald3r-MCP connection not install-tested in this repo.

> **Correction vs. prior SKILL.md**: the old skill framed MCP as a near-blocker ("MCP server requires
> external URL (Replit can't connect to localhost of a different machine)"). The localhost point is a
> *real* constraint, but MCP itself is fully supported and first-class — it is the recommended
> integration path, not a limitation.

---

## 9. Known Gaps vs. Cursor Reference

Per the Common-vs-Platform-Specific decision tree (`g-skl-platform-cursor/SKILL.md`):

1. **Hooks ❌** — no native lifecycle-hook config (`hooks.json` analogue), and Linux/PowerShell
   mismatch. gald3r `g-hk-*.ps1` do not auto-fire and would need bash rewrites. → documented gap;
   replace with `replit.md` prose.
2. **Rules ⚠️** — no `.mdc`, no `alwaysApply:` / `globs:` scoping. Rules collapse into a single
   `replit.md` blob (all-or-nothing), and Agent can self-rewrite that file. → partial + not
   tamper-stable.
3. **Skills ❌** — no `SKILL.md` folder discovery. gald3r skills have no auto-load path. → gap.
4. **Commands ❌** — no user-authored slash-command registry. Native slash commands are
   Replit-owned (connection selection). gald3r `g-*` commands run only by describing intent. → gap.
5. **Agents ❌** — no agent-definition file format. `g-agnt-*.md` has no load path; degrade to
   `replit.md` prose. → gap.
6. **MCP ✅** — Replit's strongest surface; first-class MCP client, servers via Integrations pane.
   Belongs in platform-specific config (UI/Secrets), not a committed file. Constraint: remote URL
   only (no cross-machine localhost).
7. **Instruction file** — Replit uses **`replit.md`** (auto-created, auto-read, self-updated) plus
   `AGENTS.md`. The prior SKILL.md treated `.replit` (run config) as the instruction surface — that
   is wrong; `.replit`/`replit.nix` are environment config, not AI instructions. Corrected here.
8. **Cloud / non-local constraints** — Linux Nix containers (no PowerShell by default); container
   restarts reset uncommitted state (commit `.gald3r/` files frequently); Replit's git integration
   is separate from Agent, so Agent commits may not surface in gald3r task tracking; Replit Secrets
   replace `.env`.
9. **SCAN_DOCS not yet run** — `last_doc_scan: never`. Exact `replit.md` precedence vs. `AGENTS.md`,
   any 2026 Agent-3 hook/command additions, and the precise custom-MCP config contract should be
   confirmed by `@g-platform-scan-docs replit` against https://docs.replit.com/replitai/replit-dot-md.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ❌ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

`Docs Fresh = ❓` because `last_doc_scan: never` — flip to ✅ after the first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Instruction file (`replit.md`) | Doc citation — Replit docs: Agent auto-creates `replit.md`, auto-reads it on every request, and may self-update it (docs.replit.com/replitai/replit-dot-md) |
| `AGENTS.md` honored | Doc citation — AGENTS.md works in Replit/Lovable (sourcetoad.com/using-agents-md-in-replit-or-lovable) |
| `.replit` / `replit.nix` = env config | Doc citation — Configuring a Repl: run command, language, [nix], [deployment] (docs.replit.com); NOT an AI-instruction file |
| MCP (first-class client) | Doc citation — Replit MCP Overview: Agent connects via MCP, one-click server install, automatic tool loading; custom MCP servers via Integrations pane with auto discovery + security scanning (docs.replit.com/replitai/mcp/overview; blog.replit.com 2025 custom-MCP announcement) |
| Hooks | Absence-of-evidence — no lifecycle-hook config documented; Linux container + PowerShell mismatch; marked ❌ pending SCAN_DOCS |
| Rules / skills / commands / agents | Absence-of-evidence — no `.mdc` rules, no `SKILL.md` discovery, no user command registry, no agent-file format documented; marked ❌/⚠️ |
| Cloud constraints | Doc/known-platform — Linux Nix containers, ephemeral state on restart, separate git integration, Replit Secrets replace `.env` |
| Install / live connection | ❓ Not install-tested in this repo; no live Replit Agent run performed |
</content>
</invoke>
