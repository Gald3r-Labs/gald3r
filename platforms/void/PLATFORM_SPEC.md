---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: void
authoring_path: update
docs_url: https://voideditor.com
docs_url_secondary:
  - https://voideditor.com/changelog
  - https://deepwiki.com/voideditor/void/3.6-model-context-protocol-(mcp)-service
  - https://deepwiki.com/voideditor/void/1.1-getting-started
  - https://github.com/voideditor/void/issues/643
  - https://github.com/voideditor/void/issues/629
  - https://github.com/voideditor/void/issues/912
crawl_max_age_days: 90
vault_doc_path: research/platforms/void/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Void (open-source VS Code fork)

Void is an **open-source VS Code fork** focused on direct-to-LLM AI coding (Agent / Gather / Chat
modes), backed by Y Combinator. Of the six gald3r-relevant extension primitives, only **two ship
natively**: **MCP** (via `mcp.json`) and a **single persistent rules file** (`.voidrules`). There are
**no** user-defined custom commands, **no** Skills system, **no** lifecycle hooks, and **no**
user-definable sub-agents (only the three built-in product modes). Overall parity is therefore
**⚠️ partial**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://voideditor.com + the
`voideditor/void` codebase wiki (see Verification Evidence). This **supersedes** the prior stale spec
which incorrectly mapped rules to `.cursorrules` and marked Agents as ✅ — Void's rules file is
`.voidrules` (not `.cursorrules`), and the built-in modes are **not** user-definable sub-agents (❌).

> **Development PAUSED.** The maintainer (Andrew Pareles) stated in GitHub issue #912 that the team
> paused Void to work in stealth on more innovative ideas rather than compete on feature-parity. Last
> binary release **v1.99.30044 (2025-06-23)**; last meaningful source change ~2025-08-04. The build
> still runs and connects to current model APIs, but **no new features are landing**. This strongly
> bounds "current" capabilities: proposed-but-unmerged features (e.g. the directory-based
> `.void/rules/` system #643, auto-approve commands #629) are treated as **NOT shipped**. Because the
> surface is frozen, `crawl_max_age_days: 90` (a slow cadence is appropriate for a paused project).

> **Surface note:** Void is a single desktop editor (no separate CLI surface). It also inherits the
> **VS Code extension ecosystem** (one-click import) and VS Code themes/keybinds/settings — an
> extensibility surface, but **not** an AI-agent extension mechanism, so it does not raise gald3r
> parity.

---

## 1. Folder Hierarchy

```
<project-root>/
├── .voidrules                     ← single persistent always-on rules file (root; .cursorrules-style)
└── ~/[appName]/mcp.json           ← MCP server config (user-level, app data dir)
```

No `.void/` project config tree ships. **There is no instruction-file convention for `AGENTS.md` or
`CLAUDE.md`** — Void reads neither; the only persistent guidance file is the project-root
`.voidrules`. (A directory-based `.void/rules/` convention was **requested** in issue #643 but never
merged — do not rely on it.)

**gald3r writes**: `.voidrules` (rules) and `mcp.json` (MCP). Nothing else is a gald3r-writable
surface on Void.
**Void owns**: the built-in product modes (Agent/Gather/Chat), the underlying system prompts
(user-editable via "prompt editing"), autocomplete/Quick-Edit, checkpoints, and the open-source
codebase itself.

---

## 2. AI Instruction File

Void's only persistent instruction surface is **`.voidrules`** — a single file in the project root,
prepended to chat context (Cursor `.cursorrules`-style). It is managed via command-palette actions
(`Void: New Rule` / `Void: Edit Rules`) with a rules explorer in the sidebar. **No `AGENTS.md`, no
`CLAUDE.md`, no `VOID.md`** is read. gald3r's `AGENTS.md`/`CLAUDE.md` are therefore **not** picked up
automatically — their key directives must be mirrored into `.voidrules`.

---

## 3. Agents Support — ❌ NONE

- Only **built-in, fixed operating modes** exist: **Agent mode** (search/create/edit/delete files &
  folders, terminal access, MCP tool access), **Gather mode** (read/search only, no modification),
  and **Chat mode**. These are product modes, **not** user-definable sub-agents/roles.
- There is **no** mechanism to author named sub-agents with scoped tools/models (unlike Claude Code
  `.claude/agents/`). gald3r `g-agnt-*` definitions have **no native target** on Void.
- Source: https://voideditor.com/

## 4. Skills Support — ❌ NONE

- **No Skills system** — no `SKILL.md`, no Agent Skills, no reusable skill/workflow files anywhere in
  Void's official docs, changelog, or codebase wiki.
- gald3r `g-skl-*/SKILL.md` have **no native loader** on Void.
- Source: https://voideditor.com/changelog

## 5. Commands / Workflows — ❌ NONE

- **No user-defined custom/slash command system.** Void exposes built-in command-palette actions
  (`Void: New Rule`, `Void: Edit Rules`, Quick Edit `Ctrl+K`) but **no facility to author reusable
  prompt/slash commands**. The only adjacent customization is "prompt editing" (view/modify the
  underlying built-in system prompts).
- gald3r `@g-*` / `/g-*` commands have **no native target**.
- Source: https://deepwiki.com/voideditor/void/1.1-getting-started

## 6. Hooks System — ❌ NONE

- **No lifecycle/event hook system** — no SessionStart, no Pre/PostToolUse, no pre-commit, no
  file-watch script hooks. A related-but-distinct feature (user-defined **auto-approve** rules for
  Agent-mode commands, issue #629) was **requested** but is command auto-approval, **not** a
  script-executing hook, and is unmerged.
- gald3r `g-hk-*.ps1` hooks have **no native target**; session-start context injection / `.gald3r/`
  guards / pre-commit gates cannot be wired on Void.
- Source: https://github.com/voideditor/void/issues/629

## 7. Rules / Memory — ✅ NATIVE

- **`.voidrules`** — a single persistent, always-on rules/instructions file in the project root.
  Content is prepended to chat context to enforce coding standards/guidelines (Cursor
  `.cursorrules`-style). Managed via the command palette (`Void: New Rule` / `Void: Edit Rules`) with
  a rules explorer in the sidebar. **Single-file only** — directory-based `.void/rules/` (#643) is
  **not merged**, so there is no per-glob / multi-file rule scoping.
- gald3r `g-rl-*` map to a **single concatenated `.voidrules`** (no `always_apply`/`agent_requested`
  type distinction, no per-glob targeting — all content is always-on).
- Source: https://github.com/voideditor/void/issues/643

## 8. MCP Support — ✅ NATIVE

- **Native Model Context Protocol** support. MCP servers are discovered/configured via a
  user-editable **`mcp.json`** file (`~/[appName]/mcp.json`); each entry is a local `command`+`args`
  or remote URL with env vars / HTTP headers. An MCP Service (`IMCPService`) manages server lifecycle
  (loading/online/offline/error) and exposes external tools via `getMCPTools()` / `callMCPTool()`.
  MCP tools are invocable from **Agent mode**.
- Caveat: integration is **narrower than Cursor's** and has had reliability issues (e.g. issue #752,
  local-LLM filesystem access).
- Source: https://deepwiki.com/voideditor/void/3.6-model-context-protocol-(mcp)-service

---

## Parity vs. Cursor Reference

Void reaches only **partial parity** with the Cursor reference (`g-skl-platform-cursor`): native
**rules** (single-file `.voidrules`) and native **MCP** (`mcp.json`), but **no** commands, skills,
hooks, or user-definable sub-agents. The honest overall status is **⚠️ partial**.

**Reuse note (important):** unlike Claude-compatible platforms, Void reads **neither `CLAUDE.md` nor
`AGENTS.md`** and discovers **no** `.claude/` / `.agents/` trees. gald3r's Claude-Code artifacts are
therefore **not** reusable on Void — the only portable assets are (a) the **MCP server set** (drop
into `mcp.json`) and (b) a **flattened rules digest** written to `.voidrules`. Everything else
(commands/skills/agents/hooks) must degrade to manual `.voidrules` instructions or be skipped.

**Frozen-upstream note:** development is paused, so none of these gaps are likely to close upstream.
Treat all "proposed" enhancements (#643 `.void/rules/` directory, #629 auto-approve) as unavailable.

## Hook System

- **Type**: ❌ none (no lifecycle/event hook subsystem)
- **Config file**: n/a
- **Events available**: none (no SessionStart / Pre-PostToolUse / pre-commit / file-watch)
- **Event payload format**: n/a
- **Command extensions**: n/a
- **gald3r hook files**: `g-hk-*.ps1` cannot be wired — no native target. Closest concept is the
  unmerged auto-approve-commands request (#629), which is not a script-executing hook.

## Atypical Handling

- **No `AGENTS.md`/`CLAUDE.md`**: Void reads only `.voidrules`. Mirror the essential gald3r directives
  there; the standard instruction files are ignored.
- **No `.claude/` interop**: gald3r's Claude-Code tree is not discovered — there is no cheap reuse
  path. Port only MCP (`mcp.json`) + a `.voidrules` digest.
- **Single-file rules**: no multi-file / per-glob rule scoping (the `.void/rules/` directory is
  unmerged) — concatenate all `g-rl-*` content into one `.voidrules`.
- **Built-in modes ≠ agents**: Agent/Gather/Chat are fixed product modes, not authorable sub-agents.
- **Open-source escape hatch**: deeper behavior changes require editing the built-in system prompts
  ("prompt editing") or forking the MIT/Apache-licensed code — not a gald3r-managed surface.

## gald3r Integration Notes

- Ship the **MCP server set** into `~/[appName]/mcp.json` and a **flattened rules digest** into
  `.voidrules` — these are the only two native gald3r targets on Void.
- **Skip** commands / skills / agents / hooks (no native target); degrade their intent to plain
  `.voidrules` instructions where it matters.
- Development is **paused** — re-verify only on the slow cadence (`crawl_max_age_days: 90`); do not
  expect new primitives upstream.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://voideditor.com + voideditor/void wiki)

| Capability | How verified |
|---|---|
| Commands | ❌ — DeepWiki Getting Started lists Chat/Agent/Gather modes, Quick Edit, Autocomplete, MCP; **no** command-authoring system. Only "prompt editing" of built-in prompts. (deepwiki .../1.1-getting-started) |
| Rules | ✅ — `.voidrules` single root file (issues #585, #643); loaded from project root (e.g. `d:\story-buddy\.voidrules`). Directory `.void/rules/` proposed in #643, **not merged**. |
| Agents | ❌ — voideditor.com: built-in Agent/Gather/Chat modes only; no way to define additional/custom sub-agents. |
| Skills | ❌ — searches for Void skills / `SKILL.md` return only Claude Code material; changelog/Getting Started enumerate MCP/modes/autocomplete/quick-edit/checkpoints/SSH-WSL/AI-commit — no skills concept. |
| Hooks | ❌ — no hook subsystem in changelog or DeepWiki; issue #629 (user-defined auto-approve commands) is the closest concept and is a feature request, not a shipped hook API. |
| MCP | ✅ — changelog "Added MCP support!" (Beta Patch #7, v1.4.1); DeepWiki MCP Service: user-editable `mcp.json`, tool discovery/invocation from Agent mode. Narrower than Cursor; reliability caveat (#752). |
| Instruction file | ❌ `AGENTS.md`/`CLAUDE.md` — Void reads neither; only project-root `.voidrules`. |
| Cross-compat | ❌ — no `.claude/`/`.agents/` discovery; gald3r Claude artifacts **not** reusable. Portable assets: `mcp.json` + a `.voidrules` digest only. |
| Project status | Development PAUSED (issue #912); last binary v1.99.30044 (2025-06-23); last source change ~2025-08-04. Proposed features (#643, #629) unavailable. |
