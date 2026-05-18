<#
.SYNOPSIS
    Nightly hook: trigger session summary extraction into learned-facts.md (T928).

.DESCRIPTION
    Fired by HEARTBEAT.md scheduler (or manually). Runs gald3r_nightly_learn.ps1
    in gather mode — collects new session summaries and writes an extraction prompt
    to .gald3r/logs/nightly_learn_pending.txt.

    When a pending extraction exists, the session-start protocol should surface it
    so the next agent can run "@g-learn extract" to apply the facts.

.PARAMETER ProjectRoot
    Root of the gald3r project. Defaults to nearest .gald3r/ ancestor.
#>

[CmdletBinding()]
param(
    [string] $ProjectRoot = ''
)

$ErrorActionPreference = 'Stop'

# Locate project root by walking up from script location
if (-not $ProjectRoot) {
    $dir = $PSScriptRoot
    while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { $dir = ''; break }
        $dir = $parent
    }
    $ProjectRoot = if ($dir) { $dir } else { (Get-Location).Path }
}

$helperScript = Join-Path $ProjectRoot 'scripts' 'gald3r_nightly_learn.ps1'

if (-not (Test-Path $helperScript)) {
    Write-Warning "gald3r_nightly_learn.ps1 not found at: $helperScript"
    exit 0
}

# Check HEARTBEAT to see if nightly learning is enabled
$heartbeat = Join-Path $ProjectRoot '.gald3r' 'config' 'HEARTBEAT.md'
if (Test-Path $heartbeat) {
    $hb = Get-Content $heartbeat -Raw
    if ($hb -match 'nightly_learn:\s*false') {
        Write-Host "[g-hk-nightly-learn] Skipped — disabled in HEARTBEAT.md" -ForegroundColor Gray
        exit 0
    }
}

Write-Host "[g-hk-nightly-learn] Starting nightly session extraction..." -ForegroundColor Cyan

& powershell -NoProfile -ExecutionPolicy Bypass -File $helperScript `
    -ProjectRoot $ProjectRoot `
    -LookbackDays 3

$pendingPath = Join-Path $ProjectRoot '.gald3r' 'logs' 'nightly_learn_pending.txt'
if (Test-Path $pendingPath) {
    Write-Host ""
    Write-Host "[g-hk-nightly-learn] Pending extraction ready." -ForegroundColor Yellow
    Write-Host "  Run '@g-learn extract' in your next agent session to apply facts." -ForegroundColor Yellow
}
