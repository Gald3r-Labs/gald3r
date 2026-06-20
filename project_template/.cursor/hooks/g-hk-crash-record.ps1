# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    CRASH activation recorder hook (T433): appends one activation record to
    .gald3r/logs/crash_activations.jsonl for the manual/heuristic recording path.

.DESCRIPTION
    CRASH = Commands, Rules, Agents, Skills, Hooks. The engine auto-records every
    *Command* it dispatches (see gald3r.crash + adapters/cli.py). IDE harnesses
    (Cursor / Claude Code) do NOT emit a discrete event for every Rule / Skill /
    Agent / Hook activation, so this hook is the explicit recording path for those:
    a hook event, the gald3r skill/command runner, or an agent invokes it with a
    payload describing the component that just activated.

    Rule "activation" in particular has no native event — rules are always-loaded
    context — so a faithful "rule fired" signal must be reported explicitly here.

    The payload arrives on stdin as JSON and SHOULD include:
        component_type   one of: command | rule | agent | skill | hook
        component_name   e.g. g-skl-tasks, g-rl-00-always, g-hk-encoding-normalize
        trigger_source   what triggered it (a command/rule/hook/agent name)
        elapsed_ms        optional duration
        session_id        optional; falls back to GALD3R_SESSION_ID / a per-proc id

    Zero overhead when disabled: if GALD3R_CRASH_STATS is unset or 'off', this hook
    records nothing and returns immediately (matches the engine's hot-path gate).
    Non-blocking by design — never delays the event it observes.

.PARAMETER ProjectRoot
    Override project-root detection (defaults to nearest .gald3r/ ancestor).
#>

[CmdletBinding()]
param([string] $ProjectRoot = '')

$ErrorActionPreference = 'SilentlyContinue'

# -- Zero-overhead gate: only record when CRASH stats are enabled --------------
$mode = ($env:GALD3R_CRASH_STATS).ToString().Trim().ToLower()
if ($mode -ne 'show_in_response' -and $mode -ne 'show_in_log' -and $mode -ne 'show_in_terminal') {
    @{ continue = $true } | ConvertTo-Json -Compress
    exit 0
}

# -- stdin payload (gald3r CRASH-event schema) --------------------------------
$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

$componentType = "skill"; $componentName = "unknown"; $triggerSource = ""
$elapsedMs = $null; $payloadSession = ""
try {
    $payload = $inputJson | ConvertFrom-Json
    if ($payload.component_type) { $componentType = ([string]$payload.component_type).Trim().ToLower() }
    if ($payload.component_name) { $componentName = [string]$payload.component_name }
    if ($payload.trigger_source) { $triggerSource = [string]$payload.trigger_source }
    if ($null -ne $payload.elapsed_ms) { $elapsedMs = $payload.elapsed_ms }
    if ($payload.session_id)     { $payloadSession = [string]$payload.session_id }
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

# -- Session id (harness id if exported, else a per-process fallback) ---------
$sessionId = $payloadSession
if (-not $sessionId) { $sessionId = $env:GALD3R_SESSION_ID }
if (-not $sessionId) { $sessionId = $env:CURSOR_CONVERSATION_ID }
if (-not $sessionId) { $sessionId = "proc-" + ([guid]::NewGuid().ToString('N').Substring(0, 12)) }

$activatedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# -- Append one JSONL record (schema matches gald3r.crash.ActivationRecord) ----
$record = [ordered]@{
    component_type = $componentType
    component_name = $componentName
    activated_at   = $activatedAt
    session_id     = $sessionId
    trigger_source = $triggerSource
    elapsed_ms     = $elapsedMs
}
try {
    $line = $record | ConvertTo-Json -Compress
    $logFile = Join-Path $logsDir 'crash_activations.jsonl'
    Add-Content -Path $logFile -Value $line -Encoding UTF8
} catch {}

# -- Non-blocking: never delay the observed event ------------------------------
@{
    continue           = $true
    additional_context = "[crash-record] $componentType/$componentName recorded."
} | ConvertTo-Json -Compress
exit 0
