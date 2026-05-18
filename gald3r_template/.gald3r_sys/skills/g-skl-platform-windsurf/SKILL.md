---
name: g-skl-platform-windsurf
description: Authoritative reference for Windsurf IDE customization in gald3r projects. Covers .windsurfrules layout, Cascade agent integration, rules format, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
vault_docs_url: https://docs.windsurf.com
---

# g-skl-platform-windsurf

Activate for: setting up gald3r in Windsurf IDE, authoring Windsurf rules, understanding `.windsurfrules` structure, or verifying Windsurf gald3r integration.

---

## 1. Platform Overview

**Windsurf** (by Codeium) is a VS Code-based AI-first IDE featuring the **Cascade** agentic AI system. Windsurf supports global and workspace-level rules that are automatically injected into Cascade sessions.

- **Cascade**: Multi-step agentic AI that reads `rules` context automatically
- **Rules system**: Project-level `.windsurfrules`, global user rules
- **MCP**: Supports MCP servers via settings

**gald3r target tier**: VS Code family (similar rule injection to Cursor). Skills are served from root `skills/` via gald3r install.

---

## 2. Config File Layout

```
<project-root>/
├── .windsurfrules          ← Project-level rules (auto-injected into Cascade)
└── .windsurf/
    └── rules/              ← Per-file or per-folder rule overrides (optional)
```

**Global rules**: Managed in Windsurf settings UI → AI → Rules (stored in `~/.codeium/windsurf/memories/`).

**Format**: Plain markdown. No frontmatter required. All content injected as context.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only windsurf
```

Installs to `.windsurf/` in the target project.

### Rules File

gald3r writes its always-apply rules to `.windsurfrules`. Keep under 8K tokens for Cascade context budget.

### Skills

Windsurf does not have a native skills discovery path equivalent to Cursor's `.cursor/skills/`. Approach:
1. Surface skill content via `.windsurfrules` (compact summary)
2. Use `@mention` patterns in Cascade prompts to reference skill names

---

## 4. Verification

```bash
# Confirm rules file exists
Test-Path .windsurfrules

# Confirm install
node bin/install.js --list --target .
```

Expected: `.windsurfrules` present, `windsurf` row shows `detected: yes`.

---

## 5. Common Pitfalls

- Windsurf previously used `.windsurf/rules/` subdirs — current versions prefer `.windsurfrules` at project root
- Global user rules override project rules in some Cascade versions — test with project-scoped rules first
- Cascade context window is separate from inline completion context; rules are injected into Cascade only
