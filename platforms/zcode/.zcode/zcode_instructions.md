# ZCode Platform — gald3r Configuration Guide

**Platform**: ZCode (Z.ai / Zhipu) — free cross-platform Agentic Development Environment built
around GLM-5.2, with BYOK support for other providers.
**Config Folder**: `.zcode/` (project-scoped config; MCP server entries also live here)
**gald3r Version**: 1.0.0
**Official Docs**: https://zcode.z.ai/en/docs/welcome
**Instruction File**: root `AGENTS.md`, appended to the global `~/.zcode/AGENTS.md` (global first,
then workspace — **no** hierarchical directory scan, no `@import`/`@include`). ZCode does NOT read
`CLAUDE.md`.
**Authoritative skill**: `g-skl-platform-zcode`
**Capability detail**: see `../PLATFORM_SPEC.md`

---

## Folder Layout

```
<project-root>/
├── AGENTS.md                        # instruction file — appended AFTER ~/.zcode/AGENTS.md (global-then-workspace)
└── .zcode/
    └── skills/   <name>/SKILL.md    # Agent Skills (YAML frontmatter: name, description + Markdown body)

~/.zcode/
├── AGENTS.md                        # global/user instructions — read FIRST, workspace AGENTS.md appended after
├── agents/   <name>.md              # subagents — Beta, GLOBAL/USER-LEVEL ONLY (no project-level agents yet)
├── commands/ <name>.md              # custom slash commands (invoked as /name); workspace commands also supported
└── skills/   <name>/SKILL.md        # user-level skills

(MCP servers)                        # configured via Settings -> MCP Servers UI, or Full-configuration
                                      # JSON paste; stored in a `.zcode` config file at User or Workspace
                                      # scope. Accepts {"server-name": {...}} or {"mcpServers": {...}}.
```

---

## Instruction File Merge Behavior (read carefully)

ZCode reads **`AGENTS.md`** at two scopes and concatenates them — it does **not** merge
hierarchically the way Cursor/Windsurf/Claude Code do:

1. `~/.zcode/AGENTS.md` (global, read first)
2. `<workspace-root>/AGENTS.md` (appended after the global file)

There is **no** directory-hierarchy scan (no per-subfolder `AGENTS.md`), and **no** `@file.md`
import/include mechanism. Whatever gald3r wants ZCode to see must be inline in the workspace-root
`AGENTS.md` — do not rely on `@AGENTS.md`-style imports the way Qwen/Gemini/Antigravity do.

## Cross-Tool Reuse

ZCode's Agent Skills format (`SKILL.md` with `name`/`description` YAML frontmatter + Markdown body,
folder-per-skill under `.zcode/skills/<name>/`) matches the agentskills.io convention gald3r already
targets — gald3r's `g-skl-*/SKILL.md` files are drop-in native, no adaptation needed. ZCode also
supports importing skills from other tools (Claude Code, Codex CLI, etc.) via symlink or copy.

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Rules / instructions | root `AGENTS.md` (appended after `~/.zcode/AGENTS.md`; no imports, no dir scan) |
| Skills | `.zcode/skills/<name>/SKILL.md` (native, agentskills.io-compatible) |
| Commands | `~/.zcode/commands/<name>.md` (global) or workspace-scoped; invoked `/command-name` |
| Agents | `~/.zcode/agents/<name>.md` — **Beta, global/user-level only**, no project-level agents yet |
| MCP | `.zcode` config file (User or Workspace scope); stdio / HTTP / SSE transports |
| Hooks | **not supported for user authoring** — no documented event taxonomy/schema; plugins can bundle hooks internally, but there is no gald3r-writable hook surface |

## Capability Note

ZCode natively supports Agent Skills, rules/instructions (AGENTS.md, append-only merge), MCP, and
user-defined slash commands. Subagents are Beta and **global/user-level only** — no project-scoped
agent roster yet, so gald3r's `g-agnt-*.md` set does not have a project-level landing zone. There is
**no** lifecycle-hook system exposed for hand-authored hooks — do not expect `g-hk-*.ps1` to fire.
See `PLATFORM_SPEC.md` for full verification evidence and source URLs.
