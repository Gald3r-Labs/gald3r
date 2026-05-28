# Augment Code Platform — gald3r Configuration Guide

**Platform**: Augment Code (VS Code extension + JetBrains plugin; `auggie` CLI)
**Config Folder**: `.augment/` (plus the root `.augment-guidelines` file)
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.augmentcode.com
**Instruction surfaces**: `.augment/rules/*.md` (modern) and/or root `.augment-guidelines` (legacy)
**Authoritative skill**: `g-skl-platform-augment`
**Capability spec**: `PLATFORM_SPEC.md` (this directory) — read before editing

---

## Folder Layout

Augment supports two coexisting repository-level instruction surfaces:

```
<project-root>/
├── .augment-guidelines          # legacy single-file workspace guidelines (root, plain text/markdown)
└── .augment/
    └── rules/                   # modern rules directory (markdown, frontmatter-typed)
        ├── g-rl-gald3r.md       # type: always — gald3r core context, injected every prompt
        ├── <auto-rule>.md       # type: auto   — attached when description: matches the request
        └── <manual-rule>.md     # type: manual — IDE @-mention attach only (auggie CLI skips these)
```

**What Augment does NOT have (per PLATFORM_SPEC §3–§6):**
- No `agents/` folder — single built-in Agent; `g-agnt-*` personas port as rule text only.
- No `commands/` folder — no slash-command namespace; `@g-*` commands are doc-only prose.
- No `skills/` folder — no skills framework; `g-skl-*/SKILL.md` is not invokable.
- No `hooks/` folder — no lifecycle hook system; `g-hk-*.ps1` hooks cannot be wired.

> **Correction (T1499)**: earlier scaffold text referenced a `.augment/guidelines.md` config
> file and claimed "no `rules/` folder". Both were Cursor-generic / fabricated. The documented
> surfaces are the root **`.augment-guidelines`** file (no `.md` extension) and the
> **`.augment/rules/*.md`** directory. `augment.yaml` is NOT a documented gald3r config surface.

---

## Rules — Augment's strongest surface

`.augment/rules/*.md` files use frontmatter to set a `type:`:

| type | Behavior | `auggie` CLI |
|---|---|---|
| `always` | Content injected into **every** prompt | ✅ (`always_apply`) |
| `auto` | Auto-attached when the rule's `description:` matches the request | ✅ (`agent_requested`) |
| `manual` | Attached only via IDE `@`-mention | ⚠️ IDE-only — CLI skips |

- Files are plain **`.md`** / `.mdx` — **not** Cursor's `.mdc`. Parity sync handles the
  extension swap when porting `g-rl-*` rules.
- gald3r `alwaysApply: true` rules map to `type: always`; `description:`-scoped rules map to
  `type: auto`.
- Per-file `globs:` scoping (Cursor-style) is `❓` — not clearly documented for Augment.

---

## Context Engine (Augment-native, no Cursor analog)

Augment indexes the entire codebase for semantic retrieval. This index is **separate** from
the rules surface — it is built/managed by the extension and is **not** a gald3r-writable store.
Behavioral instructions belong in `.augment/rules/*.md` / `.augment-guidelines`; the index
carries code knowledge only. Do not mistake the Context Engine for a rules/memory store.

---

## MCP

Augment supports MCP servers (extension MCP client; `auggie` CLI also connects). Configuration
is **IDE-settings-driven** (Settings panel / Easy MCP install) — there is no documented committed
repo-root config file, so MCP is not fully captured by a repo-tracked gald3r install. See the MCP
server registry at https://www.augmentcode.com/mcp.

---

## gald3r Naming Conventions

| Component | Surface on Augment |
|-----------|--------------------|
| Rules | `.augment/rules/*.md` (`type: always`/`auto`/`manual`) + `.augment-guidelines` |
| Skills | (none) — referenced as prose in rules; served from root `skills/` |
| Agents | (none) — ported as rule text |
| Commands | (none) — described to the Agent, not invoked via slash command |
| Hooks | (none) — policies carried by `type: always` rules or run manually |

---

## Config Files Shipped

- **`.augment/rules/g-rl-gald3r.md`** — `type: always` rule with gald3r task management,
  commit, and bug-protocol guidance (injected into every session).
- Optionally a root **`.augment-guidelines`** file may carry the same content for installs that
  prefer the legacy single-file form.

---

## gitignore Decision (T1277 AC6)

`.augment/rules/*.md` and `.augment-guidelines` are **source** — keep them tracked. Augment writes
no generated output directory in the project root, so no gitignore entry is needed in installed
projects (the Context Engine index is managed by the extension, not committed).

---

## Verification

```powershell
Test-Path .augment/rules/g-rl-gald3r.md
```

---

## Common Pitfalls

- The Context Engine index is not the rules surface — behavioral rules must live in
  `.augment/rules/*.md` or `.augment-guidelines`.
- `manual`-type rules are skipped by the `auggie` CLI — use `always` / `auto` for CLI parity.
- Rule files are `.md`/`.mdx`, never `.mdc` (that is Cursor).
- JetBrains may also read a user/global path (`~/.augment/`) — project rules take precedence
  for workspace-scoped behavior.
- Enterprise team guidelines can override workspace guidelines depending on tier.
