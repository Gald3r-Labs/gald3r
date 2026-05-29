---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: copilot
authoring_path: update
docs_url: https://docs.github.com/en/copilot/reference/customization-cheat-sheet
docs_url_secondary:
  - https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
  - https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
  - https://docs.github.com/en/copilot/customizing-copilot/extending-copilot-chat-with-mcp
crawl_max_age_days: 7
vault_doc_path: research/platforms/github_copilot/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1463
---

# PLATFORM_SPEC.md — GitHub Copilot

GitHub Copilot is GitHub's AI coding assistant. It runs across multiple surfaces (VS Code,
Visual Studio, JetBrains, GitHub.com cloud agent, and Copilot CLI), and each surface supports
a different subset of customization primitives. gald3r targets the VS Code + CLI + GitHub.com
surfaces, since those expose the richest customization (instructions, agents, prompt files,
MCP, and — recently — hooks on the cloud/CLI agent).

**Authoring path**: UPDATE — `g-skl-platform-copilot/SKILL.md` already ships. This spec records
verified findings and the honest capability assessment that feeds `PLATFORM_STATUS.md`.

> **Verification caveat (read first)**: `last_doc_scan: never`. This spec is authored from prior
> Copilot knowledge and the existing SKILL.md, NOT from a fresh `@g-platform-scan-docs copilot`
> crawl. GitHub Copilot's customization surface moves fast (hooks and CLI agents are recent and
> change frequently). Every capability whose behavior could not be confirmed by a current doc
> citation or an install test is marked `❓`. Do not promote `❓` → `✅` without evidence recorded
> in the Verification Evidence section.

---

## 1. Folder Hierarchy

Copilot customization is split across **two real locations** plus a gald3r convention folder:

```
.github/                              ← Copilot's native customization home (Copilot reads this)
├── copilot-instructions.md           ← Repo-wide always-apply custom instructions (auto-loaded)
├── instructions/                     ← Path-scoped instructions (Copilot-only feature)
│   └── *.instructions.md             ← frontmatter: applyTo: "glob/pattern"
├── prompts/                          ← Reusable prompt files (VS Code chat; "/" picker)
│   └── *.prompt.md                   ← frontmatter: mode, model, tools
├── chatmodes/                        ← Custom chat modes (VS Code, newer)        ❓ untested in gald3r
│   └── *.chatmode.md
└── agents/                           ← Custom agents (cloud agent / CLI)         ⚠️ surface-dependent
    └── *.md

.claude/skills/                       ← Copilot auto-discovers agent skills here  ❓ (see §4)
└── <name>/SKILL.md

.copilot/                             ← gald3r CONVENTION folder — NOT a Copilot-native path
├── README.md                         ← Platform orientation for gald3r users
└── commands/                         ← gald3r command reference docs (NOT executed by Copilot)
    └── g-*.md

<repo-root>/.vscode/mcp.json          ← MCP server config (VS Code)              (see §8)
~/.copilot/                           ← CLI agent home (mcp-config.json, agents)  (CLI surface)
```

**What gald3r writes vs. what Copilot owns:**
- gald3r writes/generates: `.github/copilot-instructions.md` (from always-apply rules),
  `.copilot/commands/` + `.copilot/README.md` (convention), and on full/adv tiers the
  `.github/agents/`, `.github/prompts/`, and hooks config.
- Copilot owns the *meaning* of `.github/copilot-instructions.md`, `.github/instructions/`,
  `.github/prompts/`, and MCP config — gald3r only populates these paths.
- `.copilot/` is purely a gald3r invention. Copilot does not read it.

---

## 2. AI Instruction File

**Primary**: `.github/copilot-instructions.md` — repo-wide custom instructions, auto-loaded into
every Copilot Chat/agent session for the repository. This is the canonical, documented file. ✅

- Plain Markdown, no required frontmatter.
- gald3r generates it from always-apply rules via `generate_copilot_instructions.ps1`.
- Context budget caution: very large files compete for the model context window. Keep consumer
  installs lean (the existing SKILL.md recommends < 500 lines).

**Secondary**: `.github/instructions/*.instructions.md` — path-scoped instructions with an
`applyTo:` glob in frontmatter. Applied only when the active file matches the glob. This is a
Copilot-unique feature with no Cursor/Claude equivalent; gald3r does not currently generate these.

**Note on AGENTS.md**: GitHub Copilot has been adding `AGENTS.md` support (the cross-tool agent
instruction convention), but coverage varies by surface and version. ❓ Not relied upon by gald3r
for Copilot — `.github/copilot-instructions.md` is the documented, stable path.

---

## 3. Agents Support

Copilot's "agent" concept is **surface-dependent** and differs materially from Cursor's model:

- **Copilot coding agent (GitHub.com cloud)** and **Copilot CLI** support **custom agents** —
  Markdown files (in `.github/agents/` for the repo, or `~/.copilot/agents/` for CLI) that define
  a named agent with its own instructions/persona, invoked explicitly (manual selection / CLI
  invoke), NOT auto-loaded by relevance. ⚠️ The exact discovery rules and file schema are
  evolving; treat as partial until install-tested.
- **VS Code** uses "agent mode" (an interaction mode), and supports **custom chat modes**
  (`.github/chatmodes/*.chatmode.md`) rather than the cloud-agent `agents/` file format. ❓
- gald3r `g-agnt-*.md` files are authored in a generic Markdown persona format. They can be
  dropped into `.github/agents/` but require manual selection; there is no "auto-pick the right
  agent by task" behavior comparable to a richer orchestration layer.

**Comparison to Cursor**: Cursor auto-applies rules and lets the agent reason over the whole
`.cursor/` tree; agent selection is implicit. Copilot agents are explicitly invoked by name and
the format/surface support is fragmented across cloud/CLI/VS Code. This is the key architectural
difference the task asks to document: **Copilot agents are named, manually-invoked primitives on
the cloud/CLI surface, not ambient persona auto-loading like the Cursor reference.**

---

## 4. Skills Support

Copilot has an **agent skills** concept (documented under "about agent skills"). Reported
behavior: the agent can discover skill folders containing a `SKILL.md` and load them when
relevant — including from `.claude/skills/` on some surfaces. ❓

- The existing SKILL.md claims Copilot auto-discovers `.claude/skills/`, `.agents/skills/`, and
  `.github/skills/`. The `.claude/skills/` auto-discovery and the exact precedence are **not
  verified against a current doc citation** and are marked `❓`.
- Folder-per-skill (`<name>/SKILL.md`) with frontmatter is the documented shape for agent skills.
- Invocation is relevance-driven (the agent decides), not an explicit `/skill` command.

**Conservative gald3r position**: do not assume gald3r skills "just work" on every Copilot
surface. Treat skills as ⚠️ partial / surface-dependent until an install test on a target
surface (VS Code vs. cloud agent vs. CLI) confirms discovery.

---

## 5. Commands / Workflows

Copilot has **no slash-command system equivalent to gald3r's `@g-*` / `/g-*` commands.** The
closest primitives:

- **Prompt files** (`.github/prompts/*.prompt.md`) — VS Code chat surfaces these in a "/" picker;
  the user manually selects one to run. This is the nearest analog to a gald3r command, but it is
  manual-selection, VS Code-only, and not a programmable command namespace. ⚠️
- **Copilot CLI** supports slash-style controls (e.g. `/mcp`) for the CLI itself, but does NOT
  execute gald3r's `g-*` command files as commands. ❌ for gald3r command parity.
- gald3r's 90+ `g-*` commands are shipped to `.copilot/commands/*.md` as **reference docs only** —
  they document the workflow for humans/agents; Copilot does not auto-discover or run them. ❌

**Net**: gald3r commands are NOT natively executable on Copilot. Prompt files cover a small,
manual, VS Code-only slice. This is a documented gap.

---

## 6. Hooks System

Copilot has a **recent, surface-limited hooks capability** on the coding agent (cloud) and CLI
agent. Reported lifecycle events include `sessionStart`, `userPromptSubmitted`, `preToolUse`,
`postToolUse`, `agentStop`/`sessionEnd`, `subagentStop`, and `errorOccurred`. ⚠️ This area is new
and changes frequently — treat all event names and the exact config schema as `❓` pending a
fresh doc crawl.

- Config format is **JSON**, not a raw `.ps1` path. Each hook object wraps a command via
  `"bash"` / `"powershell"` keys and `"type": "command"`. The existing SKILL.md documents a
  `.github/hooks/gald3r-hooks.json` (`version: 1`) example.
- **Critical scope note**: Copilot hooks fire only **during an active agent session** (cloud/CLI).
  They are NOT git hooks, CI scripts, or GitHub Actions. Normal commits/pushes are unaffected.
- **VS Code hook support is partial/preview** at best. ❓
- gald3r's Claude-Code-style `hooks.json` is **not** the same schema — Copilot requires the
  `"type": "command"` wrapper and different event names (e.g. `stop` → `agentStop`).

**Comparison to Cursor**: Cursor hooks (`.cursor/hooks/*.ps1` + `hooks.json`) run locally and
predictably for the desktop agent. Copilot hooks are JSON-wrapped, surface-fragmented (CLI/cloud
strong, VS Code weak/preview), and newer. ⚠️ partial.

---

## 7. Rules / Memory

- **Persistent rules** = `.github/copilot-instructions.md` (always-apply, auto-loaded). ✅ This is
  the documented, stable mechanism and maps cleanly to gald3r always-apply rules.
- **Path-scoped rules** = `.github/instructions/*.instructions.md` with `applyTo:` glob. ✅ Native
  Copilot feature, no Cursor equivalent. gald3r does not currently emit these.
- **Extension**: `.md` (Copilot), vs. Cursor's `.mdc`. gald3r flattens always-apply rules into the
  single `copilot-instructions.md` rather than shipping per-rule files.
- **Size limits**: no hard documented cap, but large instruction files compete for context window.
  Keep lean. There is no separate long-term "memory" store beyond the instruction files for the
  customization surface gald3r uses. ❓ (Copilot memory features, where present, are not used.)

---

## 8. MCP Support

**Yes.** Copilot supports MCP (Model Context Protocol) servers across VS Code, CLI, and the
GitHub.com agent (support added progressively through 2025). ✅ (config format) / ⚠️ (cross-surface
parity).

- **VS Code**: `.vscode/mcp.json` (workspace) or user-level MCP config; servers auto-connect.
- **Copilot CLI**: `~/.copilot/mcp-config.json`; manage/list with the `/mcp` control.
- **GitHub.com coding agent**: MCP configured in repo/org settings.
- Config is JSON describing server command/args/env (stdio) or URL (http). Discovery and timeout
  behavior follow the host surface's MCP client.

The exact file name/location differs per surface, so MCP is fully supported but **not single-path
portable** — gald3r cannot ship one `mcp.json` that every Copilot surface reads. ⚠️

---

## 9. Known Gaps vs. Cursor Reference

Honest gap list (feeds `PLATFORM_STATUS.md` and the capability matrix). Decision-tree disposition
per `g-skl-platform-cursor` ((a) common `.gald3r_sys/`, (b) platform-specific config, (c) gap):

| Cursor-reference feature | Copilot status | Disposition |
|---|---|---|
| Always-apply rules | ✅ `.github/copilot-instructions.md` | (b) generated per-platform |
| Per-rule `.mdc` files | ❌ no equivalent — flattened into one instructions file | (c) gap (acceptable) |
| Path-scoped rules | ✅ `.github/instructions/` (Copilot-only superset) | (b) optional, adv tier |
| Skills auto-discovery | ❓ surface-dependent; `.claude/skills/` claim unverified | (c) untested gap |
| Agents (ambient persona) | ⚠️ named, manual-invoke, cloud/CLI only | (b) platform-specific |
| Slash commands (`g-*`) | ❌ not executable; `.copilot/commands/` are docs only | (c) gap |
| Prompt files (manual) | ⚠️ VS Code-only `/` picker analog | (b) full/adv tier |
| Hooks (local PS1) | ⚠️ JSON-wrapped, cloud/CLI only, VS Code preview, newer/volatile | (b) platform-specific |
| MCP | ⚠️ supported but per-surface config paths differ | (b) platform-specific |

**Biggest honest gaps**: (1) no native executable command system — gald3r commands are reference
docs only; (2) skills auto-discovery is unverified across surfaces; (3) hooks are new, JSON-only,
and not available uniformly (strong on CLI/cloud, preview/absent in VS Code).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ✅ | ❓ | ❌ | ⚠️ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Rationale:
- **Hooks ⚠️** — exist (cloud/CLI, JSON schema) but surface-fragmented and newly evolving.
- **Rules ✅** — `.github/copilot-instructions.md` is documented, stable, auto-loaded.
- **Skills ❓** — agent-skills concept exists but `.claude/skills/` discovery is unverified here.
- **Commands ❌** — no native execution of gald3r commands; reference docs only.
- **MCP ⚠️** — supported but config path differs per surface (not single-path portable).
- **Docs Fresh ❌** — `last_doc_scan: never`; no current crawl performed.

---

## Verification Evidence

| Capability | How assessed | Confidence |
|---|---|---|
| Rules (copilot-instructions.md) | Documented GitHub feature; existing SKILL.md; long-stable | High (doc-backed) |
| Path-scoped instructions | Documented Copilot-only feature (`applyTo:` frontmatter) | Medium |
| Agents | Prior knowledge of cloud agent + CLI custom agents; surface-fragmented | Medium-Low |
| Skills | Agent-skills concept known; `.claude/skills/` auto-discovery NOT confirmed | Low — marked ❓ |
| Commands | Architectural fact: no gald3r command runtime on Copilot | High (negative) |
| Hooks | Recent Copilot hooks feature; JSON schema per existing SKILL.md; volatile | Low-Medium |
| MCP | Documented Copilot MCP support across VS Code/CLI/cloud | Medium-High |

**No install test or live `@g-platform-scan-docs copilot` crawl was run for this spec.** All
`❓`/`⚠️` ratings remain provisional until a fresh crawl (T1484 parity / a future SCAN_DOCS run)
records dated evidence here. Promote ratings only with citations.
