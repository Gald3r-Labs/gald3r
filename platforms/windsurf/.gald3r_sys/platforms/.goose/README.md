# Goose (Block) — gald3r Deploy Scaffold

**Config folder**: `.goose/` · **Instruction file**: `.goosehints` (project root)

This directory is the gald3r deploy scaffold for **Goose (Block)**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity sync tooling.

## Read These First

- **`PLATFORM_SPEC.md`** (this folder) — verified per-platform capability findings, including
  the **Known Gaps** section (no native hooks, no slash-commands, `.goosehints` not `GOOSE.md`,
  extensions ARE MCP servers, config is GLOBAL at `~/.config/goose/config.yaml`).
- **`goose_instructions.md`** — deploy guide (folder layout, instruction file, MCP extension
  wiring, gitignore decision, common pitfalls).
- Authoritative install + customization guide: **`g-skl-platform-goose`**
  (`.gald3r_sys/skills/g-skl-platform-goose/SKILL.md`).

## Files in This Scaffold

| File | Purpose |
|------|---------|
| `.goosehints` | The real Goose instruction file (gald3r task context, commit format, MCP pointer). |
| `config.yaml` | REFERENCE ONLY snippet for the gald3r MCP extension — destined for the GLOBAL `~/.config/goose/config.yaml`. Goose does not read it from the project. |
| `PLATFORM_SPEC.md` | Verified capability findings (read first). |
| `goose_instructions.md` | Deploy/configuration guide. |

> **Corrections applied (T1500):** the scaffold previously shipped a fabricated `GOOSE.md`
> instruction file and a project-level `.goose/config.yaml` profile schema. Neither is a Goose
> convention. Goose uses `.goosehints` for instructions and a GLOBAL
> `~/.config/goose/config.yaml` for config (extensions = MCP servers). See `PLATFORM_SPEC.md`.
