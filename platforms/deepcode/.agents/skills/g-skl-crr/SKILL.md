---
name: g-skl-crr
description: Clean-Room Rewrite pipeline. Orchestrates 4 phases via independent background subagents — capture a source repo as a whole-system, consumer-neutral functional spec centralized in the shared vault (research/CRR_FunctionalSpecs/), write all findings to IDEA_BOARD (mandatory), triage tasks, and produce a gald3r-native clean-room implementation spec.
triggers:
  - "@g-crr"
  - "clean room rewrite"
  - "clean-room rewrite"
  - "crr"
  - "harvest and spec"
token_budget: high
subsystem_memberships: [VAULT_AND_RESEARCH, AGENT_ORCHESTRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# SKILL: g-skl-crr — Clean-Room Rewrite Pipeline

## PURPOSE

End-to-end command for adopting an external repo's architectural patterns into gald3r.
Replaces the cumbersome manual workflow of: analyze repo → write ideas → create tasks → write spec.

**What it does:**

1. **Phase 1** — Deep 5-pass, whole-system consumer-neutral functional-spec capture of the source repo, centralized in the shared vault (background subagent)
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
| Source-named environment variables (e.g. `PROJECTNAME_EVENT`, `PROJECTNAME_SESSION_ID`) transcribed verbatim in recon/deep-dive prose | Describe the *shape* generically — "a namespaced-prefix env var set covering event/tool/session/cwd" — never the literal source-branded names, even in `research/` recon files (BUG-004) |
| Source project/org name in commit message **subject or body** | Descriptive language; source URL goes in `Source:` trailer only |
| Source project name in IDEA_BOARD **Title** or **Summary** | Descriptive title; URL in `**Source**:` field only |
| Source project name in task file **title** or **Implementation Notes** | Descriptive; source goes in `## Background` and `## License Note` only |

**Where source names ARE allowed (provenance fields only):**
- `source:` YAML frontmatter field in task files and vault notes
- `**Source**:` field in IDEA_BOARD entries
- Recon vault paths and slugs (e.g., `research/CRR_FunctionalSpecs/owner__repo/`)
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
2. **Check for existing recon**: if `{vault}/research/CRR_FunctionalSpecs/{slug}/05_synthesis.md` exists → prompt `[CRR] Recon already exists for {slug}. Using cached synthesis — skip to Phase 2? (or pass RESUME to re-analyze)`
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

Write all output to: {vault}/research/CRR_FunctionalSpecs/{slug}/

WHOLE-SYSTEM, CONSUMER-NEUTRAL CAPTURE (HARD RULE):
Document the ENTIRE source system as a consumer-neutral functional spec. Do NOT
scope the harvest to "what gald3r could adopt" or filter out capabilities that
seem irrelevant to this project — capture every subsystem, interface, data
model, CLI/UI surface, and workflow, even ones with no conceivable use here.
Relevance and adoption are DOWNSTREAM decisions (Phase 2+ / human), never
capture-time filters. Do NOT editorialize about adoption ("adoption angle
for…", "conceptually adjacent to our own…") in the spec body. Keep license /
clean-room legal commentary in a separate LEGAL_REVIEW.md, not woven through
FEATURES.md. Omit Effort/ROI adoption-triage columns (keep similarity_risk —
it is a legal-safety signal, not adoption triage).

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
  "recon_path": "{vault}/research/CRR_FunctionalSpecs/{slug}/",
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

Read `{vault}/research/CRR_FunctionalSpecs/{slug}/04_FEATURES.md` and `05_synthesis.md`.

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
Recon path: {vault}/research/CRR_FunctionalSpecs/{slug}/
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
> controller — by the standard WPAC dispatch commands. If `.gald3r/linking/link_topology.md` is
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

> The master deliverable. Produces one comprehensive task that specs out HOW to implement the core patterns from the source repo in gald3r's architecture — without copying code. Phase 4 also emits a companion clean-room FUNCTIONAL SPEC package with a requirements-discipline layer (T352): stable FR-/NFR- IDs, MUST/SHOULD/MAY, mandatory VERIFIED-vs-ASSUMPTION flagging, named design principles, a post-write sanitize pass, and — when a prior attempt exists — a critique deliverable. This layer is additive: the STRICT CLEAN-ROOM NAMING ENFORCEMENT table above still governs every artifact this phase writes and is unchanged by it.

Spawn a **background `generalPurpose` subagent** with this prompt:

```
You are the Phase 4 Clean-Room Spec agent for g-crr.

Source repo: {url} ({license})
Slug: {slug}
Synthesis: {vault}/research/CRR_FunctionalSpecs/{slug}/05_synthesis.md
Feature list: {vault}/research/CRR_FunctionalSpecs/{slug}/04_FEATURES.md
Target subsystem hint: {target_subsystem or "auto-detect from synthesis"}
Tasks already created in Phase 3: {tasks_created_ids}

Your job: produce TWO deliverables.
  (A) ONE master task file that specs a gald3r-native clean-room rewrite/integration
      (the implementation plan — see "Task file MUST include" below).
  (B) A companion clean-room FUNCTIONAL SPEC package with requirements discipline
      (see "REQUIREMENTS-DISCIPLINE SPEC PACKAGE" below), written to
      {vault}/research/CRR_FunctionalSpecs/{slug}/clean_room_spec/.

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
6. Write the REQUIREMENTS-DISCIPLINE SPEC PACKAGE (below) to the clean_room_spec/ path.

Task file MUST include:
  - YAML frontmatter (id, title, type: feature, status: pending, priority, subsystems, source, workspace_repos)
  - ## Objective — one paragraph explaining what we're building and why (cost savings, quality, etc.)
  - ## Background — key patterns from the source repo and how they map to gald3r; link the
    companion spec package (spec_package_path) for full requirement-level detail
  - ## gald3r Hook Point — where exactly this plugs into the existing architecture
  - ## Acceptance Criteria — specific, testable checklist items
  - ## Implementation Notes — class names, file paths, method signatures (gald3r-native naming)
  - ## Files to Create/Modify — table with repo, file path, action
  - ## License Note — brief note on the source license and clean-room compliance (the FULL
    legal analysis lives in the spec package's LEGAL_REVIEW.md, not here)
  - ## Cost/Benefit — quantified if possible (e.g. "$250/month saved")
  - ## Status History — initial pending row

Add to .gald3r/TASKS.md as [📋] entry.

REQUIREMENTS-DISCIPLINE SPEC PACKAGE (T352 — mandatory, in addition to the task file):
Write to {vault}/research/CRR_FunctionalSpecs/{slug}/clean_room_spec/:
  - README.md — index, reading order, requirement-keyword conventions (FR-/NFR-, MUST/SHOULD/MAY,
    VERIFIED/ASSUMPTION), actors, glossary.
  - 00_system_overview.md — purpose, scope, actors, capability map, and a short list of named
    DESIGN PRINCIPLES (P1, P2, P3, ...) that every later requirement in this package cites by ID.
  - One file per subsystem covered by the source (derive the breakdown from Phase 1's
    02_module_map.md and 04_FEATURES.md). Complete coverage — do not omit or footnote whole areas.
  - LEGAL_REVIEW.md — a SEPARATE file. State license/IP facts only; defer judgment to a human.
    Never blend legal commentary into the spec body or the task file's ## License Note.
  - CRITIQUE_of_existing_attempt.md — ONLY when a prior spec/analysis of this source already
    exists in the vault or workspace (e.g. an earlier CRR_FunctionalSpecs run, a hand-written
    analysis doc). Evaluate it AS a functional spec: genre fit, presence of testable requirements
    with stable IDs, naming/clean-room discipline, consumer coupling, duplication, completeness,
    legal-content placement, and verified-vs-guessed rigor. Be fair, cite files/lines, end with a
    scorecard table and a recommendation. Skip cleanly (do not create the file) when no prior
    attempt exists.

REQUIREMENTS FORM (mandatory, applies to every requirement written in the spec package):
  - Every behavior is a numbered, testable requirement using MUST/SHOULD/MAY.
  - Stable IDs: FR-<AREA>-<n> for functional requirements, NFR-<n> for non-functional
    requirements. IDs are permanent anchors a test plan can trace to — never renumber, only append.
  - Explicitly NO effort/risk/adoption columns on these requirements (that is consumer coupling —
    adoption triage stays in Phase 1's 05_synthesis.md, not in the spec package).
  - External standards are referenced by CATEGORY, not product name (e.g. "a language-server
    protocol", "a model-context/tool-server protocol", "an OAuth flow"), so a reader is not
    steered into re-adopting the source's exact dependency graph.
  - Data models are specified as enumerated fields with types/constraints, not prose.
  - Contract literals (exit codes, precedence orders, wire fields) MAY be stated when genuinely
    part of an interface contract — but abstract each into a requirement explaining WHY it
    matters, never transcribed as bare source trivia.
  - Keep the spec package CONSUMER-NEUTRAL: no adoption commentary, no portability notes, no
    editorializing about whether gald3r should adopt a given capability — that judgment lives in
    Phase 1's 05_synthesis.md and Phase 2's IDEA_BOARD entries, never in the spec package.

VERIFIED vs ASSUMPTION (mandatory, structural — not optional prose):
Every requirement and every claim about source behavior in the spec package MUST be tagged
VERIFIED (confirmed by reading the source directly) or ASSUMPTION (inferred, not confirmed).
Never blend a guess into a requirement silently — an unflagged assumption becomes a fabricated
requirement for whoever implements from this spec. When in doubt, tag ASSUMPTION.

FINAL SANITIZE PASS (mandatory, post-write — in addition to the pre-write self-check above):
Before returning, grep your own spec-package output for residual proper nouns, brand names, and
CamelCase/snake_case source identifiers. Genericize anything that is not a justified contract
literal. This is a mechanical sweep of what you actually wrote, run LAST after every file in the
package is written — it does not replace the pre-write self-check, it catches what that check missed.

Return a JSON summary when complete:
{
  "task_id": N,
  "task_path": ".gald3r/tasks/task{N}_crr_{slug}.md",
  "spec_package_path": "{vault}/research/CRR_FunctionalSpecs/{slug}/clean_room_spec/",
  "requirement_count": {"functional": N, "non_functional": N},
  "assumption_count": N,
  "critique_written": true|false,
  "sanitize_pass": "clean" | "flagged: [...]"
}
```

**Wait for Phase 4 subagent to complete.**

### Framework-Isolation / Personality-Suppression Ruling (T352)

A related field-tested prompt for this same task genre opens with an instruction to ignore all
project/agent framework rules, personas, and task-system conventions in the workspace. That
instruction is correct for a **fresh session pointed at a foreign repo with no framework of its
own** — its intent is to stop harness personas, rule-file idioms, or task-system vocabulary
contaminating a vendor-neutral spec deliverable. It is **not** ported verbatim here, because it
is self-contradictory inside a gald3r skill: the skill IS the framework instructing the agent.

**Ruling**: the Phase 4 (and Phase 1) subagent dispatch prompts suppress *voice*, not
*governance*:
- The `gald3r_personality.md` persona overlay does NOT apply to spec-package deliverables
  (README.md, 00_system_overview.md, subsystem files, LEGAL_REVIEW.md,
  CRITIQUE_of_existing_attempt.md) — these are written for an audience with no knowledge of
  gald3r, in neutral technical register, with no persona voice, no Norse framing, no gald3r
  commit-message conventions, and no task-system vocabulary bleeding into the prose.
- This does NOT suspend gald3r's own operating rules for the *agent* (task/bug logging, naming
  enforcement, commit discipline, `.gald3r/` write gates) — those still govern how the subagent
  behaves. Only the *written voice of the spec artifacts* is suppressed.
- The STRICT CLEAN-ROOM NAMING ENFORCEMENT table above is unaffected by this ruling and remains
  in force for all artifacts.

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
  Recon: {vault}/research/CRR_FunctionalSpecs/{slug}/

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
  • Review recon: {vault}/research/CRR_FunctionalSpecs/{slug}/05_synthesis.md
  • Implement: @g-go tasks {crr_task_id}
  • Review IDEA_BOARD: @g-idea-review
```

---

## STATUS / RESUME OPERATIONS

### STATUS `<slug>`

```
[CRR] Status for {slug}
  Recon path: {vault}/research/CRR_FunctionalSpecs/{slug}/
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
- Vault: `research/CRR_FunctionalSpecs/Tencent-Hunyuan__Hunyuan3D-2/` (5 files — slug OK in path)
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

---

## Rescued-Artifact Convention (D019, T374)

`skills/<skill>/reference/` is the **standing home for rescued cross-repo
artifacts** (owner ruling 2026-07-21, `DECISIONS.md` D019). `research/` is
gitignored and stays that way — a rescue instructed to land there must instead
land in the consuming skill's `reference/` directory (precedent:
`g-skl-crr/reference/clean_room_spec_prompt.md`). Future `g-skl-crr` /
`g-skl-res-*` rescues point here, not at `research/harvests/`.
