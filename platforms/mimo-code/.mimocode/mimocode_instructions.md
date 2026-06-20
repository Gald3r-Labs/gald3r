# MiMo-Code Platform — gald3r Configuration Guide

**Platform**: Xiaomi MiMo-Code (OpenCode fork by Xiaomi)
**Config Folder**: `.mimocode/`
**Config File**: `mimocode.json` (project root)
**Official Docs**: https://mimo.xiaomi.com/mimocode
**GitHub**: https://github.com/XiaomiMiMo/MiMo-Code
**gald3r Version**: 1.0.0

---

## Quick Setup

1. Copy `.mimocode/` into your project root
2. Copy `mimocode.json` into your project root
3. Copy `AGENTS.md` (and optionally `MEMORY.md`) into your project root
4. Run `mimocode` in the project directory

## Key Files

| File | Purpose |
|---|---|
| `AGENTS.md` | Primary instruction file (read natively) |
| `MEMORY.md` | Persistent cross-session project memory |
| `CLAUDE.md` | Claude Code compat layer |
| `mimocode.json` | Primary config + MCP wiring |
| `.mimocode/agents/*.md` | Custom agent definitions |
| `.mimocode/commands/*.md` | Slash commands (`/g-*`) |

## Platform Notes

MiMo-Code is based on OpenCode (anomalyco/opencode fork by Xiaomi).
It uses the same `.claude/skills/` discovery path as OpenCode for gald3r skills.
See `PLATFORM_SPEC.md` for the full capability analysis.
