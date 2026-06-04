# Qwen Code Platform — gald3r Configuration Guide

**Platform**: Qwen Code (Alibaba Cloud AI coding CLI — Qwen2.5-Coder / Qwen-Max)
**Config Folder**: `.qwen/`
**gald3r Version**: 1.0.0
**Official Docs**: https://github.com/QwenLM/qwen-code
**Config File**: `.qwen/config.yaml` (or `QWEN.md` at root)
**Authoritative skill**: `g-skl-platform-qwen`

---

## Folder Layout

```
.qwen/
├── config.yaml         # Qwen Code configuration (model, instructions pointer)
└── instructions.md     # Project-level instructions
```

Alternative: some versions read `QWEN.md` at the project root (CLAUDE.md pattern).

**What Qwen Code does NOT have:**
- No project `agents/` folder — single-agent CLI (Claude Code-like pattern)
- No `commands/` folder — invocation is via the `qwen` CLI
- No `rules/` folder — behavioral guidance lives in `instructions.md`
- No `hooks/` folder — no lifecycle hook system

---

## What Makes Qwen Code Unique

### Claude Code-Like Pattern
Qwen Code follows conventions close to Claude Code / OpenAI Codex CLI. Interactive and
headless (`qwen --no-interactive`) modes are both supported; headless is useful for CI but
needs explicit task scoping.

### Config Points at Instructions
`config.yaml` selects the Qwen model and points `instructions:` at `instructions.md`, which
carries the gald3r task workflow, commit format, and bug protocol.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name) |
| Agents | (none) |
| Commands | (none) |
| Rules | `.qwen/instructions.md` |

---

## Config Files Shipped

- **`.qwen/config.yaml`** — model selection + instructions pointer.
- **`.qwen/instructions.md`** — gald3r task workflow, commit format, bug protocol.

---

## gitignore Decision (T1277 AC6)

`.qwen/config.yaml` and `.qwen/instructions.md` are **source** — keep them tracked. Do not
place Alibaba Cloud API keys in `config.yaml`; use environment variables. With no key in the
config there is nothing to gitignore for this platform in installed projects.

---

## Verification

```powershell
Test-Path .qwen
qwen --version
```

---

## Common Pitfalls

- Qwen Code evolves rapidly — config paths may change between versions.
- Model availability depends on Alibaba Cloud API key configuration.
- Headless mode requires explicit task scoping.
