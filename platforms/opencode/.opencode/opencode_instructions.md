# OpenCode Platform — gald3r Configuration Guide

**Platform**: OpenCode (open-source AI coding agent)
**Config Folder**: `.opencode/`
**gald3r Version**: 1.0.0
**Official Docs**: https://opencode.ai/docs
**Config File**: `opencode.json` (project root)

---

## Folder Layout

```
.opencode/
├── agents/          # Subagent definitions — invoked with @agent-name
│   └── g-agnt-*.md  # gald3r agents (g-agnt- prefix)
├── commands/        # Slash commands — invoked with /g-command-name
│   └── g-*.md
├── INSTALL.md       # Setup instructions for OpenCode
└── rules/           # Plain markdown rules (no YAML frontmatter required)
    └── g-rl-*.md    # gald3r enforcement rules (plain .md copies from .cursor/rules/)
```

**What gald3r writes here:**
- `agents/`, `commands/`, `rules/` (plain `.md`) — plus a root-level `opencode.json`.

**What gald3r does NOT emit here (but the platform supports):**
- No `plugins/` folder — OpenCode's hook mechanism IS the plugins system (JS/TS),
  but gald3r's PowerShell `.ps1` hooks are not portable to it (see "Hooks" below and
  PLATFORM_SPEC.md sections 6/9). This is a documented gap, not a platform limitation.
- gald3r serves skills from the shared `.claude/skills/` Claude Code path rather than
  copying them into `.opencode/skills/`, even though OpenCode discovers BOTH (see
  "Native Skills" below).

---

## What Makes OpenCode Unique

### Hooks — native plugin system; gald3r `.ps1` hooks are NOT portable
OpenCode **does** have a native hook system, but it is the **plugins** system, not a
PowerShell-script + `hooks.json` wiring like Cursor. Plugins are **JavaScript / TypeScript**
modules in `.opencode/plugins/` (and `~/.config/opencode/plugins/`) that export a function
receiving a context object (project info, cwd, git worktree path, an SDK client, Bun's shell
API) and return a hooks object. Verified lifecycle events include `tool.execute.before` /
`tool.execute.after`, `session.created` / `session.idle` / `session.compacted`,
`file.edited`, and `shell.env`.

gald3r ships its hooks as **PowerShell `g-hk-*.ps1`** scripts. These do **NOT** run natively
on OpenCode — there is no `.ps1`/JSON hook wiring. Bridging them would require a JS/TS plugin
shim that shells out to the PowerShell scripts via the plugin context's Bun shell API (e.g.
mapping `sessionStart` -> `session.created`, `stop` -> `session.idle`, `beforeShellExecution`
-> `tool.execute.before`). Until that shim exists, gald3r hook automation on OpenCode is a
documented gap. This scaffold therefore ships **no** `hooks.json` and **no** `.ps1` hook
wiring — importing Cursor's would silently never fire. See PLATFORM_SPEC.md sections 6 and 9
(gap #1).

### Native Skills — `.opencode/skills/` AND `.claude/skills/`
OpenCode has a native skills system with a dedicated `skill` tool. It discovers
folder-per-skill `SKILL.md` files from **`.opencode/skills/`**, **`.claude/skills/`**, and
**`.agents/skills/`** (plus global `~/.config/opencode/skills/`, `~/.claude/skills/`,
`~/.agents/skills/`), walking up from cwd to the git worktree root.

gald3r serves its skills from the shared **`.claude/skills/`** path (Claude Code
compatibility), so all gald3r `g-skl-*` skills are available in OpenCode sessions **without**
a separate `.opencode/skills/` copy. gald3r skill names (lowercase + hyphens) satisfy
OpenCode's `name` constraint (1–64 lowercase alphanumeric, single hyphens). gald3r's extra
frontmatter (`subsystem_memberships`, etc.) lands in the unvalidated metadata space and should
be tolerated, but this was verified by docs only, not by a live install run.

To explicitly disable the Claude Code skill path: `export OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`

See PLATFORM_SPEC.md section 4.

### opencode.json Controls Everything
The `opencode.json` at the project root is the master config for OpenCode:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "AGENTS.md",
    "GUARDRAILS.md",
    ".opencode/rules/*.md"
  ]
}
```

The `instructions` array accepts:
- Relative file paths (including glob patterns like `*.md`)
- Absolute file paths
- Remote URLs (fetched with 5s timeout)

**Important**: OpenCode reads `.opencode/rules/*.md` via the glob in `opencode.json`. The `.cursor/rules/*.mdc` files are NOT read directly — `.mdc` doesn't match `*.md`. This is why gald3r maintains a separate `.opencode/rules/` folder with plain `.md` copies of all rules.

### Rules Precedence
OpenCode looks for instruction files in this order:
1. Project `AGENTS.md` (highest priority)
2. `opencode.json` `instructions` array entries
3. Global `~/.config/opencode/AGENTS.md`
4. `CLAUDE.md` (Claude Code compatibility fallback)
5. `~/.claude/CLAUDE.md` (global Claude Code fallback)

### Claude Code Compatibility
OpenCode has built-in Claude Code compatibility. It reads:
- `CLAUDE.md` if no `AGENTS.md` exists
- `~/.claude/CLAUDE.md` as global fallback
- `.claude/skills/` for skills

gald3r has `AGENTS.md` at root, so `CLAUDE.md` is used as supplementary context only.

### Commands Use `/` Prefix
```
/g-setup
/g-task-new
/g-code-review
/g-workspace-status
/g-workspace-validate
/g-workspace-export --dry-run
/g-workspace-sync --dry-run
```

### Agents Use `@` Mention
OpenCode supports subagents that can be invoked with `@`:
```
@g-agnt-task-manager create a task for...
@g-agnt-code-reviewer review these files...
```

Agents are defined as markdown files in `.opencode/agents/`. They have YAML frontmatter for `description`, `mode`, and `tools`.

### Two Agent Types
OpenCode has two built-in agent types:
- **Primary agents** (Build, Plan) — main conversation agents, switch with Tab
- **Subagents** (General, Explore) — invoked via `@` for specific tasks

gald3r's `g-agnt-*` agents are configured as subagents.

---

## gald3r Naming Conventions

| Component | Prefix | Location |
|-----------|--------|----------|
| Agents | `g-agnt-` | `.opencode/agents/g-agnt-*.md` |
| Skills | `g-skl-` | loaded from `.claude/skills/g-skl-*/` |
| Commands | `g-` | `.opencode/commands/g-*.md` |
| Rules | `g-rl-` | `.opencode/rules/g-rl-*.md` |

---

## Rules Maintenance

The `.opencode/rules/` folder contains plain `.md` copies of the `.cursor/rules/*.mdc` files, with YAML frontmatter stripped. These are generated copies — **do not edit them directly**. When updating rules:

1. Edit the canonical version in `.cursor/rules/*.mdc`
2. Copy the content (without frontmatter) to `.opencode/rules/*.md`
3. Also update `.agent/rules/*.md` and `.claude/rules/*.md`

---

## FAQ

**Q: Why doesn't `.opencode/` have a `skills/` folder?**
A: OpenCode discovers native skills from `.opencode/skills/` AND `.claude/skills/` (and `.agents/skills/`). gald3r serves its skills from the shared `.claude/skills/` path, so all gald3r skills are available without a separate `.opencode/skills/` copy. (OpenCode does support a native `.opencode/skills/` folder — gald3r simply reuses the Claude Code path to avoid duplicating skill content.)

**Q: Why can't I use `.cursor/rules/*.mdc` directly in opencode.json?**
A: OpenCode's glob `*.md` doesn't match `.mdc` files. The `.opencode/rules/` folder contains plain `.md` versions that the `"instructions"` glob can find.

**Q: Why don't gald3r's hooks run on OpenCode?**
A: OpenCode DOES support lifecycle hooks — via its **plugins** system (JS/TS modules in `.opencode/plugins/`), not PowerShell scripts. gald3r ships hooks as PowerShell `g-hk-*.ps1` scripts, which are not portable to JS/TS plugins without a shim. So gald3r hook automation does not run natively on OpenCode today (documented gap, PLATFORM_SPEC.md sections 6/9). Behavioral enforcement instead carries through `AGENTS.md`/`CLAUDE.md` and the `instructions` files. This is a gald3r portability gap, not a missing OpenCode capability.

**Q: Is the gald3r skills content accessible?**
A: Yes — via `.claude/skills/` compatibility layer. OpenCode auto-loads these unless `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` is set.

---

## Comparison to Other Platforms

| Feature | OpenCode | Cursor | Claude Code | Gemini | Codex |
|---------|----------|--------|-------------|--------|-------|
| Rules format | `.md` via `opencode.json` | `.mdc` | `.md` | `.md` | via AGENTS.md |
| Command prefix | `/` | `@` | `/` | `/` | via AGENTS.md |
| Agents folder | ✅ `agents/` | ✅ `agents/` | ✅ `agents/` | ❌ `workflows/` | ❌ |
| Hooks | ⚠️ native plugins (JS/TS); gald3r `.ps1` not portable | ✅ Full | ✅ Full | ✅ Full | ❌ None |
| Skills | ✅ native (`.opencode/skills/` + `.claude/` compat) | ✅ auto | ✅ auto | ✅ auto | ✅ explicit |
| Config file | `opencode.json` | `hooks.json` | `settings.json` | `mcp_config.json` | `config.toml` |
| Project instructions | `AGENTS.md` + `opencode.json` | rules/ folder | `CLAUDE.md` + rules/ | `GEMINI.md` + rules/ | `AGENTS.md` |
