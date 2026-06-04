# .gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_housekeeping_commit.ps1
#
# Safe controller .gald3r/ housekeeping safety classifier (T531).
#
# Used by /g-go, /g-go-code, /g-go-review, /g-go-swarm, /g-go-code-swarm, and
# /g-go-review-swarm at two points:
#
#   1. Preflight (immediately after PCAC inbox check, before Clean Controller Gate
#      hard-blocking, claims, worktrees, or swarm partitioning).
#   2. Post-coordinator-write (immediately after coordinator-owned shared `.gald3r`
#      writes such as task/bug status updates, review-result writes, sent_orders
#      ledger updates, safe report/log outputs, etc., before the next major phase).
#
# When the orchestration root has dirty paths and ALL of them are safe controller
# `.gald3r/` housekeeping/coordination files, the helper can stage exactly those
# paths and create a focused commit -- no `git add .`, no source/docs/config drift.
# Any unsafe or mixed-dirty state preserves the existing hard-gate behavior.
#
# Exit codes:
#   0 - clean OR safe-and-committed (caller may continue)
#   1 - dirty, but contains unsafe/non-allowlisted paths (caller MUST stop and
#       surface the listed blockers; user action required)
#   2 - configuration fault (not a git repo, member-repo target, conflict, etc.)
#
# Examples:
#   .\scripts\gald3r_housekeeping_commit.ps1                          # classify only
#   .\scripts\gald3r_housekeeping_commit.ps1 -Apply                   # commit if safe
#   .\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply
#   .\scripts\gald3r_housekeeping_commit.ps1 -Mode post-write -Apply -TaskId 531
#   .\scripts\gald3r_housekeeping_commit.ps1 -Json                    # structured output

[CmdletBinding()]
param(
    [string]$OrchestrationRoot = '',

    [ValidateSet('preflight', 'post-write')]
    [string]$Mode = 'preflight',

    [Alias('Task', 'Bug')]
    [string]$TaskId = '',

    [string]$BugId = '',

    [string]$Message = '',

    [switch]$Apply,

    [switch]$Json,

    [switch]$NoColor
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$script:UseColor = -not $NoColor

# Allowlisted controller .gald3r/ path globs. Matched against repo-relative paths
# (forward-slash-normalized). Order does not matter.
$script:AllowGlobs = @(
    '.gald3r/TASKS.md'
    '.gald3r/BUGS.md'
    '.gald3r/FEATURES.md'
    '.gald3r/PRDS.md'
    '.gald3r/SUBSYSTEMS.md'
    '.gald3r/IDEA_BOARD.md'
    '.gald3r/learned-facts.md'
    '.gald3r/tracking/IDEA_BOARD.md'
    '.gald3r/tasks/*.md'
    '.gald3r/tasks/**/*.md'
    '.gald3r/tasks/open/*.md'
    '.gald3r/tasks/in-progress/*.md'
    '.gald3r/tasks/awaiting/*.md'
    '.gald3r/tasks/closed/*.md'
    '.gald3r/bugs/*.md'
    '.gald3r/bugs/**/*.md'
    '.gald3r/bugs/open/*.md'
    '.gald3r/bugs/closed/*.md'
    '.gald3r/features/*.md'
    '.gald3r/prds/*.md'
    '.gald3r/subsystems/*.md'
    '.gald3r/reports/*.md'
    '.gald3r/reports/*.json'
    '.gald3r/logs/pcac_auto_actions.log'
    '.gald3r/linking/sent_orders/*.md'
    '.gald3r/linking/INBOX.md'
)

# Always-unsafe globs (override allowlist; surfaced as blockers).
$script:DenyGlobs = @(
    '.gald3r/.identity'
    '.gald3r/.user_id'
    '.gald3r/.project_id'
    '.gald3r/.vault_location'
    '.gald3r/vault/*'
    '.gald3r/vault/**/*'
    '.gald3r/config/*'
    '.gald3r/config/**/*'
    '.gald3r/.gald3r-worktree.json'
)

# Secret-name regex (filename match, case-insensitive).
$script:SecretNameRx = '(?i)(secret|credential|token|password|api[._-]?key|private[._-]?key)'

function Write-StatusLine {
    param(
        [ValidateSet('GREEN', 'YELLOW', 'RED', 'INFO')]
        [string]$Level,
        [string]$Message
    )
    if (-not $script:UseColor) {
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

function Find-DefaultOrchestrationRoot {
    $here = $PSScriptRoot
    if (-not $here) { $here = Split-Path -Parent $MyInvocation.MyCommand.Path }
    $candidate = Resolve-Path -LiteralPath (Join-Path $here '..')
    $gitOut = & git -C $candidate.Path rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($gitOut | Select-Object -Last 1).Trim()
}

function Test-MemberRepoMarker {
    # Returns $true if the candidate root LOOKS like a Workspace-Control member repo
    # (marker-only .gald3r/: has .identity but no manifest AND no live control plane).
    # A normal gald3r controller has TASKS.md or a manifest; a member has neither.
    param([string]$Root)
    $identity = Join-Path $Root '.gald3r/.identity'
    $manifest = Join-Path $Root '.gald3r/linking/workspace_manifest.yaml'
    $tasksMd  = Join-Path $Root '.gald3r/TASKS.md'
    if (-not (Test-Path -LiteralPath $identity)) { return $false }
    if (Test-Path -LiteralPath $manifest)        { return $false }
    if (Test-Path -LiteralPath $tasksMd)         { return $false }
    return $true
}

function Test-PathAgainstGlobs {
    param([string]$Path, [string[]]$Globs)
    foreach ($g in $Globs) {
        # PowerShell's -like supports * and ?; convert ** to * for our purposes.
        $g2 = $g -replace '\*\*', '*'
        if ($Path -like $g2) { return $true }
    }
    return $false
}

function Get-PorcelainEntries {
    param([string]$Root)
    # -uall expands untracked directories into individual file entries so per-path
    # safety classification works (otherwise an untracked .gald3r/ would collapse to "?? .gald3r/").
    $raw = & git -C $Root status --porcelain=v1 -uall 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    $lines = @()
    foreach ($l in @($raw)) {
        if ($null -eq $l) { continue }
        $s = [string]$l
        if ($s.Length -lt 4) { continue }
        $xy = $s.Substring(0, 2)
        $rest = $s.Substring(3)
        # Renames look like "R  old -> new"; consider the destination path.
        $path = $rest
        $orig = ''
        if ($rest -match '^(.+)\s->\s(.+)$') {
            $orig = $Matches[1].Trim('"')
            $path = $Matches[2]
        }
        $path = $path.Trim('"').Replace('\', '/')
        $lines += [pscustomobject]@{
            XY       = $xy
            Path     = $path
            Original = $orig
            Raw      = $s
        }
    }
    return , $lines
}

function Test-PathSafety {
    param([string]$Path, [string]$XY)
    # Conflict markers: U?, ?U, AA, DD, etc. all imply unresolved merge state.
    if ($XY -match 'U' -or $XY -eq 'AA' -or $XY -eq 'DD') {
        return @{ Safe = $false; Reason = 'unresolved-conflict' }
    }
    # Must live inside .gald3r/.
    if ($Path -notmatch '^\.gald3r/') {
        return @{ Safe = $false; Reason = 'not-in-gald3r' }
    }
    # Member-repo .gald3r/ control plane is forbidden as a write target — but the
    # repo-level Test-MemberRepoMarker check elsewhere catches this; here we only
    # block live-control-plane paths if seen in such a repo.
    # Filename secret heuristic.
    $leaf = Split-Path -Leaf $Path
    if ($leaf -match $script:SecretNameRx) {
        return @{ Safe = $false; Reason = 'secret-name-pattern' }
    }
    # Deny list wins.
    if (Test-PathAgainstGlobs -Path $Path -Globs $script:DenyGlobs) {
        return @{ Safe = $false; Reason = 'sensitive-gald3r-path' }
    }
    # Allow list.
    if (Test-PathAgainstGlobs -Path $Path -Globs $script:AllowGlobs) {
        return @{ Safe = $true; Reason = 'allowlisted' }
    }
    return @{ Safe = $false; Reason = 'unknown-gald3r-path' }
}

function Format-CommitMessage {
    param(
        [string]$Mode,
        [string]$TaskId,
        [string]$BugId,
        [string]$Override,
        [int]$FileCount
    )
    if ($Override) { return $Override }
    $title = if ($Mode -eq 'preflight') {
        'chore(gald3r): preflight gald3r housekeeping'
    } else {
        'chore(gald3r): commit g-go coordination state'
    }
    $body = if ($Mode -eq 'preflight') {
        "Commit controller .gald3r housekeeping before g-go clean gate execution.`n`nFiles: $FileCount"
    } else {
        "Commit controller .gald3r coordination updates after g-go shared-state writes.`n`nFiles: $FileCount"
    }
    $refs = @()
    if ($TaskId) { $refs += "Task: #$TaskId" }
    if ($BugId)  { $refs += "Bug: $BugId" }
    if ($refs.Count -gt 0) { $body += "`n" + ($refs -join "`n") }
    return "$title`n`n$body"
}

# --- main ---
$orch = $OrchestrationRoot
if (-not $orch) { $orch = Find-DefaultOrchestrationRoot }
if (-not $orch) {
    if ($Json) {
        @{ status = 'config-fault'; reason = 'no-orchestration-root' } | ConvertTo-Json -Compress
    } else {
        Write-StatusLine RED 'Could not resolve orchestration git root.'
    }
    exit 2
}
$orch = (Resolve-Path -LiteralPath $orch).Path

# Refuse to operate on member-repo targets (T213/g-rl-36 boundary).
if (Test-MemberRepoMarker -Root $orch) {
    if ($Json) {
        @{ status = 'config-fault'; reason = 'member-repo-target'; root = $orch } | ConvertTo-Json -Compress
    } else {
        Write-StatusLine RED "Refusing to run: $orch looks like a Workspace-Control member repo (marker-only .gald3r/)."
    }
    exit 2
}

$entries = Get-PorcelainEntries -Root $orch
if ($null -eq $entries) {
    if ($Json) {
        @{ status = 'config-fault'; reason = 'git-status-failed'; root = $orch } | ConvertTo-Json -Compress
    } else {
        Write-StatusLine RED 'git status --porcelain failed.'
    }
    exit 2
}

if ($entries.Count -eq 0) {
    $payload = @{
        status   = 'clean'
        mode     = $Mode
        root     = $orch
        files    = @()
        unsafe   = @()
    }
    if ($Json) { $payload | ConvertTo-Json -Depth 4 -Compress } else { Write-StatusLine GREEN "Clean working tree at $orch" }
    exit 0
}

$safe   = @()
$unsafe = @()
foreach ($e in $entries) {
    $r = Test-PathSafety -Path $e.Path -XY $e.XY
    if ($r.Safe) {
        $safe += [pscustomobject]@{ Path = $e.Path; XY = $e.XY; Reason = $r.Reason }
    } else {
        $unsafe += [pscustomobject]@{ Path = $e.Path; XY = $e.XY; Reason = $r.Reason }
    }
}

# Drift check: any unsafe -> mixed-dirty / unsafe-gald3r / conflict / unknown.
if ($unsafe.Count -gt 0) {
    $hasConflict = @($unsafe | Where-Object { $_.Reason -eq 'unresolved-conflict' }).Count -gt 0
    $hasNonGald3r = @($unsafe | Where-Object { $_.Reason -eq 'not-in-gald3r' }).Count -gt 0
    $status = if ($hasConflict) { 'conflict' }
              elseif ($hasNonGald3r -and $safe.Count -gt 0) { 'mixed-dirty' }
              elseif ($hasNonGald3r) { 'mixed-dirty' }
              else { 'unsafe-gald3r' }

    $payload = @{
        status = $status
        mode   = $Mode
        root   = $orch
        files  = @($safe | ForEach-Object { @{ path = $_.Path; xy = $_.XY; reason = $_.Reason } })
        unsafe = @($unsafe | ForEach-Object { @{ path = $_.Path; xy = $_.XY; reason = $_.Reason } })
    }
    if ($Json) {
        $payload | ConvertTo-Json -Depth 4 -Compress
    } else {
        Write-StatusLine RED "Blocker: $status ($($unsafe.Count) unsafe path(s); $($safe.Count) safe path(s))"
        foreach ($u in $unsafe) { Write-Output ('  ' + $u.XY + ' ' + $u.Path + '  -- ' + $u.Reason) }
        if ($safe.Count -gt 0) {
            Write-Output ''
            Write-Output 'Safe paths (would have been committed if dirt set were uniform):'
            foreach ($s in $safe) { Write-Output ('  ' + $s.XY + ' ' + $s.Path) }
        }
        Write-Output ''
        Write-Output 'Resolve unsafe paths first (commit/stash/move them), then re-run.'
    }
    exit 1
}

# Pure safe set. Determine sub-classification for the structured payload.
$cls = if ($Mode -eq 'preflight') { 'safe-gald3r-housekeeping' } else { 'safe-gald3r-coordination' }

if (-not $Apply) {
    $payload = @{
        status = $cls
        mode   = $Mode
        root   = $orch
        files  = @($safe | ForEach-Object { @{ path = $_.Path; xy = $_.XY; reason = $_.Reason } })
        unsafe = @()
    }
    if ($Json) {
        $payload | ConvertTo-Json -Depth 4 -Compress
    } else {
        Write-StatusLine YELLOW "$cls -- $($safe.Count) safe path(s); pass -Apply to commit."
        foreach ($s in $safe) { Write-Output ('  ' + $s.XY + ' ' + $s.Path) }
    }
    exit 0
}

# Apply: stage explicit paths, re-check drift, commit, post-check drift.
$paths = @($safe | ForEach-Object { $_.Path } | Select-Object -Unique)
$gitArgs = @('-C', $orch, 'add', '--')
$gitArgs += $paths
& git @gitArgs | Out-Null
if ($LASTEXITCODE -ne 0) {
    if ($Json) {
        @{ status = 'config-fault'; reason = 'git-add-failed'; root = $orch } | ConvertTo-Json -Compress
    } else {
        Write-StatusLine RED 'git add failed.'
    }
    exit 2
}

# Drift re-check: anything unstaged outside our path set => fail closed.
$post = Get-PorcelainEntries -Root $orch
$drift = @()
foreach ($e in $post) {
    # If the post-status XY shows working-tree changes (second char != ' '), and
    # the path is not in our safe set, this is drift.
    $wtDirty = ($e.XY[1] -ne ' ')
    if ($wtDirty -and ($paths -notcontains $e.Path)) {
        $drift += $e
    }
}
if ($drift.Count -gt 0) {
    & git -C $orch reset HEAD -- @paths | Out-Null
    if ($Json) {
        @{ status = 'drift-detected'; mode = $Mode; root = $orch
          files = @(); unsafe = @($drift | ForEach-Object { @{ path = $_.Path; xy = $_.XY; reason = 'concurrent-write' } }) } |
            ConvertTo-Json -Depth 4 -Compress
    } else {
        Write-StatusLine RED 'Drift detected after staging: another writer touched the tree concurrently. Staging reverted.'
        foreach ($d in $drift) { Write-Output ('  ' + $d.XY + ' ' + $d.Path) }
    }
    exit 1
}

$msg = Format-CommitMessage -Mode $Mode -TaskId $TaskId -BugId $BugId -Override $Message -FileCount $paths.Count

# Use a temp file to avoid PowerShell heredoc / quoting hazards on Windows.
$tmp = [System.IO.Path]::GetTempFileName()
try {
    Set-Content -LiteralPath $tmp -Value $msg -Encoding UTF8
    & git -C $orch commit -F $tmp | Out-Null
    if ($LASTEXITCODE -ne 0) {
        if ($Json) {
            @{ status = 'config-fault'; reason = 'git-commit-failed'; root = $orch } | ConvertTo-Json -Compress
        } else {
            Write-StatusLine RED 'git commit failed.'
        }
        exit 2
    }
} finally {
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}

$sha = (& git -C $orch rev-parse HEAD).Trim()
$payload = @{
    status      = "committed-$cls"
    mode        = $Mode
    root        = $orch
    commit_sha  = $sha
    file_count  = $paths.Count
    files       = @($paths | ForEach-Object { @{ path = $_; xy = ''; reason = 'allowlisted' } })
    unsafe      = @()
}
if ($Json) {
    $payload | ConvertTo-Json -Depth 4 -Compress
} else {
    Write-StatusLine GREEN "Committed $($paths.Count) safe path(s) as $sha ($cls). Run continues."
    foreach ($p in $paths) { Write-Output ('  -- ' + $p) }
}
exit 0
