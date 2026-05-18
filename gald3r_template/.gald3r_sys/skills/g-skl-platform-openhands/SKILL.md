---
name: g-skl-platform-openhands
description: Authoritative reference for OpenHands (OpenDevin) AI agent customization in gald3r projects. Covers .openhands/microagents, custom instructions, Docker sandbox integration, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/openhands/
vault_docs_url: https://docs.all-hands.dev
---

# g-skl-platform-openhands

Activate for: setting up gald3r with OpenHands, authoring microagent instructions, configuring OpenHands sandbox, or verifying OpenHands gald3r integration.

---

## 1. Platform Overview

**OpenHands** (formerly OpenDevin) is a powerful open-source AI software development agent. It runs in a Docker sandbox with full filesystem access, web browsing, and code execution. It reads custom instructions from `.openhands/microagents/` or `.openhands_instructions`.

- **Microagents**: Custom agent instructions in `.openhands/microagents/`
- **Sandbox**: Docker-based isolated execution environment
- **Web UI**: Browser-based interface + REST API
- **GitHub integration**: Auto-raises PRs, pushes commits

**gald3r target tier**: Open-source agentic CLI/server. Instructions via `.openhands/microagents/`.

---

## 2. Config File Layout

```
<project-root>/
└── .openhands/
    ├── microagents/
    │   ├── repo.md             ← Repository-level instructions (auto-loaded)
    │   └── task_{name}.md      ← Task-specific microagent (loaded on trigger)
    └── config.toml             ← Optional OpenHands project config
```

**`repo.md` format**: Plain markdown injected into every OpenHands session for this repo.

**`config.toml` example:**
```toml
[core]
max_iterations = 50
sandbox_type = "local"
```

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only openhands
```

Creates `.openhands/microagents/repo.md` with gald3r task management instructions.

### repo.md Content

```markdown
# Repository Context

## Task Management (gald3r)
This project uses gald3r for task tracking.
- Active tasks: .gald3r/TASKS.md
- Task details: .gald3r/tasks/task{id}_*.md
- Constraints: .gald3r/CONSTRAINTS.md

## Development Workflow
1. Read active task before implementing
2. Reference task ID in all commits: feat(T{id}): ...
3. Mark tasks complete by updating task YAML status

## Bug Protocol
Pre-existing bugs → document in .gald3r/BUGS.md, never silently ignore.
```

### MCP Integration

OpenHands supports MCP (in recent versions):
```toml
[sandbox]
mcp_url = "http://host.docker.internal:8092"
```

---

## 4. Verification

```bash
Test-Path .openhands/microagents/repo.md
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- OpenHands runs in Docker sandbox — file paths must be accessible to the container
- `repo.md` is loaded for ALL sessions; keep it under 4K tokens
- OpenHands' GitHub integration commits with its own identity — verify commit author in gald3r task records
