# Replit Agent Platform — gald3r Configuration Guide

**Platform**: Replit Agent (AI agent built into the Replit cloud IDE)
**Instruction surface**: `replit.md` (primary) + `AGENTS.md`
**Environment config**: root `.replit` + `replit.nix`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.replit.com/replitai/replit-dot-md
**Authoritative skill**: `g-skl-platform-replit`

> See `PLATFORM_SPEC.md` (this directory) for the verified capability matrix. T1506 corrected
> this guide: the prior version omitted `replit.md` (the real instruction surface) and framed
> MCP only as a constraint rather than a first-class, recommended integration.

---

## Folder Layout

```
<repl-root>/
├── replit.md               # Agent instruction + memory surface (PRIMARY) — auto-created,
│                           #   auto-read every request, self-updated by the Agent
├── AGENTS.md               # also honored (cross-tool instruction-file convention)
├── .replit                 # Replit ENVIRONMENT config (run command, language, deployment) — NOT instructions
├── replit.nix              # Nix environment definition (system packages / toolchain)
└── .gald3r/                # gald3r project state (commit often — container restarts reset uncommitted state)
```

> `.env` is not used in the cloud — **Replit Secrets** replace it. Configure the gald3r MCP URL
> as a Secret.

**What Replit does NOT have (gald3r-relevant):**
- No project `agents/`, `commands/`, `rules/`, or `skills/` folders — Replit Agent has no
  `.mdc` rules, no `SKILL.md` discovery, no agent-file format, and no user slash-command registry
- No lifecycle `hooks/` — gald3r PowerShell hooks do NOT run in Replit's Linux container
- `.replit` is **environment/run config, not an AI-instruction file** — Agent instructions live
  in `replit.md` (a common stale assumption is that `.replit` is the instruction surface; it is not)

---

## What Makes Replit Unique

### Cloud, Nix, Linux Container
Replit runs in a Nix-based Linux container. gald3r PowerShell hooks/scripts are not
available — use bash equivalents. Container restarts reset uncommitted state, so commit
gald3r task files frequently.

### MCP is First-Class (recommended integration)
Replit Agent is a first-class **MCP client**. Add the gald3r MCP server as a **custom MCP
server** via the **Integrations pane** (UI) — one-click install + automatic tool discovery.
MCP servers are configured in the UI, **not** a committed `mcp.json` file. Constraint: the
server must be reachable via an external URL — the container cannot reach another machine's
localhost. This is the **strongest** gald3r surface on Replit, not a blocker.

### Secrets, Not .env
Replit Secrets replace `.env` files in the cloud. Configure the gald3r MCP URL/token as a Secret.

### Agent Reads `replit.md` (not chat-only)
Replit Agent **auto-creates and auto-reads `replit.md`** on every request — it is the project
instruction/memory surface. Merge gald3r conventions there (task IDs in commits, "tasks live in
`.gald3r/TASKS.md`", "read `.gald3r/CONSTRAINTS.md` before architecture changes"). Because the
Agent can **self-update `replit.md`**, re-prime at session start so injected conventions are not
trimmed. `AGENTS.md` is also honored.

---

## gald3r Naming Conventions

| Component | Surface on Replit |
|-----------|---------|
| Instructions | `replit.md` (primary, auto-read/self-updated) + `AGENTS.md` |
| Rules | collapse into the `replit.md` blob (no `.mdc`, no glob scoping); `.gald3r/` files are the source of truth |
| MCP | first-class — add via the Integrations pane (custom MCP server, remote URL) |
| Skills | ❌ no `SKILL.md` discovery — reference intent in `replit.md` / Agent chat |
| Agents | ❌ no agent-file format — describe roles as `replit.md` prose |
| Commands | ❌ no user slash-command registry — describe intent to the Agent |

---

## Config Files Shipped

- **`.replit`** — environment/run+deploy config + a commented gald3r priming snippet that points
  at `replit.md` (it is NOT itself the instruction file).
- **`replit.nix`** — Nix environment (Node.js + git for the gald3r installer).

> `replit.md` is **not** shipped as a template here — Replit Agent auto-creates it on first use.
> gald3r merges its conventions into the Agent-generated file (or `AGENTS.md`), rather than
> overwriting an Agent-owned, self-updating file.

---

## gitignore Decision (T1277 AC6)

`.replit` and `replit.nix` are **source** — keep them tracked. `.env` is already gitignored
by the universal gald3r `.gitignore` section (Replit Secrets are used instead in the cloud).
Replit writes no other generated project output dir that needs gitignoring.

---

## Verification

```bash
test -f .replit && echo ok
node --version
```

---

## Common Pitfalls

- PowerShell scripts are unavailable — use bash equivalents for gald3r automation.
- Container restarts reset uncommitted state — commit `.gald3r/` task files frequently.
- The Agent **self-updates `replit.md`** — re-prime gald3r conventions at session start.
- Treating `.replit` as the instruction file — it is environment config; instructions go in `replit.md`.
- The MCP server needs an external (remote) URL — Replit cannot reach a different machine's localhost.
- Agent commits may not surface in gald3r task tracking — verify the commit author.
