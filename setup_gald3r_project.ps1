# setup_gald3r_project.ps1 — gald3r Installer
# =============================================
# Default (no -Platform):  installs Cursor + Claude Code + shared brain.
# -Platform <name>:        installs the specified platform's thin adapter + shared brain.
#                          Cursor/Claude config is skipped when installing other platforms.
#
# Usage:
#   .\setup_gald3r_project.ps1                                                   # Cursor + Claude
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject"                        # same, specify target
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform windsurf     # Windsurf only
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform cursor       # Cursor only (no .claude/)
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -DryRun                # preview
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Force                 # skip confirmations

param(
    [string]$TargetPath = "",
    [string]$Platform   = "",
    [switch]$Force,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Resolve paths ──────────────────────────────────────────────────────────────
$scriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$templateDir  = Join-Path $scriptDir "project_template"
$platformsDir = Join-Path $scriptDir "platforms"

if (-not (Test-Path $templateDir)) {
    Write-Error "Cannot find project_template/ next to this script."
    exit 1
}

$availablePlatforms = if (Test-Path $platformsDir) {
    (Get-ChildItem $platformsDir -Directory | Select-Object -ExpandProperty Name | Sort-Object)
} else { @() }

# ── Validate platform if given ────────────────────────────────────────────────
$Platform = $Platform.Trim().ToLower()
if ($Platform -and $availablePlatforms -notcontains $Platform -and
    $Platform -notin @("cursor","claude")) {
    Write-Host ""
    Write-Host "  Unknown platform '$Platform'." -ForegroundColor Yellow
    Write-Host "  Available: $($availablePlatforms -join ', ')" -ForegroundColor DarkGray
    Write-Host "  Leave blank for the default Cursor + Claude install." -ForegroundColor DarkGray
    exit 1
}

# ── Prompt for target if not given ────────────────────────────────────────────
if (-not $TargetPath) {
    Write-Host ""
    Write-Host "  gald3r Installer" -ForegroundColor Cyan
    Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkGray
    if (-not $Platform) {
        Write-Host "  Default: installs Cursor + Claude Code support."
        Write-Host "  Use -Platform <name> for a single platform."
        if ($availablePlatforms) {
            Write-Host "  Supported: $($availablePlatforms -join ', ')" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
    $TargetPath = Read-Host "  Target project path"
}

$TargetPath = $TargetPath.Trim().TrimEnd('\').TrimEnd('/')

if (-not (Test-Path $TargetPath)) {
    if (-not $Force) {
        $create = Read-Host "  '$TargetPath' does not exist. Create it? (y/N)"
        if ($create -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }
    }
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Write-Host "  Created: $TargetPath" -ForegroundColor Green
}

# ── Check for existing install ────────────────────────────────────────────────
$existingGald3r = Test-Path (Join-Path $TargetPath ".gald3r")
if ($existingGald3r -and -not $Force -and -not $DryRun) {
    Write-Host ""
    Write-Host "  WARNING: .gald3r/ already exists." -ForegroundColor Yellow
    Write-Host "  Your tasks, bugs, and plans will NOT be overwritten." -ForegroundColor Yellow
    $confirm = Read-Host "  Update gald3r config files? (y/N)"
    if ($confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }
}

# ── Helper: copy files from a source dir → target, respecting protected dirs ──
function Copy-Layer {
    param(
        [string]$SourceDir,
        [string]$TargetDir,
        [string[]]$Protected = @(),
        [string[]]$SkipTopDirs = @()
    )
    $n = 0
    Get-ChildItem -Path $SourceDir -Recurse -File | ForEach-Object {
        $rel    = $_.FullName.Substring($SourceDir.Length).TrimStart('\').TrimStart('/')
        $topDir = ($rel -split '[/\\]')[0]
        if ($SkipTopDirs -contains $topDir) { return }
        $dest   = Join-Path $TargetDir $rel
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

$protectedDirs = @(".gald3r")

# ── Determine install mode ────────────────────────────────────────────────────
Write-Host ""
if ($DryRun) { Write-Host "  DRY RUN — no files will be written" -ForegroundColor Yellow }

$label    = ""
$baseSkip = @()
$platformDir = $null

if (-not $Platform -or $Platform -in @("cursor","claude")) {
    # Default: full project_template/ (has .cursor + .claude + brain)
    $label = if ($Platform -eq "claude") { "Claude Code" }
             elseif ($Platform -eq "cursor") { "Cursor" }
             else { "Cursor + Claude Code (default)" }
    # For cursor-only: skip .claude; for claude-only: skip .cursor
    if ($Platform -eq "cursor")  { $baseSkip = @(".claude") }
    if ($Platform -eq "claude")  { $baseSkip = @(".cursor") }
} else {
    # Specific non-Tier1 platform: brain from project_template (no .cursor/.claude) + platform overlay
    $label = $Platform
    $baseSkip   = @(".cursor", ".claude")
    $platformDir = Join-Path $platformsDir $Platform
    if (-not (Test-Path $platformDir)) {
        Write-Error "platforms/$Platform/ not found."
        exit 1
    }
}

Write-Host "  Installing gald3r [$label] into: $TargetPath" -ForegroundColor Cyan
Write-Host ""

$total = 0

# Step 1: shared base
$n1 = Copy-Layer -SourceDir $templateDir -TargetDir $TargetPath `
                 -Protected $protectedDirs -SkipTopDirs $baseSkip
$total += $n1
Write-Host "  Base   : $n1 files copied"

# Step 2: platform overlay (only for non-Tier1)
if ($platformDir) {
    $n2 = Copy-Layer -SourceDir $platformDir -TargetDir $TargetPath `
                     -Protected $protectedDirs
    $total += $n2
    Write-Host "  Config : $n2 files copied ($Platform)"
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
if ($DryRun) {
    Write-Host "  Dry run — would copy $total files." -ForegroundColor Yellow
} else {
    Write-Host "  Done. $total files installed." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor Cyan
    if ($Platform -eq "claude") {
        Write-Host "   Open in Claude Code and run /g-setup"
    } elseif (-not $Platform -or $Platform -eq "cursor") {
        Write-Host "   Open in Cursor → @g-setup  |  or Claude Code → /g-setup"
    } else {
        Write-Host "   Open in $Platform — .gald3r/ brain and AGENTS.md are ready"
    }
    Write-Host ""
    Write-Host "  Docs: https://github.com/wrm3/gald3r" -ForegroundColor DarkGray
}
