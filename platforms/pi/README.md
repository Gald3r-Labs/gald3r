# Pi Platform Template

**Tier 3 - Experimental**

This folder is a complete, ready-to-deploy gald3r template targeted at **Pi**
(badlogic/pi-mono terminal coding-agent harness).

## What this is

A pre-built gald3r template containing skills configured for the Pi coding-agent CLI/TUI
(67.5k+ GitHub stars, minimal open-source harness). Drop this folder's contents into your project
root and run the bootstrap to get a gald3r setup tuned for Pi.

## How to install

1. Clone or download this folder.
2. Copy the contents of `pi/` into the root of your project.
3. Restart Pi (or start a new session) so it picks up the new configuration.
4. See the full setup guide at the [main gald3r README](../README.md).

## Tier definition

**Tier 3 - Experimental** -- Scaffold available. May have structural issues, missing features, or untested edge cases.

Pi natively supports Agent Skills, hierarchical `AGENTS.md` instructions, prompt-template slash
commands, and TypeScript-extension lifecycle hooks. There is no project-level subagent roster and
no MCP support at all (explicit design choice) — see `PLATFORM_SPEC.md` for the full capability
picture and source URLs.

## Related

- [gald3r main README](../README.md) -- full feature documentation + platform comparison matrix
- [CHANGELOG](../CHANGELOG.md) -- release history
