---
name: g-skl-platform-goose
description: Authoritative reference for Goose (Block) AI agent customization in gald3r projects. Covers .goose/ config, instructions files, extensions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/goose/
vault_docs_url: https://block.github.io/goose/docs
token_budget: low
---

# g-skl-platform-goose

Activate for: setting up gald3r with Goose (Block's open source AI agent), authoring Goose instructions, configuring extensions, or verifying Goose gald3r integration.

---

## 1. Platform Overview

**Goose** (by Block, fka Square) is an open-source AI developer agent that runs in the terminal. It supports extensions (MCP and built-in), profile-based configuration, and session-scoped instructions.

- **Config**: `~/.config/goose/config.yaml` (global) or project-level `GOOSE.md` / `.goose/config.yaml`
- **Instructions**: `GOOSE.md` at project root or via `--instructions` flag
- **Extensions**: MCP servers, built-in tools (browser, code execution, etc.)
- **Profiles**: Named profiles for different task types

**gald3r target tier**: Open-source CLI agent. Config via `GOOSE.md` + `.goose/config.yaml`.

---

## 2. Config File Layout

```
<project-root>/
├── GOOSE.md                ← Project-level instructions (read at session start)
└── .goose/
    └── config.yaml         ← Project-specific Goose config (overrides global)
```

**Global config**: `~/.config/goose/config.yaml`

**`GOOSE.md` format**: Plain markdown — Goose reads this as project context.

**`.goose/config.yaml` example:**
```yaml
extensions:
  - name: mcp-gald3r
    type: mcp
    url: http://localhost:8092
profiles:
  default:
    instructions: GOOSE.md
```

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only goose
```

Creates `GOOSE.md` and `.goose/config.yaml` with gald3r task context and optional MCP configuration.

### GOOSE.md Content

```markdown
# Project Context — gald3r

## Task Management
All tasks tracked in .gald3r/TASKS.md. Reference task ID in all work.
Active task details: .gald3r/tasks/task{id}_*.md

## Commit Convention
feat(T{id}): description

## gald3r MCP
If available: use gald3r MCP at localhost:8092 for task/bug/vault operations.
```

### MCP Integration

Goose supports MCP — point it at the gald3r Docker MCP server:
```yaml
extensions:
  - name: gald3r-mcp
    type: mcp
    url: http://localhost:8092/mcp
```

---

## 4. Verification

```bash
Test-Path GOOSE.md
goose version
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Goose is session-based; instructions reload at session start but MCP state persists
- `GOOSE.md` is community convention, not enforced — Goose reads it if extensions support it
- Extensions (MCP) need to be running before Goose session starts
