---
name: g-skl-pcac-spawn
description: >
  Spawn a new gald3r project from the current project. Creates the new project folder
  in the same ecosystem root, installs gald3r (matching the current project's install
  type — symlinks or fresh template), seeds it with any passed description/features/code,
  runs gald3r-setup, and immediately links both projects via PCAC topology
  (--parent | --sibling | --child).
---

# g-skl-pcac-spawn

**File Owner**: none (creates a new project; source project's topology is updated in place)

**Activate for**: "spawn a new project", "create a new child/sibling/parent project", "extract this into its own repo", "new project from features", `@g-pcac-spawn`

---

## When to Use

When a part of the current project has grown large enough to warrant its own separately
maintained repository, but it currently lives inside this project (as code, features,
specifications, or ideas). This skill orchestrates the full lifecycle:

1. Create the new project folder in the ecosystem root
2. Install gald3r (matching current project's install style)
3. Seed the new project with passed context (description, features, code, etc.)
4. Run gald3r-setup subsystem discovery in the new project
5. Register PCAC topology link in both projects

---

## Command Syntax

```
@g-pcac-spawn <new_project_name> --sibling [options]
@g-pcac-spawn <new_project_name> --child [options]
@g-pcac-spawn <new_project_name> --parent [options]

Options:
  --description "..."          One-line mission statement for the new project
  --features <subfolder>       Path (relative or absolute) to a features/ subfolder to transfer
  --code <path>                Path to code folder(s) to copy into the new project
  --template slim|full|adv     Which gald3r template tier to install (default: matches current)
  --dry-run                    Show what would be created without touching anything
```

**Examples**:
```
@g-pcac-spawn gald3r_valhalla --sibling --description "Single-user Docker backend for gald3r" --features .gald3r/features/gald3r_backend
@g-pcac-spawn gald3r_payments --child --description "Payment processing subsystem" --code src/payments/
@g-pcac-spawn gald3r_platform --parent --description "Platform coordination layer"
```

---

## Pre-Flight Checks

Before doing anything, validate:

```
□ Current project has .gald3r/.identity (gald3r is installed here)
□ Current project has .gald3r/linking/link_topology.md (PCAC is initialized)
□ new_project_name does not already exist in the ecosystem root
□ If --features: the specified path exists and contains at least one .md file
□ If --code: the specified path exists
□ relationship (--sibling/--child/--parent) is specified
□ Template source has .gitignore and opencode.json (warn if missing, use inline defaults)
□ Workspace-Control member-repo guard (BUG-021 / Task 213 / g-rl-36)
```

### Workspace-Control Member-Repo Guard

`g-pcac-spawn` creates a brand-new standalone gald3r project (with full control plane and PCAC topology link) at `<ecosystem_root>/<new_project_name>`. PCAC spawn is **not** the Workspace-Control member path — Workspace-Control members hold a slim marker-only `.gald3r/` (`.identity` + `PROJECT.md` only), while PCAC spawn intentionally seeds the full control plane.

If the destination falls inside (or matches) a Workspace-Control controlled_member or migration_source registered in any ancestor `workspace_manifest.yaml`, this would violate the marker-only invariant documented in `g-rl-36` (BUG-021 / Task 213).

Run the guard helper against the planned new-project path **before Step 2** materializes any `.gald3r/` directory:

```powershell
$newProjectPath = Join-Path $ecosystemRoot $new_project_name
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_member_repo_gald3r_guard.ps1 -TargetPath $newProjectPath
```

- exit `0` — proceed (target is not a workspace member).
- exit `1` — **stop with `BLOCK pcac_spawn_member_repo_gald3r_guard_block`**. The target is a Workspace-Control member; PCAC spawn would seed the full control plane and violate the marker-only invariant. Direct the user to either:
  1. Spawn under a non-member parent path, OR
  2. Use `@g-wrkspc-spawn` for new empty workspace members (which uses `scripts/bootstrap_member_gald3r_marker.ps1` to create only `.identity` + `PROJECT.md`).
- exit `2` — stop with `BLOCK pcac_spawn_member_repo_gald3r_guard_error`. Resolve the manifest before retrying.

Installed projects ship the helper at `scripts/check_member_repo_gald3r_guard.ps1`.

If `--dry-run`: print a full preview and stop. Do not create anything. The guard is reported in dry-run preview but does not block dry-run output (only blocks apply).

If any non-dry-run check fails → stop and report with fix instructions.

---

## Steps

### Step 0 — Determine ecosystem root

```
Read: .gald3r/.identity → project_path
Ecosystem root = parent directory of project_path
Example: G:\gald3r_ecosystem\current_project → root is G:\gald3r_ecosystem\
New project path = <ecosystem_root>\<new_project_name>
```

### Step 1 — Detect current project's gald3r install style

```
Check if .cursor/rules/ contains symlinks → PowerShell: (Get-Item .cursor/rules/g-rl-00-always.mdc).LinkType
  "SymbolicLink" → style = "symlink"
  $null or "" → style = "copy"

Check which template tier:
  If gald3r_template_full/.gald3r/ exists in current project → tier = "full"
  Else read .gald3r/.identity for gald3r_version hints or assume "slim"
```

Store: `$install_style`, `$template_tier` (overridden by `--template` if provided)

### Step 2 — Create new project folder structure

```powershell
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\tasks"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\features"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\bugs"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\subsystems"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\reports"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\logs"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\.gald3r\linking"
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\docs"
```

Create git repo:
```powershell
cd "<ecosystem_root>\<new_project_name>"
git init
```

### Step 3 — Install gald3r (matching style)

**If style = "symlink"**:
  - Determine the symlink target root (usually the current project's template path)
  - Create `.cursor/rules/` symlinks pointing to `gald3r_template_full/.cursor/rules/`
  - Create `.claude/` symlinks or copies as appropriate
  - Create `.cursor/skills/` symlinks pointing to template skills

**If style = "copy"** (default safe path):
  - Read the current project `.gald3r/.identity` → locate `gald3r_template_slim/` or `gald3r_template_full/` path
  - Copy `.cursor/rules/` from the appropriate template tier
  - Copy `.claude/skills/` from the current project `.claude/skills/` (all PCAC and core skills)
  - Copy `AGENTS.md`, `CLAUDE.md` from the appropriate template or the current project root
  - Copy `.gitignore` from the appropriate template (contains gald3r-standard ignore section with section markers)
  - Copy `opencode.json` from the appropriate template (enables OpenCode IDE rule discovery)

**In both cases**, create `.gald3r/.identity`:
```
project_id=<generate new UUID>
project_name=<new_project_name>
user_id=<copy from current project's .identity>
user_name=<copy from current project's .identity>
gald3r_version=<copy from current project's .identity>
vault_location=<copy from current project's .identity>
repos_location=<copy from current project's .identity>
```

**In both cases**, also ensure the following root files are present (copy from template if not already handled above):
- `.gitignore` — gald3r-standard ignore patterns; uses section markers (`# <!-- gald3r GITIGNORE SECTION -->`) so user additions survive upgrades. Prevents `.gald3r/`, `.env`, `__pycache__`, and other generated files from being committed.
- `opencode.json` — enables OpenCode IDE to discover rules. Without it, the spawned project is invisible to OpenCode.

### Step 4 — Seed with passed description

Create `.gald3r/PROJECT.md` using the `g-skl-project` scaffold, with:
- **Mission**: `--description` value (or `"[PENDING — set mission before starting work]"` if not provided)
- **Project Linking** section pre-populated with the relationship to the spawning project
- **Origin note**: `> Spawned from: <current_project_name> on <YYYY-MM-DD>`

Create `.gald3r/PLAN.md`, `TASKS.md`, `FEATURES.md`, `BUGS.md`, `SUBSYSTEMS.md`, `IDEA_BOARD.md`,
`CONSTRAINTS.md` from slim templates (empty, numbered headers only).

### Step 4.5 - Propagate parent constraints (scope-aware)

After seeding `CONSTRAINTS.md`, offer to propagate applicable constraints from the current (parent/source) project:

1. Read `<current_project>/.gald3r/CONSTRAINTS.md` -- collect all constraints where `**Scope**:` is `inheritable` or `ecosystem-wide`
2. Display the list:
   ```
   Found N constraints eligible for propagation to <new_project_name>:
     C-001 [file-first-vault] (ecosystem-wide)
     C-007 [no-secrets] (ecosystem-wide)
     C-003 [path-via-identity] (inheritable)
     ...
   Propagate these N constraints to the child? [y/n/select]
   ```
3. If **y**: copy all listed constraints into child's `CONSTRAINTS.md` with:
   - Same definition block (Status, Established, Scope, Rationale, Applies to, etc.)
   - Add field: `**Inherited from**: <current_project_name> (propagated <YYYY-MM-DD>)`
   - Note in child's CONSTRAINTS.md Change Log: `| <date> | C-NNN | Inherited from <source> via spawn | <source_project> |`
4. If **select**: present numbered list, user picks which to include
5. If **n**: skip constraint propagation entirely
6. `ecosystem-wide` constraints are pre-selected by default; `inheritable` are offered but not pre-selected

**Note**: Constraints with `**Inherited from**:` are read-only in the child -- agents should warn if asked to modify them locally.


### Step 5 — Transfer features (if --features provided)

**Source**: `<current_project>/<features_subfolder>/` (e.g. `.gald3r/features/gald3r_backend/`)
**Destination**: `<new_project>/.gald3r/features/`

```powershell
Copy-Item -Path "<source_features_path>\*" -Destination "<new_project>/.gald3r/features/" -Recurse -Force
```

- Copy ALL files/subfolders in the specified features path
- Do NOT delete source yet (Step 11 handles that, after confirmation)
- Update FEATURES.md in the new project: parse copied feat-NNN_*.md files, build the index table

Log in source project's `.gald3r/vault/log.md`:
```markdown
## <YYYY-MM-DD> — Spawn: features transferred to <new_project_name>
- source_path: <features_subfolder>
- dest_project: <new_project_name>
- file_count: N
- status: copied (originals kept pending confirmation)
```

### Step 6 — Transfer code (if --code provided)

```powershell
Copy-Item -Path "<source_code_path>" -Destination "<new_project>/<same_relative_subpath>" -Recurse -Force
```

- Mirror the directory structure (e.g., `src/payments/` → `<new_project>/src/payments/`)
- Do NOT delete source yet
- Log in vault/log.md

### Step 7 — Run gald3r-setup subsystem discovery in new project

Follow `g-skl-setup` Step 7 (Subsystem Discovery) scoped to the new project's contents:
- Scan code folders (if transferred)
- Scan features/ for subsystem hints
- Create `.gald3r/subsystems/` spec files
- Update `.gald3r/SUBSYSTEMS.md`

### Step 8 — Initialize PCAC linking in new project

Create `.gald3r/linking/link_topology.md` in the new project:

```yaml
---
project_id: "<new UUID>"
project_name: "<new_project_name>"
project_path: "<ecosystem_root>\<new_project_name>"
role: "<sibling | child | parent>"
description: "<--description value>"
parent: {}         # populated below if --child
children: []       # populated below if --parent
siblings: []       # populated below if --sibling
last_updated: "<YYYY-MM-DD>"
---
```

Set relationships:
- `--sibling`: add current project to `siblings[]`; set `role: sibling`
- `--child`: add current project to `parent:`; set `role: child`
- `--parent`: add current project to `children[]`; set `role: parent`

Create `.gald3r/linking/INBOX.md`:
```markdown
# INBOX — <new_project_name>

> Cross-project coordination inbox. Maintained by PCAC skills.
> Format: [OPEN] | [ACTIONED] | [CLOSED]

---

## [INFO] Project spawned from <current_project_name> — <YYYY-MM-DD>
**Source**: <current_project_name>
**Relationship**: <sibling | child | parent>
**Seeded with**: <description | features: N files | code: N folders>
**Next step**: Review .gald3r/PROJECT.md, curate features, and run @g-tasks to plan first sprint.
```

Create `.gald3r/linking/capabilities.md` using the template at `gald3r_template_full/.gald3r/linking/capabilities.md`:
- Replace `{project_slug}` and `{project_name}` with the actual new project name
- Replace `{YYYY-MM-DD}` with today's date
- If `--child` and explicit responsibilities were delegated at spawn time (via `--delegate-responsibility` flag or `$ARGUMENTS` description): add those delegated responsibilities to the `## Responsibilities` table with `status: planned`
- Prefix delegated responsibilities with `delegated_by: <current_project_slug>` in the Description field

### Step 9 — Update current project's topology

Update `<current_project>/.gald3r/linking/link_topology.md`:

- `--sibling`: add new project to `siblings[]`
- `--child`: add new project to `children[]`
- `--parent`: set new project as `parent:`, update `role: child`

Update `last_updated` to today.

Write `<current_project>/.gald3r/linking/peers/<new_project_name>.md`:
```markdown
# Peer: <new_project_name>
relationship: <sibling | child | parent>
project_path: <ecosystem_root>\<new_project_name>
project_id: <new UUID>
spawned_from_here: true
spawned_date: <YYYY-MM-DD>
```

### Step 10 — Initial git commit in new project

```powershell
cd "<new_project>/"
git add -A
git commit -m "feat: gald3r scaffold — spawned from <current_project_name> <YYYY-MM-DD>"
```

### Step 11 — Ask about source cleanup

```
New project <new_project_name> is ready at:
  <ecosystem_root>\<new_project_name>

If you transferred features: the originals are still at <source_features_path>.
Delete source features from <current_project_name>? [yes / no / keep for now]
```

If "yes":
- Delete source feature files/folder
- Update `<current_project>/.gald3r/FEATURES.md` to remove or stub the transferred features
- Add forwarding comment in FEATURES.md: `> [transferred to <new_project_name> — <YYYY-MM-DD>]`

If code was transferred and source delete confirmed:
- Delete source code folder
- Add forwarding stub at source path

### Step 12 — Final report

```
✅ SPAWN COMPLETE
  New project  : <new_project_name>
  Path         : <ecosystem_root>\<new_project_name>
  gald3r        : installed (<style>/<tier>)
  Features     : N files transferred (originals: kept | deleted)
  Code         : N folders transferred (originals: kept | deleted)
  Topology     : linked as <sibling | child | parent> of <current_project_name>
  Git          : initial commit created

Next steps:
  1. Open <new_project_name> in a new IDE window
  2. Review .gald3r/PROJECT.md — confirm mission and goals
  3. Curate transferred features (prioritize, merge, assign to subsystems)
  4. Run @g-tasks to plan first sprint
  5. (Optional) Run @g-pcac-order from <current_project_name> to push initial tasks down
```

---

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Folder already exists at target path | Stop: "Path already exists: <path>. Use a different name or delete the existing folder." |
| No gald3r in current project | Stop: "No .gald3r/.identity found. Run @g-setup first." |
| No PCAC in current project | Create `.gald3r/linking/` in current project; initialize topology; then proceed |
| --features path doesn't exist | Stop: "Features path not found: <path>" |
| --features path is empty | Warn: "No .md files found in <path>. Proceeding without feature transfer." |
| gald3r_install MCP available | Prefer calling `gald3r_install(project_path=..., use_v2=True)` in Step 3 over manual copy |
| Symlink detection fails | Default to "copy" style (safe fallback) |
| Git init fails | Warn but continue — git can be initialized manually |
| `.gitignore` not found in template | Write a minimal inline default with gald3r section markers: `.gald3r/`, `.env`, `__pycache__/`, `*.py[cod]`, `node_modules/`, `.DS_Store` |
| `opencode.json` not found in template | Write inline default: `{"$schema":"https://opencode.ai/config.json","instructions":["AGENTS.md","GUARDRAILS.md",".cursor/rules/*.mdc"]}` |

---

## Topology Relationship Guide

| Flag | New project role | Current project role becomes |
|------|-----------------|------------------------------|
| `--sibling` | sibling of current | adds new project to siblings[] |
| `--child` | child (current is parent) | adds new project to children[] |
| `--parent` | parent (current becomes child) | sets new project as parent |

---

## Notes on gald3r Install Detection

The skill should check in this order:
1. If `gald3r_install` MCP tool responds → use it (preferred)
2. If `gald3r_template_full/` exists in current project → use as copy source
3. If current project has `.cursor/rules/` symlinks → replicate symlink structure
4. Fallback: copy `.cursor/rules/` and `.claude/skills/` from the current project template root if path is known

The goal is that the spawned project has the same level of gald3r tooling as the project
that spawned it — no orphaned child left without proper skill coverage.