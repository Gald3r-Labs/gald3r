#!/usr/bin/env pwsh
<#
.SYNOPSIS
    gald3r pre-push gate: regular (light) vs release (CHANGELOG/version discipline).

.DESCRIPTION
    Regular: status, unpushed commits, .gald3r sync hint. Never blocks.
    Release: requires a versioned ## [x] section in CHANGELOG.md (Keep a Changelog style);
             optional override via GALD3R_PUSH_GATE_OVERRIDE=1 or interactive prompt.

.PARAMETER Release
    Force release-mode checks.

.PARAMETER NonInteractive
    No Read-Host; use env vars only for overrides.

.PARAMETER HookMode
    Invoked from git pre-push: NonInteractive; release only if GALD3R_RELEASE_PUSH=1.

.PARAMETER DryRun
    Print mode and checks but always exit 0 (for agents verifying wiring).

.EXAMPLE
    ./.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1
    ./.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1 -Release
    $env:GALD3R_RELEASE_PUSH=1; ./.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1 -NonInteractive
#>
[CmdletBinding()]
param(
    [switch]$Release,
    [switch]$NonInteractive,
    [switch]$HookMode,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

if ($DryRun) {
    $NonInteractive = $true
}

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Host "gald3r push gate: not a git repository — skip" -ForegroundColor DarkGray
    exit 0
}
Set-Location $repoRoot

$isRelease = $false
if ($Release) {
    $isRelease = $true
}
elseif ($env:GALD3R_RELEASE_PUSH -eq "1" -or $env:GALD3R_RELEASE_PUSH -eq "true") {
    $isRelease = $true
}

if ($HookMode) {
    $NonInteractive = $true
    $isRelease = ($env:GALD3R_RELEASE_PUSH -eq "1" -or $env:GALD3R_RELEASE_PUSH -eq "true")
}
elseif (-not $isRelease -and -not $NonInteractive) {
    try {
        if ($Host.UI.RawUI -and $Host.Name -ne "ServerRemoteHost") {
            $resp = Read-Host "Is this a release push? (y/N)"
            if ($resp -match "^(y|yes)$") { $isRelease = $true }
        }
    }
    catch {
        # Non-interactive host
    }
}

function Write-ReleaseChangelogHint {
    $cl = Join-Path $repoRoot "CHANGELOG.md"
    if (-not (Test-Path $cl)) {
        Write-Host "BLOCK: CHANGELOG.md missing — add Keep a Changelog-style file at repo root." -ForegroundColor Red
        return $false
    }
    $raw = Get-Content $cl -Raw -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-Host "BLOCK: CHANGELOG.md is empty." -ForegroundColor Red
        return $false
    }
    # Versioned section other than [Unreleased]
    $hasVersioned = $raw -match '(?m)^##\s*\[(?!Unreleased\])[^\]]+\]'
    if (-not $hasVersioned) {
        Write-Host "BLOCK: Release push requires a versioned heading in CHANGELOG.md (e.g. ## [1.2.3] - YYYY-MM-DD) below [Unreleased]." -ForegroundColor Red
        Write-Host "       Resolve [Unreleased] into a version section per g-rl-26, or set GALD3R_PUSH_GATE_OVERRIDE=1 to skip." -ForegroundColor Yellow
        return $false
    }
    # Warn if [Unreleased] still has bullet lines (might mean not fully moved)
    if ($raw -match '(?ms)^##\s*\[Unreleased\]\s*\r?\n(?<body>.*?)(?=^##\s*\[|\z)') {
        $ub = $matches["body"]
        if ($ub -match '(?m)^\s*[-*]\s+\S') {
            Write-Host "WARN: [Unreleased] still lists bullets — confirm they should not move into the new version section." -ForegroundColor Yellow
        }
    }
    Write-Host "CHANGELOG: versioned section present — OK" -ForegroundColor Green
    return $true
}

function Show-VersionFiles {
    foreach ($vf in @("pyproject.toml", "package.json")) {
        $p = Join-Path $repoRoot $vf
        if (-not (Test-Path $p)) { continue }
        if ($vf -eq "pyproject.toml") {
            $ln = Select-String -Path $p -Pattern "^\s*version\s*=" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($ln) { Write-Host "  $($ln.Line.Trim()) ($vf)" -ForegroundColor DarkGray }
        }
        else {
            $ln = Select-String -Path $p -Pattern '"version"\s*:' -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($ln) { Write-Host "  $($ln.Line.Trim()) ($vf)" -ForegroundColor DarkGray }
        }
    }
    if (Test-Path (Join-Path $repoRoot "AGENTS.md")) {
        Write-Host "  AGENTS.md present — spot-check Version / Last Updated if applicable." -ForegroundColor DarkGray
    }
}

# --- Regular mode ---
if (-not $isRelease) {
    Write-Host ""
    Write-Host "gald3r push gate — REGULAR" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    git status -sb 2>$null
    Write-Host ""
    $null = git rev-parse --abbrev-ref "@{upstream}" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Unpushed commits (@{upstream}..HEAD, max 25):" -ForegroundColor Cyan
        git --no-pager log --oneline -n 25 "@{upstream}..HEAD" 2>$null
    }
    else {
        Write-Host "Recent commits (no upstream set):" -ForegroundColor Cyan
        git --no-pager log --oneline -n 10 2>$null
    }
    Write-Host ""
    if (Test-Path ".gald3r") {
        $porcelain = git status --porcelain 2>$null
        if ($porcelain -match '(?m)\.gald3r/') {
            Write-Host "NOTE: .gald3r/ has local changes — consider @g-task-sync-check before sharing branch state." -ForegroundColor Yellow
        }
    }
    Write-Host "Regular push gate: OK (informational only)" -ForegroundColor Green
    Write-Host ""
    if ($DryRun) { exit 0 }
    exit 0
}

# --- Release mode ---
Write-Host ""
Write-Host "gald3r push gate — RELEASE" -ForegroundColor Magenta
Write-Host "=========================" -ForegroundColor Magenta

$block = $false
$ok = Write-ReleaseChangelogHint
if (-not $ok) { $block = $true }

if ($block -and ($env:GALD3R_PUSH_GATE_OVERRIDE -eq "1")) {
    Write-Host "OVERRIDE: GALD3R_PUSH_GATE_OVERRIDE=1 — proceeding despite CHANGELOG gate." -ForegroundColor Yellow
    $block = $false
}
elseif ($block -and -not $NonInteractive) {
    try {
        $o = Read-Host "Release gate failed. Override and continue? (y/N)"
        if ($o -match "^(y|yes)$") { $block = $false }
    }
    catch { }
}

if (-not $block) {
    Write-Host ""
    Write-Host "README: re-read install, features, and contributor/version sections before tagging." -ForegroundColor Cyan
    Write-Host "Declared versions (if present):" -ForegroundColor Cyan
    Show-VersionFiles
}

Write-Host ""
if ($DryRun) {
    Write-Host "DryRun: exit 0" -ForegroundColor DarkGray
    exit 0
}
if ($block) {
    Write-Host "Release push gate: BLOCKED" -ForegroundColor Red
    exit 1
}
Write-Host "Release push gate: OK" -ForegroundColor Green
Write-Host ""
exit 0
