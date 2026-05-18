---
name: g-skl-platform-warp
description: Authoritative reference for Warp AI terminal customization in gald3r projects. Covers Warp Drive workflows, AI agent mode, custom prompts, and gald3r integration patterns.
crawl_max_age_days: 14
vault_doc_path: research/platforms/warp/
vault_docs_url: https://docs.warp.dev
---

# g-skl-platform-warp

Activate for: setting up gald3r with Warp terminal, configuring Warp AI workflows, understanding Warp's agent mode, or verifying Warp gald3r integration.

---

## 1. Platform Overview

**Warp** is an AI-native terminal with built-in AI assistance. It supports notebooks (Warp Drive), AI agent mode for multi-step terminal tasks, and workflow sharing. Context is primarily session-level rather than project-level file-based.

- **AI mode**: Natural language → terminal commands
- **Warp Drive**: Shareable workflows and notebooks (cloud-backed)
- **Agent mode**: Multi-step terminal task execution
- **Context**: Session context; no project-level rules file (different paradigm from IDE tools)

**gald3r target tier**: AI terminal. Integration via shell profile + Warp Drive workflows.

---

## 2. Config File Layout

Warp does not use a project-level config file like `.windsurfrules` or `.clinerules`. Integration points:

```
~/.warp/
├── themes/                 ← Custom themes
└── launch_configurations/  ← Session launch configs (Warp Drive)
```

**Project-level context**: Use environment variables and shell profiles for per-project context.

---

## 3. gald3r Integration

### Shell Profile Integration

Add to `~/.bashrc` / `~/.zshrc` / PowerShell profile for gald3r context in Warp:

```bash
# gald3r context for Warp sessions
export GALD3R_ACTIVE_TASK=$(cat .gald3r/TASKS.md 2>/dev/null | grep '\[🔄\]' | head -1)
export GALD3R_PROJECT=$(cat .gald3r/PROJECT.md 2>/dev/null | head -3)
```

### Install

```bash
node bin/install.js --only warp
```

Creates Warp-compatible shell setup instructions (no file install needed).

### Warp Drive Workflows

Create shareable gald3r workflows in Warp Drive:
- `gald3r status` — show active tasks
- `gald3r commit T{id}` — commit with task reference
- `gald3r new-task` — launch task creation

---

## 4. Verification

```bash
warp --version 2>/dev/null || echo "Warp not detected as CLI"
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Warp's AI mode operates on the terminal session context, not project files — gald3r rules don't auto-inject
- Warp Drive workflows are cloud-backed; ensure workspace is set up before sharing team workflows
- Warp's paradigm is terminal-first — skills/agents/commands still apply but via shell invocation rather than IDE integration
