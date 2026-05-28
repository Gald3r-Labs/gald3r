---
name: g-skl-platform-antigravity
description: Reference for Google Antigravity (agent-first IDE) customization in gald3r projects. Covers the post-2.0-relaunch config conventions (.antigravity/ + ~/.gemini/antigravity/), AGENTS.md instruction file, MCP config, workflows/slash commands, and the large set of currently-untested gald3r primitives. Created from scratch (T1465) — platform relaunched ~2026-05-19; many capabilities remain UNVERIFIED.
docs_url: https://antigravity.google/docs/home
docs_url_secondary: https://codelabs.developers.google.com/getting-started-google-antigravity
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
last_doc_scan: never
reference: g-skl-platform-cursor
capability_status:
  hooks: ❓        # no documented native hook/lifecycle system found post-relaunch
  rules: ⚠️        # AGENTS.md project-root instruction file confirmed; .mdc-style always-apply rules dir NOT confirmed
  skills: ❓        # no documented folder-per-skill SKILL.md discovery mechanism found
  commands: ⚠️     # "workflows" = saved-prompt slash commands (/), stored in ~/.gemini/antigravity/global_workflows/
  mcp: ✅          # MCP supported — .antigravity/mcp.json or ~/.gemini/antigravity/mcp_config.json
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-antigravity

Activate for: setting up Google **Antigravity** in a gald3r project, wiring MCP servers, authoring
the project `AGENTS.md`, creating Antigravity workflows (slash commands), or answering questions
about Antigravity's gald3r-relevant capabilities.

> **⚠️ VOLATILE PLATFORM — needs SCAN_DOCS.** Google Antigravity 2.0 relaunched on/around
> **2026-05-19** as an agent-first platform (desktop IDE + CLI + SDK + Managed Agents API +
> enterprise tier). Its config surface changed materially from the pre-2.0 product. Most gald3r
> primitive mappings below are **UNVERIFIED** (`❓`) and were authored conservatively from public
> guides, not from a live install. **Run `@g-platform-scan-docs antigravity` (or
> `g-skl-platform-monitor SCAN_DOCS antigravity`) and an install test before trusting any `❓`/`⚠️`
> cell.** Do NOT copy assumptions from the Cursor reference.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://antigravity.google/docs/home
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://antigravity.google/docs/home
   → READ new vault notes at research/platforms/antigravity/
   → UPDATE sections "Platform Overview", "Supported Primitives", "Known Gaps"
4. Else: proceed with current content
```

The Antigravity docs site is heavily JS-rendered; a headless/dynamic crawl (g-skl-recon-url) may
be required where g-skl-recon-docs returns only the page title.

---

## 1. Platform Overview

**Google Antigravity** is an **agent-first** development platform (not just an AI-assisted IDE).
Antigravity 2.0 (May 2026) ships five surfaces:

- **Desktop IDE** — runs dynamic subagents in parallel, schedules background tasks, accepts voice commands
- **CLI** — `antigravity` command-line entry point
- **SDK** — programmatic agent orchestration
- **Managed Agents** — a tier inside the Gemini API
- **Enterprise** — via the Gemini Enterprise Agent Platform

Backed by Gemini models. Security model centers on **Trusted Workspaces** (workspace-scoped file
access, terminal sandbox, terminal-command auto-execution policy, artifact review policy, browser
URL allow-list).

**gald3r target tier**: NEW integration (T1465). Treated as a first-time platform — no prior
gald3r state is assumed.

---

## 2. Folder Layout (PARTIALLY VERIFIED — confirm via SCAN_DOCS)

```
<project_root>/
├── AGENTS.md                         ← ✅ project-root instruction file (Antigravity reads this)
└── .antigravity/
    └── mcp.json                      ← ✅ MCP server config ({ "mcpServers": { ... } })

~/.gemini/antigravity/                ← user-global Antigravity state (Gemini-namespaced)
├── global_workflows/                 ← ✅ saved-prompt workflows = slash commands (invoked with /)
└── mcp_config.json                   ← ✅ alternate global MCP config location (same mcpServers shape)
```

| Path | Status | Notes |
|---|---|---|
| `AGENTS.md` (project root) | ✅ | The instruction file Antigravity reads. gald3r already generates `AGENTS.md`. |
| `.antigravity/mcp.json` | ✅ | Project-local MCP config. Some installs use the global path instead. |
| `~/.gemini/antigravity/mcp_config.json` | ✅ | Global MCP config (Settings → Customizations → "Open MCP Config"). |
| `~/.gemini/antigravity/global_workflows/` | ✅ | Stores saved-prompt workflows invoked as `/` slash commands. |
| `.antigravity/rules/` or always-apply rule dir | ❓ | NOT confirmed. No documented Cursor-`.mdc`-style always-apply rules folder found. |
| `.antigravity/skills/` (folder-per-skill) | ❓ | NOT confirmed. No documented `SKILL.md` auto-discovery mechanism found. |
| `.antigravity/agents/` (gald3r `g-agnt-*`) | ❓ | Antigravity has a native subagent concept, but file-based `g-agnt-*.md` discovery is unconfirmed. |
| hooks / lifecycle wiring | ❓ | No native hook config file (`hooks.json` equivalent) documented. |

---

## 3. Supported Primitives (gald3r capability map)

| gald3r primitive | Antigravity mechanism | Location | Status |
|---|---|---|---|
| AI instruction file | `AGENTS.md` | project root | ✅ Confirmed |
| MCP servers | `mcpServers` JSON | `.antigravity/mcp.json` or `~/.gemini/antigravity/mcp_config.json` | ✅ Confirmed |
| Commands / workflows | saved-prompt workflows, `/`-invoked | `~/.gemini/antigravity/global_workflows/` | ⚠️ Confirmed mechanism, gald3r `g-*` mapping untested |
| Rules / memory | `AGENTS.md` (instructions); native "memories" via memories.sh MCP | project root / MCP | ⚠️ No dedicated always-apply `.mdc` rules dir confirmed |
| Skills (`g-skl-*/SKILL.md`) | none documented | — | ❓ Untested — likely a gap |
| Agents (`g-agnt-*.md`) | native subagents (not file-discovered) | — | ❓ Untested |
| Hooks (`g-hk-*.ps1`) | none documented | — | ❓ Likely a gap (run manually or via AGENTS.md guidance) |

---

## 4. AGENTS.md (the verified integration point)

`AGENTS.md` in the project root is the standard instruction file Antigravity reads at session
start. This is gald3r's primary, confirmed wiring point: gald3r already authors `AGENTS.md`, so the
baseline integration (mission, rules pointer, task-location pointer) works out of the box.

Because gald3r's per-file rules/skills/agents discovery is **not** confirmed on Antigravity, the
pragmatic v1 approach is: fold the essential always-apply rule guidance into `AGENTS.md` (or the
gald3r-lite trim from `g-skl-platform-cursor` §"gald3r-lite context mode") until per-file rule
discovery is verified.

---

## 5. MCP Configuration (verified)

Antigravity supports MCP. Two locations (install-dependent):

```json
// .antigravity/mcp.json  (project-local)  OR  ~/.gemini/antigravity/mcp_config.json (global)
{
  "mcpServers": {
    "server-name": {
      "command": "...",
      "args": ["..."]
    }
  }
}
```

- UI path: **Settings → Customizations → Open MCP Config**.
- **Trusted Workspaces security** (v1.20.5+): only enable write-capable MCP servers in repos you own.

---

## 6. Workflows / Slash Commands (verified mechanism)

Antigravity "workflows" are **saved prompts** triggered with `/` in agent chat, stored at
`~/.gemini/antigravity/global_workflows/`. This is the nearest analogue to gald3r `@g-*` commands.

- ⚠️ The exact file format and whether gald3r can drop `g-*` command files into
  `global_workflows/` to expose them as `/g-*` is **UNTESTED**. Verify via SCAN_DOCS + install test.

---

## 7. Vault Doc Location

```
{vault_location}/research/platforms/antigravity/
```

Crawl entry point: `https://antigravity.google/docs/home`
Secondary: `https://codelabs.developers.google.com/getting-started-google-antigravity`

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Official docs | https://antigravity.google/docs/home |
| Getting-started codelab | https://codelabs.developers.google.com/getting-started-google-antigravity |
| MCP setup (community) | https://composio.dev/content/howto-mcp-antigravity |

---

## 9. Known Gaps vs. Cursor Reference

Honest, conservative gap list (feeds `PLATFORM_STATUS.md`). Use the decision tree in
`g-skl-platform-cursor/SKILL.md` §4a — each item below is either (b) a needed platform-specific
override or (c) a documented gap.

1. **Hooks — likely a GAP (❓).** No native hook/lifecycle config (`hooks.json` equivalent,
   `sessionStart`/`stop`/`preToolUse`) documented for Antigravity post-relaunch. gald3r hooks
   would run manually or be folded into `AGENTS.md` guidance until verified.
2. **Skills — likely a GAP (❓).** No documented folder-per-skill `SKILL.md` auto-discovery. gald3r
   `g-skl-*` content cannot be assumed to auto-load; may need to be referenced from `AGENTS.md`.
3. **Agents — UNTESTED (❓).** Antigravity has native **subagents**, but it is unconfirmed whether
   gald3r `g-agnt-*.md` files are discovered/loadable. The mechanism differs from Cursor's
   `.cursor/agents/` manual-select model.
4. **Always-apply rules — PARTIAL (⚠️).** Confirmed: `AGENTS.md`. NOT confirmed: a dedicated
   always-apply rules directory (Cursor `.mdc` analogue). gald3r `g-rl-*` always-apply guarantees
   may not hold beyond what `AGENTS.md` carries.
5. **Commands — PARTIAL (⚠️).** Workflow/slash mechanism exists (`global_workflows/`), but gald3r
   `g-*` → `/g-*` mapping is untested.
6. **Parity override dir.** `.gald3r_sys/platforms/.antigravity/` did not exist before T1465; create
   it for any genuinely platform-specific config (MCP defaults, AGENTS.md merge rules) and run
   `g-skl-platform-monitor VALIDATE antigravity` to flag Cursor-generic copies.
7. **Volatility.** Platform relaunched ~7 days before authoring; doc structure and config paths may
   shift again. Keep `crawl_max_age_days: 7` and re-scan before relying on any cell.

**Verified working (✅):** `AGENTS.md` instruction file; MCP server config.

---

## 10. Install Verification Checklist (to run after SCAN_DOCS)

```
✅ Project root has gald3r-generated AGENTS.md (instruction file is read)
✅ .antigravity/mcp.json OR ~/.gemini/antigravity/mcp_config.json has gald3r MCP servers
⚠️ ~/.gemini/antigravity/global_workflows/ — test exposing one g-* command as a /workflow
❓ rules auto-load — verify whether any always-apply mechanism exists beyond AGENTS.md
❓ skills auto-load — verify SKILL.md discovery (expected: none)
❓ agents — verify g-agnt-*.md discovery vs. native subagents
❓ hooks — verify any lifecycle/hook wiring exists (expected: none)
```

---

## 11. Self-Update Procedure

After each fresh crawl: read `research/platforms/antigravity/*.md`, then update §1, §2, §3, and §9
with verified capabilities and corrected file paths. Promote `❓`/`⚠️` cells to `✅`/`❌` ONLY with
recorded evidence (install test or specific doc citation) — never optimistically.
