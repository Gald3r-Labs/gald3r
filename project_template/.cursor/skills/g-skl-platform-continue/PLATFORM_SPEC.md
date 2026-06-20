---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: continue
authoring_path: create
docs_url: https://docs.continue.dev
docs_url_secondary:
  - https://docs.continue.dev/customize/overview
crawl_max_age_days: 14
vault_doc_path: research/platforms/continue/
last_doc_scan: 2026-06-13
reference: g-skl-platform-cursor
status: ❓
gald3r_support_tier: T3
task: T1487
---

# PLATFORM_SPEC.md — Continue.dev

> **Authoring status**: `create` — initial scaffold from known-good sources.
> Run `@g-platform-scan-docs continue` after crawling `https://docs.continue.dev` to verify and expand.

Open-source AI coding extension for VS Code and JetBrains. Context providers, slash commands from .prompt files, MCP integration, custom models.

**Relationship**: Open-source VS Code / JetBrains extension

> Highly configurable. MCP + context providers. ~15k GitHub stars. Good match for gald3r CRASH primitives.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                     ← primary instruction file

└── .continue/
    ├── (config file: config.yaml)

    └── (platform-specific structure — verify against docs)
```

**Config file**: `~/.continue/config.yaml`

---

## 2. CRASH Primitive Support

| Primitive | Support | Notes |
|---|---|---|
| **Hooks** | ❌ | |
| **Rules** | ✅ (.continuerules, AGENTS.md, system prompt) | |
| **Skills** | ❓ | |
| **Commands** | ✅ (slash commands / .prompt files) | |
| **MCP** | ✅ (mcpServers in config.yaml) | |

---

## 3. Instruction Files (Rules Equivalent)

Primary instruction file: `AGENTS.md` — gald3r's standard.


- `AGENTS.md` — check docs for exact load order and scope
- `.continuerules` — check docs for exact load order and scope

---

## 4. Skills

❓

**TODO**: Verify whether `SKILL.md` files in `.continue/skills/` (or equivalent) are discovered. Document discovery path after doc crawl.

---

## 5. Commands (Slash Commands)

✅ (slash commands / .prompt files)

**TODO**: Document available slash commands and how to add custom ones after doc crawl.

---

## 6. Hooks

❌

**TODO**: Document hook events and registration mechanism after doc crawl.

---

## 7. MCP

✅ (mcpServers in config.yaml)

**TODO**: Document MCP server config syntax for `~/.continue/config.yaml` after doc crawl.

---

## 8. gald3r Installation

### Install Path

gald3r files should live under `.continue/`.

```bash
# After doc crawl — verify this install path:
# gald3r install --platform continue
```

### Verification Checklist (complete after SCAN_DOCS)

- [ ] Instruction file (`AGENTS.md` or equivalent) is read at session start
- [ ] MCP config syntax verified
- [ ] Skills/agents discovery path confirmed
- [ ] Hooks registration method confirmed
- [ ] Full gald3r install test completed

---

## 9. Official Docs

- Primary: <https://docs.continue.dev>

- https://docs.continue.dev/customize/overview

---

*Scaffold created 2026-06-13. Run `@g-platform-scan-docs continue` to populate from live docs.*
