# Windsurf Platform — gald3r Configuration Guide

**Platform**: Windsurf (by Codeium — VS Code-based AI IDE with the Cascade agent)
**Config Folder**: root `.windsurfrules` (+ optional `.windsurf/rules/`)
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.windsurf.com
**Config File**: `.windsurfrules` (project root)
**Authoritative skill**: `g-skl-platform-windsurf`

---

## Folder Layout

```
<project-root>/
├── .windsurfrules          # Project-level rules, auto-injected into Cascade
└── .windsurf/
    └── rules/              # Per-file/per-folder rule overrides (optional)
```

Global rules are managed in Windsurf settings (stored in `~/.codeium/windsurf/memories/`).

**What Windsurf does NOT have:**
- No native skills discovery path equivalent to `.cursor/skills/`
- No project `agents/` or `commands/` folders — Cascade is the agent
- No lifecycle `hooks/` — MCP is supported via settings

---

## What Makes Windsurf Unique

### Cascade Agent + Rules Injection
Cascade is Windsurf's multi-step agent. It auto-reads `.windsurfrules` (and global rules)
into its context. Keep `.windsurfrules` under ~8K tokens for the Cascade budget. Inline
completion context is separate — rules inject into Cascade only.

### Rules File Location
gald3r writes its always-apply rules to the legacy `.windsurfrules` file at the project root.
Per PLATFORM_SPEC §7 (T1466), `.windsurfrules` is the **legacy** single-file format (still
honored, always injected into Cascade), while `.windsurf/rules/*.md` — one file per rule with
**activation modes** (Always On / Manual / Model Decision / Glob) — is the **current** model going
forward. The rule extension is `.md` (not Cursor's `.mdc`). gald3r ships the legacy `.windsurfrules`
for maximum compatibility; emitting `.windsurf/rules/*.md` is an opt-in upgrade.

### Skills
Windsurf has no native skills discovery. Surface skill content via `.windsurfrules`
(compact summary) and reference skill names with `@mention` in Cascade prompts.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/`; summarized in `.windsurfrules` |
| Agents | Cascade (built-in) |
| Commands | (none) |
| Rules | `.windsurfrules` (+ `.windsurf/rules/` overrides) |

---

## Config Files Shipped

- **`.windsurfrules`** — gald3r always-apply rule subset (task gate, commit format, bug protocol).

---

## gitignore Decision (T1277 AC6)

`.windsurfrules` and any `.windsurf/rules/*.md` are **source** — keep them tracked. Windsurf
writes global memories under `~/.codeium/windsurf/` (outside the project), so no generated
project output dir needs gitignoring.

---

## Verification

```powershell
Test-Path .windsurfrules
```

Expected: `.windsurfrules` present.

---

## MCP (Cascade)

Windsurf/Cascade supports MCP servers. Config is JSON at `~/.codeium/windsurf/mcp_config.json`
(and/or via Windsurf Settings → Cascade → MCP). This path differs from Cursor's `.cursor/mcp.json`,
so a single `mcp.json` cannot be shared between Cursor and Windsurf (PLATFORM_SPEC §8). ⚠️

---

## Common Pitfalls

- `.windsurfrules` (root) is the legacy always-apply file gald3r ships; `.windsurf/rules/*.md`
  (with activation modes) is the current model — do not assume one supersedes the other (§7).
- Global user rules can override project rules in some Cascade versions — test project scope.
- Cascade context is separate from inline-completion context; rules inject into Cascade only.
- MCP config lives at `~/.codeium/windsurf/mcp_config.json`, NOT a repo-local `mcp.json`.
