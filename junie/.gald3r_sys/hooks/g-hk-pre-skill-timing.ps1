# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    Example pre_skill lifecycle hook (T1055): records a skill-invocation start
    marker for per-skill timing and tracing.

.DESCRIPTION
    Fires on the gald3r-internal "pre_skill" lifecycle event, immediately before
    a gald3r skill body executes. Cursor and Claude Code do NOT expose a native
    skill-boundary event, so pre_skill is a gald3r-internal lifecycle point:
    it is dispatched by the gald3r skill/command runner (or fired manually /
    by future harness support) rather than auto-wired into hooks.json under a
    harness event name. The payload arrives on stdin as JSON and SHOULD include
    skill_name, skill_path, and timestamp (see Implementation Notes in T1055).

    This is a reference example: it is non-blocking and only stages a start
    record so the companion post_skill hook can compute elapsed time.

.PARAMETER ProjectRoot
    Override project-root detection (defaults to nearest .gald3r/ ancestor).
#>

[CmdletBinding()]
param([string] $ProjectRoot = '')

$ErrorActionPreference = 'SilentlyContinue'

# -- stdin payload (gald3r skill-event schema) --------------------------------
$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

$skillName = "unknown"; $skillPath = ""; $eventTimestamp = ""
try {
    $payload = $inputJson | ConvertFrom-Json
    if ($payload.skill_name) { $skillName      = $payload.skill_name }
    if ($payload.skill_path) { $skillPath      = $payload.skill_path }
    if ($payload.timestamp)  { $eventTimestamp = $payload.timestamp }
} catch {}

# -- Locate project root ------------------------------------------------------
if (-not $ProjectRoot) {
    $dir = $PSScriptRoot
    while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { $dir = ''; break }
        $dir = $parent
    }
    $ProjectRoot = if ($dir) { $dir } else { (Get-Location).Path }
}

$logsDir = Join-Path $ProjectRoot '.gald3r/logs'
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

$now = (Get-Date).ToUniversalTime()
$timestamp = if ($eventTimestamp) { $eventTimestamp } else { $now.ToString('yyyy-MM-ddTHH:mm:ssZ') }

# -- Stage a per-skill start marker (keyed by skill name) ---------------------
$startMarker = @{
    skill_name = $skillName
    skill_path = $skillPath
    started_at = $timestamp
    epoch_ms   = [long]([DateTimeOffset]$now).ToUnixTimeMilliseconds()
}
$markerFile = Join-Path $logsDir ("skill_timing_" + ($skillName -replace '[^A-Za-z0-9_-]','_') + ".json")
try {
    $startMarker | ConvertTo-Json -Depth 4 | Set-Content -Path $markerFile -Encoding UTF8
} catch {}

# -- Append a structured log line ---------------------------------------------
$logLine = "{0} | pre_skill | skill={1} | path={2}" -f $timestamp, $skillName, $skillPath
$logLine | Add-Content -Path (Join-Path $logsDir 'skill_lifecycle.log') -Encoding UTF8

# -- Non-blocking: never delay skill execution --------------------------------
@{
    continue           = $true
    additional_context = "[pre_skill] $skillName start recorded."
} | ConvertTo-Json -Compress
exit 0
