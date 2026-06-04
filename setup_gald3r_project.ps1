# setup_gald3r_project.ps1 — gald3r Installer
# =============================================
# Copies the gald3r project_template/ into a target project.
# Supports Cursor and Claude Code (Tier 1). Other platforms via AGENTS.md.
#
# Usage:
#   .\setup_gald3r_project.ps1                                      # interactive
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject"          # specify target
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Force   # no confirmation
#   .\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -DryRun  # preview only

param(
    [string]$TargetPath = "",
    [switch]$Force,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Resolve paths ──────────────────────────────────────────────────────────────
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$templateDir = Join-Path $scriptDir "project_template"

if (-not (Test-Path $templateDir)) {
    Write-Error "Cannot find project_template/ next to this script. Run from the gald3r repo root."
    exit 1
}

# ── Prompt for target if not given ────────────────────────────────────────────
if (-not $TargetPath) {
    Write-Host ""
    Write-Host "  gald3r Installer" -ForegroundColor Cyan
    Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "  This will copy the gald3r template into your project."
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
    Write-Host "  WARNING: .gald3r/ already exists in '$TargetPath'." -ForegroundColor Yellow
    Write-Host "  Existing .gald3r/ data (tasks, bugs, plans) will NOT be overwritten." -ForegroundColor Yellow
    $confirm = Read-Host "  Update gald3r config files (.cursor/, .claude/, .gald3r_sys/)? (y/N)"
    if ($confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }
}

# ── Dirs that should never be overwritten (user data) ────────────────────────
$protectedDirs = @(".gald3r")

# ── Copy template → target ────────────────────────────────────────────────────
Write-Host ""
if ($DryRun) {
    Write-Host "  DRY RUN — no files will be written" -ForegroundColor Yellow
}
Write-Host "  Installing gald3r into: $TargetPath" -ForegroundColor Cyan
Write-Host ""

$copied   = 0
$skipped  = 0

Get-ChildItem -Path $templateDir -Recurse -File | ForEach-Object {
    $rel  = $_.FullName.Substring($templateDir.Length).TrimStart('\').TrimStart('/')
    $dest = Join-Path $TargetPath $rel

    # Skip if the file is inside a protected user-data dir
    $topDir = ($rel -split '[/\\]')[0]
    if ($protectedDirs -contains $topDir -and (Test-Path $dest)) {
        $skipped++
        return
    }

    if ($DryRun) {
        Write-Host "  [dry] $rel" -ForegroundColor DarkGray
        $copied++
        return
    }

    $destDir = Split-Path -Parent $dest
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item -Path $_.FullName -Destination $dest -Force
    $copied++
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
if ($DryRun) {
    Write-Host "  Dry run complete." -ForegroundColor Yellow
    Write-Host "  Would copy : $copied files" -ForegroundColor White
    Write-Host "  Would skip : $skipped files (existing user data)" -ForegroundColor White
} else {
    Write-Host "  Installation complete." -ForegroundColor Green
    Write-Host "  Copied : $copied files" -ForegroundColor White
    if ($skipped -gt 0) {
        Write-Host "  Skipped: $skipped files (existing .gald3r/ data preserved)" -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Open '$TargetPath' in Cursor or Claude Code"
    Write-Host "   2. Run @g-setup (Cursor) or /g-setup (Claude Code)"
    Write-Host "   3. Follow the prompts to name your project"
    Write-Host ""
    Write-Host "  Docs: https://github.com/wrm3/gald3r" -ForegroundColor DarkGray
}
