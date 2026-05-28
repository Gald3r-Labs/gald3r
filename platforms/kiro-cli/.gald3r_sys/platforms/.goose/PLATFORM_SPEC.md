---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: goose
authoring_path: update
docs_url: https://block.github.io/goose/docs
docs_url_secondary:
  - https://block.github.io/goose/docs/guides/config-file/
  - https://block.github.io/goose/docs/getting-started/using-extensions/
  - https://block.github.io/goose/docs/guides/recipes/
  - https://block.github.io/goose/docs/mcp/skills-mcp/
  - https://block.github.io/goose/docs/experimental/subagents/
crawl_max_age_days: 14
vault_doc_path: research/platforms/goose/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Goose (Block)

**Goose** (by Block, fka Square — "codename goose") is an open-source, local-first AI developer
agent that runs in the terminal (CLI) and a desktop app. Its distinguishing trait is a **strong,
first-class MCP story**: every capability beyond the built-in tools is an **extension**, and every
extension is an MCP server. Goose has no Cursor-style `.mdc` rules, no native lifecycle-hook config
file, and no `g-*` slash-command registry — gald3r maps onto Goose primarily through `.goosehints`
(instructions/rules), config-declared MCP extensions, **recipes** (reusable workflows), and the
**Skills extension** (which discovers `SKILL.md` folders).

> **Authoring path: UPDATE** — `g-skl-platform-goose/SKILL.md` already ships. This spec records the
> verified/doc-confirmed findings and corrects stale content in that skill (the prior skill claimed
> `GOOSE.md` + `.goose/config.yaml` as the instruction/config surface; the actual Goose convention
> is `.goosehints` for instructions and `~/.config/goose/config.yaml` for config).

---

## 1. Folder Hierarchy

Goose is **global-config-first**: the primary config lives in the user's home directory, not the
repo. Project-scoped customization is via `.goosehints` and (for skills) a `.agents/skills/` tree.

```
~/.config/goose/
├── config.yaml             ← GLOBAL config: provider, model, enabled extensions (MCP servers)
└── (session / log state)

~/.config/agents/skills/    ← GLOBAL skills discovered by the Skills extension

<project-root>/
├── .goosehints             ← project-scoped instructions/rules (markdown-ish; auto-read) ❓ exact load order
└── .agents/skills/         ← PROJECT skills discovered by the Skills extension
    └── <name>/SKILL.md
```

- **gald3r writes**: `.goosehints` (project instructions/rules), and — if the Skills extension is
  enabled — copies of `g-skl-*/SKILL.md` into `.agents/skills/<name>/`. MCP extension entries are
  declared in `~/.config/goose/config.yaml` (global, machine-specific).
- **Goose owns**: the `~/.config/goose/` namespace, `config.yaml` schema, extension lifecycle, the
  Skills-extension discovery rules, and recipe execution.

> **Correction vs. prior SKILL.md**: there is **no** standard `GOOSE.md` or `.goose/config.yaml`
> project convention. Instructions go in `.goosehints`; config is `~/.config/goose/config.yaml`.

---

## 2. AI Instruction File

Goose reads **`.goosehints`** as project-specific instructions ("goosehints" — custom instructions
that customize Goose behavior for the project). This is the gald3r instruction-file target on Goose
(analogous to `AGENTS.md` / `CLAUDE.md` on other platforms, but Goose-specific in name).

- **Format**: plain text / markdown content; treated as appended instructions/context.
- **Location**: project root (`.goosehints`). A global hints mechanism also exists. ❓ Exact
  precedence between global and project hints not verified here — confirm via SCAN_DOCS.
- gald3r **generates** `.goosehints` with task-management conventions, commit format, and an MCP
  pointer. The legacy `GOOSE.md` text in the old SKILL.md is **not** an actual Goose convention.

---

## 3. Agents Support

- **Native concept**: Goose has **subagents** (experimental) — Goose itself decides when to spawn
  short-lived subagent instances to parallelize work; their lifecycle is auto-managed (spawn → run
  → cleanup, no manual intervention). There is **no** user-authored agent-definition file format
  equivalent to Cursor's `.cursor/agents/g-agnt-*.md`.
- **Discovery of gald3r agents**: ❌ No native load path. gald3r `g-agnt-*.md` files have no Goose
  ingestion mechanism. The closest fit is to express agent behavior as **recipes** (§5) or as
  instructions inside `.goosehints`.
- **Status**: ⚠️ partial — subagents exist but are platform-driven, not gald3r-authored agent files.
  gald3r's agent layer does not map cleanly.

---

## 4. Skills Support

- **Native concept**: Goose ships a **Skills extension** (MCP-based). When enabled, Goose
  **auto-discovers skills at startup** from `.agents/skills/` in the project directory and
  `~/.config/agents/skills/` globally.
- **Format**: folder-per-skill with a `SKILL.md` — the **same convention gald3r already uses**, so
  `g-skl-*/SKILL.md` is structurally compatible if copied into `.agents/skills/<name>/`.
- **Caveat**: skill discovery requires the **Skills extension to be installed/enabled** in
  `config.yaml`; it is not on by default. The discovery directory (`.agents/skills/`) differs from
  the gald3r canonical `skills/` tree, so a parity copy step is required.
- **Status**: ⚠️ partial — native skills exist and the `SKILL.md` format aligns, but discovery
  is in `.agents/skills/` (not the gald3r default path) and gated on the Skills extension. ❓ Not
  install-tested in this repo.

---

## 5. Commands / Workflows

- **No slash-command registry.** Goose has no `.cursor/commands/g-*.md`-style command directory and
  no `@g-*`/`/g-*` invocation surface.
- **Native equivalent = Recipes**: Goose **recipes** are reusable, shareable YAML workflow templates
  (with parameters); **sub-recipes** compose them for specialized multi-step tasks. This is the
  correct mapping target for gald3r commands/workflows on Goose.
- **gald3r mapping**: gald3r `g-*` commands (markdown) are **not** executable on Goose as-is. They
  would need to be re-expressed as recipe YAML to run natively. Otherwise they are reference-only
  prose a user runs by describing the intent.
- **Status**: ⚠️ partial — recipes provide a genuine workflow primitive, but gald3r's markdown
  command files do not auto-port; manual recipe authoring required.

---

## 6. Hooks System

- **No native lifecycle-hook config file.** Goose does **not** expose a Cursor-style `hooks.json`
  with `sessionStart` / `stop` / `preToolUse` / `beforeShellExecution` events, nor a settings-based
  hook wiring. gald3r's PowerShell hooks (`g-hk-*.ps1`) have **no automatic firing mechanism** on
  Goose.
- **Closest analogues** (not equivalent): the **Extension Allowlist** (admin control over which MCP
  servers may install) is a security gate, not a per-event hook; subagent spawning is
  platform-driven, not user-hookable.
- **gald3r impact**: session-start context injection, agent-complete, pre-commit, and shell-guard
  hooks must run **manually** or be wrapped into a recipe/extension — they do not auto-fire.
- **Status**: ❌ not supported (no native hook events). ❓ Whether any 2026 Goose release adds an
  event/hook surface should be confirmed by SCAN_DOCS.

---

## 7. Rules / Memory

- **Mechanism**: `.goosehints` is the persistent-rules surface — project instructions Goose loads
  as context. There is **no** `.mdc` extension, **no** `alwaysApply:`/`globs:` frontmatter scoping,
  and **no** per-file rule auto-load like Cursor's `.cursor/rules/`.
- **gald3r mapping**: gald3r rules (`g-rl-*.md`) are concatenated/summarized into `.goosehints`
  rather than dropped as individual scoped rule files. All-or-nothing context injection — no
  glob-scoped activation.
- **Durable memory**: gald3r's own `.gald3r/learned-facts.md` remains the cross-session fact store;
  Goose has session/recipe state but no gald3r-specific rule-memory beyond `.goosehints` content.
- **Status**: ⚠️ partial — `.goosehints` works as a single instruction blob, but the granular
  always-apply / glob-scoped rule model does not exist.

---

## 8. MCP Support

- **Supported**: ✅ **Yes — first-class and central.** In Goose, **extensions ARE MCP servers**.
  Goose supports stdio and remote (SSE/HTTP) MCP servers and connects to many model providers.
- **Config format/location**: declared under `extensions:` in `~/.config/goose/config.yaml`
  (global, machine-specific), and managed interactively via `goose configure`. A built-in
  **Developer** MCP extension is enabled by default on install.
- **Server discovery / governance**: extensions are enabled in config; an admin **Extension
  Allowlist** can restrict which MCP servers may be installed.
- **gald3r mapping**: the gald3r MCP server is added as a Goose extension in `config.yaml`
  (stdio or remote URL). This is the strongest, best-supported integration surface on Goose.
- **Status**: ✅ verified at the doc/mechanism level (MCP is the platform's core extension model);
  ❓ active gald3r-MCP-as-extension connection not install-tested in this repo.

---

## 9. Known Gaps vs. Cursor Reference

Per the Common-vs-Platform-Specific decision tree (`g-skl-platform-cursor/SKILL.md`):

1. **Hooks ❌** — no native lifecycle-hook config (`hooks.json` analogue). gald3r `g-hk-*.ps1` do
   not auto-fire. Session-start/agent-complete/pre-commit/shell-guard behavior is manual or must be
   wrapped into a recipe/extension. → documented gap.
2. **Agents ⚠️/❌** — no user-authored agent-definition file format. Goose **subagents** are
   platform-spawned and experimental; gald3r `g-agnt-*.md` files have no load path. → map to recipes
   or `.goosehints`.
3. **Commands ⚠️** — no slash-command registry. gald3r `g-*` markdown commands are not executable;
   the native equivalent is **recipes** (YAML), requiring manual authoring per command. → gap (no
   auto-port).
4. **Rules ⚠️** — no `.mdc`, no `alwaysApply:`/`globs:` scoping. Rules collapse into a single
   `.goosehints` blob (all-or-nothing context). → partial.
5. **Skills ⚠️** — native Skills extension uses the **same `SKILL.md` folder format** ✅ but
   discovers from `.agents/skills/` (not gald3r's canonical `skills/`) and is **gated on the Skills
   extension being enabled**, not on by default. → needs platform-specific parity copy +
   extension-enable step. ❓ not install-tested.
6. **MCP ✅** — Goose's strongest surface; MCP is the core extension model. Belongs in
   platform-specific config (`~/.config/goose/config.yaml`), machine-specific.
7. **Instruction file** — Goose uses **`.goosehints`** (not `AGENTS.md`/`GOOSE.md`). Prior SKILL.md
   referenced a nonexistent `GOOSE.md` / `.goose/config.yaml` convention — corrected here.
8. **SCAN_DOCS not yet run** — `last_doc_scan: never`. Exact `.goosehints` load precedence, any
   2026 hook/event additions, and the precise Skills-extension discovery contract should be
   confirmed by `@g-platform-scan-docs goose` against https://block.github.io/goose/docs.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

`Docs Fresh = ❓` because `last_doc_scan: never` — flip to ✅ after the first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| MCP / extensions | Doc citation — Goose docs: extensions are MCP servers; `extensions:` in `~/.config/goose/config.yaml`; built-in Developer MCP enabled by default; Extension Allowlist (block.github.io/goose/docs) |
| Instruction file (`.goosehints`) | Doc citation — goosehints are project-specific instructions that customize Goose behavior (block.github.io/goose/docs) |
| Config location | Doc citation — Configuration File guide: `~/.config/goose/config.yaml` (block.github.io/goose/docs/guides/config-file) |
| Skills extension | Doc citation — Skills extension auto-discovers from `.agents/skills/` (project) + `~/.config/agents/skills/` (global), folder-per-`SKILL.md` (block.github.io/goose/docs/mcp/skills-mcp) |
| Recipes / sub-recipes | Doc citation — reusable/shareable YAML workflow templates with parameters; sub-recipes compose them (block.github.io/goose/docs/guides/recipes) |
| Subagents | Doc citation — experimental; Goose auto-decides spawning + lifecycle (block.github.io/goose/docs/experimental/subagents) |
| Hooks | Absence-of-evidence — no lifecycle-hook config documented; marked ❌ pending SCAN_DOCS |
| Install / live connection | ❓ Not install-tested in this repo; no live Goose run performed |
