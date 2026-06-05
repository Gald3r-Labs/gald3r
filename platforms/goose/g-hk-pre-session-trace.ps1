# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    Example pre_session lifecycle hook (T1055): records a session-start trace
    marker for richer per-session observability.

.DESCRIPTION
    Fires on the gald3r-internal "pre_session" lifecycle event at the very start
    of a gald3r work session. This is a gald3r-internal lifecycle point distinct
    from the harness-native sessionStart event: pre_session is the gald3r-level
    boundary (dispatched by the skill/command runner or fired manually), whereas
    sessionStart is the IDE harness boundary that wires g-hk-session-start.ps1.
    Keeping them separate lets gald3r trace session lifecycle independent of
    which harness (Cursor / Claude / CLI) launched the session.

    The payload arrives on stdin as JSON and SHOULD include session_id (if
    available) and project_path (see T1055 Implementation Notes).

    This is a reference example: it is non-blocking and only stages a session
    start record so the companion post_session hook can compute session duration.

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
if (-not $sessionId) { $sessionId = $now.ToString('yyyyMMddHHmmss') }

# -- Stage a per-session start marker (keyed by session id) -------------------
$startMarker = @{
    session_id   = $sessionId
    project_path = if ($projectPath) { $projectPath } else { $ProjectRoot }
    started_at   = $timestamp
    epoch_ms     = [long]([DateTimeOffset]$now).ToUnixTimeMilliseconds()
}
$markerFile = Join-Path $logsDir ("session_trace_" + ($sessionId -replace '[^A-Za-z0-9_-]','_') + ".json")
try {
    $startMarker | ConvertTo-Json -Depth 4 | Set-Content -Path $markerFile -Encoding UTF8
} catch {}

# -- Append a structured log line ---------------------------------------------
$logLine = "{0} | pre_session | session={1} | project={2}" -f $timestamp, $sessionId, $ProjectRoot
$logLine | Add-Content -Path (Join-Path $logsDir 'session_lifecycle.log') -Encoding UTF8

# -- Non-blocking: never delay session start ----------------------------------
@{
    continue           = $true
    additional_context = "[pre_session] session $sessionId start recorded."
} | ConvertTo-Json -Compress
exit 0
