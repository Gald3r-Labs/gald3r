---
subsystem_memberships: [PLATFORM_INTEGRATION]
spec_for: antigravity
---

# PLATFORM_SPEC.md — antigravity (Google Antigravity)

> **Authoring path: CREATE** (T1465). There was NO pre-existing `g-skl-platform-antigravity/`.
> This spec accompanies a newly scaffolded `g-skl-platform-antigravity/SKILL.md`.
>
> **⚠️ VOLATILE. Partially web-verified (T1512, 2026-05-27), NOT install-verified.** Google
> Antigravity 2.0 launched at I/O 2026 (**2026-05-19**) and **replaces Gemini CLI** (Gemini CLI
> consumer/free tiers stop serving **2026-06-18**). A T1512 web-doc scan (sources at bottom)
> **confirmed from multiple 2026 secondary sources**: CLI command **`agy`** (Go, closed-source),
> instruction file **`AGENTS.md`** (`GEMINI.md` also works), workspace config dir **`.agents/`**,
> **Agent Skills**, **JSON lifecycle hooks**, and **dynamic subagents**. Remaining `❓` items
> require `@g-platform-scan-docs antigravity` + a live install test. Do NOT fabricate specifics.

---

## Header / Metadata

```yaml
platform: antigravity
authoring_path: create               # antigravity (T1465) — no existing skill
docs_url: https://antigravity.google/docs/home
docs_url_secondary: https://codelabs.developers.google.com/getting-started-google-antigravity
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
last_doc_scan: 2026-05-27             # T1512 web-doc scan (secondary sources); live install test still pending
cli_command: agy                     # T1512: Antigravity CLI binary is `agy` (Go, closed-source) ❓ install-untested
reference: g-skl-platform-cursor
status: ⚠️                           # partial — AGENTS.md/MCP/skills/hooks/subagents web-verified; install test pending
```

> `docs_url:` is co-located in `g-skl-platform-antigravity/SKILL.md` frontmatter so
> `g-skl-platform-monitor SCAN_DOCS` knows what to crawl.

---

## 1. Folder Hierarchy

> **T1512 correction (2026-05-27):** the **Antigravity CLI (`agy`)** uses **`.agents/`** as its
> per-workspace config dir, NOT `.antigravity/`. `.antigravity/` was the earlier T1465 assumption.
> The Gemini-namespaced `~/.gemini/...` global tree is confirmed; the exact global subpaths differ
> between sources (`~/.gemini/skills/`, `~/.gemini/config/mcp_config.json`, and
> `~/.gemini/antigravity-cli/` are all cited) — marked `❓` until install-verified.

```
<project_root>/
├── AGENTS.md                  ← ✅ project-root instruction file (GEMINI.md also still works)
└── .agents/                   ← ✅ per-workspace Antigravity CLI config dir (was assumed .antigravity/)
    ├── skills/                ← ✅ per-workspace Agent Skills (migrated from .gemini/skills/)
    │   └── <name>/SKILL.md    ← ❓ folder-per-skill SKILL.md (one source) vs flat <name>.md (another)
    └── (mcp_config.json / hooks config — exact in-workspace path ❓)

~/.gemini/                     ← ✅ Gemini-namespaced global state shared across Antigravity tools
├── skills/<name>/SKILL.md     ← ✅ global shared Agent Skills (❓ exact path: also ~/.gemini/antigravity-cli/skills/)
├── config/mcp_config.json     ← ✅ shared MCP config (❓ some sources say ~/.gemini/antigravity-cli/)
└── antigravity-cli/           ← ✅ CLI-specific state (conversations, settings)
```

- **gald3r writes**: `AGENTS.md` (already generated). Skills now have a real target: **`.agents/skills/`**.
- **Platform owns**: `~/.gemini/` global state, IDE settings, subagent runtime, hook execution.
- **✅ NOW CONFIRMED (web, T1512)**: Agent Skills (`.agents/skills/`), JSON lifecycle hooks, dynamic
  subagents (`/agent`), MCP via `mcp_config.json`.
- **❓ STILL UNCONFIRMED**: exact skill file shape (folder vs flat `.md`), always-apply rules dir,
  in-workspace hooks-config path, exact global subpaths. Verify on live install.

## 2. AI Instruction File

✅ **`AGENTS.md`** in the project root is the standard instruction file Antigravity reads.
This is the verified, primary gald3r integration point — gald3r already authors `AGENTS.md`, so
mission + rule-pointer + task-location-pointer wiring works without platform-specific changes.
Format: standard markdown. gald3r **generates** it (shared `AGENTS.md`, not Antigravity-bespoke).

## 3. Agents Support

⚠️ **Subagents confirmed (T1512); file-based agent discovery still ❓.** Antigravity CLI runs native
**dynamic subagents** spawned via the **`/agent`** command for parallel/async work — confirmed by
multiple 2026 sources. However, there is still **no documented mechanism for loading file-based
`g-agnt-*.md` definitions** (unlike Cursor's `.cursor/agents/` manual-select model); the native
subagent concept is runtime-spawned, not file-defined. Verify whether any `.agents/agents/` path is
honored during install test. Until then, fold critical agent guidance into `AGENTS.md` / skills.

## 4. Skills Support

✅ **Now web-confirmed (T1512) — a major improvement over Gemini CLI (which had NO skills).**
Antigravity CLI has **Agent Skills** stored per-workspace at **`.agents/skills/`** and globally at
`~/.gemini/skills/` (❓ some sources cite `~/.gemini/antigravity-cli/skills/`). Skills surface as
**slash commands** (one source: a markdown file at `.agents/skills/lint.md` becomes `/lint`; the
Google Cloud Community source describes folder-per-skill `<name>/SKILL.md`). **❓ exact file shape
(flat `<name>.md` vs folder `<name>/SKILL.md`) conflicts between sources — verify on install.**
For gald3r this means `g-skl-*` content has a **real native target** for the first time on this
platform family; migrating gald3r skills into `.agents/skills/` is now viable (was instruction-only).

## 5. Commands / Workflows

⚠️→✅ **Custom commands now come from Agent Skills.** Built-in slash commands include `/help`,
`/context`, `/usage`, `/export`, `/model`, and `/agent`; **custom commands are defined as Agent
Skills** (see §4) rather than a separate `global_workflows/` prompt store. (The earlier T1465
`~/.gemini/antigravity/global_workflows/` claim is **superseded** by the skills-as-commands model
per T1512 sources.) gald3r `g-*` commands can map to `/g-*` via `.agents/skills/`. **❓ exact
skill→slash-command naming + whether legacy `.gemini/commands/*.toml` TOML still loads — verify.**

## 6. Hooks System

✅ **Now web-confirmed (T1512) — another major improvement over Gemini CLI (which had NO hooks).**
Antigravity CLI supports **JSON-defined lifecycle hooks** that fire at specific moments: **before a
tool call, after a file edit, and on session start** (described as "the same JSON hook format
introduced in Antigravity 2.0"). This gives gald3r a real firing surface for PCAC inbox checks,
session-start context injection, and pre-commit/pre-push gates — capabilities that were **manual-only**
on Gemini CLI. **❓ exact hook config file path/schema + whether PowerShell `g-hk-*.ps1` can be
invoked from a hook entry — verify on install.** (Antigravity also has security *policies* — terminal
auto-execution, sandbox, artifact review, browser URL allow-list — which are settings, not hooks.)

## 7. Rules / Memory

⚠️ **Partial.** Confirmed persistent-context mechanism: **`AGENTS.md`** (project-root instructions).
NOT confirmed: a dedicated always-apply rules directory analogous to Cursor's `.cursor/rules/*.mdc`.
Antigravity also supports **"memories"** (durable agent state), surfaced via the memories.sh MCP
server rather than a gald3r-style rules file. gald3r `g-rl-*` always-apply guarantees therefore may
not hold beyond whatever `AGENTS.md` carries. No documented extension/token/size limit found.
Verify whether any always-apply rule file/dir exists during SCAN_DOCS.

## 8. MCP Support

✅ **Yes — verified.** Config shape `{ "mcpServers": { ... } }` at one of (install-dependent):
- `.antigravity/mcp.json` (project-local), or
- `~/.gemini/antigravity/mcp_config.json` (global; **Settings → Customizations → Open MCP Config**).

Server discovery is via that JSON. **Trusted Workspaces** security (v1.20.5+): only enable
write-capable MCP servers in repositories you own. Timeout behavior: **❓ not documented** — verify.

## 9. Known Gaps vs. Cursor Reference

Per `g-skl-platform-cursor/SKILL.md` §4a decision tree, each Cursor-reference feature is (a) common,
(b) a platform-specific override, or (c) a documented gap here:

| Cursor-reference feature | Antigravity status (T1512 web scan) | Classification |
|---|---|---|
| Always-apply rules (`.mdc`) | ⚠️ only via `AGENTS.md`; no rules dir confirmed | (c) documented gap / partial |
| Skills (folder-per-skill `SKILL.md`) | ✅ `.agents/skills/` (file shape ❓ flat vs folder) | (b) platform-specific config |
| Agents (`g-agnt-*.md` files) | ⚠️ native `/agent` subagents ✅; file discovery still ❓ | (c) documented gap (file-based) |
| Commands (`@g-*`) | ✅ custom commands = Agent Skills → `/name`; mapping ❓ | (b) platform-specific override |
| Hooks (`hooks.json` + PS1) | ✅ JSON lifecycle hooks (before-tool/after-edit/session-start); PS1 invoke ❓ | (b) platform-specific config |
| MCP (`mcp.json`) | ✅ `mcp_config.json` (`url`→`serverUrl` for remote) | (b) platform-specific config |
| AI instruction file | ✅ `AGENTS.md` (project root; `GEMINI.md` also works) | (a) common (gald3r already generates) |

**Needs SCAN_DOCS**: every `❓`/`⚠️` cell above. The parity override dir
`.gald3r_sys/platforms/.antigravity/` did not exist before T1465 — create it for genuinely
platform-specific config and run `g-skl-platform-monitor VALIDATE antigravity` to catch
Cursor-generic copies.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.
(Docs Fresh ⚠️ = web-doc scanned 2026-05-27 via secondary sources; still no live install test.)

---

## Verification Evidence (T1512 web scan, accessed 2026-05-27)

| Capability | Status | How verified (source URL + access date 2026-05-27) |
|---|---|---|
| Replaces Gemini CLI; EOL 2026-06-18 | ✅ | developers.googleblog.com "Transitioning Gemini CLI to Antigravity CLI"; theregister.com 2026-05-20; techcrunch.com 2026-05-19 |
| CLI command `agy`, Go, closed-source | ✅(secondary) | buildfastwithai.com guide; dev.to/arindam_1729 hands-on guide; techcrunch.com (Go) |
| AGENTS.md instruction file (GEMINI.md still works) | ✅ | buildfastwithai.com guide; aimadetools.com migration guide ("GEMINI.md and AGENTS.md continue to work… no modifications") |
| Workspace config dir `.agents/` (skills migrate from `.gemini/skills/`) | ✅ | aimadetools.com ("mv .gemini/skills/ .agents/skills/"); dev.to hands-on guide |
| Agent Skills → slash commands | ✅ | dev.to (".agents/skills/lint.md → /lint"); medium.com Google Cloud Community (folder-per-skill `SKILL.md`) — file shape conflicts ❓ |
| JSON lifecycle hooks (before-tool/after-edit/session-start) | ✅(secondary) | dev.to hands-on guide; search excerpt "same JSON hook format introduced in Antigravity 2.0" |
| Dynamic subagents (`/agent`) | ✅(secondary) | dev.to hands-on guide; marktechpost.com 2026-05-19 |
| MCP `mcp_config.json` (`url`→`serverUrl` remote) | ✅(secondary) | aimadetools.com migration guide; medium.com Google Cloud Community (`~/.gemini/config/mcp_config.json`) — exact global path conflicts ❓ |
| Always-apply rules dir | ⚠️ | AGENTS.md confirmed; no dedicated `.mdc`-style rules dir found in any source |
| Exact skill file shape / global paths | ❓ | Sources conflict (flat `.md` vs folder `SKILL.md`; `~/.gemini/skills/` vs `~/.gemini/antigravity-cli/skills/`) |

**Authoring note**: All ✅ cells rest on Google's official transition blog + multiple 2026 secondary
sources (no live install). Antigravity is **closed-source**, so no repo/source-of-truth crawl is
possible — secondary developer guides are the best available evidence. Promote remaining `❓`/`⚠️`
cells and resolve the file-shape/path conflicts ONLY after a live `agy` install test.

### Source URLs (accessed 2026-05-27)
- https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- https://techcrunch.com/2026/05/19/google-launches-antigravity-2-0-with-an-updated-desktop-app-and-cli-tool-at-io-2026/
- https://www.theregister.com/ai-ml/2026/05/20/bye-bye-gemini-cli-google-nudges-devs-toward-antigravity/5243605
- https://www.marktechpost.com/2026/05/19/google-launches-antigravity-2-0-at-i-o-2026-a-standalone-agent-first-platform-with-cli-sdk-managed-execution-and-enterprise-support/
- https://www.buildfastwithai.com/blogs/google-antigravity-2-0-developer-guide-2026
- https://dev.to/arindam_1729/antigravity-cli-a-hands-on-guide-to-googles-terminal-coding-agent-5bc7
- https://www.aimadetools.com/blog/migrate-gemini-cli-to-antigravity-cli/
- https://medium.com/google-cloud/configuring-mcp-servers-and-skills-for-antigravity-cli-and-ide-a938c7eebb78
