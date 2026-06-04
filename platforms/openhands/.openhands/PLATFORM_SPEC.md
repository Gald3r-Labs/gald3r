---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: openhands
authoring_path: update
docs_url: https://docs.openhands.dev
docs_url_secondary:
  - https://docs.openhands.dev/overview/skills
  - https://docs.openhands.dev/usage/prompting/microagents-overview
crawl_max_age_days: 7
vault_doc_path: research/platforms/openhands/
last_doc_scan: 2026-05-26
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — OpenHands (All Hands AI, formerly OpenDevin)

OpenHands is an open-source agentic AI software developer from All Hands AI (repo
`OpenHands/OpenHands`, formerly `All-Hands-AI/OpenHands` / "OpenDevin"). Unlike the desktop-IDE
platforms, OpenHands runs the agent loop inside a **Docker-sandboxed runtime** with full
filesystem, shell, web-browsing, and code-execution capability, driven from a web UI / REST API /
CLI rather than an editor. This spec compares OpenHands against the Cursor reference
(`g-skl-platform-cursor`).

> **Authoring path: UPDATE** — `g-skl-platform-openhands/SKILL.md` already ships. This spec records
> verified findings from a doc scan of https://docs.openhands.dev (skills + microagents overview)
> on 2026-05-26 and corrects several stale assumptions in the prior SKILL.md (see §9).
>
> **Verification basis**: doc-citation scan of https://docs.openhands.dev on 2026-05-26 (current
> docs host; `docs.all-hands.dev` 308-redirects there). NOT verified by a local install/sandbox run
> in this repo (no `.openhands/` or `.agents/` folder is present here, and no Docker sandbox was
> launched). Capability cells depending on observed runtime behavior are marked ⚠️/❓ rather than ✅.

---

## 1. Folder Hierarchy

OpenHands reads project-level customization from a small set of repo-root files/folders. There is
**no single `.openhands/` config tree mirroring Cursor's `.cursor/`** — the surfaces are a context
file at root plus a skills folder. Verified loading precedence for skills (from docs, 2026-05-26):

```
<project-root>/
├── AGENTS.md                      ← always-on context (primary, recommended)
├── CLAUDE.md                      ← model-specific always-on variant (Claude)
├── GEMINI.md                      ← model-specific always-on variant (Gemini)
├── .agents/
│   └── skills/<name>/SKILL.md     ← RECOMMENDED skills location (current)
└── .openhands/
    ├── skills/<name>/SKILL.md     ← skills location (deprecated, still loaded)
    └── microagents/
        ├── repo.md                ← repository microagent (always-on, legacy)
        └── <name>.md              ← knowledge microagent, keyword-triggered (legacy)
```

**Skill-location precedence (verified)**: `.agents/skills/` (recommended) →
`.openhands/skills/` (deprecated) → `.openhands/microagents/` (legacy backward-compat).

**gald3r writes** (current convention, per prior SKILL.md): `.openhands/microagents/repo.md`.
This is the **legacy** path; the current recommended targets are `AGENTS.md` (always-on context)
and `.agents/skills/` (skills). See §9 — aligning gald3r output to `.agents/skills/` + `AGENTS.md`
is the main parity follow-up.
**OpenHands owns**: the Docker sandbox runtime, the `.openhands/`/`.agents/` namespaces, skill
discovery/triggering, the microagent→skill migration, and the system-prompt injection mechanism.

❓ The exact directory set gald3r's parity sync writes for OpenHands was not re-verified against a
live install here (no `.openhands/`/`.agents/` present); the gald3r override dir
(`.gald3r_sys/platforms/.openhands/`) currently carries only `openhands_instructions.md`.

---

## 2. AI Instruction File

Verified: OpenHands auto-discovers repo-root **`AGENTS.md`** (primary, recommended), with
**`CLAUDE.md`** and **`GEMINI.md`** as model-specific variants. These are described as **injected
into the system prompt at conversation start** — i.e. always-on repository context, the OpenHands
equivalent of Cursor's always-apply rules.

- This is the most significant correction vs. the prior SKILL.md, which framed
  `.openhands/microagents/repo.md` (or `.openhands_instructions`) as the sole instruction surface.
  `repo.md` still works (legacy repository microagent), but **`AGENTS.md` is the current primary**.
- gald3r already ships personalized `AGENTS.md` / `CLAUDE.md` at root (`g-rl-02` protected/gitignored),
  so gald3r's instruction content reaches OpenHands **with no extra glue** — a strong positive parity.
- gald3r **generates/merges** `AGENTS.md` / `CLAUDE.md` via the setup + parity pipeline.

---

## 3. Agents Support

- **Native concept**: ⚠️ OpenHands is a *single generalist agent* (CodeActAgent and variants),
  customized via skills/microagents — it does **not** expose a Cursor-style roster of named,
  selectable agent files (`@agent-name`). There is no `.openhands/agents/` discovery folder.
- **gald3r mapping**: gald3r `g-agnt-*.md` agent definitions have **no native OpenHands agent slot**.
  Their *content* can be delivered as knowledge skills (keyword-triggered) or folded into `AGENTS.md`,
  but the multi-agent selection model does not transfer. Marked ⚠️ partial / ❌ for native roster.
- **Status**: ⚠️ — agent *behavior content* portable as skills/context; agent *selection* not native.

---

## 4. Skills Support

- **Native concept**: ✅ Yes — OpenHands has a first-class **skills** system (the successor to
  microagents), folder-per-skill with `SKILL.md`. gald3r's `g-skl-*/SKILL.md` shape maps directly.
- **Discovery** (verified precedence): `.agents/skills/<name>/SKILL.md` (recommended) →
  `.openhands/skills/<name>/SKILL.md` (deprecated) → `.openhands/microagents/<name>.md` (legacy).
- **Skill types** (verified): (a) **always-on context** skills, (b) **keyword-triggered** skills
  (activated when keywords appear in the prompt — these require frontmatter), (c) **on-demand /
  agent-invoked** skills. Keyword triggering ≈ Cursor's relevance auto-load but is keyword-gated.
- **Frontmatter**: knowledge/keyword skills use YAML frontmatter (`name`, `trigger_type`,
  `keywords`, optional `mcp_tools` — see §8). ⚠️ Whether gald3r's extra frontmatter fields
  (`subsystem_memberships`, `token_budget`, `description`) are tolerated vs. rejected was not
  install-verified.
- **gald3r mapping**: `g-skl-*/SKILL.md` → `.agents/skills/` (recommended) or `.openhands/skills/`.
  The prior SKILL.md's `.openhands/microagents/` target is the **legacy** path.
- **Status**: ⚠️ — native skills mechanism + folder-per-skill shape verified by docs; gald3r
  frontmatter tolerance and live load not install-tested.

---

## 5. Commands / Workflows

- **Native concept**: ❌ No Cursor-style slash-command / `@g-*` invocation surface and no
  `.openhands/commands/` discovery folder were found in the docs. OpenHands is prompt-driven inside
  the sandbox; "workflows" are expressed as natural-language tasks plus skills, not as registered
  command files.
- **gald3r mapping**: gald3r `g-*.md` command files have **no native OpenHands command runtime**.
  Their content can be ported into keyword-triggered skills (so "do the g-go-code flow" style asks
  activate the relevant skill), but the `/g-*` / `@g-*` invocation syntax does not transfer.
- **Status**: ❌ native commands; ⚠️ content portable as keyword skills.

---

## 6. Hooks System

- **Native hook system**: ❌ OpenHands exposes **no Cursor-style lifecycle-hook wiring** — there is
  no `hooks.json`, no `sessionStart`/`stop`/`preToolUse`/`beforeShellExecution` event registration
  surface, and the agent runs inside a Docker sandbox where host-side PowerShell hooks would not
  execute anyway.
- **gald3r gap**: gald3r ships hooks as host **PowerShell `.ps1`** scripts wired through Cursor's
  `hooks.json`. None of this runs on OpenHands. The closest analog is the `mcp_tools`/MCP mechanism
  (§8) for adding tool capability, and always-on `AGENTS.md` context for injecting behavior — but
  these are not event-driven hooks. This is one of the two largest parity gaps (see §9).
- **Status**: ❌ — no native hook system; gald3r hook automation does not run on OpenHands.

---

## 7. Rules / Memory

- **Mechanism**: rules/memory == the always-on **`AGENTS.md`** (+ `CLAUDE.md`/`GEMINI.md`) context
  file injected into the system prompt, plus **repository microagents** (`repo.md`, always-on legacy)
  and keyword-triggered knowledge skills for scoped guidance.
- **No `.mdc` rule engine**: there is **no `.mdc` extension** and **no per-file `globs:`/
  `alwaysApply:` glob-scoping rule engine** like `.cursor/rules/*.mdc`. The split is binary:
  always-on (AGENTS.md / repo.md) vs. keyword-triggered (knowledge skills).
- **gald3r mapping**: gald3r's many `g-rl-*` rules must be consolidated into `AGENTS.md`
  (always-on) or split into keyword-triggered skills. Rule *content* carries over; Cursor's per-rule
  glob scoping does not. ⚠️ partial.
- **Positive parity**: because OpenHands reads `CLAUDE.md`/`AGENTS.md` directly, gald3r's existing
  instruction files already deliver rules content to OpenHands with no extra work (verified by docs).
- **Status**: ⚠️ — content carries via AGENTS.md/CLAUDE.md; glob scoping lost.

---

## 8. MCP Support

- **Supported**: ✅ Yes — OpenHands supports MCP at two levels (verified by docs):
  1. **Skill-scoped `mcp_tools`** — a keyword-triggered skill's YAML frontmatter can declare an
     `mcp_tools` / `mcp_location` block that spins up an MCP server and dynamically registers its
     tools **when the skill activates** (per-skill, on-demand tool injection).
  2. **Global MCP config** — MCP servers configured for the OpenHands instance/sandbox. The prior
     SKILL.md shows a sandbox config form (`mcp_url`); exact 2026 config key/location was not
     install-verified here.
- **Sandbox note**: because the agent runs in Docker, an MCP server on the host must be reachable
  from the container (e.g. `host.docker.internal`), unlike a desktop IDE talking to a local server.
- **Status**: ⚠️ — MCP capability verified by docs (skill-scoped `mcp_tools` + global config); the
  concrete gald3r MCP server block and a live sandbox-to-host connection were not install-tested.

---

## 9. Known Gaps vs. Cursor Reference

1. **No native hook system** (❌). gald3r's entire `g-hk-*.ps1` hook suite + `hooks.json` wiring has
   no OpenHands equivalent, and host PowerShell would not run inside the Docker sandbox regardless.
   gald3r lifecycle automation (session-start context inject, agent-complete, pre-tool guard) does
   not run on OpenHands. Behavior must be reframed as always-on `AGENTS.md` context or MCP tools.
2. **No native command runtime** (❌). No `.openhands/commands/` / slash-command surface; gald3r
   `g-*.md` commands are not invocable as `/g-*`. Content portable only as keyword-triggered skills.
3. **No multi-agent roster** (⚠️/❌). OpenHands is a single generalist agent; gald3r `g-agnt-*`
   selectable agents have no native slot — content portable as skills/context only.
4. **No `.mdc` glob-scoped rule engine** (⚠️). Cursor's per-rule `alwaysApply`/`globs` selectivity
   collapses into binary always-on (AGENTS.md) vs. keyword-triggered (skills). Content transfers;
   scoping does not.
5. **gald3r currently targets the legacy microagents path** (⚠️). The shipped SKILL.md writes
   `.openhands/microagents/repo.md`; current docs deprecate that in favor of `AGENTS.md` (context)
   + `.agents/skills/` (skills). Re-targeting parity output is the main follow-up.
6. **Docker sandbox constraints** (⚠️). The agent runs in an isolated container: host file paths,
   host PowerShell hooks, and host-local MCP servers are not directly reachable; commit identity is
   the sandbox/OpenHands identity (verify task-record authorship). gald3r assumptions baked for a
   host-resident editor do not hold.
7. **No live install verification in this repo** (❓). No `.openhands/`/`.agents/` folder, no
   sandbox launched; all ✅-by-docs claims await a real `openhands` run + skill/MCP load test.
8. **Decision-tree placement**: OpenHands's skills frontmatter (`mcp_tools`, keyword triggers) and
   sandbox/MCP config are correctly classified **platform-specific** — they live in the OpenHands
   tree (`.gald3r_sys/platforms/.openhands/`), not common `.gald3r_sys/`. The shared `AGENTS.md`/
   `CLAUDE.md` instruction files are the one place OpenHands reuses common gald3r output directly.

**Positive parity (better than prior SKILL.md assumed):** OpenHands DOES have a native skills
system (folder-per-skill `SKILL.md`), DOES auto-discover `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` as
always-on context, and DOES support MCP (skill-scoped `mcp_tools` + global) — so rules and skills
content reach OpenHands with minimal glue. The losses are hooks, commands, and the multi-agent roster.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌**: no native hook system; Docker sandbox blocks host `.ps1` hooks.
- **Rules ⚠️**: content carries via `AGENTS.md`/`CLAUDE.md`; `.mdc` glob scoping lost.
- **Skills ⚠️**: native skills + folder-per-skill verified by docs; gald3r frontmatter tolerance & live load untested.
- **Commands ❌**: no native command/slash surface; content portable only as keyword skills.
- **MCP ⚠️**: skill-scoped `mcp_tools` + global config verified by docs; live gald3r server block untested.
- **Docs Fresh ✅**: doc scan of https://docs.openhands.dev completed 2026-05-26.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Skill discovery + precedence | Doc scan https://docs.openhands.dev/overview/skills (2026-05-26): `.agents/skills/` (recommended) → `.openhands/skills/` (deprecated) → `.openhands/microagents/` (legacy) |
| Instruction file | Same scan: `AGENTS.md` (primary) / `CLAUDE.md` / `GEMINI.md` auto-discovered, "injected into the system prompt at conversation start" |
| Skill types / triggering | Same scan + microagents overview: always-on, keyword-triggered (frontmatter required), on-demand |
| Microagents → skills migration | Microagents overview (2026-05-26): `.openhands/microagents/` deprecated; `repo.md` repository microagent + keyword knowledge microagents; markdown + YAML frontmatter (name, trigger_type, keywords, mcp_location) |
| MCP | Microagents/skills docs (2026-05-26): skill-scoped `mcp_tools` block spins up MCP server + registers tools on skill activation; sandbox config form in prior SKILL.md |
| Sandbox runtime | OpenHands docs/overview: Docker-sandboxed runtime with shell/fs/browser; host-side hooks not reachable |
| No hooks/commands/agent-roster | Absence in docs scan (no `hooks.json`, no `.openhands/commands/`, no `.openhands/agents/` discovery) |
| Live install | ❓ NOT verified — no `.openhands/`/`.agents/` in this repo; no sandbox launched |
</content>
</invoke>
