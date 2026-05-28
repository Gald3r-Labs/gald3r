# Continue + gald3r

**Tier 1 — Fully Supported**

[Continue](https://continue.dev) is the leading open-source AI coding assistant with 3M+ VS Code installs. It supports project-level rules (`.continue/rules/*.md`), MCP integration, custom prompts, and Hub-based rule sharing.

## Why Tier 1?

- **Rules system**: `.continue/rules/*.md` with YAML frontmatter — analogous to Cursor rules
- **MCP**: Full MCP server support via `config.yaml`
- **VS Code + JetBrains**: Broader IDE coverage than most platforms
- **3M+ installs**: Most popular open-source AI coding extension
- **Active**: Apache 2.0, maintained by Continue Dev Inc.

## Quick Start (New Project)

1. Install **Continue** from [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=Continue.continue) or JetBrains Marketplace
2. Copy the `continue/` folder contents to your project root
3. Open your IDE — Continue auto-loads rules from `.continue/rules/`

## What's Inside

```
continue/
  .continue/
    config.yaml           # Model configuration + rules references
    rules/
      gald3r.md           # gald3r project conventions (auto-loaded)
    prompts/
      gald3r-task.md      # Slash command: /gald3r-task
  README.md               # This file
```

## Rules Format

Rules in `.continue/rules/*.md` are auto-loaded for your workspace:

```markdown
---
name: gald3r-conventions
description: "gald3r framework conventions"
alwaysApply: true
---

# Your project conventions here
```

## MCP Configuration

In `.continue/config.yaml`:

```yaml
mcpServers:
  - name: my-server
    command: uvx
    args: [mcp-server-name]
```

## Documentation

- **Primary**: [docs.continue.dev](https://docs.continue.dev)
- **Rules deep-dive**: [docs.continue.dev/customize/deep-dives/rules](https://docs.continue.dev/customize/deep-dives/rules)
- **VS Code Marketplace**: [Continue extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue)
