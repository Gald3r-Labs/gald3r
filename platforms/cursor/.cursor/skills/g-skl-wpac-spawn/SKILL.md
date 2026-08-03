---
name: g-skl-wpac-spawn
description: >
  Spawn a new gald3r project from the current project. Creates the new project folder
  in the same ecosystem root, installs gald3r (matching the current project's install
  type — symlinks or fresh template), seeds it with any passed description/features/code,
  runs gald3r-setup, and immediately links both projects via WPAC topology
  (--parent | --sibling | --child).
token_budget: medium
subsystem_memberships: [WORKSPACE_COORDINATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

> **Multi-agent framework (T1094):** Topology registration + Delegation — creates & seeds a child project.

# g-skl-wpac-spawn

**File Owner**: none (creates a new project; source project's topology is updated in place)

**Activate for**: "spawn a new project", "create a new child/sibling/parent project", "extract this into its own repo", "new project from features", `@g-wpac-spawn`

---

## When to Use

When a part of the current project has grown large enough to warrant its own separately
maintained repository, but it currently lives inside this project (as code, features,
specifications, or ideas). This skill orchestrates the full lifecycle:

1. Create the new project folder in the ecosystem root
2. Install gald3r (matching current project's install style)
3. Seed the new project with passed context (description, features, code, etc.)
4. Run gald3r-setup subsystem discovery in the new project
5. Register WPAC topology link in both projects

---

## Transport layer (WPAC-v2 — T1608)

Spawning is inherently LOCAL (folder creation, install, seeding) — all steps run as
written. The online part is the topology registration (step 5): after the local
topology link is written, when both projects carry a registered `project_id` UUID,
register the edge in the world_tree linking registry (T1625):

```
gald3r workspace outbox send --verb link \
    --project-uuid <subject_project_id> \
    --payload '{"target_project_id": "<target_project_id>", "relation": "<parent|sibling>"}'
```

(Subject/target/relation follow the spawned relationship — for `--child`, the NEW
project is the subject and this project the `parent` target; for `--sibling`, either
is subject with `relation: "sibling"`; mirror of `g-skl-wpac-claim`/`-adopt`.)

Branch on the verdict in code (g-rl-38): `ok` → registry edge recorded, and (T255)
`gald3r workspace outbox send --verb link` auto-refreshes the **D7 linking mirror**
(`.gald3r/linking/link_topology.md` / `link_registry.json`) itself, immediately, by
chaining a `gald3r workspace pull` after the edge is accepted — no separate manual
pull needed for this edge; `offline`/`error` → local (WPAC-v1) file topology is
authoritative, queued entry reconciled by `gald3r workspace outbox flush` on
reconnect; `auth_required` / `upgrade_required` → print the shim's hint/upgrade line
and continue file-only. A freshly spawned project usually has no server registration
yet — file-only is the expected first state; the linking-mirror skill (`g-skl-linking`,
T1610) reconciles it as soon as `link` is later sent successfully (or on any manual
`gald3r workspace pull`). Verb surface (name + arguments) unchanged. `wpac_transport`'s
`link` verb (server edge writer) and `linking_mirror` (D7 linking-mirror writer, reused
automatically above) own disjoint state and are not duplicates of each other (T255).
**T261**: "linking mirror" always means this D7 surface; the legacy WPAC-v1 file
topology this skill writes by hand (Steps 8-9 below) is never called "a mirror".

---

## Command Syntax

```
@g-wpac-spawn <new_project_name> --sibling [options]
@g-wpac-spawn <new_project_name> --child [options]
@g-wpac-spawn <new_project_name> --parent [options]

Options:
  --description "..."          One-line mission statement for the new project
  --features <subfolder>       Path (relative or absolute) to a features/ subfolder to transfer
  --code <path>                Path to code folder(s) to copy into the new project
  --template slim|full|adv     Which gald3r template tier to install (default: matches current)
  --dry-run                    Show what would be created without touching anything
```

**Examples**:
```
@g-wpac-spawn example_app --sibling --description "Single-user Docker backend for gald3r" --features .gald3r/features/gald3r_backend
@g-wpac-spawn gald3r_payments --child --description "Payment processing subsystem" --code src/payments/
@g-wpac-spawn gald3r_platform --parent --description "Platform coordination layer"
```

---

## Pre-Flight Checks

Before doing anything, validate:

```
□ Current project has .gald3r/.identity (gald3r is installed here)
□ Current project has .gald3r/linking/link_topology.md (WPAC is initialized) —
  the real, documented location (BUG-224); NOT .gald3r/workspace/topology.md,
  which does not exist anywhere in the real template or in any reading code
□ new_project_name does not already exist in the ecosystem root
□ If --features: the specified path exists and contains at least one .md file
□ If --code: the specified path exists
□ relationship (--sibling/--child/--parent) is specified
□ Template source has .gitignore and opencode.json (warn if missing, use inline defaults)
□ Workspace-Control member-repo guard (BUG-021 / Task 213 / g-rl-36)
```

### Workspace-Control Member-Repo Guard

`g-wpac-spawn` creates a brand-new standalone gald3r project (with full control plane and WPAC topology link) at `<ecosystem_root>/<new_project_name>`. WPAC spawn is **not** the Workspace-Control member path — Workspace-Control members hold a slim marker-only `.gald3r/` (`.identity` + `PROJECT.md` only), while WPAC spawn intentionally seeds the full control plane.

If the destination falls inside (or matches) a Workspace-Control controlled_member or migration_source registered in any ancestor `workspace_manifest.yaml`, this would violate the marker-only invariant documented in `g-rl-36` (BUG-021 / Task 213).

Run the guard helper against the planned new-project path **before Step 2** materializes any `.gald3r/` directory:

```powershell
$newProjectPath = Join-Path $ecosystemRoot $new_project_name
gald3r workspace member guard --target-path $newProjectPath
```

- exit `0` — proceed (target is not a workspace member).
- exit `1` — **stop with `BLOCK wpac_spawn_member_repo_gald3r_guard_block`**. The target is a Workspace-Control member; WPAC spawn would seed the full control plane and violate the marker-only invariant. Direct the user to either:
  1. Spawn under a non-member parent path, OR
  2. Use `@g-wrkspc-spawn` for new empty workspace members (which uses `gald3r workspace member bootstrap` to create only `.identity` + `PROJECT.md`).
- exit `2` — stop with `BLOCK wpac_spawn_member_repo_gald3r_guard_error`. Resolve the manifest before retrying.

Installed projects ship the helper at `gald3r workspace member guard`.

If `--dry-run`: print a full preview and stop. Do not create anything. The guard is reported in dry-run preview but does not block dry-run output (only blocks apply).

If any non-dry-run check fails → stop and report with fix instructions.

### Member Role Confirmation (T1454)

Before Step 2 materializes any `.gald3r/` (and unless a `--role` was supplied or the session is non-interactive), confirm the new project's workspace role with the user:

```
This spawn will create a new project. Pick its role:

  [1] autonomous_child  (recommended for new project repos)
      Needs its own tasks, bugs, and full IDE setup?
      -> Independently workable; full .gald3r/ + full gald3r install.

  [2] controlled_member
      Read-only / source-only member managed entirely by the controller?
      -> Marker-only .gald3r/ (.identity + PROJECT.md). Use @g-wrkspc-spawn instead.

Default [1] autonomous_child. Choose [1/2]:
```

- The **default recommended answer is `autonomous_child`** — treat empty/Enter as `autonomous_child`. A `--child`/`--sibling`/`--parent` WPAC spawn is an `autonomous_child` by design and receives the full framework via the T1452 installer in Step 3.
- If the user picks **`controlled_member`**, stop and direct them to `@g-wrkspc-spawn` (Workspace-Control SPAWN), which creates a marker-only member instead of a full WPAC project.
- For **non-interactive / unattended** runs, do not prompt: proceed as `autonomous_child` (the documented WPAC-spawn default) and note the auto-selection in the final report.

---

## Steps

### Step 0 — Determine ecosystem root

```
Read: .gald3r/.identity → project_path
Ecosystem root = parent directory of project_path
Example: <workspace>\current_project → root is <workspace>\
New project path = <ecosystem_root>\<new_project_name>
```

### Step 1 — Detect current project's gald3r install style

```
Check if .cursor/rules/ contains symlinks → PowerShell: (Get-Item .cursor/rules/g-rl-00-always.mdc).LinkType
  "SymbolicLink" → style = "symlink"
  $null or "" → style = "copy"

Check which template tier:
  If <ECOSYSTEM_ROOT>/<template_full>/.gald3r/ exists → tier = "full"
  Else read .gald3r/.identity for gald3r_version hints or assume "slim"
```

Store: `$install_style`, `$template_tier` (overridden by `--template` if provided)

### Step 2 — Create new project folder structure

**Do NOT hand-list `.gald3r/` subdirectories one-by-one — that is exactly what
caused BUG-224** (a hand-built subset silently omitted `config/`, `muninn/`, `prds/`,
`themes/`, `vault/`, `specifications_collection/`, and most of the top-level files,
leaving a spawn that looked scaffolded but was missing most of the real control
plane). Copy the **entire** canonical `.gald3r/` tree from the reference template
instead — it is the single source of truth for "everything that's supposed to be in
there":

```powershell
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>"
Copy-Item -Path "<ECOSYSTEM_ROOT>\gald3r_templates_workspace\gald3r\project_template\.gald3r" `
          -Destination "<ecosystem_root>\<new_project_name>\.gald3r" -Recurse -Force
New-Item -ItemType Directory -Path "<ecosystem_root>\<new_project_name>\docs"
```

If the reference template path above isn't present on this machine, fall back to
copying from the current (spawning) project's own already-verified `.gald3r/` tree
(`<current_project>\.gald3r`) instead of hand-listing directories — same principle:
copy the whole tree, then let Steps 4-9 below fill in real values over the
placeholders. Either way, verify after copying that all of these top-level entries
exist (this is the full canonical shape — cross-check with `ls -Force .gald3r/` if in
doubt, don't assume): `bugs/`, `config/`, `features/`, `linking/`, `muninn/`, `prds/`,
`reports/`, `specifications_collection/`, `subsystems/`, `tasks/`, `themes/`, `vault/`,
`.gitignore`, `.identity`, `BUGS.md`, `COMBINED_READINESS.md`, `CONSTRAINTS.md`,
`DECISIONS.md`, `FEATURES.md`, `IDEA_BOARD.md`, `learned-facts.md`, `PLAN.md`,
`PLATFORM_CAPABILITY_MATRIX.md`, `PRDS.md`, `PRODUCT_SYSTEMS.md`, `PROJECT.md`,
`RELEASES.md`, `SUBSYSTEMS.md`, `TASKS.md`, `TEST_PLANS.md`, `vocab.md`.

Regenerate a fresh `.identity` afterward (Step 4 below) — do not keep the template's
copy verbatim, it has no real `project_id`/`user_id`.

Create git repo:
```powershell
cd "<ecosystem_root>\<new_project_name>"
git init
```

### Step 3 — Install gald3r (matching style)

**PREFERRED — run the full installer (T1452).** Do NOT hand-build the project's gald3r layout
file-by-file. A `--child`/`--sibling` spawn is an `autonomous_child` (g-rl-36) and MUST receive
the **complete** framework: `.claude/`, `.cursor/` (skills, agents, commands, rules, hooks)
and the root docs (`CLAUDE.md`, `AGENTS.md`, `WORKFLOW.md`, `GUARDRAILS.md`,
`GALD3R-PROMPT.md`, `GALD3R-MIGRATION.md`, `scripts/`). Hand-writing only `.gald3r/` leaves the
child without skills/agents/rules and is the defect T1452 fixes.

Run (or instruct the user to run) the installer against the new project path:

```powershell
# $newProjectPath = <ecosystem_root>\<new_project_name>
# Use the same platforms the parent project uses (read from the parent's installed IDE dirs).
gald3r platform install cursor --into $newProjectPath --generated
gald3r platform install claude --into $newProjectPath --generated
```

- `gald3r platform install <platform> --into <dir> --generated` is a self-contained `gald3r`
  engine CLI verb (T177) — it reads the neutral component set embedded in the engine binary and
  writes that platform's overlay straight into `--into`, no `<template_adv>` checkout required.
- Ensure the `gald3r` engine binary is installed first (`g-install-agent`, or verify with
  `gald3r --version`); run the install verb once per platform the parent project uses.
- Prefer the `gald3r_install` MCP tool when available (see Edge Cases); otherwise use the installer above.
- After the installer completes, continue with the `.gald3r/.identity` and topology steps below.
- **Verify the install (T1452 AC)** — before reporting success confirm the IDE overlay deployed:
  ```powershell
  @(".claude", ".cursor") |
    ForEach-Object { Test-Path (Join-Path $newProjectPath $_) }
  ```
  If either is missing, re-run the installer (or fall back to the manual copy below) before continuing.
  NOTE: `gald3r platform install` writes the IDE overlay (`.claude/`, `.cursor/` + their
  `commands/`, `rules/`, `skills/`, `agents/`, `hooks/` subdirs) AND that platform's root docs
  (a subset of `CLAUDE.md`/`AGENTS.md`/`GALD3R.md`, per-platform filtering, T357/BUG-341/T408).
  `.gald3r_sys/` has been retired from the system entirely (D016/D017/T335/T274) — it is not part
  of the deploy contract and no verb ever writes it; that is intentional, not a gap (BUG-189).

The manual copy fallback below is **only** for environments where the installer and the MCP tool are
both unavailable.

**If style = "symlink"**:
  - Determine the symlink target root (usually the current project's template path)
  - Create `.cursor/rules/` symlinks pointing to `<ECOSYSTEM_ROOT>/<template_full>/.cursor/rules/`
  - Create `.claude/` symlinks or copies as appropriate
  - Create `.cursor/skills/` symlinks pointing to template skills

**If style = "copy"** (default safe path):
  - Read the current project `.gald3r/.identity` → locate `<ECOSYSTEM_ROOT>/<template_slim>` or `<ECOSYSTEM_ROOT>/<template_full>` path
  - Copy `.cursor/rules/` from the appropriate template tier
  - Copy `.claude/skills/` from the current project `.claude/skills/` (all WPAC and core skills)
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

### Step 8 — Initialize WPAC linking in new project (ADR-011 unified spawn)

**Canonical location is `.gald3r/linking/`, NOT `.gald3r/workspace/`** (BUG-224 —
this step previously pointed at a `workspace/` path that does not exist anywhere in
the real template or in any reading code; the correct, actually-referenced-elsewhere
location is `.gald3r/linking/`, matching `linking/README.md`'s documented schema and
what `gald3r_core_dev`'s own `.gald3r/linking/` already uses).

The full canonical `.gald3r/` shape (see Step 2 note) already ships an unfilled
`linking/link_topology.md`, `linking/INBOX.md`, `linking/capabilities.md`,
`linking/_peers/.gitkeep`, `linking/workspace_manifest.yaml`, `linking/sent_orders/`
from the template copy — this step fills in the real values.

Edit `.gald3r/linking/link_topology.md` in the new project (replace the placeholder
frontmatter, keep the file — do not create a second file):

```yaml
---
project_id: "<new UUID>"
project_name: "<new_project_name>"
project_type: "<development | templates | website | business-plan | content>"
project_path: "<ecosystem_root>\<new_project_name>"
role: "<sibling | child | parent>"
description: "<--description value>"
parent: null       # populated below if --child
children: []       # populated below if --parent
siblings: []       # populated below if --sibling
last_updated: "<YYYY-MM-DD>"
---
```

Set relationships:
- `--sibling`: add current project to `siblings[]`; set `role: sibling`
- `--child`: add current project to `parent:`; set `role: child`
- `--parent`: add current project to `children[]`; set `role: parent`

**Register in controller `workspace_manifest.yaml` (merged from g-wrkspc-spawn, ADR-011)**:

If the current project (or any ancestor) has a `workspace_manifest.yaml` in `.gald3r/linking/`:
1. Add a new entry under `repositories:` for the new project
2. Set `project_type:` per `--type` parameter
3. Set `wpac_role: child | sibling` per `--child | --sibling` flag
4. Set `lifecycle_status: active`
5. Run `gald3r workspace member bootstrap --member-path <new_path> --member-id <new_project_name> --apply`
   - This creates `.gald3r/.identity` + `.gald3r/PROJECT.md` as the marker pair
6. Update `controlled_members:` list in the manifest

This replaces the need to call `@g-wrkspc-member-add` separately after spawn.

Edit `.gald3r/linking/INBOX.md` (already shipped by the template copy — append, do
not overwrite the section headers) — add under `## [SYNC]`:
```markdown
- [x] [INFO] <YYYY-MM-DD> — Project spawned from <current_project_name> as a
  <sibling | child | parent>. Seeded with: <description | features: N files | code: N folders>.
  Next step: review .gald3r/PROJECT.md, curate features, run @g-tasks to plan first sprint.
  → resolved <YYYY-MM-DD>
```

Fill in `.gald3r/linking/capabilities.md` (already shipped by the template copy —
edit in place, do not create a new file):
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

Write `<current_project>/.gald3r/linking/_peers/<new_project_name>.md`:
```markdown
---
project_id: "<new UUID>"
project_name: "<new_project_name>"
project_path: "<ecosystem_root>\<new_project_name>"
role: "<sibling | child | parent>"
description: "<--description value>"
parent: null
children: []
siblings: []
last_updated: "<YYYY-MM-DD>"
---

# Peer Copy: <new_project_name>

Local advisory copy of <new_project_name>'s `linking/link_topology.md`. Refresh with
`@g-wpac-sync`.
```

Add the mirrored `[SYNC]` entry to `<current_project>/.gald3r/linking/INBOX.md` as well
(same format as the new project's INBOX entry above, from this project's perspective).

### Step 9.5 — Completion Gate (mandatory, BUG-223)

**Do not run Step 10 until every check below passes.** BUG-223 was filed after a spawn
run committed at Step 10 having only ever executed Steps 0-3 (folder + minimal
`.gald3r/` scaffold + IDE overlay) — the commit message made an incomplete child look
finished. This gate exists so that never happens silently again.

**Run the deterministic check (T360) — do not hand-verify the checklist alone.** The
checklist below is exactly what `gald3r workspace member verify-spawn` checks
programmatically; running it replaces trusting your own read of the folder tree with
a real pass/fail:

```powershell
gald3r workspace member verify-spawn --target "<new_project_path>" --source "<current_project_path>"
```

Exit code `0` means every check passed — proceed to Step 10. A non-zero exit prints
every missing item by name (add `--json` for machine-readable output); fix each one
and re-run before proceeding. `--source` is optional and enables the Step 9 reciprocal
check against the current project's own topology files; omit it only if the current
project's path is unavailable to the verb (e.g. a different filesystem). The manual
checklist below documents exactly what the verb verifies, for the rare case the CLI
itself is unavailable.

Verify, in the new project (`<new_project>/.gald3r/` unless noted):

```
□ PROJECT.md contains the real mission/description (NOT the generic scaffold
  placeholder "_(fill in the project mission)_") — Step 4
□ PLAN.md, FEATURES.md, SUBSYSTEMS.md, IDEA_BOARD.md, CONSTRAINTS.md all exist — Step 4
□ linking/link_topology.md exists and correctly declares parent/children/siblings per
  the requested relationship (NOT the unfilled template placeholder) — Step 8
□ linking/INBOX.md and linking/capabilities.md are filled in (not left as template
  placeholders) — Step 8
□ <current_project>/.gald3r/linking/link_topology.md was updated to add the new
  project (siblings[]/children[]/parent:) — Step 9
□ <current_project>/.gald3r/linking/_peers/<new_project_name>.md was written — Step 9
```

If ANY item is unchecked:
- Do **not** proceed to Step 10.
- Go back and run the missing step(s) now — do not skip ahead because the folder
  structure "looks done."
- If you cannot complete a step in this session (context limit, tool failure, user
  interrupt), STOP and report exactly which steps are done vs. missing. Do NOT commit
  a partial scaffold with the Step 10 message below — that message asserts the spawn
  is complete. If a commit is needed to save partial progress, use
  `chore(gald3r): partial scaffold — spawn incomplete, see checklist` instead, and
  leave a note in the new project's `docs/` (or session summary) listing exactly which
  of the checks above are still open.

### Step 10 — Initial git commit in new project

Only reachable once every Step 9.5 checkbox is checked.

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
  Framework    : IDE overlay verified (.claude/, .cursor/ present; platform install also writes that platform's root docs, T357; .gald3r_sys/ permanently retired from the deploy contract, not produced by design)
  Git          : initial commit created

Next steps:
  1. Open <new_project_name> in a new IDE window
  2. Review .gald3r/PROJECT.md — confirm mission and goals
  3. Curate transferred features (prioritize, merge, assign to subsystems)
  4. Run @g-tasks to plan first sprint
  5. (Optional) Run @g-wpac-order from <current_project_name> to push initial tasks down
```

---

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Folder already exists at target path | Stop: "Path already exists: <path>. Use a different name or delete the existing folder." |
| No gald3r in current project | Stop: "No .gald3r/.identity found. Run @g-setup first." |
| No WPAC in current project | Ensure `.gald3r/linking/` exists in the current project (copy from the canonical template per Step 2 if missing) and initialize `link_topology.md`; then proceed. **Not** `.gald3r/workspace/` (BUG-224 — that path does not exist anywhere in the real template or in any reading code). |
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
2. If `<ECOSYSTEM_ROOT>/<template_full>` exists → use as copy source
3. If current project has `.cursor/rules/` symlinks → replicate symlink structure
4. Fallback: copy `.cursor/rules/` and `.claude/skills/` from the current project template root if path is known

The goal is that the spawned project has the same level of gald3r tooling as the project
that spawned it — no orphaned child left without proper skill coverage.