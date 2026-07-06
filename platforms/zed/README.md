# Zed Platform Template

**Tier 3 - Experimental**

This folder is a complete, ready-to-deploy gald3r template targeted at **Zed** (agent panel + ACP
host).

## What this is

A pre-built gald3r template containing skills configured for **Zed**, the Rust-native code editor
whose Agent Panel hosts both its own built-in Zed Agent and **External Agents** (Claude Code, Kimi
Code, Codex, and others) via the open **Agent Client Protocol (ACP)**. Drop this folder's contents
into your project root to get a gald3r setup tuned for Zed.

## How to install

1. Clone or download this folder.
2. Copy the contents of `zed/` into the root of your project.
3. Restart Zed so it picks up the new configuration.
4. See the full setup guide at the [main gald3r README](../README.md).

## Tier definition

**Tier 3 - Experimental** -- Scaffold available. May have structural issues, missing features, or
untested edge cases.

Zed natively supports Agent Skills (`.agents/skills/`, the shared cross-client convention), the
open `AGENTS.md` standard (personal + project scopes), and native MCP (`context_servers`) — plus a
project-root `.rules` file that takes precedence over `AGENTS.md` for backward compatibility with
`.cursorrules`/`.windsurfrules`/`.clinerules`-era projects. There is no gald3r-writable
project-level custom-commands or hooks surface — see `PLATFORM_SPEC.md` for the full capability
picture and source URLs.

## Related

- [gald3r main README](../README.md) -- full feature documentation + platform comparison matrix
- [CHANGELOG](../CHANGELOG.md) -- release history
