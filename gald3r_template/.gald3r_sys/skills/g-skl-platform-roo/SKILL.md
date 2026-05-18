---
name: g-skl-platform-roo
description: Authoritative reference for Roo Code (VS Code extension) customization in gald3r projects. Covers .roorules, mode-specific rules, memory bank, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/roo/
vault_docs_url: https://github.com/RooVetGit/Roo-Code
---

# g-skl-platform-roo

Activate for: setting up gald3r with Roo Code, authoring `.roorules`, understanding Roo's mode system, or verifying Roo gald3r integration.

---

## 1. Platform Overview

**Roo Code** (formerly Roo Cline) is a fork of Cline with enhanced agentic capabilities, custom AI modes (Code, Architect, Debug, etc.), and boomerang task orchestration. It supports both `.roorules` and `.clinerules`.

- **Modes**: Code, Architect, Debug, Test, Ask — each can have separate rules
- **Rules**: `.roorules` (preferred) or `.clinerules` (fallback)
- **Mode-specific rules**: `.roorules-code`, `.roorules-architect`, etc.
- **Memory bank**: Compatible with Cline memory bank pattern
- **MCP**: Full MCP support

**gald3r target tier**: VS Code extension. High overlap with Cline pattern.

---

## 2. Config File Layout

```
<project-root>/
├── .roorules               ← Global project rules (all modes)
├── .roorules-code          ← Code mode specific rules (optional)
├── .roorules-architect     ← Architect mode specific rules (optional)
├── .clinerules             ← Fallback (Roo reads this if .roorules absent)
└── memory-bank/            ← Persistent memory (same as Cline)
```

**Format**: Plain markdown.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only roo
```

Writes gald3r rules to `.roorules`. Also writes `.clinerules` as fallback.

### Mode-Specific Rules

For Architect mode (planning/design work), add gald3r architecture context:

```markdown
# .roorules-architect
Always read .gald3r/PLAN.md and .gald3r/CONSTRAINTS.md before making architecture decisions.
Subsystem changes require reading .gald3r/subsystems/{name}.md.
```

---

## 4. Verification

```bash
Test-Path .roorules
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Roo reads `.roorules` first, then `.clinerules` — set `.roorules` as primary
- Mode-specific rule files override global `.roorules` for that mode (not additive by default in some versions)
- Boomerang task orchestration may not read rules if sub-tasks use different modes — test cross-mode behavior
