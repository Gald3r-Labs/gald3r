---
name: g-skl-platform-qwen
description: Authoritative reference for Qwen Code (Alibaba CLI coding agent) customization in gald3r projects. Covers .qwen/ config, instructions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/qwen/
vault_docs_url: https://github.com/QwenLM/qwen-code
token_budget: low
---

# g-skl-platform-qwen

Activate for: setting up gald3r with Qwen Code CLI, authoring Qwen instructions, or verifying Qwen gald3r integration.

---

## 1. Platform Overview

**Qwen Code** is Alibaba Cloud's AI coding CLI agent (similar to Claude Code / OpenAI Codex CLI pattern). It uses Qwen models and follows conventions close to the Claude Code CLI pattern.

- **Config**: `.qwen/` directory or `QWEN.md` project instructions
- **Models**: Qwen2.5-Coder series, Qwen-Max
- **Tools**: File read/write, shell commands, code analysis
- **Session**: Interactive or non-interactive (headless) mode

**gald3r target tier**: Alibaba CLI agent. Config via `.qwen/` directory or `QWEN.md`.

---

## 2. Config File Layout

```
<project-root>/
└── .qwen/
    ├── config.yaml         ← Qwen Code configuration
    └── instructions.md     ← Project-level instructions
```

**Alternative**: Some versions read `QWEN.md` at project root (similar to CLAUDE.md pattern).

**`config.yaml` example:**
```yaml
model: qwen-max
max_tokens: 8192
instructions: .qwen/instructions.md
```

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only qwen
```

Creates `.qwen/instructions.md` with gald3r task management context.

### instructions.md Content

```markdown
# Project Instructions — gald3r

## Task Management
Tasks tracked in .gald3r/TASKS.md.
Before implementing: read active task in .gald3r/tasks/task{id}_*.md.
Commit format: feat(T{id}): description

## Architecture Constraints
Read .gald3r/CONSTRAINTS.md before making architectural decisions.
Subsystem boundaries in .gald3r/SUBSYSTEMS.md.

## Bug Protocol
Never silently ignore bugs. Pre-existing bugs → document in .gald3r/BUGS.md.
```

---

## 4. Verification

```bash
Test-Path .qwen
qwen --version 2>/dev/null || echo "Qwen Code not detected"
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Qwen Code is rapidly evolving — config file paths may change between versions; check official docs
- Model availability depends on Alibaba Cloud API key configuration
- Headless mode (`qwen --no-interactive`) useful for CI but requires explicit task scoping
