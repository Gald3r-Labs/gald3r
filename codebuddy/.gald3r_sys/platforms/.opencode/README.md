<!-- subsystem_memberships: [PLATFORM_INTEGRATION] -->

# .opencode/ — gald3r Deploy Scaffold (OpenCode)

This folder is the per-platform deploy scaffold for **OpenCode** (`sst/opencode`),
an open-source, terminal-first AI coding agent. It is installed into a project's
`.opencode/` (plus a root-level `opencode.json`) when the `opencode` platform is
selected during setup.

## Read this first: PLATFORM_SPEC.md

**[`PLATFORM_SPEC.md`](./PLATFORM_SPEC.md)** is the honest, per-platform integration
report for OpenCode (authored under T1470, the Phase 1 platform spec task; copied
here under T1495). It documents — section by section — what gald3r integration is
**verified-by-docs** on OpenCode vs. what is **partial / untested**, plus a Known
Gaps table (section 9). If something in this scaffold looks off, the spec explains
why. Verification basis = a doc-citation scan of https://opencode.ai/docs on
2026-05-26; NOT a live install run in this repo.

Capability summary (from the spec):

| Hooks | Rules | Skills | Commands | MCP |
|---|---|---|---|---|
| WARNING partial | WARNING partial | WARNING partial | WARNING partial | WARNING partial |

(Legend: verified working / WARNING partial-or-untested / not-supported. See the
spec's Capability Summary table for the emoji-rendered version.)

## Files in this scaffold

| File | Purpose |
|---|---|
| `PLATFORM_SPEC.md` | Honest integration report — read first (see above) |
| `opencode_instructions.md` | Human-facing setup/config guide for this platform |

> **Note on config artifacts:** this scaffold ships docs only. gald3r does NOT emit a
> generated `opencode.json`, `.opencode/plugins/` hook shim, or pre-built agent/command
> files here. The root `opencode.json` `instructions` array, native skill discovery
> (`.opencode/skills/` + `.claude/skills/`), and `AGENTS.md`/`CLAUDE.md` are what carry
> gald3r content to OpenCode — see the instructions file and the spec.

## Known gaps (PLATFORM_SPEC sections 6 / 9)

The two biggest open items for OpenCode parity are documented in the spec and
reflected in the instructions guide:

- **Hooks: gald3r `.ps1` hooks are NOT portable** (spec section 6, gap #1). OpenCode
  DOES have a native hook system — but it is the **plugins** system (JavaScript /
  TypeScript callbacks in `.opencode/plugins/`), not PowerShell scripts wired through a
  `hooks.json` file. gald3r's `g-hk-*.ps1` hooks do not run natively; a JS/TS plugin
  shim that shells out to the PowerShell scripts (via the plugin context's Bun shell
  API) would be required. Until that shim exists, gald3r hook automation on OpenCode is
  a documented gap. The scaffold ships NO `hooks.json` and NO `.ps1` hook wiring —
  importing Cursor's would be misleading because it would silently never fire.
- **Rules: no `.mdc` glob-scoped rule engine** (spec section 7, gap #2). OpenCode has
  no `.cursor/rules/*.mdc` equivalent. Rule *content* carries via `AGENTS.md` /
  `CLAUDE.md` (read directly) and/or a `.opencode/rules/*.md` glob referenced from the
  `opencode.json` `instructions` array; the per-rule `alwaysApply`/`globs` *scoping*
  does not transfer (everything becomes effectively always-on).

## Positive parity (better than the original scaffold doc assumed)

The prior `opencode_instructions.md` claimed OpenCode had **no hooks** and **no native
skills folder**. The 2026-05-26 doc scan corrected both:

- OpenCode **does** have a native hook system (plugins) — the gap is `.ps1` portability,
  not the absence of hooks.
- OpenCode **does** have native skill discovery from `.opencode/skills/` (in addition to
  the `.claude/skills/` Claude Code compatibility path).

The instructions file in this folder has been updated to reflect these findings.

## Maintenance

The authoritative source for the human-facing guide is the matching
`g-skl-platform-opencode` skill (`.gald3r_sys/skills/g-skl-platform-opencode/SKILL.md`).
The `PLATFORM_SPEC.md` here is a straight copy of that skill's spec — do not edit the
copy directly; update the skill source and re-run
`custom_scripts/platform_parity_sync.ps1 -Sync` to propagate. The spec recommends
running `@g-platform-scan-docs opencode` + a live `opencode --version` install test to
upgrade the untested rows.
