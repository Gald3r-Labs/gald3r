---
name: g-skl-subsystems
description: Own and manage SUBSYSTEMS.md (registry + mermaid graph) and subsystems/ spec files. Tracks what subsystems exist, their boundaries, dependencies, and activity logs.
token_budget: medium
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-subsystems

**Files Owned**: `.gald3r/SUBSYSTEMS.md`, `.gald3r/subsystems/**/*.md` (flat `name.md` or nested `domain/name.md`)

**Activate for**: "add subsystem", "g-subsystem-add", "update subsystem spec", "g-subsystem-upd", "deprecate subsystem", "g-subsystem-del", "what subsystems exist", "@g-subsystems", sync check for subsystem drift, before modifying any subsystem's code.

**Commands**: `@g-subsystem-add` (create), `@g-subsystem-upd` (update), `@g-subsystem-del` (deprecate), `@g-subsystems` (list/sync-check)

**Rule**: Read the subsystem spec BEFORE modifying subsystem code. Append to its Activity Log on task completion or bug fix.

---

## Operation: DISCOVER (used during g-setup)

Scan the project to identify subsystems:
- Top-level directories and `src/` subdirectories → candidate subsystems
- Database schema files → table groups suggest subsystems
- Config files → each config suggests a consuming subsystem
- API route files → each route group suggests a subsystem
- Docker services → each container is likely its own subsystem
- External service integrations → listed under their host subsystem

**Classify**:
- **Subsystem** — own code + state + lifecycle → top-level entry + spec file
- **Sub-feature** — shares parent's code/state → documented in parent spec (not its own entry)
- **Integration** — external adapter → listed in host subsystem spec

---

## Operation: CREATE SUBSYSTEM SPEC

**Naming Convention** (validate before creating):
- 2–6 hyphenated words
- Lead with a domain cluster prefix when applicable: `ai-agents-*`, `knowledge-vault-*`
- Describe *what it does or enables* — not just what it is
- Memorable and evocative for developers browsing the project
- Reads naturally as a bullet-point in a README feature list

**Bad**: `planning`, `ideas`, `commands`, `verification`, `hooks-system`  
**Good**: `project-planning-and-roadmaps`, `idea-white-board`, `command-library`, `adversarial-code-review`, `cross-platform-portable-history-logging`

Ask: *"Would a curious developer reading this name want to click into it?"*

If proposed name fails the convention → suggest a compliant alternative and wait for confirmation before creating.

**ENFORCEMENT (C-026 / T1458)**: Before creating the spec file, you MUST ask:
> "Which L1 product system does this subsystem belong to? Valid groups: LOGGING_SYSTEM,
> MEMORY_AND_KNOWLEDGE, TASK_MANAGEMENT, BUG_AND_QUALITY, WORKSPACE_COORDINATION,
> PROJECT_IDENTITY_SETUP, PLATFORM_INTEGRATION, AGENT_ORCHESTRATION, RELEASE_AND_VERSIONING,
> VAULT_AND_RESEARCH, UI_AND_OUTPUT, SECURITY_AND_COMPLIANCE"

If PRODUCT_SYSTEMS.md exists, read `defined_groups:` from its frontmatter to get the authoritative list.
If the user cannot classify it → create with `parent_system: UNCATEGORIZED` and flag for
`@g-subsystem-audit` follow-up. NEVER create a subsystem spec without the `parent_system:` field.

Create `.gald3r/subsystems/{name}.md` (or nested `.gald3r/subsystems/<domain>/<name>.md` when using folder grouping). **Task frontmatter `subsystems:`** continues to use the logical `name:` value — nested folders do not change the identifier agents put in tasks.

```yaml
---
name: subsystem-name
status: active | planned | deprecated
parent_system: TASK_MANAGEMENT    # REQUIRED -- L1 group from PRODUCT_SYSTEMS.md defined_groups:
min_tier: slim | full | adv
# Optional hierarchy (Task 515) -- orthogonal to dependencies:
parent_subsystem: ''   # logical name of parent grouping (must exist when set)
domain: ''           # e.g. platform, harvest, adopted
layer: ''             # e.g. policy, transport, presentation
children: []          # logical child subsystem names (explicit; not inferred only from folders)
dependencies: [other-subsystem-names]
dependents: [subsystem-names-that-depend-on-this]
# Optional code ownership (T1298) — GitHub usernames or @org/team slugs.
# Consumed by `@g-codeowners-gen` (T1299) to generate .github/CODEOWNERS from
# each owned subsystem's `locations:` paths. Empty/absent on most specs; only
# meaningful on project_type=software_development with GitHub integration.
owners: []           # e.g. [octocat, "@acme/backend"]
locations:
  code: [src/subsystem/]
  skills: [g-tasks, g-bugs]
  commands: [g-task-new]
  config: [config/subsystem.yaml]
  db_tables: [table_name]
---

# Subsystem: {name}

## Responsibility
[What this subsystem owns and does — 2-3 sentences]

## Data Flow
[How data enters and exits — inputs, outputs, events]

## Architecture Rules
- [What agents must never do when modifying this subsystem]
- [Patterns required or forbidden]

## When to Modify
[Trigger conditions that indicate work in this subsystem]

## Activity Log
| Date | Type | ID | Title | PRD |
|---|---|---|---|---|
| YYYY-MM-DD | TASK | NNN | {title} | PRD-NNN |
| YYYY-MM-DD | BUG | NNN | Fixed: {brief} | — |
```

**Add to SUBSYSTEMS.md** index and update the mermaid graph.

**Prompts during CREATE**:
- `min_tier:` — What is the minimum gald3r tier required to use this subsystem? (default: `slim`)
  - `slim` — No Docker, no API keys required; pure file-based skill
  - `full` — Requires API keys or network access (e.g., LLM API, GitHub API)
  - `adv` — Requires Docker backend, MCP server, or managed cloud service
- `owners:` (optional, T1298) — GitHub usernames or `@org/team` slugs that own this
  subsystem's code. Leave empty (`[]`) unless GitHub integration is in use. When
  populated, `@g-codeowners-gen` (T1299) emits a `.github/CODEOWNERS` line for each of
  this subsystem's `locations.code` paths assigning these owners. Existing specs need
  no migration — the field is optional and defaults to empty.

  Example populated value:
  ```yaml
  owners: [wrm3, "@gald3r/maintainers"]
  ```

---

## Operation: UPDATE ACTIVITY LOG

After any task completion or bug fix:
1. Read the task/bug's `subsystems:` field
2. For each subsystem, read `.gald3r/subsystems/{name}.md`
3. Append row to Activity Log table

---

## Operation: SYNC CHECK (staleness audit)

Collect all unique `subsystems:` values from task files. Compare to SUBSYSTEMS.md entries.
- In tasks but not in SUBSYSTEMS.md → add stub entry
- In SUBSYSTEMS.md but no spec file → create spec stub
- Spec file exists but `min_tier:` is missing from YAML frontmatter → flag as incomplete: `⚠️ {name} — missing min_tier field. Add: min_tier: slim | full | adv`

**Hierarchy validation (dry-run, no writes)** — recursively scans `.gald3r/subsystems/**/*.md` (excluding generated artifact names), validates parent/child metadata, duplicate names, `locations:` for **index-listed** specs, optional parent/child **domain** mismatch, **SUBSYSTEMS.md** link targets that point at missing files, and emits `disk_not_indexed` in `-Json` for specs not referenced from the index.

```powershell
gald3r subsystem sync
```

Use `-WarnOnly` for advisory exit 0; `-Json` for automation. **Do not conflate** this with the dependency graph: `dependencies:` / `dependents:` describe runtime coupling; `parent_subsystem` / `children` / nested folders describe documentation ownership grouping.

**Regenerate architecture diagrams** (Mermaid, separate tree vs dependency views; includes nested spec paths): `.claude/skills/g-skl-subsystems/scripts/gald3r_subsystem_diagrams_generate.py` (see `SUBSYSTEMS.md` → Generated architecture diagrams).

---

## Operation: LIST (g-subsystems)

Invoked by `@g-subsystems --status active|all`. Renders the subsystem registry.

- **When `parent_system:` is present** on the subsystem spec files (i.e. `PRODUCT_SYSTEMS.md`
  exists and tagging has run): group the output **by L1 parent system**, one section per group,
  in `defined_groups:` order. Append an `UNCATEGORIZED` / ungrouped section last for any spec
  missing `parent_system:`.
  ```
  ## TASK_MANAGEMENT
  | subsystem | status | purpose |
  | task-tracking | active | ... |

  ## BUG_AND_QUALITY
  | subsystem | status | purpose |
  | adversarial-code-review | active | ... |

  ## Ungrouped (run @g-subsystem-audit)
  | subsystem | status | purpose |
  | legacy-thing | active | ... |
  ```
- **Fallback** — when no subsystem file carries `parent_system:`, render the flat
  alphabetical list (legacy behavior).

---

## Operation: DEPRECATE SUBSYSTEM (g-subsystem-del)

1. Read subsystem spec at `.gald3r/subsystems/{name}.md`
2. Update YAML frontmatter: `status: deprecated`
3. Add deprecation note: `deprecated_reason:` and `deprecated_date:`
4. Update SUBSYSTEMS.md index: change Status column to `deprecated`
5. Scan all task files for `subsystems: [{name}]` references — report any that still reference it
6. If active tasks reference it: prompt "These tasks still reference {name} — reassign? [y/n]"
7. Append to Activity Log: `| {date} | DEPRECATE | — | {name} | Deprecated — {reason} |`

**Hard rule**: never delete the spec file. Deprecated subsystems are kept for audit trail.

---

## Operation: AUDIT (g-subsystem-audit)

Invoked by `@g-subsystem-audit`. Reads `PRODUCT_SYSTEMS.md` (frontmatter `defined_groups:` list)
and scans all subsystem spec files + skill SKILL.md files for tagging compliance.

**Outputs**:
- Ungrouped subsystems: spec files missing `parent_system:` frontmatter field
- Unknown groups: `parent_system:` values not in `defined_groups:` list (typo guard)
- Empty groups: L1 groups with no members
- Skills needing review: SKILL.md files with `subsystem_memberships: [UNCATEGORIZED]`

**Algorithm**:
1. Read `PRODUCT_SYSTEMS.md` frontmatter → `$definedGroups` list. If file missing, use
   hardcoded default group list.
2. Scan `.gald3r/subsystems/*.md` — check `parent_system:` in frontmatter.
   - Missing field → report as "ungrouped"
   - Present but not in `$definedGroups` → report as "unknown group (typo?)"
3. Scan `skills/**/SKILL.md` — check `subsystem_memberships:` in frontmatter.
   - Missing → report as "untagged skill"
   - `[UNCATEGORIZED]` → report as "needs manual review"
   - Any value not in `$definedGroups` → report as "unknown group"
4. Report counts per group → flag empty groups as warnings.
5. Recommend: run `@g-system-rebuild` to regenerate `PRODUCT_SYSTEMS.md` from current tags.

---

## Subsystem Tagging Convention (T1457)

Every subsystem spec file MUST include `parent_system:` in its YAML frontmatter:

```yaml
---
name: my-subsystem
status: active
parent_system: TASK_MANAGEMENT    # L1 group — must match defined_groups in PRODUCT_SYSTEMS.md
min_tier: slim
---
```

Every SKILL.md file MUST include `subsystem_memberships:` in its YAML frontmatter:

```yaml
---
name: g-skl-tasks
subsystem_memberships: [TASK_MANAGEMENT]          # single group
# or multi-group when the skill serves multiple systems:
subsystem_memberships: [MEMORY_AND_KNOWLEDGE, TASK_MANAGEMENT]
---
```

Every standalone script (`.ps1`/`.py`) that is NOT inside a tagged skill directory MUST
declare its membership with a header comment in the first ~15 lines:

```powershell
# my_script.ps1 — one-line purpose
# @subsystems: PLATFORM_INTEGRATION
```

**Canonical L1 groups** (from `PRODUCT_SYSTEMS.md` `defined_groups:`):
- `LOGGING_SYSTEM` — session logs, hook output, event capture
- `MEMORY_AND_KNOWLEDGE` — learned facts, session memory, knowledge graphs
- `TASK_MANAGEMENT` — tasks, status, dependency tracking
- `BUG_AND_QUALITY` — bugs, code review, test plans, quality gates
- `WORKSPACE_COORDINATION` — WPAC, topology, cross-repo linking
- `PROJECT_IDENTITY_SETUP` — setup, PROJECT.md, constraints, plans, subsystems
- `PLATFORM_INTEGRATION` — per-platform skills, CLI tools, parity sync
- `AGENT_ORCHESTRATION` — multi-agent coordination, delegation, auto-loops
- `RELEASE_AND_VERSIONING` — git commits, PRs, versioning, changelogs
- `VAULT_AND_RESEARCH` — knowledge ingestion, crawl, recon, research notes
- `UI_AND_OUTPUT` — HTML/JSON/TOON output, themes, image generation
- `SECURITY_AND_COMPLIANCE` — SAST, license scanning, dependency audits

**Adding a new L1 group**: only via T1457-class task. Update `defined_groups:` in
`PRODUCT_SYSTEMS.md` frontmatter first, then re-run `@g-system-rebuild`.

---

## SUBSYSTEMS.md Structure

Add a **navigable hierarchy** view: keep the existing index + mermaid dependency graph, and link to generated `reports/architecture/SUBSYSTEM_TREE.md` (containment) and `DEPENDENCY_GRAPH.md` (depends-on) so readers can switch lenses without merging the two models.

**L1-grouped index (T1458)** — when `PRODUCT_SYSTEMS.md` exists and subsystem specs carry
`parent_system:`, the **Subsystem Index** is rendered grouped by L1 product system (one
`## GROUP_NAME` header per `defined_groups:` entry, members listed beneath) instead of a single
flat alphabetical table. `migrate_schemas.py` regenerates SUBSYSTEMS.md into this grouped form
when `parent_system:` data is present; the flat table remains the fallback when no `parent_system:`
data exists.

```markdown
## LOGGING_SYSTEM
| subsystem | description |
| logging-hooks | ... |

## MEMORY_AND_KNOWLEDGE
| subsystem | description |
| agent-memory | ... |
```

**Hierarchy graph (T1458)** — `@g-subsystem-graph` renders the L1 → L2 containment edges with
Mermaid when `parent_system:` is present (`LOGGING_SYSTEM --> logging-hooks`, etc.); the flat
dependency graph (`dependencies:` edges) remains the fallback when no `parent_system:` data exists.

```markdown
# SUBSYSTEMS.md — {project_name}

## Overview
Read the spec file before modifying any subsystem.

## Taxonomy
- **Subsystem** = engineering unit with its own code, config, state, lifecycle
- **Sub-feature** = component documented within a parent subsystem's spec
- **Integration** = external adapter listed under its host subsystem

## Subsystem Index

| Subsystem | Status | Spec File | Purpose |
|---|---|---|---|
| {name} | active | `subsystems/{name}.md` | {purpose} |

## Sub-Features (in parent specs)
| Sub-Feature | Parent | What It Covers |
|---|---|---|

## Integrations (in parent specs)
| Integration | Host Subsystem | What It Connects |
|---|---|---|

## Interconnection Graph
```mermaid
graph TD
    A[subsystem-a] --> B[subsystem-b]
    B --> C[subsystem-c]
```
```
