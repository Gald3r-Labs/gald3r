# Platform Support — all 38 platforms, with the honest gaps marked

**One binary, every platform.** Download `gald3r` from
[gald3r_core releases](https://github.com/Gald3r-Labs/gald3r_core/releases), run
`gald3r setup` in your project, then `gald3r platform install <name>` for your tool
below — the binary generates the exact, always-current overlay for that platform.

This matrix is ported from the canonical, hand-verified capability matrix in the
engine repo (reconciled 2026-08-03, task T624). It deliberately marks what does
**not** function today, not just what does — including which gaps are platform
limitations and which are gald3r-side follow-ups already tracked as tasks.

Legend: ✅ verified working · ⚠️ partial · ❌ not supported today · ❓ untested.

| Platform | Hooks | Rules | Skills | Commands | MCP | Engine tier |
|---|---|---|---|---|---|---|
| aider | ⚠ | ✅ | ❌ | ⚠ | ❌ | CLI (L1) |
| amp | ❌ | ✅ | ✅ | ❓ | ✅ | MCP (L2) |
| antigravity | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| astrbot | ❌ | ✅ | ✅ | ❓ | ✅ | MCP (L2) |
| augment | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| claude | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| cline | ⚠ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| codebuddy | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| codex | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| continue | ❌ | ✅ | ⚠ | ✅ | ✅ | MCP (L2) |
| copilot | ⚠ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| cursor | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| deepcode | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| goose | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| hermes | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| junie | ⚠ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| kilo_code | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| kimi | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| kiro | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| kiro_cli | ⚠ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| mimo-code | ⚠ | ✅ | ⚠ | ✅ | ✅ | MCP (L2) |
| mistral | ⚠ | ⚠ | ✅ | ⚠ | ✅ | MCP (L2) |
| openclaw | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| opencode | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| openhands | ✅ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| pi | ✅ | ✅ | ✅ | ✅ | ❌ | CLI (L1) |
| qoder | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| qwen | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| replit | ❌ | ✅ | ✅ | ❌ | ✅ | MCP (L2) |
| roo | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| trae | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| void | ❌ | ✅ | ❌ | ❌ | ✅ | MCP (L2) |
| warp | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) |
| windsurf | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| zcode | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) |
| zed | ❌ | ✅ | ✅ | ❌ | ✅ | MCP (L2) |
| subq | ❌ | ❌ | ❌ | ❌ | ❌ | files-only (L0) |

## Reading the columns

- **Hooks** — native lifecycle-hook wiring. ✅ means `gald3r platform install`
  emits a real per-event registration file that reaches the platform's actual
  hook mechanism. ⚠ means hook *scripts* are delivered but the registration
  doesn't reach the platform's real mechanism yet (cline, copilot, kiro_cli —
  each with a named follow-up task). ❌ means nothing hook-related ships today.
- **Rules** — persistent always-apply instructions/memory for the platform.
- **Skills** — `g-skl-*` skill discovery and invocation.
- **Commands** — `/g-*` / `@g-*` slash commands or the platform's equivalent.
- **MCP** — the platform can host the gald3r MCP server (37 engine tools).
- **Engine tier** — how the deterministic engine reaches the platform:
  **L2 MCP** (native MCP server), **L1 CLI** (`gald3r` invoked directly),
  **L0 files-only** (markdown fallback). Even where a native column is ❌/⚠,
  the engine supplies the same behavior via MCP/CLI on nearly every platform —
  the *effective* readiness is higher than the native columns alone.

## The honest gaps, in one list

Tracked as tasks, not hidden:

- **cline / copilot (Hooks ⚠)** — both have a real native hook system; gald3r
  doesn't emit registrations for them yet. Follow-ups filed.
- **kiro_cli (Hooks ⚠)** — receives kiro's `.kiro.hook` adapter mechanically,
  but that adapter doesn't reach kiro-cli's real lifecycle-hook mechanism
  (embedded agent-config JSON `hooks` field). Follow-up filed.
- **hermes / kimi / openclaw (Hooks ❌)** — real native hook systems exist, but
  wiring them honestly is blocked (user-global-only config surfaces, or an
  unverified event mapping). Follow-ups filed, nothing fabricated.
- **roo (Hooks ❌)** — Roo Code was discontinued upstream (2026-05-15); entry
  kept for existing installs.

> **Retired:** `gemini` (Gemini Code Assist shut down 2026-06-18 for
> individual/Pro/Ultra tiers — removed entirely, no EOL row).
