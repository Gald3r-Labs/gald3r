<#
.SYNOPSIS
    Capture Claude Code session JSONL from a worktree to the host for cross-sandbox resume.

.DESCRIPTION
    Implements Task 1124 (sandcastle-pattern session capture). After a g-go iteration runs
    inside an agent worktree/sandbox, the active Claude Code session transcript lives under
    the worktree's encoded project folder. This helper:

      1. Locates the Claude Code session JSONL for a given worktree path
      2. Copies it to a stable host location keyed by project + task + session id
      3. Rewrites embedded `cwd` (and any worktree absolute-path references) to the host
         repo path so `claude --resume <session_id>` works natively from any sandbox
      4. Records session metadata in sessions.json

    This is distinct from `memory_capture_session` (semantic search over summaries). JSONL
    capture preserves the full conversation thread for native `--resume`.

    Path encoding:
      Claude Code names each project folder by replacing every non-alphanumeric character
      in the absolute cwd with '-'. e.g. "G:\gald3r_ecosystem\gald3r_dev"
      -> "G--gald3r-ecosystem-gald3r-dev".

    Default locations (overridable):
      Claude projects dir : $env:CLAUDE_CONFIG_DIR\projects, else ~/.claude/projects
      Sessions root       : $env:GALD3R_SESSIONS_ROOT, else ~/.gald3r-sessions

.PARAMETER Action
    Capture  - locate, copy, cwd-rewrite, and record one session (default writer; needs -Apply to write)
    List     - list recorded sessions for a project from sessions.json
    Resolve  - given -SessionId, print the host JSONL path and the `claude --resume` command
    Report   - default; print resolved paths and what Capture would do (no writes)

.PARAMETER WorktreePath
    Path of the worktree/sandbox the session ran in. Default: current directory.

.PARAMETER HostRepoPath
    Canonical host repo path that cwd fields should be rewritten to. Default: resolved git
    top-level of WorktreePath's main working tree, else the parent repo of the worktree.

.PARAMETER ProjectId
    Stable project id used as the sessions.json key. Default: read from .gald3r/.project_id
    under HostRepoPath, else the encoded host repo folder name.

.PARAMETER TaskId
    Task id this capture is associated with (used in the host path layout).

.PARAMETER SessionId
    Explicit Claude session id (JSONL basename without extension). Default: newest *.jsonl
    in the worktree's encoded project folder.

.PARAMETER SessionsRoot
    Root for captured sessions. Default: $env:GALD3R_SESSIONS_ROOT or ~/.gald3r-sessions.

.PARAMETER ClaudeProjectsDir
    Claude Code projects directory. Default: $env:CLAUDE_CONFIG_DIR\projects or ~/.claude/projects.

.PARAMETER Apply
    Perform writes. Without it, Capture is a dry-run (Report-equivalent output).

.PARAMETER Json
    Emit a machine-readable JSON result object instead of human text.

.EXAMPLE
    pwsh -File gald3r_session_capture.ps1 -Action Capture -WorktreePath ../.gald3r-worktrees/gald3r_dev/T1124 -TaskId 1124 -Apply

.EXAMPLE
    pwsh -File gald3r_session_capture.ps1 -Action Resolve -SessionId 7f3c... -ProjectId my-proj
#>

param(
    [ValidateSet("Capture", "List", "Resolve", "Report")]
    [string]$Action = "Report",

    [string]$WorktreePath = ".",
    [string]$HostRepoPath,
    [string]$ProjectId,
    [string]$TaskId,
    [string]$SessionId,
    [string]$SessionsRoot = $env:GALD3R_SESSIONS_ROOT,
    [string]$ClaudeProjectsDir,
    [switch]$Apply,
    [switch]$Json
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Get-HomeDir {
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) { return $env:USERPROFILE }
    if (-not [string]::IsNullOrWhiteSpace($env:HOME)) { return $env:HOME }
    return [Environment]::GetFolderPath("UserProfile")
}

function ConvertTo-ClaudeProjectFolder {
    # Mirror Claude Code's project-folder encoding: every non-alphanumeric char -> '-'.
    param([string]$Path)
    return ($Path -replace '[^A-Za-z0-9]', '-')
}

function Resolve-GitTopLevel {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $top = & git -C $Path rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($top)) {
            return ((Resolve-Path -LiteralPath $top.Trim()).Path)
        }
    } finally {
        $ErrorActionPreference = $saved
    }
    return $null
}

function Resolve-HostRepoPath {
    # The host repo is the COMMON git dir's working tree, not the worktree itself.
    # `git rev-parse --path-format=absolute --git-common-dir` points at <mainrepo>/.git.
    param([string]$WorktreePath)
    if (-not (Test-Path -LiteralPath $WorktreePath)) { return $null }
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $common = & git -C $WorktreePath rev-parse --path-format=absolute --git-common-dir 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($common)) {
            $commonDir = $common.Trim()
            # common-dir is "<mainrepo>/.git"; its parent is the host working tree.
            $parent = Split-Path -Parent $commonDir
            if ($parent -and (Test-Path -LiteralPath $parent)) {
                return ((Resolve-Path -LiteralPath $parent).Path)
            }
        }
    } finally {
        $ErrorActionPreference = $saved
    }
    # Fallback: the worktree's own top-level (no worktree => host == worktree).
    return (Resolve-GitTopLevel -Path $WorktreePath)
}

function Get-ProjectIdFor {
    param([string]$RepoPath)
    $idFile = Join-Path $RepoPath ".gald3r/.project_id"
    if (Test-Path -LiteralPath $idFile) {
        $val = (Get-Content -LiteralPath $idFile -Raw).Trim()
        if (-not [string]::IsNullOrWhiteSpace($val)) { return $val }
    }
    return (ConvertTo-ClaudeProjectFolder -Path $RepoPath)
}

function Write-JsonOrText {
    param($Object, [string]$Text)
    if ($Json) {
        $Object | ConvertTo-Json -Depth 8
    } else {
        $Text
    }
}

# ---------------------------------------------------------------------------
# Resolve common context
# ---------------------------------------------------------------------------

$homeDir = Get-HomeDir

if ([string]::IsNullOrWhiteSpace($SessionsRoot)) {
    $SessionsRoot = Join-Path $homeDir ".gald3r-sessions"
}

if ([string]::IsNullOrWhiteSpace($ClaudeProjectsDir)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CLAUDE_CONFIG_DIR)) {
        $ClaudeProjectsDir = Join-Path $env:CLAUDE_CONFIG_DIR "projects"
    } else {
        $ClaudeProjectsDir = Join-Path $homeDir ".claude/projects"
    }
}

# Resolve worktree to an absolute path when it exists on disk.
$worktreeAbs = $WorktreePath
if (Test-Path -LiteralPath $WorktreePath) {
    $worktreeAbs = (Resolve-Path -LiteralPath $WorktreePath).Path
}

if ([string]::IsNullOrWhiteSpace($HostRepoPath)) {
    $HostRepoPath = Resolve-HostRepoPath -WorktreePath $worktreeAbs
}
if ($HostRepoPath -and (Test-Path -LiteralPath $HostRepoPath)) {
    $HostRepoPath = (Resolve-Path -LiteralPath $HostRepoPath).Path
}

if ([string]::IsNullOrWhiteSpace($ProjectId) -and $HostRepoPath) {
    $ProjectId = Get-ProjectIdFor -RepoPath $HostRepoPath
}

# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

function Invoke-List {
    $sessionsJson = Join-Path (Join-Path $SessionsRoot $ProjectId) "sessions.json"
    if (-not (Test-Path -LiteralPath $sessionsJson)) {
        Write-JsonOrText -Object @{ project_id = $ProjectId; sessions = @() } `
            -Text "No captured sessions for project '$ProjectId' (expected $sessionsJson)."
        return
    }
    $data = Get-Content -LiteralPath $sessionsJson -Raw | ConvertFrom-Json
    if ($Json) {
        @{ project_id = $ProjectId; sessions = @($data) } | ConvertTo-Json -Depth 8
        return
    }
    "Captured sessions for project '$ProjectId':"
    foreach ($s in @($data)) {
        "  {0}  task={1}  {2}" -f $s.session_id, $s.task_id, $s.timestamp
    }
}

# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

function Invoke-Resolve {
    if ([string]::IsNullOrWhiteSpace($SessionId)) {
        throw "Resolve requires -SessionId."
    }
    $sessionsJson = Join-Path (Join-Path $SessionsRoot $ProjectId) "sessions.json"
    $rec = $null
    if (Test-Path -LiteralPath $sessionsJson) {
        $data = Get-Content -LiteralPath $sessionsJson -Raw | ConvertFrom-Json
        $rec = @($data) | Where-Object { $_.session_id -eq $SessionId } | Select-Object -First 1
    }
    $hostJsonl = if ($rec) { $rec.host_jsonl_path } else {
        Join-Path (Join-Path (Join-Path $SessionsRoot $ProjectId) ($rec.task_id)) "$SessionId.jsonl"
    }
    $resumeCmd = "claude --resume $SessionId"
    if ($Json) {
        @{ session_id = $SessionId; host_jsonl_path = $hostJsonl; resume_command = $resumeCmd; record = $rec } |
            ConvertTo-Json -Depth 8
        return
    }
    "Session:  $SessionId"
    "JSONL:    $hostJsonl"
    "Resume:   $resumeCmd"
    if (-not $rec) { "(no metadata record found in $sessionsJson)" }
}

# ---------------------------------------------------------------------------
# Capture (and Report = dry-run Capture)
# ---------------------------------------------------------------------------

function Find-WorktreeSessionJsonl {
    $folderName = ConvertTo-ClaudeProjectFolder -Path $worktreeAbs
    $projFolder = Join-Path $ClaudeProjectsDir $folderName
    if (-not (Test-Path -LiteralPath $projFolder)) {
        return [pscustomobject]@{ ProjFolder = $projFolder; File = $null }
    }
    $file = $null
    if (-not [string]::IsNullOrWhiteSpace($SessionId)) {
        $candidate = Join-Path $projFolder "$SessionId.jsonl"
        if (Test-Path -LiteralPath $candidate) { $file = Get-Item -LiteralPath $candidate }
    } else {
        $file = Get-ChildItem -LiteralPath $projFolder -Filter "*.jsonl" -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    }
    return [pscustomobject]@{ ProjFolder = $projFolder; File = $file }
}

function Repair-CwdPaths {
    # Rewrite worktree absolute-path references to the host repo path across the JSONL.
    # JSON encodes Windows backslashes as "\\"; rewrite both raw and JSON-escaped forms so
    # cwd, file references, and tool args all resolve under the host repo after --resume.
    param([string[]]$Lines, [string]$FromPath, [string]$ToPath)

    # Build JSON-escaped variants: each single backslash separator becomes two
    # backslashes, matching how the path appears inside the JSONL on disk.
    $fromEsc = $FromPath.Replace('\', '\\')
    $toEsc = $ToPath.Replace('\', '\\')

    $out = New-Object System.Collections.Generic.List[string]
    foreach ($line in $Lines) {
        $rewritten = $line
        # JSON-escaped (Windows) form first, then raw form (POSIX or already-unescaped).
        $rewritten = $rewritten.Replace($fromEsc, $toEsc)
        $rewritten = $rewritten.Replace($FromPath, $ToPath)
        $out.Add($rewritten)
    }
    return $out.ToArray()
}

function Invoke-Capture {
    param([bool]$DoApply)

    $found = Find-WorktreeSessionJsonl
    $result = [ordered]@{
        action          = "Capture"
        applied         = $DoApply
        worktree_path   = $worktreeAbs
        host_repo_path  = $HostRepoPath
        project_id      = $ProjectId
        task_id         = $TaskId
        claude_proj_dir = $found.ProjFolder
        session_id      = $null
        source_jsonl    = $null
        host_jsonl_path = $null
        sessions_json   = $null
        cwd_rewrites    = 0
        status          = $null
    }

    if (-not $found.File) {
        $result.status = "no-session-found"
        Write-JsonOrText -Object $result `
            -Text "No session JSONL found under $($found.ProjFolder). Nothing to capture."
        return
    }

    $sourceJsonl = $found.File.FullName
    $sid = if (-not [string]::IsNullOrWhiteSpace($SessionId)) { $SessionId } else { $found.File.BaseName }
    $result.session_id = $sid
    $result.source_jsonl = $sourceJsonl

    $taskSeg = if ([string]::IsNullOrWhiteSpace($TaskId)) { "_no-task" } else { $TaskId }
    $destDir = Join-Path (Join-Path $SessionsRoot $ProjectId) $taskSeg
    $destJsonl = Join-Path $destDir "$sid.jsonl"
    $sessionsJson = Join-Path (Join-Path $SessionsRoot $ProjectId) "sessions.json"
    $result.host_jsonl_path = $destJsonl
    $result.sessions_json = $sessionsJson

    # Compute cwd-rewrite count for reporting (and to perform it on apply).
    $lines = Get-Content -LiteralPath $sourceJsonl
    $rewritten = $lines
    $doRewrite = ($HostRepoPath -and ($worktreeAbs -ne $HostRepoPath))
    if ($doRewrite) {
        $rewritten = Repair-CwdPaths -Lines $lines -FromPath $worktreeAbs -ToPath $HostRepoPath
        $diff = 0
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -ne $rewritten[$i]) { $diff++ }
        }
        $result.cwd_rewrites = $diff
    }

    if (-not $DoApply) {
        $result.status = "dry-run"
        Write-JsonOrText -Object $result -Text @"
[dry-run] Would capture session:
  source : $sourceJsonl
  dest   : $destJsonl
  cwd     rewrites: $($result.cwd_rewrites) line(s) ($worktreeAbs -> $HostRepoPath)
  meta   : $sessionsJson
Pass -Apply to write.
"@
        return
    }

    # --- writes ---
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Set-Content -LiteralPath $destJsonl -Value $rewritten -Encoding utf8

    # Upsert sessions.json metadata.
    $records = @()
    if (Test-Path -LiteralPath $sessionsJson) {
        try { $records = @(Get-Content -LiteralPath $sessionsJson -Raw | ConvertFrom-Json) } catch { $records = @() }
    }
    $records = @($records | Where-Object { $_.session_id -ne $sid })
    $records += [pscustomobject]@{
        session_id      = $sid
        task_id         = $TaskId
        timestamp       = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        worktree_path   = $worktreeAbs
        host_repo_path  = $HostRepoPath
        host_jsonl_path = $destJsonl
        cwd_rewrites    = $result.cwd_rewrites
    }
    Set-Content -LiteralPath $sessionsJson -Value ($records | ConvertTo-Json -Depth 8) -Encoding utf8

    $result.status = "captured"
    Write-JsonOrText -Object $result -Text @"
Captured session $sid
  -> $destJsonl
  cwd rewrites: $($result.cwd_rewrites) line(s)
  metadata: $sessionsJson
  resume: claude --resume $sid
"@
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

switch ($Action) {
    "List"    { Invoke-List }
    "Resolve" { Invoke-Resolve }
    "Capture" { Invoke-Capture -DoApply:([bool]$Apply) }
    "Report"  { Invoke-Capture -DoApply:$false }
}
