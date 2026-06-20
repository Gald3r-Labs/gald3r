# Qoder Platform — gald3r Configuration Guide

**Platform**: Qoder (agentic IDE)
**Config Folder**: `.qoder/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.qoder.com
**Instruction File**: root `AGENTS.md` (`.qoder/rules` takes precedence on conflict). Qoder does NOT read `CLAUDE.md`.
**Authoritative skill**: `g-skl-platform-qoder` (if present) / `g-skl-platform-cursor` (reference)
**Capability detail**: see `../PLATFORM_SPEC.md`

---

## Folder Layout

```
<project-root>/
├── AGENTS.md                         # instruction file Qoder reads (.qoder/rules wins on conflict)
└── .qoder/
    ├── rules/        g-rl-*.md       # Always Apply / Model Decision / Specific Files / Apply Manually
    ├── commands/     g-*.md          # custom slash commands (invoke with /)
    ├── agents/       g-agnt-*.md     # Custom Agents / subagents (markdown + YAML frontmatter)
    ├── skills/       <name>/SKILL.md # Agent Skills (SKILL.md / agentskills.io standard)
    └── .mcp.json                     # MCP configuration (reference template)
```

Rules use the plain **`.md`** extension. User-level (`~/.qoder/…`) and project-level
(`<project>/.qoder/…`) variants exist for commands, rules, agents, and skills.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | `.qoder/skills/<name>/SKILL.md` |
| Agents | `.qoder/agents/g-agnt-*.md` (Custom Agents) |
| Commands | `.qoder/commands/g-*.md` (slash commands) |
| Rules | `.qoder/rules/g-rl-*.md` |
| MCP | `.qoder/.mcp.json` (reference template; key `mcpServers`) |

## Capability Note

Qoder supports **all six** gald3r-relevant primitives — custom slash commands, rules/memory,
subagents (Custom Agents), Agent Skills, lifecycle hooks, and MCP. Hooks + MCP configuration
live in `.qoder/settings.json` on Qoder; this scaffold ships the MCP reference at `.qoder/.mcp.json`.
**Memory** is a separate UI/Knowledge-Center-managed store, not a flat editable file.
