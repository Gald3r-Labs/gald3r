# .gald3r_sys/skills/g-skl-workspace/scripts/gald3r_promote_member.ps1
#
# Promote a Workspace-Control `controlled_member` repository to a fully
# self-managed `autonomous_child` (BUG-097 / T1435 / g-rl-36).
#
# A controlled_member is intentionally restricted to a marker-only `.gald3r/`
# (`.identity` + `PROJECT.md`). When a member needs to become independent, the
# g-rl-36 guard must be lifted AND the standard framework files that postdate
# the original member creation (RELEASES.md, releases/, vocab.md,
# workspace/topology.md, workspace/inbox.md, FEATURES.md, BUGS.md, PLAN.md)
# must be scaffolded. This helper performs that migration safely.
#
# Default mode is dry-run: reports the plan (files that would be created,
# .identity changes, manifest role change) without touching the filesystem.
# With -Apply it backfills missing standard files, rewrites `.identity`
# (workspace_role=autonomous_child, member_gald3r_marker_only removed,
# gald3r_version bumped to current), and updates the workspace manifest
# workspace_role for the member.
#
# Standard gald3r files (PROJECT.md, CONSTRAINTS.md, SUBSYSTEMS.md, IDEA_BOARD.md,
# tasks/, bugs/, etc.) created by g-skl-setup are NOT all re-created here; this
# helper backfills the minimum autonomous_child set enumerated in BUG-097 plus
# the files most commonly missing on legacy members. Run @g-skl-setup
# --upgrade-existing afterward (now unblocked by the guard) for a full top-up.
#
# Exit codes:
#   0 - dry-run plan produced, apply succeeded, or member already autonomous (info)
#   1 - block (guard refused, member has unexpected state, manifest unwritable)
#   2 - input or manifest error

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$MemberPath,

    [string]$MemberId = '',

    [string]$ControllerPath = '',

    [string]$ManifestPath = '',

    [string]$Gald3rVersion = '',

    [switch]$Apply,

    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# Files / dirs that a fully-equipped autonomous_child should have but a
# marker-only member lacks. Enumerated from BUG-097 + g-rl-25 slim layout.
$StandardFiles = @('RELEASES.md', 'vocab.md', 'FEATURES.md', 'BUGS.md', 'PLAN.md')
$StandardDirs = @('releases', 'workspace')
$WorkspaceFiles = @('topology.md', 'inbox.md')

function ConvertTo-NormalPath {
    param([string]$Path)
    if (-not $Path) { return '' }
    $resolved = $Path
    try { $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath } catch { $resolved = $Path }
    return ($resolved -replace '\\', '/').TrimEnd('/')
}

function Read-IdentityMap {
    param([string]$IdentityFile)
    $map = [ordered]@{}
    if (-not (Test-Path -LiteralPath $IdentityFile)) { return $map }
    foreach ($line in Get-Content -LiteralPath $IdentityFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            $map[$matches[1]] = $matches[2].Trim()
        }
    }
    return $map
}

function Get-CurrentFrameworkVersion {
    param([string]$ControllerRoot, [string]$Override)
    if ($Override) { return $Override }
    # Prefer the controller-installed system VERSION file.
    $candidates = @(
        (Join-Path -Path $ControllerRoot -ChildPath '.gald3r_sys/VERSION'),
        (Join-Path -Path $PSScriptRoot -ChildPath '../../../VERSION')
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            $v = (Get-Content -LiteralPath $c -Raw -ErrorAction SilentlyContinue).Trim()
            if ($v) { return $v }
        }
    }
    return ''
}

function Write-Result {
    param([pscustomobject]$Result, [switch]$AsJson)
    if ($AsJson) {
        $Result | ConvertTo-Json -Depth 6
        return
    }
    $statusToken = $Result.Status.ToUpperInvariant()
    Write-Output "[$statusToken] member promote: $($Result.Reason)"
    if ($Result.Message) { Write-Output "  $($Result.Message)" }
    if ($Result.MemberId) { Write-Output "  member_id        : $($Result.MemberId)" }
    if ($Result.MemberPath) { Write-Output "  member_path      : $($Result.MemberPath)" }
    if ($Result.ControllerPath) { Write-Output "  controller       : $($Result.ControllerPath)" }
    if ($Result.FromRole) { Write-Output "  from_role        : $($Result.FromRole)" }
    if ($Result.ToRole) { Write-Output "  to_role          : $($Result.ToRole)" }
    if ($Result.Gald3rVersion) { Write-Output "  gald3r_version   : $($Result.Gald3rVersion)" }
    if ($Result.ManifestUpdated) { Write-Output "  manifest_updated : $($Result.ManifestUpdated)" }
    if ($Result.Actions -and @($Result.Actions).Count -gt 0) {
        Write-Output "  actions:"
        foreach ($a in @($Result.Actions)) { if ($a) { Write-Output "    - $a" } }
    }
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

if (-not (Test-Path -LiteralPath $MemberPath)) {
    Write-Result -Result ([pscustomobject]@{
            Status     = 'error'
            Reason     = 'member_path_not_found'
            Message    = "Member path does not exist: $MemberPath"
            MemberPath = $MemberPath
        }) -AsJson:$Json
    exit 2
}

$normalMember = ConvertTo-NormalPath -Path $MemberPath

# Delegate membership classification to the shared guard helper.
$guardScript = Join-Path -Path $PSScriptRoot -ChildPath 'check_member_repo_gald3r_guard.ps1'
if (-not (Test-Path -LiteralPath $guardScript)) {
    Write-Result -Result ([pscustomobject]@{
            Status     = 'error'
            Reason     = 'guard_helper_missing'
            Message    = "Companion guard helper not found at $guardScript"
            MemberPath = $normalMember
        }) -AsJson:$Json
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
    Write-Result -Result ([pscustomobject]@{
            Status     = 'error'
            Reason     = 'guard_parse_failed'
            Message    = "Could not parse guard output: $($_.Exception.Message). Raw: $guardOutput"
            MemberPath = $normalMember
        }) -AsJson:$Json
    exit 2
}

# Read the member identity to learn its current role and controller wiring
# authoritatively (independent of guard manifest discovery).
$dotGald3r = Join-Path -Path $MemberPath -ChildPath '.gald3r'
$identityFile = Join-Path -Path $dotGald3r -ChildPath '.identity'
$identity = Read-IdentityMap -IdentityFile $identityFile
$identityRole = if ($identity.Contains('workspace_role')) { $identity['workspace_role'] } else { '' }

$matchedId = $guardResult.MatchedRepoId
$matchedRole = $guardResult.MatchedRole
if (-not $MemberId -and $matchedId) { $MemberId = $matchedId }
if (-not $MemberId -and $identity.Contains('project_name')) { $MemberId = $identity['project_name'] }

# Resolve the controller root: explicit flag > member identity wiring.
$controllerRoot = ''
if ($ControllerPath) {
    $controllerRoot = (Resolve-Path -LiteralPath $ControllerPath -ErrorAction SilentlyContinue).Path
}
elseif ($identity.Contains('workspace_controller_path') -and (Test-Path -LiteralPath $identity['workspace_controller_path'])) {
    $controllerRoot = (Resolve-Path -LiteralPath $identity['workspace_controller_path']).Path
}

# Resolve the manifest file to rewrite on apply. Priority:
#   explicit -ManifestPath > guard-discovered manifest > controller-derived path.
$manifestFile = ''
if ($ManifestPath -and (Test-Path -LiteralPath $ManifestPath)) {
    $manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
}
elseif ($guardResult.ManifestPath) {
    $manifestFile = $guardResult.ManifestPath
}
elseif ($controllerRoot) {
    $candidate = Join-Path -Path $controllerRoot -ChildPath '.gald3r/linking/workspace_manifest.yaml'
    if (Test-Path -LiteralPath $candidate) { $manifestFile = (Resolve-Path -LiteralPath $candidate).Path }
}

# If the role was unknown from the guard, derive it from the manifest entry.
if (-not $matchedRole -and $manifestFile -and $MemberId) {
    $mtext = Get-Content -LiteralPath $manifestFile -Raw -ErrorAction SilentlyContinue
    $mrx = [regex]::Match($mtext, '(?ms)^- id:\s*' + [regex]::Escape($MemberId) + '\s*\r?\n(?:^(?!- id:)[^\r\n]*\r?\n)*?^  workspace_role:\s*([A-Za-z_]+)')
    if ($mrx.Success) { $matchedRole = $mrx.Groups[1].Value }
}

$effectiveRole = if ($matchedRole) { $matchedRole } elseif ($identityRole) { $identityRole } else { '' }

# Already autonomous? Informational no-op.
if ($effectiveRole -eq 'autonomous_child' -or $identityRole -eq 'autonomous_child') {
    Write-Result -Result ([pscustomobject]@{
            Status     = 'info'
            Reason     = 'already_autonomous_child'
            Message    = "Member $MemberId is already workspace_role=autonomous_child. Nothing to promote. Run @g-skl-setup --upgrade-existing if files are still missing."
            MemberId   = $MemberId
            MemberPath = $normalMember
            FromRole   = $effectiveRole
            ToRole     = 'autonomous_child'
        }) -AsJson:$Json
    exit 0
}

# Only controlled_member / migration_source are promotable.
if ($effectiveRole -ne 'controlled_member' -and $effectiveRole -ne 'migration_source') {
    Write-Result -Result ([pscustomobject]@{
            Status     = 'block'
            Reason     = 'not_a_promotable_member'
            Message    = "Target role '$effectiveRole' is not promotable. PROMOTE only migrates controlled_member or migration_source to autonomous_child. Guard reason: $($guardResult.Reason)."
            MemberId   = $MemberId
            MemberPath = $normalMember
            FromRole   = $effectiveRole
        }) -AsJson:$Json
    exit 1
}

# Backfill controller root from the manifest path when not yet resolved.
if (-not $controllerRoot -and $manifestFile) {
    # manifest lives at <controller>/.gald3r/linking/workspace_manifest.yaml
    $linking = Split-Path -Parent -Path $manifestFile
    $gald3rDir = Split-Path -Parent -Path $linking
    $controllerRoot = Split-Path -Parent -Path $gald3rDir
}

$targetVersion = Get-CurrentFrameworkVersion -ControllerRoot $controllerRoot -Override $Gald3rVersion

# Build the scaffold plan.
$actions = @()

if (-not (Test-Path -LiteralPath $dotGald3r)) {
    $actions += "create dir: .gald3r/"
}

foreach ($d in $StandardDirs) {
    $dirPath = Join-Path -Path $dotGald3r -ChildPath $d
    if (-not (Test-Path -LiteralPath $dirPath)) {
        $actions += "create dir: .gald3r/$d/"
    }
}

foreach ($f in $StandardFiles) {
    $filePath = Join-Path -Path $dotGald3r -ChildPath $f
    if (-not (Test-Path -LiteralPath $filePath)) {
        $actions += "create file: .gald3r/$f"
    }
    else {
        $actions += "preserve: .gald3r/$f (already present)"
    }
}

foreach ($wf in $WorkspaceFiles) {
    $wfPath = Join-Path -Path $dotGald3r -ChildPath "workspace/$wf"
    if (-not (Test-Path -LiteralPath $wfPath)) {
        $actions += "create file: .gald3r/workspace/$wf"
    }
    else {
        $actions += "preserve: .gald3r/workspace/$wf (already present)"
    }
}

$actions += "rewrite: .gald3r/.identity (workspace_role -> autonomous_child; remove member_gald3r_marker_only; gald3r_version -> $targetVersion)"
if ($manifestFile) {
    $actions += "update manifest: $manifestFile (repositories[$MemberId].workspace_role -> autonomous_child)"
}
else {
    $actions += "warn: no workspace manifest resolved; manifest workspace_role not updated"
}

if (-not $Apply) {
    Write-Result -Result ([pscustomobject]@{
            Status        = 'plan'
            Reason        = 'dry_run'
            Message       = "Dry-run: no files written. Pass -Apply to promote member $MemberId to autonomous_child."
            MemberId      = $MemberId
            MemberPath    = $normalMember
            ControllerPath = $controllerRoot
            FromRole      = $effectiveRole
            ToRole        = 'autonomous_child'
            Gald3rVersion = $targetVersion
            ManifestUpdated = $false
            Actions       = $actions
        }) -AsJson:$Json
    exit 0
}

# --------------------------------------------------------------------------
# Apply
# --------------------------------------------------------------------------

$today = (Get-Date).ToString('yyyy-MM-dd')
$applied = @()

if (-not (Test-Path -LiteralPath $dotGald3r)) {
    New-Item -ItemType Directory -Path $dotGald3r -Force | Out-Null
    $applied += "created dir: .gald3r/"
}

foreach ($d in $StandardDirs) {
    $dirPath = Join-Path -Path $dotGald3r -ChildPath $d
    if (-not (Test-Path -LiteralPath $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        $applied += "created dir: .gald3r/$d/"
    }
}

function Write-StubFile {
    param([string]$Path, [string]$Body)
    if (-not (Test-Path -LiteralPath $Path)) {
        Set-Content -LiteralPath $Path -Value $Body -Encoding UTF8
        return $true
    }
    return $false
}

$stubs = @{
    'RELEASES.md'  = "# Releases`n`n_Promoted to autonomous_child on $today. Release index managed by @g-release-* commands._`n`n## Release Index`n`n| Version | Date | Status | Tasks |`n|---------|------|--------|-------|`n"
    'vocab.md'     = "# Project Vocabulary`n`n_Promoted to autonomous_child on $today. Manage with @g-vocab-add / @g-vocab-list._`n`n## Active Vocabulary`n`n| Abbreviation | Expansion | Notes |`n|--------------|-----------|-------|`n"
    'FEATURES.md'  = "# Features`n`n_Promoted to autonomous_child on $today. Managed by @g-feat-* commands._`n`n## Feature Index`n`n| ID | Title | Status |`n|----|-------|--------|`n"
    'BUGS.md'      = "# Bugs`n`n_Promoted to autonomous_child on $today. Managed by @g-bug-* commands._`n`n## Bug Index`n`n| ID | Title | Severity | Status |`n|----|-------|----------|--------|`n"
    'PLAN.md'      = "# Plan`n`n_Promoted to autonomous_child on $today. Managed by @g-plan._`n`n## Strategy`n`n_Define the master strategy and milestones here._`n"
}

foreach ($name in $StandardFiles) {
    $filePath = Join-Path -Path $dotGald3r -ChildPath $name
    if (Write-StubFile -Path $filePath -Body $stubs[$name]) {
        $applied += "created: .gald3r/$name"
    }
    else {
        $applied += "preserved: .gald3r/$name"
    }
}

$workspaceStubs = @{
    'topology.md' = "# Workspace Topology`n`n> Created on promotion to autonomous_child ($today).`n>`n> Declare WPAC parent / children / siblings here. An autonomous_child is`n> self-managed and WPAC-linked to its controller.`n`n## Relationships`n`nparent: `n`nchildren: []`n`nsiblings: []`n"
    'inbox.md'    = "# Workspace Inbox`n`n> Created on promotion to autonomous_child ($today).`n>`n> Cross-project WPAC directives land here. Action with @g-wpac-read.`n`n## Open Items`n`n_None._`n"
}

foreach ($wf in $WorkspaceFiles) {
    $wfPath = Join-Path -Path $dotGald3r -ChildPath "workspace/$wf"
    if (Write-StubFile -Path $wfPath -Body $workspaceStubs[$wf]) {
        $applied += "created: .gald3r/workspace/$wf"
    }
    else {
        $applied += "preserved: .gald3r/workspace/$wf"
    }
}

# Rewrite .identity: set role, drop marker flag, bump version. Preserve order
# and any unknown keys.
$newLines = @()
$sawRole = $false
$sawVersion = $false
if (Test-Path -LiteralPath $identityFile) {
    foreach ($line in Get-Content -LiteralPath $identityFile) {
        if ($line -match '^\s*member_gald3r_marker_only\s*=') {
            # Drop the marker-only flag entirely.
            continue
        }
        elseif ($line -match '^(\s*)workspace_role\s*=') {
            $newLines += "workspace_role=autonomous_child"
            $sawRole = $true
        }
        elseif ($line -match '^(\s*)gald3r_version\s*=') {
            if ($targetVersion) { $newLines += "gald3r_version=$targetVersion"; $sawVersion = $true }
            else { $newLines += $line; $sawVersion = $true }
        }
        else {
            $newLines += $line
        }
    }
}
if (-not $sawRole) { $newLines += "workspace_role=autonomous_child" }
if (-not $sawVersion -and $targetVersion) { $newLines += "gald3r_version=$targetVersion" }
Set-Content -LiteralPath $identityFile -Value ($newLines -join "`n") -Encoding UTF8
$applied += "rewrote: .gald3r/.identity (workspace_role=autonomous_child, marker flag removed, gald3r_version=$targetVersion)"

# Update the workspace manifest workspace_role for this member.
$manifestUpdated = $false
if ($manifestFile -and (Test-Path -LiteralPath $manifestFile)) {
    $content = Get-Content -LiteralPath $manifestFile -Raw
    # Match the member's repository entry block and rewrite its workspace_role.
    # Entry headers are `- id: <MemberId>`; the body uses two-space indent.
    $pattern = '(?ms)(^- id:\s*' + [regex]::Escape($MemberId) + '\s*\r?\n(?:^(?!- id:)[^\r\n]*\r?\n)*?^  workspace_role:\s*)([A-Za-z_]+)'
    $rx = [regex]$pattern
    if ($rx.IsMatch($content)) {
        $content = $rx.Replace($content, { param($m) $m.Groups[1].Value + 'autonomous_child' }, 1)
        Set-Content -LiteralPath $manifestFile -Value $content -Encoding UTF8 -NoNewline
        $manifestUpdated = $true
        $applied += "updated manifest: repositories[$MemberId].workspace_role -> autonomous_child"
    }
    else {
        $applied += "warn: could not locate repositories[$MemberId].workspace_role in manifest; update it manually"
    }
}
else {
    $applied += "warn: no workspace manifest resolved; manifest workspace_role not updated"
}

Write-Result -Result ([pscustomobject]@{
        Status          = 'applied'
        Reason          = 'promotion_complete'
        Message         = "Member $MemberId promoted to autonomous_child. The g-rl-36 guard now allows @g-skl-setup. Run @g-skl-setup --upgrade-existing for a full file top-up, then @g-wrkspc-validate."
        MemberId        = $MemberId
        MemberPath      = $normalMember
        ControllerPath  = $controllerRoot
        FromRole        = $effectiveRole
        ToRole          = 'autonomous_child'
        Gald3rVersion   = $targetVersion
        ManifestUpdated = $manifestUpdated
        Actions         = $applied
    }) -AsJson:$Json
exit 0
