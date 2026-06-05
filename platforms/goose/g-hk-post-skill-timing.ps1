# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    Example post_skill lifecycle hook (T1055): closes the skill-invocation
    timing record opened by g-hk-pre-skill-timing and logs elapsed duration.

.DESCRIPTION
    Fires on the gald3r-internal "post_skill" lifecycle event, immediately after
    a gald3r skill body finishes. Like pre_skill, post_skill is a gald3r-internal
    lifecycle point (no native Cursor / Claude Code skill-boundary event exists):
    it is dispatched by the gald3r skill/command runner or fired manually. The
    payload arrives on stdin as JSON and SHOULD include skill_name, skill_path,
    and timestamp.

    This is a reference example: it is non-blocking. It reads the start marker
    staged by g-hk-pre-skill-timing, computes elapsed milliseconds, and appends
    a timing line. If no start marker is found it logs duration as unknown.

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
$nowMs = [long]([DateTimeOffset]$now).ToUnixTimeMilliseconds()

# -- Read the start marker and compute elapsed --------------------------------
$elapsedMs = "unknown"
$markerFile = Join-Path $logsDir ("skill_timing_" + ($skillName -replace '[^A-Za-z0-9_-]','_') + ".json")
if (Test-Path $markerFile) {
    try {
        $start = Get-Content $markerFile -Raw | ConvertFrom-Json
        if ($null -ne $start.epoch_ms) {
            $elapsedMs = [long]($nowMs - [long]$start.epoch_ms)
        }
        Remove-Item $markerFile -Force
    } catch {}
}

# -- Append a structured log line ---------------------------------------------
$logLine = "{0} | post_skill | skill={1} | elapsed_ms={2}" -f $timestamp, $skillName, $elapsedMs
$logLine | Add-Content -Path (Join-Path $logsDir 'skill_lifecycle.log') -Encoding UTF8

# -- Non-blocking -------------------------------------------------------------
@{
    continue           = $true
    additional_context = "[post_skill] $skillName finished (elapsed_ms=$elapsedMs)."
} | ConvertTo-Json -Compress
exit 0
