# Amp Code (Sourcegraph) + gald3r

**Tier 1 — Fully Supported**

[Amp](https://ampcode.com) is the frontier coding agent built by Sourcegraph, rebuilt from the ground up in May 2026. It features subagent spawning, Oracle reasoning (GPT-5.5 high), MCP integration, and a skills system at `.agents/skills/`.

## Why Tier 1?

- **Native skill compatibility**: Amp reads `.claude/skills/` as a fallback — gald3r skills work without extra setup
- **AGENTS.md**: Analogous to CLAUDE.md / Cursor rules — full project guidance support
- **MCP**: Full MCP server support via VS Code `settings.json`
- **Active**: Rebuilt May 2026, hot in the developer community

## Quick Start (New Project)

```bash
# Install Amp CLI
curl -fsSL https://ampcode.com/install.sh | bash

# Or via npm
npm install -g @ampcode/cli
```

1. Copy the `amp/` folder contents to your project root
2. Install gald3r for your other IDEs using the appropriate platform folder
3. Run `amp` to start

## What's Inside

```
amp/
  .agents/
    skills/
      gald3r/
        SKILL.md          # gald3r project conventions for Amp
  AGENTS.md               # Project guidance (architecture, build/test commands)
  README.md               # This file
```

## Migration from Cursor / Claude Code

Amp supports one-command migration:

```bash
# From Cursor
mv .cursorrules AGENTS.md && ln -s AGENTS.md .cursorrules

# From Claude Code
mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md
```

## Documentation

- **Primary**: [ampcode.com/manual](https://ampcode.com/manual)
- **Sourcegraph overview**: [sourcegraph.com/amp](https://sourcegraph.com/amp)
