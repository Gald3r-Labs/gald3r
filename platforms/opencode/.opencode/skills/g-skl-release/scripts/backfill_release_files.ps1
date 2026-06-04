<#
.SYNOPSIS
    gald3r Release File Backfill (BUG-104 / C-023)

.DESCRIPTION
    Scans a project's CHANGELOG.md for versioned headers (## [X.Y.Z]) and creates a
    matching release file under .gald3r/releases/ for any version that does not already
    have one. This silences the session-start C-023 warning:
        "N CHANGELOG version(s) missing release file - run @g-release-sync"

    Backfilled release files are named release{NNN}_v{X}-{Y}-{Z}.md so they satisfy both
    the canonical release{NNN}_{slug}.md naming and the g-rl-25 Step 2b "filename contains
    the version" check. They are written with status: released and the date parsed from the
    CHANGELOG header (when present).

    Invoked by @g-update on the upgrade path and by @g-release-sync / g-medic --heal-c023.

.PARAMETER ProjectRoot
    Root directory of the target project. Defaults to current directory.

.PARAMETER Apply
    Actually write files. Without -Apply, runs in dry-run mode (prints the plan only).

.PARAMETER Json
    Emit a JSON result object instead of human-readable text.

.EXAMPLE
    # Dry-run: show which release files would be created
    .\backfill_release_files.ps1 -ProjectRoot "G:\MyProject"

    # Apply: create the missing release files
    .\backfill_release_files.ps1 -ProjectRoot "G:\MyProject" -Apply

.NOTES
    Task: T1438  Bug: BUG-104
    Ships in g-skl-release skill (full + adv tiers).
#>

param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$Apply,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Status($msg, $color = "Cyan") {
    if (-not $Json) { Write-Host $msg -ForegroundColor $color }
}

$changelogPath = Join-Path $ProjectRoot "CHANGELOG.md"
$releasesDir   = Join-Path $ProjectRoot ".gald3r\releases"

if (-not (Test-Path $changelogPath)) {
    if ($Json) { @{ success = $false; error = "CHANGELOG.md not found at $changelogPath" } | ConvertTo-Json | Write-Output }
    else { Write-Host "ERROR: CHANGELOG.md not found at $changelogPath" -ForegroundColor Red }
    exit 1
}

# Parse CHANGELOG versions: capture version + optional date from "## [X.Y.Z] - YYYY-MM-DD"
$versions = @()
foreach ($line in (Get-Content $changelogPath)) {
    if ($line -match '^\#\#\s*\[(\d+\.\d+\.\d+)\]\s*-?\s*(\d{4}-\d{2}-\d{2})?') {
        $versions += [pscustomobject]@{
            Version = $matches[1]
            Date    = if ($matches[2]) { $matches[2] } else { (Get-Date -Format "yyyy-MM-dd") }
        }
    }
}

if ($versions.Count -eq 0) {
    Write-Status "No versioned CHANGELOG headers found - nothing to backfill." "DarkGray"
    if ($Json) { @{ success = $true; created = @(); skipped = @(); dry_run = (-not $Apply) } | ConvertTo-Json | Write-Output }
    exit 0
}

# Collect existing release-file versions (from frontmatter version: field and from filenames)
$existingVersions = @()
$existingMaxId = 0
if (Test-Path $releasesDir) {
    Get-ChildItem $releasesDir -Filter "release*.md" -File -ErrorAction SilentlyContinue | ForEach-Object {
        $raw = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($raw -match "(?m)^\s*version:\s*'?`"?(\d+\.\d+\.\d+)") { $existingVersions += $matches[1] }
        if ($_.Name -match '^release(\d+)_') { $idNum = [int]$matches[1]; if ($idNum -gt $existingMaxId) { $existingMaxId = $idNum } }
    }
}

$created = @()
$skipped = @()
$nextId = $existingMaxId

if (-not (Test-Path $releasesDir)) {
    if ($Apply) { New-Item -ItemType Directory -Force $releasesDir | Out-Null }
}

Write-Status ""
Write-Status "gald3r Release File Backfill (C-023)" "Cyan"
Write-Status ("-" * 50) "DarkGray"
Write-Status "  Project root : $ProjectRoot"
Write-Status "  Mode         : $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })" "$(if ($Apply) { 'Yellow' } else { 'DarkGray' })"
Write-Status ""

foreach ($v in $versions) {
    if ($existingVersions -contains $v.Version) {
        $skipped += $v.Version
        Write-Status "  skip: [$($v.Version)] already has a release file" "DarkGray"
        continue
    }

    $nextId++
    $idStr   = "{0:000}" -f $nextId
    $verSlug = "v" + ($v.Version -replace '\.', '-')
    $fileName = "release${idStr}_${verSlug}.md"
    $filePath = Join-Path $releasesDir $fileName

    $body = @"
---
id: $nextId
name: 'v$($v.Version)'
version: '$($v.Version)'
target_date: '$($v.Date)'
status: released
cadence_days: 14
features: []
tasks: []
notes: 'Backfilled from CHANGELOG by backfill_release_files.ps1 (BUG-104 / C-023).'
created_date: '$($v.Date)'
released_date: '$($v.Date)'
---
# Release ${nextId}: v$($v.Version)

## Release Notes

See CHANGELOG.md section [$($v.Version)] for the full notes.

## Blockers

- None (backfilled record).
"@

    if ($Apply) {
        Set-Content -Path $filePath -Value $body -Encoding utf8
        Write-Status "  created: $fileName  ([$($v.Version)] released $($v.Date))" "Green"
    } else {
        Write-Status "  would create: $fileName  ([$($v.Version)] released $($v.Date))" "Gray"
    }
    $created += $v.Version
}

Write-Status ""
Write-Status "Backfill summary: $($created.Count) created, $($skipped.Count) already present." "Cyan"
if (-not $Apply -and $created.Count -gt 0) {
    Write-Status "DRY-RUN: no files written. Re-run with -Apply to create them." "DarkGray"
}

if ($Json) {
    @{
        success = $true
        dry_run = (-not $Apply)
        created = $created
        skipped = $skipped
    } | ConvertTo-Json | Write-Output
}
