# .claude/skills/g-skl-workspace/scripts/preflight_touch_set.ps1
#
# Human- and CI-friendly touch-set git preflight (T504 / g-rl-33).
# Resolves the orchestration repo + optional workspace manifest members and
# prints a short GREEN / YELLOW / RED checklist with copy-paste next commands.
#
# Exit codes:
#   0 - every resolved git root has a clean working tree (and no config faults)
#   1 - one or more roots are dirty (typical g-go coordinator gate failure)
#   2 - configuration fault (not a git repo, unknown manifest id, manifest missing when required)
#
# Examples:
#   .\scripts\preflight_touch_set.ps1
#   .\scripts\preflight_touch_set.ps1 -WorkspaceRepoId example_desktop,example_app
#   .\scripts\preflight_touch_set.ps1 -TaskFile .\.gald3r\tasks\task230_k8s_manifest_authoring_adopted_example_web.md

[CmdletBinding()]
param(
    [string]$OrchestrationRoot = '',

    [Alias('WorkspaceRepos')]
    [string[]]$WorkspaceRepoId = @(),

    [string[]]$ExtendedTouchRepoId = @(),

    [string[]]$TouchRepoId = @(),

    [string[]]$SubsystemName = @(),

    [string]$TaskFile = '',

    [string]$ManifestPath = '',

    [switch]$Json,

    [switch]$NoColor
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$script:PreflightUseColor = -not $NoColor
$PreflightExit = 0

function Write-StatusLine {
    param(
        [ValidateSet('GREEN', 'YELLOW', 'RED', 'INFO')]
        [string]$Level,
        [string]$Message
    )
    # Use Write-Output so CI / pipes / Out-String capture the checklist (Write-Host is host-only).
    if (-not $script:PreflightUseColor) {
        Write-Output "[$Level] $Message"
        return
    }
    $c = switch ($Level) {
        'GREEN' { 'Green' }
        'YELLOW' { 'Yellow' }
        'RED' { 'Red' }
        default { 'Cyan' }
    }
    Write-Host "[$Level] $Message" -ForegroundColor $c
}

function Find-GitRoot {
    param([string]$StartDir)
    $p = (Resolve-Path -LiteralPath $StartDir).Path
    $gitOut = & git -C $p rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($gitOut | Select-Object -Last 1).Trim()
}

function Find-DefaultOrchestrationRoot {
    $here = $PSScriptRoot
    if (-not $here) { $here = Split-Path -Parent $MyInvocation.MyCommand.Path }
    $candidate = Resolve-Path -LiteralPath (Join-Path $here '..')
    return (Find-GitRoot -StartDir $candidate.Path)
}

function Find-WorkspaceManifestPath {
    param([string]$StartPath)
    $c = $StartPath
    while ($c -and (Test-Path -LiteralPath $c)) {
        $m = Join-Path $c '.gald3r/linking/workspace_manifest.yaml'
        if (Test-Path -LiteralPath $m) { return (Resolve-Path -LiteralPath $m).Path }
        $parent = Split-Path -Parent $c
        if (-not $parent -or $parent -eq $c) { break }
        $c = $parent
    }
    return $null
}

function Read-ManifestRepositories {
    param([string]$ManifestFile)
    $all = Get-Content -LiteralPath $ManifestFile -Raw -ErrorAction Stop
    $m = [regex]::Match($all, '(?ms)^repositories:\s*\r?\n(?<body>.*?)(?=^controlled_members:\s*\r?\n)')
    if (-not $m.Success) { return @{} }
    $block = $m.Groups['body'].Value

    $map = @{}
    $curId = $null
    foreach ($line in ($block -split "`r?`n")) {
        if ($line -match '^-\s*id:\s*(.+)$') {
            $curId = $Matches[1].Trim()
            continue
        }
        if ($curId -and $line -match '^\s+local_path:\s*(.+)$') {
            $raw = $Matches[1].Trim().Trim("'").Trim('"')
            $map[$curId] = $raw
            $curId = $null
        }
    }
    return $map
}

function Get-TaskFrontmatter {
    param([string]$Path)
    $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
    if ($raw -notmatch '(?s)^---\s*\r?\n(.+?)\r?\n---') { return '' }
    return $Matches[1]
}

function Expand-YamlStringListKey {
    param([string]$Frontmatter, [string]$Key)
    $ids = [System.Collections.Generic.List[string]]::new()
    if ($Frontmatter -match "(?m)^${Key}:\s*\[(.*?)\]\s*$") {
        foreach ($p in ($Matches[1] -split ',')) {
            $t = $p.Trim().Trim("'").Trim('"')
            if ($t) { $ids.Add($t) }
        }
        return , $ids.ToArray()
    }
    $lines = $Frontmatter -split "`r?`n"
    $capture = $false
    foreach ($line in $lines) {
        if ($line -match "^${Key}:\s*$") {
            $capture = $true
            continue
        }
        if ($capture) {
            if ($line -match '^\s*-\s+(.+)$') {
                $ids.Add($Matches[1].Trim().Trim("'").Trim('"'))
                continue
            }
            if ($line -match '^\s*(#|$)') { continue }
            if ($line -match '^\s+$') { continue }
            if ($line -match '^[A-Za-z_][A-Za-z0-9_]*:') { break }
        }
    }
    return , $ids.ToArray()
}

function Get-AbsolutePathsFromSubsystemSpec {
    param([string]$SpecPath, [string]$OrchestrationRoot)
    $paths = [System.Collections.Generic.List[string]]::new()
    if (-not (Test-Path -LiteralPath $SpecPath)) { return , $paths.ToArray() }
    $raw = Get-Content -LiteralPath $SpecPath -Raw
    if ($raw -notmatch '(?s)^---\s*\r?\n(.+?)\r?\n---') { return , $paths.ToArray() }
    $fm = $Matches[1]
    $winAbs = [regex]::Matches($fm, '["'']([A-Za-z]:[/\\][^"''\r\n]+)["'']')
    foreach ($m in $winAbs) { $paths.Add($m.Groups[1].Value) }
    $posix = [regex]::Matches($fm, '(?m)(?:^\s*-\s+|:\s+)["'']?(/[^"''\s\]\r\n]+)["'']?')
    foreach ($m in $posix) {
        $v = $m.Groups[1].Value
        if ($v -match '^/') { $paths.Add($v) }
    }
    return , $paths.ToArray()
}

function Resolve-ToGitRoot {
    param([string]$PathLike)
    if (-not $PathLike) { return $null }
    $expanded = [Environment]::ExpandEnvironmentVariables($PathLike)
    if (-not (Test-Path -LiteralPath $expanded)) { return $null }
    $item = Get-Item -LiteralPath $expanded
    $dir = if ($item.PSIsContainer) { $item.FullName } else { Split-Path -Parent $item.FullName }
    return (Find-GitRoot -StartDir $dir)
}

# --- main ---
$orch = $OrchestrationRoot
if (-not $orch) { $orch = Find-DefaultOrchestrationRoot }
if (-not $orch) {
    Write-StatusLine RED "Could not resolve orchestration git root. Run from inside <gald3r_source> or pass -OrchestrationRoot."
    Write-Output ''
    Write-Output 'Next:'
    Write-Output '  cd <path-to-your-controller-repo>'
    Write-Output '  git rev-parse --show-toplevel'
    exit 2
}
$orch = (Resolve-Path -LiteralPath $orch).Path

$manifest = $ManifestPath
if (-not $manifest) { $manifest = Find-WorkspaceManifestPath -StartPath $orch }
elseif (-not [System.IO.Path]::IsPathRooted($manifest)) {
    $manifest = Join-Path $orch $manifest.TrimStart('/\')
}
if ($manifest) { $manifest = (Resolve-Path -LiteralPath $manifest).Path }

$subsystemNamesFromTask = [System.Collections.Generic.List[string]]::new()
$repoIds = [System.Collections.Generic.List[string]]::new()
foreach ($x in @($WorkspaceRepoId)) { if ($x) { $repoIds.Add($x.Trim()) } }
foreach ($x in @($ExtendedTouchRepoId)) { if ($x) { $repoIds.Add($x.Trim()) } }
foreach ($x in @($TouchRepoId)) { if ($x) { $repoIds.Add($x.Trim()) } }

if ($TaskFile) {
    $tf = $TaskFile
    if (-not [System.IO.Path]::IsPathRooted($tf)) { $tf = Join-Path (Get-Location) $tf }
    if (-not (Test-Path -LiteralPath $tf)) {
        Write-StatusLine RED "TaskFile not found: $tf"
        exit 2
    }
    $fm = Get-TaskFrontmatter -Path $tf
    foreach ($k in @('workspace_repos', 'extended_touch_repos', 'touch_repos')) {
        foreach ($id in (Expand-YamlStringListKey -Frontmatter $fm -Key $k)) {
            $repoIds.Add($id)
        }
    }
    foreach ($sn in (Expand-YamlStringListKey -Frontmatter $fm -Key 'subsystems')) {
        if ($sn) { [void]$subsystemNamesFromTask.Add($sn) }
    }
}

$subsystemScanList = @(@($SubsystemName) + @($subsystemNamesFromTask.ToArray()) | Where-Object { $_ } | Select-Object -Unique)

$repoIds = @($repoIds | Where-Object { $_ } | Select-Object -Unique)

$manifestMap = @{}
if ($manifest) {
    try { $manifestMap = Read-ManifestRepositories -ManifestFile $manifest }
    catch {
        Write-StatusLine RED "Failed to read manifest: $manifest"
        exit 2
    }
}
elseif (@($repoIds).Count -gt 0) {
    Write-StatusLine RED "workspace_manifest.yaml not found under $orch but repository IDs were supplied. Fix path or create manifest."
    Write-Output ''
    Write-Output 'Next:'
    Write-Output '  .\scripts\validate_workspace_members_gald3r.ps1'
    exit 2
}

$gitRoots = [ordered]@{}
$gitRoots[$orch] = 'orchestration'

foreach ($id in $repoIds) {
    if (-not $manifestMap.ContainsKey($id)) {
        Write-StatusLine RED "Unknown repository.id in manifest: $id"
        Write-Output ''
        Write-Output 'Next:'
        Write-Output '  Open .gald3r/linking/workspace_manifest.yaml and confirm repositories[].id, or fix task frontmatter workspace_repos.'
        exit 2
    }
    $lp = $manifestMap[$id]
    if (-not (Test-Path -LiteralPath $lp)) {
        Write-StatusLine YELLOW "Skip $id - local_path not on disk: $lp (planned / not cloned yet)"
        continue
    }
    $g = Resolve-ToGitRoot -PathLike $lp
    if (-not $g) {
        Write-StatusLine RED "Member $id path exists but is not inside a git repo: $lp"
        exit 2
    }
    if (-not $gitRoots.Contains($g)) { $gitRoots[$g] = $id }
}

foreach ($sn in $subsystemScanList) {
    $spec = Join-Path $orch ".gald3r/subsystems/$sn.md"
    foreach ($abs in (Get-AbsolutePathsFromSubsystemSpec -SpecPath $spec -OrchestrationRoot $orch)) {
        $g = Resolve-ToGitRoot -PathLike $abs
        if ($g -and $g -ne $orch -and -not $gitRoots.Contains($g)) {
            $gitRoots[$g] = "subsystem:$sn"
        }
    }
}

$results = @()
foreach ($kv in $gitRoots.GetEnumerator()) {
    $root = $kv.Key
    $label = $kv.Value
    $short = @( & git -C $root status --short 2>$null )
    if ($LASTEXITCODE -ne 0) {
        $results += [pscustomobject]@{ Root = $root; Label = $label; State = 'RED'; Detail = 'git status failed'; Lines = @() }
        $PreflightExit = 2
        continue
    }
    $lines = @($short | Where-Object { $_ })
    if ($lines.Count -eq 0) {
        $results += [pscustomobject]@{ Root = $root; Label = $label; State = 'GREEN'; Detail = 'clean'; Lines = @() }
    }
    else {
        $lineArr = @($lines)
        $results += [pscustomobject]@{ Root = $root; Label = $label; State = 'RED'; Detail = "$($lineArr.Count) path(s) dirty"; Lines = $lineArr }
        if ($PreflightExit -lt 1) { $PreflightExit = 1 }
    }
}

if ($Json) {
    $results | ConvertTo-Json -Depth 5
    exit $PreflightExit
}

Write-Output ''
Write-Output "=== preflight_touch_set ===  orchestration: $orch"
if ($manifest) { Write-Output "                      manifest: $manifest" }
Write-Output ''

foreach ($r in $results) {
    Write-StatusLine $r.State "$($r.Label)  $($r.Root)"
    $lineList = @($r.Lines)
    if ($r.State -eq 'RED' -and $lineList.Count -gt 0) {
        $lineList | Select-Object -First 8 | ForEach-Object { Write-Output "      $_" }
        if ($lineList.Count -gt 8) {
            $moreN = $lineList.Count - 8
            Write-Output ('      ... ' + $moreN + ' more lines')
        }
    }
}

Write-Output ''
Write-Output '--- Next commands ---'
if ($PreflightExit -eq 0) {
    Write-StatusLine GREEN "All listed git roots are clean. Safe to proceed with coordinator writes / checkpoint commit (subject to your staging allowlist)."
    Write-Output ''
    Write-Output "  git -C `"$orch`" status"
}
else {
    foreach ($r in ($results | Where-Object { $_.State -eq 'RED' })) {
        $qRoot = $r.Root.Replace("'", "''")
        Write-Output ''
        Write-Output "  # $($r.Label) ($($r.Root))"
        Write-Output "  git -C `"$($r.Root)`" status"
        Write-Output ('  git -C "' + $r.Root + '" add -- YOUR_PATHS    # then')
        Write-Output ('  git -C "' + $r.Root + '" commit -m "fix: ..."')
        Write-Output '  # or stash unrelated WIP:'
        Write-Output "  git -C `"$($r.Root)`" stash push -u -m `"wip: preflight_touch_set`""
    }
    Write-Output ''
    $rerunLine = '.\scripts\preflight_touch_set.ps1'
    if (@($repoIds).Count -gt 0) {
        $rerunLine += ' -WorkspaceRepoId ' + ($repoIds -join ',')
    }
    Write-StatusLine INFO "Re-run:  $rerunLine"
}

Write-Output ''
exit $PreflightExit
