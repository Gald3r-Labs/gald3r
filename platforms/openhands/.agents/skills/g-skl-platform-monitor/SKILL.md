---
name: g-skl-platform-monitor
description: Cross-platform health and freshness monitor for the 23 gald3r platforms. Checks per-platform capability gaps against the Cursor reference, scans official docs for breaking changes, validates platform-specific config, and generates the PLATFORM_STATUS / PLATFORM_CAPABILITY_MATRIX living indexes. Owned by g-agnt-platformer.
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-monitor

Activate when checking platform capability gaps, scanning platform docs for breaking changes,
validating platform config, or (re)generating `PLATFORM_STATUS.md` /
`PLATFORM_CAPABILITY_MATRIX.md`. The `g-agnt-platformer` agent is the primary caller.

## The 23 Platforms

`cursor`, `claude`, `copilot`, `codex`, `antigravity`, `windsurf`, `gemini`, `cline`, `roo`,
`opencode`, `openhands`, `kiro`, `aider`, `augment`, `goose`, `junie`, `kiro-cli`, `mistral`,
`openclaw`, `qwen`, `replit`, `subq`, `warp`.

Reference implementation = `g-skl-platform-cursor`. Source-of-truth per platform =
`g-skl-platform-<name>/SKILL.md` (and its `docs_url:` frontmatter). Status indexes live at
`.gald3r/PLATFORM_STATUS.md` and `.gald3r/PLATFORM_CAPABILITY_MATRIX.md`.

> **Scaffolding note (T1460):** the operation contracts below are fully specified, but the heavy
> doc-diff / config-introspection logic is intentionally deferred to the per-platform tasks
> (T1461–T1483) that exercise each operation. Where an operation's full implementation is deferred,
> it is marked **[deferred — T146x]** in the body. This is scaffolding by design, not an
> unannotated stub.

---

## Operations

### CHECK `<platform>`

Compare one platform's declared capability support against the Cursor reference.

1. Read `g-skl-platform-<platform>/SKILL.md` — extract declared support for hooks, rules,
   skills, commands, MCP (sections 3/6/7/8 in the platform SKILL or its PLATFORM_SPEC).
2. Read `g-skl-platform-cursor/SKILL.md` as the reference baseline.
3. For each capability the reference has, check whether the platform declares an equivalent.
   Emit gaps: `cursor has <X>; <platform> has no equivalent`.
4. Update the platform's row in `PLATFORM_STATUS.md` (capability cells + Notes).
5. If `g-skl-platform-<platform>/SKILL.md` does not exist (antigravity) → report
   `NO SKILL — create via T1465` and mark all cells `❓`.

Delegates the read/report mechanics to `custom_scripts/check_platform_status.py -Platform <name>`.

### SCAN_DOCS `<platform>`

Crawl the platform's official docs and diff against the last crawl.

1. Read `docs_url:` from `g-skl-platform-<platform>/SKILL.md` frontmatter.
2. Invoke `g-skl-crawl` (or `g-skl-recon-docs`) on that URL; store results under
   `{vault_location}/research/platforms/<platform>/`.
3. Diff against the previous crawl snapshot. Surface changed sections:
   `These sections changed since last scan — review for gald3r compatibility impact`.
4. Update `last_doc_scan` (today) in `PLATFORM_STATUS.md` and the platform SKILL's
   `last_doc_scan:` field. **[deferred — T146x: per-platform diff heuristics]**

### SCAN_ALL

Run CHECK + SCAN_DOCS for every platform in the list, then summarize:
`N healthy (✅) · M need attention (⚠️) · K need full rework (❌) · U unknown (❓)`.
Respects each platform's `crawl_max_age_days` — skips a doc scan that is still fresh.

### VALIDATE `<platform>`

Confirm the platform's config is platform-specific, not Cursor-copied.

1. Inspect `project_template/.gald3r_sys/platforms/.<platform>/` (the per-platform override dir).
2. Check format correctness: is `hooks.json` valid JSON? does `settings.json` match the
   platform's expected structure?
3. If the override dir is empty or its files are byte-identical to the Cursor copy →
   report `Platform <X> config appears Cursor-generic — see gaps`.
4. Record findings in the platform's `PLATFORM_STATUS.md` Notes.
   **[deferred — T146x: per-platform structural schema checks]**

### GENERATE_MATRIX

(Re)build `.gald3r/PLATFORM_CAPABILITY_MATRIX.md` — 23 platforms × 6 capability columns
(Hooks, Rules, Skills, Commands, MCP, Docs Fresh). Cells: ✅ / ⚠️ / ❌ / ❓. Source the cell
values from each platform's CHECK result. Generated, never hand-maintained.

### UPGRADE `<platform>`

Given a `SCAN_DOCS` result, propose specific config changes to gald3r's platform template.

1. Read the doc-scan diff for the platform.
2. Map changed capabilities to gald3r template locations (common skill vs.
   `platforms/.<platform>/` override) using the decision tree in `g-skl-platform-cursor`.
3. Produce a **proposal/diff for human review** — never auto-apply, never run
   `platform_parity_sync.ps1`. The human reviews, then runs parity sync.
   **[deferred — T146x: per-platform change mapping]**

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Verified working (with evidence) |
| ⚠️ | Partial / Cursor-generic / untested-but-present |
| ❌ | Not supported on this platform |
| ❓ | Unknown — never checked |

## Wiring

- Agent owner: `g-agnt-platformer`.
- Commands: `@g-platform-check`, `@g-platform-scan-docs`, `@g-platform-status`.
- Script: `custom_scripts/check_platform_status.py` (CHECK / status-read entry point).
- Medic: g-medic L2 calls `g-skl-platform-monitor CHECK <current-platform>` for platform health.
