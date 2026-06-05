# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    Session-end hook (T1057): records structured session-end metadata and
    stages a memory-capture pending marker for the next agent session to action.

.DESCRIPTION
    Fires under the Cursor "stop" event alongside g-hk-agent-complete and
    g-hk-nightly-learn. Unlike those siblings (which write reflection hints
    and trigger N-session-rollup learning), this hook focuses exclusively on
    persisting a structured session-end record that the next session-start
    hook (or @g-learn / memory_capture_session) can act on.

    Why a separate hook from g-hk-agent-complete?
    - g-hk-agent-complete is heavy: it persists chat logs and writes
      reflection hints. Keeping the session-end marker write separate keeps
      the responsibility focused and lets either hook be disabled
      independently.
    - g-hk-nightly-learn batches N sessions and runs heavy LLM extraction.
      The per-session marker is the input the rollup eventually consumes.

    PowerShell hooks cannot invoke MCP tools directly (the MCP client is the
    chat agent, not the shell). The actual `memory_capture_session` call is
    deferred to T1263 — see TODO comment below. This hook stages the data
    that integration needs.

.PARAMETER ProjectRoot
    Override project-root detection (defaults to nearest .gald3r/ ancestor).
#>

[CmdletBinding()]
param([string] $ProjectRoot = '')

$ErrorActionPreference = 'SilentlyContinue'

# ── stdin payload (Cursor stop schema) ───────────────────────────────────────
$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

# ── Idempotency: do not re-write the marker if already done this session ────
if ($env:GALD3R_HK_SESSION_END_APPLIED -eq "1") {
    @{ continue = $true } | ConvertTo-Json -Compress
    exit 0
}
$env:GALD3R_HK_SESSION_END_APPLIED = "1"

# ── Locate project root ─────────────────────────────────────────────────────
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

# ── Parse stop payload ──────────────────────────────────────────────────────
$status = "unknown"; $loopCount = 0; $conversationId = ""; $transcriptPath = ""
try {
    $payload = $inputJson | ConvertFrom-Json
    if ($payload.status)          { $status         = $payload.status }
    if ($null -ne $payload.loop_count) { $loopCount     = $payload.loop_count }
    if ($payload.conversation_id) { $conversationId = $payload.conversation_id }
    if ($payload.transcript_path) { $transcriptPath = $payload.transcript_path }
} catch {}

# ── Read identity for project_id ────────────────────────────────────────────
$identityFile = Join-Path $ProjectRoot '.gald3r/.identity'
$projectId = ""; $projectName = ""
if (Test-Path $identityFile) {
    foreach ($line in (Get-Content $identityFile)) {
        if ($line -match '^project_id=(.+)$')   { $projectId   = $matches[1].Trim() }
        if ($line -match '^project_name=(.+)$') { $projectName = $matches[1].Trim() }
    }
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# ── Append a structured log line ────────────────────────────────────────────
$logLine = "{0} | session_end | status={1} | loop_count={2} | project={3} | conv={4}" -f `
    $timestamp, $status, $loopCount, $projectName, $conversationId
$logFile = Join-Path $logsDir 'session_end.log'
$logLine | Add-Content -Path $logFile -Encoding UTF8

# ── Stage memory-capture pending marker ─────────────────────────────────────
# TODO[T1057→T1263]: replace this marker pattern with an actual
# memory_capture_session MCP call once the gald3r agent CLI is wired into
# the hook execution chain (PS shells cannot call MCP tools directly).
$markerFile = Join-Path $logsDir 'session_end_pending.json'
$marker = @{
    timestamp        = $timestamp
    project_id       = $projectId
    project_name     = $projectName
    conversation_id  = $conversationId
    transcript_path  = $transcriptPath
    status           = $status
    loop_count       = $loopCount
    capture_pending  = $true
    deferred_to      = "T1263"
}
try {
    $marker | ConvertTo-Json -Depth 4 | Set-Content -Path $markerFile -Encoding UTF8
} catch {}

# ── Non-blocking: never delay session close ─────────────────────────────────
@{
    continue           = $true
    additional_context = "[session-end] Marker staged. Memory capture wiring deferred to T1263."
} | ConvertTo-Json -Compress
exit 0
