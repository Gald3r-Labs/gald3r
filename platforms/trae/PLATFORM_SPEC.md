---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: trae
authoring_path: rewrite
docs_url: https://docs.trae.ai
docs_url_secondary:
  - https://docs.trae.ai/ide/rules?_lang=en
  - https://docs.trae.ai/ide/skills
  - https://docs.trae.ai/ide/best-practice-for-how-to-write-a-good-skill
  - https://docs.trae.ai/ide/agent
  - https://docs.trae.ai/ide/custom-agents-ready-for-one-click-import
  - https://docs.trae.ai/ide/solo-mode
  - https://docs.trae.ai/ide/models
crawl_max_age_days: 14
vault_doc_path: research/platforms/trae/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — TRAE (ByteDance AI-native IDE)

TRAE is ByteDance's AI-native IDE, shipping in two surfaces: **IDE Mode** (chat + custom agents) and
**SOLO Mode** (autonomous planning-through-deployment agent). The international edition (`trae.ai`)
and the China edition (`trae.cn` / `.trae-cn`) **share project-level `.trae/` paths** but use separate
global paths. As of mid-2026 TRAE natively supports **rules, agents, Agent Skills, and MCP**; custom
slash commands are **partial** (only the built-in Spec Kit workflow + `@agent-name` routing, no
user-defined slash-command file primitive); and **lifecycle hooks are not supported at all**.

**Authoring path**: REWRITE (created from the 2026-06-02 crawl assessment). **Verified 2026-06-02**
against https://docs.trae.ai (see Verification Evidence). MCP and the `.rules` mechanism landed in
**Trae IDE v1.3.0**; Skills (the `SKILL.md` Agent-Skills open standard) are present and in active use
by Q1 2026.

> **Instruction-file truth:** TRAE's first-class persistent-instruction surface is **`.trae/rules/`
> (`project_rules.md` + `user_rules.md`)** — **NOT** a root `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`.
> Third-party material references `AGENTS.md` in a TRAE context, but the official docs do **not**
> confirm `AGENTS.md` as a natively-read instruction file — treat that as **unknown/unverified**.
> For gald3r installs, target `.trae/rules/` for rules and `.trae/skills/<name>/SKILL.md` for skills.

> **Surface split:** IDE Mode and SOLO Mode share the same `.trae/` project tree. SOLO adds an
> autonomous end-to-end agent plus **time-based scheduled/automated tasks** (scheduling, not event
> hooks). Where a capability is SOLO-only it is noted inline.

---

## 1. Folder Hierarchy

```
<project-root>/
└── .trae/
    ├── rules/
    │   ├── project_rules.md      ← project-scope persistent instructions (#rulename)
    │   └── user_rules.md         ← user-scope persistent instructions
    └── skills/
        └── <name>/SKILL.md       ← Agent Skills (SKILL.md open standard) + scripts/ references/ assets/

~/.trae/rules/                    ← global user rules (international edition)
~/.trae-cn/rules/                 ← global user rules (China edition)
```

Custom agents and MCP servers are managed through **Settings > Rules & Skills** and the in-app
Skills/MCP marketplaces rather than committed config files. Trae and Trae CN **share the same local
`.trae/skills` and `.trae/rules` directories** at the project level.

**gald3r writes**: `.trae/rules/project_rules.md` (and `user_rules.md`), plus
`.trae/skills/<name>/SKILL.md` directories.
**TRAE owns**: the `.trae/` namespace, the Settings-managed agent/MCP registries, the Skills
Marketplace, and the SOLO automation surface.

---

## 2. AI Instruction File

TRAE has **no root agent-context file**. The native persistent-instruction layer is
**`.trae/rules/project_rules.md`** (project scope) and **`.trae/rules/user_rules.md`** (user scope),
with global rules at `~/.trae/rules/` (`~/.trae-cn/rules/` for the China edition). The Agent loads
`.rules` during the **initialization phase** and they shape generation thereafter. Rule files are
plain Markdown and can be invoked explicitly with `#rulename`.

No dedicated `TRAE.md` exists, and `AGENTS.md` / `CLAUDE.md` are **not confirmed** as natively read —
gald3r's `AGENTS.md`-centric install pattern must be translated into `.trae/rules/`.

---

## 3. Agents Support — ✅ NATIVE

- **Built-in agents**: Builder, Builder with MCP. **Custom Agents** = a custom system prompt + a
  selectable toolset + attached MCP servers (e.g. a "Documentation Agent"), invoked via
  **`@agent-name`** or from the chat dropdown. **Agents in TRAE act as MCP clients.**
- **One-click import/export** of custom agents (docs.trae.ai/ide/custom-agents-ready-for-one-click-import)
  — agents are shareable config bundles.
- **SOLO Mode** (SOLO Coder / SOLO Builder, `/solo-coder`) is an autonomous end-to-end agent that runs
  planning → deployment. Strong subagent/role support.
- gald3r `g-agnt-*` definitions map to TRAE Custom Agents (system prompt + toolset + MCP).
- Source: https://docs.trae.ai/ide/agent

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (the `SKILL.md` open standard — same format as Claude / Amp / gald3r) discovered in
  **`.trae/skills/<name>/SKILL.md`** (plus a global path). Frontmatter `name` + `description`, Markdown
  body, optional `scripts/` `references/` `assets/`. Managed/uploadable via **Settings > Rules &
  Skills** (`.md` or `.zip`).
- **Lazy discovery**: at startup only `name` + `description` are loaded; when a task matches the
  description the full `SKILL.md` is read into context and bundled scripts may run.
- Built-in **Skills Marketplace** plus the external **agentskills.io** registry. **gald3r skills install
  directly with zero format translation.** (Feature request #2253, 2026-02, tracks broadening to other
  `SKILL.md` ecosystems.)
- Best-practices guide: docs.trae.ai/ide/best-practice-for-how-to-write-a-good-skill.
- Source: https://docs.trae.ai/ide/skills

## 5. Commands / Workflows — ⚠️ PARTIAL

- **No user-defined arbitrary slash-command file primitive** (no `.trae/commands/`), unlike Claude
  `.claude/commands` or Gemini `.gemini/commands/*.toml`. Official docs expose slash commands only as:
  1. The **built-in Spec Kit workflow** — `/constitution` → `/specify` → `/clarify` → `/plan` →
     `/tasks` → `/analyze` → `/implement` (each phase emits a Markdown artifact feeding the next).
  2. **`@agent-name` routing** to custom agents (dropdown or `@`-syntax).
- Community "custom commands" (SAVEAGG / LOADAGG / LISTPROMPT) are prompt-library conventions layered
  on `user_rules.md` + a `PROMPT.md` — **NOT** an official platform primitive.
- gald3r's `/g-*` command suite **cannot** be installed as native slash commands; surface it via
  rules/skills or via `@agent-name` Custom Agents. Hence **partial**.
- Source: https://docs.trae.ai/ide/agent

## 6. Hooks System — ❌ NOT SUPPORTED

- **No lifecycle/event script-hook primitive** is documented: no `session-start`, `pre-tool`,
  `pre-commit`, or file-watch shell-hook configuration anywhere in the TRAE docs index. Multiple
  targeted searches (trae hooks / lifecycle / pre-tool / event) surfaced **no** official hooks
  mechanism, corroborated by the internal gald3r platform reference (capability matrix: Hooks NOT
  supported).
- Closest adjacent capability is **SOLO scheduled/automated tasks** (solo.trae.ai/automation) — these
  are **time-triggered scheduling**, not the deterministic event hooks gald3r needs (SessionStart
  context injection, pre-commit gates, pre-tool guards).
- **Impact**: gald3r's session-start protocol and pre-commit/pre-push gates have **no native execution
  surface** on TRAE — they must be degraded to manual invocation or folded into `.trae/rules/`
  instructions. Marked **none** (not unknown) because the absence is consistent across the docs index.
- Source: https://docs.trae.ai/ide/solo-mode

## 7. Rules / Memory — ✅ NATIVE

- **`.trae/rules/`** is TRAE's native persistent-instruction layer. Two scopes: project
  (`project_rules.md`) and user (`user_rules.md`); global rules at `~/.trae/rules/` (and
  `~/.trae-cn/rules/` for the China edition). Markdown rule files, invoked with `#rulename`, managed in
  **Settings > Rules & Skills**. Rules load at **session/init** and shape generation. Introduced as the
  `.rules` mechanism in **v1.3.0**.
- gald3r `g-rl-*` map to `.trae/rules/project_rules.md` (project-wide) or `user_rules.md` (user-wide).
- Source: https://docs.trae.ai/ide/rules?_lang=en

## 8. MCP Support — ✅ NATIVE

- **Full Model Context Protocol client support.** Add MCP servers via **stdio** (local command + env,
  e.g. Supabase MCP) or **SSE** (remote `url` + `type: sse`). Built-in **MCP Marketplace** with
  one-click install; manual add via Settings. **Per-agent MCP scoping** ("Builder with MCP"); MCP
  servers attach to Custom Agents. Landed in **v1.3.0** alongside `.rules`. Strong, mature support.
- Source: https://docs.trae.ai/ide/agent

## 9. Other Extensibility — Spec Kit, SOLO, Marketplace

- **Spec Kit workflow**: a phased spec-driven pipeline (`/constitution` → `/specify` → `/clarify` →
  `/plan` → `/tasks` → `/analyze` → `/implement`), adoptable as a structured planning pipeline.
- **SOLO Mode**: autonomous agent running planning-through-deployment (SOLO Coder / SOLO Builder); also
  supports scheduled/automated tasks.
- **Custom-agent import/export** and a **Skills Marketplace** (+ agentskills.io) make agents and skills
  shareable config bundles.
- **Models**: multi-model — Doubao-Seed-2.0-Code (free, ByteDance), Claude, GPT, Gemini; custom models
  configurable (docs.trae.ai/ide/models).
- **Output formats**: no documented machine-readable output-format primitive (Spec Kit artifacts are
  Markdown).

---

## Parity vs. Cursor Reference

TRAE reaches **partial parity** with the Cursor reference (`g-skl-platform-cursor`): native **rules,
agents, skills, and MCP**, but **partial commands** (Spec Kit + `@agent-name` only, no custom
slash-command files) and **no hooks**. The two biggest gaps for a gald3r install are:

1. **Hooks (❌)** — no event-hook surface; SessionStart context injection and pre-commit/pre-push gates
   must be manual or rules-driven. Only SOLO time-based scheduled tasks exist.
2. **Commands (⚠️)** — no user-defined slash-command files; gald3r `/g-*` commands surface via
   rules/skills or `@agent-name` Custom Agents.

**Install note (important):** because TRAE consumes the **`SKILL.md` open standard** directly, gald3r
skills install into `.trae/skills/<name>/SKILL.md` with **zero format translation** — that is the
cheapest high-value path. Rules go to `.trae/rules/project_rules.md`. There is **no** `.claude/` /
`AGENTS.md` reuse path here (unlike Augment) — the instruction surface is `.trae/rules/` only.

## Hook System

- **Type**: none (no lifecycle/event hook primitive documented)
- **Config file**: n/a
- **Events available**: none (SessionStart / PreToolUse / pre-commit all unavailable)
- **Event payload format**: n/a
- **Command extensions**: n/a
- **gald3r hook files**: `g-hk-*.ps1` have **no native execution surface** — degrade to manual or fold
  into `.trae/rules/`. Closest adjacent: SOLO scheduled/automated tasks (time-triggered, not events).

## Atypical Handling

- **Instruction file**: `.trae/rules/project_rules.md` is the native surface — **not** a root
  `CLAUDE.md`/`AGENTS.md` (AGENTS.md support is unverified/unknown).
- **Two editions, shared project paths**: international (`trae.ai`) and China (`trae.cn` / `.trae-cn`)
  share `.trae/` project paths but use separate global paths (`~/.trae/` vs `~/.trae-cn/`).
- **Two modes, one tree**: IDE Mode and SOLO Mode share `.trae/`; SOLO adds autonomy + scheduling.
- **Commands**: only the built-in Spec Kit workflow + `@agent-name`; no committed slash-command files.

## gald3r Integration Notes

- Ship gald3r skills to `.trae/skills/<name>/SKILL.md` (open standard — installs as-is).
- Ship gald3r rules into `.trae/rules/project_rules.md`; map `g-agnt-*` to TRAE Custom Agents.
- Do **not** rely on hooks — degrade SessionStart/pre-commit gates to manual or rules-embedded steps.
- Surface `/g-*` commands via rules/skills or `@agent-name` (no native slash-command files).
- Re-verify on the next `@g-platform-scan-docs trae` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.trae.ai)

| Capability | How verified |
|---|---|
| Commands | /ide/agent — only built-in Spec Kit workflow (/constitution.../implement) + `@agent-name` routing; NO `.trae/commands/` user slash-command primitive → ⚠️ partial |
| Rules | /ide/rules?_lang=en — `.trae/rules/` (project_rules.md + user_rules.md), `#rulename`, loads at init; `.rules` since v1.3.0 → ✅ |
| Agents | /ide/agent — Builder / Builder-with-MCP + Custom Agents (prompt+toolset+MCP), `@agent-name`, one-click import; SOLO Mode autonomous agent → ✅ |
| Skills | /ide/skills — `.trae/skills/<name>/SKILL.md` open standard, lazy name+description discovery, Marketplace + agentskills.io; gald3r skills install verbatim → ✅ |
| Hooks | /ide/solo-mode — no lifecycle/event hook primitive in docs index; only SOLO time-based scheduled tasks (scheduling ≠ event hooks) → ❌ |
| MCP | /ide/agent — full MCP client, stdio + SSE transports, MCP Marketplace, per-agent scoping; since v1.3.0 → ✅ |
| Instruction file | /ide/rules?_lang=en — native surface is `.trae/rules/project_rules.md`; root CLAUDE.md/AGENTS.md NOT confirmed (unknown) |
| Editions | /ide/what-is-trae?_lang=en — trae.ai + trae.cn share `.trae/` project paths, separate global (~/.trae vs ~/.trae-cn) |
