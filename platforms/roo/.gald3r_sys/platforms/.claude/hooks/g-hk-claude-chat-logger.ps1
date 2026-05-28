# g-hk-claude-chat-logger.ps1 — Claude Code Stop hook for chat logging (BUG-091)
#
# Mirrors the Cursor logging flow (g-hk-agent-complete.ps1 -> g-hk-cursor-chat-logger.py)
# for Claude Code. Claude fires the "Stop" event with a JSON payload on stdin that
# includes the session transcript path, so this wrapper just locates Python and the
# project root, then hands the transcript to g-hk-claude-chat-logger.py.
#
# Claude Stop payload (snake_case): { session_id, transcript_path, cwd,
#   hook_event_name, stop_hook_active }. We also read camelCase defensively.
#
# Guard stdin with IsInputRedirected before ReadToEnd() so the script never blocks
# when run from a console rather than a pipe (BUG-003 pattern).

$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

# ── Resolve project root: prefer payload cwd, else walk up from script to .gald3r ──
function Resolve-ProjectRoot {
    param([string] $StartDir)
    $dir = $StartDir
    while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { return $null }
        $dir = $parent
    }
    return $dir
}

$transcriptPath = $null
$sessionId      = $null
$cwd            = $null
try {
    $payload = $inputJson | ConvertFrom-Json
    if ($payload.transcript_path) { $transcriptPath = $payload.transcript_path }
    elseif ($payload.transcriptPath) { $transcriptPath = $payload.transcriptPath }
    if ($payload.session_id) { $sessionId = $payload.session_id }
    elseif ($payload.sessionId) { $sessionId = $payload.sessionId }
    if ($payload.cwd) { $cwd = $payload.cwd }
} catch {}

# --- Platform-detection guard (T1455) ----------------------------------------
# A genuine Claude Code Stop event always carries a JSON payload on stdin with at
# least a transcript_path (and normally session_id / cwd). When this hook is
# invoked outside a real Claude Stop context (e.g. a non-Claude IDE such as Cursor
# triggering the workspace Stop wiring, or a Stop fired with no/empty stdin), the
# payload is empty and every field is null. In that case this is NOT a Claude
# session, so exit silently WITHOUT writing diagnostic noise to hook_diag.log.
# (ASCII-only strings per g-rl-08; this guard removes the false-fire log spam.)
if (-not $transcriptPath -and -not $sessionId -and -not $cwd) {
    '{}' ; exit 0
}

$projectRoot = $null
if ($cwd) { $projectRoot = Resolve-ProjectRoot -StartDir $cwd }
if (-not $projectRoot) { $projectRoot = Resolve-ProjectRoot -StartDir $PSScriptRoot }
if (-not $projectRoot) { $projectRoot = (Get-Location).Path }

# ── Diagnostic log (fires unconditionally — proves the hook ran) ──────────────
$diagLog = Join-Path $projectRoot ".gald3r/logs/hook_diag.log"
try {
    $logsDir = Join-Path $projectRoot ".gald3r/logs"
    if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') claude-chat-logger fired, session=$sessionId transcript=$transcriptPath" |
        Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
} catch {}

if (-not $transcriptPath -or -not (Test-Path $transcriptPath)) {
    try {
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') claude-chat-logger: no usable transcript_path; skipping" |
            Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {}
    '{}' ; exit 0
}

# ── Locate Python (mirror the Cursor wrapper's py/python/python3 probe) ───────
$loggerScript = Join-Path $PSScriptRoot "g-hk-claude-chat-logger.py"
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue)            { $pythonCmd = "py";      $pyPrefix = @("-3") }
elseif (Get-Command python -ErrorAction SilentlyContinue)    { $pythonCmd = "python";  $pyPrefix = @() }
elseif (Get-Command python3 -ErrorAction SilentlyContinue)   { $pythonCmd = "python3"; $pyPrefix = @() }

if ($pythonCmd -and (Test-Path $loggerScript)) {
    $pyArgs = @()
    $pyArgs += $pyPrefix
    $pyArgs += @(
        $loggerScript,
        "--transcript-path", $transcriptPath,
        "--project-path",    $projectRoot,
        "--platform",        "claude",
        "--status",          "completed"
    )
    if ($sessionId) { $pyArgs += @("--conversation-id", $sessionId) }

    try {
        $out = & $pythonCmd @pyArgs 2>&1
        $code = $LASTEXITCODE
        if ($code -eq 0) {
            "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') claude-chat-logger OK: chat log written" |
                Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
        } else {
            "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') claude-chat-logger exit=$code : $out" |
                Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
        }
    } catch {
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') claude-chat-logger launch error: $_" |
            Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
    }
} else {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') claude-chat-logger: python or logger script missing (py=$pythonCmd script=$loggerScript)" |
        Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
}

# Non-blocking: never alter the Stop decision.
'{}'
exit 0
