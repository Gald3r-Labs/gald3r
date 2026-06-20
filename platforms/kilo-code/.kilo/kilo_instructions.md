# Kilo Code Platform — gald3r Configuration Guide

**Platform**: Kilo Code (open-source AI coding agent; VS Code / JetBrains; Kilo Marketplace)
**Config Folder**: `.kilo/` (replaces legacy `.kilocode/`, auto-migrated and backward compatible)
**gald3r Version**: 1.0.0
**Official Docs**: https://kilo.ai/docs/
**Instruction File**: root `AGENTS.md` (root + subdirectory cascade; subdir precedence on conflict). Kilo does NOT read `CLAUDE.md`.
**Authoritative skill**: `g-skl-platform-kilo-code` (if present) / `g-skl-platform-cursor` (reference)
**Capability detail**: see `../PLATFORM_SPEC.md`

---

## Folder Layout

```
<project-root>/
├── AGENTS.md                         # instruction file Kilo reads (root + subdir cascade)
├── kilo.jsonc                        # central JSONC config (agent / mcp / skills keys, global rules)
└── .kilo/                            # replaces legacy .kilocode/ (auto-migrated)
    ├── rules/      g-rl-*.md         # Custom Rules (loaded automatically every interaction)
    ├── commands/   g-*.md            # Workflows / slash commands (/<name>)
    ├── agents/     g-agnt-*.md       # Custom Subagents (isolated sessions)
    └── skills/     <name>/SKILL.md   # Agent Skills (agentskills.io standard)
```

Rules use the plain **`.md`** extension. Global equivalents live under `~/.config/kilo/`
(`commands/`, `agents/`) and `~/.kilo/skills/`.

---

## Cross-Tool Reuse (important)

Kilo **also** discovers `.claude/skills/` (Claude Code compatibility) and `.agents/skills/`
(open Agent Skills standard, loaded by default), and reads `AGENTS.md` as-is. gald3r's
`SKILL.md` skill tree therefore works on Kilo with **no Kilo-specific port** — the `.kilo/`
copies shipped here are the explicit native form for projects that prefer the dedicated namespace.

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | `.kilo/skills/<name>/SKILL.md` (also `.claude/skills/` + `.agents/skills/`) |
| Agents | `.kilo/agents/g-agnt-*.md` (Custom Subagents) |
| Commands | `.kilo/commands/g-*.md` (Workflows / slash commands) |
| Rules | `.kilo/rules/g-rl-*.md` (always-loaded) |
| MCP | `kilo.jsonc` `mcp` key / `.mcp.json` |

## Capability Note

Five of the six gald3r-relevant mechanisms are NATIVE and documented (commands, rules, agents,
skills, MCP); **only lifecycle/event hooks are missing** (open feature request, GitHub Issue
#5827). gald3r `g-hk-*.ps1` hooks have no native auto-fire target — wire the commit/push subset
via git `core.hooksPath` if needed.
