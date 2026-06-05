<#
.SYNOPSIS
    Verification fixtures for `g-go --workspace` and `g-go --swarm --workspace`
    (T532 contract), adapted for the gald3r_templates repo (T1532).

.DESCRIPTION
    Documentation-and-policy fixtures for the workspace mode behavior contract.
    Because `g-go` is an LLM-executed prompt, not a runtime, these fixtures verify
    that the policy CONTRACT surfaces are intact across the IDE command surfaces
    PRESENT IN THIS REPO and that the supporting workspace manifest + helper
    scripts honor the cases the spec calls out.

    ADAPTATION NOTES (T1532, restore-from-split):
    - IDE command surfaces are DISCOVERED dynamically (any top-level
      `.<ide>/commands/g-go.md`), not hardcoded to the old gald3r_dev 6-IDE list.
      This tracks the D015 parity IDE targets actually installed in this repo
      (currently .cursor, .claude, .gald3r_sys).
    - The workspace manifest is read from the RELOCATED path
      `.gald3r/workspace/workspace_manifest.yaml` (NOT the old `.gald3r/linking/`).
    - The marker-only guard helper is read from its current home
      `.gald3r_sys/skills/g-skl-workspace/scripts/`.
    - Content fixtures verify the SAFETY PRIMITIVE SURFACES exist (workspace mode
      documented, manifest parseable, guard present, rule mirrors present) rather
      than matching exact legacy wording, which has intentionally drifted since
      the split. Missing surfaces fail closed.

      F1. g-go command surface present on every discovered IDE root
      F2. Workspace flag documented (--workspace) on every discovered g-go.md
      F3. Workspace mode rules surface (workspace + per-repo/marker-only) present
      F4. Member-scoped task: manifest resolves >= 1 member with existing path
      F5. Marker-only guard + bootstrap helpers present (relocated home)
      F6. Per-root dirty member gate documented in g-rl-33 (md or mdc mirror)
      F7. Marker-only invariant rule (g-rl-36) installed in IDE rule trees
      F8. Manifest declares controlled members (skip/deferred reason source)
      F9. Swarm workspace coordination surface present on every g-go.md

.PARAMETER Json
    Emit machine-readable JSON instead of human-readable lines.

.EXAMPLE
    .\custom_scripts\tests\test_g_go_workspace_mode_fixtures.ps1
.EXAMPLE
    .\custom_scripts\tests\test_g_go_workspace_mode_fixtures.ps1 -Json
#>

[CmdletBinding()]
param(
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $RepoRoot

# D015 parity: discover IDE command-surface roots actually present in this repo
# instead of hardcoding the old gald3r_dev list.
function Get-IdeCommandRoots {
    param([string]$CommandFile)
    $found = @()
    foreach ($dir in (Get-ChildItem -LiteralPath $RepoRoot -Directory -Force -ErrorAction SilentlyContinue)) {
        if ($dir.Name -notmatch '^\.') { continue }
        $cmd = Join-Path $dir.FullName "commands\$CommandFile"
        if (Test-Path $cmd) { $found += $dir.Name }
    }
    return , ($found | Sort-Object -Unique)
}

$IdeRoots = Get-IdeCommandRoots -CommandFile 'g-go.md'
$ManifestPath = Join-Path $RepoRoot '.gald3r\workspace\workspace_manifest.yaml'
$results = @()

function Add-Result {
    param([string]$Id, [string]$Name, [bool]$Pass, [string]$Evidence)
    $script:results += [PSCustomObject]@{ id = $Id; name = $Name; pass = $Pass; evidence = $Evidence }
}

# F1. g-go command surface present on at least one discovered IDE root.
$f1Pass = ($IdeRoots.Count -ge 1)
$f1Evidence = if ($f1Pass) { "g-go.md discovered in: $($IdeRoots -join ', ')" } else { 'no IDE command surface with g-go.md found' }
Add-Result -Id 'F1' -Name 'g-go command surface present (discovered IDE roots)' -Pass $f1Pass -Evidence $f1Evidence

# F2. Workspace flag documented in each discovered g-go.md.
$f2Pass = ($IdeRoots.Count -ge 1)
$f2Evidence = @()
foreach ($ide in $IdeRoots) {
    $content = Get-Content -Raw (Join-Path $RepoRoot "$ide\commands\g-go.md")
    if ($content -notmatch '--workspace') { $f2Pass = $false; $f2Evidence += "${ide}: missing --workspace" }
}
if ($f2Pass) { $f2Evidence = @("--workspace flag documented in all $($IdeRoots.Count) discovered g-go.md files") }
Add-Result -Id 'F2' -Name 'Workspace flag documented in g-go.md' -Pass $f2Pass -Evidence ($f2Evidence -join '; ')

# F3. Workspace mode rules surface present (workspace + per-repo / marker-only language).
$f3Pass = ($IdeRoots.Count -ge 1)
$f3Evidence = @()
foreach ($ide in $IdeRoots) {
    $content = Get-Content -Raw (Join-Path $RepoRoot "$ide\commands\g-go.md")
    $hasWorkspaceMode = $content -match '(?i)Workspace Mode|--workspace'
    $hasPerRepoOrMarker = $content -match '(?i)per-repo|per-root|marker-only|workspace_repos'
    if (-not ($hasWorkspaceMode -and $hasPerRepoOrMarker)) {
        $miss = @()
        if (-not $hasWorkspaceMode) { $miss += 'workspace-mode' }
        if (-not $hasPerRepoOrMarker) { $miss += 'per-repo/marker-only' }
        $f3Pass = $false; $f3Evidence += "${ide}: missing $($miss -join ',')"
    }
}
if ($f3Pass) { $f3Evidence = @('Workspace-mode + per-repo/marker-only surfaces present on all discovered g-go.md files') }
Add-Result -Id 'F3' -Name 'Workspace queue / per-repo / marker-only surface present' -Pass $f3Pass -Evidence ($f3Evidence -join '; ')

# F4. Member-scoped task - manifest resolves >= 1 non-owner member with an existing local_path.
$f4Pass = $false
$f4Evidence = @()
if (-not (Test-Path $ManifestPath)) {
    $f4Evidence += "manifest missing at $ManifestPath"
} else {
    $manifestText = Get-Content -Raw $ManifestPath
    $idMatches = [regex]::Matches($manifestText, '(?ms)^- id:\s+(?<id>[a-z][a-z0-9_]*).*?^  local_path:\s+(?<path>.+?)$')
    $resolved = @()
    foreach ($m in $idMatches) {
        $id = $m.Groups['id'].Value
        $p = $m.Groups['path'].Value.Trim()
        if ($id -notin @('gald3r_dev') -and (Test-Path $p)) { $resolved += "$id => $p" }
    }
    if ($resolved.Count -gt 0) {
        $f4Pass = $true
        $f4Evidence += "Resolved $($resolved.Count) non-owner member(s) with existing local_path"
    } else {
        $f4Evidence += "manifest parsed ($($idMatches.Count) entries) but no non-owner member local_path exists on disk"
    }
}
Add-Result -Id 'F4' -Name 'Manifest resolves at least one member-scoped target' -Pass $f4Pass -Evidence ($f4Evidence -join '; ')

# F5. Marker-only guard + bootstrap helpers present (relocated home under .gald3r_sys/).
$guard = Join-Path $RepoRoot '.gald3r_sys\skills\g-skl-workspace\scripts\check_member_repo_gald3r_guard.ps1'
$bootstrap = Join-Path $RepoRoot '.gald3r_sys\skills\g-skl-workspace\scripts\bootstrap_member_gald3r_marker.ps1'
$f5Pass = (Test-Path $guard) -and (Test-Path $bootstrap)
$f5Evidence = if ($f5Pass) { 'guard + bootstrap helpers present under .gald3r_sys/skills/g-skl-workspace/scripts/' } else { "missing (guard=$([bool](Test-Path $guard)), bootstrap=$([bool](Test-Path $bootstrap)))" }
Add-Result -Id 'F5' -Name 'Marker-only guard + bootstrap helpers present' -Pass $f5Pass -Evidence $f5Evidence

# F6. Per-root dirty member gate documented in g-rl-33 across discovered IDE rule mirrors.
$f6Pass = $true
$f6Evidence = @()
$f6Checked = 0
foreach ($ide in $IdeRoots) {
    $rulesDir = Join-Path $RepoRoot "$ide\rules"
    if (-not (Test-Path $rulesDir)) { continue }  # not all IDE roots carry a rule mirror (e.g. .gald3r_sys, copilot)
    $rule = Get-ChildItem -LiteralPath $rulesDir -Filter 'g-rl-33-*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $rule) { $f6Pass = $false; $f6Evidence += "${ide}: g-rl-33 missing"; continue }
    $f6Checked++
    $content = Get-Content -Raw $rule.FullName
    if ($content -notmatch '(?i)per-root|every git root in the computed touch set|Pre-Reconciliation Clean Gate') {
        $f6Pass = $false; $f6Evidence += "${ide} rl-33: missing per-root touch-set language"
    }
}
if ($f6Checked -eq 0 -and $f6Pass) { $f6Evidence += 'no IDE rule mirror present to check (skipped)' }
elseif ($f6Pass) { $f6Evidence = @("g-rl-33 per-root touch-set gate present in $f6Checked IDE rule mirror(s)") }
Add-Result -Id 'F6' -Name 'Per-root dirty member gate documented in g-rl-33' -Pass $f6Pass -Evidence ($f6Evidence -join '; ')

# F7. Marker-only invariant rule (g-rl-36) installed in discovered IDE rule trees.
$f7Pass = $true
$f7Evidence = @()
$f7Checked = 0
foreach ($ide in $IdeRoots) {
    $rulesDir = Join-Path $RepoRoot "$ide\rules"
    if (-not (Test-Path $rulesDir)) { continue }
    $rule = Get-ChildItem -LiteralPath $rulesDir -Filter 'g-rl-36-*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $rule) { $f7Pass = $false; $f7Evidence += "${ide}: g-rl-36 missing"; continue }
    $f7Checked++
}
if ($f7Checked -eq 0 -and $f7Pass) { $f7Evidence += 'no IDE rule mirror present to check (skipped)' }
elseif ($f7Pass) { $f7Evidence = @("g-rl-36 marker-only guard rule present in $f7Checked IDE rule mirror(s)") }
Add-Result -Id 'F7' -Name 'Marker-only invariant rule (g-rl-36) installed' -Pass $f7Pass -Evidence ($f7Evidence -join '; ')

# F8. Manifest declares controlled members (the skip / deferred-path reason source).
$f8Pass = $false
$f8Evidence = @()
if (-not (Test-Path $ManifestPath)) {
    $f8Evidence += 'manifest missing'
} else {
    $manifestText = Get-Content -Raw $ManifestPath
    if ($manifestText -match '(?im)^\s*controlled_members:' -or $manifestText -match '(?im)workspace_role:\s*controlled_member') {
        $f8Pass = $true; $f8Evidence += 'manifest declares controlled_members / controlled_member roles'
    } else {
        $f8Evidence += 'manifest has no controlled_members block or controlled_member roles'
    }
}
Add-Result -Id 'F8' -Name 'Controlled members declared in manifest (deferred-path source)' -Pass $f8Pass -Evidence ($f8Evidence -join '; ')

# F9. Swarm workspace coordination surface present on each discovered g-go.md.
$f9Pass = ($IdeRoots.Count -ge 1)
$f9Evidence = @()
foreach ($ide in $IdeRoots) {
    $content = Get-Content -Raw (Join-Path $RepoRoot "$ide\commands\g-go.md")
    if ($content -notmatch '(?i)--swarm') { $f9Pass = $false; $f9Evidence += "${ide}: missing --swarm coordination surface" }
}
if ($f9Pass) { $f9Evidence = @('--swarm coordination surface present on all discovered g-go.md files') }
Add-Result -Id 'F9' -Name 'Swarm workspace coordination surface present' -Pass $f9Pass -Evidence ($f9Evidence -join '; ')

# --- Output ---
$total = $results.Count
$passed = ($results | Where-Object { $_.pass }).Count
$failed = $total - $passed

if ($Json) {
    [PSCustomObject]@{
        suite     = 'T532 g-go --workspace fixtures (T1532 adapted)'
        repo_root = $RepoRoot
        ide_roots = $IdeRoots
        total     = $total
        passed    = $passed
        failed    = $failed
        results   = $results
        timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    } | ConvertTo-Json -Depth 5
} else {
    Write-Host ''
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host '  g-go --workspace fixture suite (T1532)    ' -ForegroundColor Cyan
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host ("  IDE roots discovered: {0}" -f ($IdeRoots -join ', ')) -ForegroundColor DarkGray
    foreach ($r in $results) {
        $icon = if ($r.pass) { 'PASS' } else { 'FAIL' }
        $color = if ($r.pass) { 'Green' } else { 'Red' }
        Write-Host ("  [{0}] {1}: {2}" -f $icon, $r.id, $r.name) -ForegroundColor $color
        Write-Host ("        {0}" -f $r.evidence) -ForegroundColor DarkGray
    }
    Write-Host ''
    $summaryColor = if ($failed -eq 0) { 'Green' } else { 'Yellow' }
    Write-Host ("Summary: {0}/{1} passed, {2} failed" -f $passed, $total, $failed) -ForegroundColor $summaryColor
    Write-Host ''
}

if ($failed -eq 0) { exit 0 } else { exit 1 }
