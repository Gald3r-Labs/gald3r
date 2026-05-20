# .gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1
#
# Workspace-Control member-marker AND license-posture validator
# (BUG-021 / Task 213 / g-rl-36 + Task 804 / C-020).
#
# Reads `.gald3r/linking/workspace_manifest.yaml`, enumerates every
# repository, and reports:
#
#   Marker compliance (controlled_member + migration_source only):
#     * clean              - .gald3r/ contains only .identity and/or PROJECT.md
#     * marker_missing     - member exists, .gald3r/ absent or marker incomplete
#                            (.identity and/or PROJECT.md missing)
#     * has_violations     - .gald3r/ contains forbidden control-plane content
#     * not_yet_created    - member path does not exist on disk yet
#                            (planned_clean_member is fine; migration_source is fine)
#
#   License posture (every repository, including control_project):
#     * license_match      - LICENSE file exists and matches manifest `license:` value
#     * license_drift      - LICENSE file exists but content does not match template
#     * license_missing    - LICENSE file absent
#     * license_undeclared - manifest entry has no `license:` key
#     * reference_archive  - skipped (historical archive, not a live workspace repo)
#
# Exit codes:
#   0 - all members compliant or only informational findings
#   1 - one or more members have_violations OR license_drift / license_missing
#   2 - manifest error
#
# Used by:
#   * Standalone audit run before adopting new members like gald3r_valhalla.
#   * @g-wrkspc-validate as a workspace-validation extension.
#   * CI checks, dry-run gates, and operator review.
#
# License canonical templates (resolved relative to controller repo root):
#   .gald3r_sys/licenses/LICENSE_FSL_TEMPLATE.txt        -> license: FSL-1.1-Apache
#   .gald3r_sys/licenses/LICENSE_PROPRIETARY_TEMPLATE.txt -> license: Proprietary

[CmdletBinding()]
param(
    [string]$ManifestPath = '',

    [switch]$Json,

    [switch]$WarnOnly,

    [switch]$SkipLicenseCheck
)

$ErrorActionPreference = 'Stop'
$markerAllowlist = @('.identity', 'PROJECT.md')

# Map of license-posture key (manifest `license:` value) to canonical template path
# (resolved relative to the manifest's controller repo root).
$LicenseTemplateMap = @{
    'FSL-1.1-Apache' = '.gald3r_sys/licenses/LICENSE_FSL_TEMPLATE.txt'
    'Proprietary'    = '.gald3r_sys/licenses/LICENSE_PROPRIETARY_TEMPLATE.txt'
}

function Find-WorkspaceManifest {
    param([string]$StartPath)
    $candidate = $StartPath
    if ($candidate -and (Test-Path -LiteralPath $candidate)) {
        $candidate = (Resolve-Path -LiteralPath $candidate).Path
    }
    while ($candidate -and (Test-Path -LiteralPath $candidate)) {
        $manifest = Join-Path -Path $candidate -ChildPath '.gald3r/linking/workspace_manifest.yaml'
        if (Test-Path -LiteralPath $manifest) { return (Resolve-Path -LiteralPath $manifest).Path }
        $parent = Split-Path -Parent -Path $candidate
        if (-not $parent -or $parent -eq $candidate) { break }
        $candidate = $parent
    }
    return $null
}

function Read-WorkspaceManifestRepositories {
    param([string]$ManifestFile)
    $content = Get-Content -LiteralPath $ManifestFile -Raw -ErrorAction Stop

    $reposBlock = $null
    $reposPattern = '(?ms)^repositories:\s*\r?\n(.*?)^controlled_members:\s*$'
    $m = [regex]::Match($content, $reposPattern)
    if ($m.Success) { $reposBlock = $m.Groups[1].Value }
    if (-not $reposBlock) { return @() }

    $entries = @()
    $entryPattern = '(?m)^- id:\s*([A-Za-z][A-Za-z0-9_]*)\s*\r?\n((?:^(?!- id:)[^\r\n]*\r?\n)*)'
    foreach ($em in [regex]::Matches($reposBlock, $entryPattern)) {
        $id = $em.Groups[1].Value
        $body = $em.Groups[2].Value
        $localPath = ''
        $workspaceRole = ''
        $lifecycleStatus = ''
        $license = ''
        $lpMatch = [regex]::Match($body, '(?m)^  local_path:\s*[''"]?([^''"\r\n]+?)[''"]?\s*$')
        if ($lpMatch.Success) { $localPath = $lpMatch.Groups[1].Value.Trim() }
        $wrMatch = [regex]::Match($body, '(?m)^  workspace_role:\s*([A-Za-z_]+)\s*$')
        if ($wrMatch.Success) { $workspaceRole = $wrMatch.Groups[1].Value.Trim() }
        $lsMatch = [regex]::Match($body, '(?m)^  lifecycle_status:\s*([A-Za-z_]+)\s*$')
        if ($lsMatch.Success) { $lifecycleStatus = $lsMatch.Groups[1].Value.Trim() }
        $licMatch = [regex]::Match($body, '(?m)^  license:\s*[''"]?([A-Za-z0-9.\-_]+)[''"]?\s*$')
        if ($licMatch.Success) { $license = $licMatch.Groups[1].Value.Trim() }
        $entries += [pscustomobject]@{
            Id              = $id
            LocalPath       = $localPath
            WorkspaceRole   = $workspaceRole
            LifecycleStatus = $lifecycleStatus
            License         = $license
        }
    }
    return $entries
}

function Test-MemberLicensePosture {
    param(
        [pscustomobject]$Repo,
        [string]$ControllerRoot,
        [hashtable]$TemplateMap
    )
    # Returns hashtable @{ Status='license_match|license_drift|license_missing|license_undeclared|license_path_missing'; Note='...'; Posture='<value>' }
    $posture = $Repo.License
    if (-not $posture) {
        return @{ Status = 'license_undeclared'; Note = "Manifest entry missing `license:` key (C-020 violation)."; Posture = '' }
    }
    if (-not $TemplateMap.ContainsKey($posture)) {
        return @{ Status = 'license_drift'; Note = "Unknown posture value `$posture` (allowed: $($TemplateMap.Keys -join ', '))."; Posture = $posture }
    }
    if (-not (Test-Path -LiteralPath $Repo.LocalPath)) {
        return @{ Status = 'license_path_missing'; Note = "Repo path does not exist; cannot inspect LICENSE."; Posture = $posture }
    }
    $licenseFile = Join-Path -Path $Repo.LocalPath -ChildPath 'LICENSE'
    if (-not (Test-Path -LiteralPath $licenseFile)) {
        return @{ Status = 'license_missing'; Note = "No LICENSE file at $licenseFile (C-020: posture is $posture)."; Posture = $posture }
    }
    $templateFile = Join-Path -Path $ControllerRoot -ChildPath $TemplateMap[$posture]
    if (-not (Test-Path -LiteralPath $templateFile)) {
        return @{ Status = 'license_drift'; Note = "Canonical template not found at $templateFile (controller setup issue)."; Posture = $posture }
    }
    $actual = (Get-Content -LiteralPath $licenseFile -Raw).Trim()
    $expected = (Get-Content -LiteralPath $templateFile -Raw).Trim()
    if ($actual -eq $expected) {
        return @{ Status = 'license_match'; Note = ''; Posture = $posture }
    }
    # Soft compare: first 400 normalized chars
    $normActual = ($actual -replace '\s+', ' ').Substring(0, [Math]::Min(400, $actual.Length))
    $normExpected = ($expected -replace '\s+', ' ').Substring(0, [Math]::Min(400, $expected.Length))
    if ($normActual -eq $normExpected) {
        return @{ Status = 'license_match'; Note = '(matched after whitespace normalization)'; Posture = $posture }
    }
    return @{ Status = 'license_drift'; Note = "LICENSE content does not match canonical $($TemplateMap[$posture])."; Posture = $posture }
}

# Resolve manifest
$manifestFile = $null
if ($ManifestPath) {
    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        Write-Error "Specified ManifestPath does not exist: $ManifestPath"
        exit 2
    }
    $manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
}
else {
    $manifestFile = Find-WorkspaceManifest -StartPath (Get-Location).Path
}

if (-not $manifestFile) {
    Write-Error 'No .gald3r/linking/workspace_manifest.yaml found in current dir or any ancestor.'
    exit 2
}

try {
    $repos = Read-WorkspaceManifestRepositories -ManifestFile $manifestFile
}
catch {
    Write-Error "Could not parse workspace manifest: $($_.Exception.Message)"
    exit 2
}

# Controller repo root = directory holding .gald3r/linking/workspace_manifest.yaml
$controllerRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $manifestFile))

$results = @()
$violationsCount = 0
$markerMissingCount = 0
$cleanCount = 0
$notCreatedCount = 0
$templateSkippedCount = 0
$licenseMatchCount = 0
$licenseDriftCount = 0
$licenseMissingCount = 0
$licenseUndeclaredCount = 0

# License-posture sweep (every repository — including control_project)
$licenseResults = @()
if (-not $SkipLicenseCheck) {
    foreach ($r in $repos) {
        if ($r.WorkspaceRole -eq 'reference_archive') {
            $licenseResults += [pscustomobject]@{
                Id        = $r.Id
                LocalPath = $r.LocalPath
                Posture   = $r.License
                Status    = 'reference_archive'
                Note      = 'Reference archive skipped by C-020 license validation.'
            }
            continue
        }
        $check = Test-MemberLicensePosture -Repo $r -ControllerRoot $controllerRoot -TemplateMap $LicenseTemplateMap
        $licenseResults += [pscustomobject]@{
            Id        = $r.Id
            LocalPath = $r.LocalPath
            Posture   = $check.Posture
            Status    = $check.Status
            Note      = $check.Note
        }
        switch ($check.Status) {
            'license_match'        { $licenseMatchCount++ }
            'license_drift'        { $licenseDriftCount++ }
            'license_missing'      { $licenseMissingCount++ }
            'license_undeclared'   { $licenseUndeclaredCount++ }
            default                { } # license_path_missing — informational
        }
    }
}

foreach ($r in $repos) {
    if ($r.WorkspaceRole -ne 'controlled_member' -and $r.WorkspaceRole -ne 'migration_source') {
        continue
    }
    # Installable template repos intentionally ship full `.gald3r/` scaffolding (g-rl-36 template_directory_exception).
    if ($r.Id -match '^gald3r_template_(slim|full|adv)$') {
        $templateSkippedCount++
        continue
    }
    $memberPath = $r.LocalPath
    $resultEntry = [pscustomobject]@{
        Id              = $r.Id
        LocalPath       = $memberPath
        WorkspaceRole   = $r.WorkspaceRole
        LifecycleStatus = $r.LifecycleStatus
        Status          = ''
        MarkerPreserved = @()
        Forbidden       = @()
        Notes           = @()
    }

    if (-not (Test-Path -LiteralPath $memberPath)) {
        $resultEntry.Status = 'not_yet_created'
        $resultEntry.Notes += "Path does not exist on disk; lifecycle_status=$($r.LifecycleStatus)."
        $notCreatedCount++
        $results += $resultEntry
        continue
    }

    $dotGald3r = Join-Path -Path $memberPath -ChildPath '.gald3r'
    if (-not (Test-Path -LiteralPath $dotGald3r)) {
        $resultEntry.Status = 'marker_missing'
        $resultEntry.Notes += '.gald3r/ directory absent. Run bootstrap_member_gald3r_marker.ps1 -Apply to create the marker.'
        $markerMissingCount++
        $results += $resultEntry
        continue
    }

    $entries = Get-ChildItem -LiteralPath $dotGald3r -Force -ErrorAction SilentlyContinue
    foreach ($entry in $entries) {
        if ($entry.Name -in $markerAllowlist) {
            $resultEntry.MarkerPreserved += $entry.Name
        }
        else {
            $resultEntry.Forbidden += $entry.Name
        }
    }

    if ($resultEntry.Forbidden.Count -gt 0) {
        $resultEntry.Status = 'has_violations'
        $resultEntry.Notes += "Run remediate_member_gald3r_marker.ps1 -MemberPath '$memberPath' (dry-run first, then -Apply)."
        $violationsCount++
    }
    else {
        $missingMarker = @()
        foreach ($req in $markerAllowlist) {
            if ($req -notin $resultEntry.MarkerPreserved) { $missingMarker += $req }
        }
        if ($missingMarker.Count -gt 0) {
            $resultEntry.Status = 'marker_incomplete'
            $resultEntry.Notes += "Marker pair incomplete: missing $($missingMarker -join ', '). Run bootstrap_member_gald3r_marker.ps1 -Apply to fill in."
            $markerMissingCount++
        }
        else {
            $resultEntry.Status = 'clean'
            $cleanCount++
        }
    }
    $results += $resultEntry
}

$licenseFail = ($licenseDriftCount + $licenseMissingCount + $licenseUndeclaredCount) -gt 0

$summary = [pscustomobject]@{
    ManifestPath        = $manifestFile
    MemberCount         = $results.Count
    Clean               = $cleanCount
    HasViolations       = $violationsCount
    MarkerMissing       = $markerMissingCount
    NotYetCreated       = $notCreatedCount
    Members             = $results
    LicenseChecked      = (-not $SkipLicenseCheck)
    LicenseRepoCount    = $licenseResults.Count
    LicenseMatch        = $licenseMatchCount
    LicenseDrift        = $licenseDriftCount
    LicenseMissing      = $licenseMissingCount
    LicenseUndeclared   = $licenseUndeclaredCount
    Licenses            = $licenseResults
    OverallStatus       = if ($violationsCount -gt 0 -or $licenseFail) { 'fail' } else { 'pass' }
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 6
}
else {
    Write-Output "Workspace member marker + license validation"
    Write-Output ("  manifest         : {0}" -f $manifestFile)
    Write-Output ("  member count     : {0}" -f $results.Count)
    if ($templateSkippedCount -gt 0) {
        Write-Output ("  template_skipped : {0}  (gald3r_template_slim|full|adv carry intentional install .gald3r/)" -f $templateSkippedCount)
    }
    Write-Output ("  clean            : {0}" -f $cleanCount)
    Write-Output ("  has_violations   : {0}" -f $violationsCount)
    Write-Output ("  marker_missing   : {0}" -f $markerMissingCount)
    Write-Output ("  not_yet_created  : {0}" -f $notCreatedCount)
    Write-Output ""
    foreach ($m in $results) {
        Write-Output ("[{0}] {1}  ({2}/{3})" -f $m.Status.ToUpperInvariant(), $m.Id, $m.WorkspaceRole, $m.LifecycleStatus)
        Write-Output ("  local_path      : {0}" -f $m.LocalPath)
        if ($m.MarkerPreserved.Count -gt 0) {
            Write-Output ("  marker          : {0}" -f ($m.MarkerPreserved -join ', '))
        }
        if ($m.Forbidden.Count -gt 0) {
            Write-Output ("  forbidden       : {0}" -f ($m.Forbidden -join ', '))
        }
        foreach ($n in $m.Notes) { Write-Output ("  note            : {0}" -f $n) }
        Write-Output ""
    }
    if (-not $SkipLicenseCheck) {
        Write-Output "License posture (C-020):"
        Write-Output ("  license_match    : {0}" -f $licenseMatchCount)
        Write-Output ("  license_drift    : {0}" -f $licenseDriftCount)
        Write-Output ("  license_missing  : {0}" -f $licenseMissingCount)
        Write-Output ("  license_undeclared: {0}" -f $licenseUndeclaredCount)
        foreach ($l in $licenseResults) {
            Write-Output ("[{0}] {1}  posture={2}" -f $l.Status.ToUpperInvariant(), $l.Id, $l.Posture)
            if ($l.Note) { Write-Output ("  note            : {0}" -f $l.Note) }
        }
        Write-Output ""
    }
    Write-Output ("Overall: {0}" -f $summary.OverallStatus.ToUpperInvariant())
}

if ($summary.OverallStatus -eq 'fail') {
    if ($WarnOnly) { exit 0 } else { exit 1 }
}
exit 0
