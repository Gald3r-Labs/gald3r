# @subsystems: AGENT_ORCHESTRATION
# T630 behavioral test — scripts/ggo_outer_loop.py deterministic outer-loop contract.
# Proves: outer loop owns budget/iter counting + hard-stop detection (NOT the LLM); brief
# is rendered from disk state; a coordinator-written hard stop halts the loop. No real LLM.
# Migrated from ggo_outer_loop.ps1 to the Python port (T669, PS1-KILL epic T667). The harness
# stays PowerShell; only the script under test changed from .ps1 to .py.
$ErrorActionPreference = 'Stop'

$dir = $PSScriptRoot
while ($dir -and -not (Test-Path (Join-Path $dir '.gald3r'))) {
    $p = Split-Path $dir -Parent; if ($p -eq $dir) { $dir=''; break }; $dir = $p
}
$repoRoot = if ($dir) { $dir } else { (Get-Location).Path }
$loop = Join-Path $repoRoot '.gald3r_sys/scripts/ggo_outer_loop.py'
if (-not (Test-Path $loop)) { Write-Host "FAIL: ggo_outer_loop.py not found" -ForegroundColor Red; exit 1 }

$fails = 0
function Assert($cond,$msg){ if($cond){Write-Host "  [PASS] $msg" -ForegroundColor Green}else{Write-Host "  [FAIL] $msg" -ForegroundColor Red;$script:fails++} }
function New-Proj(){
    $r = Join-Path ([IO.Path]::GetTempPath()) ("t630_"+[Guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path (Join-Path $r '.gald3r/logs') -Force | Out-Null
    "# TASKS`n- [📋] T999 sample" | Set-Content (Join-Path $r '.gald3r/TASKS.md') -Encoding UTF8
    return $r
}
function State($r){ Get-Content (Join-Path $r '.gald3r/logs/ggo_run_state.json') -Raw | ConvertFrom-Json }

Write-Host "`n=== T1: parse-check ===" -ForegroundColor Cyan
& python -m py_compile $loop 2> $null
Assert ($LASTEXITCODE -eq 0) "ggo_outer_loop.py parses clean"

Write-Host "`n=== T2: DryRun budget=3 -> 3 iterations, budget->0, deactivated ===" -ForegroundColor Cyan
$r = New-Proj
& python $loop --project-root $r --budget 3 --dry-run *> $null
$st = State $r
Assert ([int]$st.iter -eq 3) "iter advanced to 3 (outer loop owns iter counting)"
Assert ([int]$st.budget_remaining -eq 0) "budget decremented to 0 (outer loop owns budget)"
Assert ($st.active -eq $false) "run deactivated at terminal exit"
Assert ($st.mode -eq 'stateless') "state tagged mode=stateless"
Remove-Item $r -Recurse -Force

Write-Host "`n=== T3: pre-seeded authorized_hard_stop -> immediate halt, no iteration ===" -ForegroundColor Cyan
$r = New-Proj
@{ active=$true; platform='claude'; mode='stateless'; iter=0; budget_remaining=5;
   authorized_hard_stop='No runnable work | clean halt'; resets_done=0;
   completed_iterations=@() } | ConvertTo-Json | Set-Content (Join-Path $r '.gald3r/logs/ggo_run_state.json') -Encoding UTF8
& python $loop --project-root $r --resume --dry-run *> $null
$st = State $r
Assert ([int]$st.iter -eq 0) "iter unchanged (hard stop detected before any iteration)"
Assert ($st.active -eq $false) "run deactivated"
Remove-Item $r -Recurse -Force

Write-Host "`n=== T4: stub coordinator writes hard stop after 2 calls -> loop halts at iter 2 ===" -ForegroundColor Cyan
$r = New-Proj
$stub = Join-Path $r 'stub_coord.ps1'
@'
$ErrorActionPreference='Stop'
$null = $input | Out-String          # consume the briefed prompt on stdin
$sf = $env:GGO_TEST_STATE
$cf = $env:GGO_TEST_COUNTER
$n = 0; if (Test-Path $cf) { $n = [int](Get-Content $cf -Raw) }
$n++; Set-Content $cf $n
$s = Get-Content $sf -Raw | ConvertFrom-Json
if ($n -ge 2) { $s.authorized_hard_stop = 'No runnable work | clean halt' }
$s | ConvertTo-Json -Depth 10 | Set-Content $sf -Encoding UTF8
exit 0
'@ | Set-Content $stub -Encoding UTF8
$env:GGO_TEST_STATE   = Join-Path $r '.gald3r/logs/ggo_run_state.json'
$env:GGO_TEST_COUNTER = Join-Path $r 'counter.txt'
$cmd = "pwsh -NoProfile -ExecutionPolicy Bypass -File $stub"
& python $loop --project-root $r --budget 10 --coordinator-command $cmd *> $null
$st = State $r
Assert ([int]$st.iter -eq 2) "loop halted at iter 2 (coordinator-written hard stop honored by outer loop)"
Assert ($st.active -eq $false) "run deactivated"
Remove-Item Env:\GGO_TEST_STATE, Env:\GGO_TEST_COUNTER
Remove-Item $r -Recurse -Force

Write-Host "`n=== T5: brief rendering substitutes disk state ===" -ForegroundColor Cyan
$r = New-Proj
$out = & python $loop --project-root $r --budget 1 --dry-run 2>&1 | Out-String
Assert ($out -match 'Budget remaining : 1') "brief shows budget_remaining from state"
Assert ($out -match 'BLANK context window') "brief asserts fresh/blank coordinator context"
Assert ($out -match 'EXACTLY ONE g-go-go iteration') "brief constrains coordinator to one iteration"
Remove-Item $r -Recurse -Force

Write-Host ""
if ($fails -eq 0) { Write-Host "ALL T630 OUTER-LOOP TESTS PASSED" -ForegroundColor Green; exit 0 }
else { Write-Host "$fails ASSERTION(S) FAILED" -ForegroundColor Red; exit 1 }
