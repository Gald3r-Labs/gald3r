# @subsystems: MEMORY_AND_KNOWLEDGE
<#
.SYNOPSIS
    Nightly hook: trigger session summary extraction into learned-facts.md (T928, T1233).

.DESCRIPTION
    Fires under `stop` (agent session complete). Lightweight by design:

    1. Walks up to find the project root.
    2. Reads the per-N-sessions counter at `.gald3r/logs/learn-counter`.
       Increments it. Only proceeds when the counter hits `nightly_learn_interval`
       (default 5; configurable in `.gald3r/config/AGENT_CONFIG.md`).
    3. Checks `nightly_learn:` in HEARTBEAT.md for an explicit off switch.
    4. Spawns the heavy helper (`gald3r_nightly_learn.ps1`) as a fully detached
       background process via `Start-Process -WindowStyle Hidden -PassThru`. The
       hook itself returns within milliseconds — it never blocks the agent UI
       waiting for LLM extraction.
    5. Writes a `.gald3r/logs/nightly-learn-last-run.log` with the spawn time,
       PID, helper path, and counter state so future hangs are diagnosable.

    The previous T928 implementation invoked the helper synchronously (`& powershell ... `)
    and scanned ALL historical logs every call, causing 20+ minute stalls (T1233 motivation).
    This version delegates lookback narrowing to the helper itself (default `-LookbackDays 1`)
    and never blocks the hook's synchronous path.

.PARAMETER ProjectRoot
    Root of the gald3r project. Defaults to nearest .gald3r/ ancestor.

.PARAMETER Force
    Bypass the every-N-sessions counter and run the extraction immediately.
    Counter is still incremented (resets to 0 after the spawn).
#>

[CmdletBinding()]
param(
    [string] $ProjectRoot = '',
    [switch] $Force
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

$helperScript = Join-Path (Join-Path (Join-Path (Join-Path $ProjectRoot '.gald3r_sys') 'skills') 'g-skl-learn') (Join-Path 'scripts' 'gald3r_nightly_learn.ps1')
# D015 fallback: try legacy scripts/ location if .gald3r_sys/ path is missing
if (-not (Test-Path $helperScript)) {
    $helperScript = Join-Path (Join-Path $ProjectRoot 'scripts') 'gald3r_nightly_learn.ps1'
}
$logsDir      = Join-Path (Join-Path $ProjectRoot '.gald3r') 'logs'
$counterFile  = Join-Path $logsDir 'learn-counter'
$lastRunLog   = Join-Path $logsDir 'nightly-learn-last-run.log'
$configFile   = Join-Path (Join-Path (Join-Path $ProjectRoot '.gald3r') 'config') 'AGENT_CONFIG.md'
$heartbeat    = Join-Path (Join-Path (Join-Path $ProjectRoot '.gald3r') 'config') 'HEARTBEAT.md'

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# ---- Disable switch (HEARTBEAT.md `nightly_learn: false`) -----------------
if (Test-Path $heartbeat) {
    $hb = Get-Content $heartbeat -Raw
    if ($hb -match 'nightly_learn:\s*false') {
        # Cheap exit — do not increment counter when explicitly disabled.
        exit 0
    }
}

# ---- Read interval (default: every 5 sessions) ----------------------------
$interval = 5
if (Test-Path $configFile) {
    $cfg = Get-Content $configFile -Raw
    if ($cfg -match 'nightly_learn_interval:\s*(\d+)') {
        $candidate = [int]$matches[1]
        if ($candidate -gt 0) { $interval = $candidate }
    }
}

# ---- Counter (only fire every N sessions) ---------------------------------
$counter = 0
if (Test-Path $counterFile) {
    try { $counter = [int](Get-Content $counterFile -ErrorAction Stop) } catch { $counter = 0 }
}
$counter += 1

if (-not $Force -and $counter -lt $interval) {
    # Not yet time — bump counter and exit silently within a few ms.
    Set-Content -Path $counterFile -Value $counter -Encoding ASCII
    exit 0
}

# ---- Helper script existence check ----------------------------------------
if (-not (Test-Path $helperScript)) {
    "[$(Get-Date -Format o)] gald3r_nightly_learn.ps1 not found at $helperScript -- hook skipped." |
        Out-File -FilePath $lastRunLog -Encoding UTF8 -Append
    # Reset counter so a fixed helper doesn't immediately re-fire on next session.
    Set-Content -Path $counterFile -Value 0 -Encoding ASCII
    exit 0
}

# ---- Detached spawn of the heavy extraction work --------------------------
# Critical: WindowStyle Hidden + no -Wait + redirected stdout/stderr keep the
# hook non-blocking even when the helper takes minutes. PassThru gives us a
# PID for the diagnostic log.
$helperOut = Join-Path $logsDir 'nightly-learn-helper.out.log'
$helperErr = Join-Path $logsDir 'nightly-learn-helper.err.log'

try {
    $proc = Start-Process powershell.exe `
        -ArgumentList @(
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', $helperScript,
            '-ProjectRoot', $ProjectRoot,
            '-LookbackDays', '1'
        ) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $helperOut `
        -RedirectStandardError $helperErr `
        -PassThru

    # Reset counter on successful spawn.
    Set-Content -Path $counterFile -Value 0 -Encoding ASCII

    "[$(Get-Date -Format o)] spawned PID=$($proc.Id) helper=$helperScript counter_was=$counter interval=$interval" |
        Out-File -FilePath $lastRunLog -Encoding UTF8 -Append

    # Surface a one-line note to the agent's terminal; the heavy work runs detached.
    Write-Host "[g-hk-nightly-learn] background extraction queued (PID $($proc.Id)); see $lastRunLog" -ForegroundColor DarkCyan
} catch {
    "[$(Get-Date -Format o)] FAILED to spawn helper: $_" |
        Out-File -FilePath $lastRunLog -Encoding UTF8 -Append
    # Do not propagate the failure -- hooks must not block the agent's exit path.
    Write-Warning "[g-hk-nightly-learn] spawn failed: $_"
}

exit 0
