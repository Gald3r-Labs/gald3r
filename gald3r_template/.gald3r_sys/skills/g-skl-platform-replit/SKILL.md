---
name: g-skl-platform-replit
description: Authoritative reference for Replit Agent (cloud IDE) customization in gald3r projects. Covers .replit config, Agent instructions, and gald3r integration patterns for web-based development.
crawl_max_age_days: 14
vault_doc_path: research/platforms/replit/
vault_docs_url: https://docs.replit.com/replit-ai/agent
---

# g-skl-platform-replit

Activate for: setting up gald3r on Replit, configuring Replit Agent, understanding Replit's cloud environment constraints, or verifying Replit gald3r integration.

---

## 1. Platform Overview

**Replit Agent** is an AI coding agent built into the Replit cloud IDE. It can build, run, and deploy applications within Replit's containerized environment. It reads project configuration from `.replit` and accepts natural language instructions.

- **Config**: `.replit` file controls run commands, nix environment, language
- **Agent**: Natural language task execution within the Replit cloud
- **Deployment**: Built-in Replit hosting and deployment
- **Environment**: Nix-based containerized development

**gald3r target tier**: Cloud IDE. Integration via `.replit` config + environment setup.

---

## 2. Config File Layout

```
<project-root>/
├── .replit                 ← Replit project config (run command, language, env)
├── replit.nix              ← Nix environment definition
└── .env                    ← Environment variables (via Replit Secrets)
```

**`.replit` format:**
```toml
run = "node bin/install.js && npm start"
language = "nodejs"
entrypoint = "index.js"

[nix]
channel = "stable-24_05"

[deployment]
run = ["sh", "-c", "npm start"]
deploymentTarget = "cloudrun"
```

---

## 3. gald3r Integration

### Install

Replit Agent is cloud-based — install via npm/node from the Replit shell:
```bash
node bin/install.js --only replit
```

### Limitations in Replit Environment

- `.gald3r/` directory works in Replit but git operations require Replit's git integration
- Replit Secrets replace `.env` files — configure gald3r MCP URL as a Secret
- gald3r's PowerShell hooks are not compatible with Replit's Linux environment; use bash equivalents

### Agent Instructions

Replit Agent accepts instructions in the chat panel. Prime it with:
```
This project uses gald3r for task management. Tasks are in .gald3r/TASKS.md.
Always reference the active task ID in commits: feat(T{id}): ...
Read .gald3r/CONSTRAINTS.md before making architecture changes.
```

---

## 4. Verification

```bash
Test-Path .replit
node --version
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Replit's git integration is separate from the Replit Agent — commits made by Agent may not surface in gald3r task tracking
- PowerShell scripts not available — use bash equivalents for any gald3r automation
- Replit's container restarts reset uncommitted state — commit gald3r task files frequently
- MCP server requires external URL (Replit can't connect to localhost of a different machine)
