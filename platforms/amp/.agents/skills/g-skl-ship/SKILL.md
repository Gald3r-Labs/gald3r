---
name: g-skl-ship
description: >
  Semantic versioning and release management for gald3r projects.
  Promotes CHANGELOG [Unreleased] to a versioned release, bumps VERSION,
  updates README badge, creates git tag, and optionally publishes a GitHub release.
  Also handles incremental CHANGELOG entries during development.
version: 1.0.0
task: T1210
token_budget: medium
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

# g-skl-ship — Release Management Skill

## When to Use

- User says `@g-ship`, `ship it`, `release`, `bump version`, `publish`
- At task completion when a CHANGELOG [Unreleased] entry is needed
- At bug fix closure when a `### Fixed` entry is needed
- When `@g-git-push` detects a non-empty [Unreleased] section

---

## Boundaries — What This Skill NEVER Touches

| File | Owner | Update path |
|------|-------|-------------|
| `VERSION` | **This skill** — user's project version | `@g-ship patch/minor/major` |
| `CHANGELOG.md` | **This skill** — user's release notes | `@g-ship` / `@g-go-code` task completion |
| `README.md` badge | **This skill** — version badge only | `@g-ship` |
| `.gald3r/.identity` `gald3r_version=` | **NEVER this skill** | `@g-update` only |

**`.gald3r/.identity gald3r_version=` is the gald3r FRAMEWORK version** — it records which version of gald3r is installed in the project. It is set by `gald3r_install` at first install and updated by `@g-update` when the user upgrades gald3r. It has nothing to do with the user's product version.

**Never suggest, add, or imply that `@g-ship` should touch `.gald3r/.identity`.** A user shipping their SaaS app `v3.0` must not corrupt their gald3r framework version record.

---

## Semver Definitions

| Digit | Trigger | Decision rule |
|---|---|---|
| **MAJOR** (X.0.0) | Breaking changes, complete reframe, new architecture | Users must change how they work after upgrading |
| **MINOR** (0.X.0) | New features, additive, nothing existing breaks | New skill/command/subsystem added |
| **PATCH** (0.0.X) | Bug fixes, small extensions, doc-only updates | No new capabilities, just corrections |

---

## Operations

### BUMP — Ship a release

Invoked by `@g-ship [major|minor|patch]`.

**Steps:**
1. Read current version from `VERSION` file (fallback: latest `## [X.Y.Z]` header in CHANGELOG.md)
2. Calculate new version based on bump type
3. Show the `[Unreleased]` section preview and new version to user — confirm before proceeding
4. Run `.claude/skills/g-skl-release/scripts/gald3r_semver.py -BumpType <type> -Theme "<theme>" -Apply`
   - Promotes `## [Unreleased]` → `## [X.Y.Z] - YYYY-MM-DD (Theme)`
   - Writes new empty `## [Unreleased]` at top
   - Bumps `VERSION` file
   - Updates README badge if version-X.Y-green pattern found
   - Creates focused commit: `release: vX.Y.Z -- Theme`
   - Creates annotated git tag: `vX.Y.Z`
5. Ask: "Push to remote? (yes/no)"
   - If yes: `git push origin main --tags`
6. Ask: "Create GitHub release? (yes/no)"
   - If yes: extract the new `[X.Y.Z]` section from CHANGELOG.md, pass to `gh release create`

**PowerShell (agent calls this):**
```powershell
python scripts/gald3r_semver.py -BumpType patch -Theme "Bug Fix Sprint" -Apply
git push origin main --tags
gh release create vX.Y.Z --title "vX.Y.Z -- Bug Fix Sprint" --notes-file <temp_notes_file>
```

**If `gald3r_semver.py` is not found** (project doesn't have it yet):
- Perform the steps manually:
  1. Read CHANGELOG.md, identify current version
  2. Calculate new version
  3. Edit CHANGELOG.md: replace `## [Unreleased]` section header with `## [X.Y.Z] - YYYY-MM-DD`, insert new `## [Unreleased]` with empty subsections above it
  4. Write VERSION file
  5. Update README badge line
  6. `git add CHANGELOG.md VERSION README.md && git commit -m "release: vX.Y.Z"`
  7. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`

---

### POST-RELEASE — Schema migration sweep (T1441)

Runs as a post-release phase **after the git tag is created (BUMP step 7) and before the
GitHub release is published (BUMP step 6's `gh release create`)**. When a release ships
schema changes (new required fields, deprecated/removed fields), existing `.gald3r/` files
in member projects must be migrated forward so projects are never left partially upgraded.

**Steps:**

1. **Emit the schema-migration notice** (always — even when no schema change shipped, the
   notice is harmless and idempotent):
   ```
   This release may include schema changes. To migrate existing projects forward, run:
     platform_parity_sync.ps1 -MigrateSchemas -Apply
   (dry-run first: platform_parity_sync.ps1 -MigrateSchemas)
   ```

2. **For a gald3r framework release** (this repo is `<gald3r_source>` and member repos
   are accessible on disk), OPTIONALLY auto-run the migration on all registered workspace
   members. Dry-run first, then apply on confirmation:
   ```powershell
   # Dry-run across all members (report only)
   .\custom_scripts\platform_parity_sync.ps1 -MigrateSchemas

   # Apply after reviewing the dry-run
   .\custom_scripts\platform_parity_sync.ps1 -MigrateSchemas -Apply

   # Single member only
   .\custom_scripts\platform_parity_sync.ps1 -MigrateSchemas -Target <gald3r_source> -Apply
   ```
   The migration engine (`.gald3r_sys/scripts/migrate_schemas.ps1`) never deletes fields:
   deprecated fields become `deprecated_<name>`, removed fields become `legacy_<name>`, and
   un-populatable added fields get a `TODO:` marker. It is idempotent — re-running is a no-op.

3. **For a user-project release** (not the gald3r framework itself), emit the notice only —
   do NOT auto-run migration. The user runs `@g-medic` or the command above when ready.

**Ordering guarantee:** `-MigrateSchemas` must run after `-SyncGaldSys -Sync` so the new
schema files exist on each member before migration reads them.

---

### CHANGELOG-ENTRY — Add to [Unreleased] during development

Called automatically at task completion and bug fix closure. Can also be called directly.

**When called from task completion:**
```
User-facing task completed → Ask: "Add CHANGELOG entry? [yes/skip]"
If yes → determine category (Added/Changed/Removed) → write one-liner to [Unreleased]
```

**When called from bug fix:**
```
Bug closed → Always write: "- Fixed: {bug title}" under ### Fixed in [Unreleased]
```

**Format for [Unreleased] entries:**
```markdown
## [Unreleased]

### Added
- Brief user-facing description of new capability

### Changed
- What changed and what it replaces/improves

### Fixed
- Brief description of what was broken and now works

### Removed
- What was deprecated or deleted
```

**Rules:**
- One line per entry (no internal task IDs in user-project CHANGELOGs)
- Past tense: "Added X", "Fixed Y", "Changed Z"
- User-facing language — not implementation details
- Skip entries for: purely internal refactors, task file updates, .gald3r/ housekeeping

**Writing the entry (agent steps) — CRITICAL: never overwrite the whole file:**

> **CHANGELOG SAFETY RULE**: CHANGELOG.md must only grow. Never use the `Write` tool on CHANGELOG.md.
> Always use `StrReplace` (targeted section edit) or the PowerShell append below.
> Reading with a line limit then writing back = silent truncation of everything past the limit.

**Option A — PowerShell append (preferred, no truncation risk):**
```powershell
# Append under ### Fixed in [Unreleased]
$cl = Get-Content CHANGELOG.md -Raw
$entry = "- Fixed: Brief description of what was corrected."
# Insert after "### Fixed" inside [Unreleased] (before next ### or ## heading)
$cl = $cl -replace "(## \[Unreleased\][\s\S]*?### Fixed\n)", "`$1$entry`n"
Set-Content CHANGELOG.md $cl -NoNewline
```

**Option B — StrReplace (safe for targeted edits):**
Use the `StrReplace` tool to replace the target subsection with itself + the new bullet.
Include at least 3 lines of context before and after to ensure uniqueness.
Never include more than the targeted subsection — do NOT assemble the full file in memory.

**Steps:**
1. Read only enough context to identify the `### Fixed` (or other subsection) location
2. Use `StrReplace` to insert the new bullet after the subsection header
3. Verify the bullet appears correctly
4. Done — rest of file is untouched

---

### STATUS — Show current release state

Show:
- Current version (from VERSION file or CHANGELOG)
- Contents of [Unreleased] section
- Latest git tag
- Whether working tree is clean
- Whether `gh` CLI is available for GitHub releases

```powershell
python scripts/gald3r_semver.py -Status  # (not implemented yet — do manually)

# Manual approach:
$ver = Get-Content VERSION 2>$null; Write-Host "Version: $ver"
git describe --tags --abbrev=0
git log --oneline -5
```

---

## CHANGELOG.md Structure (Required)

The file must have this structure for the skill to work correctly:

```markdown
# Changelog

All notable changes to [project] are documented here.
Format follows Keep a Changelog.

---

## [Unreleased]

### Added
### Changed
### Fixed
### Removed

---

## [1.2.0] - 2026-05-16 (Theme Name)

### Added
- Feature X

---

## [1.1.0] - 2026-04-14
...
```

**If CHANGELOG.md doesn't exist:** Create it with the above structure and `## [0.0.0] - today` as the baseline, then proceed.

**If VERSION file doesn't exist:** Create it with `0.1.0` (or ask user for starting version).

---

## GitHub Release Notes

Release notes come directly from the CHANGELOG section — no separate file needed.

```powershell
# Extract section for gh release create
$lines = Get-Content CHANGELOG.md
$inSection = $false; $notes = @()
foreach ($line in $lines) {
    if ($line -match "^\#\# \[1\.2\.0\]") { $inSection = $true; continue }
    if ($inSection -and $line -match "^\#\# \[") { break }
    if ($inSection) { $notes += $line }
}
$notes | Set-Content "$env:TEMP\release_notes.md"
gh release create v1.2.0 --title "v1.2.0" --notes-file "$env:TEMP\release_notes.md"
```

---

## Files Managed

| File | Action |
|---|---|
| `CHANGELOG.md` | BUMP: promotes [Unreleased]; CHANGELOG-ENTRY: appends to [Unreleased] |
| `VERSION` | BUMP: writes new version number; created if absent |
| `README.md` | BUMP: updates `version-X.Y-green` badge pattern if found |

---

## Choosing a Changelog Mode (T1305 / T1306)

gald3r supports **two** changelog modes. Either way, gald3r tasks/commits always use Conventional Commit prefixes (`feat`/`fix`/`docs`/…) — that does not change.

### 1. Manual mode (default)

The implementing agent appends entries to `CHANGELOG.md` `[Unreleased]` per `g-rl-26` (via this skill's CHANGELOG-ENTRY operation); `@g-ship` BUMP promotes `[Unreleased]` to a versioned section. No GitHub Action, works fully offline. **This is the default and the behavior when no Release Please workflow is installed.**

### 2. Auto mode (Release Please, T1305)

Install the opt-in workflow + config:

```bash
cp .gald3r_sys/templates/github/workflows/release-please.yml .github/workflows/
cp .gald3r_sys/templates/release-please-config.json ./release-please-config.json
echo '{".": "0.0.0"}' > .release-please-manifest.json   # set to current version
```

On each push to `main`, Release Please opens/updates a **release PR** that accumulates `CHANGELOG.md` entries (Conventional Commit → Keep-a-Changelog sections, matching gald3r's format) and the version bump. Merging the release PR cuts the release + tag.

### Decision matrix

| Profile | Recommended mode |
|---|---|
| Solo dev / offline | **Manual** — no CI dependency, full control |
| Small team | Manual or Auto — Auto reduces "who bumped the version?" friction |
| OSS project | **Auto** — contributors' Conventional Commits drive the changelog automatically |
| Enterprise / audited | **Auto** — release PR is a reviewable, audit-able artifact |

### Migrating between modes

- **Manual → Auto**: install the templates above; set the manifest to the current `VERSION`; stop hand-editing `[Unreleased]` (Release Please owns it from then on).
- **Auto → Manual**: remove `.github/workflows/release-please.yml`; resume CHANGELOG-ENTRY. Existing `## [x.y.z]` history is compatible with both modes.

Pick **one** mode per repo — do not run both against the same `CHANGELOG.md`.

---

## Related

- `@g-ship` — command that invokes this skill
- `@g-git-push` — prompts for version bump if [Unreleased] is non-empty
- `g-skl-tasks` COMPLETE — calls CHANGELOG-ENTRY for user-facing tasks
- `g-skl-bugs` FIX — calls CHANGELOG-ENTRY for bug closures
- `.claude/skills/g-skl-release/scripts/gald3r_semver.py` — Python engine (gald3r projects)
- `.claude/skills/g-skl-release/scripts/gald3r_release.py` — maintainer tool for gald3r's own 3-repo release
