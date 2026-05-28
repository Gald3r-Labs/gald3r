# Replit Agent -- gald3r Deploy Scaffold

**Config folder**: `.replit/`

Authoritative install + customization guide: **`g-skl-platform-replit`** (.gald3r_sys/skills/g-skl-platform-replit/SKILL.md).

See **`PLATFORM_SPEC.md`** in this directory for verified platform capability details (Phase 1 research, T1481).
Phase 2 deploy artifact adaptation: T1506.

## What this scaffold is (and is not) (T1506)

> **Replit Agent is an instruction-file + cloud-IDE platform, NOT a rules/skills/hooks platform.**
> Replit Agent runs in a Nix-based **Linux container** in the Replit cloud IDE -- there is no
> on-disk `.cursor/`-style config tree, no lifecycle-hook config, and no user-authored
> slash-command registry. gald3r maps onto Replit through exactly **three** real surfaces:
> the **`replit.md`** instruction/memory file (primary), the **`.replit` / `replit.nix`**
> environment config, and **MCP** (Replit Agent is a first-class MCP client).

> **Two file roles in play (do not conflate):**
> - **`replit.md`** -- the Agent's instruction/memory surface (auto-created, auto-read on every
>   request, and **self-updated** by the Agent). This is where gald3r conventions belong.
> - **`.replit` / `replit.nix`** -- environment/run config (TOML + Nix). NOT AI-instruction files;
>   they declare the run command, language, deployment target, and system packages.

## Honest capability table (from PLATFORM_SPEC.md section 9)

| Capability | Status | gald3r artifact / reality on Replit |
|---|---|---|
| AI instruction file (`replit.md`) | OK -- verified (doc) | Primary surface: Agent auto-creates it, auto-reads it every request, and may self-update it. gald3r conventions merged here (re-prime at session start since Agent can rewrite it). `AGENTS.md` is also honored |
| MCP (Integrations pane) | OK -- verified (doc) | First-class MCP client: one-click server install + automatic tool discovery via the Integrations pane (UI, not a committed `mcp.json`). gald3r MCP added as a **custom MCP server**. Constraint: remote URL only -- the container cannot reach a different machine's localhost |
| Rules (always-apply dir) | partial -- only via `replit.md` | No `.mdc`, no `alwaysApply:`/`globs:` scoping. gald3r `g-rl-*.md` collapse into a single `replit.md` instruction blob (all-or-nothing), and that blob is not tamper-stable (Agent self-edits the file) |
| Skills (`SKILL.md` discovery) | not supported | No `SKILL.md` folder-per-skill discovery. `g-skl-*/SKILL.md` sit in `.gald3r/` as reference-only prose the user points the Agent at |
| Commands (slash) | not supported | No user-authored slash-command registry. Native slash commands are Replit-owned (connection/integration selection). gald3r `g-*` run only by describing intent to the Agent |
| Agents (`g-agnt-*.md` discovery) | not supported | No agent-definition file format. `g-agnt-*.md` has no load path; degrade to `replit.md` prose roles |
| Hooks (lifecycle / `hooks.json`) | not supported | No native lifecycle-hook config + Linux/PowerShell mismatch (`g-hk-*.ps1` would need bash and PowerShell is not present by default). Session-start injection, agent-complete, pre-commit/push gates have no automatic firing surface -- run manually or encode as `replit.md` prose |
| Docs freshness | untested | `last_doc_scan: never` -- run `@g-platform-scan-docs replit` |

Legend: OK = doc-verified mechanism, partial = works only via a non-native path, not supported = no native primitive, untested = not yet crawled/installed.

## No Cursor-specific artifacts shipped here (AC5)

This scaffold contains **no** `hooks.json`, no `.ps1` hook wiring, and no `.cursor/`-style
`.mdc` always-apply rule files, because PLATFORM_SPEC.md section 9 confirms Replit Agent has
**no native hook, rules-folder, skills, or agent-file system**. Shipping those would be Cursor
copypasta and would mislead users into expecting auto-loaded behavior Replit does not provide.

The files in this scaffold are:

- **`.replit`** -- legitimate Repl environment/run config (TOML). The spec (section 1) confirms
  this is environment config, NOT an AI-instruction file. Carries a commented gald3r priming
  snippet pointing at `replit.md`.
- **`replit.nix`** -- legitimate Nix environment definition (Node.js + git for the installer).
- **`replit_instructions.md`** -- the deploy/config guide (corrected in T1506: `replit.md`
  documented as the primary instruction surface; MCP reframed from a near-blocker to first-class;
  stale docs URL fixed).
- **`README.md`** / **`PLATFORM_SPEC.md`** -- this file and the verified capability spec.

No file in this scaffold was fabricated and none was deleted -- `.replit`/`replit.nix` are real
Replit config surfaces per the spec, so they were corrected/annotated, not removed.

## Next steps (before this scaffold gains real MCP config artifacts)

1. Run `@g-platform-scan-docs replit` (or `g-skl-platform-monitor SCAN_DOCS replit`) to crawl
   the current Replit docs (https://docs.replit.com/replitai/replit-dot-md,
   https://docs.replit.com/replitai/mcp/overview) -- `last_doc_scan` is `never`.
2. Confirm the `partial`/`untested` rows in PLATFORM_SPEC.md section 9 against a live Repl
   (exact `replit.md` vs `AGENTS.md` precedence, any 2026 Agent-3 hook/command additions, the
   precise custom-MCP config contract). MCP lives in the Integrations pane UI, not a committed
   file -- there is no `mcp.json` template to ship.
3. Only after concrete evidence is recorded: add confirmed artifacts here, update
   PLATFORM_SPEC.md, and bump the PLATFORM_STATUS.md row.

If you opened this folder expecting auto-loaded rules/skills/hooks/commands and found only
docs + environment config: that is by design -- Replit Agent does not support those natively.
File feedback via the gald3r GitHub issues.
