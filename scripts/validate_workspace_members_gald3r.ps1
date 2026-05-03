# scripts/validate_workspace_members_gald3r.ps1
#
# Workspace-Control member-marker validator (BUG-021 / Task 213 / g-rl-36).
#
# Reads `.gald3r/linking/workspace_manifest.yaml`, enumerates every
# controlled_member and migration_source, and reports per-member marker
# compliance:
#
#   * clean              - .gald3r/ contains only .identity and/or PROJECT.md
#   * marker_missing     - member exists, .gald3r/ absent or marker incomplete
#                          (.identity and/or PROJECT.md missing)
#   * has_violations     - .gald3r/ contains forbidden control-plane content
#   * not_yet_created    - member path does not exist on disk yet
#                          (planned_clean_member is fine; migration_source is fine)
#
# Exit codes:
#   0 - all members compliant or only informational findings
#   1 - one or more members have_violations
#   2 - manifest error
#
# Used by:
#   * Standalone audit run before adopting new members like gald3r_valhalla.
#   * @g-wrkspc-validate as a workspace-validation extension.
#   * CI checks, dry-run gates, and operator review.

[CmdletBinding()]
param(
    [string]$ManifestPath = '',

    [switch]$Json,

    [switch]$WarnOnly
)

$ErrorActionPreference = 'Stop'
$markerAllowlist = @('.identity', 'PROJECT.md')

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
        $lpMatch = [regex]::Match($body, '(?m)^  local_path:\s*[''"]?([^''"\r\n]+?)[''"]?\s*$')
        if ($lpMatch.Success) { $localPath = $lpMatch.Groups[1].Value.Trim() }
        $wrMatch = [regex]::Match($body, '(?m)^  workspace_role:\s*([A-Za-z_]+)\s*$')
        if ($wrMatch.Success) { $workspaceRole = $wrMatch.Groups[1].Value.Trim() }
        $lsMatch = [regex]::Match($body, '(?m)^  lifecycle_status:\s*([A-Za-z_]+)\s*$')
        if ($lsMatch.Success) { $lifecycleStatus = $lsMatch.Groups[1].Value.Trim() }
        $entries += [pscustomobject]@{
            Id              = $id
            LocalPath       = $localPath
            WorkspaceRole   = $workspaceRole
            LifecycleStatus = $lifecycleStatus
        }
    }
    return $entries
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

$results = @()
$violationsCount = 0
$markerMissingCount = 0
$cleanCount = 0
$notCreatedCount = 0
$templateSkippedCount = 0

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

$summary = [pscustomobject]@{
    ManifestPath        = $manifestFile
    MemberCount         = $results.Count
    Clean               = $cleanCount
    HasViolations       = $violationsCount
    MarkerMissing       = $markerMissingCount
    NotYetCreated       = $notCreatedCount
    Members             = $results
    OverallStatus       = if ($violationsCount -gt 0) { 'fail' } else { 'pass' }
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 6
}
else {
    Write-Output "Workspace member marker validation"
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
    Write-Output ("Overall: {0}" -f $summary.OverallStatus.ToUpperInvariant())
}

if ($summary.OverallStatus -eq 'fail') {
    if ($WarnOnly) { exit 0 } else { exit 1 }
}
exit 0
