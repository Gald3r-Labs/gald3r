---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: augment
authoring_path: update
docs_url: https://docs.augmentcode.com
docs_url_secondary:
  - https://docs.augmentcode.com/setup-augment/guidelines
  - https://www.augmentcode.com/changelog/introducing-augment-rules
  - https://www.augmentcode.com/mcp
crawl_max_age_days: 14
vault_doc_path: research/platforms/augment/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Augment Code (VS Code + JetBrains extension)

Augment Code is an enterprise-focused AI coding assistant delivered as a **VS Code extension** and
**JetBrains plugin**, with a separate **`auggie` CLI** for terminal/agent use. Its defining feature
is the **Context Engine** — a codebase-wide semantic index that supplies retrieval context to Agent
and Chat automatically. For gald3r purposes, the platform's customization surface is two things:
the legacy root **`.augment-guidelines`** file and the newer **`.augment/rules/`** directory of
markdown rule files. It has **no native hook system**, **no skills framework**, and **no
slash-command namespace** for arbitrary user commands.

**Authoring path**: UPDATE — `g-skl-platform-augment/SKILL.md` already ships. This spec records the
verified findings and the honest capability assessment that feeds `PLATFORM_STATUS.md`.

> **Verification caveat (read first)**: `last_doc_scan: never`. This spec is authored from the
> existing SKILL.md plus a brief live doc check (May 2026) of
> https://docs.augmentcode.com/setup-augment/guidelines and the Augment Rules changelog — **not**
> from a full `@g-platform-scan-docs augment` crawl. There is **no `.augment/` config in this repo**
> to inspect (confirmed by repo scan). Every capability not confirmed by a current doc citation or
> an install test is marked `❓` (untested) or `⚠️` (partial / Cursor-generic). Do not promote
> `❓`/`⚠️` → `✅` without evidence recorded in the Verification Evidence section.

---

## 1. Folder Hierarchy

Augment Code supports **two coexisting layouts** for repository-level instructions:

```
<project-root>/
├── .augment-guidelines          ← legacy single-file workspace guidelines (root, plain text/markdown)
└── .augment/
    └── rules/                   ← modern rules directory (markdown, frontmatter-typed)
        ├── always-rule.md       ← type: always  (injected into every prompt)
        ├── auto-rule.md         ← type: auto    (attached when description matches)
        └── manual-rule.md       ← type: manual  (IDE @-mention attach only)
```

There is **no** native `.augment/skills/`, `.augment/agents/`, `.augment/commands/`, or
`.augment/hooks/` concept. gald3r's skill/agent/command/hook trees have no Augment-native home
and are degraded to documentation-only ports under the guidelines/rules surface (see §3–§6).

**gald3r writes**: `.augment-guidelines` (or `.augment/rules/*.md`), as the behavioral-instruction
surface only.
**Augment owns**: the `.augment/` namespace, the Context Engine index (built/managed by the
extension, not a gald3r-writable artifact), and the rule type-resolution mechanism.

User-level and global rules exist but live **outside the repo** (IDE settings / home directory) and
are out of scope for gald3r's repo-tracked install (`❓` — not gald3r-managed).

---

## 2. AI Instruction File

Augment's repo-level instruction surface is **`.augment-guidelines`** (root) and/or the
**`.augment/rules/`** markdown files. There is no `AGENTS.md` / `CLAUDE.md` auto-read contract
documented for the extension; the canonical input is the guidelines/rules surface above.

- **`.augment-guidelines`**: a single file at the repo root. Natural-language instructions applied
  to **all** Agent and Chat sessions on the codebase. This is the simplest gald3r target.
- **`.augment/rules/`**: the modern, recommended mechanism — see §7.

gald3r **generates** `.augment-guidelines` (and optionally seeds `.augment/rules/`) at install with
task-management / architecture / code-standards context. These are personalized and gitignored per
`g-rl-02` protected-files policy when they carry user-specific content.

> **Correction vs. prior SKILL.md**: earlier SKILL.md text referenced `.augment/guidelines.md` and a
> possible `augment.yaml`. The documented path is the root **`.augment-guidelines`** file (no `.md`
> extension) for the legacy single-file form, and **`.augment/rules/*.md`** for the directory form.
> `augment.yaml` is **not** a documented gald3r-relevant config surface (`❌` / unverified).

---

## 3. Agents Support

- **Native concept**: ❌ No user-authored agent-definition files. Augment ships its own built-in
  Agent (and the `auggie` CLI agent); it does **not** load arbitrary `g-agnt-*.md` agent personas.
- **Discovery / loading**: N/A — there is no `.augment/agents/` directory contract.
- **gald3r mapping**: gald3r `g-agnt-*` definitions can only be ported as **rule/guidelines text**
  (e.g. "act as the code-reviewer per these criteria"), not as selectable agents.
- **Status**: ❌ not supported as a native primitive.

---

## 4. Skills Support

- **Native concept**: ❌ No skills framework. There is no `.augment/skills/` discovery path and no
  SKILL.md loading contract.
- **gald3r mapping**: gald3r `g-skl-*/SKILL.md` content can only be referenced as prose inside
  guidelines/rules. The Context Engine may surface a skill file as retrieval context if it lives in
  the indexed repo, but Augment does **not** treat it as an invokable skill.
- **Status**: ❌ not supported.

---

## 5. Commands / Workflows

- **Native concept**: ❌ No user-extensible slash-command or workflow-file namespace. Augment
  exposes its own built-in chat/agent interactions; there is no documented `.augment/commands/`
  directory for arbitrary `g-*` commands.
- **gald3r mapping**: gald3r `@g-*` commands are degraded to documentation in guidelines text — the
  user invokes the behavior by describing it to the Agent, not via a slash command.
- **Status**: ❌ not supported (no command framework).

---

## 6. Hooks System

- **Native concept**: ❌ No native lifecycle-hook system. Augment exposes no documented
  `sessionStart` / `stop` / `preToolUse` / `beforeShellExecution` events and no `hooks.json`
  equivalent for the extension.
- **gald3r mapping**: gald3r PowerShell hooks (`g-hk-*.ps1`) have no wiring mechanism on Augment.
  Hook-enforced policies (session-start context injection, pre-commit checks) must be carried by
  always-rules text or run manually outside the extension.
- **Status**: ❌ not supported.

---

## 7. Rules / Memory

This is Augment's **primary and strongest** customization surface.

- **Extension**: plain **`.md`** (and `.mdx`) — *not* Cursor's `.mdc`. Augment auto-imports markdown
  rule files detected in the workspace.
- **Location**: `.augment/rules/*.md` (workspace rules, repo-tracked) plus the legacy root
  `.augment-guidelines` file. User/global rules live in IDE settings / home dir (out of gald3r scope).
- **Rule types** (frontmatter `type:` field):
  | type | Behavior | CLI (`auggie`) |
  |---|---|---|
  | `always` | Content injected into **every** prompt | ✅ supported (`always_apply`) |
  | `auto` | Agent auto-attaches when the rule's `description:` matches the request | ✅ supported (`agent_requested`) |
  | `manual` | Attached only via IDE `@`-mention | ⚠️ **IDE-only** — skipped by the `auggie` CLI |
- **Frontmatter note**: the CLI expects snake_case values (`always_apply`, `agent_requested`) for
  cross-surface compatibility. gald3r `g-rl-*` rules map cleanly to `type: always` (for
  `alwaysApply: true` rules) or `type: auto` (for `description:`-scoped rules).
- **Context injection / memory**: always-rules + `.augment-guidelines` are the persistent
  context-injection mechanism. The **Context Engine** supplements this with codebase retrieval but is
  not a user-writable rules store. gald3r `.gald3r/learned-facts.md` remains the durable project-fact
  store, surfaced by `g-rl-25` at session start (manually, since there is no native sessionStart hook).
- **Status**: ✅ rules mechanism verified by docs (May 2026); ⚠️ exact glob-scoping support per rule
  is not documented the way Cursor's `globs:` works — treat per-file scoping as `❓`.

---

## 8. MCP Support

- **Supported**: ✅ Yes. Augment Code supports Model Context Protocol servers (extension hosts an MCP
  client; the `auggie` CLI also connects to MCP servers).
- **Config format/location**: configured via Augment **Settings / Settings Panel** (Easy MCP
  install) or an MCP server JSON entry; there is **no committed repo-root `.augment/mcp.json`** in
  this repo to confirm the exact file path, so the on-disk path is `❓` / settings-driven.
- **Server discovery**: Augment connects to configured servers and exposes their tools to Agent/Chat.
  An MCP server registry is published at https://www.augmentcode.com/mcp.
- **Status**: ✅ supported (mechanism); ⚠️ exact repo-tracked config-file format unverified — likely
  IDE-settings-driven rather than a committed file, so not fully gald3r-install-managed.

---

## 9. Known Gaps vs. Cursor Reference

Compared to the Cursor reference implementation (`g-skl-platform-cursor`):

1. **No native agents** (❌) — Cursor's `.cursor/agents/g-agnt-*.md` selectable-agent layout has no
   Augment equivalent. gald3r agents become rule/guidelines prose only.
2. **No skills framework** (❌) — no `.augment/skills/` discovery; `g-skl-*/SKILL.md` is not invokable.
3. **No command/workflow namespace** (❌) — no `.augment/commands/`; `@g-*` commands are doc-only.
4. **No native hook system** (❌) — no `hooks.json`, no lifecycle events. PowerShell `g-hk-*.ps1`
   hooks cannot be wired; session-start context injection and pre-commit checks run manually or via
   always-rules text. This is the single biggest enforcement gap (mirrors cline/windsurf/gemini).
5. **Rules** (✅/⚠️) — strong: `.augment/rules/*.md` with `always`/`auto`/`manual` types maps well to
   gald3r rules. Gaps vs. Cursor: plain `.md` not `.mdc` (parity sync handles the extension swap);
   per-file `globs:` scoping is `❓` (Cursor-style glob scoping not clearly documented); `manual`
   rules are IDE-only (the `auggie` CLI skips them).
6. **MCP** (⚠️) — supported, but configuration appears IDE-settings-driven rather than a committed
   repo file, so it is not fully captured by a repo-tracked gald3r install (unlike Cursor's optional
   `.cursor/mcp.json`).
7. **Context Engine** — Augment-native strength with **no Cursor analog**; it is a retrieval index,
   not a gald3r-writable surface, so it neither helps nor hurts parity but should not be mistaken for
   a rules/memory store.

**Decision-tree placement** (per Cursor SKILL.md §4a): the `.augment-guidelines` / `.augment/rules/`
format is **platform-specific** (lives in the Augment tree, generated by parity sync from common
`g-rl-*` sources). Hooks/skills/agents/commands are documented gaps here (option (c)).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ❌ | ❌ | ⚠️ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

`Docs Fresh = ❓` because `last_doc_scan: never` — flip to ✅ after the first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Rules `.augment/rules/*.md` + types | Doc check (May 2026): https://docs.augmentcode.com/setup-augment/guidelines + Augment Rules changelog — 3 types (always/manual/auto), markdown `.md`/`.mdx`, frontmatter-driven |
| `.augment-guidelines` root file | Doc confirmed: single root file applied to all Agent/Chat sessions |
| `manual` rule = IDE-only | Doc confirmed: `auggie` CLI skips manual rules (no @-mention in CLI) |
| MCP | Doc confirmed supported (https://www.augmentcode.com/mcp); repo-tracked config-file path unverified (settings-driven) |
| Hooks | No documented hook/lifecycle-event system found — ❌ |
| Skills | No documented skills-loading contract — ❌ |
| Agents | No documented user-agent-definition contract — ❌ |
| Commands | No documented user slash-command/workflow namespace — ❌ |
| Repo config presence | No `.augment/` config in this repo (scan returned nothing) — claims from docs + SKILL.md, not install test |
| Docs freshness | Not a full crawl — `last_doc_scan: never`; pending `@g-platform-scan-docs augment` |
