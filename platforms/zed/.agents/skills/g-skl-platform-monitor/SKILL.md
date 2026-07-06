---
name: g-skl-platform-monitor
description: Cross-platform health and freshness monitor for the registry-driven gald3r platform roster (PLATFORM_REGISTRY.yaml — single source of truth, T516). Checks per-platform capability gaps against the Cursor reference, scans official docs for breaking changes, validates platform-specific config, and generates the PLATFORM_STATUS / PLATFORM_CAPABILITY_MATRIX living indexes. Owned by g-agnt-platformer.
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-monitor

Activate when checking platform capability gaps, scanning platform docs for breaking changes,
validating platform config, or (re)generating `PLATFORM_STATUS.md` /
`PLATFORM_CAPABILITY_MATRIX.md`. The `g-agnt-platformer` agent is the primary caller.

## The Platform Roster — registry-driven (single source of truth, T516)

The roster of shipped platforms is defined **once** in
`gald3r_templates/gald3r_core/platforms/PLATFORM_REGISTRY.yaml`. Every consumer derives from it —
there is no hand-typed list anywhere else:

- `scripts/check_platform_status.py` / `.ps1` load `KNOWN_PLATFORMS` from the registry via the shared
  reader `scripts/platform_registry.py` (the `.ps1` shells out to it so YAML parsing is not
  duplicated). If the registry file is missing, the reader returns a baked-in fallback roster so the
  tooling still runs.
- The `-GenerateMatrix` path iterates the registry roster and resolves each platform's
  `PLATFORM_SPEC.md` from its registry `spec_path`, so `PLATFORM_STATUS.md` and
  `PLATFORM_CAPABILITY_MATRIX.md` share one roster.
- A roster-parity gate (`g-medic` L1-J → `g-skl-medic/scripts/check_roster_parity.py`) asserts
  **overlays == registry == specs == STATUS rows** and fails loudly on drift.

**Registry entry fields:** `name` (canonical id = overlay dir), `display_name`, `overlay_dir`,
`spec_path`, `lifecycle` (`active|abandoned|off_target|redundant|stub`), `alias_of`
(e.g. `vibe → mistral`), `support_level`, `notes`. **Edit the roster in the registry and nowhere
else.** To add a platform: add its overlay dir, add a registry entry, run the parity gate, then
generate at least a stub `PLATFORM_SPEC.md` (honest all-❓). Aliases are resolved via `alias_of` and
never double-counted.

Reference implementation = `g-skl-platform-cursor`. Source-of-truth per platform =
`g-skl-platform-<name>/PLATFORM_SPEC.md` (and its `docs_url:` frontmatter). Status indexes live at
`.gald3r/PLATFORM_STATUS.md` and `.gald3r/PLATFORM_CAPABILITY_MATRIX.md`.

Inspect the roster: `python scripts/platform_registry.py --list` (canonical names) /
`--list --all` (incl. aliases) / `--json` (full registry).

> **Scaffolding note (T1460):** the operation contracts below are fully specified. The
> **freshness loop is now implemented** (T513): `SCAN_DOCS` → spec proposals (`gald3r platform refresh`,
> T514, GAP A) and `GENERATE_STATUS` (`gald3r platform status`, T515, GAP B) close the broken
> crawl→spec→status chain. The remaining heavy `CHECK` gap-analysis / `VALIDATE`
> config-introspection logic is still deferred to the per-platform tasks (T1461–T1483); those
> spots are marked **[deferred — T146x]** in the body. This is scaffolding by design, not an
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

Delegates the read/report mechanics to the engine: `gald3r platform status --platform <name>`
(falls back to `scripts/check_platform_status.ps1 -Platform <name>` where the engine is unavailable).

### SCAN_DOCS `<platform>`

Crawl the platform's official docs and diff against the last crawl.

1. Read `docs_url:` from `g-skl-platform-<platform>/SKILL.md` frontmatter.
2. Invoke `g-skl-crawl` (or `g-skl-recon-docs`) on that URL; store results under
   `{vault_location}/research/platforms/<platform>/`.
3. Diff against the previous crawl snapshot. Surface changed sections:
   `These sections changed since last scan — review for gald3r compatibility impact`.
4. Feed the crawled doc snapshot to the **spec-refresh consumer** (T514, GAP A):
   `gald3r platform refresh --platform <name> --crawl-snapshot <export.json>
   [--crawl-ledger <registry.json>]` (`.ps1` parity wrapper alongside). It emits a
   **reviewable proposal** — a `PLATFORM_SPEC.md.proposed` draft + a "what changed and why"
   summary — and stamps the proposed `last_doc_scan` from the crawl-ledger completion date. It
   NEVER blind-overwrites the curated spec: capability-cell disagreements between the crawled
   docs and the spec surface as `[needs-review]` for a human to judge; only the mechanical
   `last_doc_scan` stamp lands on `--apply`. Then regenerate `PLATFORM_STATUS.md` via
   `GENERATE_STATUS` and the matrix via `GENERATE_MATRIX`.

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

(Re)build `.gald3r/PLATFORM_CAPABILITY_MATRIX.md` — the registry roster (PLATFORM_REGISTRY.yaml)
× 6 capability columns (Hooks, Rules, Skills, Commands, MCP, Docs Fresh). Cells: ✅ / ⚠️ / ❌ / ❓.
Source the cell values from each platform's `PLATFORM_SPEC.md` (resolved via the registry
`spec_path`). Generated, never hand-maintained.

### GENERATE_STATUS

(Re)build `.gald3r/PLATFORM_STATUS.md` from the specs + the crawl ledger (T515, GAP B):
`gald3r platform status --apply [--crawl-ledger <registry.json>]` (`.ps1` parity wrapper
alongside; dry-run is the default — omit `--apply` to preview). Closes the second freshness-loop
gap: STATUS was hand-maintained and rotted (`check_platform_status` reads it READ-ONLY and never
wrote it). **Source-of-truth = Option 2 merge:** the curated **Status verdict + Notes** columns
are PRESERVED from the existing STATUS; only the *mechanical* cells are regenerated — the 5
capability cells derived from each `PLATFORM_SPEC.md` `## Capability Summary` the SAME way
`GENERATE_MATRIX` derives them (so a regen leaves **zero** STATUS-vs-matrix cross-check warnings),
and `Last Doc Scan` taken from the crawl ledger (real `update_crawl_registry` completion date)
else the spec frontmatter `last_doc_scan` (never "now" blindly). Idempotent: a re-run with no
input change is byte-identical modulo the generated timestamp line (use `--no-timestamp` for
byte-for-byte CI diffs). The human edits the SPEC, not STATUS.

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
- Engine: `gald3r platform status [--platform <name>]` (CHECK entry point); fallback `scripts/check_platform_status.ps1`.
- Freshness loop (T513): `gald3r platform refresh`/`.ps1` (T514 — crawled docs → `PLATFORM_SPEC.md` proposals) and `gald3r platform status`/`.ps1` (T515 — specs + crawl ledger → `PLATFORM_STATUS.md`). Shared spec/ledger parsing in `scripts/platform_spec_io.py`. Both run host-side (C-001), need no DB connection or migration, and are dry-run by default (proposals, not blind writes).
- Roster source of truth: `gald3r_templates/gald3r_core/platforms/PLATFORM_REGISTRY.yaml` (T516), read via `scripts/platform_registry.py`.
- Roster-parity gate: `g-skl-medic/scripts/check_roster_parity.py`, wired into `g-medic` L1-J — fails loudly when overlays / registry / specs / STATUS rows disagree.
- Medic: g-medic L2 calls `g-skl-platform-monitor CHECK <current-platform>` for platform health.
