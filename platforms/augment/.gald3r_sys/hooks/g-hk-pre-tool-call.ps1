# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    Pre-tool-call shell output compression hook (T1106, IDEA-HARVEST-191).

.DESCRIPTION
    Fires under the PreToolUse / preToolUse event. Inspects the incoming tool
    event payload for any large stdout/stderr/output text block and compresses
    it to the last N lines plus a summary prefix, returning the compressed form
    as additional_context. This cuts context bloat from heavy CLI sessions
    (community pattern reports 60-90% token reduction in shell-heavy runs).

    Compression is non-destructive: the FULL original block is preserved to
    .gald3r/logs/tool_output_<session_id>.log before the compressed summary is
    emitted, so nothing is lost.

    Compression strategy:
      - Read N from .gald3r/config/AGENT_CONFIG.md field
        pre_tool_call_compress_lines (default 50; 0 = disabled).
      - For each output block whose line count exceeds N, keep the last N lines
        and prepend:
          ... [<total> lines compressed, last <N> shown -- run ID: <id>] ...
      - Error/warning lines anywhere in the block are surfaced in the summary so
        signal is preserved even when truncated.

    Harness contract note (achievable scope): a PowerShell PreToolUse hook
    receives the upcoming tool-call JSON on stdin and returns an allow verdict
    plus additional_context. It cannot retroactively rewrite terminal output
    blocks already rendered in the agent's context window -- only the harness
    can splice additional_context. Where the harness supplies prior/preview
    output on the event payload, this hook compresses it; where it does not,
    the hook is a safe no-op (permission=allow, exit 0). This is the documented
    gap (see companion hook.md ## Side Effects).

    Always non-blocking: this hook NEVER denies a tool call. On any parse error,
    missing field, disabled config, or short output it emits permission=allow
    and exits 0.

.PARAMETER ProjectRoot
    Override project-root detection (defaults to nearest .gald3r/ ancestor).
#>

[CmdletBinding()]
param([string] $ProjectRoot = '')

$ErrorActionPreference = 'SilentlyContinue'

# -- Always-allow helper ------------------------------------------------------
function Emit-Allow([string] $context) {
    if ($context) {
        @{ permission = 'allow'; additional_context = $context } | ConvertTo-Json -Compress
    } else {
        @{ permission = 'allow' } | ConvertTo-Json -Compress
    }
    exit 0
}

# -- stdin payload (PreToolUse event schema) ----------------------------------
$raw = ''
if ([Console]::IsInputRedirected) {
    try { $raw = [Console]::In.ReadToEnd() } catch {}
}
# NOTE: do NOT add a `$input | Out-String` fallback here — referencing $input in a
# [CmdletBinding()] script pre-binds the pipeline and drains [Console]::In before the
# read above, making the hook a no-op under `powershell -File` (the wired invocation). (T1106)
if (-not $raw) { Emit-Allow '' }

$event = $null
try { $event = $raw | ConvertFrom-Json } catch { Emit-Allow '' }
if (-not $event) { Emit-Allow '' }

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

# -- Read N from AGENT_CONFIG.md (default 50; 0 = disabled) --------------------
$maxLines  = 50
$configFile = Join-Path (Join-Path (Join-Path $ProjectRoot '.gald3r') 'config') 'AGENT_CONFIG.md'
if (Test-Path $configFile) {
    $cfg = Get-Content $configFile -Raw -ErrorAction SilentlyContinue
    if ($cfg -match 'pre_tool_call_compress_lines:\s*(\d+)') {
        $maxLines = [int]$matches[1]
    }
}
if ($maxLines -le 0) {
    # Explicitly disabled -- pure no-op.
    Emit-Allow ''
}

# -- Find a large output text block on the event payload ----------------------
# The harness may attach prior/preview output under several field names. Probe
# both top-level fields and the tool_input/tool_response sub-objects.
function Get-FieldValue($obj, [string] $name) {
    if ($null -eq $obj) { return $null }
    if ($obj.PSObject.Properties[$name]) { return [string]$obj.$name }
    return $null
}

$candidateFields = @('output', 'stdout', 'stderr', 'tool_output', 'result', 'text')
$block = $null
foreach ($f in $candidateFields) {
    $v = Get-FieldValue $event $f
    if ($v) { $block = $v; break }
}
if (-not $block -and $event.tool_response) {
    foreach ($f in $candidateFields) {
        $v = Get-FieldValue $event.tool_response $f
        if ($v) { $block = $v; break }
    }
}
if (-not $block -and $event.tool_input) {
    foreach ($f in $candidateFields) {
        $v = Get-FieldValue $event.tool_input $f
        if ($v) { $block = $v; break }
    }
}

if (-not $block) { Emit-Allow '' }

# -- Split into lines and decide whether compression is warranted -------------
$lines = $block -split "`r?`n"
$total = $lines.Count
if ($total -le $maxLines) {
    # Already small enough -- nothing to compress.
    Emit-Allow ''
}

# -- Session/run id (stable per session when provided, else random) -----------
$sessionId = ''
foreach ($k in @('session_id', 'sessionId', 'conversation_id', 'run_id')) {
    $sv = Get-FieldValue $event $k
    if ($sv) { $sessionId = $sv; break }
}
if (-not $sessionId) {
    $sessionId = ([guid]::NewGuid().ToString('N').Substring(0, 8))
}
$runId = ([guid]::NewGuid().ToString('N').Substring(0, 6))

# -- Preserve full output to .gald3r/logs/ BEFORE compressing -----------------
$logsDir = Join-Path (Join-Path $ProjectRoot '.gald3r') 'logs'
try {
    if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
    $safeSession = ($sessionId -replace '[^A-Za-z0-9_-]', '_')
    $logFile = Join-Path $logsDir ("tool_output_{0}.log" -f $safeSession)
    $header  = "===== run {0} | {1} | {2} lines =====" -f $runId, ((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')), $total
    Add-Content -Path $logFile -Value $header -Encoding UTF8
    Add-Content -Path $logFile -Value $block  -Encoding UTF8
} catch {}

# -- Surface error/warning signal even when truncated -------------------------
$signalLines = @()
foreach ($ln in $lines) {
    if ($ln -match '(?i)\b(error|warning|fatal|exception|fail(ed|ure)?|traceback|denied)\b') {
        $signalLines += $ln.Trim()
    }
}
$signalLines = $signalLines | Select-Object -First 10

# -- Build compressed block: summary prefix + last N lines --------------------
$tail = $lines | Select-Object -Last $maxLines
$compressedCount = $total - $maxLines
$prefix = "... [{0} lines compressed, last {1} shown -- run ID: {2}] ..." -f $compressedCount, $maxLines, $runId

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine($prefix)
if ($signalLines.Count -gt 0) {
    [void]$sb.AppendLine("[signal lines preserved from compressed region:]")
    foreach ($s in $signalLines) { [void]$sb.AppendLine("  $s") }
}
foreach ($t in $tail) { [void]$sb.AppendLine($t) }
[void]$sb.AppendLine("[full output: .gald3r/logs/tool_output_${sessionId}.log]")

Emit-Allow ($sb.ToString())
