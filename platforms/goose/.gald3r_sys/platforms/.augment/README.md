# Augment Code — gald3r Deploy Scaffold

**Config folder**: `.augment/` (plus the root `.augment-guidelines` file)

This directory is the gald3r deploy scaffold for **Augment Code** (VS Code extension +
JetBrains plugin, with the `auggie` CLI). It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity sync tooling.

- **Capability spec**: **`PLATFORM_SPEC.md`** (this directory, T1474) — the honest,
  per-capability assessment of what works on Augment vs. what is a gap. Read it first.
- **Install + customization guide**: **`g-skl-platform-augment`**
  (`.gald3r_sys/skills/g-skl-platform-augment/SKILL.md`).
- **Deploy guide**: **`augment_instructions.md`** (this directory) — folder layout, config
  files, conventions.

## Honest capability summary

Per `PLATFORM_SPEC.md` (legend: ✅ supported · ⚠️ partial · ❌ gap · ❓ untested):

| Capability | Status | Notes |
|---|---|---|
| Rules | ✅ | `.augment/rules/*.md` (`always`/`auto`/`manual` types) + legacy root `.augment-guidelines`; plain `.md`/`.mdx`, NOT Cursor's `.mdc`; per-file glob scoping `❓` |
| MCP | ⚠️ | supported (extension + `auggie` CLI), but configured via IDE Settings panel — no committed repo-root config file, so not fully gald3r-install-managed |
| Skills | ❌ | no skills framework; gald3r `SKILL.md` files are not auto-discovered (Context Engine may index them as retrieval context only) |
| Commands | ❌ | no user slash-command / workflow namespace; `@g-*` commands are doc-only prose |
| Agents | ❌ | single built-in Agent; no user-authored `g-agnt-*` persona registry |
| Hooks | ❌ | no lifecycle hook system; `g-hk-*.ps1` hooks cannot be wired — session-start context injection and pre-commit checks run via always-rules text or manually |

> **Context Engine note**: Augment's defining feature is the Context Engine — a codebase-wide
> semantic retrieval index. It is **not** a gald3r-writable rules/memory store; behavioral
> instructions belong in `.augment/rules/*.md` / `.augment-guidelines`, not the index.

> **Verification caveat**: `last_doc_scan: never`. The spec is authored from the existing skill
> plus a brief live doc check (May 2026), not a fresh `@g-platform-scan-docs augment` crawl.
> Re-verify `❓`/`⚠️` ratings before promoting them. File issues / corrections via the gald3r repo.
