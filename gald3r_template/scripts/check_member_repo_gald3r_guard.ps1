# scripts/check_member_repo_gald3r_guard.ps1
#
# Workspace-Control member-repo .gald3r/ guard.
#
# Purpose: block accidental live control-plane `.gald3r/` writes into ordinary
# Workspace-Control members while allowing installable template repos to carry
# their intended template `.gald3r/` content.
#
# Non-template member repos may contain ONLY a slim `.gald3r/` marker:
#   * .gald3r/.identity      -  identifies the member; ties back to controller
#   * .gald3r/PROJECT.md     -  copied / parity-maintained from controller
#
# Non-template member repos must NOT contain live gald3r control-plane files or folders:
#   * .gald3r/TASKS.md, tasks/, BUGS.md, bugs/, PLAN.md, FEATURES.md,
#     SUBSYSTEMS.md, RELEASES.md, CONSTRAINTS.md, IDEA_BOARD.md, PRDS.md,
#     config/, linking/, experiments/, logs/, reports/, archive/,
#     specifications_collection/, features/, releases/, subsystems/, prds/,
#     or any other orchestration state.
#
# Live `.gald3r/` belongs to the workspace control project (e.g. gald3r_dev).
# External template repos under gald3r_template_(slim|full|adv) are the legitimate
# exception - their `.gald3r/` content is intentional install template content.
#
# Returns:
#   0 - clear (write is allowed)
#   1 - block (member repo + control-plane path)
#   2 - input or manifest error
#
# Modes (mutually informative):
#   * Default (no -DotGald3rPath, no -AllowMarkerInit):
#       For member targets, BLOCK because intent is unspecified and most
#       callers historically write the full control plane. Forces callers
#       to choose either explicit per-path checks or marker-init mode.
#   * -DotGald3rPath <relative_path>:
#       Evaluate the specific path. ALLOW iff it is the .identity file or
#       the PROJECT.md file. BLOCK for any other path inside .gald3r/.
#   * -AllowMarkerInit:
#       Caller asserts they will only write marker-safe files (.identity,
#       PROJECT.md). Guard returns ALLOW. The bootstrap helper enforces
#       the actual filesystem boundary.
#
# Usage:
#   ./scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <path>
#   ./scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <path> -DotGald3rPath ".identity"
#   ./scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <path> -DotGald3rPath "TASKS.md"
#   ./scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <path> -AllowMarkerInit
#   ./scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <path> -WarnOnly -Json

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TargetPath,

    [string]$DotGald3rPath = '',

    [switch]$AllowMarkerInit,

    [string]$ManifestPath = '',

    [switch]$WarnOnly,

    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# Marker allowlist: relative paths inside .gald3r/ that are safe in member repos.
# Bare basenames only (one level under .gald3r/). Anything else is control plane.
$MarkerAllowlist = @('.identity', 'PROJECT.md')

# Forbidden examples for diagnostic output (not exhaustive  -  anything not in
# the allowlist is forbidden).
$ControlPlaneExamples = @(
    'TASKS.md', 'tasks/', 'BUGS.md', 'bugs/', 'PLAN.md', 'FEATURES.md',
    'SUBSYSTEMS.md', 'RELEASES.md', 'CONSTRAINTS.md', 'IDEA_BOARD.md',
    'PRDS.md', 'config/', 'linking/', 'experiments/', 'logs/', 'reports/',
    'archive/', 'specifications_collection/', 'features/', 'releases/',
    'subsystems/', 'prds/', 'learned-facts.md'
)

function ConvertTo-NormalPath {
    param([string]$Path)
    if (-not $Path) { return '' }
    $resolved = $Path
    try { $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath } catch { $resolved = $Path }
    $resolved = $resolved -replace '\\', '/'
    return $resolved.TrimEnd('/').ToLowerInvariant()
}

function ConvertTo-DotGald3rRelative {
    param([string]$Path)
    if (-not $Path) { return '' }
    $p = $Path -replace '\\', '/'
    # Strip any leading ".gald3r/" prefix the caller may have included.
    $p = $p -replace '^\.gald3r/+', ''
    $p = $p -replace '^/+', ''
    return $p.TrimEnd('/')
}

function Test-IsMarkerSafePath {
    param([string]$DotGald3rRelative)
    if (-not $DotGald3rRelative) { return $false }
    foreach ($allowed in $MarkerAllowlist) {
        if ($DotGald3rRelative -ieq $allowed) { return $true }
    }
    return $false
}

function Test-IsTemplatePath {
    param([string]$NormalPath)
    if (-not $NormalPath) { return $false }
    return ($NormalPath -match '/gald3r_template_(slim|full|adv)(/|$)')
}

function Find-WorkspaceManifest {
    param([string]$StartPath)
    $candidate = $StartPath
    if (Test-Path -LiteralPath $candidate) {
        $candidate = (Resolve-Path -LiteralPath $candidate).Path
    }
    while ($candidate -and (Test-Path -LiteralPath $candidate)) {
        $manifest = Join-Path -Path $candidate -ChildPath '.gald3r/linking/workspace_manifest.yaml'
        if (Test-Path -LiteralPath $manifest) { return (Resolve-Path -LiteralPath $manifest).Path }
        $parent = Split-Path -Parent -Path $candidate
        if (-not $parent -or $parent -eq $candidate) { break }
        $candidate = $parent
    }
    $cwd = (Get-Location).Path
    while ($cwd) {
        $manifest = Join-Path -Path $cwd -ChildPath '.gald3r/linking/workspace_manifest.yaml'
        if (Test-Path -LiteralPath $manifest) { return (Resolve-Path -LiteralPath $manifest).Path }
        $parent = Split-Path -Parent -Path $cwd
        if (-not $parent -or $parent -eq $cwd) { break }
        $cwd = $parent
    }
    return $null
}

function Read-WorkspaceManifestRepositories {
    param([string]$ManifestFile)
    $content = Get-Content -LiteralPath $ManifestFile -Raw -ErrorAction Stop

    $reposBlock = $null
    # v1 workspace manifest: sequence items are `- id:` at line start; fields use two-space indent.
    # Block ends at top-level `controlled_members:` (sibling of `repositories:`).
    $reposPattern = '(?ms)^repositories:\s*\r?\n(.*?)^controlled_members:\s*$'
    $m = [regex]::Match($content, $reposPattern)
    if ($m.Success) { $reposBlock = $m.Groups[1].Value }
    if (-not $reposBlock) { return @() }

    $entries = @()
    # Do not use (?s) here: . would span newlines and swallow subsequent `- id:` repo headers.
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

function Write-Result {
    param([pscustomobject]$Result, [switch]$AsJson)
    if ($AsJson) {
        $Result | ConvertTo-Json -Depth 6
        return
    }
    $statusToken = $Result.Status.ToUpperInvariant()
    Write-Output "[$statusToken] member-repo .gald3r guard: $($Result.Reason)"
    if ($Result.Message) { Write-Output "  $($Result.Message)" }
    if ($Result.MatchedRepoId) {
        Write-Output "  matched_repo_id : $($Result.MatchedRepoId)"
        Write-Output "  matched_role    : $($Result.MatchedRole)"
    }
    if ($Result.DotGald3rPath) {
        Write-Output "  dot_gald3r_path  : $($Result.DotGald3rPath)"
    }
    if ($Result.MarkerAllowlist) {
        Write-Output "  marker_allowed  : $($Result.MarkerAllowlist -join ', ')"
    }
    if ($Result.ManifestPath) { Write-Output "  manifest        : $($Result.ManifestPath)" }
    Write-Output "  target_path     : $($Result.TargetPath)"
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

if (-not $TargetPath) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'missing_target_path'
        Message    = 'TargetPath is required.'
        TargetPath = ''
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

$normalTarget = ConvertTo-NormalPath -Path $TargetPath
$relativeDotPath = ConvertTo-DotGald3rRelative -Path $DotGald3rPath

if (Test-IsTemplatePath -NormalPath $normalTarget) {
    $allow = [pscustomobject]@{
        Status       = 'allow'
        Reason       = 'template_directory_exception'
        Message      = 'Target is inside a gald3r_template_(slim|full|adv) repo; .gald3r/ template content is allowed.'
        TargetPath   = $normalTarget
        DotGald3rPath = $relativeDotPath
    }
    Write-Result -Result $allow -AsJson:$Json
    exit 0
}

$manifestFile = $null
if ($ManifestPath) {
    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        $err = [pscustomobject]@{
            Status     = 'error'
            Reason     = 'manifest_not_found'
            Message    = "Specified ManifestPath does not exist: $ManifestPath"
            TargetPath = $normalTarget
        }
        Write-Result -Result $err -AsJson:$Json
        exit 2
    }
    $manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
}
else {
    $manifestFile = Find-WorkspaceManifest -StartPath $TargetPath
}

if (-not $manifestFile) {
    $allow = [pscustomobject]@{
        Status       = 'allow'
        Reason       = 'no_workspace_manifest'
        Message      = 'No .gald3r/linking/workspace_manifest.yaml found near target. Workspace-Control inactive; member-repo boundary not enforced.'
        TargetPath   = $normalTarget
        ManifestPath = $null
        DotGald3rPath = $relativeDotPath
    }
    Write-Result -Result $allow -AsJson:$Json
    exit 0
}

$repos = @()
try {
    $repos = Read-WorkspaceManifestRepositories -ManifestFile $manifestFile
}
catch {
    $err = [pscustomobject]@{
        Status       = 'error'
        Reason       = 'manifest_parse_failed'
        Message      = "Could not parse repositories block: $($_.Exception.Message)"
        TargetPath   = $normalTarget
        ManifestPath = $manifestFile
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

if (-not $repos -or $repos.Count -eq 0) {
    $allow = [pscustomobject]@{
        Status       = 'allow'
        Reason       = 'manifest_empty_repositories'
        Message      = 'Workspace manifest parsed but no repositories[] entries found. Boundary not enforced.'
        TargetPath   = $normalTarget
        ManifestPath = $manifestFile
        DotGald3rPath = $relativeDotPath
    }
    Write-Result -Result $allow -AsJson:$Json
    exit 0
}

$normalTargetWithSlash = "$normalTarget/"
$match = $null
foreach ($r in $repos) {
    if (-not $r.LocalPath) { continue }
    $rNorm = ($r.LocalPath -replace '\\', '/').TrimEnd('/').ToLowerInvariant()
    if (-not $rNorm) { continue }
    if ($normalTarget -eq $rNorm -or $normalTargetWithSlash.StartsWith("$rNorm/")) {
        $match = $r
        break
    }
}

if (-not $match) {
    $allow = [pscustomobject]@{
        Status       = 'allow'
        Reason       = 'outside_workspace'
        Message      = 'Target path is not registered as any workspace repository.'
        TargetPath   = $normalTarget
        ManifestPath = $manifestFile
        DotGald3rPath = $relativeDotPath
    }
    Write-Result -Result $allow -AsJson:$Json
    exit 0
}

if ($match.WorkspaceRole -eq 'control_project') {
    $allow = [pscustomobject]@{
        Status        = 'allow'
        Reason        = 'control_project'
        Message       = "Target is the workspace control project ($($match.Id)); .gald3r/ is permitted here."
        TargetPath    = $normalTarget
        ManifestPath  = $manifestFile
        MatchedRepoId = $match.Id
        MatchedRole   = $match.WorkspaceRole
        DotGald3rPath  = $relativeDotPath
    }
    Write-Result -Result $allow -AsJson:$Json
    exit 0
}

# Member or migration_source path matched. Apply marker policy.
$isMemberRole = ($match.WorkspaceRole -eq 'controlled_member' -or $match.WorkspaceRole -eq 'migration_source')

if (-not $isMemberRole) {
    $warn = [pscustomobject]@{
        Status        = 'warn'
        Reason        = "unknown_workspace_role:$($match.WorkspaceRole)"
        Message       = "Target matches manifest entry $($match.Id) with unrecognized workspace_role '$($match.WorkspaceRole)'. Treating as advisory; do not write to .gald3r/ here without explicit task authorization."
        TargetPath    = $normalTarget
        ManifestPath  = $manifestFile
        MatchedRepoId = $match.Id
        MatchedRole   = $match.WorkspaceRole
        DotGald3rPath  = $relativeDotPath
    }
    Write-Result -Result $warn -AsJson:$Json
    if ($WarnOnly) { exit 0 } else { exit 1 }
}

# Member or migration_source.
if ($relativeDotPath) {
    if (Test-IsMarkerSafePath -DotGald3rRelative $relativeDotPath) {
        $allow = [pscustomobject]@{
            Status          = 'allow'
            Reason          = 'marker_safe_path'
            Message         = "Path .gald3r/$relativeDotPath is in the marker allowlist for member repository $($match.Id)."
            TargetPath      = $normalTarget
            ManifestPath    = $manifestFile
            MatchedRepoId   = $match.Id
            MatchedRole     = $match.WorkspaceRole
            DotGald3rPath    = $relativeDotPath
            MarkerAllowlist = $MarkerAllowlist
        }
        Write-Result -Result $allow -AsJson:$Json
        exit 0
    }
    else {
        $block = [pscustomobject]@{
            Status          = 'block'
            Reason          = 'controlled_member_control_plane_path'
            Message         = "BLOCK: .gald3r/$relativeDotPath is forbidden in member repository $($match.Id) - it is live gald3r control-plane state. Marker allowlist: $($MarkerAllowlist -join ', '). Forbidden examples: $($ControlPlaneExamples -join ', ')."
            TargetPath      = $normalTarget
            ManifestPath    = $manifestFile
            MatchedRepoId   = $match.Id
            MatchedRole     = $match.WorkspaceRole
            DotGald3rPath    = $relativeDotPath
            MarkerAllowlist = $MarkerAllowlist
        }
        Write-Result -Result $block -AsJson:$Json
        if ($WarnOnly) { exit 0 } else { exit 1 }
    }
}

if ($AllowMarkerInit) {
    $allow = [pscustomobject]@{
        Status          = 'allow'
        Reason          = 'marker_init_authorized'
        Message         = "Marker-init mode authorized for member $($match.Id). Caller MUST write only marker-safe paths ($($MarkerAllowlist -join ', ')). Use bootstrap_member_gald3r_marker.ps1 for the actual filesystem write to enforce the allowlist."
        TargetPath      = $normalTarget
        ManifestPath    = $manifestFile
        MatchedRepoId   = $match.Id
        MatchedRole     = $match.WorkspaceRole
        MarkerAllowlist = $MarkerAllowlist
    }
    Write-Result -Result $allow -AsJson:$Json
    exit 0
}

# Default member match without -DotGald3rPath or -AllowMarkerInit: BLOCK.
$block = [pscustomobject]@{
    Status          = 'block'
    Reason          = 'controlled_member_repository'
    Message         = "BLOCK: Target ($($match.Id)) is a Workspace-Control $($match.WorkspaceRole). Specify -DotGald3rPath <path> to evaluate a specific .gald3r/ write, or -AllowMarkerInit when bootstrapping the marker pair ($($MarkerAllowlist -join ', ')). Live control-plane content is forbidden in member repositories; use the workspace control project for project task state."
    TargetPath      = $normalTarget
    ManifestPath    = $manifestFile
    MatchedRepoId   = $match.Id
    MatchedRole     = $match.WorkspaceRole
    MarkerAllowlist = $MarkerAllowlist
}
Write-Result -Result $block -AsJson:$Json
if ($WarnOnly) { exit 0 } else { exit 1 }
