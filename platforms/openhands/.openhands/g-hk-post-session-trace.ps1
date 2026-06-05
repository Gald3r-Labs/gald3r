# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    Example post_session lifecycle hook (T1055): closes the session trace record
    opened by g-hk-pre-session-trace and logs total session duration.

.DESCRIPTION
    Fires on the gald3r-internal "post_session" lifecycle event at the very end
    of a gald3r work session. Like pre_session, this is a gald3r-internal
    lifecycle point distinct from the harness-native stop event (which wires
    g-hk-session-end.ps1). Keeping them separate lets gald3r close its own
    session trace independent of which harness emitted the stop.

    The payload arrives on stdin as JSON and SHOULD include session_id (if
    available) and project_path.

    This is a reference example: it is non-blocking. It reads the start marker
    staged by g-hk-pre-session-trace, computes elapsed milliseconds, and appends
    a duration line. If no start marker is found it logs duration as unknown.

.PARAMETER ProjectRoot
    Override project-root detection (defaults to nearest .gald3r/ ancestor).
#>

[CmdletBinding()]
param([string] $ProjectRoot = '')

$ErrorActionPreference = 'SilentlyContinue'

# -- stdin payload (gald3r session-event schema) ------------------------------
$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

$sessionId = ""; $projectPath = ""
try {
    $payload = $inputJson | ConvertFrom-Json
    if ($payload.session_id)   { $sessionId   = $payload.session_id }
    if ($payload.project_path) { $projectPath = $payload.project_path }
} catch {}

# -- Locate project root ------------------------------------------------------
if (-not $ProjectRoot) {
    if ($projectPath -and (Test-Path (Join-Path $projectPath '.gald3r'))) {
        $ProjectRoot = $projectPath
    } else {
        $dir = $PSScriptRoot
        while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
            $parent = Split-Path $dir -Parent
            if ($parent -eq $dir) { $dir = ''; break }
            $dir = $parent
        }
        $ProjectRoot = if ($dir) { $dir } else { (Get-Location).Path }
    }
}

$logsDir = Join-Path $ProjectRoot '.gald3r/logs'
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

$now = (Get-Date).ToUniversalTime()
$timestamp = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')
$nowMs = [long]([DateTimeOffset]$now).ToUnixTimeMilliseconds()

# -- Read the start marker and compute elapsed --------------------------------
$elapsedMs = "unknown"
if ($sessionId) {
    $markerFile = Join-Path $logsDir ("session_trace_" + ($sessionId -replace '[^A-Za-z0-9_-]','_') + ".json")
    if (Test-Path $markerFile) {
        try {
            $start = Get-Content $markerFile -Raw | ConvertFrom-Json
            if ($null -ne $start.epoch_ms) {
                $elapsedMs = [long]($nowMs - [long]$start.epoch_ms)
            }
            Remove-Item $markerFile -Force
        } catch {}
    }
} else {
    $sessionId = "unknown"
}

# -- Append a structured log line ---------------------------------------------
$logLine = "{0} | post_session | session={1} | elapsed_ms={2}" -f $timestamp, $sessionId, $elapsedMs
$logLine | Add-Content -Path (Join-Path $logsDir 'session_lifecycle.log') -Encoding UTF8

# -- Non-blocking -------------------------------------------------------------
@{
    continue           = $true
    additional_context = "[post_session] session $sessionId finished (elapsed_ms=$elapsedMs)."
} | ConvertTo-Json -Compress
exit 0
