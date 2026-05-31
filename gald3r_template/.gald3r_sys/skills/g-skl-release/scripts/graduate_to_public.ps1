# graduate_to_public.ps1 - Tier graduation to public (T1419) -- scrub or carry modes
# @subsystems: RELEASE_AND_VERSIONING
<#
.SYNOPSIS
    Promotes a tagged release to the public-tier repository.

.DESCRIPTION
    Mode A (scrub): replaces public repo history with a clean root commit. Requires -ConfirmScrub.
    Mode B (carry): incremental commit on public main after content scrub. No force push.

    History mode read from AGENT_CONFIG test_to_public_history (scrub|carry). Default: scrub.

.PARAMETER Version
    Semantic version (tag vX.Y.Z must exist in source repo).

.PARAMETER ConfirmScrub
    Required for scrub mode (destructive history replace).

.PARAMETER DryRun
    Plan only.

.PARAMETER DevRepoPath
    Override dev repo path for audit log.

.PARAMETER HistoryMode
    Override test_to_public_history (scrub|carry).
#>
param(
    [Parameter(Mandatory)]
    [string]$Version,

    [switch]$ConfirmScrub,
    [switch]$DryRun,
    [string]$DevRepoPath = "",
    [ValidateSet("scrub", "carry", "")]
    [string]$HistoryMode = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptsDir = $PSScriptRoot

function Write-Info  { param([string]$Msg) Write-Host "  [INFO]  $Msg" -ForegroundColor Cyan }
function Write-OK    { param([string]$Msg) Write-Host "  [ OK ]  $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "  [WARN]  $Msg" -ForegroundColor Yellow }
function Write-Fail  { param([string]$Msg) Write-Host "  [FAIL]  $Msg" -ForegroundColor Red; exit 1 }
function Write-Dry   { param([string]$Msg) Write-Host "  [DRY ]  $Msg" -ForegroundColor Magenta }

$tierCfg = & (Join-Path $ScriptsDir "read_tier_config.ps1") -ProjectRoot (Get-Location).Path
$mode = if ($HistoryMode) { $HistoryMode } else { $tierCfg.test_to_public_history }
if ($mode -notin @("scrub", "carry")) { $mode = "scrub" }

Write-Host ""
Write-Host " Gald3r Tier Graduation -> public" -ForegroundColor $(if ($mode -eq "scrub") { "Red" } else { "Blue" })
Write-Host " Version: v$Version | History mode: $mode"
if ($DryRun) { Write-Host " Mode: DRY RUN" -ForegroundColor Magenta }
Write-Host ""

if ($mode -eq "scrub" -and -not $ConfirmScrub -and -not $DryRun) {
    Write-Fail "scrub mode requires -ConfirmScrub (public history will be replaced)."
}

$publicPath = $tierCfg.tier_public_path
$devPath = if ($DevRepoPath) { $DevRepoPath } elseif ($tierCfg.tier_dev_path) { $tierCfg.tier_dev_path } else { (Get-Location).Path }

if ($tierCfg.tier -notin @("dev", "test")) {
    Write-Fail "tier='$($tierCfg.tier)'. Run from dev or test tier repo."
}
if (-not $publicPath) { Write-Fail "tier_public_path not set in .gald3r/.identity" }
if (-not (Test-Path $publicPath)) { Write-Fail "Public repo path does not exist: $publicPath" }

$tagName = "v$Version"
$sourceRepo = (Get-Location).Path

if (-not (git rev-parse $tagName 2>$null)) {
    Write-Fail "Tag '$tagName' not found in source repo."
}

$sensitiveFiles = git ls-tree -r --name-only $tagName 2>$null | Where-Object {
    $_ -like ".gald3r/*" -or $_ -like ".env" -or $_ -like ".env.local" -or
    $_ -like "docs/internal/*" -or $_ -like ".gald3r_sys/*"
}
if ($sensitiveFiles) {
    Write-Fail "Sensitive paths in tag '$tagName'. Aborting.`n$($sensitiveFiles -join "`n")"
}

$dirty = git status --porcelain=v1
if ($dirty) { Write-Fail "Working tree has uncommitted changes." }

if ($mode -eq "scrub" -and -not $DryRun) {
    Write-Warn "DESTRUCTIVE: public history at $publicPath will be REPLACED."
    $answer = Read-Host "Type YES to proceed (case-sensitive)"
    if ($answer -ne "YES") { Write-Host "Cancelled."; exit 0 }
}

if ($DryRun) {
    Write-Dry "Would export $tagName, scrub tree, publish to $publicPath (mode: $mode)"
    exit 0
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "gald3r_public_$Version"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Info "Exporting $tagName..."
git archive --format=tar $tagName | tar -x -C $tempDir
& (Join-Path $ScriptsDir "scrub_public_tree.ps1") -TreePath $tempDir | Out-Null

Push-Location $publicPath
try {
    if ($mode -eq "scrub") {
        $publicGit = Join-Path $publicPath ".git"
        if (Test-Path $publicGit) { Remove-Item $publicGit -Recurse -Force }

        git init
        git checkout -b main 2>$null
        if ($LASTEXITCODE -ne 0) { git branch -M main }

        Copy-Item -Path "$tempDir\*" -Destination "." -Recurse -Force

        New-Item -ItemType Directory -Path ".gald3r" -Force | Out-Null
        $projType = if ($tierCfg.tier_profile) { "development" } else { "development" }
        @"
tier=public
tier_profile=$($tierCfg.tier_profile)
project_type=$projType
"@ | Set-Content ".gald3r/.identity"

        git add -A
        git commit -m "release: v$Version (public release -- clean history)"
        git tag -f $tagName
        Write-OK "Public repo scrubbed to clean root at $tagName"
    } else {
        if (-not (Test-Path (Join-Path $publicPath ".git"))) {
            Write-Fail "carry mode requires existing git repo at $publicPath"
        }
        $branch = (git rev-parse --abbrev-ref HEAD).Trim()
        if ($branch -ne "main") {
            Write-Fail "carry mode requires public repo on main (currently: $branch)"
        }
        $pubDirty = git status --porcelain=v1
        if ($pubDirty) { Write-Fail "Public repo has uncommitted changes. Commit or stash first." }

        Copy-Item -Path "$tempDir\*" -Destination "." -Recurse -Force
        git add -A
        git commit -m "release: v$Version (public incremental -- scrubbed content)"
        git tag -f $tagName
        Write-OK "Public repo updated incrementally at $tagName (no history scrub)"
    }
}
finally {
    Pop-Location
    Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

$logRoot = if (Test-Path "$devPath/.gald3r/logs") { "$devPath/.gald3r/logs" } else { ".gald3r/logs" }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logFile = Join-Path $logRoot ("graduation_public_{0}_{1}.md" -f $Version, (Get-Date -Format "yyyyMMdd"))
@"
# Graduation Log: -> public -- v$Version
- **Date**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- **Source**: $sourceRepo
- **Target**: $publicPath
- **History mode**: $mode
- **History scrubbed**: $(if ($mode -eq "scrub") { "YES" } else { "NO" })
"@ | Set-Content $logFile

Write-OK "Graduation v$Version -> public complete"
Write-Info "Next: git -C `"$publicPath`" push origin main --tags"
