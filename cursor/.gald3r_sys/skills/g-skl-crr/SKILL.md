---
name: g-skl-crr
description: Clean-Room Rewrite pipeline. Orchestrates 4 phases via independent background subagents — harvest a source repo, write all findings to IDEA_BOARD (mandatory), triage tasks, and produce a gald3r-native clean-room implementation spec.
triggers:
  - "@g-crr"
  - "clean room rewrite"
  - "clean-room rewrite"
  - "crr"
  - "harvest and spec"
token_budget: high
subsystem_memberships: [VAULT_AND_RESEARCH, AGENT_ORCHESTRATION]
---

# SKILL: g-skl-crr — Clean-Room Rewrite Pipeline

## PURPOSE

End-to-end command for adopting an external repo's architectural patterns into gald3r.
Replaces the cumbersome manual workflow of: analyze repo → write ideas → create tasks → write spec.

**What it does:**

1. **Phase 1** — Deep 5-pass harvest of the source repo (background subagent)
2. **Phase 2** — Mandatory IDEA_BOARD write of ALL findings (coordinator-owned)
3. **Phase 3** — Task triage + task file creation for immediate candidates (background subagent)
4. **Phase 4** — Clean-room implementation spec task (background subagent)

Each phase is a separate agent. The coordinator never implements — it routes work, collects outputs, and writes shared state.

---

## STRICT CLEAN-ROOM NAMING ENFORCEMENT (HARD RULE — DEFAULT FOR ALL EXTERNAL SOURCES)

**Applies to ALL output: task titles, task implementation notes, IDEA_BOARD entries, vault notes, commit messages, commit subjects, code class names, function names, variable names, config keys, .md file prose — everywhere.**

**Default mode = external source.** Unless `$ARGUMENTS` contains `--own-work` or `--allow-source-names`, the following are **FORBIDDEN** in every artifact this pipeline produces or instructs subagents to produce:

| FORBIDDEN in generated artifacts | REQUIRED instead |
|---|---|
| Source project name in any code symbol | Descriptive functional name — `LocalMeshProvider`, not `HunyuanProvider` |
| Source organization name in any symbol | gald3r-native naming conventions throughout |
| Exact non-generic source function/method/class names | Equivalent role with a new name — `generate_mesh()` not `hunyuan3d_generate()` |
| Source library/package names used as identifiers | Generic role names — `mesh_backend`, `diffusion_engine`, `local_3d_provider` |
| Source-named constants, enums, or config keys | Descriptive gald3r-native keys |
| Source project/org name in commit message **subject or body** | Descriptive language; source URL goes in `Source:` trailer only |
| Source project name in IDEA_BOARD **Title** or **Summary** | Descriptive title; URL in `**Source**:` field only |
| Source project name in task file **title** or **Implementation Notes** | Descriptive; source goes in `## Background` and `## License Note` only |

**Where source names ARE allowed (provenance fields only):**
- `source:` YAML frontmatter field in task files and vault notes
- `**Source**:` field in IDEA_BOARD entries
- Recon vault paths and slugs (e.g., `research/recon/owner__repo/`)
- `## Background` prose: *"the source project implements a diffusion-based pipeline..."* (describe the pattern, not the name)
- `## License Note` section
- Commit message **trailer** line only: `Source: https://github.com/...`
- `_recon_index.yaml` entries (traceability index, never implementation)

**Opt-out flags (must appear in `$ARGUMENTS`):**
- `--own-work` — source is the user's own project or their employer's project; all naming restrictions lifted
- `--allow-source-names` — user explicitly permits source naming in generated artifacts (log the reason in the pipeline summary)

**Subagent propagation (MANDATORY):** Every subagent dispatch prompt spawned by this skill MUST include the full enforcement table above and the active flag state (`--own-work: false` or `--allow-source-names: false` by default). Subagents may NOT relax this rule on their own.

**Self-check before writing any artifact:**
> "Does this output contain a source project name, org name, or exact source identifier outside a provenance field?"
> If YES → replace with a descriptive gald3r-native name before writing.

---

## COORDINATOR RULES

> **The coordinator MUST NOT ask the user to confirm, select, or approve.** Fire-and-forget operation. Apply auto-plan rules silently and proceed.

> **The coordinator NEVER implements.** It routes to subagents, collects their outputs, and performs shared `.gald3r/` writes (IDEA_BOARD, TASKS.md, task files, commits).

> **IDEA_BOARD writes are MANDATORY after Phase 1.** Never skip. Never defer. Never ask permission. Every finding, even if immediately becoming a task, also appears in IDEA_BOARD.

---

## ARGUMENT PARSING

Parse `$ARGUMENTS` before doing anything:

```
@g-crr <url>                              → full 4-phase pipeline
@g-crr <url> --target-subsystem <name>   → hint the spec toward a subsystem
@g-crr <url> --ideas-only                → phases 1+2 only (no tasks, no spec)
@g-crr <url> --no-spec                   → phases 1+2+3 (no spec task)
@g-crr <url> --mode fast                 → haiku-class subagents for phases 1/3/4
@g-crr STATUS <slug>                     → show recon status for existing slug
@g-crr RESUME <slug>                     → resume from last complete phase
```

Extract:
- `url` — the GitHub repo URL (required unless STATUS/RESUME)
- `slug` — `owner__repo` derived from URL (e.g. `Tencent-Hunyuan__Hunyuan3D-2`)
- `target_subsystem` — from `--target-subsystem` or left blank (auto-detected in Phase 4)
- `ideas_only` — boolean flag
- `no_spec` — boolean flag
- `mode` — `fast` | `standard` (default standard)

---

## PHASE 0 — PRE-FLIGHT

Before spawning any subagents:

1. **Resolve vault location**: read `.gald3r/.identity`, extract `vault_location=`
2. **Check for existing recon**: if `{vault}/research/recon/{slug}/05_synthesis.md` exists → prompt `[CRR] Recon already exists for {slug}. Using cached synthesis — skip to Phase 2? (or pass RESUME to re-analyze)`
3. **Get current IDEA-HARVEST-NNN**: run `Select-String -Path ".gald3r/IDEA_BOARD.md" -Pattern "IDEA-HARVEST-(\d+)"` → take max → store as `idea_start_num`
4. **Get current task count**: scan `tasks/` for highest id → store as `task_start_id`
5. **Load target subsystem** (if provided): read `.gald3r/subsystems/{target_subsystem}.md`
6. **Log**: `[CRR] Starting pipeline for {url} | slug={slug} | idea_start={idea_start_num} | task_start={task_start_id}`

---

## PHASE 1 — DEEP HARVEST (background subagent)

Spawn a **background `generalPurpose` subagent** with this prompt:

```
You are the Phase 1 Harvest agent for g-crr.

Read and follow the skill at: .claude/skills/g-skl-res-deep/SKILL.md

Then run: ANALYZE {url}

This is a 5-pass deep analysis. Complete all 5 passes:
  01_skeleton.md — repo structure + tech fingerprint
  02_module_map.md — module/component decomposition
  03_feature_scan.md — raw feature inventory
  04_FEATURES.md — structured feature list (adoption-ready)
  05_synthesis.md — adoption recommendations + cost/benefit

Write all output to: {vault}/research/recon/{slug}/

Clean-room boundary: observe and summarize source behavior, interfaces,
workflows, data shapes, and architectural patterns only. Never copy source
code, docs prose, prompts, tests, or unique strings verbatim.

STRICT NAMING RULE (active unless --own-work or --allow-source-names was passed):
Do NOT use the source project name, org name, or exact non-generic source
function/class/variable names in any output you write. Use descriptive
gald3r-native names throughout. Source names are allowed ONLY in provenance
fields (source: YAML field, ## Background prose, recon vault paths).
If you cannot describe a pattern without using a source-specific name, use
a bracketed placeholder like [PATTERN: diffusion-mesh-pipeline] and flag it.

Return a JSON summary when complete:
{
  "status": "complete" | "partial" | "error",
  "slug": "{slug}",
  "recon_path": "{vault}/research/recon/{slug}/",
  "passes_complete": ["01", "02", "03", "04", "05"],
  "feature_count": N,
  "top_findings": ["...", "...", "..."],
  "license": "MIT|Apache|Custom|Unknown",
  "error": null | "description"
}
```

**Wait for Phase 1 subagent to complete before proceeding.**

If Phase 1 returns `status: error`, log and stop: `[CRR] BLOCKED — Phase 1 harvest failed: {error}. Fix and RESUME.`

---

## PHASE 2 — IDEA_BOARD WRITE (coordinator-owned, mandatory)

> **This phase is coordinator-owned. No subagent. The coordinator writes directly.**

### 2a. Read the synthesis

Read `{vault}/research/recon/{slug}/04_FEATURES.md` and `05_synthesis.md`.

Extract ALL findings:
- Features worth adopting (high/medium/low priority)
- Architectural patterns worth noting
- Patterns gald3r already has (document as SKIP entries — still write them)
- License/cost/risk notes worth tracking
- Anything else in the synthesis

**Minimum entries**: 3 entries per repo. An "everything is already covered" finding still produces 3 SKIP entries explaining why.

### 2b. Number entries

```powershell
$max = (Select-String -Path ".gald3r/IDEA_BOARD.md" -Pattern "IDEA-HARVEST-(\d+)" |
    ForEach-Object { [int]($_.Matches[0].Groups[1].Value) } |
    Measure-Object -Maximum).Maximum
$next = if ($max) { $max + 1 } else { 1 }
```

### 2c. Write to IDEA_BOARD.md

Append a batch block using `StrReplace` (never overwrite):

```markdown
## HARVEST-BATCH-{YYYY-MM-DD}-crr-{slug}
*Source: {url} | Harvested: {YYYY-MM-DD} | License: {license} | via g-crr*

---

### IDEA-HARVEST-{NNN}
**Title**: {idea title}
**Source**: {file/section in recon where this was found}
**Priority**: high|medium|low
**Type**: feature|enhancement|architecture|research|skip
**Summary**: {2-3 sentences: what gald3r could adopt and why, or why it's a skip}
**Action**: [Task candidate — pending Phase 3] OR [IDEA_BOARD capture] OR [SKIP — {reason}]

### IDEA-HARVEST-{NNN+1}
...
```

### 2d. Record batch metadata

Store:
- `idea_batch_start` = `$next`
- `idea_batch_end` = last written number
- `immediate_candidates` = list of IDEA-HARVEST-NNN entries with Action: `[Task candidate]`

Log: `[CRR] Phase 2 complete — wrote IDEA-HARVEST-{idea_batch_start} through {idea_batch_end}. Immediate task candidates: {count}`

**If `--ideas-only` flag was set:** commit the IDEA_BOARD write and stop here. Print summary and exit.

---

## PHASE 3 — TASK TRIAGE + CREATION (background subagent)

Spawn a **background `generalPurpose` subagent** with this prompt:

```
You are the Phase 3 Task Triage agent for g-crr.

Source repo: {url}
Slug: {slug}
Recon path: {vault}/research/recon/{slug}/
IDEA_BOARD candidates: IDEA-HARVEST-{idea_batch_start} through {idea_batch_end}

Read and follow the skill at: .claude/skills/g-skl-tasks/SKILL.md

Your job:
1. Read .gald3r/IDEA_BOARD.md — find all IDEA-HARVEST-{NNN} entries from this batch
   that have Action: "[Task candidate — pending Phase 3]"
2. For each candidate, decide: IMMEDIATE task (implement now) or PARK (stays on IDEA_BOARD)
   - IMMEDIATE criteria: clear AC, no major architectural unknowns, additive (not replacement), high/medium priority
   - PARK: research needed, architectural conflict, low value, duplicate of existing task
3. For each IMMEDIATE candidate, create a task file using CREATE TASK operation:
   - id: next sequential (check .gald3r/tasks/ for max)
   - title: descriptive, gald3r-native (not source repo terminology)
   - type: feature | enhancement | research
   - priority: high | medium | low
   - subsystems: [relevant subsystem names]
   - source: {url}
   - target_repo: pass through the IDEA_BOARD entry's "Target Repo" value (default `local`) — T1430
   - Write .gald3r/tasks/task{N}_{slug}.md with full Objective + AC + Implementation Notes
4. Update .gald3r/TASKS.md — add each new task row

> **WPAC-aware routing (T1430):** Phase 3 does NOT itself dispatch cross-repo. It only carries
> `target_repo:` through from each IDEA-HARVEST entry onto the created task's frontmatter. Actual
> routing (parent direct-write / sibling INBOX send-to / multi-repo decomposition / controller
> `requires_decomposition`) is performed by `g-skl-res-apply` per its routing table, OR — for a
> controller — by the standard WPAC dispatch commands. If `.gald3r/workspace/topology.md` is
> absent, `target_repo:` is forced to `local` and tasks are created in the local repo only.

Return a JSON summary:
{
  "tasks_created": [{"id": N, "title": "...", "idea_ref": "IDEA-HARVEST-NNN", "target_repo": "local"}, ...],
  "tasks_parked": [{"idea_ref": "IDEA-HARVEST-NNN", "reason": "..."}, ...],
  "next_task_id": N
}
```

**Wait for Phase 3 subagent to complete before proceeding.**

Coordinator writes: collect task IDs from subagent output. Do NOT let the subagent commit.

**If `--no-spec` flag was set:** commit everything (IDEA_BOARD + task files + TASKS.md) and stop. Print summary and exit.

---

## PHASE 4 — CLEAN-ROOM SPEC TASK (background subagent)

> The master deliverable. Produces one comprehensive task that specs out HOW to implement the core patterns from the source repo in gald3r's architecture — without copying code.

Spawn a **background `generalPurpose` subagent** with this prompt:

```
You are the Phase 4 Clean-Room Spec agent for g-crr.

Source repo: {url} ({license})
Slug: {slug}
Synthesis: {vault}/research/recon/{slug}/05_synthesis.md
Feature list: {vault}/research/recon/{slug}/04_FEATURES.md
Target subsystem hint: {target_subsystem or "auto-detect from synthesis"}
Tasks already created in Phase 3: {tasks_created_ids}

Your job: produce ONE master task file that specs a gald3r-native clean-room rewrite/integration.

This is NOT a copy of the source repo. This is a NEW gald3r implementation that adopts the
PATTERNS and ARCHITECTURE from the source, using gald3r's existing subsystems and conventions.

STRICT NAMING RULE — active unless you were explicitly told --own-work or --allow-source-names:
- FORBIDDEN in task title, class names, function names, config keys, commit messages:
  source project name, org name, exact non-generic source identifiers
- REQUIRED: descriptive gald3r-native names throughout
  (e.g. "LocalDiffusionMeshProvider" not "[SourceName]Provider")
- ALLOWED only in provenance fields: source: YAML, ## Background, ## License Note, Source: trailer
- If you cannot name something without using the source name, use a descriptive role name
  and note the original term in ## Background only

Steps:
1. Read .gald3r/SUBSYSTEMS.md — find the most relevant target subsystem
   If --target-subsystem was given, read .gald3r/subsystems/{target_subsystem}.md
2. Read the synthesis report — extract the 3-5 most architecturally significant patterns
3. Identify the gald3r hook point (existing abstraction, provider, skill, or subsystem boundary
   where the new implementation plugs in — like Mesh3DProvider for Hunyuan3D)
4. Design the gald3r-native implementation:
   - What files to create (with gald3r-style naming)
   - What existing files to modify (minimal surface area)
   - What the new component's interface looks like (class/function signatures)
   - Acceptance criteria as a checklist
5. Write the task file to .gald3r/tasks/task{next_id}_crr_{slug}.md

Task file MUST include:
  - YAML frontmatter (id, title, type: feature, status: pending, priority, subsystems, source, workspace_repos)
  - ## Objective — one paragraph explaining what we're building and why (cost savings, quality, etc.)
  - ## Background — key patterns from the source repo and how they map to gald3r
  - ## gald3r Hook Point — where exactly this plugs into the existing architecture
  - ## Acceptance Criteria — specific, testable checklist items
  - ## Implementation Notes — class names, file paths, method signatures (gald3r-native naming)
  - ## Files to Create/Modify — table with repo, file path, action
  - ## License Note — brief note on the source license and clean-room compliance
  - ## Cost/Benefit — quantified if possible (e.g. "$250/month saved")
  - ## Status History — initial pending row

Add to .gald3r/TASKS.md as [📋] entry.

Return the task ID and file path.
```

**Wait for Phase 4 subagent to complete.**

---

## PHASE 5 — COORDINATOR COMMIT

After all subagents complete, the coordinator performs the final write and commit:

```powershell
# Stage all new/modified files
git add ".gald3r/IDEA_BOARD.md"
git add ".gald3r/TASKS.md"
# Stage all new task files created by phases 3 and 4
git add ".gald3r/tasks/task*.md"

# Commit
$msg = "feat(crr): {slug} harvest — IDEA-HARVEST-{start}..{end}, T{task_ids_csv}`n`nClean-room rewrite pipeline via g-crr.`nSource: {url} ({license})`nPhase 1: {feature_count} features analyzed`nPhase 2: {idea_count} IDEA_BOARD entries`nPhase 3: {task3_count} immediate tasks created`nPhase 4: CRR spec task T{crr_task_id}"
git commit -m $msg
```

---

## PIPELINE SUMMARY OUTPUT

```
[CRR] Pipeline complete for {url}

Phase 1 — Harvest
  Passes complete: 01 02 03 04 05
  Features found: {N}
  Recon: {vault}/research/recon/{slug}/

Phase 2 — IDEA_BOARD
  Entries written: IDEA-HARVEST-{start} → {end} ({count} entries)
  Immediate candidates: {N}

Phase 3 — Task triage
  Tasks created: {list of T{id}: title}
  Parked (IDEA_BOARD only): {count}

Phase 4 — CRR spec task
  Task: T{id} — {title}
  File: .gald3r/tasks/task{id}_crr_{slug}.md

Commit: {sha}

Next steps:
  • Review recon: {vault}/research/recon/{slug}/05_synthesis.md
  • Implement: @g-go tasks {crr_task_id}
  • Review IDEA_BOARD: @g-idea-review
```

---

## STATUS / RESUME OPERATIONS

### STATUS `<slug>`

```
[CRR] Status for {slug}
  Recon path: {vault}/research/recon/{slug}/
  Passes complete: {list}
  IDEA_BOARD entries: IDEA-HARVEST-{start}..{end} (or "none yet")
  Tasks created: T{ids} (or "none yet")
  CRR spec task: T{id} (or "none yet")
  Last phase: {1|2|3|4|none}
```

### RESUME `<slug>`

Detect last completed phase by checking what exists:
- No `01_skeleton.md` → start from Phase 1
- Has `05_synthesis.md` but no IDEA_BOARD entries for slug → start from Phase 2
- Has IDEA_BOARD entries but no CRR task → start from Phase 3 or 4
- Has CRR task and commit → `Already complete. Nothing to resume.`

Re-run from the detected restart point.

---

## CLEAN-ROOM BOUNDARY (HARD RULE)

All four phases must respect this boundary:

| ✅ Allowed | ❌ Forbidden |
|-----------|-------------|
| Summarizing what the source does | Copying source code |
| Describing architectural patterns | Copying doc prose verbatim |
| Noting interfaces and data shapes | Copying prompts or system instructions |
| Describing workflows | Copying test cases |
| Referencing file paths as traceability | Using source variable/function names as-is |
| Quantifying cost/performance improvements | Reproducing any unique strings |

The Phase 4 spec must use gald3r-native naming conventions throughout.
Source file paths in the spec are traceability references, NOT implementation instructions.

---

## EXAMPLE RUN

```
@g-crr https://github.com/Tencent-Hunyuan/Hunyuan3D-2 --target-subsystem 3d-pipeline
```

Produces (default — strict naming, source name NOT in artifacts):
- Vault: `research/recon/Tencent-Hunyuan__Hunyuan3D-2/` (5 files — slug OK in path)
- IDEA_BOARD: entries titled e.g. "Local-first open-source diffusion 3D mesh generator (zero API cost)"
  NOT: "Hunyuan3D-2 integration" — source name stays in `**Source**:` field only
- Phase 4 task: T1187 — "Add local-first diffusion mesh provider as primary Mesh3DProvider"
  Class name: `LocalDiffusionMeshProvider` NOT `HunyuanProvider`
- Commit: `feat(3d): add local-first diffusion mesh provider (clean-room)\n\nSource: https://github.com/Tencent-Hunyuan/Hunyuan3D-2`

With `--allow-source-names` (user explicitly permits):
- Task: T1187 — "HunyuanProvider: add Hunyuan3D-2.1 as primary Mesh3DProvider"  
- Class: `HunyuanProvider` — source name permitted, documented in pipeline summary

With `--own-work` (source is user's own code):
- No restrictions. Source names used freely.

---

## FILE PATHS TO NEVER TOUCH

- Source repo files (recon is read-only observation)
- `.gald3r/.identity`, `.gald3r/.project_id` (marker-only invariant)
- Any file outside `.gald3r/`, `docs/`, `vault/` unless explicitly in a task's `workspace_repos:`
