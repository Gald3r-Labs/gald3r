# Mistral Vibe Platform — gald3r Configuration Guide

**Platform**: Mistral Vibe (Mistral AI's coding agent CLI — Codestral / Mistral-Large)
**Config Folder**: `.mistral/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.mistral.ai/capabilities/code_generation
**Config File**: `.mistral/config.yaml` (or flat `mistral.yaml` at root)
**Authoritative skill**: `g-skl-platform-mistral`

---

## Folder Layout

```
.mistral/
├── config.yaml         # Agent configuration (model, instructions pointer, generation params)
└── instructions.md     # Project-level instructions
```

Alternative: a flat `mistral.yaml` at the project root.

**What Mistral Vibe does NOT have:**
- No project `agents/` folder — single-agent CLI
- No `commands/` folder — invocation is via the `mistral` CLI
- No `rules/` folder — behavioral guidance lives in `instructions.md`
- No `hooks/` folder — no lifecycle hook system

---

## What Makes Mistral Vibe Unique

### Codestral Specialist Model
Codestral is a code-specialist model with a separate API endpoint
(`codestral.mistral.ai`) from the general Mistral API. Set the correct endpoint when using
Codestral for completion/refactor work.

### Config Points at Instructions
`config.yaml` selects the model and points `instructions:` at `instructions.md`, which
carries the gald3r task workflow, commit format, and bug protocol.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name) |
| Agents | (none) |
| Commands | (none) |
| Rules | `.mistral/instructions.md` |

---

## Config Files Shipped

- **`.mistral/config.yaml`** — model selection + instructions pointer + generation params.
- **`.mistral/instructions.md`** — gald3r task workflow, commit format, bug protocol.

---

## gitignore Decision (T1277 AC6)

`.mistral/config.yaml` and `.mistral/instructions.md` are **source** — keep them tracked.
Do NOT place API keys in `config.yaml`; use environment variables. With no key in the
config, there is nothing to gitignore for this platform in installed projects.

---

## Verification

```powershell
Test-Path .mistral
mistral --version
```

---

## Common Pitfalls

- Mistral Vibe is emerging — config conventions may change; verify against your version.
- Codestral uses a separate API endpoint vs the general Mistral API.
- Never commit API keys in `config.yaml` — use environment variables.
