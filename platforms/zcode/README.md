# ZCode Platform Template

**Tier 3 - Experimental**

This folder is a complete, ready-to-deploy gald3r template targeted at **ZCode** (Z.ai / Zhipu).

## What this is

A pre-built gald3r template containing skills configured for the ZCode Agentic Development
Environment (GLM-5.2, BYOK-capable). Drop this folder's contents into your project root and run
the bootstrap to get a gald3r setup tuned for ZCode.

## How to install

1. Clone or download this folder.
2. Copy the contents of `zcode/` into the root of your project.
3. Restart ZCode so it picks up the new configuration.
4. See the full setup guide at the [main gald3r README](../README.md).

## Tier definition

**Tier 3 - Experimental** -- Scaffold available. May have structural issues, missing features, or untested edge cases.

ZCode natively supports Agent Skills, `AGENTS.md` instructions, MCP, and slash commands. Subagents
are Beta and global/user-level only (no project-level agent roster yet), and there is no
lifecycle-hook system exposed for hand-authored hooks — see `PLATFORM_SPEC.md` for the full
capability picture and source URLs.

## Related

- [gald3r main README](../README.md) -- full feature documentation + platform comparison matrix
- [CHANGELOG](../CHANGELOG.md) -- release history
