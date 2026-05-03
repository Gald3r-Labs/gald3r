---
name: g-skl-setup
description: Initialize gald3r in a project — folder structure and template files for task management.
---
# gald3r-setup

## When to Use
First-time setup of gald3r in a project. @g-setup command.

## Slim vs Full — Know Which You Are Installing

**This skill creates the SLIM layout.** Do not create the folders marked "full only" below.

| Folder | Slim | Full (gald3r_dev only) |
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
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_member_repo_gald3r_guard.ps1 -TargetPath "<absolute_install_target>"
```

Outcomes:

- exit `0` (ALLOW) — target is the workspace control project, outside any workspace, or a template directory; proceed with full setup.
- exit `1` (BLOCK) — target is a Workspace-Control controlled_member or migration_source. **Stop**. Direct the user to either:
  1. Run setup against the workspace control project instead, OR
  2. Run `@g-wrkspc-spawn` (new empty member) or `@g-wrkspc-adopt` (existing standalone gald3r project) if the target should be a workspace member. Both paths use `scripts/bootstrap_member_gald3r_marker.ps1` to create the marker pair (`.identity` + `PROJECT.md`) — they do NOT install the full gald3r control plane in members.
- exit `2` (ERROR) — manifest unparseable. Resolve before continuing. If the project is genuinely standalone (no `.gald3r/linking/workspace_manifest.yaml` in any ancestor), the helper returns ALLOW; an actual exit `2` indicates a broken manifest.

Installed projects ship the same helper at `scripts/check_member_repo_gald3r_guard.ps1`. Template directories (`gald3r_template_slim/`, `gald3r_template_full/`, `gald3r_template_adv/`) are the only legitimate exception for live `.gald3r/` writes outside the control project.

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
   - Create `.gald3r/specifications_collection/README.md` with the index template (see template in `gald3r_template_full/.gald3r/specifications_collection/README.md`)
   - Create `.gald3r/learned-facts.md` from the template in `gald3r_template_full/.gald3r/learned-facts.md`
   - If `.gald3r/.identity` contains `vault_location`, create `{vault_location}/log.md` as a seed file (one header line — `append_log()` will populate it on first ingest)
   - If `.gald3r/.identity` contains `vault_location`, create `{vault_location}/projects/{project_name}/` directory; this is where `repos.txt` and `repo_tracker.json` will live when `github_sync.py` runs
   - If `.gald3r/.identity` contains `vault_location` **and** `{vault_location}/obsidian_setup.md` does not already exist, copy `gald3r_template_full/.gald3r/vault/obsidian_setup.md` (or the installed equivalent at `{skill_root}/reference/obsidian_setup.md`) to `{vault_location}/obsidian_setup.md`. This seeds the one-page Obsidian setup guide so vault users can find it immediately.
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

4. **Generate .identity**:
   ```bash
   python -c "import uuid; print(uuid.uuid4())" > .gald3r/.identity
   ```

5. **Verify structure** (slim v3 layout — ground truth from G:\gald3r\.gald3r):
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
   > These belong in `gald3r_dev` only. Do not create them here.
   > **When `linking/` IS created** (full tier): also seed `.gald3r/linking/capabilities.md` using the template at `gald3r_template_full/.gald3r/linking/capabilities.md`. Replace `{project_slug}` and `{project_name}` placeholders with the actual project name. Replace `{YYYY-MM-DD}` with today's date.

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

8. **Print next steps**:
   - Review `.gald3r/PROJECT.md` and confirm mission and goals
   - Review SUBSYSTEMS.md and adjust detected components
   - Review subsystem spec files in `.gald3r/subsystems/` for accuracy
   - Create first task with @g-tasks (CREATE) (sequential task IDs)
   - Draft or refine `.gald3r/PLAN.md` and Feature under `features/` as needed
   - Declare cross-project relationships in **Project Linking** (`@g-project (Project Linking section)`) when ready
   - **Optional**: Install domain-specific skill packs from `skill_packs/` directory — run `.\skill_packs\{pack}\install.ps1` for infrastructure, ai-ml-dev, startup-tools, and other packs
