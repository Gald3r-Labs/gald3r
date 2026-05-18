# .copilot/ — gald3r Copilot Platform Config

## Phase 1: Fully Compatible Target (Current)

GitHub Copilot is supported as gald3r's **6th IDE platform** at the "compatible" level.

### What's Available Now

| Feature | Location | Status | Notes |
|---------|----------|--------|-------|
| Always-apply rules | `.github/copilot-instructions.md` | ✅ Active | Auto-generated |
| Commands (`g-*`) | `.copilot/commands/` | ✅ Active | Reference docs for CLI |
| Skills | `.claude/skills/` | ✅ Active | Auto-discovered by Copilot |
| Agents | `.github/agents/` | ✅ Active | 10 gald3r agents |
| Hooks | `.github/hooks/gald3r-hooks.json` | ✅ Active | JSON format |
| Prompt files | `.github/prompts/` | ✅ Active | VS Code prompt picker |
| MCP | `mcp.json` / `/mcp add` | ✅ Active | Requires MCP server URL |

### The .github/ vs .copilot/ Split

All Copilot-native customization lives in `.github/`:

```
.github/
├── copilot-instructions.md  ← Always-apply rules (auto-generated)
├── agents/                  ← Custom agent definitions
├── hooks/                   ← Lifecycle hooks (JSON format)
├── prompts/                 ← Prompt templates (VS Code only)
└── instructions/            ← Path-specific rules (optional, Phase 2)
```

`.copilot/commands/` is a **gald3r convention** — it stores command reference docs for human and agent lookup. GitHub Copilot itself does not read this directory.

**Skills**: Copilot auto-discovers skills from `.claude/skills/` natively — no copy to `.github/skills/` needed.

### Regenerating .github/ Targets

Run after modifying rules, agents, hooks, or commands:

```powershell
.\scripts\generate_copilot_instructions.ps1
```

This generates:
1. `.github/copilot-instructions.md` — from `.cursor/rules/g-rl-*.mdc`
2. `.github/agents/` — from `.claude/agents/g-agnt-*.md`
3. `.github/hooks/gald3r-hooks.json` — lifecycle hook JSON wrapper
4. `.github/prompts/` — from `.cursor/commands/*.md` (renamed to `.prompt.md`)

### Phase 2 (Future)

Phase 2 will wire gald3r MCP tools (`gald3r_valhalla` public URL) directly to Copilot CLI, enabling full slash command support and deeper agent capabilities. See task149 for the implementation plan.
