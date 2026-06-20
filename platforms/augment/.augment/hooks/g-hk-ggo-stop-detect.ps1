# @subsystems: TASK_MANAGEMENT
<#
.SYNOPSIS
    g-go-go stop-detection re-invoke hook (T1444, BUG-107 Fix Direction #2).

.DESCRIPTION
    Fires under the "stop" event. Detects when a g-go-go autopilot run halts
    mid-loop WITHOUT quoting an authorizing hard-stop row, and forces the loop
    to continue by emitting a re-invoke decision plus a verbatim reminder of the
    forbidden stop reasons. This makes the BUG-107 "disguised context-panic stop"
    contract mechanically self-enforcing instead of prose-only.

    Platform + session isolation (cross-agent safety):
      Platform is determined from $PSScriptRoot at runtime -- the same script is
      deployed to all platform hook folders; the folder path tells us who is calling:
        .cursor/hooks     -> "cursor"
        .claude/hooks     -> "claude"
        .windsurf/        -> "windsurf"
        .codex/           -> "codex"
        .agent/hooks      -> "gemini"
        .agents/          -> "antigravity"
        .openhands/       -> "openhands"
        .codebuddy/       -> "codebuddy"
        .kiro/hooks       -> "kiro"
        .kiro-cli/hooks   -> "kiro-cli"
        (anything else)   -> "claude"

      A stored run owned by a DIFFERENT platform or DIFFERENT session is NEVER
      re-invoked -- the hook allows those stops through immediately. This prevents
      a Cursor agent from being caught in a Claude Code g-go-go loop (or vice
      versa) and prevents a fresh chat session from inheriting a stale run.

    First-touch session registration:
      The g-go-go INIT write includes "platform" but not "session_id" (the agent
      does not have the session ID at INIT time). On the FIRST stop the hook sees
      for an active run without a stored session_id, it captures the ID from the
      stop-event stdin payload and writes it into the state file. All subsequent
      stops compare against it.

    State machine (file-first, no backend):
      The g-go-go command writes a run-state marker at INIT and refreshes it each
      iteration: .gald3r/logs/ggo_run_state.json with fields:
        { "active": true, "platform": "<platform>",
          "session_id": "<uuid>" (written on first stop),
          "iter": N, "budget_remaining": B,
          "authorized_hard_stop": "" | "<verbatim hard-stop row>",
          "reinvoke_count": R, "updated_at": "<iso>" }

      On stop, this hook:
        0. No active run            -> no-op (continue, exit 0).
        1. Platform mismatch        -> allow exit (different agent's run).
        2. Session mismatch         -> allow exit (different chat session).
        3. authorized_hard_stop set -> genuine hard stop; allow exit, clear marker.
        4. budget exhausted         -> allow exit (the budget cap IS a hard stop).
        5. re-invoke ceiling hit    -> allow exit (anti-infinite-loop fail-safe).
        6. otherwise (unauthorized) -> re-invoke: increment reinvoke_count, emit
           block/continue decision with the forbidden-reason reminder.

    Bounding guarantees (Acceptance Criterion #3):
      - reinvoke_count never exceeds budget_remaining, and is independently
        capped by GGO_REINVOKE_CEILING so it can never infinite-loop.
      - A genuine hard stop (authorized_hard_stop populated) is NEVER re-invoked.
      - Budget exhaustion is treated as a hard stop and is NEVER re-invoked.
      - Platform or session mismatch is always allowed through, never re-invoked.

    PowerShell stop hooks cannot literally re-prompt an LLM; the re-invoke is
    expressed through the platform stop-hook continuation contract on stdout:
      - Claude Code Stop hook : {"decision":"block","reason":"<reminder>"}
      - Cursor stop hook      : {"continue":false,"followup":"<reminder>"}
    Both schemas are emitted together; each platform ignores the foreign keys.

.PARAMETER ProjectRoot
    Override project-root detection (defaults to nearest .gald3r/ ancestor).
#>

[CmdletBinding()]
param([string] $ProjectRoot = '')

$ErrorActionPreference = 'SilentlyContinue'

# Hard ceiling on re-invokes regardless of budget (anti-infinite-loop fail-safe).
$GGO_REINVOKE_CEILING = 25

# -- Detect calling platform from script location --------------------------------
# The same script is deployed to every platform's hook folder; $PSScriptRoot
# tells us which platform is invoking it at runtime.
$scriptDir = "$PSScriptRoot\"
$currentPlatform = switch -Wildcard ($scriptDir) {
    '*\.cursor\*'     { 'cursor';      break }
    '*/.cursor/*'     { 'cursor';      break }
    '*\.windsurf\*'   { 'windsurf';    break }
    '*/.windsurf/*'   { 'windsurf';    break }
    '*\.codex\*'      { 'codex';       break }
    '*/.codex/*'      { 'codex';       break }
    '*\.kiro-cli\*'   { 'kiro-cli';    break }
    '*/.kiro-cli/*'   { 'kiro-cli';    break }
    '*\.kiro\*'       { 'kiro';        break }
    '*/.kiro/*'       { 'kiro';        break }
    '*\.openhands\*'  { 'openhands';   break }
    '*/.openhands/*'  { 'openhands';   break }
    '*\.codebuddy\*'  { 'codebuddy';   break }
    '*/.codebuddy/*'  { 'codebuddy';   break }
    '*\.agents\*'     { 'antigravity'; break }
    '*/.agents/*'     { 'antigravity'; break }
    '*\.agent\*'      { 'gemini';      break }
    '*/.agent/*'      { 'gemini';      break }
    default           { 'claude' }
}

# -- stdin payload (stop event schema) ------------------------------------------
$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

# -- Extract session_id from stop-event payload ----------------------------------
$currentSessionId = ''
if ($inputJson) {
    try {
        $payload = $inputJson | ConvertFrom-Json
        # Claude Code stop payload: { session_id, transcript_path, stop_hook_active }
        if ($payload.session_id) {
            $currentSessionId = [string]$payload.session_id
        }
        # Fallback: derive UUID from transcript_path filename pattern
        # e.g. .gald3r/logs/20260607_b24090d8-9d3a-4f83_claude_chat.jsonl
        if (-not $currentSessionId -and $payload.transcript_path) {
            if ($payload.transcript_path -match '[\\\/]\d{8}_([0-9a-f]{8}-[0-9a-f-]+)') {
                $currentSessionId = $Matches[1]
            }
        }
    } catch {}
}

# -- Locate project root ---------------------------------------------------------
if (-not $ProjectRoot) {
    $dir = $PSScriptRoot
    while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { $dir = ''; break }
        $dir = $parent
    }
    $ProjectRoot = if ($dir) { $dir } else { (Get-Location).Path }
}

$logsDir   = Join-Path $ProjectRoot '.gald3r/logs'
$stateFile = Join-Path $logsDir 'ggo_run_state.json'
$diagLog   = Join-Path $logsDir 'hook_diag.log'

function Write-Diag([string] $msg) {
    try {
        if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ggo-stop-detect [$currentPlatform]: $msg" |
            Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {}
}

# Allow-exit response: g-go-go run is not being held open by this hook.
function Emit-AllowExit([string] $context) {
    @{
        continue           = $true
        additional_context = $context
    } | ConvertTo-Json -Compress
    exit 0
}

# Case 0: no active run marker -> this stop is unrelated to g-go-go. No-op.
if (-not (Test-Path $stateFile)) {
    Emit-AllowExit "[ggo-stop-detect] No active g-go-go run; stop allowed."
}

# Read + parse the run-state marker.
$state = $null
try {
    $raw = Get-Content -Path $stateFile -Raw -ErrorAction Stop
    $state = $raw | ConvertFrom-Json
} catch {
    Write-Diag "unreadable/invalid state marker; allowing exit"
    Emit-AllowExit "[ggo-stop-detect] Run-state marker unreadable; stop allowed."
}

$active = $false
if ($state.PSObject.Properties.Name -contains 'active') { $active = [bool]$state.active }
if (-not $active) {
    Emit-AllowExit "[ggo-stop-detect] g-go-go run not active; stop allowed."
}

# -- Case 1: Platform mismatch -- a different agent owns this run. Allow exit. ---
$storedPlatform = ''
if ($state.PSObject.Properties.Name -contains 'platform') { $storedPlatform = [string]$state.platform }

if ($storedPlatform -and $storedPlatform -ne $currentPlatform) {
    Write-Diag "platform mismatch (stored=$storedPlatform current=$currentPlatform); allowing exit"
    Emit-AllowExit "[ggo-stop-detect] Platform mismatch: '$storedPlatform' owns this run, '$currentPlatform' is stopping — stop allowed."
}

# -- Case 2: Session mismatch -- a different chat instance. Allow exit. ----------
$storedSessionId = ''
if ($state.PSObject.Properties.Name -contains 'session_id') { $storedSessionId = [string]$state.session_id }

if ($storedSessionId -and $currentSessionId -and $storedSessionId -ne $currentSessionId) {
    Write-Diag "session_id mismatch (stored=$storedSessionId current=$currentSessionId); allowing exit"
    Emit-AllowExit "[ggo-stop-detect] Session mismatch: run owned by session '$storedSessionId', stopping session is '$currentSessionId' — stop allowed."
}

# -- First-touch session registration (no session_id stored yet) -----------------
# The g-go-go INIT write does not have the session_id; the first stop captures it.
if (-not $storedSessionId -and $currentSessionId) {
    try {
        $state | Add-Member -NotePropertyName 'session_id' -NotePropertyValue $currentSessionId -Force
        # Also backfill platform if INIT did not write it.
        if (-not $storedPlatform) {
            $state | Add-Member -NotePropertyName 'platform' -NotePropertyValue $currentPlatform -Force
        }
        $state | Add-Member -NotePropertyName 'updated_at' -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) -Force
        $state | ConvertTo-Json -Depth 6 | Set-Content -Path $stateFile -Encoding UTF8
        Write-Diag "first-touch: registered session_id=$currentSessionId platform=$currentPlatform"
    } catch {
        Write-Diag "first-touch registration failed (non-fatal): $_"
    }
}

$iter            = 0;  if ($null -ne $state.iter)             { $iter            = [int]$state.iter }
$budgetRemaining = 0;  if ($null -ne $state.budget_remaining) { $budgetRemaining = [int]$state.budget_remaining }
$reinvokeCount   = 0;  if ($null -ne $state.reinvoke_count)   { $reinvokeCount   = [int]$state.reinvoke_count }
$hardStop        = ""; if ($state.authorized_hard_stop)       { $hardStop        = [string]$state.authorized_hard_stop }

# Case 3: a genuine, authorized hard stop was recorded. Never re-invoke.
if ($hardStop.Trim().Length -gt 0) {
    Write-Diag "authorized hard stop recorded (`"$hardStop`"); allowing exit and clearing marker"
    try { Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue } catch {}
    Emit-AllowExit "[ggo-stop-detect] Authorized hard stop ($hardStop); stop allowed."
}

# Case 4: budget exhausted -> the budget cap itself is a hard stop. Never re-invoke.
if ($budgetRemaining -le 0) {
    Write-Diag "budget exhausted (budget_remaining=$budgetRemaining); allowing exit and clearing marker"
    try { Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue } catch {}
    Emit-AllowExit "[ggo-stop-detect] Run budget exhausted; stop allowed."
}

# Case 5: re-invoke ceiling reached -> anti-infinite-loop fail-safe. Allow exit.
$reinvokeCap = [Math]::Min($budgetRemaining, $GGO_REINVOKE_CEILING)
if ($reinvokeCount -ge $reinvokeCap) {
    Write-Diag "re-invoke cap reached (reinvoke_count=$reinvokeCount cap=$reinvokeCap); allowing exit and clearing marker"
    try { Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue } catch {}
    Emit-AllowExit "[ggo-stop-detect] Re-invoke cap reached ($reinvokeCount/$reinvokeCap); stop allowed (treat as hard stop)."
}

# Case 6: unauthorized mid-loop stop -> re-invoke with forbidden-reason reminder.
$newCount = $reinvokeCount + 1
try {
    $state.reinvoke_count = $newCount
    $state | Add-Member -NotePropertyName 'updated_at' -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) -Force
    $state | ConvertTo-Json -Depth 6 | Set-Content -Path $stateFile -Encoding UTF8
} catch {
    Write-Diag "failed to persist incremented reinvoke_count; re-invoking anyway"
}

Write-Diag "unauthorized mid-loop stop detected; re-invoking (reinvoke_count=$newCount/$reinvokeCap, iter=$iter)"

$reminder = @"
[ggo-stop-detect / BUG-107] This g-go-go autopilot run is NOT authorized to stop.
You halted mid-loop without quoting an authorizing hard-stop row. Per the g-go-go
contract, a 'session checkpoint', 'handing off cleanly', 'natural stopping point',
'good progress so far', or any context/complexity/subagent-count concern is the
FORBIDDEN CONTEXT WINDOW PANIC stop wearing a gentler name -- it is not a valid exit.

Resume the loop now. There are exactly two valid moves:
  (a) run the next lowest-ID eligible iteration anyway (at N=1 bucket if needed), or
  (b) if and only if a genuine hard-stop table row applies, write that verbatim row
      into .gald3r/logs/ggo_run_state.json (field authorized_hard_stop) and THEN stop.
If --context-aware is active, REDUCE the bucket count N (never below 1) instead of
stopping. Re-invoke $newCount of $reinvokeCap. Continue.
"@

@{
    # Claude Code Stop-hook continuation contract.
    decision           = "block"
    reason             = $reminder
    # Cursor stop-hook continuation contract.
    continue           = $false
    followup           = $reminder
    additional_context = $reminder
} | ConvertTo-Json -Compress
exit 0
