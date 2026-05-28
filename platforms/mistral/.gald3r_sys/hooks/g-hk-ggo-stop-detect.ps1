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

    State machine (file-first, no backend):
      The g-go-go command writes a run-state marker at INIT and refreshes it each
      iteration: .gald3r/logs/ggo_run_state.json with fields:
        { "active": true, "iter": N, "budget_remaining": B,
          "authorized_hard_stop": "" | "<verbatim hard-stop row>",
          "reinvoke_count": R, "updated_at": "<iso>" }

      On stop, this hook:
        1. No active run            -> no-op (continue, exit 0).
        2. authorized_hard_stop set -> genuine hard stop; allow exit, clear marker.
        3. budget exhausted         -> allow exit (the budget cap IS a hard stop).
        4. re-invoke ceiling hit    -> allow exit (anti-infinite-loop fail-safe).
        5. otherwise (unauthorized) -> re-invoke: increment reinvoke_count, emit
           block/continue decision with the forbidden-reason reminder.

    Bounding guarantees (Acceptance Criterion #3):
      - reinvoke_count never exceeds budget_remaining, and is independently
        capped by GGO_REINVOKE_CEILING so it can never infinite-loop.
      - A genuine hard stop (authorized_hard_stop populated) is NEVER re-invoked.
      - Budget exhaustion is treated as a hard stop and is NEVER re-invoked.

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

# -- stdin payload (stop event schema) ----------------------------------------
$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

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

$logsDir   = Join-Path $ProjectRoot '.gald3r/logs'
$stateFile = Join-Path $logsDir 'ggo_run_state.json'
$diagLog   = Join-Path $logsDir 'hook_diag.log'

function Write-Diag([string] $msg) {
    try {
        if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ggo-stop-detect: $msg" |
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

# Case 1: no active run marker -> this stop is unrelated to g-go-go. No-op.
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

$iter            = 0;  if ($null -ne $state.iter)             { $iter            = [int]$state.iter }
$budgetRemaining = 0;  if ($null -ne $state.budget_remaining) { $budgetRemaining = [int]$state.budget_remaining }
$reinvokeCount   = 0;  if ($null -ne $state.reinvoke_count)   { $reinvokeCount   = [int]$state.reinvoke_count }
$hardStop        = ""; if ($state.authorized_hard_stop)       { $hardStop        = [string]$state.authorized_hard_stop }

# Case 2: a genuine, authorized hard stop was recorded. Never re-invoke.
if ($hardStop.Trim().Length -gt 0) {
    Write-Diag "authorized hard stop recorded (`"$hardStop`"); allowing exit and clearing marker"
    try { Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue } catch {}
    Emit-AllowExit "[ggo-stop-detect] Authorized hard stop ($hardStop); stop allowed."
}

# Case 3: budget exhausted -> the budget cap itself is a hard stop. Never re-invoke.
if ($budgetRemaining -le 0) {
    Write-Diag "budget exhausted (budget_remaining=$budgetRemaining); allowing exit and clearing marker"
    try { Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue } catch {}
    Emit-AllowExit "[ggo-stop-detect] Run budget exhausted; stop allowed."
}

# Case 4: re-invoke ceiling reached -> anti-infinite-loop fail-safe. Allow exit.
$reinvokeCap = [Math]::Min($budgetRemaining, $GGO_REINVOKE_CEILING)
if ($reinvokeCount -ge $reinvokeCap) {
    Write-Diag "re-invoke cap reached (reinvoke_count=$reinvokeCount cap=$reinvokeCap); allowing exit and clearing marker"
    try { Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue } catch {}
    Emit-AllowExit "[ggo-stop-detect] Re-invoke cap reached ($reinvokeCount/$reinvokeCap); stop allowed (treat as hard stop)."
}

# Case 5: unauthorized mid-loop stop -> re-invoke with forbidden-reason reminder.
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
