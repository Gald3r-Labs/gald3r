# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    gald3r schema migration engine (T1441). Migrates .gald3r/ files forward to the
    current schema version when a new gald3r release introduces new required fields
    or renames deprecated/removed ones. Data is NEVER deleted.

.DESCRIPTION
    Reads .gald3r_sys/schemas/_registry.yaml, globs every file matching each registered
    pattern under <ProjectPath>/.gald3r/, reads each file's `schema_version` frontmatter
    (absent == v0), and runs a per-version migration chain up to the target version.

    DATA PRESERVATION GUARANTEE
      * No field is ever deleted.
      * `added[]` fields are populated via Population Rules (git creation date,
        registry/identity version, or a `TODO:` marker when unknowable).
      * `deprecated[]` fields are renamed to `deprecated_<name>` preserving the value.
      * `removed[]`    fields are renamed to `legacy_<name>`    preserving the value.
      * `deprecated_` / `legacy_` prefixed fields are excluded from validation.

    VERSION ORDERING
      * file_version  == target  -> skip (already current)
      * file_version  >  target  -> skip + log "newer than target" (NEVER downgrade)
      * file_version  <  target  -> run migration chain v(n+1)..target

    IDEMPOTENCY
      Running with -Apply twice produces zero additional changes: a file already at
      the target version is skipped on the second pass.

.PARAMETER ProjectPath
    Path to the project root that contains a .gald3r/ directory. Default: current dir.

.PARAMETER Apply
    Write changes to disk. Without this switch the engine runs in DRY-RUN mode and only
    reports what it WOULD migrate.

.PARAMETER TargetVersion
    Schema version to migrate TO (e.g. "v1"). Default: the highest current_version found
    in _registry.yaml for the matched schema, falling back to the registry-wide max.

.PARAMETER SchemasDir
    Explicit path to the .gald3r_sys/schemas/ directory. Default: auto-resolved relative
    to this script ($PSScriptRoot/../schemas), then <ProjectPath>/.gald3r_sys/schemas.

.PARAMETER RestoreMissing
    T1442: When a required single-file .gald3r/ artifact is MISSING in the target project,
    restore it from the canonical pristine template at .gald3r_sys/template_verification/ (resolved
    via $PSScriptRoot/../template_verification, falling back to <ProjectPath>/.gald3r_sys/template_verification).
    OFF by default -- migration behavior is unchanged unless this switch is passed. Honors -Apply:
    without -Apply the engine only reports what it WOULD restore. Only restores literal single-file
    patterns (e.g. .gald3r/TASKS.md) -- wildcard/recursive patterns (tasks/**) are never bulk-restored.

.EXAMPLE
    .\migrate_schemas.ps1
    # Dry-run against the current directory's .gald3r/ — prints "Files to migrate".

.EXAMPLE
    .\migrate_schemas.ps1 -ProjectPath <project-root> -Apply
    # Migrates all out-of-date files in <project-root>\.gald3r\ to the current schema version.

.NOTES
    ============================================================================
    gald3r_install MCP INTEGRATION CONTRACT (cross-repo follow-up — NOT IMPLEMENTED HERE)
    ============================================================================
    The `gald3r_install` MCP tool lives in the separate `example_app` repo and is
    OUT OF SCOPE for T1441. This block documents the intended integration so the
    follow-up task in example_app has an authoritative contract to implement against.

    When `gald3r_install` runs on a project that already has a .gald3r/ directory:
      1. DETECT  — invoke this engine in dry-run and parse its summary, OR read
                   schema_version from any .gald3r/ file. If any file's schema_version
                   is < the installing system's current schema version, migration is needed.
                       pwsh -File .gald3r_sys/scripts/migrate_schemas.ps1 -ProjectPath <proj>
                   Exit code 0 + a non-zero "Files to migrate" count => older schema present.
      2. PROMPT  — "This project uses an older gald3r schema (vN). Migrate to vM? [Y/n]"
      3. ON Y    — run with -Apply:
                       pwsh -File .gald3r_sys/scripts/migrate_schemas.ps1 -ProjectPath <proj> -Apply
      4. ON N    — skip; print "Run @g-medic or platform_parity_sync -MigrateSchemas later".
      5. FRESH   — no .gald3r/ present => no migration; all files are created at current version.

    The engine is the canonical implementation; gald3r_install must SHELL OUT to it,
    never re-implement the migration logic. g-medic L1 follows the same shell-out rule.
    ============================================================================
#>
[CmdletBinding()]
param(
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$Apply,
    [string]$TargetVersion = "",
    [string]$SchemasDir = "",
    [switch]$RestoreMissing
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Resolve-SchemasDir {
    param([string]$Explicit, [string]$Project, [string]$ScriptRoot)
    if ($Explicit -and (Test-Path $Explicit)) { return (Resolve-Path $Explicit).Path }
    # 1. Sibling of this script: <ScriptRoot>/../schemas
    $cand = Join-Path (Split-Path $ScriptRoot -Parent) "schemas"
    if (Test-Path $cand) { return (Resolve-Path $cand).Path }
    # 2. Project-local: <Project>/.gald3r_sys/schemas
    $cand = Join-Path $Project ".gald3r_sys\schemas"
    if (Test-Path $cand) { return (Resolve-Path $cand).Path }
    return $null
}

# T1442: Resolve the canonical pristine .gald3r/ template instance shipped under
# .gald3r_sys/template_verification/. Used by -RestoreMissing to restore absent files.
function Resolve-DotGald3rCanonical {
    param([string]$Project, [string]$ScriptRoot)
    # 1. Script-adjacent: <ScriptRoot>/../template_verification/.gald3r  (scripts/ is sibling of template_verification/)
    $cand = Join-Path (Split-Path $ScriptRoot -Parent) "template_verification\.gald3r"
    if (Test-Path $cand) { return (Resolve-Path $cand).Path }
    # 2. Project-local: <Project>/.gald3r_sys/template_verification/.gald3r
    $cand = Join-Path $Project ".gald3r_sys\template_verification\.gald3r"
    if (Test-Path $cand) { return (Resolve-Path $cand).Path }
    return $null
}

# Parse the schema -> version-step number. "v0" => 0, "v1" => 1, "registry-v1" ignored here.
function ConvertTo-VersionNumber {
    param([string]$Ver)
    if ([string]::IsNullOrWhiteSpace($Ver)) { return 0 }
    $m = [regex]::Match($Ver, 'v(\d+)\s*$')
    if ($m.Success) { return [int]$m.Groups[1].Value }
    return 0
}

# Lightweight YAML-frontmatter reader. Returns a hashtable:
#   FrontMatterLines (string[]), BodyLines (string[]), HasFrontMatter (bool),
#   Fields (ordered hashtable name->raw value string for simple `key: value` scalars).
function Read-FrontMatter {
    param([string]$Path)
    $raw = [System.IO.File]::ReadAllText($Path)
    $nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
    $lines = [regex]::Split($raw, '\r?\n')

    $result = [ordered]@{
        Newline          = $nl
        HasFrontMatter   = $false
        FmStart          = -1
        FmEnd            = -1
        Lines            = $lines
        Fields           = [ordered]@{}
    }

    # Frontmatter must start at the very first line with '---'
    if ($lines.Count -gt 0 -and $lines[0].Trim() -eq '---') {
        for ($i = 1; $i -lt $lines.Count; $i++) {
            if ($lines[$i].Trim() -eq '---') {
                $result.HasFrontMatter = $true
                $result.FmStart = 0
                $result.FmEnd = $i
                break
            }
        }
    }

    if ($result.HasFrontMatter) {
        for ($i = 1; $i -lt $result.FmEnd; $i++) {
            $line = $lines[$i]
            # only top-level `key: value` scalars (no indentation)
            $m = [regex]::Match($line, '^([A-Za-z0-9_]+):\s?(.*)$')
            if ($m.Success) {
                $result.Fields[$m.Groups[1].Value] = $m.Groups[2].Value
            }
        }
    }
    return $result
}

# Read a single top-level scalar from a YAML file (used for the schema files themselves).
function Get-YamlScalar {
    param([string]$Path, [string]$Key)
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        $m = [regex]::Match($line, "^${Key}:\s*[`"']?([^`"'#]+?)[`"']?\s*(#.*)?$")
        if ($m.Success) { return $m.Groups[1].Value.Trim() }
    }
    return $null
}

# Parse migration_notes.vN.{added,deprecated,removed} from a schema yaml file.
# Supports both compact list form  (added: [a, b, c])
# and block-field form             (deprecated:\n  - field: phase\n    rename_to: deprecated_phase)
function Get-MigrationStep {
    param([string]$SchemaFile, [int]$VersionNum)
    $result = @{ Added = @(); Deprecated = @(); Removed = @() }
    if (-not (Test-Path $SchemaFile)) { return $result }
    $lines = [System.IO.File]::ReadAllLines($SchemaFile)

    $inMigration = $false
    $inVersion = $false
    $curList = $null      # 'added' | 'deprecated' | 'removed'
    $verKey = "v$VersionNum"

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^migration_notes:\s*$') { $inMigration = $true; continue }
        if (-not $inMigration) { continue }
        # A new top-level key ends the migration_notes block.
        if ($line -match '^[A-Za-z0-9_]+:' -and $line -notmatch '^\s') { break }

        if ($line -match "^\s{2}${verKey}:\s*$") { $inVersion = $true; $curList = $null; continue }
        # Another v-key at the same indent ends our version block.
        if ($inVersion -and $line -match '^\s{2}v\d+:\s*$') { $inVersion = $false; $curList = $null; continue }
        if (-not $inVersion) { continue }

        # Compact list:  added: [a, b]
        $mInline = [regex]::Match($line, '^\s{4}(added|deprecated|removed):\s*\[(.*)\]\s*$')
        if ($mInline.Success) {
            $key = $mInline.Groups[1].Value
            $items = $mInline.Groups[2].Value.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
            foreach ($it in $items) {
                $result[(Get-Culture).TextInfo.ToTitleCase($key)] += @{ field = $it; rename_to = $null }
            }
            continue
        }
        # Block list header:  added:
        $mHdr = [regex]::Match($line, '^\s{4}(added|deprecated|removed):\s*$')
        if ($mHdr.Success) { $curList = $mHdr.Groups[1].Value; continue }

        # Block list item:  - field: phase
        if ($curList) {
            $mField = [regex]::Match($line, '^\s{6,}-\s*field:\s*(.+)$')
            if ($mField.Success) {
                $entry = @{ field = $mField.Groups[1].Value.Trim(); rename_to = $null }
                # peek ahead for rename_to within the same item
                for ($j = $i + 1; $j -lt $lines.Count; $j++) {
                    if ($lines[$j] -match '^\s{6,}-\s') { break }
                    if ($lines[$j] -match '^\s{4}\S') { break }
                    $mr = [regex]::Match($lines[$j], '^\s{6,}rename_to:\s*(.+)$')
                    if ($mr.Success) { $entry.rename_to = $mr.Groups[1].Value.Trim() }
                }
                $result[(Get-Culture).TextInfo.ToTitleCase($curList)] += $entry
                continue
            }
        }
    }
    return $result
}

# Git creation date for a file (first ADD commit). Falls back to $null.
function Get-GitCreationDate {
    param([string]$FilePath, [string]$RepoDir)
    try {
        $out = & git -C $RepoDir log --diff-filter=A --follow --format=%ad --date=short -- $FilePath 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) {
            $dates = @($out | Where-Object { $_ -match '^\d{4}-\d{2}-\d{2}$' })
            if ($dates.Count -gt 0) { return $dates[-1] }  # earliest ADD
        }
    } catch { }
    return $null
}

# ---------------------------------------------------------------------------
# T1485: Conditional grouped-format SUBSYSTEMS.md regenerator.
#
# When PRODUCT_SYSTEMS.md exists AND at least one subsystems/*.md spec carries a
# non-empty parent_system: field, rewrite SUBSYSTEMS.md so the Subsystem Index is
# grouped by L1 product system (one '## GROUP_NAME' section per defined_groups:
# entry, members listed beneath, in defined_groups: order; an Ungrouped section
# is appended last for specs missing parent_system:). The flat alphabetical index
# remains the fallback (T1458).
#
# SAFETY (key property): this is a strict NO-OP when no parent_system: data exists
# (the common template case). It NEVER writes SUBSYSTEMS.md in that situation.
# It only ever regenerates the '## Subsystem Index' section; the file's frontmatter,
# Overview, Taxonomy, Sub-Features, Integrations, and graph sections are preserved.
# ---------------------------------------------------------------------------

# Read defined_groups: as an ordered string list from PRODUCT_SYSTEMS.md frontmatter.
# Supports the block-list form (defined_groups:\n  - NAME). Returns @() when absent.
function Get-DefinedGroupsList {
    param([string]$ProductSystemsPath)
    $groups = [System.Collections.Generic.List[string]]::new()
    if (-not (Test-Path $ProductSystemsPath)) { return @() }
    $lines = [System.IO.File]::ReadAllLines($ProductSystemsPath)
    $inFm = $false; $inGroups = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($i -eq 0 -and $line.Trim() -eq '---') { $inFm = $true; continue }
        if ($inFm -and $line.Trim() -eq '---') { break }      # end of frontmatter
        if (-not $inFm) { continue }
        if ($line -match '^defined_groups:\s*$') { $inGroups = $true; continue }
        if ($inGroups) {
            $mItem = [regex]::Match($line, '^\s+-\s*(.+?)\s*$')
            if ($mItem.Success) { $groups.Add($mItem.Groups[1].Value.Trim().Trim('"').Trim("'")); continue }
            # A non-indented line (next top-level key) ends the list.
            if ($line -match '^\S') { $inGroups = $false }
        }
    }
    return $groups.ToArray()
}

# Derive a one-line purpose for a subsystem spec from the first non-empty line under
# its '## Responsibility' heading. Returns '' when none found.
function Get-SubsystemPurpose {
    param([string[]]$Lines)
    $inResp = $false
    foreach ($line in $Lines) {
        if ($line -match '^##\s+Responsibility\s*$') { $inResp = $true; continue }
        if ($inResp) {
            if ($line -match '^##\s') { break }              # next section
            $t = $line.Trim()
            if ($t -ne '' -and $t -notmatch '^\[.*\]$') { return $t }   # skip placeholder [..]
        }
    }
    return ''
}

# Regenerate SUBSYSTEMS.md grouped by L1 system. Returns a status string.
function Update-GroupedSubsystemsIndex {
    param(
        [string]$DotGald3r,
        [bool]$DoApply
    )
    $subsystemsMd = Join-Path $DotGald3r "SUBSYSTEMS.md"
    $productSystemsMd = Join-Path $DotGald3r "PRODUCT_SYSTEMS.md"
    $specsDir = Join-Path $DotGald3r "subsystems"

    # Guard 1: both index files must exist.
    if (-not (Test-Path $subsystemsMd -PathType Leaf)) { return 'no-subsystems-md' }
    if (-not (Test-Path $productSystemsMd -PathType Leaf)) { return 'no-product-systems-md' }
    if (-not (Test-Path $specsDir -PathType Container)) { return 'no-parent-system-data' }

    # Collect subsystem specs and their parent_system: tags.
    $specs = @(Get-ChildItem -Path $specsDir -Filter '*.md' -File -Recurse -ErrorAction SilentlyContinue)
    if ($specs.Count -eq 0) { return 'no-parent-system-data' }

    $byGroup = [ordered]@{}     # group -> list of @{ Name; Status; Rel; Purpose }
    $ungrouped = [System.Collections.Generic.List[object]]::new()
    $anyParent = $false

    foreach ($spec in $specs) {
        $fm = Read-FrontMatter -Path $spec.FullName
        if (-not $fm.HasFrontMatter) { continue }
        $name = if ($fm.Fields.Contains('name')) { $fm.Fields['name'].Trim().Trim('"').Trim("'") } else { [System.IO.Path]::GetFileNameWithoutExtension($spec.Name) }
        $status = if ($fm.Fields.Contains('status')) { $fm.Fields['status'].Trim().Trim('"').Trim("'") } else { 'active' }
        $rel = "subsystems/" + $spec.Name
        $purpose = Get-SubsystemPurpose -Lines $fm.Lines
        $parent = if ($fm.Fields.Contains('parent_system')) { $fm.Fields['parent_system'].Trim().Trim('"').Trim("'") } else { '' }
        $row = @{ Name = $name; Status = $status; Rel = $rel; Purpose = $purpose }
        if ([string]::IsNullOrWhiteSpace($parent)) {
            $ungrouped.Add($row)
        } else {
            $anyParent = $true
            if (-not $byGroup.Contains($parent)) { $byGroup[$parent] = [System.Collections.Generic.List[object]]::new() }
            $byGroup[$parent].Add($row)
        }
    }

    # Guard 2 (KEY NO-OP): if no spec carries parent_system:, do nothing at all.
    if (-not $anyParent) { return 'no-parent-system-data' }

    # Build the grouped Subsystem Index in defined_groups: order, then any extra
    # groups not in the registry, then an Ungrouped section last.
    $definedGroups = Get-DefinedGroupsList -ProductSystemsPath $productSystemsMd
    $orderedGroups = [System.Collections.Generic.List[string]]::new()
    foreach ($g in $definedGroups) { if ($byGroup.Contains($g) -and -not $orderedGroups.Contains($g)) { $orderedGroups.Add($g) } }
    foreach ($g in $byGroup.Keys) { if (-not $orderedGroups.Contains($g)) { $orderedGroups.Add($g) } }

    $idx = [System.Collections.Generic.List[string]]::new()
    $idx.Add("## Subsystem Index")
    $idx.Add("")
    $idx.Add("*(Grouped by L1 product system -- regenerated by migrate_schemas.ps1 from parent_system: tags.)*")
    foreach ($g in $orderedGroups) {
        $idx.Add("")
        $idx.Add("### $g")
        $idx.Add("")
        $idx.Add("| Subsystem | Status | Spec File | Purpose |")
        $idx.Add("|-----------|--------|-----------|---------|")
        foreach ($row in ($byGroup[$g] | Sort-Object { $_.Name })) {
            $idx.Add(("| {0} | {1} | ``{2}`` | {3} |" -f $row.Name, $row.Status, $row.Rel, $row.Purpose))
        }
    }
    if ($ungrouped.Count -gt 0) {
        $idx.Add("")
        $idx.Add("### Ungrouped (run @g-subsystem-audit)")
        $idx.Add("")
        $idx.Add("| Subsystem | Status | Spec File | Purpose |")
        $idx.Add("|-----------|--------|-----------|---------|")
        foreach ($row in ($ungrouped | Sort-Object { $_.Name })) {
            $idx.Add(("| {0} | {1} | ``{2}`` | {3} |" -f $row.Name, $row.Status, $row.Rel, $row.Purpose))
        }
    }

    # Splice the new index in place of the existing '## Subsystem Index' section.
    # The replaced span runs from the '## Subsystem Index' line up to (but not
    # including) the next '## ' heading, preserving everything around it.
    $fmMain = Read-FrontMatter -Path $subsystemsMd
    $allLines = [System.Collections.Generic.List[string]]::new()
    foreach ($l in $fmMain.Lines) { $allLines.Add($l) }

    $startIdx = -1; $endIdx = $allLines.Count
    for ($i = 0; $i -lt $allLines.Count; $i++) {
        if ($allLines[$i] -match '^##\s+Subsystem Index\s*$') { $startIdx = $i; break }
    }
    if ($startIdx -lt 0) { return 'index-section-missing' }
    for ($i = $startIdx + 1; $i -lt $allLines.Count; $i++) {
        if ($allLines[$i] -match '^##\s') { $endIdx = $i; break }
    }

    $rebuilt = [System.Collections.Generic.List[string]]::new()
    for ($i = 0; $i -lt $startIdx; $i++) { $rebuilt.Add($allLines[$i]) }
    foreach ($l in $idx) { $rebuilt.Add($l) }
    $rebuilt.Add("")
    for ($i = $endIdx; $i -lt $allLines.Count; $i++) { $rebuilt.Add($allLines[$i]) }

    if ($DoApply) {
        $outText = ($rebuilt -join $fmMain.Newline)
        [System.IO.File]::WriteAllText($subsystemsMd, $outText)
        return 'regenerated'
    }
    return 'to-regenerate'
}

# ---------------------------------------------------------------------------
# Resolve inputs
# ---------------------------------------------------------------------------

if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: ProjectPath not found: $ProjectPath" -ForegroundColor Red
    exit 2
}
$ProjectPath = (Resolve-Path $ProjectPath).Path
$dotGald3r = Join-Path $ProjectPath ".gald3r"

$schemasResolved = Resolve-SchemasDir -Explicit $SchemasDir -Project $ProjectPath -ScriptRoot $PSScriptRoot
if (-not $schemasResolved) {
    Write-Host "ERROR: schemas dir not found (looked relative to script and under $ProjectPath\.gald3r_sys\schemas)." -ForegroundColor Red
    exit 2
}
$registryPath = Join-Path $schemasResolved "_registry.yaml"
if (-not (Test-Path $registryPath)) {
    Write-Host "ERROR: _registry.yaml not found in $schemasResolved" -ForegroundColor Red
    exit 2
}

$systemRelVersion = Get-YamlScalar -Path $registryPath -Key "gald3r_rel_version"
if (-not $systemRelVersion) { $systemRelVersion = "unknown" }

# Identity gald3r_version (preferred for gald3r_rel_version population when present)
$identityPath = Join-Path $dotGald3r ".identity"
$identityRelVersion = $null
if (Test-Path $identityPath) {
    foreach ($line in [System.IO.File]::ReadAllLines($identityPath)) {
        $m = [regex]::Match($line, '^\s*gald3r_version\s*=\s*(.+)$')
        if ($m.Success) { $identityRelVersion = $m.Groups[1].Value.Trim().Trim('"').Trim("'") ; break }
    }
}
$relVersionForFiles = if ($identityRelVersion) { $identityRelVersion } else { $systemRelVersion }

# ---------------------------------------------------------------------------
# Parse registry patterns
# ---------------------------------------------------------------------------

$registrySchemas = @()
$regLines = [System.IO.File]::ReadAllLines($registryPath)
$cur = $null
foreach ($line in $regLines) {
    $mPat = [regex]::Match($line, '^\s*-\s*pattern:\s*[`"'']?([^`"'']+?)[`"'']?\s*$')
    if ($mPat.Success) {
        if ($cur) { $registrySchemas += $cur }
        $cur = @{ pattern = $mPat.Groups[1].Value.Trim(); schema_id = $null; current_version = $null }
        continue
    }
    if ($cur) {
        $mId = [regex]::Match($line, '^\s+schema_id:\s*(.+)$')
        if ($mId.Success) { $cur.schema_id = $mId.Groups[1].Value.Trim() }
        $mCv = [regex]::Match($line, '^\s+current_version:\s*(.+)$')
        if ($mCv.Success) { $cur.current_version = $mCv.Groups[1].Value.Trim() }
    }
}
if ($cur) { $registrySchemas += $cur }

# Map schema_id -> schema file path (e.g. task-file -> task_file.v?.schema.yaml)
function Get-SchemaFileForId {
    param([string]$SchemaId, [int]$VersionNum, [string]$SchemasDir)
    # registry uses hyphenated ids (task-file); filenames use underscores (task_file)
    $base = $SchemaId -replace '-', '_'
    $candidate = Join-Path $SchemasDir "$base.v$VersionNum.schema.yaml"
    if (Test-Path $candidate) { return $candidate }
    # fallback: any version file for this base (used to read migration_notes when exact missing)
    $any = Get-ChildItem $SchemasDir -Filter "$base.v*.schema.yaml" -ErrorAction SilentlyContinue | Sort-Object Name
    if ($any) { return $any[-1].FullName }
    return $null
}

# ---------------------------------------------------------------------------
# Migration core (per file)
# ---------------------------------------------------------------------------

$report = [System.Collections.Generic.List[object]]::new()

function Invoke-FileMigration {
    param(
        [string]$FilePath,
        [hashtable]$SchemaEntry,    # registry entry: pattern/schema_id/current_version
        [int]$TargetNum,
        [bool]$DoApply
    )

    $fm = Read-FrontMatter -Path $FilePath
    $curVerRaw = if ($fm.Fields.Contains('schema_version')) { $fm.Fields['schema_version'].Trim().Trim('"').Trim("'") } else { '' }
    $curNum = ConvertTo-VersionNumber $curVerRaw

    if ($curNum -eq $TargetNum) {
        return @{ Status = 'skipped-current'; File = $FilePath; From = $curNum; To = $TargetNum; Added = @(); Todos = @() }
    }
    if ($curNum -gt $TargetNum) {
        return @{ Status = 'skipped-newer'; File = $FilePath; From = $curNum; To = $TargetNum; Added = @(); Todos = @() }
    }

    # curNum < TargetNum -> migrate. Files without YAML frontmatter (e.g. the key=value
    # .identity dotfile) cannot carry frontmatter schema metadata. This is NOT a failure;
    # skip them without mutation so the engine never corrupts a non-frontmatter file.
    if (-not $fm.HasFrontMatter) {
        return @{ Status = 'skipped-no-frontmatter'; File = $FilePath; From = $curNum; To = $TargetNum; Added = @(); Todos = @() }
    }

    $addedFields = [System.Collections.Generic.List[string]]::new()
    $todoFields  = [System.Collections.Generic.List[string]]::new()
    $renames     = [System.Collections.Generic.List[object]]::new()  # @{ from; to; prefix }

    # Build the migration chain v(curNum+1) .. TargetNum
    for ($v = $curNum + 1; $v -le $TargetNum; $v++) {
        $schemaFile = Get-SchemaFileForId -SchemaId $SchemaEntry.schema_id -VersionNum $v -SchemasDir $script:schemasResolved
        $step = Get-MigrationStep -SchemaFile $schemaFile -VersionNum $v

        foreach ($a in $step.Added) {
            $fieldName = $a.field
            if ([string]::IsNullOrWhiteSpace($fieldName)) { continue }
            # schema_version / gald3r_rel_version are written unconditionally below; skip here
            if ($fieldName -in @('schema_version','gald3r_rel_version')) { continue }
            if ($fm.Fields.Contains($fieldName)) { continue }  # already present, leave value
            # Population Rules
            $val = $null
            switch -Regex ($fieldName) {
                'created_date|reported_date' {
                    $val = Get-GitCreationDate -FilePath $FilePath -RepoDir $script:ProjectPath
                }
                default { $val = $null }
            }
            if ($val) {
                $addedFields.Add("$fieldName=$val")
            } else {
                $todoFields.Add($fieldName)
            }
        }
        foreach ($d in $step.Deprecated) {
            $fn = $d.field
            if ($fm.Fields.Contains($fn) -and -not $fm.Fields.Contains("deprecated_$fn")) {
                $renames.Add(@{ from = $fn; to = "deprecated_$fn" })
            }
        }
        foreach ($r in $step.Removed) {
            $fn = $r.field
            if ($fm.Fields.Contains($fn) -and -not $fm.Fields.Contains("legacy_$fn")) {
                $renames.Add(@{ from = $fn; to = "legacy_$fn" })
            }
        }
    }

    if (-not $DoApply) {
        return @{
            Status = 'to-migrate'; File = $FilePath; From = $curNum; To = $TargetNum
            Added = $addedFields; Todos = $todoFields; Renames = $renames
        }
    }

    # ---- APPLY: rewrite frontmatter ----
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($l in $fm.Lines) { $lines.Add($l) }

    # 1. Renames (in-place line edits within frontmatter)
    foreach ($rn in $renames) {
        for ($i = 1; $i -lt $fm.FmEnd; $i++) {
            $m = [regex]::Match($lines[$i], "^($($rn.from)):(\s?.*)$")
            if ($m.Success) {
                $lines[$i] = "$($rn.to):$($m.Groups[2].Value)"
                break
            }
        }
    }

    # 2. Added fields with resolved values + TODO markers (insert before closing ---)
    $insertAt = $fm.FmEnd  # index of closing '---'
    $newFieldLines = [System.Collections.Generic.List[string]]::new()
    foreach ($a in $addedFields) {
        $parts = $a.Split('=', 2)
        $newFieldLines.Add("$($parts[0]): $($parts[1])")
    }
    foreach ($t in $todoFields) {
        $newFieldLines.Add("${t}: 'TODO: populate ${t} (schema migration)'")
    }

    # 3. schema_version + gald3r_rel_version (set or overwrite)
    $targetVerStr = "v$TargetNum"
    $svFound = $false; $grFound = $false
    for ($i = 1; $i -lt $fm.FmEnd; $i++) {
        if ($lines[$i] -match '^schema_version:') { $lines[$i] = "schema_version: $targetVerStr"; $svFound = $true }
        if ($lines[$i] -match '^gald3r_rel_version:') { $lines[$i] = "gald3r_rel_version: `"$script:relVersionForFiles`""; $grFound = $true }
    }
    if (-not $svFound) { $newFieldLines.Add("schema_version: $targetVerStr") }
    if (-not $grFound) { $newFieldLines.Add("gald3r_rel_version: `"$script:relVersionForFiles`"") }

    if ($newFieldLines.Count -gt 0) {
        $lines.InsertRange($insertAt, $newFieldLines)
    }

    $outText = ($lines -join $fm.Newline)
    [System.IO.File]::WriteAllText($FilePath, $outText)

    return @{
        Status = 'migrated'; File = $FilePath; From = $curNum; To = $TargetNum
        Added = $addedFields; Todos = $todoFields; Renames = $renames
    }
}

# ---------------------------------------------------------------------------
# Drive: glob each pattern, migrate each file
# ---------------------------------------------------------------------------

$projName = Split-Path $ProjectPath -Leaf
$mode = if ($Apply) { "--apply" } else { "dry-run" }

Write-Host ""
Write-Host "gald3r schema migration ($mode) -- project: $projName" -ForegroundColor Cyan
Write-Host "  Schemas: $schemasResolved" -ForegroundColor DarkGray
Write-Host "  System rel version: $systemRelVersion  |  file rel version: $relVersionForFiles" -ForegroundColor DarkGray

if (-not (Test-Path $dotGald3r)) {
    Write-Host "  No .gald3r/ directory at $dotGald3r -- nothing to migrate." -ForegroundColor Yellow
    exit 0
}

# ---------------------------------------------------------------------------
# T1442: Restore-from-canonical pass (opt-in via -RestoreMissing)
# Restores absent single-file .gald3r/ artifacts from the pristine template at
# .gald3r_sys/template_verification/. Runs BEFORE migration so a freshly restored file
# is then migrated forward in the same invocation. Default behavior unchanged.
# ---------------------------------------------------------------------------
$restoreReport = [System.Collections.Generic.List[object]]::new()
if ($RestoreMissing) {
    $dotGald3rCanonical = Resolve-DotGald3rCanonical -Project $ProjectPath -ScriptRoot $PSScriptRoot
    Write-Host ""
    if (-not $dotGald3rCanonical) {
        Write-Host "  RestoreMissing: canonical template not found (looked relative to script and under $ProjectPath\.gald3r_sys\template_verification\.gald3r) -- restore skipped." -ForegroundColor DarkYellow
    } else {
        Write-Host "  RestoreMissing: canonical template = $dotGald3rCanonical" -ForegroundColor DarkGray
        foreach ($entry in $registrySchemas) {
            if (-not $entry.pattern) { continue }
            # Only literal single-file patterns are restorable; never bulk-restore wildcard/recursive
            # patterns (e.g. .gald3r/tasks/** would be user task data, not template-restorable).
            if ($entry.pattern -match '[\*\?]') { continue }
            $relPath = ($entry.pattern -replace '^\.gald3r/', '') -replace '/', [System.IO.Path]::DirectorySeparatorChar
            $targetFile = Join-Path $dotGald3r $relPath
            if (Test-Path $targetFile -PathType Leaf) { continue }   # present -- nothing to restore
            $sourceFile = Join-Path $dotGald3rCanonical $relPath
            if (-not (Test-Path $sourceFile -PathType Leaf)) {
                $restoreReport.Add(@{ Status = 'restore-unavailable'; Rel = $relPath })
                continue
            }
            if ($Apply) {
                $targetDir = Split-Path $targetFile -Parent
                if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Force $targetDir | Out-Null }
                Copy-Item -LiteralPath $sourceFile -Destination $targetFile -Force
                $restoreReport.Add(@{ Status = 'restored'; Rel = $relPath })
                Write-Host "    RESTORED  $relPath  (from template_verification)" -ForegroundColor Green
            } else {
                $restoreReport.Add(@{ Status = 'to-restore'; Rel = $relPath })
                Write-Host "    WOULD RESTORE  $relPath  (from template_verification)" -ForegroundColor Yellow
            }
        }
        $restoredCount  = @($restoreReport | Where-Object { $_.Status -in @('restored','to-restore') }).Count
        $unavailCount   = @($restoreReport | Where-Object { $_.Status -eq 'restore-unavailable' }).Count
        Write-Host ("  RestoreMissing: {0} file(s) {1}, {2} unavailable in template." -f $restoredCount, $(if ($Apply) { 'restored' } else { 'to restore' }), $unavailCount) -ForegroundColor Cyan
    }
}

foreach ($entry in $registrySchemas) {
    if (-not $entry.pattern) { continue }
    # Determine target version for this schema
    $thisTargetNum = if ($TargetVersion) { ConvertTo-VersionNumber $TargetVersion } else { ConvertTo-VersionNumber $entry.current_version }
    if ($thisTargetNum -le 0) { $thisTargetNum = 1 }

    # Resolve glob: pattern is repo-relative beginning with ".gald3r/"
    $relGlob = $entry.pattern -replace '^\.gald3r/', ''
    $globFull = Join-Path $dotGald3r ($relGlob -replace '/', [System.IO.Path]::DirectorySeparatorChar)

    $matched = @()
    try {
        $matched = Get-ChildItem -Path $globFull -File -Recurse -ErrorAction SilentlyContinue
    } catch { $matched = @() }
    # For non-recursive single-file patterns (e.g. .gald3r/TASKS.md), Get-ChildItem -Recurse on a
    # literal file path still returns it; for ** patterns PowerShell expands the wildcard.
    if (-not $matched -or $matched.Count -eq 0) {
        # try literal (single-file patterns like .gald3r/.identity)
        if (Test-Path $globFull -PathType Leaf) { $matched = @(Get-Item $globFull) }
    }

    foreach ($file in $matched) {
        $res = Invoke-FileMigration -FilePath $file.FullName -SchemaEntry $entry -TargetNum $thisTargetNum -DoApply:$Apply.IsPresent
        $res.SchemaId = $entry.schema_id
        $report.Add($res)
    }
}

# ---------------------------------------------------------------------------
# T1485: Grouped-format SUBSYSTEMS.md regeneration (conditional, safe no-op).
# Runs after the per-file migration pass. Only acts when PRODUCT_SYSTEMS.md exists
# and subsystem specs carry parent_system: data; otherwise it is a strict no-op.
# ---------------------------------------------------------------------------
$groupedResult = Update-GroupedSubsystemsIndex -DotGald3r $dotGald3r -DoApply:$Apply.IsPresent
switch ($groupedResult) {
    'regenerated'    { Write-Host "  SUBSYSTEMS.md regenerated grouped by L1 system (parent_system: data present)." -ForegroundColor Green }
    'to-regenerate'  { Write-Host "  SUBSYSTEMS.md WOULD be regenerated grouped by L1 system (run -Apply)." -ForegroundColor Yellow }
    'index-section-missing' { Write-Host "  SUBSYSTEMS.md has no '## Subsystem Index' section -- grouped regen skipped." -ForegroundColor DarkYellow }
    default          { }  # no-parent-system-data / no-*-md -> silent no-op (common case)
}

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

$toMigrate   = @($report | Where-Object { $_.Status -eq 'to-migrate' })
$migrated    = @($report | Where-Object { $_.Status -eq 'migrated' })
$skipCurrent = @($report | Where-Object { $_.Status -eq 'skipped-current' })
$skipNewer   = @($report | Where-Object { $_.Status -eq 'skipped-newer' })
$skipNoFm    = @($report | Where-Object { $_.Status -eq 'skipped-no-frontmatter' })
$errors      = @($report | Where-Object { $_.Status -like 'error*' })

if (-not $Apply) {
    Write-Host ""
    Write-Host "Files to migrate: $($toMigrate.Count)" -ForegroundColor Yellow
    foreach ($r in $toMigrate) {
        $name = Split-Path $r.File -Leaf
        $adds = @()
        $adds += ($r.Added | ForEach-Object { ($_ -split '=')[0] })
        $adds += $r.Todos
        if ($r.Renames) { $adds += ($r.Renames | ForEach-Object { "$($_.from)->$($_.to)" }) }
        $addStr = if ($adds.Count -gt 0) { " [ADD/RENAME: $($adds -join ', ')]" } else { "" }
        $todoStr = if ($r.Todos.Count -gt 0) { " (TODO: $($r.Todos -join ', '))" } else { "" }
        Write-Host ("  {0,-44} v{1} -> v{2}{3}{4}" -f $name, $r.From, $r.To, $addStr, $todoStr)
    }
    Write-Host ""
    Write-Host "Files with TODO required:  $(@($toMigrate | Where-Object { $_.Todos.Count -gt 0 }).Count)"
    Write-Host "Files skipped (current):   $($skipCurrent.Count)"
    Write-Host "Files skipped (newer):     $($skipNewer.Count)"
    Write-Host "Files skipped (no fm):     $($skipNoFm.Count)"
    if ($skipNewer.Count -gt 0) {
        foreach ($r in $skipNewer) {
            Write-Host ("    NEWER  {0}  (file v{1} > target v{2}) -- left untouched" -f (Split-Path $r.File -Leaf), $r.From, $r.To) -ForegroundColor DarkYellow
        }
    }
    if ($errors.Count -gt 0) {
        Write-Host "Errors:                    $($errors.Count)" -ForegroundColor Red
        foreach ($r in $errors) { Write-Host ("    {0}  [{1}]" -f (Split-Path $r.File -Leaf), $r.Status) -ForegroundColor Red }
    }
    Write-Host ""
    Write-Host "Run with -Apply to execute." -ForegroundColor Yellow
    exit 0
}

# Apply summary
$todoCount = @($migrated | Where-Object { $_.Todos.Count -gt 0 }).Count
Write-Host ""
Write-Host ("Migrated:       {0,-4} files" -f $migrated.Count) -ForegroundColor Green
Write-Host ("TODO inserted:  {0,-4} files" -f $todoCount)
Write-Host ("Skipped:        {0,-4} files  (current: {1}, newer: {2}, no-fm: {3})" -f ($skipCurrent.Count + $skipNewer.Count + $skipNoFm.Count), $skipCurrent.Count, $skipNewer.Count, $skipNoFm.Count)
Write-Host ("Errors:         {0,-4} files" -f $errors.Count) -ForegroundColor $(if ($errors.Count -gt 0) { 'Red' } else { 'Gray' })
if ($skipNewer.Count -gt 0) {
    foreach ($r in $skipNewer) {
        Write-Host ("    NEWER  {0}  (file v{1} > target v{2}) -- left untouched" -f (Split-Path $r.File -Leaf), $r.From, $r.To) -ForegroundColor DarkYellow
    }
}
if ($errors.Count -gt 0) {
    foreach ($r in $errors) { Write-Host ("    {0}  [{1}]" -f (Split-Path $r.File -Leaf), $r.Status) -ForegroundColor Red }
}
Write-Host ""
if ($migrated.Count -gt 0) {
    Write-Host "Schema migration complete. Run @g-medic to validate migrated files." -ForegroundColor Cyan
} else {
    Write-Host "Schema migration complete. No files needed migration (already current)." -ForegroundColor Cyan
}
exit $(if ($errors.Count -gt 0) { 1 } else { 0 })
