---
name: g-skl-platform-cline
description: Authoritative reference for Cline (VS Code extension) customization in gald3r projects. Covers .clinerules layout, custom instructions, memory banks, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/cline/
vault_docs_url: https://github.com/clinebot/cline
---

# g-skl-platform-cline

Activate for: setting up gald3r with Cline, authoring `.clinerules`, configuring Cline memory banks, or verifying Cline gald3r integration.

---

## 1. Platform Overview

**Cline** (formerly Claude Dev) is a highly popular open-source VS Code extension for agentic AI coding. It reads project-level instructions from `.clinerules` and supports memory bank files for persistent context across sessions.

- **Agentic mode**: Full tool use (read/write files, run commands, browser use)
- **Rules**: `.clinerules` auto-injected at session start
- **Memory Bank**: Persistent markdown files in `memory-bank/` directory
- **MCP**: Full MCP support via Cline settings

**gald3r target tier**: VS Code extension (high install base). Rules via `.clinerules`.

---

## 2. Config File Layout

```
<project-root>/
├── .clinerules             ← Project-level instructions (auto-injected)
└── memory-bank/            ← Optional persistent memory files
    ├── projectbrief.md
    ├── activeContext.md
    └── progress.md
```

**Format**: Plain markdown. Cline reads the full `.clinerules` file content.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only cline
```

Writes gald3r always-apply rules to `.clinerules`.

### Rules Content

gald3r writes its core session rules (from root `commands/` and always-apply subset) to `.clinerules`. Keep under ~4K tokens.

### Memory Bank

Create `memory-bank/projectbrief.md` to surface gald3r PROJECT.md mission to Cline sessions:

```markdown
# Project Brief
[paste .gald3r/PROJECT.md mission here]
```

---

## 4. Verification

```bash
Test-Path .clinerules
node bin/install.js --list --target .
```

Expected: `.clinerules` present, `cline` row shows `detected: yes`.

---

## 5. Common Pitfalls

- `.clinerules` must be in project root; subdirectory rules are not supported
- Memory bank files need to be manually updated — Cline reads but does not auto-write them
- Large `.clinerules` (>8K tokens) may be truncated in Cline's context; keep concise
