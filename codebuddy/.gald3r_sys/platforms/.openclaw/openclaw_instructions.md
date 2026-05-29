# OpenClaw Platform — gald3r Configuration Guide

**Platform**: OpenClaw — local-first autonomous AI agent (formerly *clawdbot* / *moltbot*), MIT-licensed
**Primary surface**: per-user workspace `~/.openclaw/workspace/` (NOT a project `.openclaw/` checkout)
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.openclaw.ai | https://github.com/openclaw/openclaw
**Primary config file**: `SOUL.md` (persona) — plus `AGENTS.md`, `TOOLS.md`, `MEMORY.md`
**Authoritative skill**: `g-skl-platform-openclaw`
**Full platform analysis**: see `PLATFORM_SPEC.md` in this directory.

> **Status: WARNING (doc-supported, install-unverified).** Findings below are derived from the
> public docs (docs.openclaw.ai) and the gald3r scaffold, NOT from a live install exercised in this
> repo. `last_doc_scan: never` — run `@g-platform-scan-docs openclaw` to confirm exact behavior.
> Items marked (?) are doc-derived-but-untested.

---

## Folder Layout (per PLATFORM_SPEC.md sec 1)

OpenClaw is NOT repo-scoped like an IDE agent. It runs out of a per-user workspace:

```
~/.openclaw/                          # per-user OpenClaw home (default; not the project repo)
├── openclaw.json                     # main config (hooks, mcp.servers, agent defaults)
└── workspace/                        # default agent workspace (agents.defaults.workspace)
    ├── SOUL.md                       # identity / tone / boundaries (gald3r ships a template)
    ├── AGENTS.md                     # agent configuration / instructions
    ├── TOOLS.md                      # notes for Skills + environment-specific settings
    ├── MEMORY.md                     # durable facts / preferences / decisions
    ├── memory/YYYY-MM-DD.md          # daily memory logs
    └── skills/{skill-name}/SKILL.md  # workspace skills dir (default install target)
```

To integrate gald3r, either point `agents.defaults.workspace` at the repo, OR install the gald3r
skills into `~/.openclaw/workspace/skills/`. There is no automatic "reads the repo root natively"
behavior.

---

## Capability Summary (per PLATFORM_SPEC.md)

| Surface | Status | Notes |
|---------|--------|-------|
| Hooks | WARNING | OpenClaw HAS a real hooks system, but it is `HOOK.md` + `handler.ts` (TypeScript) wired in `openclaw.json` `hooks.internal.*`. gald3r `.ps1` hooks are NOT portable; events differ (`gateway:startup`, `agent:bootstrap`, `command:new/reset`). |
| Rules | NOT SUPPORTED | No native `rules/`/`.mdc` mechanism. gald3r `g-rl-*` rules must be folded into `SOUL.md` / `AGENTS.md` prose. |
| Skills | WARNING | `skills/<name>/SKILL.md` folder-per-skill matches gald3r, but install-path-dependent (`~/.openclaw/workspace/skills/` or `--global`), not auto-repo-read. (?) |
| Commands | WARNING | Native slash commands (`/new`, `/reset`) + CLI exist, but gald3r `g-*.md` command files are NOT ingested as executable commands. |
| Agents | WARNING | OpenClaw IS an agent runtime, but does not discover gald3r `g-agnt-*.md` files; personas come from `SOUL.md` / `AGENTS.md` / `IDENTITY.md`. |
| MCP | WARNING | First-class MCP (`mcp.servers` in `openclaw.json`, `openclaw mcp set`), but gald3r MCP server definitions are not auto-imported. (?) |

Legend: see PLATFORM_SPEC.md sec 9 (Known Gaps) and the Capability Summary table.

---

## gald3r Naming Conventions

| Component | Surface on OpenClaw |
|-----------|---------------------|
| Skills | `skills/{name}/SKILL.md` — folder-per-skill (install into workspace `skills/` dir) |
| Agents | none discovered — fold into `SOUL.md` / `AGENTS.md` |
| Commands | none ingested — native `/new` `/reset` + `openclaw` CLI only |
| Rules | none native — embed in `SOUL.md` / `AGENTS.md` prose |
| Hooks | `HOOK.md` + `handler.ts` (TypeScript); gald3r `.ps1` non-portable |
| MCP | `mcp.servers` in `~/.openclaw/openclaw.json` via `openclaw mcp set` |

---

## Config Files Shipped

- **`SOUL.md`** — gald3r project identity / persona pointing at `.gald3r/` (TASKS.md, CONSTRAINTS.md, PROJECT.md, BUGS.md).
- **`PLATFORM_SPEC.md`** — full platform analysis (byte-identical copy of the authoring skill's spec).
- **`README.md`** — scaffold index.

AGENTS.md / TOOLS.md / MEMORY.md ingestion is doc-confirmed but the gald3r scaffold only ships
`SOUL.md` today (PLATFORM_SPEC.md sec 2). Skills are installed from the canonical root `skills/`
into the OpenClaw workspace — they are not duplicated under `.openclaw/`.

---

## gitignore Decision

`SOUL.md` is **source** — keep it tracked. OpenClaw's working files live under `~/.openclaw/`
(outside the repo), so no in-repo generated-output gitignore entry is needed.

---

## Verification

```powershell
Test-Path SOUL.md
Test-Path PLATFORM_SPEC.md
```

> Live `openclaw` CLI verification is NOT possible from this repo — the platform is doc-derived /
> install-unverified. Confirm runtime behavior with `@g-platform-scan-docs openclaw` against a real
> install before relying on any (?)-marked surface.

---

## Common Pitfalls

- `SOUL.md` is the persona file — do NOT confuse it with `AGENTS.md`; OpenClaw reads both for different purposes.
- OpenClaw is workspace-scoped (`~/.openclaw/workspace/`), NOT repo-root-scoped. Skills must be installed there.
- gald3r `.ps1` hooks do NOT run — OpenClaw hooks are TypeScript `handler.ts`.
- gald3r `g-rl-*` rules have no native injection point — summarize them into `SOUL.md` / `AGENTS.md`.
- MCP servers must be re-declared with `openclaw mcp set` — gald3r MCP config is not auto-imported.
