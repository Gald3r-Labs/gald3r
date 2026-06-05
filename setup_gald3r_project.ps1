# setup_gald3r_project.ps1 - gald3r Installer
# =============================================
# Installs gald3r into a target project.
#
# Default (no -Platform):
#   Installs Cursor + Claude Code - copies project_template/ as-is.
#
# -Platform <name>:
#   Installs a specific platform. Copies project_template/ (shared brain,
#   skipping .cursor/.claude) then overlays platforms/<name>/.
#
# Usage:
#   .\setup_gald3r_project.ps1                                                # Cursor + Claude
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject"                    # same, no prompt
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform windsurf # Windsurf only
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform cursor   # Cursor only
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -DryRun            # preview only
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Force             # skip confirmations

param(
    [string]$TargetPath = "",
    [string]$Platform   = "",
    [switch]$Force,
    [switch]$DryRun,
    [switch]$NoEngine    # skip provisioning the bundled gald3r engine (uv); skills then use SKILL.full.md
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# -- Repo identity --------------------------------------------------------------
# gald3r:            $RequirePlatform = $false  -> default = Cursor + Claude Code
# <template_adv>: $RequirePlatform = $true -> must pick a platform
$RequirePlatform = $false

# -- Resolve paths --------------------------------------------------------------
$scriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$templateDir  = Join-Path $scriptDir "project_template"
$platformsDir = Join-Path $scriptDir "platforms"

if (-not (Test-Path $templateDir)) {
    Write-Error "Cannot find project_template/ next to this script."
    exit 1
}

$availablePlatforms = if (Test-Path $platformsDir) {
    Get-ChildItem $platformsDir -Directory | Select-Object -ExpandProperty Name | Sort-Object
} else { @() }

# -- Validate / prompt for platform --------------------------------------------
$Platform = $Platform.Trim().ToLower()

if ($RequirePlatform -and -not $Platform) {
    Write-Host ""
    Write-Host "  gald3r Installer" -ForegroundColor Cyan
    Write-Host "  -----------------------------------------" -ForegroundColor DarkGray
    Write-Host "  Available platforms:"
    $availablePlatforms | ForEach-Object { Write-Host "    * $_" -ForegroundColor DarkGray }
    Write-Host ""
    $Platform = (Read-Host "  Platform (e.g. cursor, claude, windsurf)").Trim().ToLower()
}

if ($Platform -and $availablePlatforms -and $availablePlatforms -notcontains $Platform) {
    Write-Host "  Unknown platform '$Platform'." -ForegroundColor Yellow
    Write-Host "  Available: $($availablePlatforms -join ', ')" -ForegroundColor DarkGray
    exit 1
}

# -- Prompt for target path -----------------------------------------------------
if (-not $TargetPath) {
    Write-Host ""
    Write-Host "  gald3r Installer" -ForegroundColor Cyan
    Write-Host "  -----------------------------------------" -ForegroundColor DarkGray
    if (-not $Platform) {
        Write-Host "  Default: Cursor + Claude Code. Use -Platform <name> to install one platform."
        if ($availablePlatforms) {
            Write-Host "  Platforms: $($availablePlatforms -join ', ')" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  Platform: $Platform"
    }
    Write-Host ""
    $TargetPath = (Read-Host "  Target project path").Trim()
}

$TargetPath = $TargetPath.TrimEnd('\').TrimEnd('/')

# -- Create target if missing ---------------------------------------------------
if (-not (Test-Path $TargetPath)) {
    if (-not $Force) {
        $yn = Read-Host "  '$TargetPath' does not exist. Create it? (y/N)"
        if ($yn -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }
    }
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Write-Host "  Created: $TargetPath" -ForegroundColor Green
}

# -- Warn on existing .gald3r/ ------------------------------------------------
if ((Test-Path (Join-Path $TargetPath ".gald3r")) -and -not $Force -and -not $DryRun) {
    Write-Host ""
    Write-Host "  WARNING: .gald3r/ already exists. Tasks/bugs/plans will NOT be overwritten." -ForegroundColor Yellow
    $yn = Read-Host "  Update gald3r config files? (y/N)"
    if ($yn -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }
}

# -- Copy-Layer helper ---------------------------------------------------------
# Copies all files from $SourceDir into $TargetDir.
# $SkipTopDirs : top-level dirs to exclude entirely (e.g. skip .cursor when installing windsurf)
# $Protected   : top-level dirs that exist in target and should never be overwritten
function Copy-Layer {
    param(
        [string]   $SourceDir,
        [string]   $TargetDir,
        [string[]] $SkipTopDirs = @(),
        [string[]] $Protected   = @()
    )
    $n = 0
    Get-ChildItem -Path $SourceDir -Recurse -File | ForEach-Object {
        $rel    = $_.FullName.Substring($SourceDir.Length).TrimStart('\').TrimStart('/')
        $topDir = ($rel -split '[/\\]')[0]
        if ($SkipTopDirs -contains $topDir) { return }
        $dest = Join-Path $TargetDir $rel
        if ($Protected -contains $topDir -and (Test-Path $dest)) { return }
        if (-not $DryRun) {
            $d = Split-Path $dest -Parent
            if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
            Copy-Item $_.FullName $dest -Force
        }
        $n++
    }
    return $n
}

$protected = @(".gald3r")

# -- Determine what to install -------------------------------------------------
# In gald3r: .cursor/ and .claude/ live inside project_template/ (Tier 1 = no overlay needed)
# In <template_adv>: project_template/ has NO platform dirs - overlay always required
$tier1 = if (-not $RequirePlatform) { @("cursor", "claude") } else { @() }
$isTier1 = (-not $Platform) -or ($Platform -in $tier1)

$label     = if (-not $Platform) { "Cursor + Claude Code (default)" }
             elseif ($Platform -eq "cursor") { "Cursor" }
             elseif ($Platform -eq "claude") { "Claude Code" }
             else { $Platform }

Write-Host ""
if ($DryRun) { Write-Host "  DRY RUN -- no files will be written" -ForegroundColor Yellow }
Write-Host "  Installing gald3r [$label] into: $TargetPath" -ForegroundColor Cyan
Write-Host ""

$total = 0

# Step 1: shared base from project_template/
$skipDirs = if ($isTier1) {
    # Cursor: skip .claude; Claude: skip .cursor; default: skip nothing
    if ($Platform -eq "cursor") { @(".claude") }
    elseif ($Platform -eq "claude") { @(".cursor") }
    else { @() }
} else {
    @(".cursor", ".claude")   # non-Tier1: skip platform-specific dirs, brain only
}

$n1 = Copy-Layer -SourceDir $templateDir -TargetDir $TargetPath `
                 -SkipTopDirs $skipDirs -Protected $protected
$total += $n1
Write-Host "  Base   : $n1 files  (project_template/)"

# Step 2: platform overlay (only for non-Tier1 or explicit single platform)
if ($Platform -and $Platform -notin $tier1 -and (Test-Path $platformsDir)) {
    $platDir = Join-Path $platformsDir $Platform
    if (Test-Path $platDir) {
        $n2 = Copy-Layer -SourceDir $platDir -TargetDir $TargetPath -Protected $protected
        $total += $n2
        Write-Host "  Config : $n2 files  (platforms/$Platform/)"
    }
}

# -- Summary -------------------------------------------------------------------
Write-Host ""
if ($DryRun) {
    Write-Host "  Dry run -- would copy $total files." -ForegroundColor Yellow
} else {
    Write-Host "  Done. $total files installed." -ForegroundColor Green

    # -- Provision the bundled gald3r engine (uv) ------------------------------
    # Makes the slimmed skills' preferred path (`gald3r <verb>`) work out of the box.
    # Fully optional: -NoEngine skips it, and any failure is non-fatal because every
    # slimmed skill ships a SKILL.full.md fallback that works without the engine.
    if (-not $NoEngine) {
        $provPs1 = Join-Path $TargetPath ".gald3r_sys/engine/provision_engine.ps1"
        if (Test-Path $provPs1) {
            Write-Host ""
            Write-Host "  Provisioning the bundled gald3r engine (uv)..." -ForegroundColor Cyan
            try { & $provPs1 } catch {
                Write-Host "  Engine bootstrap skipped: $($_.Exception.Message)" -ForegroundColor Yellow
                Write-Host "  (Skills still work via their SKILL.full.md fallback.)" -ForegroundColor DarkGray
            }
        }
    } else {
        Write-Host "  Engine provisioning skipped (-NoEngine). Skills use their SKILL.full.md fallback;" -ForegroundColor DarkGray
        Write-Host "  provision later with: pwsh .gald3r_sys/engine/provision_engine.ps1" -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor Cyan
    if (-not $Platform -or $Platform -eq "cursor") {
        Write-Host "   Cursor      : open project, run @g-setup"
    }
    if (-not $Platform -or $Platform -eq "claude") {
        Write-Host "   Claude Code : open project, run /g-setup"
    }
    if ($Platform -and $Platform -notin $tier1) {
        Write-Host "   $Platform : open project in $Platform -- .gald3r/ brain and AGENTS.md are ready"
    }
    Write-Host ""
    Write-Host "   Engine     : slimmed skills call the bundled engine at .gald3r_sys/engine/" -ForegroundColor DarkGray
    Write-Host "                (re/provision anytime: pwsh .gald3r_sys/engine/provision_engine.ps1)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Docs: https://github.com/wrm3/gald3r" -ForegroundColor DarkGray
}
