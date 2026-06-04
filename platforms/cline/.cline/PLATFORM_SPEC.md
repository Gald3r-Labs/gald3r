---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: cline
authoring_path: update
docs_url: https://docs.cline.bot
docs_url_secondary:
  - https://docs.cline.bot/features/cline-rules
  - https://docs.cline.bot/features/slash-commands/workflows
  - https://docs.cline.bot/mcp/configuring-mcp-servers
crawl_max_age_days: 14
vault_doc_path: research/platforms/cline/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1468
---

# PLATFORM_SPEC.md — Cline (VS Code extension)

Cline (formerly Claude Dev) is a popular open-source **VS Code extension** for agentic AI coding.
It pioneered the in-editor MCP marketplace and has a strong MCP story, a directory-based rules
system (`.clinerules/`), and a workflow-file mechanism that doubles as its only "command"-like
primitive. It has **no native hook system** and **no slash-command namespace** beyond workflows.

**Authoring path**: UPDATE — `g-skl-platform-cline/SKILL.md` already ships. This spec records the
verified findings and the honest capability assessment that feeds `PLATFORM_STATUS.md`.

> **Verification caveat (read first)**: `last_doc_scan: never`. This spec is authored from prior
> Cline knowledge and the existing SKILL.md, **not** from a fresh `@g-platform-scan-docs cline`
> crawl, and **no `.clinerules` / `.cline` config exists in this repo** to inspect (confirmed by
> repo scan — `glob **/.clinerules/**` returned nothing). Every capability that could not be
> confirmed by a current doc citation or an install test is marked `❓` (untested) or `⚠️`
> (partial / Cursor-generic). Do not promote `❓`/`⚠️` → `✅` without evidence recorded in the
> Verification Evidence section.

---

## 1. Folder Hierarchy

Cline supports **two rules layouts**. The modern, recommended one is a `.clinerules/` *directory*;
the legacy one is a single `.clinerules` *file*. There is no `.cline/` namespace analogous to
`.cursor/` — Cline reads from the repo root and from VS Code/global settings.

```
<project-root>/
├── .clinerules/                 ← (modern) rules DIRECTORY — every .md inside is auto-injected
│   ├── 01-coding.md             ← arbitrary file names; concatenated in order
│   ├── gald3r-rules.md          ← gald3r-authored always-apply rules
│   └── workflows/               ← workflow files (invoked as /<workflow-name>)   (see §5)
│       └── *.md
├── .clinerules                  ← (legacy) single rules FILE (use the directory form instead)
└── memory-bank/                 ← gald3r/Cline CONVENTION — persistent context (NOT auto-written)
    ├── projectbrief.md
    ├── activeContext.md
    └── progress.md

# Global / settings-managed (NOT in the repo tree):
~/Documents/Cline/Rules/         ← global rules folder (applies across all projects)   ❓ exact path
<VS Code globalStorage>/...      ← MCP server config (cline_mcp_settings.json)         (see §8)
```

**What gald3r writes vs. what Cline owns:**
- gald3r writes/generates: `.clinerules/` (or the legacy `.clinerules` file) from the always-apply
  rules subset, `.clinerules/workflows/*.md` (full/adv tiers), and the `memory-bank/` convention files.
- Cline owns: the *meaning* of `.clinerules/` (auto-injection), `workflows/` (slash invocation),
  the global rules folder, and the MCP settings file location.
- `memory-bank/` is a **prompt convention** (popularized by the Cline community), not a Cline-native
  auto-managed store. Cline *reads* it only because the rules tell it to; it does not auto-write it.

> **Correction vs. existing SKILL.md**: the SKILL.md documents only the single-file `.clinerules`
> and says "subdirectory rules are not supported." That is outdated — Cline now supports the
> `.clinerules/` **directory** form (multiple `.md` files concatenated) and a `workflows/`
> subfolder. The directory form is the recommended target. ⚠️ exact concatenation order untested.

---

## 2. AI Instruction File

Cline's primary persistent-instruction surface is the **rules** mechanism itself (§7), not a single
top-level `AGENTS.md`/`CLAUDE.md` file:

- **`.clinerules/` directory** (or legacy `.clinerules` file) — auto-injected into every Cline task
  in the project. This is the canonical instruction surface. ✅ (mechanism documented)
- Cline also exposes **Custom Instructions** in its VS Code settings UI (a global text box) — these
  apply across all projects and are managed in settings, not in the repo. ⚠️ not a file gald3r ships.
- **`AGENTS.md`**: Cline has been adding `AGENTS.md` awareness (the cross-tool convention), but
  coverage/version behavior is not confirmed by a current doc citation. ❓ Not relied upon by gald3r —
  `.clinerules/` is the documented, stable path.

gald3r **generates** the rules content from its always-apply rule subset; the file is personalized
and gitignored per `g-rl-02` protected-files policy. Keep the injected content lean (see §7 size note).

---

## 3. Agents Support

Cline has **no multi-agent / named-persona orchestration concept** comparable to the Cursor
reference's `g-agnt-*.md` files. Cline is a single agentic assistant driven by the active model.

- There is no `.clinerules/agents/` discovery path and no "select an agent by name" UI.
- gald3r `g-agnt-*.md` persona files **do not auto-load** on Cline. The only way their guidance
  reaches Cline is by inlining the relevant persona text into a rules file or a workflow.
- **Net**: agents are a documented gap. ❌ (no native concept) — gald3r agent personas degrade to
  "rules content" at best.

This is the key architectural difference vs. Cursor: Cursor reasons over a `.cursor/agents/` tree
with ambient persona selection; Cline has a single agent and no persona registry.

---

## 4. Skills Support

Cline has **no "skills" primitive** equivalent to Cursor's folder-per-skill `SKILL.md`
auto-discovery. There is no `.clinerules/skills/` path and no relevance-driven skill loader.

- gald3r `g-skl-*/SKILL.md` files are **not auto-discovered** by Cline. ❌
- The closest substitute is the **workflow** mechanism (§5): a skill's procedure can be transcribed
  into a `.clinerules/workflows/<name>.md` file and invoked as `/<name>`, but this is manual
  authoring per skill, not automatic discovery of the 110-skill gald3r library.
- **Net**: skills are a documented gap — ❌ for auto-discovery; ⚠️ only if individual skills are
  hand-ported to workflows.

---

## 5. Commands / Workflows

Cline's only command-like primitive is **Workflows** (`/` invocation):

- **Location**: `.clinerules/workflows/*.md` (project) or the global rules folder (`workflows/`). ⚠️
- **Invocation**: typing `/<workflow-filename>` in the Cline chat input runs that workflow's
  Markdown as a scripted prompt/procedure. This is the documented Cline slash mechanism.
- Cline also has a small set of **built-in slash controls** (e.g. `/newtask`, `/smol`/compact,
  `/reportbug`) that operate on Cline itself — these are NOT user-extensible command files. ⚠️
- gald3r's `@g-*` / `/g-*` command library (174 command files on Cursor) is **not natively
  executable** on Cline. Individual commands can be hand-ported to `workflows/*.md` and then run as
  `/<name>`, but there is no bulk discovery of the gald3r command namespace. ⚠️ partial.

**Net**: workflows give Cline a *real but manual* command analog. gald3r command parity is partial:
a curated subset can be shipped as workflow files; the full namespace cannot be auto-mounted. ⚠️

---

## 6. Hooks System

Cline has **no native lifecycle hook system.** ❌

- There is no `hooks.json`, no settings entry for `sessionStart`/`stop`/`preToolUse`, and no
  documented way to register a script that fires on Cline task lifecycle events.
- gald3r's Cursor-style hooks (`g-hk-*.ps1` + `hooks.json` wiring) **do not run on Cline.** Any
  gald3r behavior that depends on hooks (session-start context injection, pre-tool guard, agent-
  complete logging) must instead be expressed as **rules text** (so the model performs it) or run
  manually / out-of-band (e.g. via git hooks or a separate scheduler).
- This is a hard gap vs. the Cursor reference. ❌

> If a future Cline release adds a hook/automation API, this section must be re-verified by a fresh
> SCAN_DOCS crawl before any rating moves off ❌.

---

## 7. Rules / Memory

- **Persistent rules** = `.clinerules/` directory (modern) or `.clinerules` file (legacy),
  auto-injected at the start of every Cline task in the project. ✅ (mechanism documented)
- **Directory form**: every `.md` in `.clinerules/` is concatenated and injected; this lets gald3r
  ship multiple focused rule files rather than one monolith. ⚠️ concatenation order/precedence untested.
- **Toggle**: Cline exposes a UI to enable/disable individual rule files and to switch between
  workspace and global rules. ⚠️ behavior known from prior use, not doc-cited here.
- **Extension**: `.md` (Cline), vs. Cursor's `.mdc`. The parity sync maps the extension; Cline has
  no frontmatter-driven `alwaysApply`/`globs` scoping — **all** rules in `.clinerules/` are
  effectively always-apply (no per-file glob scoping comparable to Cursor). ⚠️ this is a real
  behavioral difference, not a cosmetic one.
- **Memory Bank**: the community `memory-bank/` pattern (projectbrief/activeContext/progress) is a
  *prompted* convention, not a Cline-native persistent store. Cline reads it because a rule instructs
  it to; it does not auto-update it. ⚠️
- **Size note**: large injected rules compete for the model context window. The existing SKILL.md
  recommends keeping `.clinerules` concise (< ~4–8K tokens); honor that for consumer installs.

---

## 8. MCP Support

**Yes — and this is Cline's strongest capability.** ✅ Cline was an early, prominent MCP client and
ships an in-editor **MCP Marketplace** for one-click server installs.

- **Config format/location**: a JSON settings file managed by the extension —
  `cline_mcp_settings.json` under the VS Code extension's `globalStorage` (Cline also exposes an
  "Edit MCP Settings" / marketplace UI to manage it). ⚠️ exact globalStorage path is OS/VS-Code-
  version-dependent — confirm via the extension UI rather than hand-editing.
- **Schema**: standard MCP server entries — `command`/`args`/`env` for stdio servers, or `url` for
  remote/SSE servers, plus auto-approve and timeout settings per server.
- **Server discovery**: Cline auto-connects to configured servers and surfaces their tools/resources
  to the agent; the marketplace provides discoverable installs.
- **Cline can also create MCP servers on request** (a documented feature) — beyond gald3r's needs
  but notable.
- **Net**: MCP is fully supported and well-developed. ✅ (mechanism) — the active server *set* is
  per-machine and not committed, so concrete servers are untested in CI (`❓` for the live set).

---

## 9. Known Gaps vs. Cursor Reference

Honest gap list (feeds `PLATFORM_STATUS.md` and the capability matrix). Decision-tree disposition
per `g-skl-platform-cursor` ((a) common `.gald3r_sys/`, (b) platform-specific config, (c) gap):

| Cursor-reference feature | Cline status | Disposition |
|---|---|---|
| Always-apply rules | ✅ `.clinerules/` dir or legacy file, auto-injected | (b) generated per-platform |
| Per-rule glob scoping (`globs:`) | ❌ no `alwaysApply`/`globs` frontmatter — all rules always-apply | (c) gap (behavioral) |
| Per-rule `.mdc` files | ⚠️ `.md` in `.clinerules/` dir; multiple files OK, no scoping | (b) extension-mapped |
| Skills auto-discovery | ❌ no skills primitive; manual port to workflows only | (c) gap |
| Agents (ambient persona) | ❌ single agent, no persona registry | (c) gap |
| Slash commands (`g-*`) | ⚠️ Workflows (`/<name>`) — manual port of a curated subset | (b) full/adv tier |
| Hooks (local PS1 + hooks.json) | ❌ no native hook system at all | (c) gap |
| MCP | ✅ strong (marketplace, stdio + remote); per-machine server set | (b) platform-specific |
| Memory / persistent context | ⚠️ `memory-bank/` is a prompted convention, not native | (b) convention |

**Biggest honest gaps**: (1) **no hook system** — all hook-driven gald3r behavior must become rules
text or run out-of-band; (2) **no skills and no agents** primitives — gald3r's skill/agent libraries
do not auto-mount; (3) **no per-rule glob scoping** — `.clinerules/` is always-apply only.
**Cline's standout strength is MCP** (marketplace + stdio/remote), which is on par with or ahead of
the Cursor reference.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ❌ | ⚠️ | ✅ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Rationale:
- **Hooks ❌** — Cline has no native lifecycle hook system; gald3r hooks do not run.
- **Rules ✅** — `.clinerules/` (dir or file) auto-injection is documented and stable (no glob scoping).
- **Skills ❌** — no skills primitive; gald3r `SKILL.md` files are not auto-discovered.
- **Commands ⚠️** — Workflows (`/<name>`) cover a manually-ported subset; no namespace auto-mount.
- **MCP ✅** — strong, documented support (marketplace, stdio + remote); live server set per-machine.
- **Docs Fresh ❌** — `last_doc_scan: never`; no current crawl performed.

---

## Verification Evidence

| Capability | How assessed | Confidence |
|---|---|---|
| Folder hierarchy | Prior Cline knowledge (`.clinerules/` dir + legacy file + `workflows/`); existing SKILL.md; no repo config to inspect (`glob **/.clinerules/**` = none) | Medium |
| Rules (`.clinerules/`) | Documented Cline rules feature (dir + legacy file forms); long-known mechanism | High (doc-backed) |
| Per-rule glob scoping absent | Architectural fact: Cline rules have no `alwaysApply`/`globs` frontmatter | Medium-High (negative) |
| Skills | Architectural fact: Cline has no skills/`SKILL.md` discovery | High (negative) |
| Agents | Architectural fact: Cline is single-agent, no persona registry | High (negative) |
| Commands / Workflows | Documented Cline workflows + built-in slash controls (`/newtask` etc.) | Medium |
| Hooks | Architectural fact: Cline has no documented hook/lifecycle API | High (negative) |
| MCP | Well-documented Cline strength (MCP marketplace, stdio + remote, settings JSON) | High |
| Docs freshness | Not verified — `last_doc_scan: never` | n/a |

**No install test or live `@g-platform-scan-docs cline` crawl was run for this spec, and no
`.clinerules`/`.cline` config exists in this repo to inspect.** All `❓`/`⚠️` ratings remain
provisional until a fresh crawl (T1484 parity / a future SCAN_DOCS run) records dated evidence here.
Promote ratings only with citations. Specifically re-verify: `.clinerules/` directory concatenation
order, the global rules folder path, the `cline_mcp_settings.json` location, and any `AGENTS.md` /
hook support added in newer Cline releases.
