# Kimi Code (Moonshot AI) + gald3r

**Tier 1 — Fully Supported**

[Kimi Code](https://www.kimi.com/code) is Moonshot AI's next-generation terminal AI coding agent — 8,700+ GitHub stars, 97+ releases, actively maintained. Supports VS Code extension, ACP protocol for JetBrains/Zed integration, and full MCP.

## Why Tier 1?

- **AGENTS.md support**: Reads `AGENTS.md` for project guidance — cross-platform compatible
- **MCP**: Full MCP tool integration
- **8,700+ stars**: Strong community adoption
- **VS Code + JetBrains + Zed**: Broad IDE coverage via ACP
- **Context**: Kimi models known for massive context windows

## Quick Start (New Project)

1. Install the **Kimi Code** VS Code extension (`moonshot-ai.kimi-code`) from VS Code Marketplace
2. Or use CLI: log in with `kimi login`, then run `kimi acp` for IDE integration
3. Copy the `kimi/` folder contents to your project root
4. Open your project — Kimi Code reads `AGENTS.md` automatically

## What's Inside

```
kimi/
  AGENTS.md             # Project guidance (auto-read by Kimi Code)
  README.md             # This file
```

## ACP Integration

Kimi Code supports the Agent Client Protocol for multi-IDE use:

```bash
kimi acp   # Start ACP server for JetBrains, Zed, or custom clients
```

## Documentation

- **Primary**: [kimi.com/code/docs/en](https://www.kimi.com/code/docs/en)
- **GitHub**: [MoonshotAI/kimi-cli](https://github.com/MoonshotAI/kimi-cli)
