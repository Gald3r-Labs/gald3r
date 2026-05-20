<#
.SYNOPSIS
    gald3r Semantic Versioning Engine
    Core release management for gald3r projects.
    Called by @g-ship and gald3r_release.ps1.

.DESCRIPTION
    Handles version parsing, CHANGELOG promotion, VERSION file updates,
    git tagging, and optional GitHub release creation.

    Semver definitions:
      MAJOR (X.0.0) - Breaking changes, complete reframe, new architecture
      MINOR (0.X.0) - New features, additive, nothing breaks
      PATCH (0.0.X) - Bug fixes, small extensions, doc updates

.PARAMETER ProjectRoot
    Root directory of the project. Defaults to current directory.

.PARAMETER BumpType
    Version bump type: major, minor, or patch.

.PARAMETER Theme
    Short theme name for the release (e.g. "Bug Fix Sprint", "Agent Tools").
    Appears in the CHANGELOG header.

.PARAMETER Apply
    Actually apply changes. Without -Apply, runs in dry-run mode.

.PARAMETER NoTag
    Skip git tag creation.

.PARAMETER NoGitHub
    Skip GitHub release creation even if gh CLI is available.

.PARAMETER Json
    Output result as JSON instead of human-readable text.

.EXAMPLE
    .\gald3r_semver.ps1 -BumpType minor -Theme "New Skills" -Apply
    .\gald3r_semver.ps1 -BumpType patch -Apply -NoGitHub
    .\gald3r_semver.ps1 -BumpType major -Theme "v2 Architecture" -Apply -Json

.NOTES
    Task: T1210
    Part of the g-ship release management system.
#>

param(
    [string]$ProjectRoot = (Get-Location).Path,
    [ValidateSet("major", "minor", "patch")]
    [string]$BumpType,
    [string]$Theme = "",
    [switch]$Apply,
    [switch]$NoTag,
    [switch]$NoGitHub,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Status($msg, $color = "Cyan") {
    if (-not $Json) { Write-Host $msg -ForegroundColor $color }
}

function Fail($msg) {
    if ($Json) {
        @{ success = $false; error = $msg } | ConvertTo-Json | Write-Output
    } else {
        Write-Host "ERROR: $msg" -ForegroundColor Red
    }
    exit 1
}

# ── Locate key files ─────────────────────────────────────────────────────────

$changelogPath = Join-Path $ProjectRoot "CHANGELOG.md"
$versionPath   = Join-Path $ProjectRoot "VERSION"
$readmePath    = Join-Path $ProjectRoot "README.md"

if (-not (Test-Path $changelogPath)) {
    Fail "CHANGELOG.md not found at $changelogPath"
}

# ── Parse current version ─────────────────────────────────────────────────────

function Get-CurrentVersion {
    # Try VERSION file first
    if (Test-Path $versionPath) {
        $v = (Get-Content $versionPath -Raw).Trim()
        if ($v -match '^\d+\.\d+\.\d+$') { return $v }
    }

    # Fall back to latest version header in CHANGELOG
    $cl = Get-Content $changelogPath
    foreach ($line in $cl) {
        if ($line -match '^\#\# \[(\d+\.\d+\.\d+)\]') {
            return $matches[1]
        }
    }

    # Default starting version
    return "0.0.0"
}

function Bump-Version($current, $type) {
    $parts = $current -split '\.'
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2]

    switch ($type) {
        "major" { $major++; $minor = 0; $patch = 0 }
        "minor" { $minor++;              $patch = 0 }
        "patch" { $patch++ }
    }

    return "$major.$minor.$patch"
}

# ── Read [Unreleased] section ─────────────────────────────────────────────────

function Get-UnreleasedContent {
    $lines       = Get-Content $changelogPath
    $inSection   = $false
    $content     = @()

    foreach ($line in $lines) {
        if ($line -match '^\#\# \[Unreleased\]') {
            $inSection = $true
            continue
        }
        if ($inSection -and $line -match '^\#\# \[') {
            break
        }
        if ($inSection) {
            $content += $line
        }
    }

    # Strip leading/trailing blank lines
    $trimmed = ($content | Where-Object { $_ -ne "" -or $content.IndexOf($_) -gt 0 })
    return $trimmed
}

function Test-UnreleasedHasContent {
    $content = Get-UnreleasedContent
    $meaningful = $content | Where-Object { $_ -match '\S' -and $_ -notmatch '^###' }
    return ($meaningful.Count -gt 0)
}

# ── Promote CHANGELOG ─────────────────────────────────────────────────────────

function Promote-Changelog($newVersion, $theme, $date) {
    $lines       = Get-Content $changelogPath
    $result      = @()
    $promoted    = $false
    $inUnreleased = $false

    $header = if ($theme) {
        "## [$newVersion] - $date ($theme)"
    } else {
        "## [$newVersion] - $date"
    }

    foreach ($line in $lines) {
        if ($line -match '^\#\# \[Unreleased\]' -and -not $promoted) {
            # Write new empty [Unreleased] + separator
            $result += "## [Unreleased]"
            $result += ""
            $result += "### Added"
            $result += "### Changed"
            $result += "### Fixed"
            $result += "### Removed"
            $result += ""
            $result += "---"
            $result += ""
            # Write new version header in place of [Unreleased]
            $result += $header
            $inUnreleased = $true
            $promoted     = $true
            continue
        }

        if ($inUnreleased -and $line -match '^\#\# \[') {
            $inUnreleased = $false
        }

        $result += $line
    }

    return $result
}

# ── Extract release notes for a version ──────────────────────────────────────

function Get-ReleaseNotes($version) {
    $lines     = Get-Content $changelogPath
    $inSection = $false
    $notes     = @()

    foreach ($line in $lines) {
        if ($line -match "^\#\# \[$([regex]::Escape($version))\]") {
            $inSection = $true
            continue
        }
        if ($inSection -and $line -match '^\#\# \[') {
            break
        }
        if ($inSection) {
            $notes += $line
        }
    }

    return ($notes -join "`n").Trim()
}

# ── Update README badge ───────────────────────────────────────────────────────

function Update-ReadmeBadge($oldVersion, $newVersion) {
    if (-not (Test-Path $readmePath)) { return $false }

    $content = Get-Content $readmePath -Raw
    $oldMajorMinor = ($oldVersion -split '\.')[0..1] -join '.'
    $newMajorMinor = ($newVersion -split '\.')[0..1] -join '.'

    $pattern = "version-$([regex]::Escape($oldMajorMinor))-"
    if ($content -match $pattern) {
        $updated = $content -replace $pattern, "version-$newMajorMinor-"
        Set-Content $readmePath $updated -NoNewline
        return $true
    }
    return $false
}

# ── Main ──────────────────────────────────────────────────────────────────────

if (-not $BumpType) { Fail "BumpType is required: major, minor, or patch" }

$currentVersion = Get-CurrentVersion
$newVersion     = Bump-Version $currentVersion $BumpType
$today          = Get-Date -Format "yyyy-MM-dd"
$tagName        = "v$newVersion"

Write-Status ""
Write-Status "gald3r Semver Release Engine" "Cyan"
Write-Status ("-" * 50) "DarkGray"
Write-Status "  Project root : $ProjectRoot"
Write-Status "  Current ver  : $currentVersion"
Write-Status "  Bump type    : $BumpType"
Write-Status "  New version  : $newVersion"
Write-Status "  Tag          : $tagName"
Write-Status "  Theme        : $(if ($Theme) { $Theme } else { '(none)' })"
Write-Status "  Mode         : $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })" "$(if ($Apply) { 'Yellow' } else { 'DarkGray' })"
Write-Status ""

# Check [Unreleased] has content
$hasContent = Test-UnreleasedHasContent
if (-not $hasContent) {
    Write-Status "WARNING: [Unreleased] section appears empty — release will have no notes." "Yellow"
}

$unreleasedContent = Get-UnreleasedContent
Write-Status "── [Unreleased] preview ──────────────────────" "DarkGray"
$unreleasedContent | ForEach-Object { Write-Status "  $_" "Gray" }
Write-Status ""

if (-not $Apply) {
    Write-Status "DRY-RUN: No changes made. Pass -Apply to execute." "DarkGray"
    if ($Json) {
        @{
            success        = $true
            dry_run        = $true
            current        = $currentVersion
            new_version    = $newVersion
            tag            = $tagName
            has_content    = $hasContent
        } | ConvertTo-Json | Write-Output
    }
    exit 0
}

# ── Apply changes ─────────────────────────────────────────────────────────────

Write-Status "── Applying changes ──────────────────────────" "Yellow"

# 1. Promote CHANGELOG
Write-Status "  [1/5] Promoting CHANGELOG.md [Unreleased] → [$newVersion]..."
$newLines = Promote-Changelog $newVersion $Theme $today
Set-Content $changelogPath ($newLines -join "`n") -NoNewline
Write-Status "        ✓ CHANGELOG.md updated" "Green"

# 2. Bump VERSION file
Write-Status "  [2/5] Writing VERSION file: $newVersion..."
Set-Content $versionPath $newVersion -NoNewline
Write-Status "        ✓ VERSION updated" "Green"

# 3. Update README badge
Write-Status "  [3/5] Updating README badge..."
$badgeUpdated = Update-ReadmeBadge $currentVersion $newVersion
if ($badgeUpdated) {
    Write-Status "        ✓ README badge updated" "Green"
} else {
    Write-Status "        ~ README badge not found or already current" "DarkGray"
}

# 4. Git commit
Write-Status "  [4/5] Creating release commit..."
$commitMsg = if ($Theme) { "release: $tagName -- $Theme" } else { "release: $tagName" }
git -C $ProjectRoot add CHANGELOG.md VERSION README.md 2>$null
git -C $ProjectRoot commit -m $commitMsg 2>&1 | Out-Null
Write-Status "        ✓ Committed: '$commitMsg'" "Green"

# 5. Git tag
if (-not $NoTag) {
    Write-Status "  [5/5] Creating git tag $tagName..."
    $tagMsg = if ($Theme) { "Release $tagName - $Theme" } else { "Release $tagName" }
    git -C $ProjectRoot tag -a $tagName -m $tagMsg 2>&1 | Out-Null
    Write-Status "        ✓ Tag created: $tagName" "Green"
} else {
    Write-Status "  [5/5] Skipping tag (--NoTag)" "DarkGray"
}

Write-Status ""
Write-Status "── Release $tagName complete ─────────────────" "Green"
Write-Status ""
Write-Status "Next steps:" "Cyan"
Write-Status "  Push:           git push origin main --tags" "Gray"
if (-not $NoGitHub) {
    Write-Status "  GitHub release: gh release create $tagName --title '$tagName' --notes-file <(git show HEAD:CHANGELOG.md | ...)" "Gray"
    Write-Status "  Or run:         .\scripts\gald3r_semver.ps1 -CreateRelease -Version $newVersion" "Gray"
}
Write-Status ""

if ($Json) {
    @{
        success      = $true
        dry_run      = $false
        old_version  = $currentVersion
        new_version  = $newVersion
        tag          = $tagName
        theme        = $Theme
        commit_msg   = $commitMsg
        badge_updated = $badgeUpdated
    } | ConvertTo-Json | Write-Output
}
