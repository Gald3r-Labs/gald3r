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

**What OpenCode does NOT have:**
- No `hooks/` folder — OpenCode does not support lifecycle hooks
- No `skills/` folder — Skills are loaded via Claude Code compatibility (see below)

---

## What Makes OpenCode Unique

### No Hooks
OpenCode has no hook system. There is no equivalent of `sessionStart`, `stop`, or `beforeShellExecution`. All behavioral enforcement comes from AGENTS.md and the `rules/` files loaded via `opencode.json`.

### No Native Skills Folder
OpenCode does not auto-discover skills from `.opencode/skills/`. However, it **does** support Claude Code skill compatibility — skills in `.claude/skills/` are loaded automatically unless disabled.

To explicitly disable: `export OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`

This means all 17 gald3r skills from `.claude/skills/` are available in OpenCode sessions without any additional configuration.

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
A: OpenCode loads skills via Claude Code compatibility from `.claude/skills/`. All 17 gald3r skills are available without a separate `.opencode/skills/` copy.

**Q: Why can't I use `.cursor/rules/*.mdc` directly in opencode.json?**
A: OpenCode's glob `*.md` doesn't match `.mdc` files. The `.opencode/rules/` folder contains plain `.md` versions that the `"instructions"` glob can find.

**Q: Why no hooks?**
A: OpenCode (as of 2026) doesn't support lifecycle hooks. This is a platform limitation, not a gald3r choice. Behavioral enforcement is handled entirely through instructions files.

**Q: Is the gald3r skills content accessible?**
A: Yes — via `.claude/skills/` compatibility layer. OpenCode auto-loads these unless `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` is set.

---

## Comparison to Other Platforms

| Feature | OpenCode | Cursor | Claude Code | Gemini | Codex |
|---------|----------|--------|-------------|--------|-------|
| Rules format | `.md` via `opencode.json` | `.mdc` | `.md` | `.md` | via AGENTS.md |
| Command prefix | `/` | `@` | `/` | `/` | via AGENTS.md |
| Agents folder | ✅ `agents/` | ✅ `agents/` | ✅ `agents/` | ❌ `workflows/` | ❌ |
| Hooks | ❌ None | ✅ Full | ✅ Full | ✅ Full | ❌ None |
| Skills | via `.claude/` compat | ✅ auto | ✅ auto | ✅ auto | ✅ explicit |
| Config file | `opencode.json` | `hooks.json` | `settings.json` | `mcp_config.json` | `config.toml` |
| Project instructions | `AGENTS.md` + `opencode.json` | rules/ folder | `CLAUDE.md` + rules/ | `GEMINI.md` + rules/ | `AGENTS.md` |
