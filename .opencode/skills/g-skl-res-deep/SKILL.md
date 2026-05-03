---
name: g-skl-res-deep
description: Analyze any external repository and produce a structured FEATURES.md harvest report. Writes to {vault}/research/recon/{slug}/ when a shared vault is configured, else falls back to local research/harvests/{slug}/. Performs cross-project dedup via _recon_index.yaml. Agents are reporters — humans are editors. No .gald3r/ writes until human approves APPLY.
---
# g-skl-res-deep (reverse-spec)

**Activate for**: "reverse spec", "analyze this repo", "harvest this project", "what features does X have", "extract features from", "what can we adopt from".

**Files Written** (vault-aware): `{vault}/research/recon/{slug}/` when `vault_location` ≠ `{LOCAL}`, else `research/harvests/{slug}/`. Never writes to `.gald3r/` directly — that happens only via `g-skl-res-apply`.

**Core Principle**: Agents are **reporters**. Humans are **editors**. Document everything visible. Never filter by "gald3r already has this" or "not relevant." The human decides relevance.

---

## Clean Room Reverse-Spec Contract

`g-skl-res-deep` is a research and specification tool, not an implementation copier. Agents may inspect source material to understand externally visible behavior, workflows, data models, interfaces, configuration surfaces, and architectural tradeoffs. Outputs must transform those observations into original prose and structured requirements. Do not copy source code, comments, docs prose, prompts, tests, generated strings, or distinctive implementation structure into recon outputs except tiny attributed excerpts that are license-compatible and necessary as evidence.

Every recon report must preserve provenance (`source`, license when discoverable, capture date, and source file references) while keeping `FEATURES.md` entries behavior-level. `source_files` are traceability pointers only; they are not implementation instructions. If a feature cannot be described without copying implementation details, mark it `[🔍] needs-review` and require a human clean-room decision before APPLY.

---

## Vault-Aware Output Path (T081)

Every operation resolves the output base path before doing anything else.

### Path resolution (per C-003)

```
1. Read .gald3r/.identity (key=value, no quotes)
2. Extract vault_location=
3. If vault_location is {LOCAL} or missing:
     recon_base  = "research/harvests/"
     index_path  = "research/harvests/_recon_index.yaml"
     vault_mode  = "local"
4. Else (vault_location is a real path):
     recon_base  = f"{vault_location}/research/recon/"
     index_path  = f"{vault_location}/research/recon/_recon_index.yaml"
     vault_mode  = "shared"
5. output_dir = f"{recon_base}{slug}/"
```

**Rationale**: When `vault_location` points at a shared vault, any recon written locally duplicates effort already done (or queued) by another project on that vault. Moving the output to `{vault}/research/recon/` means every project sharing the vault benefits from the prior analysis. Local fallback preserves the existing behavior for projects with `vault_location={LOCAL}`.

**Constraint compliance**:
- C-001 file-first: path resolution is plain filesystem, no MCP required
- C-003: `.identity` is the only source for `vault_location`
- C-006: migration + dedup updates append to `{vault}/log.md` or `research/log.md` (see AC-7)

### Slug normalization

`user/repo` → `user__repo` (lowercase, `/` → `__`, `.` → `-`).

---

## Dedup Manifest — `_recon_index.yaml` (T081)

The dedup index is the **pre-flight gate** for every ANALYZE/HARVEST. If a recent entry exists for `{slug}`, return `[CACHED: {slug}]` and skip the expensive re-analysis.

### Schema

```yaml
# Auto-managed by g-skl-res-deep / g-skl-res-review / g-skl-res-apply
# Do not hand-edit unless you know what you're doing.
schema_version: 1
entries:
  - slug: user__repo
    source_url: https://github.com/user/repo
    title: "Repo Title"
    last_run: YYYY-MM-DD
    status: complete | partial | stale
    output_path: research/recon/user__repo/   # relative to vault root (shared) or project root (local)
```

### Location

| Mode | Path |
|------|------|
| `shared` (vault) | `{vault_location}/research/recon/_recon_index.yaml` |
| `local` | `research/harvests/_recon_index.yaml` |

### Dedup check (pre-flight)

```
Before starting ANALYZE:
1. Resolve index_path (see path resolution above)
2. If file does not exist → create empty manifest; continue with ANALYZE
3. If exists: parse YAML, find entry where slug == {slug}
4. If entry found:
     age_days = today - entry.last_run
     if age_days <= max_age_days and entry.status == complete:
         print f"[CACHED: {slug}] — last run {entry.last_run} ({age_days}d old)"
         print f"  path: {entry.output_path}"
         print f"  to force re-run: pass --force or --max-age-days 0"
         return
     else:
         mark entry for refresh; continue with ANALYZE
5. If not found → continue with ANALYZE; add entry on completion
```

### Design decision (recorded in `vault/log.md`)

> `FEATURES.md` files are NOT bulk-indexed into the vector DB. `_recon_index.yaml` is the fast-lookup manifest for dedup. Full-text search of harvest content stays a file-grep operation; semantic search of harvest content is out of scope until a dedicated ingest flow is built. (See DECISIONS.md D098.)

This keeps recon writes **file-first** (C-001) and avoids the cost of re-embedding every harvest on every vault reindex.

---

## Operations

| Operation | Usage |
|-----------|-------|
| `ANALYZE {repo_url}` | Full 5-pass analysis of a repository |
| `RESUME {slug}` | Continue an interrupted analysis from the last completed pass |
| `APPLY {slug}` | Write approved features to `.gald3r/features/` staging (delegates to `g-skl-res-apply`) |
| `APPLY --dry-run {slug}` | Print what APPLY would create without writing |
| `STATUS {slug}` | Show current harvest state, pass completion, and dedup status |

### Common parameters

| Flag | Default | Effect |
|------|---------|--------|
| `--max-age-days N` | 30 | Override dedup staleness threshold (0 = always re-run) |
| `--force` | false | Skip dedup check entirely (equivalent to `--max-age-days 0`) |
| `--dry-run` | false | Print planned writes without touching the filesystem |

---

## Operation: ANALYZE

```
ANALYZE https://github.com/user/repo
ANALYZE /path/to/local/repo
ANALYZE https://github.com/user/repo --max-age-days 7
```

### Setup

1. Derive `{slug}` from URL: `user/repo` → `user__repo`
2. **Resolve vault-aware output path** (see Vault-Aware Output Path above)
3. **Run dedup pre-flight** against `_recon_index.yaml` (see Dedup Manifest). If `[CACHED]` → return immediately
4. Create output dir: `{recon_base}{slug}/`
5. Secondary guard: if `FEATURES.md` exists and is `< max_age_days` old → offer RESUME instead (this is a defense-in-depth check; the primary dedup gate is `_recon_index.yaml`)
6. Write `_harvest_meta.yaml`:
   ```yaml
   source: {url}
   slug: {slug}
   started: {YYYY-MM-DD}
   vault_mode: shared | local
   output_path: {recon_base}{slug}/
   passes_completed: []
   ```

### 5-Pass Strategy

Each pass writes its output file before the next pass begins. If context runs out mid-pass, run RESUME.

---

#### Pass 1: Skeleton 📦

**Goal**: Map the top-level architecture — what kind of project is this?

**Read**:
- `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md` (if any)
- Root directory listing (file/folder names only, no content)
- `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` (dependencies only)

**Write** → `{output_dir}/01_skeleton.md`:
```markdown
---
pass: 1
slug: {slug}
source: {url}
completed: {YYYY-MM-DD}
---
# Pass 1: Skeleton
...
```

---

#### Pass 2: Module Map 🗂️

**Goal**: Map each top-level module/folder to its responsibilities.

**Write** → `{output_dir}/02_module_map.md`.

---

#### Pass 3: Feature Scan 🔍

**Goal**: Read the most important files in each module and catalog every distinct feature.

**Reporter Rule**: Document every distinct capability observed in original wording. Do NOT skip features because "the target project already has this." The human decides what to adopt. Do NOT copy source implementation, docs prose, prompts, tests, or unique strings.

**Write** → `{output_dir}/03_feature_scan.md`.

---

#### Pass 4: Deep Dives 🔬

**Goal**: For features worth detailed examination, inspect implementation only to understand behavior, interfaces, data flow, and constraints. Do not transcribe implementation text or structure.

**Write** → `{output_dir}/04_deep_dives.md`.

---

#### Pass 5: Synthesis 📋

**Goal**: Produce the final FEATURES.md — a clean-room, behavior-level harvest report for human review.

**Write** → `{output_dir}/FEATURES.md` with **Obsidian-standard frontmatter** (T044, T081 AC-8):

```markdown
---
date: {YYYY-MM-DD}
type: recon
ingestion_type: reverse_spec
source: {url}
title: "Recon: {project name}"
tags: [recon, reverse-spec]
target_name: {project name}
slug: {slug}
harvested: {YYYY-MM-DD}
passes_completed: [1, 2, 3, 4, 5]
features_total: N
features_approved: 0
analyst: {agent-id or "human"}
clean_room_boundary: true
license_observed: {license-or-unknown}
verbatim_excerpt_policy: tiny_attributed_excerpts_only
---

# Harvest: {project name}

## Summary
[3-5 sentences about the project and what makes it worth harvesting]

## Feature Catalog

| ID | Feature | Effort | Status | Notes |
|----|---------|--------|--------|-------|
| F-001 | Feature Name | S | [ ] pending | brief note |

---

## Feature Details
...
```

Update `_harvest_meta.yaml`:
```yaml
passes_completed: [1, 2, 3, 4, 5]
completed: {YYYY-MM-DD}
features_total: N
status: ready_for_review
```

**Finalize**: append/update entry in `_recon_index.yaml`:
```yaml
- slug: {slug}
  source_url: {url}
  title: "Recon: {project name}"
  last_run: {YYYY-MM-DD}
  status: complete
  output_path: {relative_output_path}
```

**Log**: append to `{vault}/log.md` (shared) or `research/log.md` (local):
```
| {YYYY-MM-DD} | recon-complete | {slug} | g-skl-res-deep (features_total={N}) |
```

---

## Operation: RESUME

```
RESUME user__repo
```

1. Read `{output_dir}/_harvest_meta.yaml` → `passes_completed`
2. Find highest completed pass → continue from pass N+1
3. If `passes_completed: [1,2,3,4,5]` → "Harvest complete. Run APPLY to create feature staging docs."

RESUME respects the vault-aware path: the meta file is under `{recon_base}{slug}/` regardless of mode.

---

## Operation: APPLY

```
APPLY user__repo
APPLY --dry-run user__repo
```

Delegated to `g-skl-res-apply`. See that skill for full details. APPLY reads `{output_dir}/FEATURES.md` (vault-aware) and creates `.gald3r/features/` staging documents for each `[✅] approved` feature.

---

## Operation: STATUS

```
STATUS user__repo
```

Prints:
```
Harvest: user__repo (github.com/user/repo)
Mode: shared (vault={vault_location}/research/recon/)
Passes: [1✅, 2✅, 3✅, 4⬜, 5⬜]
Features found: 23 (Pass 3)
Last updated: 2026-04-10
Dedup entry: present, status=partial, last_run=2026-04-10, 11d old (threshold 30d)
Status: Pass 4 pending — run ANALYZE to continue
```

---

## Output Directory Layout

```
{recon_base}{slug}/
├── _harvest_meta.yaml      # state tracking
├── 01_skeleton.md          # Pass 1 output
├── 02_module_map.md        # Pass 2 output
├── 03_feature_scan.md      # Pass 3 output
├── 04_deep_dives.md        # Pass 4 output (if needed)
└── FEATURES.md             # Pass 5 synthesis (review target)

{recon_base}_recon_index.yaml  # dedup manifest (shared by all slugs)
```

---

## Feature Status Codes

In `FEATURES.md`:
| Code | Meaning |
|------|---------|
| `[ ] pending` | Not yet reviewed |
| `[✅] approved` | Include in APPLY |
| `[❌] skip` | Human decided to skip |
| `[🔍] needs-review` | Interesting but needs more investigation |

---

## Migration Helper

For projects that have existing `research/harvests/*/` folders from before T081, run:

```
python .cursor/skills/g-skl-res-deep/scripts/migrate_harvests_to_recon_index.py
```

This script:
1. Resolves `vault_location` from `.gald3r/.identity`
2. Scans existing `research/harvests/*/` (local) and/or `{vault}/research/recon/*/` (shared)
3. For each harvest folder: reads existing frontmatter, adds any missing Obsidian fields (`date`, `type`, `source`, `title`, `tags`) with best-effort values
4. Seeds `_recon_index.yaml` with one entry per harvest folder
5. Appends a migration row to `{vault}/log.md` (or `research/log.md`)
6. **Never deletes files** — migration is additive only

Idempotent: re-running the script updates existing entries without duplicating them.

---

## Integration

**With `g-skl-res-review`**: `g-skl-res-review` reads the same vault-aware path and `_recon_index.yaml`. When a source is cached, review surfaces the existing report rather than re-harvesting.

**With `g-skl-res-apply`**: APPLY reads `FEATURES.md` from the vault-aware output path; the `input:` frontmatter field in `g-skl-res-apply` respects the same resolution.

**With `g-skl-vault`**: When vault is configured, output writes go through the file-first vault path — no MCP required.

**Reporter Rule — always enforced**:
> "We are documenting what this project does, not copying how it is written. A feature being already present in gald3r is NOT a reason to skip it — it is a reason to note the behavioral overlap and learn from the alternative approach in original wording."
