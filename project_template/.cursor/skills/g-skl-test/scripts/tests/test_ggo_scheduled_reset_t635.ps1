# @subsystems: AGENT_ORCHESTRATION
# T635 behavioral test — g-hk-ggo-stop-detect.ps1 scheduled_context_reset (Rolling Amnesia).
# Proves: an authorized scheduled reset RE-INVOKES with --resume (non-terminal), consumes the
# marker, bumps resets_done, keeps the run active; budget exhaustion turns a reset into a
# terminal exit; a genuine hard stop still terminates; an unauthorized stop still re-invokes.
$ErrorActionPreference = 'Stop'

# Locate repo root (nearest ancestor with .gald3r) then the canonical hook.
$dir = $PSScriptRoot
while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
    $p = Split-Path $dir -Parent
    if ($p -eq $dir) { $dir = ''; break }
    $dir = $p
}
$repoRoot = if ($dir) { $dir } else { (Get-Location).Path }
$hook = Join-Path $repoRoot '.claude/hooks/g-hk-ggo-stop-detect.ps1'
if (-not (Test-Path $hook)) {
    $hook = Join-Path $repoRoot '.cursor/hooks/g-hk-ggo-stop-detect.ps1'
}
if (-not (Test-Path $hook)) { Write-Host "FAIL: stop hook not found under $repoRoot" -ForegroundColor Red; exit 1 }

$fails = 0
function Assert($cond, $msg) {
    if ($cond) { Write-Host "  [PASS] $msg" -ForegroundColor Green }
    else { Write-Host "  [FAIL] $msg" -ForegroundColor Red; $script:fails++ }
}
function New-Root([hashtable]$state) {
    $r = Join-Path ([IO.Path]::GetTempPath()) ("t635_" + [Guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path (Join-Path $r '.gald3r/logs') -Force | Out-Null
    $state | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $r '.gald3r/logs/ggo_run_state.json') -Encoding UTF8
    return $r
}
function Invoke-Hook($root, $sessionId) {
    $payload = @{ session_id = $sessionId } | ConvertTo-Json -Compress
    ($payload | & pwsh -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot $root 2>$null) | ConvertFrom-Json
}

Write-Host "`n=== T1: scheduled_context_reset with budget => RE-INVOKE (--resume) ===" -ForegroundColor Cyan
$root = New-Root @{ active=$true; platform='claude'; session_id='sess-1'; iter=3; budget_remaining=10;
                    authorized_hard_stop='scheduled_context_reset'; reinvoke_count=0; resets_done=0 }
$res = Invoke-Hook $root 'sess-1'
Assert ($res.decision -eq 'block') "decision=block (re-invoke, not allow-exit)"
Assert ($res.continue -eq $false) "continue=false (Cursor re-invoke contract)"
Assert ($res.reason -match '--resume') "reason instructs --resume"
Assert ($res.reason -match 'Rolling Amnesia') "reason names Rolling Amnesia"
$st = Get-Content (Join-Path $root '.gald3r/logs/ggo_run_state.json') -Raw | ConvertFrom-Json
Assert ($st.authorized_hard_stop -eq '') "marker consumed (authorized_hard_stop cleared)"
Assert ([int]$st.resets_done -eq 1) "resets_done incremented to 1"
Assert ([bool]$st.active -eq $true) "run still active (non-terminal)"
Remove-Item $root -Recurse -Force

Write-Host "`n=== T2: scheduled_context_reset with budget=0 => TERMINAL exit ===" -ForegroundColor Cyan
$root = New-Root @{ active=$true; platform='claude'; session_id='sess-2'; iter=12; budget_remaining=0;
                    authorized_hard_stop='scheduled_context_reset'; reinvoke_count=0; resets_done=3 }
$res = Invoke-Hook $root 'sess-2'
Assert ($res.continue -eq $true) "continue=true (terminal exit at budget exhaustion)"
Assert ($null -eq $res.decision -or $res.decision -ne 'block') "not a block decision"
Assert (-not (Test-Path (Join-Path $root '.gald3r/logs/ggo_run_state.json'))) "marker cleared on terminal exit"
Remove-Item $root -Recurse -Force

Write-Host "`n=== T3: genuine terminal hard stop still TERMINATES (regression) ===" -ForegroundColor Cyan
$root = New-Root @{ active=$true; platform='claude'; session_id='sess-3'; iter=5; budget_remaining=7;
                    authorized_hard_stop='No runnable work | clean halt'; reinvoke_count=0; resets_done=0 }
$res = Invoke-Hook $root 'sess-3'
Assert ($res.continue -eq $true) "continue=true (genuine hard stop allowed through)"
Assert (-not (Test-Path (Join-Path $root '.gald3r/logs/ggo_run_state.json'))) "marker cleared"
Remove-Item $root -Recurse -Force

Write-Host "`n=== T4: unauthorized mid-loop stop still RE-INVOKES (BUG-107 regression) ===" -ForegroundColor Cyan
$root = New-Root @{ active=$true; platform='claude'; session_id='sess-4'; iter=2; budget_remaining=9;
                    authorized_hard_stop=''; reinvoke_count=0; resets_done=0 }
$res = Invoke-Hook $root 'sess-4'
Assert ($res.decision -eq 'block') "decision=block (unauthorized-stop re-invoke intact)"
Assert ($res.reason -match 'BUG-107') "reason cites BUG-107 contract"
Remove-Item $root -Recurse -Force

Write-Host ""
if ($fails -eq 0) { Write-Host "ALL T635 HOOK TESTS PASSED" -ForegroundColor Green; exit 0 }
else { Write-Host "$fails ASSERTION(S) FAILED" -ForegroundColor Red; exit 1 }
