<#
.SYNOPSIS
    gald3r Medic Heal - structural backfill for repos that predate a framework feature (T1436).

.DESCRIPTION
    When a new framework constraint (C-NNN) or feature requires new files/folders, the
    corresponding --heal-cNNN path backfills the gap in repos that predate it. g-medic L1
    triage detects structural gaps; this script remediates them.

    Dry-run by default. Pass -Apply to write. Every operation is logged to
    .gald3r/logs/medic_heal_YYYYMMDD.log .

    Phase 1 heals:
      c023        - create missing .gald3r/releases/ files from CHANGELOG (delegates to
                    g-skl-release/scripts/backfill_release_files.ps1)
      version     - create root VERSION file from the latest CHANGELOG ## [X.Y.Z] header
      constraints - report inheritable framework constraints missing from local CONSTRAINTS.md;
                    with -Apply, append clearly-marked stubs pointing at the framework source
      all         - run every Phase 1 heal in dependency order (version, c023, constraints)

.PARAMETER ProjectRoot
    Root directory of the target project. Defaults to current directory.

.PARAMETER Heal
    Which heal to run: c023 | version | constraints | all.

.PARAMETER Apply
    Actually write files. Without -Apply, runs dry-run (prints the plan only).

.PARAMETER Json
    Emit a JSON result object instead of human-readable text.

.EXAMPLE
    .\gald3r_medic_heal.ps1 -ProjectRoot "G:\MyProject" -Heal c023            # dry-run plan
    .\gald3r_medic_heal.ps1 -ProjectRoot "G:\MyProject" -Heal c023 -Apply     # write release files
    .\gald3r_medic_heal.ps1 -ProjectRoot "G:\MyProject" -Heal all             # consolidated dry-run

.NOTES
    Task: T1436  Constraint: C-023  Skill: g-skl-medic
#>
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [Parameter(Mandatory)][ValidateSet("c023", "version", "constraints", "all")][string]$Heal,
    [switch]$Apply,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$mode = if ($Apply) { "apply" } else { "dry-run" }
$results = New-Object System.Collections.Generic.List[object]

$logDir = Join-Path $ProjectRoot ".gald3r\logs"
$logFile = Join-Path $logDir ("medic_heal_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

function Write-HealLog {
    param([string]$Heal, [string]$Action, [string]$Detail)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    $line = "$ts | heal=$Heal | mode=$mode | $Action | $Detail"
    if ($Apply) {
        if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
        Add-Content -Path $logFile -Value $line
    }
    elseif (-not $Json) {
        Write-Host "[DRY-RUN LOG] $line"
    }
}

function Add-Result {
    param([string]$Heal, [string]$Status, [string]$Message, [string[]]$Files = @())
    $results.Add([pscustomobject]@{ heal = $Heal; status = $Status; message = $Message; files = $Files })
    if (-not $Json) { Write-Host ("  [{0}] {1}: {2}" -f $Status, $Heal, $Message) }
}

# --- heal: c023 (release file backfill) -- delegate to existing release script ---
function Invoke-HealC023 {
    $backfill = Join-Path $scriptDir "..\..\g-skl-release\scripts\backfill_release_files.ps1"
    if (-not (Test-Path $backfill)) {
        Write-HealLog "c023" "skip" "backfill_release_files.ps1 not found at $backfill"
        Add-Result "c023" "skipped" "backfill_release_files.ps1 not available (slim tier?)"
        return
    }
    $backfill = (Resolve-Path $backfill).Path
    # NOTE: do not name this $args -- that is an automatic variable and breaks splatting.
    $bfArgs = @{ ProjectRoot = $ProjectRoot; Json = $true }
    if ($Apply) { $bfArgs["Apply"] = $true }
    try {
        $out = & $backfill @bfArgs | Out-String
        $parsed = $null
        try { $parsed = $out | ConvertFrom-Json } catch {}
        $created = @()
        if ($parsed -and ($parsed.PSObject.Properties.Name -contains "created") -and $null -ne $parsed.created) {
            $created = @($parsed.created)
        }
        $createdCount = ($created | Measure-Object).Count
        $msg = if ($Apply) { "$createdCount release file(s) backfilled" } else { "$createdCount release file(s) would be backfilled" }
        Write-HealLog "c023" ($(if ($Apply) { "applied" } else { "planned" })) $msg
        Add-Result "c023" "ok" $msg $created
    }
    catch {
        Write-HealLog "c023" "error" $_.Exception.Message
        Add-Result "c023" "error" $_.Exception.Message
    }
}

# --- heal: version (VERSION file from latest CHANGELOG header) ---
function Invoke-HealVersion {
    $versionFile = Join-Path $ProjectRoot "VERSION"
    if (Test-Path $versionFile) {
        Write-HealLog "version" "skip" "VERSION already present"
        Add-Result "version" "ok" "VERSION already present (no action)"
        return
    }
    $changelog = Join-Path $ProjectRoot "CHANGELOG.md"
    if (-not (Test-Path $changelog)) {
        Write-HealLog "version" "skip" "no CHANGELOG.md to derive version from"
        Add-Result "version" "skipped" "no CHANGELOG.md found"
        return
    }
    $match = Select-String -Path $changelog -Pattern '^\#\#\s*\[(\d+\.\d+\.\d+)\]' | Select-Object -First 1
    if (-not $match) {
        Write-HealLog "version" "skip" "no versioned header in CHANGELOG"
        Add-Result "version" "skipped" "no ## [X.Y.Z] header in CHANGELOG"
        return
    }
    $ver = $match.Matches[0].Groups[1].Value
    if ($Apply) {
        Set-Content -Path $versionFile -Value $ver -NoNewline -Encoding utf8
        Write-HealLog "version" "applied" "wrote VERSION=$ver"
        Add-Result "version" "ok" "created VERSION ($ver)" @("VERSION")
    }
    else {
        Write-HealLog "version" "planned" "would write VERSION=$ver"
        Add-Result "version" "ok" "would create VERSION ($ver)" @("VERSION")
    }
}

# --- heal: constraints (report inheritable framework constraints missing locally) ---
function Invoke-HealConstraints {
    $localCon = Join-Path $ProjectRoot ".gald3r\CONSTRAINTS.md"
    $fwkCon = Join-Path $scriptDir "..\..\..\constraints\framework_inheritable_constraints.md"
    if (-not (Test-Path $fwkCon)) {
        Write-HealLog "constraints" "skip" "framework_inheritable_constraints.md not found"
        Add-Result "constraints" "skipped" "framework inheritable source not available (slim tier?)"
        return
    }
    $fwkCon = (Resolve-Path $fwkCon).Path
    $fwkIds = Select-String -Path $fwkCon -Pattern '\b(C-\d{3})\b' -AllMatches |
        ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
    $localIds = @()
    if (Test-Path $localCon) {
        $localIds = Select-String -Path $localCon -Pattern '\b(C-\d{3})\b' -AllMatches |
            ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
    }
    $missing = $fwkIds | Where-Object { $localIds -notcontains $_ }
    if (-not $missing -or $missing.Count -eq 0) {
        Write-HealLog "constraints" "ok" "no missing inheritable constraints"
        Add-Result "constraints" "ok" "all inheritable framework constraints present locally"
        return
    }
    $missingList = ($missing -join ", ")
    if ($Apply) {
        # Phase 1 is cautious: append clearly-marked pointer stubs, never the full body.
        if (-not (Test-Path $localCon)) {
            Write-HealLog "constraints" "skip" "local CONSTRAINTS.md absent; refusing to create it (needs g-setup)"
            Add-Result "constraints" "needs_attention" "local CONSTRAINTS.md missing; run @g-setup first. Missing: $missingList"
            return
        }
        $stub = "`n<!-- T1436 heal-constraints ($(Get-Date -Format 'yyyy-MM-dd')): the following inheritable framework constraints are not yet present locally. Review framework_inheritable_constraints.md and adopt via @g-constraint-add: $missingList -->`n"
        Add-Content -Path $localCon -Value $stub
        Write-HealLog "constraints" "applied" "appended pointer stub for: $missingList"
        Add-Result "constraints" "deferred_verify" "appended adoption pointer for $($missing.Count) constraint(s): $missingList" @(".gald3r/CONSTRAINTS.md")
    }
    else {
        Write-HealLog "constraints" "planned" "would flag missing: $missingList"
        Add-Result "constraints" "ok" "$($missing.Count) inheritable constraint(s) missing locally: $missingList" @()
    }
}

# --- dispatch ---
if (-not $Json) { Write-Host "g-medic heal ($mode) -- ProjectRoot: $ProjectRoot`n" }

switch ($Heal) {
    "c023" { Invoke-HealC023 }
    "version" { Invoke-HealVersion }
    "constraints" { Invoke-HealConstraints }
    "all" {
        # dependency order: version -> c023 -> constraints
        Invoke-HealVersion
        Invoke-HealC023
        Invoke-HealConstraints
    }
}

if ($Json) {
    [pscustomobject]@{
        mode    = $mode
        heal    = $Heal
        root    = $ProjectRoot
        results = $results
    } | ConvertTo-Json -Depth 6
}
else {
    Write-Host "`nDone. $($results.Count) heal operation(s). Log: $logFile (written only with -Apply)."
}
