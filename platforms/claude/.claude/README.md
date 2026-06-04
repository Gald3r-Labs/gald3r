<!-- subsystem_memberships: [PLATFORM_INTEGRATION] -->

# .claude/ — gald3r Deploy Scaffold (Claude Code)

This folder is the per-platform deploy scaffold for **Claude Code** (Anthropic's
agentic coding CLI + VS Code extension). It is installed into a project's `.claude/`
when the `claude` platform is selected during setup.

## Read this first: PLATFORM_SPEC.md

**[`PLATFORM_SPEC.md`](./PLATFORM_SPEC.md)** is the honest, per-platform integration
report for Claude Code (authored under T1462, the Phase 1 platform spec task). It
documents — section by section — what gald3r integration is **verified working** on
Claude Code vs. what is **partial / Cursor-generic / untested**, plus a Known Gaps
table (§9). If something in this scaffold looks off, the spec explains why.

Capability summary (from the spec):

| Hooks | Rules | Skills | Commands | MCP |
|---|---|---|---|---|
| ⚠️ partial | ✅ | ✅ | ✅ | ✅ |

## Files in this scaffold

| File | Purpose |
|---|---|
| `PLATFORM_SPEC.md` | Honest integration report — read first (see above) |
| `CLAUDE.md` | Project instruction file (loaded every session; `@AGENTS.md`-imports the shared source of truth) |
| `claude_instructions.md` | Human-facing setup/config guide for this platform |
| `settings.json` | Official Claude Code config surface — permissions, env, `mcpServers`, and the official `"hooks"` block |
| `settings.local.json` | User-local overrides (gitignored) |
| `local.settings.json` | Legacy/local overrides (non-standard name; see PLATFORM_SPEC §9 gap #5) |
| `hooks.json` | gald3r hook wiring — NON-standard top-level file; see the hook-config gap below |
| `hooks/` | Hook scripts (`g-hk-*.ps1`) + companion `g-hk-*.md` (T1171) |

## Known gap — hook configuration (PLATFORM_SPEC §6 / §9)

The biggest open item for Claude Code parity is the **hook config surface**:

- Claude Code's **official, supported** hook config lives in `settings.json` under the
  `"hooks"` key, with **capitalized** lifecycle event names (`SessionStart`, `Stop`,
  `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `SubagentStop`,
  `PreCompact`, `SessionEnd`) and a **matcher-grouped** shape.
- gald3r **also** ships a top-level `hooks.json` whose `sessionStart` / `stop` /
  `beforeShellExecution` entries use **lowercase** event names (Cursor-era) and a flat
  shape. `beforeShellExecution` has **no official Claude Code equivalent**. Those
  lowercase entries may **silently not fire** on current Claude Code.
- The `PreToolUse` block inside `hooks.json` already uses the correct nested
  `{ matcher, hooks:[{ type:"command", command }] }` shape and is the most likely to fire.

This scaffold **intentionally preserves both surfaces** rather than guessing at a
migration (the migration is tracked as a follow-up). `hooks.json` carries inline
`_gap` annotations pointing back to PLATFORM_SPEC §6/§9 so a deploying user understands
the situation. Do **not** delete working config when consolidating — verify firing
behavior first (`@g-platform-scan-docs claude` + a hook-firing smoke test).

## Maintenance

The authoritative source for the human-facing guide is the matching
`g-skl-platform-claude` skill. Update the skill, then re-run
`custom_scripts/platform_parity_sync.ps1 -Sync` to propagate. The spec recommends
re-running `@g-platform-scan-docs claude` to upgrade the `❓` rows in PLATFORM_SPEC §6.
