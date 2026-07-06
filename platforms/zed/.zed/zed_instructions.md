# Zed Platform — gald3r Configuration Guide

**Platform**: Zed — Rust-native code editor whose Agent Panel hosts both the built-in Zed Agent and
**External Agents** (Claude Code, Kimi Code, Codex, and others) via the open **Agent Client
Protocol (ACP)**.
**Config Folder**: `.zed/` (workspace settings live at `.zed/settings.json`; gald3r itself writes no
files directly under `.zed/` — see Capability Note)
**gald3r Version**: 1.0.0
**Official Docs**: https://zed.dev/docs/ai/external-agents
**Instruction files**: project-root `.rules` (highest precedence, back-compat with
`.cursorrules`/`.windsurfrules`/`.clinerules`-era projects) **or** project-root `AGENTS.md`, plus a
**personal, machine-global** `AGENTS.md` at `~/.config/zed/AGENTS.md` (macOS/Linux) /
`%APPDATA%\Zed\AGENTS.md` (Windows) that Zed reads for every workspace.
**Authoritative skill**: `g-skl-platform-zed`
**Capability detail**: see `PLATFORM_SPEC.md` under `g-skl-platform-zed/`

---

## Folder Layout

```
<project-root>/
├── .rules OR AGENTS.md              # project instructions — .rules wins if both exist (see precedence below)
└── .agents/
    └── skills/  <name>/SKILL.md     # Agent Skills — shared cross-client convention (project-local scope)

~/.config/zed/                       # macOS/Linux personal scope (Windows: %APPDATA%\Zed\)
└── AGENTS.md                        # personal/global instructions — always-on, applies to every workspace

~/.agents/skills/  <name>/SKILL.md   # Agent Skills — global/user scope (same convention as Codex, Amp, Deepcode)

(.zed/settings.json)                 # Zed-owned workspace settings file — houses "agent_servers"
                                      # (external ACP agents: Claude Code, Kimi Code, Codex, ...) and
                                      # "context_servers" (MCP). gald3r does not overwrite this file
                                      # wholesale; see Capability Note for the merge-snippet approach.
```

---

## Instruction File Precedence (read carefully)

Zed checks for a project-level instructions file in a fixed fallback order, first match wins:

1. `.rules`
2. `.cursorrules`
3. `.windsurfrules`
4. `.clinerules`
5. `.github/copilot-instructions.md`
6. `AGENT.md`
7. `AGENTS.md`
8. `CLAUDE.md`
9. `GEMINI.md`

Only **one** project file is read (first hit in the list above), and it is layered **on top of**
the personal `~/.config/zed/AGENTS.md`, which is always-on and applies to every workspace. Project
instructions take priority over the personal file when the two conflict.

`.rules` is a **Zed-native legacy filename kept for cross-tool back-compat** — new projects should
prefer `AGENTS.md` per the open https://agents.md/ standard, which Zed natively supports.
**gald3r ships `AGENTS.md`** (not `.rules`) as its project-instructions target, consistent with
every other AGENTS.md-native platform in this repo; if a project already has a `.rules` file from
an older Cursor/Windsurf/Cline setup, that file wins over gald3r's `AGENTS.md` until it is removed
or renamed — flag this to the user rather than silently overwriting `.rules`.

## Cross-Tool Reuse

Zed's Agent Skills format (`SKILL.md` with `name`/`description` YAML frontmatter + Markdown body,
folder-per-skill, direct children only — no nested groups) discovered from **`.agents/skills/`**
(project) and **`~/.agents/skills/`** (global) is the **same shared convention** gald3r already
targets for Codex, Amp, and Deep Code — gald3r's `g-skl-*/SKILL.md` files are drop-in native, no
adaptation needed.

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Rules / instructions | project-root `AGENTS.md` (loses to a pre-existing `.rules` file — see precedence table); personal `~/.config/zed/AGENTS.md` (%APPDATA%\Zed\AGENTS.md on Windows) is user-owned, not gald3r-written |
| Skills | `.agents/skills/<name>/SKILL.md` (native, shared cross-client convention — same tree as Codex/Amp/Deep Code) |
| Commands | **none** — Zed has no dedicated user-authored slash-command/prompt-library file format; Skills (invoked via `/` or `@skill`) are the command surface |
| Agents | **none project-scoped** — Zed's own Agent Profiles are UI-configured, and External Agents (Claude Code, Kimi Code, Codex, etc.) are hosted via ACP with their own native config, not a gald3r-writable `agents/` folder |
| MCP | `.zed/settings.json` → `context_servers.<name>` (local: `command`/`args`/`env`; remote: `url`/`headers`) — Zed-owned file, gald3r ships a merge-snippet reference rather than overwriting it |
| ACP external agents | `.zed/settings.json` → `agent_servers.<name>` (`type: "custom"`, `command`, `args`, `env`) — this is Zed's distribution channel for hosting Claude Code/Kimi Code/Codex/etc. as first-class agent-panel threads |
| Hooks | **not supported** — no documented lifecycle-event/hook system for hand-authored hooks |

## Capability Note

Zed natively supports Agent Skills (`.agents/skills/`), the open `AGENTS.md` rules standard at both
project and personal scope, and native MCP (`context_servers` in `settings.json`). It has **no**
gald3r-writable project-level custom-commands file format (Skills fill that role) and **no**
project-scoped subagent/agent-roster file gald3r can populate — Zed's own Agent Profiles are
UI-managed, and third-party coding agents (Claude Code, Kimi Code, Codex, ...) attach as **External
Agents** through the Agent Client Protocol (ACP), configured via `agent_servers` in
`.zed/settings.json`, not a gald3r overlay file. There is **no** lifecycle-hook system exposed for
hand-authored hooks. See `PLATFORM_SPEC.md` for full verification evidence and source URLs.
