# Kimi Code (Moonshot AI) + gald3r

**Tier 1 — Fully Supported**

[Kimi Code](https://www.kimi.com/code) is Moonshot AI's next-generation terminal AI coding agent —
actively maintained, with a VS Code extension, ACP protocol for JetBrains/Zed integration, and full
MCP support.

> **Rebrand note (2026-07-03):** the GitHub repo was renamed `MoonshotAI/kimi-cli` →
> `MoonshotAI/kimi-code` (v0.22.2) in the same release that moved the CLI from Python/uv to
> Node.js. The config directory renamed with it: `.kimi/` → **`.kimi-code/`** (project),
> `~/.kimi/` → **`~/.kimi-code/`** (user, override via `KIMI_CODE_HOME`). See
> `../PLATFORM_SPEC.md` for the full re-verification. "Kcode" is not a distinct product — it
> resolves to this same Kimi Code rebrand.

## Why Tier 1?

- **AGENTS.md support**: Reads `AGENTS.md` for project guidance — cross-platform compatible
- **MCP**: Full MCP tool integration
- **VS Code + JetBrains + Zed**: Broad IDE coverage via ACP
- **Context**: Kimi models known for massive context windows

## Quick Start (New Project)

1. Install the **Kimi Code** VS Code extension (`moonshot-ai.kimi-code`) from VS Code Marketplace
2. Or use CLI: log in with `kimi login`, then run `kimi acp` for IDE integration
3. Copy the `kimi/` folder contents to your project root
4. Open your project — Kimi Code reads `AGENTS.md` automatically; skills load from
   `.kimi-code/skills/` (native) or `.agents/skills/` (cross-tool)

## What's Inside

```
kimi/
  AGENTS.md             # Project guidance (auto-read by Kimi Code)
  README.md             # This file
  .kimi/                # NOTE: legacy dir name kept for the shipped overlay tree;
                         # the current CLI convention is .kimi-code/ — see PLATFORM_SPEC.md
```

## ACP Integration

Kimi Code supports the Agent Client Protocol for multi-IDE use:

```bash
kimi acp   # Start ACP server for JetBrains, Zed, or custom clients
```

## Documentation

- **Primary**: [kimi.com/code/docs/en](https://www.kimi.com/code/docs/en)
- **GitHub**: [MoonshotAI/kimi-code](https://github.com/MoonshotAI/kimi-code) (renamed from `kimi-cli`)
