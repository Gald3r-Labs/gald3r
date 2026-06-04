---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: windsurf
authoring_path: update
docs_url: https://docs.windsurf.com
docs_url_secondary:
  - https://docs.windsurf.com/windsurf/cascade/memories
  - https://docs.windsurf.com/windsurf/cascade/workflows
  - https://docs.windsurf.com/windsurf/cascade/mcp
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1466
---

# PLATFORM_SPEC.md — Windsurf (by Codeium)

Windsurf is a VS Code-based AI-first IDE built around the **Cascade** agentic assistant. Like
Cursor it is a VS Code fork, so its surface area (rules, workflows, MCP, memories) is the closest
analog to the Cursor reference among the Tier 2 platforms. The two diverge meaningfully in rule
file format/location, the absence of a native skills folder, and the workflow-vs-command model.

**Authoring path**: UPDATE — `g-skl-platform-windsurf/SKILL.md` already ships. This spec records
the verified findings and the honest capability assessment that feeds `PLATFORM_STATUS.md`.

> **Verification caveat (read first)**: `last_doc_scan: never`. This spec is authored from prior
> Windsurf knowledge, the existing SKILL.md, and the existing `platforms/.windsurf/` deploy
> scaffold in this repo — NOT from a fresh `@g-platform-scan-docs windsurf` crawl, and no
> repo-root `.windsurf/` install was present to inspect at authoring time. Windsurf's rules system
> moved through several formats (legacy single-file `.windsurfrules` → `.windsurf/rules/*.md` with
> activation modes), and Cascade workflows/hooks are recent. Every capability not confirmable by a
> current doc citation or an install test is marked `❓`/`⚠️`. Do not promote to `✅` without
> dated evidence in the Verification Evidence section.

---

## 1. Folder Hierarchy

Windsurf reads configuration from a repo-root `.windsurf/` folder plus the legacy root file. There
was no installed `.windsurf/` in this repo at authoring time; the layout below reflects current
Windsurf docs + the gald3r deploy scaffold under
`gald3r_template/.gald3r_sys/platforms/.windsurf/`.

```
<project-root>/
├── .windsurfrules               ← LEGACY single-file project rules (still honored)        ⚠️
└── .windsurf/
    ├── rules/                   ← Current per-rule files (.md) with activation frontmatter ⚠️
    │   └── *.md
    └── workflows/               ← Cascade workflow files (.md, /slash-invoked)             ❓
        └── *.md
~/.codeium/windsurf/memories/    ← Global user rules + Cascade auto-generated memories (outside repo)
~/.codeium/windsurf/             ← Cascade MCP config home (mcp_config.json)                (see §8)
```

**gald3r writes vs. Windsurf owns:**
- gald3r writes/generates: `.windsurfrules` (always-apply rule subset), and on the current rules
  model can also emit `.windsurf/rules/*.md`. The deploy scaffold ships `.windsurfrules` +
  `windsurf_instructions.md` + `README.md`.
- Windsurf owns: the `.windsurf/` namespace, the rule activation-mode schema, Cascade's memory
  store under `~/.codeium/windsurf/`, and the workflow `/`-invocation mechanism.
- **No `.windsurf/skills/`, `.windsurf/agents/`, `.windsurf/commands/`, or `.windsurf/hooks/`**
  paths — Windsurf has no native equivalent of those Cursor folders (see §3–§6).

---

## 2. AI Instruction File

Windsurf does **not** read `AGENTS.md`/`CLAUDE.md` as a primary instruction file the way the
agent-convention platforms do. Its persistent-instruction surface is the **rules** system:

- **`.windsurfrules`** (project root) — the legacy single-file always-apply instruction file.
  Plain Markdown, no frontmatter required; auto-injected into Cascade context. Still honored by
  current Windsurf. This is what the gald3r deploy scaffold ships. ⚠️ (works, but legacy)
- **`.windsurf/rules/*.md`** — the current per-rule model (see §7). Preferred going forward.
- **Global rules** — managed in Windsurf settings UI, stored under
  `~/.codeium/windsurf/memories/`. These can override project rules in some Cascade versions.

gald3r **generates/merges** `.windsurfrules` from its always-apply rule subset. Keep it lean
(historically ~6K char / ~8K token guidance for the Cascade context budget). gald3r does not
currently emit AGENTS.md-style coverage for Windsurf because Cascade does not consume it. ❓

---

## 3. Agents Support

- **Native concept**: Windsurf's agent **is Cascade** — a single built-in multi-step agent. There
  is **no project `agents/` folder** and **no multi-agent persona discovery** comparable to
  Cursor's `.cursor/agents/g-agnt-*.md`. ❌
- **gald3r `g-agnt-*.md`**: cannot be dropped into a Windsurf-native agents path (none exists).
  Agent personas can only be surfaced as *rule content* (summarized into `.windsurfrules` /
  `.windsurf/rules/`) so Cascade reasons with that context. There is no "select agent X" mechanic.
- **Comparison to Cursor**: Cursor loads named agent markdown and supports explicit agent
  selection; Windsurf collapses everything into one Cascade agent driven by injected rules. This
  is the key architectural gap — **agents are not a first-class primitive on Windsurf**. ❌

---

## 4. Skills Support

- **Native discovery**: Windsurf has **no native skills folder** equivalent to `.cursor/skills/`
  or `.claude/skills/`. Cascade does not auto-discover `SKILL.md` files. ❌
- **gald3r approach** (from existing SKILL.md): surface skill content via `.windsurfrules` (compact
  summaries) and reference skill names with `@mention`-style cues inside Cascade prompts. This is a
  manual, rule-injection workaround — not skill auto-loading. ⚠️
- The root `skills/` directory shipped by a gald3r install is therefore reference material for the
  human/agent, not a path Windsurf reads. ❌
- **Comparison to Cursor**: Cursor relevance-loads folder-per-skill `SKILL.md`. Windsurf has no
  parallel; skills degrade to rule-text summaries. Documented gap.

---

## 5. Commands / Workflows

Windsurf's closest analog to gald3r commands is **Cascade Workflows**:

- **Workflows** = `.windsurf/workflows/*.md` files describing a repeatable multi-step procedure,
  invoked in Cascade with a `/`-style slash trigger (e.g. `/deploy`). They are series-of-steps
  prompts, not a programmable command namespace. ❓ (mechanism known from docs; not install-tested
  here — no `.windsurf/workflows/` present in this repo)
- gald3r's `@g-*` / `/g-*` command files are **not natively executable** on Windsurf. They could be
  hand-translated into workflow files, but the gald3r command set is not auto-mapped to workflows.
  As shipped, gald3r commands are reference docs for Windsurf, not runnable commands. ⚠️
- **Comparison to Cursor**: Cursor surfaces `.cursor/commands/g-*.md` via `@command-name`. Windsurf
  workflows are manual `/`-invoked prompt scripts with no 1:1 mapping to the gald3r command catalog.

---

## 6. Hooks System

- **Native lifecycle hooks**: Windsurf/Cascade has **no documented general-purpose lifecycle hook
  system** comparable to Cursor's `.cursor/hooks.json` (sessionStart/stop/preToolUse/
  beforeShellExecution). There is no `.windsurf/hooks/` path that runs gald3r's `g-hk-*.ps1`. ❌
- Newer Cascade releases have introduced limited automation/trigger features, but a stable,
  documented hook-wiring file that fires gald3r PowerShell hooks is **not** confirmed. Treat as
  `❓` pending a fresh doc crawl.
- **gald3r consequence**: gald3r hooks do **not** auto-fire on Windsurf. Hook behaviors (session
  context injection, pre-commit guard, etc.) must run **manually** or be approximated via rule text
  / git hooks (`core.hooksPath`), exactly as the deploy scaffold notes ("No lifecycle `hooks/`").
- **Comparison to Cursor**: Cursor has a verified native 4-event `hooks.json`. Windsurf has none
  for gald3r's purposes. This is a documented gap (❌/❓).

---

## 7. Rules / Memory

- **Legacy format**: `.windsurfrules` (project root), plain Markdown, no frontmatter, always
  injected into Cascade. Shipped by the gald3r deploy scaffold. ⚠️ (works; legacy)
- **Current format**: `.windsurf/rules/*.md` — one file per rule with **activation modes**
  (commonly: Always On, Manual, Model Decision, Glob). Extension is **`.md`** (vs. Cursor's
  `.mdc`); the parity sync maps the extension. The activation-mode frontmatter is the Windsurf
  analog of Cursor's `alwaysApply:` / `globs:` / `description:`. ⚠️ (exact frontmatter keys not
  re-verified against a current crawl — marked provisional)
- **Memories**: Cascade maintains an auto-generated **memory** store under
  `~/.codeium/windsurf/memories/` (persistent context Cascade writes/recalls across sessions), plus
  user-defined global rules in the same area. This is richer than Cursor's static rule injection
  but is Cascade-managed and not directly authored by gald3r. ❓
- **Size budget**: historically a ~6K character / ~8K token guidance per rules file for the Cascade
  context budget; keep `.windsurfrules` compact.
- **Comparison to Cursor**: same always-apply concept, different extension (`.md` not `.mdc`),
  different location (`.windsurf/rules/` not `.cursor/rules/`), plus a Cascade-managed memory layer
  Cursor lacks.

---

## 8. MCP Support

**Yes.** ✅ (mechanism) / ⚠️ (config path differs from Cursor).

- Cascade supports MCP (Model Context Protocol) servers. Config is JSON at
  `~/.codeium/windsurf/mcp_config.json` (and/or via Windsurf Settings → Cascade → MCP / a
  `Manage MCPs` UI). Servers are described with stdio `command`/`args`/`env` or http `serverUrl`.
- Servers auto-connect on Cascade startup once configured; the UI surfaces enabled servers.
- The config file name/location (`mcp_config.json` under `~/.codeium/windsurf/`) differs from
  Cursor's `.cursor/mcp.json`, so MCP is fully supported but **not single-path portable** — gald3r
  cannot ship one `mcp.json` that both Cursor and Windsurf read. ⚠️
- The exact tool-count/timeout limits were not re-verified against a current crawl. ❓

---

## 9. Known Gaps vs. Cursor Reference

Honest gap list (feeds `PLATFORM_STATUS.md` and the capability matrix). Decision-tree disposition
per `g-skl-platform-cursor` ((a) common `.gald3r_sys/`, (b) platform-specific config, (c) gap):

| Cursor-reference feature | Windsurf status | Disposition |
|---|---|---|
| Always-apply rules | ⚠️ `.windsurfrules` (legacy) / `.windsurf/rules/*.md` (current) | (b) generated per-platform |
| Per-rule files | ⚠️ `.windsurf/rules/*.md`, `.md` not `.mdc`, activation modes | (b) platform-specific |
| Persistent memory | ❓ Cascade-managed `~/.codeium/windsurf/memories/` (not gald3r-authored) | (c) Windsurf-only superset |
| Agents (named personas) | ❌ no agents folder — single Cascade agent only | (c) gap |
| Skills auto-discovery | ❌ no native skills path; rule-text summaries only | (c) gap |
| Slash commands (`g-*`) | ⚠️ no native exec; workflows are nearest analog, manual | (c) gap / (b) workflow translation |
| Workflows | ❓ `.windsurf/workflows/*.md`, `/`-invoked, not install-tested here | (b) platform-specific |
| Hooks (local PS1) | ❌/❓ no documented lifecycle hook file for gald3r hooks | (c) gap |
| MCP | ⚠️ supported via `~/.codeium/windsurf/mcp_config.json` (different path) | (b) platform-specific |

**Biggest honest gaps**: (1) **no agents folder** — Cascade is the only agent, gald3r personas
collapse to rule text; (2) **no native skills discovery** — skills degrade to `.windsurfrules`
summaries; (3) **no native lifecycle hook system** — gald3r hooks do not auto-fire; (4) commands
have no native runtime — workflows are a manual, non-mapped analog.

**Where Windsurf is strong**: rules injection (closest to Cursor of the Tier 2 platforms), a
Cascade-managed memory layer Cursor lacks, and full MCP support (different config path).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ⚠️ | ⚠️ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Rationale:
- **Hooks ❌** — no documented lifecycle hook wiring for gald3r `g-hk-*.ps1`; gald3r hooks run
  manually at best. (`❓` for any newer Cascade automation feature, but not usable as gald3r hooks.)
- **Rules ⚠️** — fully real, but split legacy `.windsurfrules` vs. current `.windsurf/rules/*.md`
  with activation modes; gald3r ships the legacy file. Different extension/location than Cursor.
- **Skills ❌** — no native skills discovery; only rule-text summarization.
- **Commands ⚠️** — no native command runtime; Cascade workflows are a manual, non-mapped analog.
- **MCP ⚠️** — supported, but config lives at a Windsurf-specific path (`mcp_config.json`), not
  portable from Cursor's `.cursor/mcp.json`.
- **Docs Fresh ❌** — `last_doc_scan: never`; no current crawl performed.

---

## Verification Evidence

| Capability | How assessed | Confidence |
|---|---|---|
| Folder hierarchy | Existing `platforms/.windsurf/` scaffold + Windsurf docs knowledge; no installed repo-root `.windsurf/` to `ls` | Medium |
| Rules (`.windsurfrules` / `.windsurf/rules/`) | Existing SKILL.md + scaffold + prior Windsurf knowledge; activation-mode keys not re-crawled | Medium |
| Memories | Prior knowledge of Cascade `~/.codeium/windsurf/memories/`; not gald3r-authored | Low-Medium |
| Agents | Architectural fact: Cascade is the single agent, no agents folder | High (negative) |
| Skills | Architectural fact: no native skills discovery on Windsurf | High (negative) |
| Commands / Workflows | Workflow mechanism known from docs; no `.windsurf/workflows/` present to test | Low-Medium |
| Hooks | No documented gald3r-usable lifecycle hook file; deploy scaffold confirms "No lifecycle hooks/" | Medium (negative) |
| MCP | Documented Cascade MCP support; config at `~/.codeium/windsurf/mcp_config.json` | Medium |

**No install test or live `@g-platform-scan-docs windsurf` crawl was run for this spec.** All
`❓`/`⚠️` ratings remain provisional until a fresh crawl (T1484 parity / a future SCAN_DOCS run)
records dated evidence here. Promote ratings only with citations.
