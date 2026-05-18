# scripts/bootstrap_member_gald3r_marker.ps1
#
# Bootstrap the marker-only `.gald3r/` for a Workspace-Control member
# repository. Creates `.gald3r/.identity` (if absent) tying the member back
# to the workspace controller; creates a stub `.gald3r/PROJECT.md` (if
# absent) identifying the member.
#
# Used by:
#   * @g-wrkspc-spawn --apply (after git init + minimal .gitignore/README)
#   * @g-wrkspc-member-add --apply (when the path exists)
#   * @g-wrkspc-adopt --apply (after adoption preflight passes)
#
# This is the ONLY supported writer of member `.gald3r/` content. It refuses
# to write anything outside the marker allowlist (`.identity`, `PROJECT.md`).
#
# BUG-021 / Task 213 / g-rl-36.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$MemberPath,

    [Parameter(Mandatory = $true)]
    [string]$MemberId,

    [string]$ControllerPath = '',

    [string]$ManifestPath = '',

    [switch]$Apply,

    [switch]$Force,

    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$markerAllowlist = @('.identity', 'PROJECT.md')

function ConvertTo-NormalPath {
    param([string]$Path)
    if (-not $Path) { return '' }
    $resolved = $Path
    try { $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath } catch { $resolved = $Path }
    return ($resolved -replace '\\', '/').TrimEnd('/')
}

function Get-ControllerIdentity {
    param([string]$ControllerRoot)
    $idFile = Join-Path -Path $ControllerRoot -ChildPath '.gald3r/.identity'
    if (-not (Test-Path -LiteralPath $idFile)) {
        return @{}
    }
    $map = @{}
    foreach ($line in Get-Content -LiteralPath $idFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\s*$') {
            $map[$matches[1]] = $matches[2].Trim()
        }
    }
    return $map
}

function New-MarkerIdentityContent {
    param(
        [string]$MemberId,
        [string]$MemberAbsPath,
        [hashtable]$ControllerIdentity,
        [string]$ControllerAbsPath
    )
    $newProjectId = [guid]::NewGuid().ToString()
    $controllerProjectId = if ($ControllerIdentity.ContainsKey('project_id')) { $ControllerIdentity['project_id'] } else { '' }
    $controllerProjectName = if ($ControllerIdentity.ContainsKey('project_name')) { $ControllerIdentity['project_name'] } else { '' }
    $userId = if ($ControllerIdentity.ContainsKey('user_id')) { $ControllerIdentity['user_id'] } else { '' }
    $userName = if ($ControllerIdentity.ContainsKey('user_name')) { $ControllerIdentity['user_name'] } else { '' }
    $gald3rVersion = if ($ControllerIdentity.ContainsKey('gald3r_version')) { $ControllerIdentity['gald3r_version'] } else { '' }

    return @"
# Workspace-Control member identity (marker-only — BUG-021 / Task 213 / g-rl-36)
# This file ties the member repository back to the workspace controller.
# Live gald3r task/bug/plan/feature state lives in the controller, not here.

project_id=$newProjectId
project_name=$MemberId
project_path=$MemberAbsPath
user_id=$userId
user_name=$userName
gald3r_version=$gald3rVersion

# Workspace-Control wiring
workspace_role=controlled_member
workspace_controller_id=$controllerProjectName
workspace_controller_project_id=$controllerProjectId
workspace_controller_path=$ControllerAbsPath
member_gald3r_marker_only=true
"@
}

function New-MarkerProjectMdContent {
    param(
        [string]$MemberId,
        [string]$ControllerPath,
        [hashtable]$ControllerIdentity
    )
    $controllerName = if ($ControllerIdentity.ContainsKey('project_name')) { $ControllerIdentity['project_name'] } else { 'workspace controller' }
    $today = (Get-Date).ToString('yyyy-MM-dd')
    return @"
# $MemberId

> **Workspace-Control member repository** managed by $controllerName.
>
> This is a marker-only ``.gald3r/`` (BUG-021 / Task 213 / g-rl-36). Live
> gald3r task, bug, plan, feature, release, subsystem, and orchestration
> state for this project lives in the workspace controller at
> ``$ControllerPath``, not here.
>
> Allowed in this folder: ``.identity`` and ``PROJECT.md`` only.

## Mission

_Member-specific mission to be filled in. The structure of this file
follows the standard gald3r ``PROJECT.md`` shape and is parity-maintained
with the workspace controller's documentation conventions._

## Workspace-Control Membership

- **Role**: ``controlled_member``
- **Controller**: $controllerName
- **Member ID**: ``$MemberId``
- **Marker bootstrapped**: $today

## Source of Truth

- Live tasks, bugs, plans, releases: workspace controller (``$ControllerPath``)
- This member's source code, build configuration, runtime files: this repository
- Cross-project coordination (PCAC, INBOX, orders): workspace controller

## Why marker-only?

The Workspace-Control invariant (g-rl-36) requires that controlled member
repositories not contain live gald3r control-plane state. This prevents
member-vs-controller drift, accidental task/bug duplication, and broken
ownership boundaries. See ``BUG-021`` and ``Task 213`` for the full
rationale and the cleanup/remediation flow.
"@
}

function Write-Result {
    param([pscustomobject]$Result, [switch]$AsJson)
    if ($AsJson) {
        $Result | ConvertTo-Json -Depth 6
        return
    }
    $statusToken = $Result.Status.ToUpperInvariant()
    Write-Output "[$statusToken] member-marker bootstrap: $($Result.Reason)"
    if ($Result.Message) { Write-Output "  $($Result.Message)" }
    foreach ($action in @($Result.Actions)) {
        if ($action) { Write-Output "  - $action" }
    }
    if ($Result.MemberId) { Write-Output "  member_id      : $($Result.MemberId)" }
    if ($Result.MemberPath) { Write-Output "  member_path    : $($Result.MemberPath)" }
    if ($Result.ControllerPath) { Write-Output "  controller     : $($Result.ControllerPath)" }
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

$normalMember = ConvertTo-NormalPath -Path $MemberPath
if (-not $normalMember) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'invalid_member_path'
        Message    = 'MemberPath did not resolve to a valid path.'
        MemberPath = $MemberPath
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

if (-not (Test-Path -LiteralPath $MemberPath)) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'member_path_not_found'
        Message    = "Member path does not exist: $normalMember. Create the directory first (g-wrkspc-spawn handles this)."
        MemberPath = $normalMember
        MemberId   = $MemberId
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

# Resolve controller path: explicit --ControllerPath > walk upward to find manifest
$controllerRoot = $null
if ($ControllerPath) {
    if (-not (Test-Path -LiteralPath $ControllerPath)) {
        $err = [pscustomobject]@{
            Status         = 'error'
            Reason         = 'controller_path_not_found'
            Message        = "ControllerPath does not exist: $ControllerPath"
            MemberPath     = $normalMember
            MemberId       = $MemberId
            ControllerPath = $ControllerPath
        }
        Write-Result -Result $err -AsJson:$Json
        exit 2
    }
    $controllerRoot = (Resolve-Path -LiteralPath $ControllerPath).Path
}
else {
    # Find from manifest discovery
    $candidate = (Resolve-Path -LiteralPath $MemberPath).Path
    while ($candidate -and (Test-Path -LiteralPath $candidate)) {
        $manifest = Join-Path -Path $candidate -ChildPath '.gald3r/linking/workspace_manifest.yaml'
        if (Test-Path -LiteralPath $manifest) {
            $controllerRoot = $candidate
            break
        }
        $parent = Split-Path -Parent -Path $candidate
        if (-not $parent -or $parent -eq $candidate) { break }
        $candidate = $parent
    }
    if (-not $controllerRoot) {
        # fall back to current working directory walk-up
        $cwd = (Get-Location).Path
        while ($cwd) {
            $manifest = Join-Path -Path $cwd -ChildPath '.gald3r/linking/workspace_manifest.yaml'
            if (Test-Path -LiteralPath $manifest) {
                $controllerRoot = $cwd
                break
            }
            $parent = Split-Path -Parent -Path $cwd
            if (-not $parent -or $parent -eq $cwd) { break }
            $cwd = $parent
        }
    }
}

if (-not $controllerRoot) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'controller_not_found'
        Message    = 'Could not locate workspace controller (no .gald3r/linking/workspace_manifest.yaml in any ancestor of MemberPath or current directory). Pass -ControllerPath explicitly.'
        MemberPath = $normalMember
        MemberId   = $MemberId
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

# Run the guard helper to confirm member identity matches the manifest
$guardScript = Join-Path -Path $PSScriptRoot -ChildPath 'check_member_repo_gald3r_guard.ps1'
if (-not (Test-Path -LiteralPath $guardScript)) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'guard_helper_missing'
        Message    = "Companion guard helper not found at $guardScript"
        MemberPath = $normalMember
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

# Use -AllowMarkerInit to confirm membership without blocking
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
        Message    = "Could not parse guard output: $($_.Exception.Message). Raw: $guardOutput"
        MemberPath = $normalMember
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

if ($guardResult.Status -ne 'allow') {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = "guard_refused:$($guardResult.Reason)"
        Message    = "Guard refused marker-init for $MemberPath. $($guardResult.Message)"
        MemberPath = $normalMember
        MemberId   = $MemberId
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

if ($guardResult.MatchedRepoId -and $guardResult.MatchedRepoId -ne $MemberId -and -not $Force) {
    $err = [pscustomobject]@{
        Status     = 'error'
        Reason     = 'member_id_mismatch'
        Message    = "MemberId '$MemberId' does not match manifest entry '$($guardResult.MatchedRepoId)' for path $normalMember. Pass -Force to override (rare)."
        MemberPath = $normalMember
        MemberId   = $MemberId
    }
    Write-Result -Result $err -AsJson:$Json
    exit 2
}

# Determine actions
$actions = @()
$violations = @()
$dotGald3rPath = Join-Path -Path $MemberPath -ChildPath '.gald3r'
$identityPath = Join-Path -Path $dotGald3rPath -ChildPath '.identity'
$projectMdPath = Join-Path -Path $dotGald3rPath -ChildPath 'PROJECT.md'

# Scan existing .gald3r/ for forbidden content
if (Test-Path -LiteralPath $dotGald3rPath) {
    foreach ($entry in Get-ChildItem -LiteralPath $dotGald3rPath -Force -ErrorAction SilentlyContinue) {
        if ($entry.Name -in $markerAllowlist) { continue }
        $violations += $entry.Name
    }
    if ($violations.Count -gt 0) {
        $actions += "skip: existing .gald3r/ contains non-marker content: $($violations -join ', '). Run remediate_member_gald3r_marker.ps1 first."
    }
}
else {
    $actions += "create dir: $dotGald3rPath"
}

# .identity action
if (-not (Test-Path -LiteralPath $identityPath)) {
    $actions += "create: $identityPath (member identity tying back to controller)"
}
else {
    $actions += "preserve: $identityPath (already present)"
}

# PROJECT.md action
if (-not (Test-Path -LiteralPath $projectMdPath)) {
    $actions += "create: $projectMdPath (member-stub identifying member + cross-link to controller)"
}
else {
    $actions += "preserve: $projectMdPath (already present)"
}

if ($violations.Count -gt 0) {
    # Refuse to write into a member with existing forbidden content
    $blocker = [pscustomobject]@{
        Status         = 'block'
        Reason         = 'member_gald3r_has_control_plane'
        Message        = "Member .gald3r/ already contains non-marker content. Bootstrap refuses to proceed until remediation is run. Forbidden entries: $($violations -join ', '). Use scripts/remediate_member_gald3r_marker.ps1 -MemberPath '$MemberPath' --dry-run, then -Apply, before re-running bootstrap."
        Actions        = $actions
        MemberPath     = $normalMember
        MemberId       = $MemberId
        ControllerPath = $controllerRoot
    }
    Write-Result -Result $blocker -AsJson:$Json
    exit 1
}

if (-not $Apply) {
    $plan = [pscustomobject]@{
        Status         = 'plan'
        Reason         = 'dry_run'
        Message        = 'Dry-run: no files written. Pass -Apply to write the marker.'
        Actions        = $actions
        MemberPath     = $normalMember
        MemberId       = $MemberId
        ControllerPath = $controllerRoot
    }
    Write-Result -Result $plan -AsJson:$Json
    exit 0
}

# Apply mode
$controllerIdentity = Get-ControllerIdentity -ControllerRoot $controllerRoot

if (-not (Test-Path -LiteralPath $dotGald3rPath)) {
    New-Item -ItemType Directory -Path $dotGald3rPath -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $identityPath)) {
    $identityContent = New-MarkerIdentityContent `
        -MemberId $MemberId `
        -MemberAbsPath $normalMember `
        -ControllerIdentity $controllerIdentity `
        -ControllerAbsPath $controllerRoot
    Set-Content -LiteralPath $identityPath -Value $identityContent -Encoding UTF8 -NoNewline:$false
}

if (-not (Test-Path -LiteralPath $projectMdPath)) {
    $projectMdContent = New-MarkerProjectMdContent `
        -MemberId $MemberId `
        -ControllerPath $controllerRoot `
        -ControllerIdentity $controllerIdentity
    Set-Content -LiteralPath $projectMdPath -Value $projectMdContent -Encoding UTF8 -NoNewline:$false
}

$applied = [pscustomobject]@{
    Status         = 'applied'
    Reason         = 'marker_bootstrap_complete'
    Message        = "Marker .gald3r/ bootstrapped for member $MemberId. Live control-plane content remains forbidden here per g-rl-36."
    Actions        = $actions
    MemberPath     = $normalMember
    MemberId       = $MemberId
    ControllerPath = $controllerRoot
}
Write-Result -Result $applied -AsJson:$Json
exit 0
