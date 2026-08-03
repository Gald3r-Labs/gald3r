---
name: g-skl-platform-void
description: Authoritative reference for Void (VS Code fork) customization in gald3r projects. Covers curated (BUG-137, human-assessed, not yet live-crawled) capability signals — Hooks/Skills/Commands curated not-supported, Rules via the legacy .cursorrules file, and MCP curated supported — plus the still-unverified folder hierarchy and instruction file.
crawl_max_age_days: 14
vault_doc_path: research/platforms/void/
vault_docs_url: https://voideditor.com
docs_url: https://voideditor.com
docs_url_secondary: []
last_doc_scan: never
capability_status:
  hooks: "❌ curated (BUG-137) — human-assessed not supported; no native lifecycle-hook system assessed as present"
  rules: "✅ curated (BUG-137) — human-assessed supported via the legacy .cursorrules file (rules_ext: '.cursorrules'); loading behavior unverified"
  skills: "❌ curated (BUG-137) — human-assessed not supported; do not assume any g-skl-*/SKILL.md discovery path exists"
  commands: "❌ curated (BUG-137) — human-assessed not supported; no slash-command or workflow-file primitive assessed as present"
  agents: "❓ untested — not a matrix-tracked column; no verified info"
  mcp: "✅ curated (BUG-137) — human-assessed supported, curated engine-integration tier MCP (L2); connection config unverified"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# g-skl-platform-void

Activate for: questions about Void's gald3r-relevant capabilities, deciding whether a gald3r
install on Void is worthwhile given its curated capability gaps, or scoping the follow-up work
needed to move this platform from curated to verified.

---

> Full breakdown + provenance in `PLATFORM_SPEC.md` (this folder). **Status: ❓ crawl-untested,
> curated mixed.** Void (a VS Code fork) is registered in the gald3r platform roster. Per the
> **curated** capability matrix (`platform_matrix_data.json`, reconciled under **BUG-137**),
> **Hooks, Skills, and Commands** are human-assessed **❌ not supported**, while **Rules** (via
> the legacy **`.cursorrules`** file) and **MCP** (curated tier MCP (L2)) are **✅ supported**.
> This is a **curation, not a live docs crawl or install test**.

## 1. Platform Overview

**Void** is a VS Code fork registered in the gald3r platform roster. No live docs crawl has run
against `https://voideditor.com`; what is known comes from a human-assessed curation
(`platform_matrix_data.json` / `.gald3r/PLATFORM_CAPABILITY_MATRIX.md`, reconciled into this
platform's `PLATFORM_SPEC.md` under **BUG-137**). Folder hierarchy, the AI instruction file
(distinct from the curated `.cursorrules` Rules signal below), and native agent/subagent support
are **not** matrix-tracked and remain `❓` unknown.

## 2. Config Layout

**Status: ❓ untested — no verified info.** Not a capability the curated matrix tracks either.
Do not assume a `.void/` tree exists, and do not fabricate a directory diagram, until
`@g-platform-scan-docs void` confirms one. The one known signal is the curated **Rules** file
below.

## 3. gald3r Integration

Two of five curated primitives are **not supported** (Hooks, Skills, Commands) — a gald3r install
on Void today can, at best, target **Rules** (best-effort, via the legacy `.cursorrules` file) and
**MCP** (curated supported, transport unverified). Do not fabricate hook, skill, or command
wiring that the curated matrix says does not exist. Treat `.cursorrules` as the best-known
curated target for rule content, but do not assume gald3r's `.mdc`/`.md` rule files translate
without a verified crawl:

```
@g-platform-scan-docs void   # crawl https://voideditor.com
@g-platform-check void       # upgrade curated cells to verified
```

## 4. Common Pitfalls

- **Curated is not verified.** A curated cell means "a human assessed this as (not) supported,"
  not that any mechanism has been confirmed by a live crawl or install test.
- **Do not wire `g-hk-*.py` hooks** — Hooks are curated **❌**; there is no assessed lifecycle-hook
  system to invoke them from.
- **Do not ship `g-skl-*/SKILL.md`** expecting Void to discover it — Skills are curated **❌**.
- **Rules target is `.cursorrules`, not `.mdc`/`.md`** — this is the VS Code/Cursor-fork legacy
  convention Void inherited; do not assume gald3r's own rule-file format loads as-is.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ❌ curated | BUG-137; no lifecycle-hook system assessed |
| Skills (`g-skl-*/SKILL.md`) | ❌ curated | BUG-137; no discovery path assessed |
| Agents (`g-agnt-*.md`) | ❓ | not matrix-tracked; no info |
| Commands (`@g-*`) | ❌ curated | BUG-137; no slash-command primitive assessed |
| Rules (`g-rl-*`) | ✅ curated | BUG-137; via legacy `.cursorrules` (`rules_ext: ".cursorrules"`) |
| MCP | ✅ curated | BUG-137; curated tier MCP (L2); transport unverified |

Full curated provenance + evidence table in `PLATFORM_SPEC.md`. Re-verify on the next
`@g-platform-scan-docs void` (crawl_max_age_days: 14) — that scan should replace every curated
cell above with a live-crawl-verified one.
