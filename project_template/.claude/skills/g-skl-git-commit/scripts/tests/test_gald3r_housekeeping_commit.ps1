# .gald3r_sys/skills/g-skl-git-commit/scripts/tests/test_gald3r_housekeeping_commit.ps1
# @subsystems: TASK_MANAGEMENT
#
# Fixture-based smoke tests for gald3r_housekeeping_commit.ps1 (T531).
# Restored under T1532 (framework test harness re-arm). Colocated next to the
# helper it tests; the only change from the original gald3r_dev copy is the
# @subsystems tag above (g-rl-38) and this header comment. Logic is unchanged.
#
# Spins up disposable git repos under $env:TEMP, drives a matrix of dirty states,
# and asserts the helper's exit code + JSON status. No Pester dependency -- runs
# anywhere PowerShell 5.1+ runs.
#
# Run:
#   .\tests\test_gald3r_housekeeping_commit.ps1
#
# Exit:
#   0 - all cases pass
#   1 - one or more cases failed (each failure printed)

param(
    [switch]$VerboseOutput
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$script:Helper = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\gald3r_housekeeping_commit.ps1')).Path
$script:Failures = @()
$script:CaseCount = 0

function New-DisposableRepo {
    $name = 'gald3r_hkc_test_' + [System.Guid]::NewGuid().ToString('N').Substring(0, 8)
    $root = Join-Path ([System.IO.Path]::GetTempPath()) $name
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    & git -C $root init --quiet --initial-branch=main 2>$null
    if ($LASTEXITCODE -ne 0) {
        & git -C $root init --quiet 2>$null
    }
    & git -C $root config user.email 'hkc@test.invalid' | Out-Null
    & git -C $root config user.name  'hkc-test'         | Out-Null
    & git -C $root config commit.gpgsign false          | Out-Null
    # Establish an initial commit so HEAD exists.
    Set-Content -LiteralPath (Join-Path $root 'README.md') -Value '# fixture' -Encoding UTF8
    & git -C $root add README.md | Out-Null
    & git -C $root commit --quiet -m 'init' | Out-Null
    return $root
}

function Remove-DisposableRepo {
    param([string]$Root)
    if ($Root -and (Test-Path -LiteralPath $Root)) {
        Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function New-File {
    param([string]$Root, [string]$RelPath, [string]$Body = 'x')
    $full = Join-Path $Root $RelPath
    $dir = Split-Path -Parent $full
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Set-Content -LiteralPath $full -Value $Body -Encoding UTF8
}

function Invoke-Helper {
    param([string]$Root, [string[]]$ExtraArgs = @())
    $args = @('-OrchestrationRoot', $Root, '-Json', '-NoColor') + $ExtraArgs
    $stdout = & pwsh -NoProfile -ExecutionPolicy Bypass -File $script:Helper @args 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ ExitCode = $code; Stdout = ($stdout -join "`n") }
}

function Assert-Case {
    param(
        [string]$Name,
        [int]$ExpectedExit,
        [string]$ExpectedStatus,
        [Parameter(Mandatory)] [scriptblock]$Setup
    )
    $script:CaseCount++
    $root = New-DisposableRepo
    try {
        & $Setup $root
        $r = Invoke-Helper -Root $root
        $stdoutText = [string]$r.Stdout
        $obj = $null
        try { $obj = $stdoutText | ConvertFrom-Json -ErrorAction Stop } catch { $obj = $null }

        $statusOk = $true
        if ($ExpectedStatus) {
            if (-not $obj) { $statusOk = $false }
            elseif ($obj.status -ne $ExpectedStatus) { $statusOk = $false }
        }
        $exitOk = ($r.ExitCode -eq $ExpectedExit)

        if ($exitOk -and $statusOk) {
            if ($VerboseOutput) {
                Write-Host "[PASS] $Name (exit=$($r.ExitCode), status=$($obj.status))" -ForegroundColor Green
            } else {
                Write-Host "[PASS] $Name" -ForegroundColor Green
            }
        } else {
            $msg = "[FAIL] $Name -- exit expected=$ExpectedExit got=$($r.ExitCode); status expected=$ExpectedStatus got=$($obj.status)"
            Write-Host $msg -ForegroundColor Red
            Write-Host '       stdout:' -ForegroundColor DarkGray
            Write-Host '       ' ($stdoutText -replace "`n", "`n       ") -ForegroundColor DarkGray
            $script:Failures += $msg
        }
    } finally {
        Remove-DisposableRepo -Root $root
    }
}

# ----- Cases -----

Assert-Case -Name 'clean working tree' -ExpectedExit 0 -ExpectedStatus 'clean' -Setup {
    param($root)
}

Assert-Case -Name 'safe .gald3r/TASKS.md only -- classify' -ExpectedExit 0 -ExpectedStatus 'safe-gald3r-housekeeping' -Setup {
    param($root)
    New-File -Root $root -RelPath '.gald3r/TASKS.md' -Body 'Task list'
}

Assert-Case -Name 'safe nested .gald3r/tasks/*.md -- classify' -ExpectedExit 0 -ExpectedStatus 'safe-gald3r-housekeeping' -Setup {
    param($root)
    New-File -Root $root -RelPath '.gald3r/tasks/task001_demo.md' -Body 'demo'
}

Assert-Case -Name 'mixed .gald3r + source dirty -> mixed-dirty (blocker)' -ExpectedExit 1 -ExpectedStatus 'mixed-dirty' -Setup {
    param($root)
    New-File -Root $root -RelPath '.gald3r/TASKS.md'
    New-File -Root $root -RelPath 'src/main.py' -Body 'print("x")'
}

Assert-Case -Name 'unsafe .gald3r/.identity -> unsafe-gald3r (blocker)' -ExpectedExit 1 -ExpectedStatus 'unsafe-gald3r' -Setup {
    param($root)
    # Establish controller shape first so member-repo detection does not short-circuit.
    New-File -Root $root -RelPath '.gald3r/TASKS.md' -Body 'tasks'
    & git -C $root add .gald3r/TASKS.md | Out-Null
    & git -C $root commit --quiet -m 'seed tasks' | Out-Null
    New-File -Root $root -RelPath '.gald3r/.identity' -Body 'project_id=abc'
}

Assert-Case -Name 'unsafe .gald3r/config/credentials.yaml -> unsafe-gald3r' -ExpectedExit 1 -ExpectedStatus 'unsafe-gald3r' -Setup {
    param($root)
    New-File -Root $root -RelPath '.gald3r/config/credentials.yaml' -Body 'k: v'
}

Assert-Case -Name 'unknown .gald3r/.unknown_thing.md -> unsafe-gald3r (unknown-gald3r-path)' -ExpectedExit 1 -ExpectedStatus 'unsafe-gald3r' -Setup {
    param($root)
    New-File -Root $root -RelPath '.gald3r/.unknown_thing.md' -Body 'x'
}

Assert-Case -Name 'untracked source file outside .gald3r -> mixed-dirty' -ExpectedExit 1 -ExpectedStatus 'mixed-dirty' -Setup {
    param($root)
    New-File -Root $root -RelPath 'CHANGELOG.md' -Body '## changes'
}

# Apply path uses an explicit invocation below (Assert-Case does not pass ExtraArgs).
$script:CaseCount++
$applyRoot = New-DisposableRepo
try {
    New-File -Root $applyRoot -RelPath '.gald3r/TASKS.md' -Body 'tasks'
    $r = Invoke-Helper -Root $applyRoot -ExtraArgs @('-Apply', '-Mode', 'preflight', '-TaskId', '531')
    $obj = $null
    try { $obj = $r.Stdout | ConvertFrom-Json -ErrorAction Stop } catch { $obj = $null }
    $expected = 'committed-safe-gald3r-housekeeping'
    if ($r.ExitCode -eq 0 -and $obj -and $obj.status -eq $expected) {
        Write-Host "[PASS] apply commits safe set" -ForegroundColor Green
    } else {
        $msg = "[FAIL] apply commits safe set -- exit=$($r.ExitCode), status=$($obj.status); expected exit=0 status=$expected"
        Write-Host $msg -ForegroundColor Red
        Write-Host '       stdout:' -ForegroundColor DarkGray
        Write-Host '       ' ([string]$r.Stdout -replace "`n", "`n       ") -ForegroundColor DarkGray
        $script:Failures += $msg
    }
} finally {
    Remove-DisposableRepo -Root $applyRoot
}

# post-write classify case uses explicit invocation below (Assert-Case is preflight-only).
$script:CaseCount++
$postRoot = New-DisposableRepo
try {
    New-File -Root $postRoot -RelPath '.gald3r/TASKS.md' -Body 't'
    $r = Invoke-Helper -Root $postRoot -ExtraArgs @('-Mode', 'post-write')
    $obj = $null
    try { $obj = $r.Stdout | ConvertFrom-Json -ErrorAction Stop } catch { $obj = $null }
    if ($r.ExitCode -eq 0 -and $obj -and $obj.status -eq 'safe-gald3r-coordination') {
        Write-Host "[PASS] post-write classify -> safe-gald3r-coordination" -ForegroundColor Green
    } else {
        $msg = "[FAIL] post-write classify -- exit=$($r.ExitCode), status=$($obj.status)"
        Write-Host $msg -ForegroundColor Red
        Write-Host '       stdout:' -ForegroundColor DarkGray
        Write-Host '       ' ([string]$r.Stdout -replace "`n", "`n       ") -ForegroundColor DarkGray
        $script:Failures += $msg
    }
} finally {
    Remove-DisposableRepo -Root $postRoot
}

Assert-Case -Name 'member-repo target refuses with config-fault' -ExpectedExit 2 -ExpectedStatus 'config-fault' -Setup {
    param($root)
    # Member-repo marker shape: .gald3r/.identity present, no manifest, no TASKS.md.
    New-File -Root $root -RelPath '.gald3r/.identity' -Body 'project_id=member'
    New-File -Root $root -RelPath '.gald3r/PROJECT.md' -Body '# member'
    & git -C $root add .gald3r/.identity .gald3r/PROJECT.md | Out-Null
    & git -C $root commit --quiet -m 'marker only' | Out-Null
    # Dirty something to force the helper past the clean-tree fast path.
    New-File -Root $root -RelPath 'src/something.txt' -Body 'x'
}

Write-Host ''
if ($script:Failures.Count -eq 0) {
    Write-Host "All $($script:CaseCount) cases passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "$($script:Failures.Count) of $($script:CaseCount) cases failed:" -ForegroundColor Red
    foreach ($f in $script:Failures) { Write-Host "  - $f" -ForegroundColor Red }
    exit 1
}
