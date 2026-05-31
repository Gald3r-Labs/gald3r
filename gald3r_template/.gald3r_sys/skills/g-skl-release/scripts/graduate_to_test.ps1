# graduate_to_test.ps1 - Tier graduation dev -> test (T1419)
# @subsystems: RELEASE_AND_VERSIONING
<#
.SYNOPSIS
    Promotes the dev-tier repository to the test-tier sibling.

.PARAMETER Version
    Semantic version to graduate (must match existing git tag vX.Y.Z).

.PARAMETER DryRun
    Plan without writing.

.PARAMETER Force
    Skip confirmation prompt.
#>
param(
    [Parameter(Mandatory)]
    [string]$Version,

    [switch]$DryRun,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptsDir = $PSScriptRoot
. (Join-Path $ScriptsDir "read_tier_config.ps1") | Out-Null
. (Join-Path $ScriptsDir "scrub_public_tree.ps1") | Out-Null

function Write-Info  { param([string]$Msg) Write-Host "  [INFO]  $Msg" -ForegroundColor Cyan }
function Write-OK    { param([string]$Msg) Write-Host "  [ OK ]  $Msg" -ForegroundColor Green }
function Write-Fail  { param([string]$Msg) Write-Host "  [FAIL]  $Msg" -ForegroundColor Red; exit 1 }
function Write-Dry   { param([string]$Msg) Write-Host "  [DRY ]  $Msg" -ForegroundColor Magenta }

Write-Host ""
Write-Host " Gald3r Tier Graduation: dev -> test" -ForegroundColor Blue
Write-Host " Version: v$Version"
if ($DryRun) { Write-Host " Mode: DRY RUN" -ForegroundColor Magenta }
Write-Host ""

$tierCfg = & (Join-Path $ScriptsDir "read_tier_config.ps1") -ProjectRoot (Get-Location).Path

if ($tierCfg.tier -ne "dev") { Write-Fail "tier='$($tierCfg.tier)'. Run from the dev-tier repo root." }
$testPath = $tierCfg.tier_test_path
if (-not $testPath) { Write-Fail "tier_test_path not set in .gald3r/.identity" }
if (-not (Test-Path $testPath)) { Write-Fail "Test repo path does not exist: $testPath" }

$tagName = "v$Version"
if (-not (git tag --list $tagName)) { Write-Fail "Tag '$tagName' not found. Cut release first." }

$dirty = git status --porcelain=v1
if ($dirty) { Write-Fail "Working tree has uncommitted changes." }

$gald3rFiles = git ls-tree -r --name-only $tagName | Where-Object { $_ -like ".gald3r/*" }
if ($gald3rFiles) { Write-Fail ".gald3r/ content in tag tree. Aborting." }

$historyMode = $tierCfg.dev_to_test_history
Write-Info "History mode: $historyMode"

if (-not $Force -and -not $DryRun) {
    $answer = Read-Host "Proceed dev -> test at $testPath? [y/N]"
    if ($answer -notmatch "^[yY]$") { exit 0 }
}

if ($DryRun) {
    Write-Dry "Would export $tagName, scrub, push to $testPath (mode: $historyMode)"
    exit 0
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "gald3r_graduation_test_$Version"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

git archive --format=tar $tagName | tar -x -C $tempDir
& (Join-Path $ScriptsDir "scrub_public_tree.ps1") -TreePath $tempDir -Quiet | Out-Null

$testGitDir = Join-Path $testPath ".git"
if (-not (Test-Path $testGitDir)) { Write-Fail "Test path is not a git repo: $testPath" }

$devRoot = (Get-Location).Path

Push-Location $testPath
try {
    if ($historyMode -eq "carry") {
        git remote remove _dev_source 2>$null
        git remote add _dev_source $devRoot 2>$null
        git fetch _dev_source --tags
        git merge $tagName --allow-unrelated-histories -m "chore: graduate v$Version from dev tier"
    } else {
        Copy-Item -Path "$tempDir\*" -Destination "." -Recurse -Force
        git add -A
        git commit -m "release: graduate v$Version from dev tier (squash)" --allow-empty
    }
    git tag $tagName -f
    Write-OK "Tagged $testPath at $tagName"
}
finally {
    Pop-Location
    Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

$logDir = ".gald3r/logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir ("graduation_test_{0}_{1}.md" -f $Version, (Get-Date -Format "yyyyMMdd"))
@"
# Graduation Log: dev -> test -- v$Version
- **Date**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- **Target**: $testPath
- **History mode**: $historyMode
"@ | Set-Content $logFile

Write-OK "Graduation v$Version -> test complete"
