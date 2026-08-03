---
name: g-skl-platform-astrbot
description: Authoritative reference for AstrBot customization in gald3r projects. Covers curated (BUG-137, human-assessed, not yet live-crawled) support signals for Hooks/Rules/Skills/Commands/MCP, the still-unverified folder hierarchy and instruction file, and how to upgrade this spec from curated to verified.
crawl_max_age_days: 14
vault_doc_path: research/platforms/astrbot/
vault_docs_url: https://astrbot.app
docs_url: https://astrbot.app
docs_url_secondary: []
last_doc_scan: never
capability_status:
  hooks: "✅ curated (BUG-137) — human-assessed supported; native hook config file, event list, and payload format are unverified pending a live docs crawl"
  rules: "✅ curated (BUG-137) — human-assessed supported; platform_matrix_data.json records rules_ext: '—' (no established rules-file extension curated yet)"
  skills: "✅ curated (BUG-137) — human-assessed supported; SKILL.md discovery path and frontmatter shape are unverified"
  commands: "✅ curated (BUG-137) — human-assessed supported; slash-command syntax and workflow-file format are unverified"
  agents: "❓ untested — not a matrix-tracked column; no verified info"
  mcp: "✅ curated (BUG-137) — human-assessed supported, curated engine-integration tier MCP (L2); connection config and transport details are unverified"
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

# g-skl-platform-astrbot

Activate for: questions about AstrBot's gald3r-relevant capabilities, deciding whether to
attempt a gald3r install on AstrBot, or scoping the follow-up work needed to move this platform
from curated to verified.

---

> Full breakdown + provenance in `PLATFORM_SPEC.md` (this folder). **Status: ❓ crawl-untested,
> curated ✅ across the board.** AstrBot is registered in the gald3r platform roster
> (`PLATFORM_REGISTRY.yaml`). Per the **curated** capability matrix (`platform_matrix_data.json`,
> reconciled under **BUG-137**), the five matrix-tracked primitives — **Hooks, Rules, Skills,
> Commands, and MCP** — are all human-assessed **✅ supported**, with an **MCP (L2)**
> engine-integration tier. This is a **curation, not a live docs crawl or install test** — treat
> every ✅ below as "assessed as supported," not "implementation mechanism confirmed."

## 1. Platform Overview

**AstrBot** is registered in the gald3r platform roster. As of this scan no live docs crawl has
run against `https://astrbot.app`; what is known comes from a human-assessed curation
(`platform_matrix_data.json` / `.gald3r/PLATFORM_CAPABILITY_MATRIX.md`, reconciled into this
platform's `PLATFORM_SPEC.md` under **BUG-137**). Folder hierarchy, the AI instruction file, and
native agent/subagent support are **not** matrix-tracked and remain `❓` unknown.

## 2. Config Layout

**Status: ❓ untested — no verified info.** The platform's config-folder layout has not been
crawled or verified. Do not assume a `.astrbot/` tree exists, and do not fabricate a directory
diagram, until `@g-platform-scan-docs astrbot` confirms one.

## 3. gald3r Integration

There is **no verified install path** for AstrBot yet — only a curated capability signal that the
five matrix-tracked primitives are supported in principle. Do not attempt to hand-author a
`.astrbot/` overlay from guesswork. The correct next step is a live docs crawl:

```
@g-platform-scan-docs astrbot   # crawl https://astrbot.app
@g-platform-check astrbot       # upgrade curated cells to verified
```

Once that scan lands a folder hierarchy, instruction-file convention, and per-primitive config
paths, this SKILL.md and its `PLATFORM_SPEC.md` should be refreshed together with the real,
dir-specific mechanism details (config file names, event lists, discovery paths).

## 4. Common Pitfalls

- **Curated is not verified.** A curated ✅ means "a human assessed this as supported," not that
  any install mechanism, file path, or config schema has been confirmed by a live crawl or
  install test. Do not treat these cells as install-ready specifications.
- **Do not assume Claude-Code-style reuse** (`.claude/skills/`, `AGENTS.md`, etc.) — no cross-tool
  discovery claim has been made or verified for AstrBot.
- **Rules file extension is unknown** — `platform_matrix_data.json` records `rules_ext: "—"`
  (no established extension), so do not guess `.md`/`.mdc`/`.rules`.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ✅ curated | BUG-137; mechanism unverified |
| Skills (`g-skl-*/SKILL.md`) | ✅ curated | BUG-137; discovery path unverified |
| Agents (`g-agnt-*.md`) | ❓ | not matrix-tracked; no info |
| Commands (`@g-*`) | ✅ curated | BUG-137; syntax unverified |
| Rules (`g-rl-*`) | ✅ curated | BUG-137; `rules_ext: "—"` (no extension curated yet) |
| MCP | ✅ curated | BUG-137; curated tier MCP (L2); transport unverified |

Full curated provenance + evidence table in `PLATFORM_SPEC.md`. Re-verify on the next
`@g-platform-scan-docs astrbot` (crawl_max_age_days: 14) — that scan should replace every
curated cell above with a live-crawl-verified one.
