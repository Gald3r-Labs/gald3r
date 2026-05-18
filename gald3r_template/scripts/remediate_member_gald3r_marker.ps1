param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$MemberPath,

    [string]$BackupTo = '',

    [string]$ManifestPath = '',

    [switch]$Apply,

    [switch]$Json
)

# scripts/remediate_member_gald3r_marker.ps1
#
# Remediate an existing Workspace-Control member repository's `.gald3r/`
# folder so it conforms to the marker-only invariant
# (BUG-021 / Task 213 / g-rl-36).
#
# Default mode is dry-run: scans `.gald3r/` content and categorises each
# entry as marker-safe (`.identity`, `PROJECT.md`) or forbidden control
# plane. Reports planned actions without touching the filesystem.
#
# With -Apply: moves forbidden entries to a quarantine folder
# (`<member_root>/.gald3r-quarantine/<timestamp>/`) by default, or to the
# explicit -BackupTo path. Marker entries are preserved in place. Nothing
# is permanently deleted.

$ErrorActionPreference = 'Stop'
$markerAllowlist = @('.identity', 'PROJECT.md')

function ConvertTo-NormalPath {
    param([string]$InputPath)
    if (-not $InputPath) { return '' }
    $resolved = $InputPath
    try { $resolved = (Resolve-Path -LiteralPath $InputPath -ErrorAction Stop).ProviderPath } catch { $resolved = $InputPath }
    return ($resolved -replace '\\', '/').TrimEnd('/')
}

function Write-RemediateResult {
    param([pscustomobject]$Result, [switch]$AsJson)
    if ($AsJson) {
        $Result | ConvertTo-Json -Depth 6
        return
    }
    $statusToken = $Result.Status.ToUpperInvariant()
    Write-Output "[$statusToken] member-marker remediate: $($Result.Reason)"
    if ($Result.Message) { Write-Output "  $($Result.Message)" }
    if ($Result.MemberPath) { Write-Output "  member_path     : $($Result.MemberPath)" }
    if ($Result.MatchedRepoId) { Write-Output "  matched_repo_id : $($Result.MatchedRepoId)" }
    if ($Result.QuarantineDir) { Write-Output "  quarantine_dir  : $($Result.QuarantineDir)" }
    if ($Result.MarkerPreserved -and $Result.MarkerPreserved.Count -gt 0) {
        Write-Output "  preserved (marker):"
        foreach ($p in $Result.MarkerPreserved) { Write-Output "    - $p" }
    }
    if ($Result.Forbidden -and $Result.Forbidden.Count -gt 0) {
        Write-Output "  forbidden (control plane):"
        foreach ($p in $Result.Forbidden) { Write-Output "    - $p" }
    }
    if ($Result.Actions -and $Result.Actions.Count -gt 0) {
        Write-Output "  planned actions:"
        foreach ($a in $Result.Actions) { Write-Output "    - $a" }
    }
}

if (-not (Test-Path -LiteralPath $MemberPath)) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'member_path_not_found'
        Message    = "Member path does not exist: $MemberPath"
        MemberPath = $MemberPath
    }
    Write-RemediateResult -Result $err -AsJson:$Json
    exit 2
}

$normalMember = ConvertTo-NormalPath -InputPath $MemberPath

$guardScript = Join-Path -Path $PSScriptRoot -ChildPath 'check_member_repo_gald3r_guard.ps1'
if (-not (Test-Path -LiteralPath $guardScript)) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'guard_helper_missing'
        Message    = "Companion guard helper not found at $guardScript"
        MemberPath = $normalMember
    }
    Write-RemediateResult -Result $err -AsJson:$Json
    exit 2
}

if ($ManifestPath) {
    $guardOutput = & $guardScript -TargetPath $MemberPath -AllowMarkerInit -Json -ManifestPath $ManifestPath 2>&1 | Out-String
}
else {
    $guardOutput = & $guardScript -TargetPath $MemberPath -AllowMarkerInit -Json 2>&1 | Out-String
}
try {
    $guardResult = $guardOutput | ConvertFrom-Json
}
catch {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'guard_parse_failed'
        Message    = "Could not parse guard output: $($_.Exception.Message)"
        MemberPath = $normalMember
    }
    Write-RemediateResult -Result $err -AsJson:$Json
    exit 2
}

if ($guardResult.MatchedRole -ne 'controlled_member' -and $guardResult.MatchedRole -ne 'migration_source') {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'not_a_member_repository'
        Message    = "Target is not a Workspace-Control controlled_member or migration_source. Remediation only applies to member repositories. Guard reason: $($guardResult.Reason)"
        MemberPath = $normalMember
    }
    Write-RemediateResult -Result $err -AsJson:$Json
    exit 2
}

$matchedId = $guardResult.MatchedRepoId
$dotGald3r = Join-Path -Path $MemberPath -ChildPath '.gald3r'

if (-not (Test-Path -LiteralPath $dotGald3r)) {
    $clean = [pscustomobject]@{
        Status          = 'clean'
        Reason          = 'no_dot_gald3r'
        Message         = "Member $matchedId has no .gald3r/ directory. Nothing to remediate."
        MemberPath      = $normalMember
        MatchedRepoId   = $matchedId
        MarkerPreserved = @()
        Forbidden       = @()
        Actions         = @()
    }
    Write-RemediateResult -Result $clean -AsJson:$Json
    exit 0
}

$markerPreserved = @()
$forbidden = @()
$entries = Get-ChildItem -LiteralPath $dotGald3r -Force -ErrorAction SilentlyContinue
foreach ($entry in $entries) {
    if ($entry.Name -in $markerAllowlist) {
        $markerPreserved += $entry.Name
    }
    else {
        $forbidden += $entry.Name
    }
}

if ($forbidden.Count -eq 0) {
    $clean = [pscustomobject]@{
        Status          = 'clean'
        Reason          = 'already_marker_only'
        Message         = "Member $matchedId .gald3r/ is already marker-only. No remediation needed."
        MemberPath      = $normalMember
        MatchedRepoId   = $matchedId
        MarkerPreserved = $markerPreserved
        Forbidden       = @()
        Actions         = @()
    }
    Write-RemediateResult -Result $clean -AsJson:$Json
    exit 0
}

if ($BackupTo) {
    $quarantineDir = $BackupTo
}
else {
    $timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
    $quarantineDir = Join-Path -Path $MemberPath -ChildPath ".gald3r-quarantine/$timestamp"
}

$actions = @()
foreach ($entry in $forbidden) {
    $dst = Join-Path -Path $quarantineDir -ChildPath $entry
    $actions += "move: .gald3r/$entry -> $dst"
}
foreach ($entry in $markerPreserved) {
    $actions += "preserve: .gald3r/$entry"
}

if (-not $Apply) {
    $plan = [pscustomobject]@{
        Status          = 'plan'
        Reason          = 'dry_run'
        Message         = "Dry-run: $($forbidden.Count) forbidden entries would be quarantined to $quarantineDir. Pass -Apply to execute."
        MemberPath      = $normalMember
        MatchedRepoId   = $matchedId
        QuarantineDir   = $quarantineDir
        MarkerPreserved = $markerPreserved
        Forbidden       = $forbidden
        Actions         = $actions
    }
    Write-RemediateResult -Result $plan -AsJson:$Json
    exit 0
}

if (-not (Test-Path -LiteralPath $quarantineDir)) {
    New-Item -ItemType Directory -Path $quarantineDir -Force | Out-Null
}

$movedActions = @()
foreach ($entry in $forbidden) {
    $src = Join-Path -Path $dotGald3r -ChildPath $entry
    $dst = Join-Path -Path $quarantineDir -ChildPath $entry
    Move-Item -LiteralPath $src -Destination $dst -Force
    $movedActions += "moved: .gald3r/$entry -> $dst"
}
foreach ($entry in $markerPreserved) {
    $movedActions += "preserved: .gald3r/$entry"
}

$applied = [pscustomobject]@{
    Status          = 'applied'
    Reason          = 'remediation_complete'
    Message         = "Quarantined $($forbidden.Count) forbidden entries from member $matchedId .gald3r/. Marker preserved. Review and delete the quarantine folder when no longer needed."
    MemberPath      = $normalMember
    MatchedRepoId   = $matchedId
    QuarantineDir   = $quarantineDir
    MarkerPreserved = $markerPreserved
    Forbidden       = $forbidden
    Actions         = $movedActions
}
Write-RemediateResult -Result $applied -AsJson:$Json
exit 0
