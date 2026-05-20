<#
.SYNOPSIS
    Shared gald3r Git worktree helper for agent isolation.

.DESCRIPTION
    Provides the Task 170 worktree primitive used by later workflow tasks.
    The helper can create, detect/reuse, report, remove, and clean up gald3r-owned
    worktrees without nesting them inside the active repository checkout.

    Cancellation (T1123 — external-runner AbortSignal pattern):
      Run        - launch an agent subprocess inside an existing worktree and
                   record its PID on the ownership marker (non-blocking; -Wait to block).
      Cancel     - terminate the agent recorded on one worktree (graceful, then a
                   forced tree-kill after -GraceSeconds). The worktree is PRESERVED.
      CancelAll  - cancel every active agent owned by a given -TaskId. Used by the
                   g-go --swarm coordinator on timeout or conflict-gate abort.
      Cancellation events are appended to .gald3r/logs/worktree_cancellations.log.

    Default root:
      $env:GALD3R_WORKTREE_ROOT, when set
      otherwise: <repo-parent>/.gald3r-worktrees/<repo-name>

    Ownership proof:
      .gald3r-worktree.json inside each created worktree
#>

param(
    [ValidateSet("Create", "Report", "Remove", "Cleanup", "Run", "Cancel", "CancelAll")]
    [string]$Action = "Report",

    [string]$RepoPath = ".",
    [string]$TaskId,
    [string]$Role = "agent",
    [string]$Owner = $env:USERNAME,
    [string]$BaseBranch = "HEAD",
    [string]$WorktreeRoot = $env:GALD3R_WORKTREE_ROOT,
    [string]$TaskRoot,
    [int]$StaleHours = 24,
    [switch]$AllowDirty,
    [switch]$Apply,
    [switch]$Json,

    # --- Run: launch an agent subprocess inside an existing worktree (T1123) ---
    # The agent process id is recorded in the worktree's .gald3r-worktree.json so
    # Cancel / CancelAll can terminate it later. Run is non-blocking by default
    # (records the PID and returns); pass -Wait to block until the agent exits.
    [string]$AgentCommand,
    [string[]]$AgentArguments = @(),
    [switch]$Wait,

    # --- Cancel / CancelAll: graceful-then-forced termination (T1123) ---
    # Grace period before escalating from graceful stop to a forced tree-kill.
    [int]$GraceSeconds = 5,
    # Free-text reason recorded in the cancellation log.
    [string]$Reason = "coordinator-cancel"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Owner)) {
    if (-not [string]::IsNullOrWhiteSpace($env:USER)) {
        $Owner = $env:USER
    } else {
        $Owner = "agent"
    }
}

function Invoke-Git {
    param(
        [string]$Repo,
        [string[]]$Arguments
    )

    # Git uses stderr as a normal progress channel ("Preparing worktree",
    # "Updating files: N%"). Under $ErrorActionPreference = "Stop" with the
    # 2>&1 merged stream, PowerShell 7+ wraps each stderr line in an
    # ErrorRecord and terminates the pipeline before $LASTEXITCODE is
    # checked. Switch to Continue around the call so progress lines do not
    # abort us; rely on $LASTEXITCODE for true failure detection.
    $savedPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $merged = & git -C $Repo @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedPref
    }

    # Convert any ErrorRecord items (stderr captured on PS 7+) to plain
    # strings so downstream consumers and any throw get readable text.
    $output = foreach ($item in $merged) {
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            $item.Exception.Message
        } else {
            $item
        }
    }

    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed in ${Repo}: $($output -join [Environment]::NewLine)"
    }
    return $output
}

function ConvertTo-SafeSegment {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "unknown"
    }

    $safe = $Value.ToLowerInvariant() -replace "[^a-z0-9._-]+", "-"
    $safe = $safe -replace "\.{2,}", "."
    $safe = $safe.Trim("-").Trim(".")
    if ([string]::IsNullOrWhiteSpace($safe)) {
        return "unknown"
    }
    if ($safe.EndsWith(".lock")) {
        $safe = "$($safe.Substring(0, $safe.Length - 5))-lock"
    }
    if ($safe -match "^(con|prn|aux|nul|com[1-9]|lpt[1-9])$") {
        $safe = "x-$safe"
    }
    if ($safe.Length -gt 48) {
        $safe = $safe.Substring(0, 48).Trim("-").Trim(".")
    }
    return $safe
}

function Resolve-RepoRoot {
    param([string]$Path)

    $resolved = (Resolve-Path $Path).Path
    $root = (Invoke-Git -Repo $resolved -Arguments @("rev-parse", "--show-toplevel")).Trim()
    return (Resolve-Path $root).Path
}

function Test-PathInside {
    param(
        [string]$ChildPath,
        [string]$ParentPath
    )

    $child = [System.IO.Path]::GetFullPath($ChildPath).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $parent = [System.IO.Path]::GetFullPath($ParentPath).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    return $child.StartsWith($parent + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase) -or
        $child.Equals($parent, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-DefaultWorktreeRoot {
    param([string]$RepoRoot)

    $repoItem = Get-Item $RepoRoot
    $parent = $repoItem.Parent.FullName
    return Join-Path (Join-Path $parent ".gald3r-worktrees") $repoItem.Name
}

function Get-WorktreeRoot {
    param(
        [string]$RepoRoot,
        [string]$RequestedRoot
    )

    if ([string]::IsNullOrWhiteSpace($RequestedRoot)) {
        $root = Get-DefaultWorktreeRoot -RepoRoot $RepoRoot
    } else {
        $root = [System.IO.Path]::GetFullPath($RequestedRoot)
    }

    if (Test-PathInside -ChildPath $root -ParentPath $RepoRoot) {
        throw "Worktree root '$root' is inside active repo '$RepoRoot'. Set GALD3R_WORKTREE_ROOT to a sibling or external path."
    }

    return $root
}

function Get-RepoSlug {
    param([string]$RepoRoot)

    return ConvertTo-SafeSegment -Value (Split-Path $RepoRoot -Leaf)
}

function Get-ShortSuffix {
    $guid = [guid]::NewGuid().ToString("N")
    return $guid.Substring(0, 8)
}

function New-BranchName {
    param(
        [string]$TaskId,
        [string]$Role,
        [string]$Owner,
        [string]$RepoSlug,
        [string]$Suffix
    )

    $task = ConvertTo-SafeSegment -Value $TaskId
    $roleSlug = ConvertTo-SafeSegment -Value $Role
    $ownerSlug = ConvertTo-SafeSegment -Value $Owner
    return "gald3r/$task/$roleSlug/$repoSlug/$ownerSlug-$Suffix"
}

function Test-GitBranchName {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )

    & git -C $RepoRoot check-ref-format --branch $BranchName *> $null
    return $LASTEXITCODE -eq 0
}

function New-WorktreeDirectoryName {
    param(
        [string]$TaskId,
        [string]$Role,
        [string]$Owner,
        [string]$RepoSlug,
        [string]$Suffix
    )

    $task = ConvertTo-SafeSegment -Value $TaskId
    $roleSlug = ConvertTo-SafeSegment -Value $Role
    $ownerSlug = ConvertTo-SafeSegment -Value $Owner
    return "$task-$roleSlug-$repoSlug-$ownerSlug-$Suffix"
}

function Get-Gald3rWorktreeMarkers {
    param([string]$Root)

    if (-not (Test-Path $Root)) {
        return @()
    }

    return Get-ChildItem -Path $Root -Filter ".gald3r-worktree.json" -Recurse -File -ErrorAction SilentlyContinue
}

function Get-GitWorktreePaths {
    param([string]$RepoRoot)

    $paths = @()
    $lines = Invoke-Git -Repo $RepoRoot -Arguments @("worktree", "list", "--porcelain")
    foreach ($line in $lines) {
        if ($line -like "worktree *") {
            $paths += [System.IO.Path]::GetFullPath($line.Substring("worktree ".Length))
        }
    }
    return $paths
}

function Test-RegisteredWorktree {
    param(
        [string]$RepoRoot,
        [string]$WorktreePath
    )

    $target = [System.IO.Path]::GetFullPath($WorktreePath)
    foreach ($path in Get-GitWorktreePaths -RepoRoot $RepoRoot) {
        if ($path.Equals($target, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Read-Gald3rWorktreeMetadata {
    param([string]$MarkerPath)

    try {
        return Get-Content -Path $MarkerPath -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Find-Gald3rWorktree {
    param(
        [string]$Root,
        [string]$RepoRoot,
        [string]$TaskId,
        [string]$Role,
        [string]$Owner
    )

    foreach ($marker in Get-Gald3rWorktreeMarkers -Root $Root) {
        $metadata = Read-Gald3rWorktreeMetadata -MarkerPath $marker.FullName
        if ($null -eq $metadata) {
            continue
        }
        if ($metadata.gald3r_owned -and
            $metadata.repo_root -eq $RepoRoot -and
            $metadata.task_id -eq $TaskId -and
            $metadata.role -eq $Role -and
            $metadata.owner -eq $Owner) {
            return $metadata
        }
    }
    return $null
}

function Get-DirtyStatus {
    param([string]$RepoRoot)

    return @(Invoke-Git -Repo $RepoRoot -Arguments @("status", "--short"))
}

function Write-Metadata {
    param(
        [string]$MarkerPath,
        [object]$Metadata
    )

    $Metadata | ConvertTo-Json -Depth 4 | Set-Content -Path $MarkerPath -Encoding UTF8
}

function Test-BranchExists {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )

    & git -C $RepoRoot show-ref --verify --quiet "refs/heads/$BranchName"
    return $LASTEXITCODE -eq 0
}

function Get-TaskFileForWorktree {
    param(
        [string]$RepoRoot,
        [string]$TaskRoot,
        [string]$TaskId
    )

    if ([string]::IsNullOrWhiteSpace($TaskRoot)) {
        $TaskRoot = Join-Path (Join-Path $RepoRoot ".gald3r") "tasks"
    }
    if (-not (Test-Path $TaskRoot)) {
        return $null
    }
    $pattern = "task$($TaskId)_*.md"
    $match = Get-ChildItem -Path $TaskRoot -Filter $pattern -File -ErrorAction SilentlyContinue | Select-Object -First 1
    return $match
}

function Test-TaskClaimExpired {
    param([System.IO.FileInfo]$TaskFile)

    if ($null -eq $TaskFile -or -not (Test-Path $TaskFile.FullName)) {
        return $true
    }

    $text = Get-Content -Path $TaskFile.FullName -Raw
    $match = [regex]::Match($text, 'claim_expires_at:\s*"?([^"\r\n]+)"?')
    if (-not $match.Success) {
        return $false
    }

    $expiresAt = [datetime]::MinValue
    if ([datetime]::TryParse($match.Groups[1].Value, [ref]$expiresAt)) {
        return $expiresAt.ToUniversalTime() -lt (Get-Date).ToUniversalTime()
    }
    return $false
}

function Test-ValidExistingWorktree {
    param(
        [string]$RepoRoot,
        [object]$Metadata
    )

    if ($null -eq $Metadata -or -not $Metadata.gald3r_owned) {
        return $false
    }
    if (-not (Test-Path $Metadata.worktree_path)) {
        return $false
    }
    if (-not (Test-Path (Join-Path $Metadata.worktree_path ".gald3r-worktree.json"))) {
        return $false
    }
    if (-not (Test-RegisteredWorktree -RepoRoot $RepoRoot -WorktreePath $Metadata.worktree_path)) {
        return $false
    }
    $branch = (Invoke-Git -Repo $Metadata.worktree_path -Arguments @("branch", "--show-current")).Trim()
    return $branch -eq $Metadata.worktree_branch
}

function New-Gald3rWorktree {
    param(
        [string]$RepoRoot,
        [string]$Root,
        [string]$TaskId,
        [string]$Role,
        [string]$Owner,
        [string]$BaseBranch,
        [switch]$AllowDirty
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw "-TaskId is required for Create."
    }

    $existing = Find-Gald3rWorktree -Root $Root -RepoRoot $RepoRoot -TaskId $TaskId -Role $Role -Owner $Owner
    if (Test-ValidExistingWorktree -RepoRoot $RepoRoot -Metadata $existing) {
        return $existing
    }

    $dirty = Get-DirtyStatus -RepoRoot $RepoRoot
    if ($dirty.Count -gt 0 -and -not $AllowDirty) {
        throw "Active checkout is dirty. Commit/stash changes, or rerun with -AllowDirty after recording explicit ownership. Dirty entries: $($dirty -join '; ')"
    }

    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    $repoSlug = Get-RepoSlug -RepoRoot $RepoRoot
    $suffix = Get-ShortSuffix
    $branch = New-BranchName -TaskId $TaskId -Role $Role -Owner $Owner -RepoSlug $repoSlug -Suffix $suffix
    if (-not (Test-GitBranchName -RepoRoot $RepoRoot -BranchName $branch)) {
        throw "Generated branch name '$branch' is not a valid Git branch."
    }
    $directory = New-WorktreeDirectoryName -TaskId $TaskId -Role $Role -Owner $Owner -RepoSlug $repoSlug -Suffix $suffix
    $worktreePath = Join-Path $Root $directory

    Invoke-Git -Repo $RepoRoot -Arguments @("worktree", "add", "-b", $branch, $worktreePath, $BaseBranch) | Out-Null

    $metadata = [ordered]@{
        schema_version = "1.0"
        gald3r_owned = $true
        task_id = $TaskId
        role = $Role
        owner = $Owner
        repo_root = $RepoRoot
        repo_slug = $repoSlug
        worktree_path = $worktreePath
        worktree_branch = $branch
        base_branch = $BaseBranch
        created_at = (Get-Date).ToUniversalTime().ToString("o")
    }
    Write-Metadata -MarkerPath (Join-Path $worktreePath ".gald3r-worktree.json") -Metadata $metadata
    return [pscustomobject]$metadata
}

function Get-Gald3rWorktreeReport {
    param(
        [string]$Root,
        [string]$RepoRoot
    )

    $items = @()
    foreach ($marker in Get-Gald3rWorktreeMarkers -Root $Root) {
        $metadata = Read-Gald3rWorktreeMetadata -MarkerPath $marker.FullName
        if ($null -eq $metadata) {
            continue
        }
        if ($metadata.repo_root -ne $RepoRoot) {
            continue
        }
        $items += $metadata
    }
    return $items
}

function Remove-Gald3rWorktree {
    param(
        [string]$RepoRoot,
        [object]$Metadata,
        [switch]$Apply
    )

    if ($null -eq $Metadata -or -not $Metadata.gald3r_owned) {
        throw "Refusing to remove worktree without gald3r ownership metadata."
    }

    if (-not (Test-Path (Join-Path $Metadata.worktree_path ".gald3r-worktree.json"))) {
        throw "Refusing to remove '$($Metadata.worktree_path)' because the ownership marker is missing."
    }

    if (-not $Apply) {
        return [pscustomobject]@{
            action = "would_remove"
            worktree_path = $Metadata.worktree_path
            worktree_branch = $Metadata.worktree_branch
        }
    }

    if (-not (Test-RegisteredWorktree -RepoRoot $RepoRoot -WorktreePath $Metadata.worktree_path)) {
        throw "Refusing to remove '$($Metadata.worktree_path)' because it is not registered in git worktree list."
    }

    Invoke-Git -Repo $RepoRoot -Arguments @("worktree", "remove", "--force", $Metadata.worktree_path) | Out-Null
    if (Test-BranchExists -RepoRoot $RepoRoot -BranchName $Metadata.worktree_branch) {
        Invoke-Git -Repo $RepoRoot -Arguments @("branch", "-D", $Metadata.worktree_branch) | Out-Null
    }
    return [pscustomobject]@{
        action = "removed"
        worktree_path = $Metadata.worktree_path
        worktree_branch = $Metadata.worktree_branch
    }
}

function Invoke-Gald3rWorktreeCleanup {
    param(
        [string]$RepoRoot,
        [string]$Root,
        [string]$TaskRoot,
        [int]$StaleHours,
        [switch]$Apply
    )

    $cutoff = (Get-Date).ToUniversalTime().AddHours(-1 * $StaleHours)
    $results = @()
    foreach ($metadata in Get-Gald3rWorktreeReport -Root $Root -RepoRoot $RepoRoot) {
        $created = [datetime]$metadata.created_at
        $taskFile = Get-TaskFileForWorktree -RepoRoot $RepoRoot -TaskRoot $TaskRoot -TaskId $metadata.task_id
        $missingTask = $null -eq $taskFile
        $expiredClaim = Test-TaskClaimExpired -TaskFile $taskFile
        $missingBranch = -not (Test-BranchExists -RepoRoot $RepoRoot -BranchName $metadata.worktree_branch)
        $missingPath = -not (Test-Path $metadata.worktree_path)
        $oldByAge = $created.ToUniversalTime() -le $cutoff
        $claimProtectsWorktree = ($null -ne $taskFile) -and (-not $expiredClaim)
        if ($missingPath -or $missingTask -or $expiredClaim -or $missingBranch -or ($oldByAge -and -not $claimProtectsWorktree)) {
            $results += Remove-Gald3rWorktree -RepoRoot $RepoRoot -Metadata $metadata -Apply:$Apply
        }
    }
    return $results
}

# ---------------------------------------------------------------------------
# Cancellation signal threading (T1123 — external-runner AbortSignal pattern)
# ---------------------------------------------------------------------------

function Test-IsWindows {
    # $IsWindows is $true/$false on PS 7+, and $null on Windows PowerShell 5.1
    # (which only runs on Windows). Treat $null as Windows.
    return ($IsWindows -or ($null -eq $IsWindows))
}

function Write-CancellationLog {
    param(
        [string]$RepoRoot,
        [string]$TaskId,
        [string]$WorktreePath,
        [string]$Reason
    )

    $logDir = Join-Path (Join-Path $RepoRoot ".gald3r") "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    $logPath = Join-Path $logDir "worktree_cancellations.log"
    $stamp = (Get-Date).ToUniversalTime().ToString("o")
    $line = "$stamp | $TaskId | $WorktreePath | $Reason"
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

function Stop-AgentProcess {
    # Graceful termination first, then a forced tree-kill after the grace period.
    # Returns: already-exited | terminated-graceful | killed-forced
    param(
        [int]$ProcessId,
        [int]$GraceSeconds
    )

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        return "already-exited"
    }

    # Graceful request.
    if (Test-IsWindows) {
        try { [void]$proc.CloseMainWindow() } catch { }
    } else {
        & kill -TERM $ProcessId 2>$null
    }

    $deadline = (Get-Date).AddSeconds([Math]::Max(0, $GraceSeconds))
    while ((Get-Date) -lt $deadline) {
        if ($null -eq (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {
            return "terminated-graceful"
        }
        Start-Sleep -Milliseconds 200
    }

    # Force-kill the whole process tree (the agent may have spawned children).
    if (Test-IsWindows) {
        & taskkill /PID $ProcessId /T /F 2>$null | Out-Null
    } else {
        & kill -KILL $ProcessId 2>$null
    }
    Start-Sleep -Milliseconds 200
    if ($null -eq (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {
        return "killed-forced"
    }
    return "kill-failed"
}

function Start-AgentInWorktree {
    # Launch an agent subprocess inside an existing gald3r-owned worktree and
    # record its PID in the ownership marker so it can be cancelled later.
    param(
        [string]$RepoRoot,
        [object]$Metadata,
        [string]$AgentCommand,
        [string[]]$AgentArguments,
        [switch]$Wait
    )

    if ([string]::IsNullOrWhiteSpace($AgentCommand)) {
        throw "-AgentCommand is required for Run."
    }
    if ($null -eq $Metadata -or -not $Metadata.gald3r_owned) {
        throw "Run requires an existing gald3r-owned worktree (create it first with -Action Create)."
    }
    $markerPath = Join-Path $Metadata.worktree_path ".gald3r-worktree.json"
    if (-not (Test-Path $markerPath)) {
        throw "Ownership marker missing at '$markerPath' — refusing to Run."
    }

    $startArgs = @{
        FilePath         = $AgentCommand
        WorkingDirectory = $Metadata.worktree_path
        PassThru         = $true
    }
    if ($null -ne $AgentArguments -and $AgentArguments.Count -gt 0) {
        $startArgs.ArgumentList = $AgentArguments
    }
    $proc = Start-Process @startArgs

    # Persist the PID onto the marker (additive — preserve existing fields).
    $obj = [ordered]@{}
    foreach ($p in $Metadata.PSObject.Properties) { $obj[$p.Name] = $p.Value }
    $obj["agent_pid"] = $proc.Id
    $obj["agent_command"] = (@($AgentCommand) + $AgentArguments) -join " "
    $obj["agent_started_at"] = (Get-Date).ToUniversalTime().ToString("o")
    $obj["agent_status"] = "running"
    Write-Metadata -MarkerPath $markerPath -Metadata $obj

    if ($Wait) {
        $proc.WaitForExit()
        $obj["agent_status"] = "exited"
        $obj["agent_exit_code"] = $proc.ExitCode
        Write-Metadata -MarkerPath $markerPath -Metadata $obj
    }

    return [pscustomobject]@{
        action          = if ($Wait) { "ran" } else { "started" }
        task_id         = $Metadata.task_id
        worktree_path   = $Metadata.worktree_path
        agent_pid       = $proc.Id
        agent_command   = $obj["agent_command"]
        agent_status    = $obj["agent_status"]
        agent_exit_code = if ($Wait) { $proc.ExitCode } else { $null }
    }
}

function Stop-WorktreeAgentByMetadata {
    # Cancel the agent recorded on a single worktree marker. Preserves the
    # worktree (never calls Remove) so dirty state is kept for forensics.
    param(
        [string]$RepoRoot,
        [object]$Metadata,
        [int]$GraceSeconds,
        [string]$Reason
    )

    $markerPath = Join-Path $Metadata.worktree_path ".gald3r-worktree.json"
    $hasPid = ($null -ne $Metadata.PSObject.Properties['agent_pid']) -and ($null -ne $Metadata.agent_pid)
    if (-not $hasPid) {
        return [pscustomobject]@{
            action        = "no-agent"
            task_id       = $Metadata.task_id
            worktree_path = $Metadata.worktree_path
            outcome       = "no-pid-recorded"
        }
    }

    $outcome = Stop-AgentProcess -ProcessId ([int]$Metadata.agent_pid) -GraceSeconds $GraceSeconds
    Write-CancellationLog -RepoRoot $RepoRoot -TaskId $Metadata.task_id -WorktreePath $Metadata.worktree_path -Reason "$Reason ($outcome)"

    # Update the marker: clear the live PID, record the cancellation. Worktree
    # files are intentionally preserved.
    if (Test-Path $markerPath) {
        $obj = [ordered]@{}
        foreach ($p in $Metadata.PSObject.Properties) { $obj[$p.Name] = $p.Value }
        $obj["agent_status"] = "cancelled"
        $obj["agent_cancelled_at"] = (Get-Date).ToUniversalTime().ToString("o")
        $obj["agent_cancel_reason"] = $Reason
        $obj["agent_cancel_outcome"] = $outcome
        $obj["agent_pid"] = $null
        Write-Metadata -MarkerPath $markerPath -Metadata $obj
    }

    return [pscustomobject]@{
        action        = "cancelled"
        task_id       = $Metadata.task_id
        worktree_path = $Metadata.worktree_path
        outcome       = $outcome
        reason        = $Reason
    }
}

function Invoke-CancelAllForTask {
    param(
        [string]$RepoRoot,
        [string]$Root,
        [string]$TaskId,
        [int]$GraceSeconds,
        [string]$Reason
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw "-TaskId is required for CancelAll."
    }
    $results = @()
    foreach ($metadata in Get-Gald3rWorktreeReport -Root $Root -RepoRoot $RepoRoot) {
        if ($metadata.task_id -ne $TaskId) {
            continue
        }
        $results += Stop-WorktreeAgentByMetadata -RepoRoot $RepoRoot -Metadata $metadata -GraceSeconds $GraceSeconds -Reason $Reason
    }
    if ($results.Count -eq 0) {
        return [pscustomobject]@{ action = "cancel-all"; task_id = $TaskId; outcome = "no-worktrees-found" }
    }
    return $results
}

$repoRoot = Resolve-RepoRoot -Path $RepoPath
$resolvedRoot = Get-WorktreeRoot -RepoRoot $repoRoot -RequestedRoot $WorktreeRoot

switch ($Action) {
    "Create" {
        $result = New-Gald3rWorktree -RepoRoot $repoRoot -Root $resolvedRoot -TaskId $TaskId -Role $Role -Owner $Owner -BaseBranch $BaseBranch -AllowDirty:$AllowDirty
    }
    "Report" {
        $result = Get-Gald3rWorktreeReport -Root $resolvedRoot -RepoRoot $repoRoot
    }
    "Remove" {
        if ([string]::IsNullOrWhiteSpace($TaskId)) {
            throw "-TaskId is required for Remove."
        }
        $metadata = Find-Gald3rWorktree -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner
        if ($null -eq $metadata) {
            throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner'."
        }
        $result = Remove-Gald3rWorktree -RepoRoot $repoRoot -Metadata $metadata -Apply:$Apply
    }
    "Cleanup" {
        $result = Invoke-Gald3rWorktreeCleanup -RepoRoot $repoRoot -Root $resolvedRoot -TaskRoot $TaskRoot -StaleHours $StaleHours -Apply:$Apply
    }
    "Run" {
        if ([string]::IsNullOrWhiteSpace($TaskId)) {
            throw "-TaskId is required for Run."
        }
        $metadata = Find-Gald3rWorktree -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner
        if ($null -eq $metadata) {
            throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner'. Create it first."
        }
        $result = Start-AgentInWorktree -RepoRoot $repoRoot -Metadata $metadata -AgentCommand $AgentCommand -AgentArguments $AgentArguments -Wait:$Wait
    }
    "Cancel" {
        if ([string]::IsNullOrWhiteSpace($TaskId)) {
            throw "-TaskId is required for Cancel."
        }
        $metadata = Find-Gald3rWorktree -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner
        if ($null -eq $metadata) {
            throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner'."
        }
        $result = Stop-WorktreeAgentByMetadata -RepoRoot $repoRoot -Metadata $metadata -GraceSeconds $GraceSeconds -Reason $Reason
    }
    "CancelAll" {
        $result = Invoke-CancelAllForTask -RepoRoot $repoRoot -Root $resolvedRoot -TaskId $TaskId -GraceSeconds $GraceSeconds -Reason $Reason
    }
}

if ($Json) {
    if ($null -eq $result -or @($result).Count -eq 0) {
        "[]"
    } else {
        $result | ConvertTo-Json -Depth 5
    }
} else {
    $result | Format-List
}
