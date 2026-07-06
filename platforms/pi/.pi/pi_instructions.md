# Pi Platform — gald3r Configuration Guide

**Platform**: Pi (badlogic/pi-mono) — minimal, open-source terminal coding-agent harness
(67.5k+ GitHub stars). CLI/TUI only — no GUI, no Settings panels, no marketplace.
**Config Folder**: `.pi/` (project-scoped config; global config lives at `~/.pi/agent/`)
**gald3r Version**: 1.0.0
**Official Docs**: https://pi.dev/docs/latest/usage
**Instruction File**: root `AGENTS.md` (`CLAUDE.md` also accepted as an alias), merged via genuine
**hierarchical concatenation** — global `~/.pi/agent/AGENTS.md` first, then every matching file
found walking **up** from the current working directory, then the current directory's own file.
This is NOT a flat two-scope append (unlike ZCode) — it is closer to Cursor/Qwen/Gemini's
hierarchical model.
**Authoritative skill**: `g-skl-platform-pi`
**Capability detail**: see `../PLATFORM_SPEC.md`

---

## Folder Layout

```
<project-root>/
├── AGENTS.md                        # instruction file — hierarchical concat with ~/.pi/agent/AGENTS.md
└── .pi/
    ├── skills/   <name>/SKILL.md    # Agent Skills (YAML frontmatter: name, description + Markdown body)
    ├── prompts/  <name>.md          # prompt templates == slash commands, invoked /name
    ├── extensions/ gald3r-hooks.ts  # TypeScript lifecycle-hook extension (pi.on(event, handler))
    └── settings.json                # project settings (merges over global; `extensions:` array)

~/.pi/agent/                         # global config root (override via $PI_CODING_AGENT_DIR)
├── AGENTS.md                        # global/user instructions — read FIRST in the walk-up concat
├── SYSTEM.md / APPEND_SYSTEM.md     # optional system-prompt override/append (global scope)
├── skills/   <name>/SKILL.md        # global Agent Skills
├── prompts/  <name>.md              # global prompt templates
├── extensions/ <name>.ts            # global TypeScript extensions
└── settings.json                    # global settings

~/.agents/skills/                    # ALSO discovered (cross-tool shared skills location)
```

---

## Instruction File Merge Behavior (read carefully)

Pi reads **`AGENTS.md`** (or `CLAUDE.md`) via true **hierarchical directory-walk concatenation**:

1. `~/.pi/agent/AGENTS.md` (global, read first)
2. Every `AGENTS.md`/`CLAUDE.md` found walking **up** from the current working directory
3. The current directory's own file

"All matching files are concatenated." Disable entirely with `--no-context-files` / `-nc`. Unlike
ZCode's flat two-scope append, this genuinely merges across directory levels — a single
project-root `AGENTS.md` remains the simplest gald3r install target, but rule content MAY be split
across directory levels if that ever becomes useful.

Pi additionally supports **system-prompt override** distinct from `AGENTS.md`: `.pi/SYSTEM.md`
(project) or `~/.pi/agent/SYSTEM.md` (global) **replaces** the default system prompt;
`APPEND_SYSTEM.md` at either scope **appends** to it instead.

## Cross-Tool Reuse

Pi's Agent Skills format (`SKILL.md` with `name`/`description` YAML frontmatter + Markdown body,
folder-per-skill under `.pi/skills/<name>/`) implements the same agentskills.io standard gald3r
already targets — gald3r's `g-skl-*/SKILL.md` files are drop-in native, no adaptation needed. Pi
also scans the shared `~/.agents/skills/` and project `.agents/skills/` locations, so skills placed
there are cross-tool reusable with any other harness that honors the same standard.

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Rules / instructions | root `AGENTS.md` (hierarchical concat with `~/.pi/agent/AGENTS.md` + walk-up) |
| Skills | `.pi/skills/<name>/SKILL.md` (native, agentskills.io-compatible) |
| Commands | `.pi/prompts/<name>.md` (project) or `~/.pi/agent/prompts/<name>.md` (global); invoked `/name` |
| Agents | **not supported** — no project-level `agents/*.md` roster convention exists |
| Hooks | `.pi/extensions/gald3r-hooks.ts` — TypeScript extension registering `pi.on(event, handler)` calls |
| MCP | **not supported** — "No MCP" per the coding-agent README (explicit design choice) |

## Capability Note

Pi natively supports Agent Skills, hierarchical rules/instructions (`AGENTS.md`), prompt-template
slash commands, and TypeScript-extension lifecycle hooks. There is **no** project-level subagent
roster and **no MCP support** at all — do not fabricate either surface. See `PLATFORM_SPEC.md` for
full verification evidence and source URLs.
