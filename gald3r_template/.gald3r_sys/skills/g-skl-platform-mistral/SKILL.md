---
name: g-skl-platform-mistral
description: Authoritative reference for Mistral Vibe coding agent customization in gald3r projects. Covers .mistral/ config, agent instructions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
vault_docs_url: https://docs.mistral.ai/capabilities/code_generation
token_budget: low
---

# g-skl-platform-mistral

Activate for: setting up gald3r with Mistral Vibe coding agent, authoring Mistral project instructions, or verifying Mistral gald3r integration.

---

## 1. Platform Overview

**Mistral Vibe** (Mistral's agent CLI) is Mistral AI's coding agent tool. It uses Mistral models (Codestral, Mistral-Large) for code generation and follows a project-instructions pattern similar to other CLI agents.

- **Config**: `.mistral/` directory or `mistral.yaml` at project root
- **Instructions**: Project-level context injected at session start
- **Models**: Codestral (code specialist), Mistral-Large, Mistral-Medium
- **API**: Powered by Mistral API (La Plateforme)

**gald3r target tier**: Mistral CLI agent. Config via `.mistral/` directory.

---

## 2. Config File Layout

```
<project-root>/
└── .mistral/
    ├── config.yaml         ← Agent configuration
    └── instructions.md     ← Project-level instructions
```

**`config.yaml` example:**
```yaml
model: codestral-latest
instructions: .mistral/instructions.md
max_tokens: 4096
temperature: 0.1
```

**Alternative**: `mistral.yaml` at project root (flat config).

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only mistral
```

Creates `.mistral/instructions.md` with gald3r task management context.

### instructions.md Content

```markdown
# Project Instructions — gald3r

## Task Workflow
Before any implementation:
1. Read .gald3r/TASKS.md for active tasks
2. Read .gald3r/tasks/task{id}_*.md for task details
3. Check .gald3r/CONSTRAINTS.md for architectural limits

## Commit Format
feat(T{id}): description
fix(BUG-{id}): description

## Bug Discovery
Pre-existing bugs: document in .gald3r/BUGS.md — never silently ignore.
```

### Codestral-Specific Usage

Codestral excels at code completion and refactoring:
```bash
mistral code --model codestral-latest --task "refactor per T1042 spec"
```

---

## 4. Verification

```bash
Test-Path .mistral
mistral --version 2>/dev/null || echo "Mistral CLI not detected"
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Mistral Vibe is an emerging product — config conventions may change; check official docs for your version
- Codestral has a separate API endpoint (codestral.mistral.ai) vs general Mistral API — set correct endpoint
- `.mistral/` directory is gitignore-candidate if it contains API keys — use environment variables instead
