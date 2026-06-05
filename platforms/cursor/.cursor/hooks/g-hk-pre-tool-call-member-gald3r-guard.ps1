# g-hk-pre-tool-call-member-gald3r-guard.ps1
# @subsystems: WORKSPACE_COORDINATION
# Pre-tool-call guard: refuse Edit/Write to a Workspace-Control member
# repository's .gald3r/ that targets anything other than the marker pair
# (.identity / PROJECT.md).
#
# Enforces g-rl-36 "Workspace-Control Member `.gald3r/` Marker-Only Guard
# (HARD RULE)" and BUG-021 (T213).
#
# Member repos may keep ONLY .gald3r/.identity and .gald3r/PROJECT.md.
# Everything else (TASKS.md, tasks/, BUGS.md, bugs/, PLAN.md, ...) is forbidden.
#
# Hook contract: same as g-hk-pre-tool-call-gald3r-guard (Claude Code / Cursor
# PreToolUse spec). exit 2 = deny, exit 0 = allow.
#
# Bypass: $env:GALD3R_HOOK_BYPASS = '1'.
# Marker init: $env:GALD3R_MARKER_INIT_ACTIVE = '1' (set by
# bootstrap_member_gald3r_marker.ps1; allows writing the marker pair itself).
#
# Rule reference: .claude/rules/g-rl-36-workspace-member-gald3r-guard.md
# Guard helper: .cursor/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1

$ErrorActionPreference = "SilentlyContinue"

$raw = $input | Out-String
$tool = ""
$path = ""
try {
    $event = $raw | ConvertFrom-Json
    $tool  = "$($event.tool_name)"
    if ($event.tool_input) {
        foreach ($k in @("file_path", "path", "notebook_path", "target_file")) {
            if ($event.tool_input.PSObject.Properties[$k]) {
                $path = "$($event.tool_input.$k)"
                if ($path) { break }
            }
        }
    }
} catch {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

$writeTools = @("Edit", "Write", "MultiEdit", "NotebookEdit", "Patch", "ApplyPatch", "str_replace_editor")
if ($writeTools -notcontains $tool) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}
if (-not $path) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

$norm = ($path -replace '\\', '/')
if ($norm -notmatch '(^|/)\.gald3r/') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

if ($env:GALD3R_HOOK_BYPASS -eq '1') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Build an absolute path.
$full = $path
if (-not [System.IO.Path]::IsPathRooted($full)) {
    $full = Join-Path (Get-Location).Path $path
}
$fullNorm = ($full -replace '\\', '/')

# Discover the workspace manifest. Walk up from cwd; stop at filesystem root.
$cwd = (Get-Location).Path
$dir = $cwd
$manifest = $null
while ($dir -and (Test-Path -LiteralPath $dir)) {
    $candidate = Join-Path $dir ".gald3r/linking/workspace_manifest.yaml"
    if (Test-Path -LiteralPath $candidate) {
        $manifest = $candidate
        break
    }
    $parent = Split-Path -Path $dir -Parent
    if (-not $parent -or $parent -eq $dir) { break }
    $dir = $parent
}
if (-not $manifest) {
    # Not inside a workspace controller — allow (orchestration-only project).
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Read manifest, collect member local_paths whose workspace_role is
# controlled_member or migration_source (those are the marker-only members).
$mLines = Get-Content -LiteralPath $manifest -ErrorAction SilentlyContinue
if (-not $mLines) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

$members = New-Object System.Collections.ArrayList
$curPath = $null
$curRole = $null
foreach ($line in $mLines) {
    if ($line -match '^\s*-\s+id:\s+\S+') {
        # New repository entry — flush previous if it qualifies.
        if ($curPath -and ($curRole -eq 'controlled_member' -or $curRole -eq 'migration_source')) {
            [void]$members.Add(($curPath -replace '\\', '/').TrimEnd('/'))
        }
        $curPath = $null
        $curRole = $null
        continue
    }
    if ($line -match '^\s*local_path:\s*(.+)$') {
        $curPath = $matches[1].Trim().Trim('"').Trim("'")
    }
    elseif ($line -match '^\s*workspace_role:\s*(\S+)') {
        $curRole = $matches[1].Trim()
    }
}
# Flush the last entry.
if ($curPath -and ($curRole -eq 'controlled_member' -or $curRole -eq 'migration_source')) {
    [void]$members.Add(($curPath -replace '\\', '/').TrimEnd('/'))
}

# Does the target path live inside any marker-only member's .gald3r/?
$hit = $null
foreach ($mpath in $members) {
    $memberGald3r = "$mpath/.gald3r/"
    if ($fullNorm -like "${memberGald3r}*" -or $fullNorm -eq $memberGald3r.TrimEnd('/')) {
        $hit = $mpath
        break
    }
}
if (-not $hit) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Compute the suffix inside the member's .gald3r/.
$prefix = "$hit/.gald3r/"
$suffix = $fullNorm.Substring($prefix.Length)
$markerFiles = @('.identity', 'PROJECT.md')

if ($env:GALD3R_MARKER_INIT_ACTIVE -eq '1' -and $markerFiles -contains $suffix) {
    # Sanctioned marker bootstrap — allow.
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

if ($markerFiles -contains $suffix -and -not (Test-Path -LiteralPath $full)) {
    # Allow creation of marker pair without active flag too — bootstrap helper
    # will set the flag in normal flow, but allow the case where a marker is
    # being repaired by the controller.
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

if ($markerFiles -contains $suffix) {
    # Editing an existing marker file is allowed (parity sync uses this).
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Anything else inside a member's .gald3r/ is forbidden.
$msg = "Member .gald3r/ marker-only guard: refused Edit/Write to '$suffix' inside member repository '$hit'. " +
       "Workspace-Control member repositories may keep ONLY .gald3r/.identity and .gald3r/PROJECT.md. " +
       "Live control-plane state (TASKS.md, tasks/, BUGS.md, PLAN.md, ...) is forbidden in members. " +
       "Use the workspace controller (<gald3r_source>) for orchestration writes. " +
       "See .claude/rules/g-rl-36-workspace-member-gald3r-guard.md and BUG-021."
@{
    permission    = "deny"
    user_message  = $msg
    agent_message = $msg + " Target: $path (member=$hit, suffix=$suffix)"
} | ConvertTo-Json -Compress
exit 2
