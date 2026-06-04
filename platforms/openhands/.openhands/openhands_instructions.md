# OpenHands Platform — gald3r Configuration Guide

**Platform**: OpenHands (All Hands AI, formerly OpenDevin — open-source agentic dev, Docker sandbox)
**Config Surfaces**: repo-root `AGENTS.md` (primary), `.agents/skills/` (recommended skills), `.openhands/` (legacy)
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.openhands.dev
**Authoritative skill**: `g-skl-platform-openhands`
**Capability spec**: `PLATFORM_SPEC.md` (this directory) — read first

> **T1496 adaptation note**: This guide was corrected against `PLATFORM_SPEC.md` (T1471 doc
> scan of https://docs.openhands.dev, 2026-05-26). The prior version framed
> `.openhands/microagents/repo.md` as the *sole/primary* instruction surface and used the old
> `docs.all-hands.dev` URL. Per current OpenHands docs, **`AGENTS.md` is the primary always-on
> surface** and **`.agents/skills/` is the recommended skills location**; `.openhands/microagents/`
> is **legacy backward-compat**. Capability ratings are doc-verified, NOT install-tested.

---

## Folder Layout

```
<project-root>/
├── AGENTS.md                       # PRIMARY always-on context (injected into system prompt)
├── CLAUDE.md / GEMINI.md           # model-specific always-on variants
├── .agents/
│   └── skills/<name>/SKILL.md      # RECOMMENDED skills location (current)
└── .openhands/                     # legacy / optional config tree
    ├── skills/<name>/SKILL.md      # skills (deprecated, still loaded)
    ├── microagents/
    │   ├── repo.md                 # repository microagent (always-on, LEGACY)
    │   └── <name>.md               # keyword-triggered knowledge microagent (legacy)
    └── config.toml                 # OpenHands sandbox / iteration / MCP config
```

**Skill-location precedence (docs-verified)**:
`.agents/skills/` (recommended) → `.openhands/skills/` (deprecated) → `.openhands/microagents/` (legacy).

**What OpenHands maps differently:**
- Instructions/rules == always-on `AGENTS.md` (+ `CLAUDE.md`/`GEMINI.md`). There is **no `.mdc`
  glob-scoped rule engine** — the split is binary: always-on vs. keyword-triggered skills.
- `.openhands/microagents/repo.md` is the **legacy** repository microagent; it still loads but
  `AGENTS.md` is the current primary. The scaffold's `repo.md` is kept for backward-compat.
- No lifecycle `hooks/` system, and host PowerShell hooks would not run inside the Docker sandbox.
- No native commands/slash surface — `g-*` workflows port only as keyword-triggered skills.

---

## What Makes OpenHands Unique

### Docker Sandbox
OpenHands runs the agent loop inside a Docker sandbox with full filesystem, shell, web-browsing,
and code-execution capability. File paths must be reachable inside the container, host PowerShell
hooks do not execute, and MCP servers on the host are reached via `host.docker.internal`.

### AGENTS.md is the primary surface
`AGENTS.md` (and `CLAUDE.md` / `GEMINI.md`) is auto-discovered and **injected into the system
prompt at conversation start** — the OpenHands equivalent of Cursor's always-apply rules. gald3r
already ships personalized `AGENTS.md` / `CLAUDE.md` at root, so gald3r instruction content reaches
OpenHands with no extra glue (strong positive parity). Keep always-on content concise.

### Skills (microagents successor)
OpenHands has a first-class native **skills** system (folder-per-skill `SKILL.md`) — the successor
to microagents. gald3r's `g-skl-*/SKILL.md` shape maps directly; target `.agents/skills/`
(recommended). Skill types: always-on context, keyword-triggered (frontmatter required), and
on-demand. ⚠️ gald3r's extra frontmatter fields (`subsystem_memberships`, `token_budget`) tolerance
is doc-unverified.

### GitHub / commit identity
OpenHands can auto-raise PRs and commit with its own sandbox identity. Verify the commit author
against gald3r task records.

---

## gald3r Naming Conventions

| Component | OpenHands surface | Notes |
|-----------|-------------------|-------|
| Rules | root `AGENTS.md` (+ `CLAUDE.md`/`GEMINI.md`) | always-on; no `.mdc` glob scoping (⚠️) |
| Skills | `.agents/skills/<name>/SKILL.md` (recommended) | `.openhands/skills/` deprecated, `microagents/` legacy |
| Agents | (no native roster) | `g-agnt-*` content portable as skills/context only (⚠️/❌) |
| Commands | (none) | `g-*` workflows portable as keyword-triggered skills only (❌) |
| Hooks | (none) | no lifecycle hook system; host `.ps1` blocked by sandbox (❌) |
| MCP | skill-scoped `mcp_tools` frontmatter / `config.toml` | sandbox reaches host via `host.docker.internal` (⚠️) |

---

## Config Files Shipped

- **`microagents/repo.md`** — legacy repository microagent with gald3r task-management context.
  Kept for backward-compat; prefer placing this content in root `AGENTS.md` going forward.
- **`config.toml`** — OpenHands sandbox + iteration config, optional MCP pointer.

> **Parity follow-up (PLATFORM_SPEC §9 #5)**: re-targeting gald3r parity output from
> `.openhands/microagents/repo.md` to `AGENTS.md` (context) + `.agents/skills/` (skills) is the
> main outstanding alignment item. Tracked in the platform spec; not auto-applied by this scaffold.

---

## gitignore Decision

`microagents/*.md` and `config.toml` are **source** — keep them tracked. Root `AGENTS.md` /
`CLAUDE.md` follow the standard gald3r personalized-file gitignore policy (`g-rl-02`). OpenHands
writes session/runtime state outside the project; no generated project output dir needs gitignoring.

---

## Verification

```powershell
Test-Path AGENTS.md                          # primary instruction surface
Test-Path .openhands/microagents/repo.md     # legacy repository microagent
Test-Path .agents/skills                      # recommended skills location (if used)
```

> Full sandbox/skill/MCP load verification requires a live `openhands` Docker run — not yet
> performed for this scaffold (PLATFORM_SPEC §9 #7).

---

## Common Pitfalls

- File paths must be accessible inside the Docker sandbox container.
- `AGENTS.md` is the primary surface — do not rely on `.openhands/microagents/repo.md` alone.
- MCP servers on the host are reached via `host.docker.internal` from inside the sandbox.
- OpenHands' GitHub integration commits with its own identity — verify the author.
