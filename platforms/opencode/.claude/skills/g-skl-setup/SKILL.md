---
name: g-skl-setup
description: Initialize gald3r in a project — folder structure and template files for task management.
token_budget: medium
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# gald3r-setup

## When to Use
First-time setup of gald3r in a project. @g-setup command.

## Slim vs Full — Know Which You Are Installing

**This skill creates the SLIM layout.** Do not create the folders marked "full only" below.

| Folder | Slim | Full (<gald3r_source> only) |
|--------|------|------------------------|
| `tasks/`, `bugs/`, `features/`, `subsystems/`, `reports/`, `logs/` | ✅ | ✅ |
| `config/` (HEARTBEAT.md, SPRINT.md, AGENT_CONFIG.md) | ❌ | ✅ |
| `experiments/` (EXPERIMENTS.md, HYPOTHESIS.md, SELF_EVOLUTION.md) | ❌ | ✅ |
| `linking/` (README.md, INBOX.md) | ❌ | ✅ |
| `vault/` | ❌ | ✅ |
| `phases/` (legacy v2) | ❌ | ✅ |

## Steps

### Step 0 — Workspace-Control member-repo guard (BUG-021 / Task 213 v1.1 / g-rl-36)

**Before any folder or file creation**, verify the target install path is not a Workspace-Control controlled_member or migration_source repository. `g-skl-setup` is for installing a full standalone gald3r project; member repositories use a marker-only `.gald3r/` shape that is owned by `g-wrkspc-spawn` / `g-wrkspc-adopt` plus the bootstrap helper, NOT full setup.

```powershell
uv run python .claude/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.py -TargetPath "<absolute_install_target>"
```

Outcomes:

- exit `0` (ALLOW) — target is the workspace control project, outside any workspace, or a template directory; proceed with full setup.
- exit `1` (BLOCK) — target is a Workspace-Control controlled_member or migration_source. **Stop**. Direct the user to either:
  1. Run setup against the workspace control project instead, OR
  2. Run `@g-wrkspc-spawn` (new empty member) or `@g-wrkspc-adopt` (existing standalone gald3r project) if the target should be a workspace member. Both paths use `.claude/skills/g-skl-workspace/scripts/bootstrap_member_gald3r_marker.py` to create the marker pair (`.identity` + `PROJECT.md`) — they do NOT install the full gald3r control plane in members.
- exit `2` (ERROR) — manifest unparseable. Resolve before continuing. If the project is genuinely standalone (no `.gald3r/linking/workspace_manifest.yaml` in any ancestor), the helper returns ALLOW; an actual exit `2` indicates a broken manifest.

Installed projects ship the same helper at `.claude/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.py`. External template repos (`<ECOSYSTEM_ROOT>/<template_slim>`, `<ECOSYSTEM_ROOT>/<template_full>`, `<ECOSYSTEM_ROOT>/<template_adv>`) are the only legitimate exception for live `.gald3r/` writes outside the control project.

### Step 0.5 — Git Readiness Check

Run this after Step 0 passes and **before** any `.gald3r/` folder creation. Skip entirely if Step 0 blocked (member-repo targets do not need this check).

**1. Is this a git repo?**
```
git rev-parse --is-inside-work-tree
```
- Exit 0 → repo exists, continue to check 2.
- Non-zero exit → not a git repo. Offer (default Y):
  ```
  "This directory is not a git repo. Initialize git? [Y/n]"
  → Y: git init && git commit --allow-empty -m "chore: initial commit"
  → N: warn "g-go-go autopilot requires git; some features will not work" then continue
  ```

**2. Does a `main` branch exist?**

gald3r uses a **feature-branches-only model** — a single permanent `main` branch plus
short-lived `feature/*` and `fix/*` branches. There is **no long-lived `dev`/`test` branch**
(see `g-rl-02-git_workflow`). Confirm `main` exists as the integration target:
```
git branch --list main
```
- Non-empty output → `main` exists, skip.
- Empty → check the current default branch name (`git rev-parse --abbrev-ref HEAD`). If the repo
  uses a differently-named default (e.g. `master`), note it; otherwise offer (default Y):
  ```
  "No 'main' branch found. Create main from current HEAD? [Y/n]"
  → Y: git branch -M main
        [if remote exists] git push --set-upstream origin main
  → N: warn "g-go-go autopilot auto-merge will MERGE-BLOCKED without a main branch"
  ```

**2b. Migrate an existing `dev`-model repo (USER-SAFETY — T1535 / BUG-099)**

A repo created under the retired `dev`/`test` promotion model may still carry a
long-lived `dev` branch. The old auto-merge defaulted to that `dev` branch, which was
the root cause of the BUG-099 history-loss class. Detect and offer a **safe,
confirmation-gated** migration — **never auto-delete a user branch**:
```
git branch --list dev
```
- Empty → no migration needed, skip silently.
- Non-empty → a legacy `dev` branch exists. Compute its relationship to `main`:
  ```
  git rev-list --left-right --count main...dev
  ```
  Then offer (default N — destructive-adjacent, so do NOT default Y):
  ```
  "Legacy 'dev' branch detected (old promotion model). gald3r is now
   feature-branches-only -> main. Promote dev's unique work onto main, then
   retire dev? This will NOT delete dev until you confirm a second time. [y/N]"
  → Y: 1. git checkout main
       2. git merge --ff-only dev   (if dev is strictly ahead — safe fast-forward)
          - if FF is not possible, STOP and report: "dev and main diverged
            (N ahead / M behind). Manual review required — not auto-merging."
       3. Only after a clean FF, offer separately:
          "Retire (delete) the local 'dev' branch now? [y/N]"
          → Y: git branch -d dev   (safe delete; refuses if not merged)
          → N: leave dev in place; print "dev retained — delete manually when ready"
  → N: print "Left dev in place. You remain on the legacy model until migrated."
  ```
- This step is **report-only when no `dev` branch exists** and **never performs a
  force-delete (`-D`) or a non-fast-forward merge** without explicit user confirmation.

**3. Remote check (info only — never blocks setup)**
```
git remote -v
```
- No remote configured → print info note only:
  `"No git remote configured. g-go-go autopilot cross-session merges require push access. Add later: git remote add origin <url>"`

**All prompts default to Y and are non-blocking** — declining any prompt adds a warning but does not stop the setup. The agent should present options as numbered choices in its response, then run the chosen commands.

### Step 0.7 — Optional Git LFS (T1311)

Offered for **all** project types (3d_modeling and content_creation benefit most;
software_development repos with large binaries also). **Not enabled by default** —
must be explicitly opted in.

```
"Enable Git LFS for binary files? Recommended for 3d_modeling / content_creation. [y/N]"
→ Y:
   git lfs install
   copy assets/gitattributes-lfs.template  →  <project>/.gitattributes
       (if .gitattributes exists, append the gald3r LFS block under a
        '# <!-- gald3r LFS SECTION -->' marker rather than clobbering it)
   git add .gitattributes
→ N (default): skip — existing repos are unaffected.
```

Storage-cost note to surface: GitHub LFS bills for **storage + bandwidth** beyond
the free quota (1 GB / 1 GB-month on free plans); large media histories can exceed
it quickly. Use LFS deliberately, not as a default. Verify patterns apply with
`git check-attr filter <file>` (expect `filter: lfs`).

The template (`assets/gitattributes-lfs.template`) covers: `.psd .ai .fbx .obj
.blend .max .png .jpg .gif .mp4 .mov .wav .zip .glb .gltf` and similar binaries.

### Step 1 — Detect if existing (check before creating anything)
   ```
   □ .gald3r/TASKS.md exists AND > 20 lines?
   □ .gald3r/tasks/ has > 5 files?
   □ PROJECT.md has non-template content?
   → YES: EXISTING project → ask: Merge / Skip / Reset (DESTRUCTIVE)
   → NO: FRESH install → proceed
   ```

2. **Call gald3r_install MCP tool** (if available):
   ```python
   gald3r_install(project_path="{absolute_path}", use_v2=True)
   ```

3. **If gald3r_install unavailable**, create manually:
   - Folders: `.gald3r/`, `.gald3r/tasks/`, `.gald3r/features/`, `.gald3r/bugs/`, `.gald3r/subsystems/`, `.gald3r/reports/`, `.gald3r/logs/`, `.gald3r/specifications_collection/`
   - Create `.gald3r/specifications_collection/README.md` with the index template (see template in `<ECOSYSTEM_ROOT>/<template_full>/.gald3r/specifications_collection/README.md`)
   - Create `.gald3r/learned-facts.md` from the template in `<ECOSYSTEM_ROOT>/<template_full>/.gald3r/learned-facts.md`
   - If `.gald3r/.identity` contains `vault_location`, create `{vault_location}/log.md` as a seed file (one header line — `append_log()` will populate it on first ingest)
   - If `.gald3r/.identity` contains `vault_location`, create `{vault_location}/projects/{project_name}/` directory; this is where `repos.txt` and `repo_tracker.json` will live when `github_sync.py` runs
   - If `.gald3r/.identity` contains `vault_location` **and** `{vault_location}/obsidian_setup.md` does not already exist, copy `<ECOSYSTEM_ROOT>/<template_full>/.gald3r/vault/obsidian_setup.md` (or the installed equivalent at `{skill_root}/reference/obsidian_setup.md`) to `{vault_location}/obsidian_setup.md`. This seeds the one-page Obsidian setup guide so vault users can find it immediately.
   - **Research-type projects:** when creating `TASKS.md`, add a research log section below the task list
   - Files: Use g-project (CREATE PROJECT.MD) and g-plan (CREATE PLAN.MD) for all file generation
   - Seed `CONSTRAINTS.md` with:
     1. The standard Governance section (including the Constraint Scope table)
     2. An empty Constraint Index table with columns: `ID | Status | Name | Scope | One-line summary`
     3. An empty Constraint Definitions section
     4. An empty Change Log table
     5. A comment block before the index explaining scope values:
        ```markdown
        <!-- CONSTRAINT SCOPE: local-only (default) | inheritable (propagate to children on spawn) | shareable (peers opt-in) | ecosystem-wide (all topology members) -->
        ```

3b. **Skill trust-level warning (C-032 — non-blocking)**: when the install bundles or copies any skills (template skill packs, adv-tier skill_packs), apply the same provenance check as `g-skill-pack-add` step 3b — surface a non-blocking warning for any skill whose `skill_trust_level:` is `community` or unset (trust level, source, `allowed-tools:` reminder, inspect-before-first-invocation). Slim setup ships only `core` skills, so this normally produces no warning; it fires when a non-core pack is added during or after setup. Canonical wording: `skl-skill-create/SKILL.md` → `### skill_trust_level:` declaration.

4. **Generate .identity**:
   ```bash
   python -c "import uuid; print(uuid.uuid4())" > .gald3r/.identity
   ```

4b. **Set project_type** (T1280):
   Ask the user "What kind of project is this?" with numbered choices, then write
   the chosen value to `.gald3r/.identity` as `project_type=<value>` (key=value
   format, canonical lowercase). Pressing enter selects the default.
   ```
   What kind of project is this?
     1. software_development   (default — enables GitHub PR/issue integration, code review, etc.)
     2. content_creation
     3. 3d_modeling
     4. research_analysis
     5. freeform
   [1]
   ```
   - Default selection (enter) = `software_development`.
   - Honor a `--project-type=<value>` CLI flag to skip the prompt.
   - Validation is case-insensitive but stored lowercase. An unknown value read
     later logs a warning and is treated as `freeform`.
   - Confirm: `Project type set to: {value}`.
   - The chosen `project_type` gates which Workflow Profile, Integration Bundle,
     and Command Set are active (e.g. GitHub integration activates only for
     `software_development`).

5. **Verify structure** (slim v3 layout — ground truth from <project-root>\.gald3r):
   ```
   .gald3r/ ✅
   ├── .identity ✅
   ├── .gitignore ✅
   ├── TASKS.md ✅
   ├── PLAN.md ✅                 ← master strategy (above PRDs)
   ├── PROJECT.md ✅             ← mission, goals, Project Linking
   ├── CONSTRAINTS.md ✅         ← non-negotiable constraints
   ├── BUGS.md ✅                ← bug index (root)
   ├── SUBSYSTEMS.md ✅
   ├── IDEA_BOARD.md ✅
   ├── FEATURES.md ✅                ← PRD index
   ├── learned-facts.md ✅       ← agent-captured learning (updated via /g-learn)
   ├── features/ ✅                  ← individual PRD files
   ├── bugs/ ✅                  ← optional per-bug detail files
   ├── reports/ ✅
   ├── logs/ ✅
   ├── subsystems/ ✅            ← per-subsystem spec files
   ├── specifications_collection/ ✅  ← incoming specs from stakeholders
   └── tasks/ ✅
   docs/ ✅
   ```

   > **NOT in slim:** `config/`, `experiments/`, `linking/`, `vault/`, `phases/`
   > These belong in `<gald3r_source>` only. Do not create them here.
   > **When `linking/` IS created** (full tier): also seed `.gald3r/linking/capabilities.md` using the template at `<ECOSYSTEM_ROOT>/<template_full>/.gald3r/linking/capabilities.md`. Replace `{project_slug}` and `{project_name}` placeholders with the actual project name. Replace `{YYYY-MM-DD}` with today's date.

6. **Create PROJECT.MD scaffolding**:
   - `.gald3r/PROJECT.md` — include a **Project Linking** section (parents, children, siblings); starts with `relationships: none`

7. **Subsystem Discovery** (run after folder creation):
   Scan the project to identify subsystems. For each, create a spec file in `.gald3r/subsystems/`:
   
   **What to scan:**
   - Top-level directories and `src/` subdirectories → candidate subsystems
   - Database schema files → table groups suggest subsystems
   - Config files → each config suggests a consuming subsystem
   - API route files → each route group suggests a subsystem
   - Docker services → each container is likely its own subsystem
   - External service integrations → integration entries in host subsystem
   
   **For each identified subsystem, create spec with:**
   ```yaml
   locations:
     code: [source file paths]
     skills: [relevant gald3r skills]
     agents: [relevant gald3r agents]
     commands: [relevant gald3r commands]
     config: [config files]
     db_tables: [owned tables]
   ```
   Plus: Responsibility, Data Flow, Architecture Rules, When to Modify sections.
   
   **Classify as:**
   - **Subsystem** (own code + state + lifecycle) → top-level entry + spec file
   - **Sub-feature** (shares parent's code/state) → documented in parent spec
   - **Integration** (external adapter) → listed in host subsystem spec
   
   Update SUBSYSTEMS.md with the index table, sub-features table, integrations table, and mermaid interconnection graph.

8. **Write skills lock file** (T1043):
   After platform skill directories are placed (whether by `gald3r_install` MCP, by `bin/install.js`, or manually), write `gald3r-skills-lock.json` at project root via:
   ```powershell
   .\scripts\gald3r_skills_lock.ps1 -Action WRITE -ProjectPath . -Tier <slim|full|adv>
   ```
   - Records SHA-256 hash of each installed `SKILL.md` so future runs can detect tamper / drift.
   - Pair with `-Action VERIFY` during `gald3r_validate.ps1` runs.
   - Pair with `-Action UPGRADE -SourceRoot <<gald3r_source> path>` to classify each installed skill as `unchanged | local-modified | upstream-changed | both-changed | new | removed` before pulling a new gald3r version.
   - Lock file format and operations documented in `docs/SKILLS_LOCK_FORMAT.md`.

8b. **Codebase Graph Initialization (gald3r_muninn, T1149)** — non-blocking, always optional:
   - Check index state via `graph_status` (MCP) or `.claude/skills/g-skl-muninn/scripts/graph_impact.ps1 -File <any source file> -Json`. If it reports `index_missing` / `warning: not_indexed`, offer to build it now:
     ```powershell
     python -m docker.gald3r.tools.plugins.muninn.indexers.python_indexer --root .   # Python sources
     node  docker/gald3r/tools/plugins/muninn/indexers/ts_indexer.js  --root .       # TS/JS sources (needs Node.js)
     ```
     The gald3r_muninn indexers run **natively on Windows, macOS, and Linux** (clean-room rewrite — no WSL2/Docker required, unlike the deprecated GitNexus). If Python or Node.js is missing, skip that indexer and continue — setup never blocks on graph init, and if the user declines the index simply stays absent (g-go-code Step b0 falls back to ripgrep).
   - **Auto-wire the post-commit refresh hook** (idempotent, after user confirmation) so the index stays fresh:

     **PowerShell (Windows — native):**
     ```powershell
     $hookFile = ".git/hooks/post-commit"
     # use the active platform's hook path (.cursor/hooks/, .claude/hooks/, ...)
     $hookLine = "uv run python .cursor/hooks/g-hk-graph-update.py"
     $existing = if (Test-Path $hookFile) { Get-Content $hookFile -Raw } else { "" }
     if ($existing -notlike "*$hookLine*") { Add-Content -Path $hookFile -Value $hookLine }
     ```

     **Bash (Linux / macOS / Git Bash on Windows):**
     ```bash
     HOOK_FILE=".git/hooks/post-commit"
     # use the active platform's hook path (.cursor/hooks/, .claude/hooks/, ...)
     HOOK_LINE="uv run python .cursor/hooks/g-hk-graph-update.py"
     grep -qF "$HOOK_LINE" "$HOOK_FILE" 2>/dev/null || { printf '%s\n' "$HOOK_LINE" >> "$HOOK_FILE"; chmod +x "$HOOK_FILE"; }
     ```
     Re-running setup does not duplicate the line; the hook exits 0 on all platforms even if indexing fails. See the **Codebase Graph (gald3r_muninn)** section below.

9. **Print next steps**:
   - Review `.gald3r/PROJECT.md` and confirm mission and goals
   - Review SUBSYSTEMS.md and adjust detected components
   - Review subsystem spec files in `.gald3r/subsystems/` for accuracy
   - Create first task with @g-tasks (CREATE) (sequential task IDs)
   - Draft or refine `.gald3r/PLAN.md` and Feature under `features/` as needed
   - Declare cross-project relationships in **Project Linking** (`@g-project (Project Linking section)`) when ready
   - **Optional**: Install domain-specific skill packs from `skill_packs/` directory — run `.\skill_packs\{pack}\install.ps1` for infrastructure, ai-ml-dev, startup-tools, and other packs

---

## Codebase Graph (gald3r_muninn)

The codebase graph (gald3r_muninn) indexes Python and TypeScript/JavaScript source so `g-go-code` **Step b0 Impact Scan** can answer "what breaks if I change this file?" with real import/call edges instead of a linear grep. It is **optional** — when absent, Step b0 falls back to ripgrep (non-blocking).

**What it does**: builds a local SQLite graph at `~/.gald3r/muninn.db` (override with `MUNINN_DB_PATH`). `graph_impact` / `graph_callers` / `graph_callees` / `graph_deps` / `graph_status` query it.

**How to initialize** (step 8b above): run the Python + TypeScript indexers once, then let the post-commit hook (`g-hk-graph-update.ps1`) refresh changed files on every commit.

**OS support matrix** (clean-room rewrite — supersedes the WSL-only GitNexus):

| OS | Python indexer | TypeScript indexer | Notes |
|----|----------------|--------------------|-------|
| Windows | ✅ native | ✅ native (needs Node.js) | No WSL2/Docker required |
| macOS | ✅ native | ✅ native (needs Node.js) | — |
| Linux | ✅ native | ✅ native (needs Node.js) | — |

If a runtime (Python / Node.js) is missing, skip that indexer — the graph simply indexes the languages it can, and Step b0 falls back to ripgrep for the rest. Initialization, the post-commit hook, and the `gald3r_install` post-install offer are all non-blocking.

---

## Relationship to the root installer (`setup_gald3r_project.ps1`)

gald3r has **two distinct setup entry points** with non-overlapping responsibilities. They are not alternatives that ask the same questions twice:

| Entry point | Owns | Does NOT do |
|-------------|------|-------------|
| **`setup_gald3r_project.ps1`** (root installer, run from a shell) | **Platform selection** (`-Platforms`, the interactive platform picker, `-Platform all`), copying the `.gald3r_sys/` payload + per-platform IDE dirs into the target, section-marker merge of `AGENTS.md`/`CLAUDE.md`/`.gitignore`, JSON key-merge of platform config, and v1/v2/v3 version detection on upgrade | Author project mission/goals or scaffold the `.gald3r/` control plane content |
| **`@g-setup`** (this skill, run in-session) | The `.gald3r/` control-plane scaffold — folder layout, `PROJECT.md`/`PLAN.md`/`CONSTRAINTS.md`/`SUBSYSTEMS.md`, identity files, subsystem detection, codebase-graph init offer | **Platform selection** — it does **not** re-prompt for or deploy IDE platform dirs |

**Design decision (T1209 AC6 / T1275):** `@g-setup` **delegates** platform selection to the root installer; it does **not** re-prompt in-session. The platform picker (`-Platforms` / interactive prompt in `setup_gald3r_project.ps1`) is the single source of truth for *which* IDE surfaces (`.cursor/`, `.claude/`, `.codex/`, …) get deployed. Re-implementing a second platform prompt inside `@g-setup` would duplicate that logic and risk drift.

**Recommended order for a brand-new project:**

1. Run `setup_gald3r_project.ps1 -TargetPath <dir>` (it prompts for platforms if `-Platforms` is omitted) — this lays down `.gald3r_sys/` + the chosen IDE platform dirs and merges the marker-managed root files.
2. Then run `@g-setup` in-session to scaffold and personalize the `.gald3r/` control plane (mission, goals, subsystems, first task).

If a user invokes `@g-setup` on a project that has no IDE platform dirs yet, point them at `setup_gald3r_project.ps1` for platform deployment rather than prompting for platforms here.

---

## gald3r Engine (bundled) <!-- gald3r-engine-note -->

This install bundles the gald3r **engine** at `.gald3r_sys/engine/` — a deterministic Mode-A
core (no LLM calls) that the slimmed skills call for state CRUD (tasks, bugs, features, prds,
ideas, constraints, subsystems, release, vault) and to serve the centralized judgment prompts.

- **Provision / verify** (one-time): `pwsh .gald3r_sys/engine/provision_engine.ps1`
  (macOS/Linux without pwsh: `sh .gald3r_sys/engine/provision_engine.sh`). The only prerequisite
  is `uv`, which the script installs if missing. The installer runs this automatically.
- Slimmed skills then call: `uv run --project .gald3r_sys/engine gald3r <verb>` (or MCP `gald3r_*`).
- If the engine isn't provisioned, every slimmed skill still works via its **`SKILL.full.md`**
  fallback — nothing points outside the install.
