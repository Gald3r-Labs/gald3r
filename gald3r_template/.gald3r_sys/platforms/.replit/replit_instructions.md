# Replit Agent Platform — gald3r Configuration Guide

**Platform**: Replit Agent (AI agent built into the Replit cloud IDE)
**Config Folder**: root `.replit` + `replit.nix`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.replit.com/replit-ai/agent
**Config File**: `.replit` (project root)
**Authoritative skill**: `g-skl-platform-replit`

---

## Folder Layout

```
<project-root>/
├── .replit                 # Replit project config (run command, language, deployment)
├── replit.nix              # Nix environment definition
└── .env                    # Local only — Replit Secrets replace this in the cloud
```

**What Replit does NOT have (gald3r-relevant):**
- No project `agents/`, `commands/`, or `rules/` folders — Replit Agent takes chat instructions
- No lifecycle `hooks/` — gald3r PowerShell hooks do NOT run in Replit's Linux container

---

## What Makes Replit Unique

### Cloud, Nix, Linux Container
Replit runs in a Nix-based Linux container. gald3r PowerShell hooks/scripts are not
available — use bash equivalents. Container restarts reset uncommitted state, so commit
gald3r task files frequently.

### Secrets, Not .env
Replit Secrets replace `.env` files. Configure the gald3r MCP URL as a Secret. The MCP
server must be reachable via an external URL — Replit cannot reach another machine's
localhost.

### Agent Takes Chat Instructions
There is no project rules file Replit Agent auto-reads. Prime the Agent in the chat panel
with the gald3r context (see the snippet in the shipped `.replit` comment header).

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name in the Agent chat) |
| Agents | (none — Replit Agent via chat) |
| Commands | (none) |
| Rules | prime via chat; `.gald3r/` files are the source of truth |

---

## Config Files Shipped

- **`.replit`** — run/deploy config + a commented gald3r priming snippet for the Agent.
- **`replit.nix`** — Nix environment (Node.js for the gald3r installer).

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
- Container restarts reset uncommitted state — commit task files frequently.
- The MCP server needs an external URL — Replit cannot reach a remote localhost.
- Agent commits may not surface in gald3r task tracking — verify the commit author.
