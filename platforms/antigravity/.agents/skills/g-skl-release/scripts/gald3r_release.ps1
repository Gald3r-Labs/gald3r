<#
.SYNOPSIS
    gald3r Maintainer Release Tool
    Syncs and tags a release across gald3r's three template repositories.
    <gald3r_source> only — NOT shipped to user projects.

.DESCRIPTION
    This is the maintainer tool for releasing gald3r itself across:
      - <ECOSYSTEM_ROOT>/<template_slim>
      - <ECOSYSTEM_ROOT>/<template_full>
      - <ECOSYSTEM_ROOT>/<template_adv>

    For user project releases, use @g-ship / .claude/skills/g-skl-release/scripts/gald3r_semver.ps1.

    Two-track release model:
      Track A (<gald3r_source>):      version managed in <gald3r_source> CHANGELOG.md / VERSION
      Track B (template repos):  version managed in each template repo's CHANGELOG.md / VERSION

    This script handles Track B — promoting template CHANGELOGs and tagging.

.PARAMETER TemplateVersion
    Version to release in the template repos (e.g., "1.5.0").
    If omitted, reads from <template_adv>/VERSION.

.PARAMETER Theme
    Short theme name for the release (e.g., "Platform Framework Architecture").

.PARAMETER Apply
    Actually apply changes. Without -Apply, runs in dry-run mode.

.PARAMETER NoGitHub
    Skip GitHub release creation.

.PARAMETER RepoRoot
    Override the ecosystem root (default: <ECOSYSTEM_ROOT>).

.EXAMPLE
    # Dry-run: see what would happen
    .\gald3r_release.ps1 -TemplateVersion "1.5.0" -Theme "Platform Framework"

    # Apply to all three repos
    .\gald3r_release.ps1 -TemplateVersion "1.5.0" -Theme "Platform Framework" -Apply

    # Apply and create GitHub releases
    .\gald3r_release.ps1 -TemplateVersion "1.5.0" -Theme "Platform Framework" -Apply -GitHub

.NOTES
    Task: T1210
    <gald3r_source> maintainer-only. See root_only_manifest.yaml.
#>

param(
    [string]$TemplateVersion = "",
    [string]$Theme = "",
    [switch]$Apply,
    [switch]$GitHub,
    [switch]$NoGitHub,
    [string]$RepoRoot = "<workspace>"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repos = @(
    "$RepoRoot\<template_slim>",
    "$RepoRoot\<template_full>",
    "$RepoRoot\<template_adv>"
)

$semverScript = Join-Path $PSScriptRoot "gald3r_semver.ps1"

function Write-Status($msg, $color = "Cyan") {
    Write-Host $msg -ForegroundColor $color
}

function Fail($msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

# ── Validate repo existence ───────────────────────────────────────────────────

foreach ($repo in $repos) {
    if (-not (Test-Path $repo)) {
        Fail "Template repo not found: $repo"
    }
}

# ── Determine template version ────────────────────────────────────────────────

if (-not $TemplateVersion) {
    $versionFile = "$RepoRoot\<template_adv>\VERSION"
    if (Test-Path $versionFile) {
        $TemplateVersion = (Get-Content $versionFile -Raw).Trim()
        Write-Status "Auto-detected version from <template_adv>/VERSION: $TemplateVersion"
    } else {
        Fail "TemplateVersion not specified and VERSION file not found at $versionFile"
    }
}

# ── Pre-flight: check each repo is clean enough ──────────────────────────────

Write-Status ""
Write-Status "gald3r Maintainer Release Tool" "Cyan"
Write-Status ("─" * 60) "DarkGray"
Write-Status "  Template version : $TemplateVersion"
Write-Status "  Theme            : $(if ($Theme) { $Theme } else { '(none)' })"
Write-Status "  Mode             : $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })" "$(if ($Apply) { 'Yellow' } else { 'DarkGray' })"
Write-Status ""

Write-Status "── Pre-flight checks ────────────────────────" "DarkGray"
$allClean = $true
foreach ($repo in $repos) {
    $repoName = Split-Path $repo -Leaf
    $dirty = git -C $repo status --short 2>$null
    if ($dirty) {
        Write-Status "  ⚠  $repoName has uncommitted changes:" "Yellow"
        $dirty | ForEach-Object { Write-Status "       $_" "Gray" }
        $allClean = $false
    } else {
        Write-Status "  ✓  $repoName is clean" "Green"
    }
}
Write-Status ""

if (-not $allClean -and $Apply) {
    Write-Host ""
    $response = Read-Host "WARNING: Some repos have uncommitted changes. Continue anyway? [y/N]"
    if ($response -notmatch '^[yY]') {
        Write-Status "Aborted. Commit or stash changes in each repo first." "Yellow"
        exit 0
    }
}

# ── Process each template repo ────────────────────────────────────────────────

Write-Status "── Processing template repos ────────────────" "DarkGray"

foreach ($repo in $repos) {
    $repoName = Split-Path $repo -Leaf
    Write-Status ""
    Write-Status "  [$repoName]" "White"

    $changelogPath = Join-Path $repo "CHANGELOG.md"
    $versionPath   = Join-Path $repo "VERSION"

    # Read current version
    $currentVersion = "0.0.0"
    if (Test-Path $versionPath) {
        $currentVersion = (Get-Content $versionPath -Raw).Trim()
    }

    Write-Status "    Current: $currentVersion  →  Target: $TemplateVersion" "Gray"

    if ($currentVersion -eq $TemplateVersion) {
        Write-Status "    Already at $TemplateVersion — checking if tag exists..." "DarkGray"
        $tagExists = git -C $repo tag -l "v$TemplateVersion" 2>$null
        if ($tagExists) {
            Write-Status "    Tag v$TemplateVersion already exists — skipping" "DarkGray"
            continue
        }
    }

    if (-not $Apply) {
        Write-Status "    DRY-RUN: Would promote CHANGELOG + bump VERSION + tag v$TemplateVersion" "DarkGray"
        continue
    }

    # Check if semver.ps1 exists in repo (it should, via parity sync)
    $repoSemver = Join-Path $repo "scripts\gald3r_semver.ps1"
    if (Test-Path $repoSemver) {
        # Use the repo's own semver script
        $themeArg = if ($Theme) { "-Theme `"$Theme`"" } else { "" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $repoSemver `
            -ProjectRoot $repo `
            -BumpType "patch" `
            -Theme $Theme `
            -Apply
    } else {
        # Fallback: do it manually
        Write-Status "    gald3r_semver.ps1 not found in $repoName — promoting manually" "Yellow"

        # Update VERSION
        Set-Content $versionPath $TemplateVersion -NoNewline
        Write-Status "    ✓ VERSION → $TemplateVersion" "Green"

        # Promote CHANGELOG (use <gald3r_source> semver script if available)
        if (Test-Path $semverScript) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $semverScript `
                -ProjectRoot $repo `
                -BumpType "patch" `
                -Theme $Theme `
                -Apply
        }
    }

    Write-Status "    ✓ $repoName released at v$TemplateVersion" "Green"
}

# ── GitHub releases ───────────────────────────────────────────────────────────

if ($GitHub -and -not $NoGitHub -and $Apply) {
    Write-Status ""
    Write-Status "── Creating GitHub releases ─────────────────" "DarkGray"
    foreach ($repo in $repos) {
        $repoName = Split-Path $repo -Leaf
        Write-Status "  Creating GitHub release for $repoName..." "Gray"

        # Push tags first
        git -C $repo push origin "v$TemplateVersion" 2>&1 | Out-Null

        # Extract release notes from CHANGELOG
        $cl = Get-Content (Join-Path $repo "CHANGELOG.md")
        $inSection = $false; $notes = @()
        foreach ($line in $cl) {
            if ($line -match "^\#\# \[$([regex]::Escape($TemplateVersion))\]") { $inSection = $true; continue }
            if ($inSection -and $line -match "^\#\# \[") { break }
            if ($inSection) { $notes += $line }
        }
        $notesContent = ($notes -join "`n").Trim()
        $notesFile = "$env:TEMP\gald3r_release_notes_$repoName.md"
        Set-Content $notesFile $notesContent

        $title = if ($Theme) { "v$TemplateVersion — $Theme" } else { "v$TemplateVersion" }
        gh release create "v$TemplateVersion" `
            --title $title `
            --notes-file $notesFile `
            --repo "wrm3/$repoName" 2>&1

        Write-Status "  ✓ GitHub release created for $repoName" "Green"
    }
}

Write-Status ""
Write-Status "── Release v$TemplateVersion complete ─────────────────" "Green"
Write-Status ""
Write-Status "Next steps:" "Cyan"
Write-Status "  Push all template repos:  git push origin main --tags (in each)" "Gray"
Write-Status "  Update <gald3r_source> CHANGELOG if needed" "Gray"
Write-Status ""
