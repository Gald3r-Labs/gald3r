---
name: g-skl-medic
maturity: beta
version: 2.0.0
description: >
  Tiered .gald3r/ health and intervention system. L1=triage (structural), L2=diagnosis
  (plan coherence), L3=surgery (cross-subsystem interface audit), L4=ecosystem
  (linked project negotiation). Replaces g-skl-medic.
triggers:
  - "@g-medic"
  - "fix gald3r"
  - "health check"
  - "upgrade gald3r"
  - "project is out of sync"
  - "placeholders"
  - broken TASKS.md
  - missing files
  - version mismatch
  - "medic"
token_budget: high
subsystem_memberships: [PROJECT_IDENTITY_SETUP, AGENT_ORCHESTRATION]
---

# g-medic

**Replaces**: `g-medic` (deprecated — delegates to `g-medic`)

**Files Touched**: `.gald3r/` (all files and folders), optionally linked project folders at L4

**Authorization rule**: `g-medic` and `g-setup` are the ONLY things that may write `gald3r_version` to `.gald3r/.identity`. No other skill, agent, hook, or command may touch that field.

---

## Command Interface

```bash
@g-medic                      # L1 triage only (safe default, always applies)
@g-medic --level 2            # L1 + L2 (report generated; --apply to execute fixes)
@g-medic --level 3            # L1 + L2 + L3 (requires --apply to write fixes)
@g-medic --level 4            # L1 + L2 + L3 + L4 (Workspace-Control plus optional PCAC)
@g-medic --ecosystem          # alias for --level 4
@g-medic --dry-run            # any level: report only, no writes
@g-medic --level 2 --apply   # apply L2 fixes after generating report
@g-medic --curate             # feature/subsystem fragmentation analysis (dry-run; no moves)
@g-medic --curate --apply -ProposalJson .gald3r/reports/medic_curate_proposal_*.json  # git mv from approved JSON only
```

### Dry-Run and Output Contract

- `@g-medic --dry-run` is strictly read-only for L1-L4: no task status changes, no TTL resets, no identity/version writes, no backlog regeneration, no report files, and no member-repo changes. It may read `.gald3r/` and print findings only.
- L1 "auto-applies" only when `--dry-run` is absent. If `--dry-run` is present, L1 must report what it would create/update/reset instead of writing.
- If a report finds material drift, blockers, high/critical bugs, phantoms/orphans, stale claims, parser skips, or workspace/member risks, surface the full operational findings to the user. Do not hide them behind a short summary. Summaries may be added after the full findings.
- For any count above 25, include either the complete ID/file list inline or a named report artifact path containing the complete list. Compressed ranges are acceptable only as an additional convenience, never as the only evidence.
- `--curate` is a special curation workflow: by default it writes gitignored proposal/report files for human review; pass the script-level `-NoReportFiles` option when the user requests a no-disk-side-effect dry run.

### Heal operations (`--heal-cNNN`, T1436)

When L1 triage detects a **structural gap** matching a known framework constraint/feature (e.g.
a repo that predates C-023 release files), the corresponding heal path backfills it. Heals are
**dry-run by default**; pass `--apply` to write. Every operation is logged to
`.gald3r/logs/medic_heal_YYYYMMDD.log` (only when `--apply`). Runner:
`gald3r medic heal`.

```
@g-medic --heal-c023 --dry-run     # plan release-file backfill from CHANGELOG (no writes)
@g-medic --heal-c023 --apply       # create missing .gald3r/releases/ files
@g-medic --heal-version --apply    # create root VERSION from latest CHANGELOG ## [X.Y.Z]
@g-medic --heal-constraints        # report inheritable framework constraints missing locally
@g-medic --heal-all --dry-run      # consolidated plan for all known structural gaps
@g-medic --heal-all --apply        # run every Phase 1 heal in dependency order
```

| Flag | What it heals | Mechanism |
|------|---------------|-----------|
| `--heal-c023` | Missing `.gald3r/releases/RELEASE_*` files | Delegates to `gald3r ship` |
| `--heal-version` | Missing root `VERSION` file | Derives from latest CHANGELOG versioned header |
| `--heal-constraints` | Inheritable framework constraints absent locally | Reports gap; `--apply` appends an adoption-pointer stub (cautious: never injects full bodies, never creates CONSTRAINTS.md) |
| `--heal-all` | All of the above | Runs in dependency order: version → c023 → constraints |

Direct invocation: `gald3r medic heal`.

> **Safety:** heals never touch workspace member marker-only `.gald3r/` trees, never delete,
> and the constraints heal is deliberately cautious (pointer stub only). Pass `-Json` for
> CI/agent consumption (structured result with per-heal `status`/`message`/`files`).

#### Heal test cases (AC: per-heal verification)

| # | Case | Expected |
|---|------|----------|
| H1 | `-Heal version` on a repo with VERSION present | `status: ok`, "VERSION already present", no write |
| H2 | `-Heal version` on a repo missing VERSION but with a CHANGELOG `## [X.Y.Z]` | dry-run plans `VERSION (X.Y.Z)`; `--apply` writes it |
| H3 | `-Heal c023` on a repo with releases in sync | "0 release file(s) would be backfilled" |
| H4 | `-Heal c023 --apply` on a repo with CHANGELOG versions lacking release files | creates `release{NNN}_v{X-Y-Z}.md` (delegated) |
| H5 | `-Heal constraints` when inheritable C-NNN missing locally | reports the missing ID list; `--apply` appends a pointer stub |
| H6 | `-Heal all -Json` | clean JSON with three result objects, no console-log leakage |
| H7 | any heal `--apply` | a row appended to `.gald3r/logs/medic_heal_YYYYMMDD.log` |

### Curation mode (`--curate`, Task 517)

**Default (dry-run)**: runs `gald3r medic curate` — counts feature/subsystem sprawl (recursive subsystem count), runs hierarchy sync helpers with `-WarnOnly`, adds a **fragmentation** section (duplicate `feat-NNN` hits in `FEATURES.md`, subsystem specs on disk not indexed in `SUBSYSTEMS.md` via sync JSON), and writes a human report plus `medic_curate_proposal_<stamp>.json` under `.gald3r/reports/` (gitignored). The proposal keeps top-level `moves` empty for safety, but now includes non-binding `suggested_moves` and `index_candidates` with source, target, risk/confidence, and rationale so the reviewer has concrete candidates to approve/edit/reject.

**No report files (CI / no disk side effects)**: pass `-NoReportFiles` to `gald3r medic curate` — prints the same report + proposal JSON to stdout only (no `medic_curate_*.md` / proposal files / `medic_curate_latest.json`).

**Apply**: **never** implied. Requires `-ProposalJson` pointing at a proposal JSON that includes non-empty top-level `moves`; dry-run `suggested_moves` are advisory only and must be copied into `moves` after review. Script **backs up** each source under `.gald3r/reports/medic_curate_backup_<stamp>/`, performs `git mv` for each entry (paths must stay under `.gald3r/features/` or `.gald3r/subsystems/`; duplicate from/to rejected), **literal path replace** in `FEATURES.md`, `SUBSYSTEMS.md`, and `.gald3r/tasks/*.md` for moved paths, writes a manifest JSON, then runs `gald3r_subsystem_diagrams_generate.py`. Refuses when the working tree has unrelated dirty paths. **Never targets** workspace member marker-only `.gald3r/` trees — pass controller repo root only.

**Default behavior**: `@g-medic` with no args runs L1 only (auto-applies — it's always safe).

---

## PCAC Inbox Health Gate

Before mode detection, determine whether the project is a PCAC participant. PCAC is active only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make a project part of a PCAC group.

Only when PCAC is active, call `g-hk-pcac-inbox-check.ps1` without `-BlockOnConflict` when present and capture the result. L1 triage must continue even when `INBOX CONFLICT GATE` is reported so health scoring can surface the conflict. Open PCAC conflicts block L2-L4 planning/apply work, task claiming, implementation, and verification after L1 completes; require `@g-pcac-read` before continuing. Non-conflict requests, broadcasts, and syncs remain advisory and should be surfaced in output. If PCAC is not active, skip the hook and report `PCAC: not configured / skipped`.

## Mode Detection (Run Before Any Level)

Read `.gald3r/.identity`. Based on what you find, select a mode:

```
□ .identity missing entirely?
  → STOP. Invoke g-setup. This is not a repair situation — it's a fresh install.

□ gald3r_version in .identity doesn't match the current gald3r version?
  → MODE: UPGRADE (full structural migration, then continue through all phases)

□ gald3r_version matches, but files/folders are missing or corrupted?
  → MODE: REPAIR (structural fixes + per-file health, skip version bump)

□ gald3r_version matches, structure is intact, just routine maintenance?
  → MODE: MAINTAIN (TTL resets, health score, backlog — skip structural phases)
```

Report selected mode at the start:
```
🩺 g-medic — L{N} | MODE: {UPGRADE | REPAIR | MAINTAIN}
   Project: {project_name} | gald3r v{current} → v{target or "current"}
   Dry-run: YES (pass --apply to execute) | APPLY
```

---

## Level 1 — Triage (Structural Integrity)

*Safe to run any time. Fully autonomous. Blast radius: files and folders only.*
*Applied automatically with no `--apply` needed unless `--dry-run` is present. Runs in all modes.*

### L1-A: Folder Structure

Verify every required `.gald3r/` folder exists. Create missing ones silently:

```
tasks/            individual task files
  tasks/paused/   paused tasks
  tasks/cancelled/ cancelled tasks
bugs/             individual bug files
  bugs/paused/    paused bugs
  bugs/cancelled/ cancelled bugs
features/         PRD/feature files
subsystems/       per-subsystem spec files
reports/          cleanup and upgrade reports
specifications_collection/   incoming specs/wireframes
linking/          INBOX.md, shared contracts
```

Report any folders created. When a required folder is missing and the canonical template
`.gald3r_sys/template_verification/.gald3r/<folder>/` exists (T1442), restore it (including its
`.gitkeep`) from there rather than creating a bare empty folder.
In `--dry-run`, report missing folders as `would_create` and do not create them.

### L1-B: Root File Audit

Check each required root file. When a file is missing, **restore the pristine canonical
copy from `.gald3r_sys/template_verification/.gald3r/` first** (T1442); fall back to an empty
in-skill template only when the canonical file is unavailable.

#### Restore-from-canonical (T1442 — preferred heal path)

The framework ships a pristine `.gald3r/` template instance at
`.gald3r_sys/template_verification/.gald3r/` on every install. When a required `.gald3r/` file
or folder is missing, g-medic L1 **restores it from that canonical source** instead of reporting
error-only or writing a bare stub. This guarantees the restored file carries the correct
T1439 versioned frontmatter (`schema_version` / `gald3r_rel_version`) for the installed release.
**Never reconstruct a missing index (BUGS.md / TASKS.md) from memory** — only the canonical
template or the empty in-skill stub are valid sources.

Restore order for any missing required file:

1. **Canonical copy** — if `.gald3r_sys/template_verification/.gald3r/<relpath>` exists, copy it
   to `.gald3r/<relpath>` (creating parent folders as needed). This is the default heal.
2. **Engine shell-out (optional)** — for a batch restore of all missing single-file artifacts,
   shell out to the canonical engine rather than re-implementing the copy:
   ```
   uv run python .gald3r_sys/scripts/migrate_schemas.py -ProjectPath <proj> -RestoreMissing -Apply
   ```
   (`-RestoreMissing` without `-Apply` reports what it would restore — use for `--dry-run`.)
   The engine resolves the same `template_verification/.gald3r/` canonical source.
3. **Empty in-skill template** — only when the canonical file is absent from
   `template_verification/.gald3r/` (e.g. a corrupt or partial install). Fall back to the
   per-file stub in the table below.

Resolve the canonical path script-adjacent (`.gald3r_sys/template_verification/.gald3r/`) or
project-local (`<proj>/.gald3r_sys/template_verification/.gald3r/`). Never hardcode a dev-machine path.

| File | If Missing (canonical absent) | Health Check |
|---|---|---|
| `TASKS.md` | Restore from template_verification, else empty template | Task Sync (L1-D) |
| `BUGS.md` | Restore from template_verification, else empty template | Bug Sync (L1-D) |
| `PLAN.md` | Restore from template_verification, else empty template | Has `## Current Focus`? |
| `FEATURES.md` | Restore from template_verification, else empty template | Has `## PRD Index` table? |
| `PROJECT.md` | Restore from template_verification, else empty template | Goals Check (L1-D) |
| `CONSTRAINTS.md` | Restore from template_verification, else header-only stub | Has `## Architectural Constraints`? |
| `SUBSYSTEMS.md` | Restore from template_verification, else empty template | Subsystem Sync (L1-D) |
| `IDEA_BOARD.md` | Restore from template_verification, else empty template | Has `## Active Ideas`? |

In `--dry-run`, report missing files as `would_restore` (from template_verification) or
`would_create` (canonical absent) and do not write them.

### L1-C: .identity Integrity

Verify all fields present and valid:
```ini
project_id=     ← UUID format — STOP if missing, invoke g-setup
project_name=   ← warn if doesn't match parent folder name
user_id=        ← fill with "unknown" if missing
user_name=      ← fill with "unknown" if missing
gald3r_version=  ← semver format
vault_location= ← fill with "{LOCAL}" if missing
```

### L1-D: Task / Bug / Feature / Subsystem Sync

- **Tasks**: activate `g-tasks → SYNC CHECK`. Auto-fix status mismatches (file is source of truth). Report phantoms/orphans.
- **Bugs**: for each BUGS.md row: check `bugs/bugNNN_*.md` exists. Missing → PHANTOM ⚠️
- **Features**: same phantom/orphan pattern.
- **Subsystems**: activate `g-subsystems → SYNC CHECK`. Add stub entries for subsystems referenced in tasks but missing from registry.

#### L1-D Parser Contract — Active Index Scope (mandatory)

Medic sync checks MUST distinguish active control-plane records from historical or imported inventory. Do not use recursive file scans for active orphan/phantom counts.

- **Active `TASKS.md` rows**: count every active task row matching a status indicator in either supported index format: bullet rows like `- [✅] **Task 090**: ...` and table rows like `| [📋] | [090](tasks/task090_*.md) | ... |` or `| [🔍] | T123 | ... |`. Normalize Markdown links, optional `Task`/`T` prefixes, leading zeros, and subtask suffixes while preserving the suffix (`052-1` is distinct from `052`). Deduplicate by normalized task ID before computing totals; matching duplicate rows are duplicate inventory findings, while conflicting duplicate statuses are critical parser findings.
- **Active task files**: scan only direct children of `.gald3r/tasks/` matching `task<id>_*.md` or `task<id>-<suffix>_*.md`. Exclude all recursive subdirectories from active orphan math, including `archive/`, `bkup/`, `backup/`, `quarantine/`, `adopted/`, `imports/`, and any future historical bucket.
- **Historical/imported task files**: report separately as archival inventory with their source metadata (`source_harvest`, `adopted_from`, `workspace_repos`, `delegated_to`, `source_quarantine`, etc.). Never call these active orphans unless the file is a direct child of `.gald3r/tasks/`.
- **Phantom** means an active `TASKS.md` row has no matching direct child task file.
- **Orphan** means a direct child task file has no matching active `TASKS.md` row.
- If a diagnostic reports more than 25 IDs, include the full list in the report body or a named report artifact path. Do not only emit compressed ranges when the user asked for operational status.

### L1-E: Sequential ID Integrity

- Tasks: find ID gaps, duplicates, out-of-order entries → report; offer auto-renumber (requires `--apply`)
- Bugs: same
- Features: same

### L1-F: YAML Frontmatter Validation

For each `tasks/*.md`, `bugs/*.md`, `features/*.md`:
- Malformed YAML (fails to parse) → report as critical
- Missing required fields → add with defaults silently
- Status normalization: `in_progress` → `in-progress`

### L1-G: Empty Stub Detection

Tasks or bugs with no `## Objective` or `## Acceptance Criteria` → flag as incomplete stub

### L1-H: BOM / Encoding Audit

Check for BOM (`\xef\xbb\xbf`) at file start in any `.gald3r/**/*.md` → report; remove with `--apply`

### L1-I: Version Bump (UPGRADE mode only, after apply confirmed)

Write new `gald3r_version` to `.gald3r/.identity`. Append to `.gald3r/reports/UPGRADE_LOG.md`.

### L1-J: Maintenance Routines (ALL modes)

- **TTL Check**: for each `in-progress` task: `now > claim_expires_at`? → reset to `pending`
- **Verification Timeout**: `[🔍]` for > 8h → reset to `pending`; > 4h → flag only
- **Platform Doc Freshness** (T1520): if `.gald3r/PLATFORM_STATUS.md` exists, parse the `Last Doc Scan` column for each platform row and compare against the `crawl_max_age_days` threshold (default `7`). Treat overdue platforms as a soft warning (⚠️), not a hard failure. Report format:
  - All fresh → `Platform docs: ✅ all N platforms fresh`
  - Any stale → `Platform docs: ⚠️ M of N platforms overdue — run @g-platform-scan`
  Pure read of one file; never writes. If `PLATFORM_STATUS.md` does not exist, skip the check silently (no warning).
- **Health Score**:
  ```
  base  = (completed / total_non_cancelled_non_paused) × 100
  -5    per stale [🔄]
  -3    per [🔍] > 4h
  -10   per task with failure_history > 2
  -15   per subsystem with no tasks ever
  -20   per open PCAC `INBOX.md` CONFLICT item (L1 continues, L2-L4 blocked until `@g-pcac-read`)
  -3    per active MCP server over 10 (see L1-K)
  -1    per MCP server flagged [ELEVATED] by Agent Shield (see L1-K)
  -10   if ANY platform overdue for doc re-crawl (T1520) — capped at -10 regardless of count
  final = max(0, base − penalties)
  Healthy: ≥80 | Degraded: 50-79 | Critical: <50
  ```
- **ACTIVE_BACKLOG.md Regeneration**: write `.gald3r/ACTIVE_BACKLOG.md`
- **Platform Parity Audit**: compare `.cursor/rules/`, `.claude/rules/`, `.agent/rules/` — report violations (see `PARITY_EXCLUDES.md`)
- **Placeholder Sweep**: scan `.gald3r/**/*.md` for `{project_name}`, `{Goal name}`, `YYYY-MM-DD` (literal) — auto-fill `{project_name}` from `.identity`; report rest

### L1-K: MCP Server Count & Agent Shield (T1165)

> **Source**: V13 "Everything Claude Code" harvest (YouTube `utHRH2FEAsY`). Claude Code recommends ≤10 active MCP servers to avoid context bloat, tool-routing slowdown, and dilution of model attention across the tool list. A single backend like `example_app` is ~42 tools on its own, so a user who adds 4–5 MCPs casually can hit 150+ tools and not notice.

**Goal**: surface excessive MCP server counts and flag servers whose tool surface includes broad filesystem/shell/execute access (Agent Shield heuristic).

#### MCP config discovery (precedence order)

Look for the active MCP config in this order; first hit wins. If none found, skip L1-K silently:

1. `<project_root>/.cursor/mcp.json` — project-scoped Cursor MCP config
2. `~/.cursor/mcp.json` — user-scoped Cursor MCP config (resolved via `$HOME` / `$env:USERPROFILE`)
3. `<project_root>/.mcp.json` — Claude Code / generic project-scoped MCP config

Parse as JSON. Active servers are the keys of the top-level `mcpServers` object. Servers explicitly disabled (`"disabled": true` field) are skipped from the count but listed in the triage table as `disabled`.

#### Count thresholds

| Active server count | Output |
|---------------------|--------|
| ≤ 10 | ✅ `MCP Count: N active servers (within recommended ≤10)` |
| 11–20 | `⚠️ MCP Count: N active servers (recommended: ≤10)` |
| > 20 | `🚨 MCP Count: N servers — context degradation likely` |

#### Agent Shield (elevated-access heuristic)

For each active server, examine its declared command/args/url and (when known from prior tool-list capture or a `tools:` annotation in the config) its tool names and description. Flag the server as `[ELEVATED]` when any of the following case-insensitive substrings appear:

- In tool names or description text: `filesystem`, `shell`, `execute`, `write_file`, `shell_exec`, `run_command`, `bash`, `python`
- In `command`/`args`: a known broad-access binary such as `mcp-server-filesystem`, `mcp-server-shell`, `mcp-server-execute`, `desktop-commander`, or any package whose name contains `filesystem` or `shell`

Servers that only expose read-only / scoped tools (search, query, fetch, get_*) without the elevated keywords are listed as `scoped`. Pure HTTP MCPs without a local command get `remote` and are evaluated by reachable tool-list metadata when available, otherwise `unknown`.

#### Health score penalty (folds into L1-J)

```
mcp_over_threshold = max(0, active_server_count - 10)
elevated_count     = count of servers flagged [ELEVATED]
penalty            = (3 × mcp_over_threshold) + (1 × elevated_count)
```

The penalty is applied alongside the other L1-J penalties before clamping at 0.

#### L1-K triage table (always emitted when an MCP config is found)

```markdown
### MCP Triage (T1165)

Active config: <resolved path>
Active servers: N  |  Elevated: M  |  Penalty: -P (-3×over10, -1×elevated)

| Server               | Tool count | Access level | Recommendation |
|----------------------|-----------:|--------------|----------------|
| example_app      | 42         | scoped       | keep           |
| chrome-devtools      | 38         | scoped       | keep           |
| muninn              | 14         | scoped       | keep           |
| desktop-commander    | 9          | [ELEVATED]   | review — broad filesystem/shell access |
| context-mode         | 8          | scoped       | keep           |
| ... (one row per active server) ...                                           |
```

Recommendations:

- `keep` — scoped, no concern
- `review — broad <kind> access` — flagged `[ELEVATED]`; user should confirm the elevated tools are intended
- `prune — duplicate <of-other-server>` — duplicate capability against another server already listed
- `prune — N servers over recommended limit` — emitted on the lowest-value servers when count > 10

Tool count is sourced from a prior live tool-list capture when available, otherwise rendered as `?` (unknown). Unknown tool counts do NOT affect the access-level classification or the penalty.

#### Operational rules

- Skip L1-K cleanly when no MCP config is discoverable (e.g., projects that never enabled MCP).
- Treat malformed JSON as a critical L1 finding (do NOT crash the rest of L1) and surface in the report.
- L1-K is read-only in all modes including `--apply`: it never edits MCP config files. Pruning is a user decision.
- In `--dry-run` mode, L1-K behaves identically (it's already read-only).

### L1-L: Schema Validation (T1440)

*Runs AFTER the L1-A/L1-B folder/file existence checks above. Read-driven; writes
only the safe auto-fixes / TODO markers described below. Skips silently if the
schema system is not installed.*

The schema layer enforces the file schemas defined in `.gald3r_sys/schemas/`
(registry: `_registry.yaml`; enum auto-fix map: `_fix_mappings.yaml`). It
auto-fixes what it safely can, inserts `TODO:` markers where human input is
required, and **never halts** — medic always continues to L1 Output.

**Skip condition**: if `.gald3r_sys/schemas/_registry.yaml` does not exist, skip
L1-L entirely (schema system not installed). Treat malformed registry/schema
YAML as a critical L1 finding without crashing the rest of L1.

#### Deterministic processing order

Collect every `.gald3r/` file matching a `pattern` in `_registry.yaml`, then
process them **sorted by path** (ascending) so reports are reproducible across
runs.

#### Schema check algorithm

For each matched file:

```
1. Determine schema version:
   - Read schema_version from frontmatter.
   - If missing → treat as v0 (pre-schema era).

2. Compare to the system current_version (from _registry.yaml for this pattern):
   - file < system  → migration path (see below), then validation path
   - file == system → validation-only path
   - file > system  → SKIP; add to "Newer than system" report (do not touch)
   - file == v0     → migration path from v0, then validation path

3. Validation path (for each REQUIRED field in the schema):
   - present + valid value          → PASS
   - present + invalid enum value   → attempt_fix     (Fix Rules)
   - missing                        → attempt_populate (Population Rules)

4. Migration path (file < system):
   - Load migration_notes from the schema file.
   - Apply each new required field added since the file's schema version.
   - Then run the validation path on the result.
```

> **Protected paths**: never touch a file whose `schema_version` is **newer than
> system** when it lives in a protected path (e.g. a PRD in `released` state).
> Log it as `skipped (newer)` and move on — no read-fix, no migration.

#### Fix Rules (invalid enum value)

The auto-fix mapping lives in `.gald3r_sys/schemas/_fix_mappings.yaml` — the
**canonical, extensible** source of enum aliases. Extend that YAML to add new
aliases; no skill/rule code changes are needed. A hit means an unambiguous fix
(auto-applied + logged); a miss means insert a `TODO:` (never guess).

| Situation | Action |
|---|---|
| `status: done` → maps to `qa_complete` in `_fix_mappings.yaml` | Auto-fix, log: `Auto-fixed status: done → qa_complete` |
| `status: complete` / `completed` → `qa_complete` | Auto-fix |
| `status: wip` / `active` → `coding` | Auto-fix |
| `status: blocked` → `resource_gated`; `hold` → `paused` | Auto-fix |
| `status: <unknown>` → not in `_fix_mappings.yaml` (ambiguous) | Insert `TODO: invalid status value "<value>" — see valid values in schema` |
| `priority: urgent` / `blocker` → `critical` | Auto-fix |
| `priority: nice_to_have` → `low` | Auto-fix |
| `priority: <unknown>` (ambiguous) | Insert TODO |
| `type: <unknown>` | Insert TODO |

> The `done → qa_complete` mapping is the canonical fix for the **"done status
> incident"**; the rationale is documented as a comment at the top of
> `_fix_mappings.yaml`.

#### Population Rules (missing required field)

| Field | Auto-populate source |
|---|---|
| `created_date` | `git log --diff-filter=A -- <file>` → extract the add date |
| `schema_version` | Current schema version from `_registry.yaml` |
| `gald3r_rel_version` | Current framework version from `.gald3r/.identity` |
| `priority` | Default to `medium` (safe neutral) |
| `id` | Cannot auto-determine → `TODO: assign sequential task ID` |
| `title` | Cannot auto-determine → `TODO: add descriptive task title` |
| `type` | Cannot auto-determine → `TODO: [feature\|bug_fix\|refactor\|chore\|documentation]` |
| `status` | Cannot auto-determine → `TODO: [see valid status values in schema]` |

#### Non-required (optional) field behavior

- Missing → **never** fail, **never** insert a TODO, **never** emit a report line.
- Present with an invalid value → **warn** in the report; do **NOT** auto-fix.

#### Missing folder handling

```powershell
foreach ($folder in $canonicalFolders) {       # canonical set from _registry.yaml patterns
    if (-not (Test-Path $folder)) {
        New-Item $folder -ItemType Directory | Out-Null
        Copy-TemplateContents $folder          # README/.gitkeep from project_template/.gald3r/
        $report.FoldersCreated += $folder
    }
}
```

Template contents are sourced from `project_template/.gald3r/`. Creation is silent
and **never halts**; created folders are listed in the medic report.

#### `schema_error` in-memory flag

When a required field is missing AND cannot be auto-populated AND a `TODO:` was
inserted, medic adds a flag to that file's **in-memory** record (it is NOT
written into the file):

```
schema_error: true
affected_fields: [title]
```

This flag surfaces in `g-status` alongside the task until a human clears the
TODO.

#### L1-L Report block (folds into L1 Output)

```
🔍 Schema Validation (L1 schema layer)
   Files checked:    42
   PASS:             38
   Auto-fixed:        2  (status: done → qa_complete, status: complete → qa_complete)
   TODO inserted:     1  (task1019 missing title field)
   Schema migrated:   1  (task0967: v0 → v1, added schema_version + gald3r_rel_version)
   Newer than system: 0
   Folders created:   1  (tasks/65_qa_complete/)

   ⚠️ Action required:
      task1019_some_task.md — title field missing (TODO inserted)
```

In `--dry-run`, L1-L reports what it *would* fix/populate/migrate/create instead
of writing (consistent with the L1 dry-run contract).

### L1 Output

Full operational report plus optional brief console summary:
```
🩺 g-medic L1 — {project_name} | TRIAGE complete
   ✅ tasks/  ✅ bugs/  ⚠️ features/ CREATED
   Tasks synced: 42  |  Bugs synced: 8  |  0 phantoms
   MCP: 5 active, 0 elevated (within ≤10 limit)
   Health score: 87/100  |  TTL resets: 0
   Report: .gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L1.md
```

---

## Level 2 — Diagnosis (Plan Coherence)

*Requires human review before applying. Blast radius: .gald3r/ data.*
*Run with `--level 2`. Generates `MEDIC_REPORT_L2.md`. Use `--apply` to execute fixes.*

### L2-A: PLAN.md vs TASKS.md Coherence

- Milestones listed as complete in PLAN.md: verify all associated tasks are `[✅]`
- Milestones with no associated tasks: flag
- Tasks in TASKS.md with no milestone parent: flag if >30 days old

### L2-B: Task Dependency DAG Validation

```
□ Circular dependencies (A depends B; B depends A) → CRITICAL flag
□ Dependency on non-existent task ID → ERROR flag
□ Dependency on cancelled/failed task → WARNING flag
□ Tasks blocked > 14 days on unresolved dependency → surface in report
```

### L2-C: Interface Compatibility Check

For tasks with `output_format:` or `input_format:` fields:
- "Task A says it outputs X format; Task B expects Y format — incompatible" → flag

### L2-D: Complexity Audit

Tasks with >8 acceptance criteria OR >3 subsystems: suggest subtask split (write as proposed blocks in report — NOT auto-created)

### L2-E: Feature ↔ Task Linkage

- Features with `status: specced` or `status: committed` but no linked task → flag: "orphaned feature spec"
- Tasks with no feature back-reference AND >2 ACs → flag: "implementation without spec"

### L2-F: SUBSYSTEMS.md ↔ subsystems/ Completeness

- SUBSYSTEMS.md entry with no `subsystems/{name}.md` file → offer to create stub
- `subsystems/*.md` files with missing `locations:` frontmatter → flag incomplete

### L2-G: Missing Cross-Project Ref

### L2-F2: Subsystem Hierarchy Sprawl (T1458)

Run after L2-F. Checks whether the subsystem count has grown without the L1 group hierarchy:

- Count subsystems/*.md files. If count > 20 AND .gald3r/PRODUCT_SYSTEMS.md does not exist:
  flag as MEDIUM health issue:
  "Subsystem sprawl detected: {N} subsystems with no group hierarchy.
   Run @g-system-rebuild to generate PRODUCT_SYSTEMS.md, or @g-subsystem-audit for details."

- Count subsystems/*.md files where parent_system: is missing from frontmatter.
  If missing count > 25% of total:
  flag as LOW health issue:
  "{M} of {N} subsystems are ungrouped -- run @g-subsystem-audit"

- If PRODUCT_SYSTEMS.md exists but has generated_by: stub in frontmatter (T1457 pre-generation stub):
  flag as LOW health issue:
  "PRODUCT_SYSTEMS.md is a stub -- run @g-system-rebuild to populate from current tags"

Tasks that span >1 subsystem AND those subsystems are owned by different projects (per `capabilities.md`) but have no `cross_project_ref:` → flag: "may need cross-project routing"

### L2-H: Creates Missing Stubs

With `--apply`:
- Creates missing `tasks/taskNNN_*.md` for TASKS.md entries that have no file
- Creates missing `features/featNNN_*.md` for FEATURES.md entries that have no file
- Each created file is a minimal stub with YAML frontmatter + `## Objective` placeholder

### L2-I: Platform Health Check (T1460)

If `.gald3r/PLATFORM_STATUS.md` exists, run a platform freshness check for the active platform:

- Call `g-skl-platform-monitor CHECK <current-platform>` (the IDE/agent gald3r is running under).
  This compares the platform's declared capabilities against the Cursor reference and reports gaps.
- Surface the platform's `last_doc_scan` age; if older than its `crawl_max_age_days`, flag LOW:
  "Platform <X> docs not scanned in N days — run @g-platform-scan-docs <X>".
- If the active platform's status row is `❓`, flag LOW:
  "Platform <X> capability unknown — run @g-platform-check <X>".
- Report-only at L2 (no auto-fix). Skip silently if `PLATFORM_STATUS.md` is absent.

### L2 Output

Write `MEDIC_REPORT_L2.md` to `.gald3r/reports/`:
```markdown
# g-medic L2 Diagnosis Report
**Project**: {name} | **Date**: YYYY-MM-DD

## Critical Findings
- [ ] CIRCULAR DEP: Task 42 ↔ Task 43

## Warnings
- [ ] PLAN coherence: Milestone "M3: Auth" shows complete but Task 17 is still pending

## Suggestions
- [ ] Task 95: 11 ACs — consider splitting into 2-3 sub-tasks

## Stubs Created (--apply)
- tasks/task099_placeholder.md
```

---

## Level 3 — Surgery (Cross-Subsystem Interface Audit)

*Requires explicit `--apply` flag. Blast radius: subsystems + schema contracts.*
*Run with `--level 3 --apply`. Generates `MEDIC_REPORT_L3.md`.*

### L3-A: Cross-Subsystem Data Flow Audit

For each pair of subsystems (A writes → B reads):
1. Find all skills/tasks where A produces output consumed by B
2. Compare output format in A's skill/task spec against expected input format in B's skill/task spec
3. Format mismatch → flag as interface violation

### L3-B: Skill Logic Chain Validation

- SKILL.md operations referenced by commands (e.g., `g-task-add` triggers `g-skl-tasks → CREATE`) → verify operation name matches
- Dead references: command references operation that no longer exists in skill → ERROR

### L3-C: Capabilities Gap Detection

- Tasks/features reference a capability (e.g., "vector search", "OAuth") that no subsystem in `capabilities.md` declares as `status: ready`
- Output: `"Capability gap: vector-search — no subsystem owns this in ready state"`

### L3-D: CONSTRAINTS.md Violation Check

For each active constraint in `CONSTRAINTS.md`:
- Scan task/feature specs for planned work that would violate the constraint
- Flag violating tasks with: `"⚠️ Constraint C-{id} violation: {title}"`

### L3-E: Activity Log Audit

Tasks marked `[✅]` that have NOT appended to any subsystem Activity Log in `subsystems/*.md`:
- Flag: "Task {id} completed but subsystem activity log not updated"

### L3-F: Creates / Annotates

With `--apply`:
- Creates missing subsystem spec files for subsystems referenced in tasks but absent from `subsystems/`
- Adds missing capability entries to `capabilities.md` based on subsystem references
- Annotates interface mismatches directly in affected SKILL.md files with:
  ```
  <!-- BUG[MEDIC-L3]: Interface mismatch — A outputs {format}; B expects {format} -->
  ```

### L3-G: Structural Release Upgrade (T430 — engine op)

In **UPGRADE mode** (`.identity` `gald3r_version` < current framework version), L3 can apply
the **structural** diff between two `.gald3r/` release snapshots — complementing the L1-L
per-file schema migration. This is delegated to the canonical engine op `gald3r upgrade`
(shell-out only; never re-implement the diff/merge logic):

```
# dry-run plan (zero writes) — part of the L3 report
gald3r --root <proj> upgrade --from-dir <from_snapshot/.gald3r> --to-dir <to_snapshot/.gald3r> --json
# with --apply (L3 requires explicit --apply): execute + write .gald3r/logs/upgrade_*.log
gald3r --root <proj> upgrade --from-dir <from/.gald3r> --to-dir <to/.gald3r> --apply
```

Per-file classification: **[ADD]** (new in target) / **[MERGE]** (frontmatter/schema changed —
user data preserved, new template keys added, `schema_version`/`gald3r_rel_version` bumped) /
**[DEPRECATE]** (removed in target — archived with `_deprecated_YYYYMMDD`). The engine enforces
an **ABSOLUTE user-data denylist** (`tasks/**`, `bugs/**`, `PLAN.md`, `IDEA_BOARD.md`, `BUGS.md`,
`TASKS.md`) that is **never** touched, and the operation is **idempotent** (a second `--apply`
reports zero changes).

> **Safety**: L3-G runs only in UPGRADE mode and only with `--apply` (consistent with the L3
> "explicit --apply required" rule). In `--dry-run` it reports the planned ADD/MERGE/DEPRECATE
> actions without writing. The engine writes a migration log under `.gald3r/logs/` on apply.
> **Snapshot prerequisite**: the framework currently ships only the single current canonical
> snapshot (`.gald3r_sys/template_verification/.gald3r/`); versioned `vN/` snapshots are a
> tracked prerequisite (T430 finding) — until then, `--from-dir`/`--to-dir` are supplied explicitly.

Engine source: `.gald3r_sys/engine/src/gald3r/systems/upgrade.py` (op: `Gald3r.upgrade`,
CLI: `gald3r upgrade`). Tests: `.gald3r_sys/engine/tests/test_upgrade.py`.

### L3 Output

Write `MEDIC_REPORT_L3.md` to `.gald3r/reports/` with full findings + remediation plan.

---

## Level 4 — Ecosystem (Workspace + Optional PCAC)

*Requires `--level 4` or `--ecosystem` flag. Workspace-Control checks run whenever `.gald3r/linking/workspace_manifest.yaml` exists. PCAC-only checks run only when active PCAC topology exists.*
*Blast radius: controller plus manifest-declared workspace members for read-only diagnostics; PCAC-linked projects only when PCAC is active.*
*If Workspace-Control is active and PCAC is inactive, do not skip L4. Print "PCAC: not active; PCAC topology/inbox checks skipped. Workspace-Control: active; L4 workspace checks ran using workspace_manifest.yaml."*

### L4-0: Mode Split (Mandatory)

Before running L4, classify both coordination systems independently:

- **Workspace-Control active**: `.gald3r/linking/workspace_manifest.yaml` exists and parses. Run L4-W checks.
- **PCAC active**: `.gald3r/linking/link_topology.md` exists and declares at least one non-empty parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares active PCAC relationships. Run L4-P checks.
- **Neither active**: report that L4 has no workspace or PCAC coordination surface.
- **Do not conflate them**: a missing PCAC topology must never suppress Workspace-Control L4 checks.

### L4-W: Workspace-Control Checks

When Workspace-Control is active:

- Parse `.gald3r/linking/workspace_manifest.yaml` as the canonical member registry.
- Validate manifest syntax, repository IDs, roles, lifecycle statuses, local paths, write policies, and routing policy fields.
- Check each existing manifest member's git root, branch, upstream, dirty status, and member `.gald3r/` marker-only compliance.
- Surface missing planned members separately from broken existing members.
- Report Workspace-Control health separately from PCAC health.

### L4-P: PCAC Checks (Only When PCAC Is Active)

Run the following only when PCAC is active:

### L4-P1: Peer Capability Readiness

- Load `.gald3r/linking/peers/*_capabilities.md`
- Find features/tasks this project depends on that a peer hasn't marked `ready`
- Flag: `"Blocked dependency: {this_task} waits on {peer_slug}:{capability} (status: {status})"`

### L4-P2: Cross-Project Constraint Conflicts

- Load peer capability snapshots
- Compare each peer's known constraints against this project's constraints
- Contradictions (Peer A: "no Docker"; this project: "requires Docker for adv tier") → flag

### L4-P3: Cross-Project Feature Contract Validation

- Find features with `cross_project_ref:` slug
- For each: check peer's version of the same feature (via PCAC INFO or snapshot)
- Spec contradictions → flag: "Feature contract mismatch: {slug} — {this_project} spec vs {peer_slug} spec differ"

### L4-P4: Stale Peer Snapshots

- Peer capabilities last synced > N days ago (default 7) → flag: "Stale peer snapshot: {peer_slug} (last sync: {date})"

### L4-P5: Long-Blocked Cross-Project Tasks

- Tasks with `cross_project_ref` blocked on peer completion for > 14 days → surface for human escalation

### L4-P6: Suggested PCAC Actions

For each finding, generate a suggested PCAC coordination message (does NOT send without explicit per-message human approval):
```
Suggested: [SYNC] to example_app — request capability status update for "vector-search"
  → Run: @g-pcac-notify example_app "Requesting capability status update for vector-search"
  Approve? [y/n]
```

### L4 Output

Write `MEDIC_REPORT_L4.md` to `.gald3r/reports/` (workspace findings plus optional affected-peer findings and consolidated ecosystem health score).

```
🌐 Ecosystem Health Score: 72/100 (Degraded)
  example_app:  3 stale capabilities  |  1 contract mismatch
  gald3r_frontend:  snapshot 12d old  |  2 blocked deps > 14d
```

---

## Cumulative Level Summary

Each level is a superset of the previous:

| Level | Name | Blast Radius | `--apply` needed? |
|-------|------|-------------|-------------------|
| L1 | Triage | Files / folders | No (auto) |
| L2 | Diagnosis | `.gald3r/` data | Yes (for fixes) |
| L3 | Surgery | Subsystems + contracts | Yes (required) |
| L4 | Ecosystem | Workspace members + optional PCAC linked projects | Yes for fixes; per-message approval for PCAC sends |

---

## Report File Naming

```
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L1.md
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L2.md
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L3.md
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L4.md
```

---

## L2-E: Harness Subtraction Audit (T1095)

> **Source**: Stanford + Tsinghua University harness engineering papers (2024-2025).
> Finding: same model shows 6× performance gap purely from harness quality. Ablation: verifiers HURT (-8.4 OS World), multi-candidate search HURT (-5.6). **Self-evolution was the ONLY consistently helpful module.** Wessel removed 80% of tools → better results.
> Principle: *"Mature harness work looks less like building structure up and more like pruning it down."*

Run as part of L2 diagnosis — asks what can be REMOVED rather than what should be added.

### Subtraction Audit Questions

Ask these 4 diagnostic questions about the current gald3r harness:

1. **Context bloat**: What's in context that doesn't need to be there? (rules, skills, always-apply content that agents rarely reference)
2. **Tool graveyard**: Which tools does the agent rarely use well? (MCP tools called but producing little value; skills invoked defensively rather than usefully)
3. **Verifier trap**: Are verifiers being added when the model can verify itself? (Per ablation data, external verifiers reduce performance on capable models)
4. **Structure security blanket**: Is scaffolding being added because it's useful or because it feels safe? (Counter-signal: the team adds rules when tasks fail, but the failures have other root causes)

### Harness Age Labels

Flag any rule/skill/hook that has **not caused an agent invocation** in the last N tasks as a "harness-age" candidate:

```
HARNESS-AGE: .cursor/rules/g-rl-XX-*.mdc — no invocations in last 20 tasks
→ Candidate for subtraction review (does not auto-remove; requires human review)
```

Threshold: N = 20 tasks (default). Override with `harness_age_threshold:` in AGENT_CONFIG.md.

### L2-E Subtraction Report Section

Add to L2 report:
```markdown
## Harness Subtraction Audit

Rules with no invocations: N (candidates listed)
Skills with no invocations: N (candidates listed)
Recommendation: [PRUNE / CONSOLIDATE / KEEP] with rationale
Source principle: C-025 (Harness Subtraction — see CONSTRAINTS.md)
```

---

## Parity Exclusion List

See `PARITY_EXCLUDES.md` in this skill's folder for files intentionally excluded from the parity audit.

---

## See Also

- `g-setup` — fresh install; invoked when `.gald3r/.identity` is missing
- `g-skl-tasks` — owns TASKS.md and tasks/
- `g-skl-subsystems` — owns SUBSYSTEMS.md and subsystems/
- `g-skl-constraints` — owns CONSTRAINTS.md
- `g-pcac-status` — PCAC topology view (required for L4)
