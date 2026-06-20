<#
.SYNOPSIS
    Orchestrate a gald3r slim template release — version injection, parity gate, export, and handoff.

.DESCRIPTION
    Drives the full release pipeline from <gald3r_source> to the public gald3r repo:
      1. Run platform parity check (unless -Force or -SkipParityCheck)
      2. Inject version string into all 5 version locations in <ECOSYSTEM_ROOT>/<template_full>
      3. Validate CHANGELOG.md contains a heading for the target version
      4. Run export_slim_template_repo.ps1 to mirror <ECOSYSTEM_ROOT>/<template_full> to -Destination
      5. Print the suggested git commit, tag, and push commands

    Default is DRY-RUN (reports what would happen). Use -Apply to write files.

    This script does NOT commit or push. Review the diff in -Destination before committing.

.PARAMETER Version
    Version string (e.g. "1.1.0" — do NOT include the "v" prefix).

.PARAMETER Destination
    Target directory (local clone of the public gald3r repo, e.g. <workspace>\gald3r).

.PARAMETER Apply
    Actually write files. Without this, performs a dry-run and validation only.

.PARAMETER Force
    Skip the parity gate (logs a warning but proceeds).

.PARAMETER SkipParityCheck
    Do not invoke platform_parity_sync.ps1 (report-only parity gate).

.EXAMPLE
    .\scripts\release.ps1 -Version 1.1.0 -Destination <workspace>\gald3r
    # Dry-run — validates only, no files written

.EXAMPLE
    .\scripts\release.ps1 -Version 1.1.0 -Destination <workspace>\gald3r -Apply
    # Full release export with version injection
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [Parameter(Mandatory = $true)]
    [string]$Destination,

    [switch]$Apply,
    [switch]$Force,
    [switch]$SkipParityCheck
)

$ErrorActionPreference = "Stop"
$ScriptsDir = $PSScriptRoot
$SkillRoot = Split-Path $ScriptsDir -Parent
# Resolve <gald3r_source> repo root (skill lives under gald3r_template/.gald3r_sys/...)
$RepoRoot = $SkillRoot
for ($i = 0; $i -lt 6; $i++) {
    if (Test-Path (Join-Path $RepoRoot "custom_scripts\platform_parity_sync.ps1")) { break }
    $parent = Split-Path $RepoRoot -Parent
    if ($parent -eq $RepoRoot) { break }
    $RepoRoot = $parent
}
$EcosystemRoot = Split-Path $RepoRoot -Parent
$TemplateSrc = Join-Path $EcosystemRoot "<template_full>"

Write-Host ""
Write-Host "gald3r release pipeline" -ForegroundColor Cyan
Write-Host "  Version     : $Version" -ForegroundColor Cyan
Write-Host "  Destination : $Destination" -ForegroundColor Cyan
Write-Host "  Mode        : $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })" -ForegroundColor $(if ($Apply) { 'Green' } else { 'Yellow' })
Write-Host ""

# --- Step 1: Parity gate ---
# Run platform_parity_sync.ps1 in report-only mode (no -Sync): it detects parity
# gaps without modifying files and exits non-zero (1) when any gap is found, which
# is what gates the release here.
$ParityScript = Join-Path $RepoRoot "custom_scripts\platform_parity_sync.ps1"
if (-not $SkipParityCheck -and -not $Force) {
    if (-not (Test-Path $ParityScript)) {
        Write-Warning "Parity check script not found at $ParityScript — skipping (use -Force to suppress this warning)"
    }
    else {
        Write-Host "Step 1: Running platform parity check (report-only)..." -ForegroundColor Cyan
        & $ParityScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Error "Parity gaps detected. Fix with:`n  .\custom_scripts\platform_parity_sync.ps1 -Sync`nThen re-run, or use -Force to override."
            exit 1
        }
        Write-Host "  Parity: CLEAN" -ForegroundColor Green
    }
}
elseif ($Force) {
    Write-Warning "Step 1: -Force specified — parity gate skipped. Not recommended for release exports."
}

# --- Step 2: Version injection ---
Write-Host "Step 2: Version injection ($Version)..." -ForegroundColor Cyan

$versionTargets = @(
    @{
        File    = Join-Path $TemplateSrc "README.md"
        Pattern = 'version-[\d.]+-green\.svg'
        Replace = "version-$Version-green.svg"
        Desc    = "README.md badge"
    },
    @{
        File    = Join-Path $TemplateSrc "AGENTS.md"
        Pattern = '\*\*gald3r version\*\*: [\d.]+'
        Replace = "**gald3r version**: $Version"
        Desc    = "AGENTS.md"
    },
    @{
        File    = Join-Path $TemplateSrc "CLAUDE.md"
        Pattern = '\*\*gald3r version\*\*: [\d.]+'
        Replace = "**gald3r version**: $Version"
        Desc    = "CLAUDE.md"
    },
    @{
        File    = Join-Path $TemplateSrc ".agent\agent_instructions.md"
        Pattern = '\*\*gald3r Version\*\*: [\d.]+'
        Replace = "**gald3r Version**: $Version"
        Desc    = ".agent/agent_instructions.md"
    },
    @{
        File    = Join-Path $TemplateSrc ".gald3r\.identity"
        Pattern = 'gald3r_version=[\d.]+'
        Replace = "gald3r_version=$Version"
        Desc    = ".gald3r/.identity"
    },
    @{
        File    = Join-Path $TemplateSrc "VERSION"
        IsSimpleOverwrite = $true
        Replace = "$Version`n"
        Desc    = "VERSION"
    }
)

$versionErrors = @()
foreach ($target in $versionTargets) {
    if (-not (Test-Path $target.File)) {
        Write-Warning "  SKIP (not found): $($target.Desc)"
        continue
    }

    if ($target.IsSimpleOverwrite) {
        if ($Apply) {
            Set-Content -Path $target.File -Value $target.Replace -Encoding utf8 -NoNewline
        }
        Write-Host "  $(if ($Apply) { 'Updated' } else { 'Would update' }): $($target.Desc) -> $Version" -ForegroundColor $(if ($Apply) { 'Green' } else { 'DarkGray' })
        continue
    }

    $content = Get-Content $target.File -Raw
    if ($content -notmatch $target.Pattern) {
        Write-Warning "  No match found in $($target.Desc) — pattern may be stale: $($target.Pattern)"
        $versionErrors += $target.Desc
        continue
    }
    $newContent = $content -replace $target.Pattern, $target.Replace
    if ($Apply -and $content -ne $newContent) {
        Set-Content -Path $target.File -Value $newContent -Encoding utf8 -NoNewline
    }
    $alreadyCurrent = ($content -eq $newContent)
    Write-Host "  $(if ($Apply -and -not $alreadyCurrent) { 'Updated' } elseif ($alreadyCurrent) { 'Already current' } else { 'Would update' }): $($target.Desc)" -ForegroundColor $(if ($Apply -and -not $alreadyCurrent) { 'Green' } elseif ($alreadyCurrent) { 'DarkGray' } else { 'DarkGray' })
}

if ($versionErrors.Count -gt 0) {
    Write-Warning "Version injection had $($versionErrors.Count) unmatched location(s): $($versionErrors -join ', ')"
}

# --- Step 3: CHANGELOG validation ---
Write-Host "Step 3: Validating CHANGELOG.md heading..." -ForegroundColor Cyan
$changelogPath = Join-Path $TemplateSrc "CHANGELOG.md"
if (-not (Test-Path $changelogPath)) {
    Write-Error "CHANGELOG.md not found at $changelogPath"
    exit 1
}
$changelogContent = Get-Content $changelogPath -Raw
$headingPattern = "## \[$([regex]::Escape($Version))\]"
if ($changelogContent -notmatch $headingPattern) {
    Write-Error "CHANGELOG.md does not contain a heading for version [$Version].`nAdd the release entries under '## [$Version] - $(Get-Date -Format 'yyyy-MM-dd')' before running this script."
    exit 1
}
Write-Host "  CHANGELOG.md: heading [[$Version]] found" -ForegroundColor Green

# --- Step 4: Export ---
Write-Host "Step 4: Running export_slim_template_repo.ps1..." -ForegroundColor Cyan
$exportScript = Join-Path $RepoRoot "custom_scripts\export_slim_template_repo.ps1"
if (-not (Test-Path $exportScript)) {
    Write-Error "Export script not found: $exportScript"
    exit 1
}

$exportSplat = @{
    Destination     = $Destination
    SkipParityCheck = $true
}
if ($Apply)  { $exportSplat.Apply = $true }
if ($Force)  { $exportSplat.Force = $true }

& $exportScript @exportSplat
if ($LASTEXITCODE -ge 8) {
    Write-Error "Export script failed with exit code $LASTEXITCODE"
    exit 1
}

# --- Step 5: Print git handoff commands ---
$destFull = [System.IO.Path]::GetFullPath($Destination)
Write-Host ""
Write-Host "Release pipeline complete." -ForegroundColor Green
if (-not $Apply) {
    Write-Host "(Dry-run — no files written. Re-run with -Apply to execute.)" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Next steps — run these in $destFull :" -ForegroundColor Cyan
Write-Host ""
Write-Host "  cd `"$destFull`""
Write-Host "  git add ."
Write-Host "  git status   # Review what changed"
Write-Host "  git diff --stat HEAD"
Write-Host ""
Write-Host "  git commit -m `"release: v$Version`""
Write-Host "  git tag -a `"v$Version`" -m `"gald3r v$Version`""
Write-Host "  git push origin main --tags"
Write-Host ""
Write-Host "After push, GitHub Actions will automatically create a GitHub Release with:" -ForegroundColor DarkGray
Write-Host "  - Release notes extracted from CHANGELOG.md [[$Version]] section" -ForegroundColor DarkGray
Write-Host "  - gald3r-template-v$Version.zip download archive" -ForegroundColor DarkGray
Write-Host ""

exit 0
