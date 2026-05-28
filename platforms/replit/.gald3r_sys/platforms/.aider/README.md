# Aider — gald3r Deploy Scaffold

**Config folder**: `.aider/`

This directory is the gald3r deploy scaffold for **Aider**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity
sync tooling.

Authoritative install + customization guide: **`g-skl-platform-aider`** (.gald3r_sys/skills/g-skl-platform-aider/SKILL.md).

## Files in this scaffold

| File | Purpose |
|------|---------|
| **`PLATFORM_SPEC.md`** | Honest per-capability status for Aider (hooks/rules/skills/commands/MCP), folder model, and Known Gaps (§9). Read this first to understand what gald3r can and cannot do on Aider. |
| `aider_instructions.md` | Deploy guide — folder layout, config files, conventions, gitignore decision. |
| `.aider.conf.yml` | Aider config shipped to project root (model placeholder, `auto-commits: false`, `read:` context). |
| `CONVENTIONS.md` | gald3r behavioral surface, pinned read-only via `read:`. |

## Honest capability summary

Aider is the most minimal gald3r target — a single-assistant terminal REPL. It has
**no agents, no skill discovery, no rules folder, no lifecycle hooks, and no native MCP**
(RFC open). The one capability that maps cleanly is **read-only context pinning**
(`read:` / `/read-only` + repo map), through which gald3r delivers `CONVENTIONS.md` and
pinned `.gald3r/` files. The many `❌` marks in `PLATFORM_SPEC.md` are accurate
assessments of a minimal CLI, not deploy failures.

> **Status (T1277 — complete):** the full per-platform deploy payload is authored.
> See **`aider_instructions.md`** in this directory for the deploy guide (folder layout, config files,
> conventions, and the T1277 AC6 gitignore decision). The config files this platform
> consumes are shipped alongside it.
