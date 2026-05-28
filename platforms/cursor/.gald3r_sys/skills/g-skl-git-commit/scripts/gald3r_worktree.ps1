<#
.SYNOPSIS
    Shared gald3r Git worktree helper for agent isolation.

.DESCRIPTION
    Provides the Task 170 worktree primitive used by later workflow tasks.
    The helper can create, detect/reuse, report, remove, and clean up gald3r-owned
    worktrees without nesting them inside the active repository checkout.

    Cancellation (T1123 — sandcastle AbortSignal pattern):
      Run        - launch an agent subprocess inside an existing worktree and
                   record its PID on the ownership marker (non-blocking; -Wait to block).
      Cancel     - terminate the agent recorded on one worktree (graceful, then a
                   forced tree-kill after -GraceSeconds). The worktree is PRESERVED.
      CancelAll  - cancel every active agent owned by a given -TaskId. Used by the
                   g-go --swarm coordinator on timeout or conflict-gate abort.
      Cancellation events are appended to .gald3r/logs/worktree_cancellations.log.

    Session resume (T967 — continuity artifact + checkpoint):
      Checkpoint - after each implementation checkpoint, write a continuity_artifact.md
                   into the worktree (atomically: temp file + Move-Item -Force) and update
                   the ownership marker's last_checkpoint_sha + continuity_artifact_path.
                   The artifact is a structured summary (goal, completed/pending ACs, last
                   tool summary, next action, blockers) — written BEFORE the checkpoint
                   commit so it survives a crash / OOM / power loss mid-commit.
      Resume     - locate the worktree for a -TaskId, read continuity_artifact.md, print the
                   "Resuming from checkpoint {sha} — {N} ACs complete, {M} remaining" line,
                   and emit the artifact body as a context prefix for g-go-code --resume.

    Mid-flight course correction (T969 — /steer + /queue):
      Steer      - write (or read+clear) steer.md at the worktree root. -SteerText writes a
                   steering prompt for the running g-go-code session to pick up at the next
                   AC-gate iteration; with no -SteerText the action READS steer.md, returns its
                   body, and DELETES the file (one-shot inject). Used by @g-steer and by the
                   g-go-code AC-gate poll.
      Queue      - append a follow-up prompt to queue.md at the worktree root (-QueueText), or
                   read the pending queue with no -QueueText. queue.md items are processed after
                   the main goal is complete. Used by @g-queue and by the g-go-code drain step.

    Default root:
      $env:GALD3R_WORKTREE_ROOT, when set
      otherwise: <repo-parent>/.gald3r-worktrees/<repo-name>

    Ownership proof:
      .gald3r-worktree.json inside each created worktree
#>

param(
    [ValidateSet("Create", "Report", "Remove", "Cleanup", "Run", "Cancel", "CancelAll", "Checkpoint", "Resume", "Steer", "Queue", "LockReport", "Keep", "MergeToMain")]
    [string]$Action = "Report",

    [string]$RepoPath = ".",
    [string]$TaskId,
    [string]$Role = "agent",
    [string]$Owner = $env:USERNAME,
    [string]$BaseBranch = "HEAD",

    # MergeToMain (T1443): integration merge target + optional explicit source branch.
    # TargetBranch defaults to "dev" (B+C pattern). When SourceBranch is omitted, the
    # task's code worktree branch is resolved from worktree metadata.
    [string]$TargetBranch = "dev",
    [string]$SourceBranch,
    [string]$WorktreeRoot = $env:GALD3R_WORKTREE_ROOT,
    [string]$TaskRoot,
    [int]$StaleHours = 24,
    # --- Keep: shared-sandbox phase handoff (T1118) ---
    # Marks an existing worktree as protected from Cleanup for KeepHours so the same
    # worktree/branch survives the g-go Phase 1 (implement) -> Phase 2 (review) handoff.
    # Writes keep_until (ISO-8601) + phase_handoff=true onto the ownership marker (additive).
    # Cleanup honours a future keep_until and skips removal during the handoff window.
    [int]$KeepHours = 2,
    [switch]$AllowDirty,
    # --- Stale-base detection (rolling-wave autopilot fix) ---
    # When an existing valid worktree is found on Create, compare its stored base_sha with the
    # current repo HEAD. If HEAD has advanced (main received new commits since the worktree was
    # branched), the existing worktree's base is stale.
    #   Reuse    - return the stale worktree unchanged (legacy behavior)
    #   Warn     - return the worktree but add stale_base=true fields to the result (default)
    #   Recreate - remove the stale worktree and create a fresh one from the current HEAD
    # Pass -StaleBaseAction Recreate for rolling-wave bucket worktrees so each iteration
    # forks from the latest commit rather than the session-start HEAD (BUG: stale-base).
    [ValidateSet("Reuse", "Warn", "Recreate")]
    [string]$StaleBaseAction = "Warn",
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
    [string]$Reason = "coordinator-cancel",

    # --- Checkpoint: write a continuity artifact for crash-safe resume (T967) ---
    # The continuity artifact is a structured resume summary distinct from the
    # conversation transcript. All fields are optional; absent fields render as a
    # placeholder so a partial checkpoint still produces a valid, resumable artifact.
    [string]$Goal,
    [string[]]$CompletedAcs = @(),
    [string[]]$PendingAcs = @(),
    [string]$LastToolSummary,
    [string]$NextAction,
    [string[]]$Blockers = @(),
    # SHA of the checkpoint commit this artifact precedes. Recorded on the marker so
    # Resume can report "Resuming from checkpoint {sha}". May be supplied after the
    # commit is created, or left blank when writing the artifact BEFORE the commit.
    [string]$CheckpointSha,

    # --- Steer / Queue: mid-flight course correction (T969) ---
    # Steer: when -SteerText is supplied, WRITE it to steer.md (overwrite — latest steer wins).
    #        when -SteerText is empty/absent, READ steer.md, return its body, and DELETE the file
    #        (one-shot inject consumed by the g-go-code AC-gate poll).
    # Queue: when -QueueText is supplied, APPEND it as a new queue.md item. when absent, READ the
    #        pending queue items.
    [string]$SteerText,
    [string]$QueueText,

    # --- Swarm file-lock manifests (T1059 - earendil-works/pi file-lock pattern) ---
    # On -Action Create, when -LockFiles is supplied, write a per-bucket lock manifest
    # under .gald3r-swarm-locks/lock_{bucket_id}.json listing the file paths this bucket
    # intends to modify, the owner, and an expiry timestamp. Before writing, existing
    # active (non-expired) manifests are re-read; if any claimed path overlaps another
    # bucket's active claim, Create fails with LOCK_CONFLICT (prints the conflicting
    # paths and owning bucket id). -Action LockReport re-reads all active manifests for
    # coordinator-side conflict detection (overlaps surfaced as WARN, never BLOCK).
    #
    # Phase 1: file-level locks only (no line-level granularity). Locks are ephemeral -
    # the .gald3r-swarm-locks/ directory is gald3rignored and never committed.
    [string]$BucketId,
    [string[]]$LockFiles = @(),
    # Bucket time-to-live in minutes; expiry = created_at + 2 * BucketTtlMinutes.
    [int]$BucketTtlMinutes = 60
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
        [switch]$AllowDirty,
        [string]$StaleBaseAction = "Warn"
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw "-TaskId is required for Create."
    }

    $existing = Find-Gald3rWorktree -Root $Root -RepoRoot $RepoRoot -TaskId $TaskId -Role $Role -Owner $Owner
    if (Test-ValidExistingWorktree -RepoRoot $RepoRoot -Metadata $existing) {
        # Stale-base detection: compare the stored base_sha (resolved at creation time) with
        # the current HEAD of the repo. When the autopilot commits iteration-N results to main,
        # HEAD advances. Iteration-(N+1) bucket worktrees still carry the session-start SHA as
        # their base_sha — those are stale and should be recreated so implementers see the
        # latest Alembic migrations, model files, and router wiring from prior iterations.
        $currentHead = (Invoke-Git -Repo $RepoRoot -Arguments @("rev-parse", "HEAD")).Trim()
        $storedBase  = if ($null -ne $existing.PSObject.Properties['base_sha'] -and
                           -not [string]::IsNullOrWhiteSpace($existing.base_sha)) {
            $existing.base_sha
        } else { $null }

        $isStale = ($null -ne $storedBase) -and ($storedBase -ne $currentHead)

        if ($isStale -and $StaleBaseAction -eq "Recreate") {
            # Remove the stale worktree; fall through to fresh creation below.
            Remove-Gald3rWorktree -RepoRoot $RepoRoot -Metadata $existing -Apply | Out-Null
        } elseif ($isStale -and $StaleBaseAction -eq "Warn") {
            $warnProps = [ordered]@{}
            foreach ($p in $existing.PSObject.Properties) { $warnProps[$p.Name] = $p.Value }
            $warnProps["stale_base"]        = $true
            $warnProps["stale_base_detail"] = "Worktree base $($storedBase.Substring(0, [Math]::Min(8,$storedBase.Length))) predates current HEAD $($currentHead.Substring(0, [Math]::Min(8,$currentHead.Length))). Pass -StaleBaseAction Recreate to auto-refresh for rolling waves."
            return [pscustomobject]$warnProps
        } else {
            # Reuse silently (explicit Reuse, or no base_sha stored on a legacy worktree).
            return $existing
        }
    }

    # The ephemeral swarm-lock directory (T1059) is gald3rignored coordination state,
    # never committed, so it must never count toward the dirty gate - otherwise a
    # bucket that claimed its own lock manifest would block its own worktree create.
    $dirty = @(Get-DirtyStatus -RepoRoot $RepoRoot | Where-Object { $_ -notmatch '\.gald3r-swarm-locks/' })
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

    # Resolve the base ref to a concrete SHA before creating the worktree.
    # Storing the resolved SHA (not the symbolic ref "HEAD") enables stale-base detection on
    # subsequent Create calls: if the repo HEAD has advanced since this worktree was branched,
    # the stored base_sha will differ from the current HEAD and the worktree is stale.
    $resolvedBaseSha = (Invoke-Git -Repo $RepoRoot -Arguments @("rev-parse", $BaseBranch)).Trim()

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
        base_sha = $resolvedBaseSha
        created_at = (Get-Date).ToUniversalTime().ToString("o")
        # T967 — session resume fields. Populated by the Checkpoint action; null at
        # creation time so a fresh worktree has no resume point yet.
        last_checkpoint_sha = $null
        continuity_artifact_path = $null
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

function Set-Gald3rWorktreeKeep {
    # T1118 - shared-sandbox phase handoff. Stamp an existing gald3r-owned worktree with a
    # future keep_until so Cleanup skips it across the g-go Phase 1 -> Phase 2 boundary.
    # Additive: preserves every existing marker field (PID, checkpoint, base_sha, etc.).
    param(
        [string]$RepoRoot,
        [object]$Metadata,
        [int]$KeepHours
    )

    if ($null -eq $Metadata -or -not $Metadata.gald3r_owned) {
        throw "Keep requires an existing gald3r-owned worktree (create it first with -Action Create)."
    }
    $markerPath = Join-Path $Metadata.worktree_path ".gald3r-worktree.json"
    if (-not (Test-Path $markerPath)) {
        throw "Ownership marker missing at '$markerPath' - refusing to Keep."
    }

    $keepUntil = (Get-Date).ToUniversalTime().AddHours([Math]::Max(0, $KeepHours)).ToString("o")
    $obj = [ordered]@{}
    foreach ($p in $Metadata.PSObject.Properties) { $obj[$p.Name] = $p.Value }
    $obj["phase_handoff"] = $true
    $obj["keep_until"] = $keepUntil
    Write-Metadata -MarkerPath $markerPath -Metadata $obj

    return [pscustomobject]@{
        action          = "kept"
        task_id         = $Metadata.task_id
        worktree_path   = $Metadata.worktree_path
        worktree_branch = $Metadata.worktree_branch
        keep_until      = $keepUntil
    }
}

function Test-WorktreeKept {
    # Returns $true when a worktree carries a keep_until that is still in the future (T1118).
    param([object]$Metadata)

    if ($null -eq $Metadata.PSObject.Properties['keep_until']) { return $false }
    $raw = $Metadata.keep_until
    if ([string]::IsNullOrWhiteSpace($raw)) { return $false }
    try {
        $until = ([datetime]$raw).ToUniversalTime()
    } catch {
        return $false
    }
    return $until -gt (Get-Date).ToUniversalTime()
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
        # T1118 - shared-sandbox handoff protection. A worktree stamped with a future
        # keep_until is mid Phase 1 -> Phase 2 handoff; never reclaim it during that window,
        # even if its claim looks expired or it is old by age.
        if (Test-WorktreeKept -Metadata $metadata) {
            continue
        }
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
# Integration merge (MergeToMain) — T1443 / BUG-099 recurrence prevention
# ---------------------------------------------------------------------------
# Fast-forward a task's code branch into an integration target (default "dev"),
# then delete the code + review branches and the worktree. Dry-run by default;
# only writes/merges when -Apply is passed (mirrors the Cleanup contract). The
# merge is FF-ONLY: a target that cannot fast-forward is reported as
# merge-blocked and is NEVER force-updated.

function Get-AheadBehind {
    # Returns @{ ahead = <commits in A not in B>; behind = <commits in B not in A> }
    # for A relative to B, via `git rev-list --left-right --count A...B`.
    param([string]$RepoRoot, [string]$RefA, [string]$RefB)
    $out = (Invoke-Git -Repo $RepoRoot -Arguments @("rev-list", "--left-right", "--count", "$RefA...$RefB")).Trim()
    $parts = $out -split "\s+"
    return @{ ahead = [int]$parts[0]; behind = [int]$parts[1] }
}

function Invoke-Gald3rMergeToMain {
    param(
        [string]$RepoRoot,
        [string]$Root,
        [string]$TaskId,
        [string]$Role,
        [string]$Owner,
        [string]$SourceBranch,
        [string]$TargetBranch,
        [switch]$Apply
    )

    # 1. Resolve the source (code) branch: explicit -SourceBranch wins; otherwise
    #    resolve from the task's worktree metadata.
    $metadata = $null
    if ([string]::IsNullOrWhiteSpace($SourceBranch)) {
        if ([string]::IsNullOrWhiteSpace($TaskId)) {
            throw "MergeToMain requires either -SourceBranch or -TaskId (to resolve the code worktree branch)."
        }
        $metadata = Find-Gald3rWorktree -Root $Root -RepoRoot $RepoRoot -TaskId $TaskId -Role $Role -Owner $Owner
        if ($null -eq $metadata) {
            throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner'. Pass -SourceBranch explicitly."
        }
        $SourceBranch = $metadata.worktree_branch
    }

    $mode = if ($Apply) { "apply" } else { "dry-run" }
    $result = [ordered]@{
        action  = "MergeToMain"
        mode    = $mode
        source  = $SourceBranch
        target  = $TargetBranch
        status  = $null
        message = $null
    }

    # 2. Both branches must exist.
    if (-not (Test-BranchExists -RepoRoot $RepoRoot -BranchName $SourceBranch)) {
        $result.status = "not-found"; $result.message = "source branch '$SourceBranch' does not exist"
        return [pscustomobject]$result
    }
    if (-not (Test-BranchExists -RepoRoot $RepoRoot -BranchName $TargetBranch)) {
        # g-go-go contract: missing target branch is merge-blocked, not an error.
        $result.status = "merge-blocked"; $result.message = "target branch '$TargetBranch' does not exist"
        return [pscustomobject]$result
    }

    # 3. FF-ability: target must be an ancestor of source (i.e. target is strictly
    #    behind-or-equal). Read-only check; no checkout side effects.
    $ab = Get-AheadBehind -RepoRoot $RepoRoot -RefA $SourceBranch -RefB $TargetBranch
    $result.source_ahead_of_target = $ab.ahead
    $result.target_ahead_of_source = $ab.behind
    $ffPossible = $false
    & git -C $RepoRoot merge-base --is-ancestor $TargetBranch $SourceBranch *> $null
    if ($LASTEXITCODE -eq 0) { $ffPossible = $true }

    if (-not $ffPossible) {
        $result.status = "merge-blocked"
        $result.message = "target '$TargetBranch' is $($ab.behind) commit(s) ahead of source; fast-forward not possible (would require a merge commit / conflict resolution) — not forcing"
        return [pscustomobject]$result
    }
    if ($ab.ahead -eq 0) {
        $result.status = "noop"; $result.message = "target '$TargetBranch' already contains source '$SourceBranch' (nothing to merge)"
        # Already merged: still safe to clean up branches/worktree under -Apply.
    }

    if (-not $Apply) {
        if ($result.status -ne "noop") {
            $result.status = "would-merge"
            $result.message = "would fast-forward '$TargetBranch' to '$SourceBranch' (+$($ab.ahead) commit(s)), then delete code+review branches and worktree"
        }
        return [pscustomobject]$result
    }

    # 4. APPLY: refuse if the main checkout has unrelated dirty paths.
    $dirty = Get-DirtyStatus -RepoRoot $RepoRoot
    if ($dirty.Count -gt 0) {
        $result.status = "merge-skipped-dirty"
        $result.message = "main checkout has $($dirty.Count) uncommitted path(s); refusing to merge"
        return [pscustomobject]$result
    }

    # 5. Fast-forward the target ref to source. If TargetBranch is the current
    #    branch, use merge --ff-only; otherwise update the ref via fetch (FF-safe,
    #    never forces) so we do not switch the user's checkout.
    $currentBranch = (Invoke-Git -Repo $RepoRoot -Arguments @("rev-parse", "--abbrev-ref", "HEAD")).Trim()
    if ($result.status -ne "noop") {
        try {
            if ($currentBranch -eq $TargetBranch) {
                Invoke-Git -Repo $RepoRoot -Arguments @("merge", "--ff-only", $SourceBranch) | Out-Null
            } else {
                # `git fetch . src:dst` updates dst to src only when it is a fast-forward.
                Invoke-Git -Repo $RepoRoot -Arguments @("fetch", ".", "$SourceBranch`:$TargetBranch") | Out-Null
            }
        } catch {
            $result.status = "merge-blocked"; $result.message = "fast-forward merge failed: $($_.Exception.Message)"
            return [pscustomobject]$result
        }
    }

    # 6. Delete code + review branches and the worktree (best-effort; merge already landed).
    $deleted = @()
    # Remove the worktree first (frees the branch checkout) if we resolved one.
    if ($null -ne $metadata) {
        try { Remove-Gald3rWorktree -RepoRoot $RepoRoot -Metadata $metadata -Apply:$true | Out-Null } catch {}
    }
    foreach ($b in @($SourceBranch)) {
        if ($b -ne $TargetBranch -and (Test-BranchExists -RepoRoot $RepoRoot -BranchName $b)) {
            try { Invoke-Git -Repo $RepoRoot -Arguments @("branch", "-D", $b) | Out-Null; $deleted += $b } catch {}
        }
    }
    # Sibling review branch: same path with /review/ role segment, if present.
    if ($SourceBranch -match "^gald3r/([^/]+)/[^/]+/(.+)$") {
        $reviewBranch = "gald3r/$($Matches[1])/review/$($Matches[2])"
        if ((Test-BranchExists -RepoRoot $RepoRoot -BranchName $reviewBranch)) {
            try { Invoke-Git -Repo $RepoRoot -Arguments @("branch", "-D", $reviewBranch) | Out-Null; $deleted += $reviewBranch } catch {}
        }
    }
    $result.deleted_branches = $deleted
    if ($result.status -ne "noop") {
        $result.status = "merged"
        $result.message = "fast-forwarded '$TargetBranch' to '$SourceBranch'; deleted $($deleted.Count) branch(es) + worktree"
    } else {
        $result.message += "; cleaned up $($deleted.Count) branch(es) + worktree"
    }
    return [pscustomobject]$result
}

# ---------------------------------------------------------------------------
# Cancellation signal threading (T1123 — sandcastle AbortSignal pattern)
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

# ---------------------------------------------------------------------------
# Session resume — continuity artifact + checkpoint (T967)
# ---------------------------------------------------------------------------
#
# The continuity artifact is a structured, on-disk resume summary written into
# the worktree after each implementation checkpoint. It is intentionally
# separate from the conversation transcript captured by gald3r_session_capture
# (which preserves the literal JSONL): the artifact answers "where was I and
# what is left" so long-horizon work can resume from the last clean state after
# a crash, OOM, or power loss.
#
# Durability (AC5): the artifact is written to a sibling temp file and then
# atomically renamed over the final path with Move-Item -Force. A kill between
# the write and the rename leaves the previous good artifact intact; the new one
# only appears once it is fully written. It is also written BEFORE the checkpoint
# commit so a crash during the commit still leaves a resumable artifact on disk.

function Format-ContinuityAcList {
    param([string[]]$Items, [string]$Box)

    if ($null -eq $Items -or $Items.Count -eq 0) {
        return "_none_"
    }
    return ($Items | ForEach-Object { "- [$Box] $_" }) -join [Environment]::NewLine
}

function Format-ContinuityBullets {
    param([string[]]$Items)

    if ($null -eq $Items -or $Items.Count -eq 0) {
        return "_none_"
    }
    return ($Items | ForEach-Object { "- $_" }) -join [Environment]::NewLine
}

function New-ContinuityArtifactBody {
    param(
        [string]$TaskId,
        [string]$Goal,
        [string[]]$CompletedAcs,
        [string[]]$PendingAcs,
        [string]$LastToolSummary,
        [string]$NextAction,
        [string[]]$Blockers,
        [string]$CheckpointSha,
        [string]$WorktreeBranch
    )

    $nl = [Environment]::NewLine
    $stamp = (Get-Date).ToUniversalTime().ToString("o")
    $goalText = if ([string]::IsNullOrWhiteSpace($Goal)) { "_not recorded_" } else { $Goal }
    $shaText = if ([string]::IsNullOrWhiteSpace($CheckpointSha)) { "_pending (artifact written before commit)_" } else { $CheckpointSha }
    $lastTool = if ([string]::IsNullOrWhiteSpace($LastToolSummary)) { "_not recorded_" } else { $LastToolSummary }
    $next = if ([string]::IsNullOrWhiteSpace($NextAction)) { "_not recorded_" } else { $NextAction }

    $lines = @(
        "# Continuity Artifact — Task $TaskId",
        "",
        "<!-- gald3r session-resume artifact (T967). Structured resume summary, not a transcript. -->",
        "",
        "- **Task**: $TaskId",
        "- **Worktree branch**: $WorktreeBranch",
        "- **Last checkpoint SHA**: $shaText",
        "- **Written at**: $stamp",
        "",
        "## Goal",
        "",
        $goalText,
        "",
        "## Completed Acceptance Criteria",
        "",
        (Format-ContinuityAcList -Items $CompletedAcs -Box "x"),
        "",
        "## Pending Acceptance Criteria",
        "",
        (Format-ContinuityAcList -Items $PendingAcs -Box " "),
        "",
        "## Last Tool Summary",
        "",
        $lastTool,
        "",
        "## Next Planned Action",
        "",
        $next,
        "",
        "## Blockers",
        "",
        (Format-ContinuityBullets -Items $Blockers),
        ""
    )
    return ($lines -join $nl)
}

function Write-ContinuityArtifact {
    param(
        [string]$RepoRoot,
        [object]$Metadata,
        [string]$Goal,
        [string[]]$CompletedAcs,
        [string[]]$PendingAcs,
        [string]$LastToolSummary,
        [string]$NextAction,
        [string[]]$Blockers,
        [string]$CheckpointSha
    )

    if ($null -eq $Metadata -or -not $Metadata.gald3r_owned) {
        throw "Checkpoint requires an existing gald3r-owned worktree (create it first with -Action Create)."
    }
    $markerPath = Join-Path $Metadata.worktree_path ".gald3r-worktree.json"
    if (-not (Test-Path $markerPath)) {
        throw "Ownership marker missing at '$markerPath' — refusing to write a continuity artifact."
    }

    $artifactPath = Join-Path $Metadata.worktree_path "continuity_artifact.md"
    $body = New-ContinuityArtifactBody `
        -TaskId $Metadata.task_id `
        -Goal $Goal `
        -CompletedAcs $CompletedAcs `
        -PendingAcs $PendingAcs `
        -LastToolSummary $LastToolSummary `
        -NextAction $NextAction `
        -Blockers $Blockers `
        -CheckpointSha $CheckpointSha `
        -WorktreeBranch $Metadata.worktree_branch

    # Atomic write (AC5): write to a unique temp file in the same directory, then
    # Move-Item -Force to swap it over the final path in one rename. Same-volume
    # rename is atomic; an interrupt before the rename leaves the prior artifact.
    $tempPath = Join-Path $Metadata.worktree_path (".continuity_artifact.$([guid]::NewGuid().ToString('N')).tmp")
    try {
        Set-Content -Path $tempPath -Value $body -Encoding UTF8 -NoNewline
        Move-Item -Path $tempPath -Destination $artifactPath -Force
    } finally {
        if (Test-Path $tempPath) {
            Remove-Item -Path $tempPath -Force -ErrorAction SilentlyContinue
        }
    }

    # Update the ownership marker (additive — preserve existing fields) with the
    # resume pointers (AC2). The marker is the small, fast index Resume reads first.
    $obj = [ordered]@{}
    foreach ($p in $Metadata.PSObject.Properties) { $obj[$p.Name] = $p.Value }
    if (-not [string]::IsNullOrWhiteSpace($CheckpointSha)) {
        $obj["last_checkpoint_sha"] = $CheckpointSha
    } elseif (-not $obj.Contains("last_checkpoint_sha")) {
        $obj["last_checkpoint_sha"] = $null
    }
    $obj["continuity_artifact_path"] = $artifactPath
    $obj["continuity_updated_at"] = (Get-Date).ToUniversalTime().ToString("o")
    Write-Metadata -MarkerPath $markerPath -Metadata $obj

    return [pscustomobject]@{
        action                   = "checkpoint"
        task_id                  = $Metadata.task_id
        worktree_path            = $Metadata.worktree_path
        worktree_branch          = $Metadata.worktree_branch
        continuity_artifact_path = $artifactPath
        last_checkpoint_sha      = $obj["last_checkpoint_sha"]
        completed_ac_count       = @($CompletedAcs).Count
        pending_ac_count         = @($PendingAcs).Count
    }
}

function Resume-FromContinuityArtifact {
    # Locate the worktree for a task, read its continuity artifact, and emit the
    # resume banner + artifact body so g-go-code --resume can inject it as a
    # context prefix (AC3/AC4). Read-only — never writes.
    param(
        [string]$Root,
        [string]$RepoRoot,
        [string]$TaskId,
        [string]$Role,
        [string]$Owner
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw "-TaskId is required for Resume."
    }

    $metadata = Find-Gald3rWorktree -Root $Root -RepoRoot $RepoRoot -TaskId $TaskId -Role $Role -Owner $Owner
    if ($null -eq $metadata) {
        throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner' — nothing to resume."
    }

    $artifactPath = $null
    if ($null -ne $metadata.PSObject.Properties['continuity_artifact_path'] -and -not [string]::IsNullOrWhiteSpace($metadata.continuity_artifact_path)) {
        $artifactPath = $metadata.continuity_artifact_path
    } else {
        $artifactPath = Join-Path $metadata.worktree_path "continuity_artifact.md"
    }

    if (-not (Test-Path $artifactPath)) {
        throw "No continuity artifact found at '$artifactPath' — task '$TaskId' has no checkpoint to resume from."
    }

    $body = Get-Content -Path $artifactPath -Raw

    # Derive the AC counts for the resume banner (AC4). Prefer the artifact's
    # checked/unchecked AC lines; fall back to 0 when the section is empty.
    $completed = ([regex]::Matches($body, '(?m)^- \[x\] ')).Count
    $remaining = ([regex]::Matches($body, '(?m)^- \[ \] ')).Count

    $sha = if ($null -ne $metadata.PSObject.Properties['last_checkpoint_sha'] -and -not [string]::IsNullOrWhiteSpace($metadata.last_checkpoint_sha)) {
        $metadata.last_checkpoint_sha
    } else {
        "(no commit recorded)"
    }

    $banner = "Resuming from checkpoint $sha — $completed ACs complete, $remaining remaining"

    return [pscustomobject]@{
        action                   = "resume"
        task_id                  = $metadata.task_id
        worktree_path            = $metadata.worktree_path
        worktree_branch          = $metadata.worktree_branch
        last_checkpoint_sha      = $metadata.last_checkpoint_sha
        continuity_artifact_path = $artifactPath
        completed_ac_count       = $completed
        remaining_ac_count       = $remaining
        banner                   = $banner
        context_prefix           = $body
    }
}

function Invoke-WorktreeSteer {
    # T969 — write or read+clear steer.md at the worktree root.
    #   -SteerText present  => WRITE steer.md (overwrite; latest steer wins), action="steer-write".
    #   -SteerText absent    => READ steer.md, return body, DELETE the file, action="steer-read".
    #                           When no steer.md exists, returns steered=$false (a no-op poll).
    param(
        [string]$Root,
        [string]$RepoRoot,
        [string]$TaskId,
        [string]$Role,
        [string]$Owner,
        [string]$SteerText
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw "-TaskId is required for Steer."
    }

    $metadata = Find-Gald3rWorktree -Root $Root -RepoRoot $RepoRoot -TaskId $TaskId -Role $Role -Owner $Owner
    if ($null -eq $metadata) {
        throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner' — cannot steer."
    }

    $steerPath = Join-Path $metadata.worktree_path "steer.md"
    $stamp = (Get-Date).ToUniversalTime().ToString("o")

    if (-not [string]::IsNullOrWhiteSpace($SteerText)) {
        # WRITE mode — atomic temp-file + rename so a poll never reads a half-written file.
        $nl = [Environment]::NewLine
        $body = (@(
            "# Steer — Task $TaskId",
            "",
            "<!-- gald3r mid-flight steering prompt (T969). g-go-code injects this at the next AC-gate, logs 'STEERED', then deletes it. -->",
            "",
            "- **Written at**: $stamp",
            "",
            "## Steering Prompt",
            "",
            $SteerText.Trim(),
            ""
        ) -join $nl)
        $tempPath = Join-Path $metadata.worktree_path (".steer.$([guid]::NewGuid().ToString('N')).tmp")
        try {
            Set-Content -Path $tempPath -Value $body -Encoding UTF8 -NoNewline
            Move-Item -Path $tempPath -Destination $steerPath -Force
        } finally {
            if (Test-Path $tempPath) { Remove-Item -Path $tempPath -Force -ErrorAction SilentlyContinue }
        }
        return [pscustomobject]@{
            action        = "steer-write"
            task_id       = $metadata.task_id
            worktree_path = $metadata.worktree_path
            steer_path    = $steerPath
            written_at    = $stamp
        }
    }

    # READ + CLEAR mode (the AC-gate poll).
    if (-not (Test-Path $steerPath)) {
        return [pscustomobject]@{
            action        = "steer-read"
            task_id       = $metadata.task_id
            worktree_path = $metadata.worktree_path
            steer_path    = $steerPath
            steered       = $false
            steer_prompt  = $null
        }
    }

    $raw = Get-Content -Path $steerPath -Raw
    Remove-Item -Path $steerPath -Force
    return [pscustomobject]@{
        action        = "steer-read"
        task_id       = $metadata.task_id
        worktree_path = $metadata.worktree_path
        steer_path    = $steerPath
        steered       = $true
        steer_prompt  = $raw
    }
}

function Invoke-WorktreeQueue {
    # T969 — append a follow-up prompt to queue.md, or read the pending queue.
    #   -QueueText present => APPEND a new "- [ ] {text}" item, action="queue-append".
    #   -QueueText absent   => READ pending items, action="queue-read".
    param(
        [string]$Root,
        [string]$RepoRoot,
        [string]$TaskId,
        [string]$Role,
        [string]$Owner,
        [string]$QueueText
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw "-TaskId is required for Queue."
    }

    $metadata = Find-Gald3rWorktree -Root $Root -RepoRoot $RepoRoot -TaskId $TaskId -Role $Role -Owner $Owner
    if ($null -eq $metadata) {
        throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner' — cannot queue."
    }

    $queuePath = Join-Path $metadata.worktree_path "queue.md"
    $nl = [Environment]::NewLine

    if (-not [string]::IsNullOrWhiteSpace($QueueText)) {
        # APPEND mode — create the file with a header on first write, then append one item per call.
        if (-not (Test-Path $queuePath)) {
            $header = (@(
                "# Follow-up Queue — Task $TaskId",
                "",
                "<!-- gald3r mid-flight follow-up queue (T969). g-go-code drains these after the main goal is complete. One item per line. -->",
                ""
            ) -join $nl)
            Set-Content -Path $queuePath -Value $header -Encoding UTF8
        }
        # Single-line item; collapse internal newlines so each queue entry stays on one row.
        $item = "- [ ] " + ($QueueText.Trim() -replace '\r?\n', ' ')
        Add-Content -Path $queuePath -Value $item -Encoding UTF8
        $pending = @([regex]::Matches((Get-Content -Path $queuePath -Raw), '(?m)^- \[ \] ')).Count
        return [pscustomobject]@{
            action          = "queue-append"
            task_id         = $metadata.task_id
            worktree_path   = $metadata.worktree_path
            queue_path      = $queuePath
            appended_item   = $item
            pending_count   = $pending
        }
    }

    # READ mode.
    if (-not (Test-Path $queuePath)) {
        return [pscustomobject]@{
            action        = "queue-read"
            task_id       = $metadata.task_id
            worktree_path = $metadata.worktree_path
            queue_path    = $queuePath
            pending_count = 0
            items         = @()
        }
    }

    $body = Get-Content -Path $queuePath -Raw
    $items = @([regex]::Matches($body, '(?m)^- \[ \] (.+)$') | ForEach-Object { $_.Groups[1].Value })
    return [pscustomobject]@{
        action        = "queue-read"
        task_id       = $metadata.task_id
        worktree_path = $metadata.worktree_path
        queue_path    = $queuePath
        pending_count = $items.Count
        items         = $items
    }
}

# ---------------------------------------------------------------------------
# Swarm file-lock manifests (T1059 - earendil-works/pi file-lock pattern)
# ---------------------------------------------------------------------------
#
# Each parallel swarm bucket declares the files it intends to modify in a lock
# manifest written under .gald3r-swarm-locks/lock_{bucket_id}.json BEFORE it
# starts work. The Create action checks existing active manifests for overlap and
# refuses (LOCK_CONFLICT) so two buckets never claim the same file. The coordinator
# re-reads all manifests before reconciliation (LockReport) and surfaces any file
# claimed by more than one bucket as a WARN - not a BLOCK - to allow manual override.
#
# Manifests are ephemeral: the .gald3r-swarm-locks/ directory is listed in
# .gald3rignore (visible during an active swarm, never committed). Expired
# manifests (expires_at in the past) are silently ignored everywhere.

function Get-SwarmLockDir {
    param([string]$RepoRoot)
    return Join-Path $RepoRoot ".gald3r-swarm-locks"
}

function ConvertTo-NormalizedLockPath {
    # Normalize a claimed path to a stable, case-insensitive comparison key.
    # Backslashes become forward slashes; leading "./" is stripped; trailing
    # separators are trimmed. Relative paths are kept relative (repo-root anchored).
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    $p = $Path.Trim() -replace '\\', '/'
    $p = $p -replace '^\./', ''
    $p = $p.TrimEnd('/')
    return $p.ToLowerInvariant()
}

function Get-ActiveSwarmLocks {
    # Read every lock_*.json manifest in the lock dir, skipping expired ones.
    # Returns an array of psobjects: { bucket_id, owner, paths[], created_at,
    # expires_at, manifest_path, normalized_paths[] }.
    param([string]$RepoRoot)

    $lockDir = Get-SwarmLockDir -RepoRoot $RepoRoot
    if (-not (Test-Path $lockDir)) { return @() }

    $now = (Get-Date).ToUniversalTime()
    $active = @()
    foreach ($file in (Get-ChildItem -Path $lockDir -Filter "lock_*.json" -File -ErrorAction SilentlyContinue)) {
        $manifest = $null
        try {
            $manifest = Get-Content -Path $file.FullName -Raw | ConvertFrom-Json
        } catch {
            continue
        }
        if ($null -eq $manifest) { continue }

        # Silently ignore expired locks (Implementation Note: expired locks are ignored).
        # The stored value is ISO-8601 UTC ("...Z"). ConvertFrom-Json may hand it back as a
        # System.DateTime whose wall-clock equals the UTC value but with Kind=Local - calling
        # .ToUniversalTime() on that would double-shift it. Coerce to a true UTC instant:
        #   - DateTime  -> reinterpret the wall-clock components as UTC (SpecifyKind Utc)
        #   - string    -> parse with AssumeUniversal/AdjustToUniversal
        $expiresRaw = $manifest.expires_at
        if ($null -ne $expiresRaw -and -not [string]::IsNullOrWhiteSpace([string]$expiresRaw)) {
            $expiresUtc = $null
            if ($expiresRaw -is [datetime]) {
                $dt = [datetime]$expiresRaw
                if ($dt.Kind -eq [System.DateTimeKind]::Utc) {
                    $expiresUtc = $dt
                } else {
                    $expiresUtc = [datetime]::SpecifyKind($dt, [System.DateTimeKind]::Utc)
                }
            } else {
                $parsed = [datetime]::MinValue
                $styles = [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal
                if ([datetime]::TryParse([string]$expiresRaw, [System.Globalization.CultureInfo]::InvariantCulture, $styles, [ref]$parsed)) {
                    $expiresUtc = $parsed
                }
            }
            if ($null -ne $expiresUtc -and $expiresUtc -lt $now) { continue }
        }

        $paths = @()
        if ($null -ne $manifest.PSObject.Properties['paths'] -and $null -ne $manifest.paths) {
            $paths = @($manifest.paths)
        }
        $normalized = @($paths | ForEach-Object { ConvertTo-NormalizedLockPath -Path $_ } | Where-Object { $_ })

        $active += [pscustomobject]@{
            bucket_id       = $manifest.bucket_id
            owner           = $manifest.owner
            paths           = $paths
            created_at      = $manifest.created_at
            expires_at      = $manifest.expires_at
            manifest_path   = $file.FullName
            normalized_paths = $normalized
        }
    }
    return $active
}

function Write-SwarmLockManifest {
    # Check for overlap against other buckets' active manifests, then write this
    # bucket's manifest. Throws LOCK_CONFLICT (listing conflicting paths + owning
    # bucket id) when any claimed path overlaps another active bucket's claim.
    # A manifest already owned by the same bucket_id is treated as a refresh
    # (its own paths do not count as a conflict).
    param(
        [string]$RepoRoot,
        [string]$BucketId,
        [string]$Owner,
        [string[]]$LockFiles,
        [int]$BucketTtlMinutes
    )

    if ([string]::IsNullOrWhiteSpace($BucketId)) {
        throw "-BucketId is required to write a swarm lock manifest."
    }

    $claimedNormalized = @($LockFiles | ForEach-Object { ConvertTo-NormalizedLockPath -Path $_ } | Where-Object { $_ })
    if ($claimedNormalized.Count -eq 0) {
        throw "-LockFiles must list at least one path to claim for bucket '$BucketId'."
    }

    $conflicts = @()
    foreach ($lock in (Get-ActiveSwarmLocks -RepoRoot $RepoRoot)) {
        if ($lock.bucket_id -eq $BucketId) { continue }   # our own prior manifest = refresh, not a conflict
        foreach ($claimed in $claimedNormalized) {
            if ($lock.normalized_paths -contains $claimed) {
                $conflicts += [pscustomobject]@{
                    path           = $claimed
                    owning_bucket  = $lock.bucket_id
                    owning_owner   = $lock.owner
                }
            }
        }
    }

    if ($conflicts.Count -gt 0) {
        $detail = ($conflicts | ForEach-Object { "$($_.path) (owned by bucket '$($_.owning_bucket)')" }) -join "; "
        throw "LOCK_CONFLICT: bucket '$BucketId' claims path(s) already locked by another bucket: $detail"
    }

    $lockDir = Get-SwarmLockDir -RepoRoot $RepoRoot
    if (-not (Test-Path $lockDir)) {
        New-Item -ItemType Directory -Path $lockDir -Force | Out-Null
    }

    $createdAt = (Get-Date).ToUniversalTime()
    $expiresAt = $createdAt.AddMinutes(2 * [Math]::Max(1, $BucketTtlMinutes))
    $safeBucket = ConvertTo-SafeSegment -Value $BucketId
    $manifestPath = Join-Path $lockDir "lock_$safeBucket.json"

    $manifest = [ordered]@{
        schema_version = "1.0"
        bucket_id      = $BucketId
        owner          = $Owner
        paths          = @($LockFiles)
        created_at     = $createdAt.ToString("o")
        expires_at     = $expiresAt.ToString("o")
        ttl_minutes    = $BucketTtlMinutes
    }

    # Atomic write: temp file + rename so a concurrent reader never sees a half file.
    $tempPath = Join-Path $lockDir (".lock_$safeBucket.$([guid]::NewGuid().ToString('N')).tmp")
    try {
        $manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $tempPath -Encoding UTF8
        Move-Item -Path $tempPath -Destination $manifestPath -Force
    } finally {
        if (Test-Path $tempPath) { Remove-Item -Path $tempPath -Force -ErrorAction SilentlyContinue }
    }

    return [pscustomobject]@{
        action        = "lock-claimed"
        bucket_id     = $BucketId
        owner         = $Owner
        manifest_path = $manifestPath
        paths         = @($LockFiles)
        created_at    = $manifest["created_at"]
        expires_at    = $manifest["expires_at"]
    }
}

function Get-SwarmLockConflictReport {
    # Coordinator-side conflict detection: re-read all active manifests and flag any
    # file claimed by more than one bucket. Overlaps are surfaced as WARN (never BLOCK)
    # to allow manual override before reconciliation.
    param([string]$RepoRoot)

    $locks = @(Get-ActiveSwarmLocks -RepoRoot $RepoRoot)

    # Map normalized path -> list of bucket ids claiming it.
    $byPath = @{}
    foreach ($lock in $locks) {
        for ($i = 0; $i -lt $lock.normalized_paths.Count; $i++) {
            $norm = $lock.normalized_paths[$i]
            $orig = if ($i -lt @($lock.paths).Count) { @($lock.paths)[$i] } else { $norm }
            if (-not $byPath.ContainsKey($norm)) {
                $byPath[$norm] = [pscustomobject]@{ path = $orig; buckets = @() }
            }
            $byPath[$norm].buckets += $lock.bucket_id
        }
    }

    $conflicts = @()
    foreach ($key in $byPath.Keys) {
        $entry = $byPath[$key]
        $uniqueBuckets = @($entry.buckets | Select-Object -Unique)
        if ($uniqueBuckets.Count -gt 1) {
            $conflicts += [pscustomobject]@{
                path    = $entry.path
                buckets = $uniqueBuckets
                level   = "WARN"
            }
        }
    }

    return [pscustomobject]@{
        action          = "lock-report"
        active_locks    = $locks.Count
        conflict_count  = $conflicts.Count
        conflicts       = $conflicts
        locks           = @($locks | Select-Object bucket_id, owner, paths, expires_at)
    }
}

$repoRoot = Resolve-RepoRoot -Path $RepoPath
$resolvedRoot = Get-WorktreeRoot -RepoRoot $repoRoot -RequestedRoot $WorktreeRoot

switch ($Action) {
    "Create" {
        # T1059 - when the bucket declares a file scope (-LockFiles), claim the lock
        # manifest FIRST. This fails with LOCK_CONFLICT before any worktree is created
        # if another active bucket already claims an overlapping path, so a conflicting
        # bucket never even spawns its worktree.
        $lockResult = $null
        if ($null -ne $LockFiles -and @($LockFiles).Count -gt 0) {
            $lockResult = Write-SwarmLockManifest -RepoRoot $repoRoot -BucketId $BucketId -Owner $Owner -LockFiles $LockFiles -BucketTtlMinutes $BucketTtlMinutes
        }
        $result = New-Gald3rWorktree -RepoRoot $repoRoot -Root $resolvedRoot -TaskId $TaskId -Role $Role -Owner $Owner -BaseBranch $BaseBranch -AllowDirty:$AllowDirty -StaleBaseAction $StaleBaseAction
        if ($null -ne $lockResult) {
            # Surface the lock claim alongside the worktree metadata (additive fields).
            $merged = [ordered]@{}
            foreach ($p in $result.PSObject.Properties) { $merged[$p.Name] = $p.Value }
            $merged["swarm_lock_manifest"] = $lockResult.manifest_path
            $merged["swarm_lock_bucket_id"] = $lockResult.bucket_id
            $merged["swarm_lock_expires_at"] = $lockResult.expires_at
            $result = [pscustomobject]$merged
        }
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
    "Keep" {
        if ([string]::IsNullOrWhiteSpace($TaskId)) {
            throw "-TaskId is required for Keep."
        }
        $metadata = Find-Gald3rWorktree -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner
        if ($null -eq $metadata) {
            throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner'. Create it first."
        }
        $result = Set-Gald3rWorktreeKeep -RepoRoot $repoRoot -Metadata $metadata -KeepHours $KeepHours
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
    "Checkpoint" {
        if ([string]::IsNullOrWhiteSpace($TaskId)) {
            throw "-TaskId is required for Checkpoint."
        }
        $metadata = Find-Gald3rWorktree -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner
        if ($null -eq $metadata) {
            throw "No gald3r-owned worktree found for task '$TaskId', role '$Role', owner '$Owner'. Create it first."
        }
        $result = Write-ContinuityArtifact -RepoRoot $repoRoot -Metadata $metadata -Goal $Goal -CompletedAcs $CompletedAcs -PendingAcs $PendingAcs -LastToolSummary $LastToolSummary -NextAction $NextAction -Blockers $Blockers -CheckpointSha $CheckpointSha
    }
    "Resume" {
        $result = Resume-FromContinuityArtifact -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner
    }
    "Steer" {
        $result = Invoke-WorktreeSteer -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner -SteerText $SteerText
    }
    "Queue" {
        $result = Invoke-WorktreeQueue -Root $resolvedRoot -RepoRoot $repoRoot -TaskId $TaskId -Role $Role -Owner $Owner -QueueText $QueueText
    }
    "LockReport" {
        # T1059 - coordinator conflict detection. Re-read all active swarm lock
        # manifests and flag files claimed by more than one bucket (WARN, not BLOCK).
        $result = Get-SwarmLockConflictReport -RepoRoot $repoRoot
    }
    "MergeToMain" {
        # T1443 - integration merge. FF-only; dry-run by default, -Apply to write.
        $result = Invoke-Gald3rMergeToMain -RepoRoot $repoRoot -Root $resolvedRoot -TaskId $TaskId -Role $Role -Owner $Owner -SourceBranch $SourceBranch -TargetBranch $TargetBranch -Apply:$Apply
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
