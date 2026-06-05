<#
.SYNOPSIS
    Verification fixtures for the `g-go-go` maximal autopilot command (T533
    contract), adapted for the gald3r_templates repo (T1532).

.DESCRIPTION
    Documentation-and-policy fixtures for the autopilot contract. Like the
    workspace-mode fixtures, `g-go-go` is an LLM-executed prompt; these fixtures
    verify that the behavior-contract surfaces are intact across the IDE command
    surfaces PRESENT IN THIS REPO and that the safety primitives the autopilot
    depends on are present.

    ADAPTATION NOTES (T1532, restore-from-split):
    - IDE command surfaces are DISCOVERED dynamically (any top-level
      `.<ide>/commands/g-go-go.md`), not hardcoded to the old gald3r_dev 6-IDE
      list. This tracks the D015 parity IDE targets actually installed in this
      repo (currently .cursor, .claude, .gald3r_sys).
    - The workspace manifest is read from the RELOCATED path
      `.gald3r/workspace/workspace_manifest.yaml` (NOT the old `.gald3r/linking/`).
    - The marker-only guard helper is read from its current home
      `.gald3r_sys/skills/g-skl-workspace/scripts/`.
    - Content fixtures verify the autopilot SAFETY PRIMITIVE SURFACES exist
      (command present, default workspace+swarm loop, hard-stops surface,
      file-first fallback, member-scoped routing, marker-only protection,
      heartbeat/final-summary, bare /g-go preserved, manifest parseable, guard
      present) rather than matching exact legacy wording, which has intentionally
      drifted since the split. Missing surfaces fail closed.

.PARAMETER Json
    Emit machine-readable JSON instead of human-readable lines.

.EXAMPLE
    .\custom_scripts\tests\test_g_go_go_autopilot_fixtures.ps1
.EXAMPLE
    .\custom_scripts\tests\test_g_go_go_autopilot_fixtures.ps1 -Json
#>

[CmdletBinding()]
param(
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $RepoRoot

# D015 parity: discover IDE command-surface roots actually present in this repo.
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

$IdeRoots = Get-IdeCommandRoots -CommandFile 'g-go-go.md'
$ManifestPath = Join-Path $RepoRoot '.gald3r\workspace\workspace_manifest.yaml'
$results = @()

function Add-Result {
    param([string]$Id, [string]$Name, [bool]$Pass, [string]$Evidence)
    $script:results += [PSCustomObject]@{ id = $Id; name = $Name; pass = $Pass; evidence = $Evidence }
}

# Helper: require a regex (or all of several) present in every discovered g-go-go.md.
function Test-AcrossGoGo {
    param([string[]]$Patterns, [string]$Description)
    if ($IdeRoots.Count -lt 1) { return [PSCustomObject]@{ Pass = $false; Missing = @('no g-go-go.md command surface found') } }
    $allPass = $true
    $missing = @()
    foreach ($ide in $IdeRoots) {
        $content = Get-Content -Raw (Join-Path $RepoRoot "$ide\commands\g-go-go.md")
        foreach ($pat in $Patterns) {
            if ($content -notmatch $pat) { $allPass = $false; $missing += "${ide}: $Description"; break }
        }
    }
    return [PSCustomObject]@{ Pass = $allPass; Missing = ($missing | Sort-Object -Unique) }
}

# F1. Command surface present.
$f1Pass = ($IdeRoots.Count -ge 1)
$f1Evidence = if ($f1Pass) { "g-go-go.md discovered in: $($IdeRoots -join ', ')" } else { 'no IDE command surface with g-go-go.md found' }
Add-Result -Id 'F1' -Name 'Command surface present (discovered IDE roots)' -Pass $f1Pass -Evidence $f1Evidence

# F2. Default = workspace + swarm rolling loop.
$r = Test-AcrossGoGo -Description 'missing default workspace+swarm rolling-loop surface' -Patterns @('(?i)--swarm', '(?i)--workspace', '(?i)loop|rolling|budget')
$f2Evidence = if ($r.Pass) { @('All discovered g-go-go.md files surface swarm+workspace rolling loop with budget') } else { $r.Missing }
Add-Result -Id 'F2' -Name 'Default = workspace + swarm + rolling loop with budget' -Pass $r.Pass -Evidence ($f2Evidence -join '; ')

# F3. File-first fallback documented.
$r = Test-AcrossGoGo -Description 'missing file-first / backend-optional fallback language' -Patterns @('(?i)file-first|file first|fallback', '(?i)backend')
$f3Evidence = if ($r.Pass) { @('All discovered g-go-go.md files document file-first / backend-optional fallback') } else { $r.Missing }
Add-Result -Id 'F3' -Name 'File-first fallback documented' -Pass $r.Pass -Evidence ($f3Evidence -join '; ')

# F4. Hard stops surface present.
$r = Test-AcrossGoGo -Description 'missing hard-stop / stop-condition surface' -Patterns @('(?i)hard stop|stop condition|stop reason|Run budget exhausted|No runnable work')
$f4Evidence = if ($r.Pass) { @('All discovered g-go-go.md files document hard-stop conditions') } else { $r.Missing }
Add-Result -Id 'F4' -Name 'Hard stops surface present' -Pass $r.Pass -Evidence ($f4Evidence -join '; ')

# F5. Member-scoped routing gates documented.
$r = Test-AcrossGoGo -Description 'missing workspace_repos / workspace_touch_policy routing' -Patterns @('(?i)workspace_repos', '(?i)workspace_touch_policy|touch_policy|per-repo|per-root')
$f5Evidence = if ($r.Pass) { @('All discovered g-go-go.md files reference workspace_repos + touch-policy / per-repo gates') } else { $r.Missing }
Add-Result -Id 'F5' -Name 'Member-scoped routing gates documented' -Pass $r.Pass -Evidence ($f5Evidence -join '; ')

# F6. Marker-only protection language.
$r = Test-AcrossGoGo -Description 'missing marker-only invariant language' -Patterns @('(?i)marker-only')
$f6Evidence = if ($r.Pass) { @('All discovered g-go-go.md files reference the marker-only `.gald3r/` invariant') } else { $r.Missing }
Add-Result -Id 'F6' -Name 'Marker-only `.gald3r/` invariant referenced' -Pass $r.Pass -Evidence ($f6Evidence -join '; ')

# F7. Rolling-loop iteration / budget mechanics.
$r = Test-AcrossGoGo -Description 'missing iteration/budget loop mechanics' -Patterns @('(?i)budget', '(?i)loop|iteration|iter')
$f7Evidence = if ($r.Pass) { @('All discovered g-go-go.md files document iter/budget loop mechanics') } else { $r.Missing }
Add-Result -Id 'F7' -Name 'Rolling-loop iteration/budget mechanics documented' -Pass $r.Pass -Evidence ($f7Evidence -join '; ')

# F8. Verification independence - reviewers spawned without Phase 1 context.
$r = Test-AcrossGoGo -Description 'missing verification-independence language' -Patterns @('(?i)fresh reviewer|no Phase 1 context|independent review|never self-verify|adversarial')
$f8Evidence = if ($r.Pass) { @('All discovered g-go-go.md files preserve adversarial review independence') } else { $r.Missing }
Add-Result -Id 'F8' -Name 'Verification independence preserved across loop' -Pass $r.Pass -Evidence ($f8Evidence -join '; ')

# F9. Heartbeat output surface.
$r = Test-AcrossGoGo -Description 'missing heartbeat surface' -Patterns @('(?i)heartbeat')
$f9Evidence = if ($r.Pass) { @('All discovered g-go-go.md files include a heartbeat surface') } else { $r.Missing }
Add-Result -Id 'F9' -Name 'Heartbeat output surface present' -Pass $r.Pass -Evidence ($f9Evidence -join '; ')

# F10. Final summary surface.
$r = Test-AcrossGoGo -Description 'missing final-summary surface' -Patterns @('(?i)final summary|session summary')
$f10Evidence = if ($r.Pass) { @('All discovered g-go-go.md files include a final/session summary surface') } else { $r.Missing }
Add-Result -Id 'F10' -Name 'Final summary surface present' -Pass $r.Pass -Evidence ($f10Evidence -join '; ')

# F11. Bare /g-go preserved - autopilot is explicit, not an alias.
$r = Test-AcrossGoGo -Description 'missing bare /g-go preservation language' -Patterns @('(?i)bare\s*`?/?g-go`?', '(?i)unchanged|explicit|not an alias|separate')
$f11Evidence = if ($r.Pass) { @('All discovered g-go-go.md files preserve bare /g-go as a separate explicit command') } else { $r.Missing }
Add-Result -Id 'F11' -Name 'Bare /g-go preserved (autopilot is explicit opt-in)' -Pass $r.Pass -Evidence ($f11Evidence -join '; ')

# F12. Manifest resolves - workspace manifest parseable for autopilot member work.
$f12Pass = $false
$f12Evidence = @()
if (-not (Test-Path $ManifestPath)) {
    $f12Evidence += "manifest missing at $ManifestPath"
} else {
    $manifestText = Get-Content -Raw $ManifestPath
    $idMatches = [regex]::Matches($manifestText, '(?ms)^- id:\s+(?<id>[a-z][a-z0-9_]*).*?^  local_path:\s+(?<path>.+?)$')
    if ($idMatches.Count -ge 2) {
        $f12Pass = $true
        $f12Evidence += "Manifest parseable; $($idMatches.Count) repository entries with id+local_path"
    } else {
        $f12Evidence += "manifest has too few parseable entries ($($idMatches.Count))"
    }
}
Add-Result -Id 'F12' -Name 'Workspace manifest parseable for autopilot' -Pass $f12Pass -Evidence ($f12Evidence -join '; ')

# F13. Guard helper present (relocated home under .gald3r_sys/).
$guard = Join-Path $RepoRoot '.gald3r_sys\skills\g-skl-workspace\scripts\check_member_repo_gald3r_guard.ps1'
$f13Pass = Test-Path $guard
$f13Evidence = if ($f13Pass) { 'guard helper present at .gald3r_sys/skills/g-skl-workspace/scripts/' } else { 'guard helper missing' }
Add-Result -Id 'F13' -Name 'Marker-only guard helper present' -Pass $f13Pass -Evidence $f13Evidence

# --- Output ---
$total = $results.Count
$passed = ($results | Where-Object { $_.pass }).Count
$failed = $total - $passed

if ($Json) {
    [PSCustomObject]@{
        suite     = 'T533 g-go-go autopilot fixtures (T1532 adapted)'
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
    Write-Host '  g-go-go autopilot fixture suite (T1532)   ' -ForegroundColor Cyan
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
