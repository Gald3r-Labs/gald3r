<#
.SYNOPSIS
    gald3r_templates framework test-harness runner (T1532).

.DESCRIPTION
    Discovers framework tests from `tests_manifest.psd1` (the test-plan manifest),
    filters them by verification level, runs each via its declared runner
    (PowerShell or Python), and reports a pass/fail summary with a proper process
    exit code (0 = all green, non-zero = one or more failures or harness errors).

    This is the entry point the verify-gate calls. By default it runs the **L1**
    plan (fast / daily). Use -Level L2 / L3 / All for the broader plans.

    Test selection is manifest-backed: a test belongs to a level when its `Level`
    field matches OR the requested level appears in its optional `AlsoLevels` list.
    Adding a new test = adding one entry to tests_manifest.psd1.

.PARAMETER Level
    Which verification level to run: L1 (default), L2, L3, or All.

.PARAMETER Json
    Emit a machine-readable JSON summary instead of human-readable lines.

.PARAMETER ListOnly
    Print the discovered/selected tests and exit without running them.

.EXAMPLE
    .\custom_scripts\tests\run_l1_tests.ps1
    # Run the L1 plan (verify-gate default).

.EXAMPLE
    .\custom_scripts\tests\run_l1_tests.ps1 -Level All -Json
    # Run every registered test and emit JSON.

.NOTES
    Verify-gate wiring (T1532, AC5): this script is the documented L1 entry point.
    g-skl-verify-ladder Level 2 (Tests) should invoke:
        pwsh -NoProfile -ExecutionPolicy Bypass -File custom_scripts/tests/run_l1_tests.ps1
    A task can also declare it explicitly:
        verification_commands:
          - "pwsh -NoProfile -ExecutionPolicy Bypass -File custom_scripts/tests/run_l1_tests.ps1"
#>

[CmdletBinding()]
param(
    [ValidateSet('L1', 'L2', 'L3', 'All')]
    [string]$Level = 'L1',

    [switch]$Json,

    [switch]$ListOnly
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

# Repo root: search upward for the .gald3r marker (depth-robust wherever this harness lives).
$RepoRoot = $PSScriptRoot
while ($RepoRoot -and -not (Test-Path (Join-Path $RepoRoot '.gald3r'))) {
    $parent = Split-Path $RepoRoot -Parent
    if ($parent -eq $RepoRoot) { break }
    $RepoRoot = $parent
}
$ManifestPath = Join-Path $PSScriptRoot 'tests_manifest.psd1'

if (-not (Test-Path $ManifestPath)) {
    Write-Host "[HARNESS ERROR] test manifest not found: $ManifestPath" -ForegroundColor Red
    exit 2
}

$manifest = Import-PowerShellDataFile -LiteralPath $ManifestPath
$allTests = @($manifest.Tests)

function Test-MatchesLevel {
    param([hashtable]$Test, [string]$Want)
    if ($Want -eq 'All') { return $true }
    if ($Test.Level -eq $Want) { return $true }
    if ($Test.ContainsKey('AlsoLevels') -and ($Test.AlsoLevels -contains $Want)) { return $true }
    return $false
}

$selected = @($allTests | Where-Object { Test-MatchesLevel -Test $_ -Want $Level })

if ($ListOnly) {
    Write-Host ("Test plan '{0}' ({1} test(s)):" -f $Level, $selected.Count) -ForegroundColor Cyan
    foreach ($t in $selected) {
        Write-Host ("  [{0}] {1} ({2}) -> {3}" -f $t.Level, $t.Name, $t.Runner, $t.Path) -ForegroundColor DarkGray
    }
    exit 0
}

# Locate Python once (uv-aware, but uv is not required for these stdlib tests).
$pythonExe = $null
foreach ($candidate in @('python', 'python3')) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { $pythonExe = $cmd.Source; break }
}

$runResults = @()

foreach ($t in $selected) {
    # Tests live beside this harness; resolve by leaf there, else fall back to repo-root-relative.
    $localPath = Join-Path $PSScriptRoot (Split-Path $t.Path -Leaf)
    $testPath = if (Test-Path $localPath) { $localPath } else { Join-Path $RepoRoot ($t.Path -replace '/', '\') }
    $name = $t.Name
    $runner = $t.Runner
    $status = 'fail'
    $exitCode = $null
    $note = ''

    if (-not (Test-Path $testPath)) {
        $status = 'error'
        $note = "test file not found: $($t.Path)"
        $runResults += [PSCustomObject]@{ name = $name; level = $t.Level; runner = $runner; status = $status; exit = $null; note = $note }
        continue
    }

    try {
        if ($runner -eq 'pwsh') {
            & pwsh -NoProfile -ExecutionPolicy Bypass -File $testPath | Out-Host
            $exitCode = $LASTEXITCODE
        } elseif ($runner -eq 'python') {
            if (-not $pythonExe) {
                $status = 'error'
                $note = 'python interpreter not found on PATH'
                $runResults += [PSCustomObject]@{ name = $name; level = $t.Level; runner = $runner; status = $status; exit = $null; note = $note }
                continue
            }
            & $pythonExe $testPath | Out-Host
            $exitCode = $LASTEXITCODE
        } else {
            $status = 'error'
            $note = "unknown runner '$runner'"
            $runResults += [PSCustomObject]@{ name = $name; level = $t.Level; runner = $runner; status = $status; exit = $null; note = $note }
            continue
        }
    } catch {
        $status = 'error'
        $note = $_.Exception.Message
        $runResults += [PSCustomObject]@{ name = $name; level = $t.Level; runner = $runner; status = $status; exit = $exitCode; note = $note }
        continue
    }

    $status = if ($exitCode -eq 0) { 'pass' } else { 'fail' }
    $runResults += [PSCustomObject]@{ name = $name; level = $t.Level; runner = $runner; status = $status; exit = $exitCode; note = $note }
}

$total = $runResults.Count
$passed = @($runResults | Where-Object { $_.status -eq 'pass' }).Count
$failed = @($runResults | Where-Object { $_.status -ne 'pass' }).Count

if ($Json) {
    [PSCustomObject]@{
        suite     = 'gald3r_templates framework harness'
        level     = $Level
        total     = $total
        passed    = $passed
        failed    = $failed
        results   = $runResults
        timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    } | ConvertTo-Json -Depth 5
} else {
    Write-Host ''
    Write-Host '================================================' -ForegroundColor Cyan
    Write-Host ("  gald3r_templates harness - plan {0,-4}          " -f $Level) -ForegroundColor Cyan
    Write-Host '================================================' -ForegroundColor Cyan
    foreach ($r in $runResults) {
        $icon = switch ($r.status) { 'pass' { 'PASS' } 'fail' { 'FAIL' } default { 'ERR ' } }
        $color = switch ($r.status) { 'pass' { 'Green' } 'fail' { 'Red' } default { 'Yellow' } }
        $line = "  [{0}] {1} ({2}/{3})" -f $icon, $r.name, $r.level, $r.runner
        if ($r.note) { $line += "  -- $($r.note)" }
        Write-Host $line -ForegroundColor $color
    }
    Write-Host ''
    $summaryColor = if ($failed -eq 0) { 'Green' } else { 'Red' }
    Write-Host ("Summary: {0}/{1} test suites passed, {2} failed (plan {3})" -f $passed, $total, $failed, $Level) -ForegroundColor $summaryColor
    Write-Host ''
}

if ($failed -eq 0) { exit 0 } else { exit 1 }
