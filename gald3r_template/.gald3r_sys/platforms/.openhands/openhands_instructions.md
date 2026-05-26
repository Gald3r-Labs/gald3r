# OpenHands Platform — gald3r Configuration Guide

**Platform**: OpenHands (formerly OpenDevin — open-source agentic dev, Docker sandbox)
**Config Folder**: `.openhands/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.all-hands.dev
**Config Surface**: `.openhands/microagents/repo.md`, `.openhands/config.toml`
**Authoritative skill**: `g-skl-platform-openhands`

---

## Folder Layout

```
.openhands/
├── microagents/
│   ├── repo.md             # Repository-level instructions (auto-loaded every session)
│   └── task_{name}.md      # Task-specific microagent (loaded on trigger)
└── config.toml             # Optional OpenHands project config (sandbox, iterations, MCP)
```

**What OpenHands maps differently:**
- Microagents replace a `rules/` folder — `repo.md` is the always-loaded behavioral surface
- `task_*.md` microagents load on trigger (keyword/topic) for task-specific guidance
- No lifecycle `hooks/` — automation is via the agent loop + GitHub integration

---

## What Makes OpenHands Unique

### Docker Sandbox
OpenHands runs in a Docker sandbox with full filesystem access, web browsing, and code
execution. File paths must be accessible to the container. MCP URLs use
`host.docker.internal` from inside the sandbox.

### Microagents
`repo.md` is loaded for ALL sessions on this repo — keep it under ~4K tokens. Trigger-based
`task_*.md` microagents add focused guidance only when relevant.

### GitHub Integration
OpenHands can auto-raise PRs and push commits with its own identity. Verify the commit
author against gald3r task records.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name) |
| Agents | microagents (`.openhands/microagents/*.md`) |
| Commands | (none) |
| Rules | `.openhands/microagents/repo.md` |

---

## Config Files Shipped

- **`.openhands/microagents/repo.md`** — gald3r task management instructions (always loaded).
- **`.openhands/config.toml`** — sandbox + iteration config, optional MCP pointer.

---

## gitignore Decision (T1277 AC6)

`.openhands/microagents/*.md` and `.openhands/config.toml` are **source** — keep them
tracked. OpenHands writes session/runtime state outside the project; no generated project
output dir needs gitignoring.

---

## Verification

```powershell
Test-Path .openhands/microagents/repo.md
```

---

## Common Pitfalls

- File paths must be accessible inside the Docker sandbox container.
- `repo.md` loads for every session — keep it under 4K tokens.
- OpenHands' GitHub integration commits with its own identity — verify the author.
