# tasks_inbox_intake.ps1 - Process .gald3r/tasks/inbox/ and .gald3r/bugs/inbox/ (T1573)
# @subsystems: TASK_MANAGEMENT
<#
.SYNOPSIS
    Intake staged task/bug drafts from gitignored inbox folders into the live tracked state.

.DESCRIPTION
    Scans .gald3r/tasks/inbox/ and .gald3r/bugs/inbox/ for .md draft files, assigns the
    next sequential IDs, writes proper task/bug files with full frontmatter, appends rows
    to TASKS.md / BUGS.md, and commits as a single gald3r housekeeping commit.

    Run at the start of each g-go-go iteration (before the WPAC gate and claim loop) so
    new tasks/bugs created mid-run are never written to TASKS.md directly — which would
    dirty the tree outside the iteration's coordinator staging allowlist and hard-block
    the Housekeeping Commit Gate.

.PARAMETER ProjectRoot
    Root of the gald3r repo. Defaults to current directory.

.PARAMETER DryRun
    Print planned actions without writing anything.

.PARAMETER Quiet
    Suppress per-file output (still prints final summary).

.EXAMPLE
    .\tasks_inbox_intake.ps1
    .\tasks_inbox_intake.ps1 -DryRun
    .\tasks_inbox_intake.ps1 -ProjectRoot G:\gald3r_ecosystem\gald3r_templates -Quiet
#>
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$DryRun,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$galdPath    = Join-Path $ProjectRoot ".gald3r"
$taskInbox   = Join-Path $galdPath "tasks\inbox"
$bugInbox    = Join-Path $galdPath "bugs\inbox"
$tasksDir    = Join-Path $galdPath "tasks\open"
$bugsDir     = Join-Path $galdPath "bugs"
$tasksMd     = Join-Path $galdPath "TASKS.md"
$bugsMd      = Join-Path $galdPath "BUGS.md"

function Write-Msg($msg, $color = "Cyan") {
    if (-not $Quiet) { Write-Host $msg -ForegroundColor $color }
}

# ── ID helpers ────────────────────────────────────────────────────────────────

function Get-NextTaskId {
    $max = 0
    if (Test-Path $tasksMd) {
        $content = Get-Content $tasksMd -Raw -Encoding UTF8
        [regex]::Matches($content, '\[T(\d+)\]') | ForEach-Object {
            $n = [int]$_.Groups[1].Value
            if ($n -gt $max) { $max = $n }
        }
    }
    return $max + 1
}

function Get-NextBugId {
    $max = 0
    if (Test-Path $bugsMd) {
        $content = Get-Content $bugsMd -Raw -Encoding UTF8
        [regex]::Matches($content, 'BUG-(\d+)') | ForEach-Object {
            $n = [int]$_.Groups[1].Value
            if ($n -gt $max) { $max = $n }
        }
    }
    return $max + 1
}

# ── Parse inbox draft ─────────────────────────────────────────────────────────

function Read-Draft($filePath) {
    $raw = Get-Content $filePath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $raw) { $raw = "" }

    $title    = if ($raw -match '(?m)^title:\s*[''"]?(.+?)[''"]?\s*$') { $Matches[1].Trim() } else { (Split-Path $filePath -Leaf) -replace '\.md$','' -replace '[-_]',' ' }
    $priority = if ($raw -match '(?m)^priority:\s*(\w+)') { $Matches[1].Trim() } else { "medium" }
    $type     = if ($raw -match '(?m)^type:\s*(\w+)') { $Matches[1].Trim() } else { "feature" }
    $subsys   = if ($raw -match '(?m)^subsystems:\s*(.+)') { $Matches[1].Trim() } else { "[]" }
    $notes    = if ($raw -match '(?ms)^##\s+.+') { $raw -replace '(?ms)^---.*?---\s*',''.Trim() } else { "" }

    return [PSCustomObject]@{
        Title    = $title
        Priority = $priority
        Type     = $type
        Subsys   = $subsys
        Notes    = $notes
    }
}

# ── Process task inbox ────────────────────────────────────────────────────────

$stagedPaths  = [System.Collections.Generic.List[string]]::new()
$tasksIngested = 0
$bugsIngested  = 0
$today = Get-Date -Format "yyyy-MM-dd"

if (Test-Path $taskInbox) {
    $drafts = @(Get-ChildItem $taskInbox -Filter "*.md" -ErrorAction SilentlyContinue | Sort-Object Name)
    foreach ($draft in $drafts) {
        $d    = Read-Draft $draft.FullName
        $id   = Get-NextTaskId
        $slug = ($d.Title -replace '[^a-zA-Z0-9 ]','') -replace '\s+','_' -replace '_+','_'
        if ($slug.Length -gt 50) { $slug = $slug.Substring(0,50).TrimEnd('_') }
        $slug = $slug.ToLower()
        $filename = "task${id}_${slug}.md"
        $destPath = Join-Path $tasksDir $filename

        $shortTitle = if ($d.Title.Length -gt 65) { $d.Title.Substring(0,62) + "..." } else { $d.Title }

        $taskBody = @"
---
id: T$id
title: "$($d.Title)"
status: pending
priority: $($d.Priority)
type: $($d.Type)
subsystems: $($d.Subsys)
created: $today
source: inbox_intake
---

## Requirements

$($d.Notes)

## Status History

| Timestamp | From | To | Agent | Message |
|-----------|------|----|-------|---------|
| $today | — | pending | hot_inbox_intake.ps1 | Ingested from tasks/inbox/$($draft.Name) |
"@

        $tasksRow = "| [pending] | [T$id]($("tasks/open/$filename")) | $shortTitle | $($d.Priority) | $($d.Type) |"

        if ($DryRun) {
            Write-Msg "  [DRY-RUN] Would create: $destPath" "DarkGray"
            Write-Msg "  [DRY-RUN] Would append TASKS.md: $tasksRow" "DarkGray"
        } else {
            New-Item -ItemType Directory -Path $tasksDir -Force | Out-Null
            Set-Content -Path $destPath -Value $taskBody.TrimEnd() -Encoding UTF8
            Write-Msg "  CREATED: $destPath" "Green"

            # Append row to TASKS.md — find the last [pending] row and insert after it
            if (Test-Path $tasksMd) {
                $lines = (Get-Content $tasksMd -Encoding UTF8)
                # Update total count comment
                $lines = $lines -replace '(?<=Total: )\d+(?= tasks)', { [int]$_.Value + 1 }
                # Find last pending row index and insert after
                $lastPendingIdx = -1
                for ($i = $lines.Count - 1; $i -ge 0; $i--) {
                    if ($lines[$i] -match '^\| \[pending\]|\[📋\]') { $lastPendingIdx = $i; break }
                }
                if ($lastPendingIdx -ge 0) {
                    $newLines = [System.Collections.Generic.List[string]]($lines)
                    $newLines.Insert($lastPendingIdx + 1, $tasksRow)
                    Set-Content -Path $tasksMd -Value ($newLines -join "`n") -Encoding UTF8 -NoNewline
                } else {
                    Add-Content -Path $tasksMd -Value $tasksRow -Encoding UTF8
                }
            }

            Remove-Item $draft.FullName -Force
            $stagedPaths.Add($destPath)
            $stagedPaths.Add($tasksMd)
        }
        $tasksIngested++
    }
}

# ── Process bug inbox ─────────────────────────────────────────────────────────

if (Test-Path $bugInbox) {
    $drafts = @(Get-ChildItem $bugInbox -Filter "*.md" -ErrorAction SilentlyContinue | Sort-Object Name)
    foreach ($draft in $drafts) {
        $d    = Read-Draft $draft.FullName
        $id   = Get-NextBugId
        $bugId = "BUG-$id"
        $slug = ($d.Title -replace '[^a-zA-Z0-9 ]','') -replace '\s+','_' -replace '_+','_'
        if ($slug.Length -gt 50) { $slug = $slug.Substring(0,50).TrimEnd('_') }
        $slug = $slug.ToLower()
        $filename = "bug${id}_${slug}.md"
        $destPath = Join-Path $bugsDir $filename

        $shortTitle = if ($d.Title.Length -gt 65) { $d.Title.Substring(0,62) + "..." } else { $d.Title }

        $bugBody = @"
---
id: $bugId
title: "$($d.Title)"
severity: $($d.Priority)
status: open
subsystems: $($d.Subsys)
reported: $today
source: inbox_intake
---

## Description

$($d.Notes)

## Status History

| Timestamp | From | To | Agent | Message |
|-----------|------|----|-------|---------|
| $today | — | open | hot_inbox_intake.ps1 | Ingested from bugs/inbox/$($draft.Name) |
"@

        $bugsRow = "| [$bugId](bugs/$filename) | $shortTitle | $($d.Priority) | open | $($d.Subsys) | $today |"

        if ($DryRun) {
            Write-Msg "  [DRY-RUN] Would create: $destPath" "DarkGray"
            Write-Msg "  [DRY-RUN] Would append BUGS.md: $bugsRow" "DarkGray"
        } else {
            New-Item -ItemType Directory -Path $bugsDir -Force | Out-Null
            Set-Content -Path $destPath -Value $bugBody.TrimEnd() -Encoding UTF8
            Write-Msg "  CREATED: $destPath" "Green"

            if (Test-Path $bugsMd) {
                Add-Content -Path $bugsMd -Value $bugsRow -Encoding UTF8
            }

            Remove-Item $draft.FullName -Force
            $stagedPaths.Add($destPath)
            $stagedPaths.Add($bugsMd)
        }
        $bugsIngested++
    }
}

# ── Summary and commit ────────────────────────────────────────────────────────

$total = $tasksIngested + $bugsIngested

if ($total -eq 0) {
    Write-Msg "Inbox empty — nothing to intake." "DarkGray"
    exit 0
}

Write-Msg "Intake complete: $tasksIngested task(s), $bugsIngested bug(s)" "Green"

if ($DryRun) {
    Write-Msg "DRY-RUN: no files written, no commit." "Magenta"
    exit 0
}

# Commit — stage explicit paths only, never git add .
$uniquePaths = @($stagedPaths | Select-Object -Unique)
Push-Location $ProjectRoot
try {
    foreach ($p in $uniquePaths) {
        $rel = $p.Replace($ProjectRoot, '').TrimStart('\', '/')
        if (Test-Path $rel) { git add -- $rel 2>$null }
    }
    $staged = (git diff --cached --name-only 2>$null)
    if ($staged) {
        $msg = "chore(gald3r): intake $tasksIngested task(s) / $bugsIngested bug(s) from inbox"
        git commit -m $msg 2>&1 | Out-Null
        Write-Msg "Committed: $msg ($(git rev-parse --short HEAD))" "Green"
    } else {
        Write-Msg "Nothing staged — files may already be current." "DarkGray"
    }
} finally {
    Pop-Location
}
