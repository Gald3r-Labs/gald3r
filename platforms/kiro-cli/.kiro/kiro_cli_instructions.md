# Kiro CLI Platform — gald3r Configuration Guide

**Platform**: Kiro CLI (Amazon's terminal agent — the Q Developer CLI rebrand). Distinct from Kiro IDE.
**Config Folder**: `.kiro/` (shared namespace with Kiro IDE; richer agent/hook/command/skills surface)
**gald3r Version**: 1.0.0
**Official Docs**: https://kiro.dev/docs/cli/
**Instruction File**: `.kiro/steering/*.md` (foundation files auto-loaded) + root `AGENTS.md`. Kiro CLI does NOT read `CLAUDE.md`.
**Authoritative skill**: `g-skl-platform-kiro-cli`
**Capability detail**: see `../README.md` and `g-skl-platform-kiro-cli`

---

## Folder Layout

```
<project-root>/
├── AGENTS.md                       # instruction file Kiro CLI reads (alongside steering)
└── .kiro/
    ├── steering/   *.md            # always-injected context (product / tech / structure)
    ├── rules/      g-rl-*.md       # gald3r rule subset (.md)
    ├── agents/     g-agnt-*.md     # JSON/markdown custom agents + subagents
    ├── skills/     <name>/SKILL.md # Agent Skills (auto-loaded from .kiro/skills/ + ~/.kiro/skills/)
    └── settings/   mcp.json        # MCP server config (key mcpServers)
```

Rules use the plain **`.md`** extension. Skills are also auto-discovered from `~/.kiro/skills/`.

---

## Cross-Tool Reuse (important)

Kiro CLI reads `AGENTS.md` (not `CLAUDE.md`) and auto-discovers `SKILL.md` under `.kiro/skills/`,
so gald3r's `AGENTS.md` + `SKILL.md` artifacts are drop-in reusable. Commands route through
skills/prompts; hooks wire per-agent-JSON via STDIN.

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | `.kiro/skills/<name>/SKILL.md` (also `~/.kiro/skills/`) |
| Agents | `.kiro/agents/g-agnt-*` (JSON / markdown custom agents) |
| Rules | `.kiro/rules/g-rl-*.md` + `.kiro/steering/*.md` (always-injected) |
| Commands | route through skills / prompts |
| MCP | `.kiro/settings/mcp.json` + `~/.kiro/settings/mcp.json` |

## Capability Note

Kiro CLI has **near-full parity** — natively supports commands, rules, agents, skills, hooks, and
MCP. It shares the `.kiro/` directory and steering mechanism with Kiro IDE but has a richer
agent/hook/command/skills surface (see `g-skl-platform-kiro` for the IDE variant).
