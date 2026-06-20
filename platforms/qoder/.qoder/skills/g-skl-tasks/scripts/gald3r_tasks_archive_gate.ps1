<#
.SYNOPSIS
    TASKS.md line-count archive gate. Checks whether TASKS.md has grown beyond the
    configured threshold and, when -Apply is passed, automatically archives all
    terminal ([check] / [X]) tasks to .gald3r/archive/.

.DESCRIPTION
    Exit codes:
        0  -- line count is below WarnAt (clean)
        1  -- line count is in the warning zone [WarnAt, Threshold)
        2  -- line count meets or exceeds Threshold (gate fires)
        3  -- error (bad paths, write failure, etc.)

    With -Apply the archive operation runs when exit would be 2.
    With -CheckOnly (default) the script never mutates files.

.PARAMETER CheckOnly
    Inspect and report only. Never writes. (default behavior when neither flag is passed)

.PARAMETER Apply
    When threshold is breached, run the full archive operation.

.PARAMETER Threshold
    Line count at which the gate fires. Default: 1200.

.PARAMETER WarnAt
    Line count at which a warning is emitted (but no auto-archive). Default: 900.

.PARAMETER ProjectRoot
    Root of the gald3r project (the folder that contains .gald3r/). Default: current directory.

.PARAMETER Json
    Emit a single-line JSON object to stdout instead of human-readable output.

.EXAMPLE
    # Check only (useful from session-start hook)
    powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/g-skl-tasks/scripts/gald3r_tasks_archive_gate.ps1 -CheckOnly

.EXAMPLE
    # Auto-archive when over 2000 lines
    powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/g-skl-tasks/scripts/gald3r_tasks_archive_gate.ps1 -Apply

.EXAMPLE
    # Lower threshold for testing
    powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/g-skl-tasks/scripts/gald3r_tasks_archive_gate.ps1 -Apply -Threshold 800
#>
param(
    [switch]$CheckOnly,
    [switch]$Apply,
    [int]$Threshold = 1200,
    [int]$WarnAt = 900,
    [string]$ProjectRoot = ".",
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

function Write-Out {
    param([string]$Msg, [string]$Color = "White")
    if (-not $Json) { Write-Host $Msg -ForegroundColor $Color }
}

function Emit-Json {
    param([hashtable]$Data)
    if ($Json) {
        $Data | ConvertTo-Json -Compress | Write-Host
    }
}

# --------------------------------------------------------------------------
# Resolve paths
# --------------------------------------------------------------------------

$root = Resolve-Path $ProjectRoot -ErrorAction SilentlyContinue
if (-not $root) {
    Write-Error "ProjectRoot not found: $ProjectRoot"
    exit 3
}
$root = $root.Path

$gald3rDir   = Join-Path $root ".gald3r"
$tasksFile   = Join-Path $gald3rDir "TASKS.md"
$tasksDir    = Join-Path $gald3rDir "tasks"
$archiveRoot = Join-Path $gald3rDir "archive"

if (-not (Test-Path $tasksFile)) {
    Write-Error "TASKS.md not found at: $tasksFile"
    exit 3
}

# --------------------------------------------------------------------------
# Count lines
# --------------------------------------------------------------------------

$allLines  = [System.IO.File]::ReadAllLines($tasksFile, [System.Text.Encoding]::UTF8)
$lineCount = $allLines.Count

Write-Out ""
Write-Out "======================================================" Cyan
Write-Out "  TASKS.md Archive Gate" Cyan
Write-Out "======================================================" Cyan
Write-Out "  File       : $tasksFile"
Write-Out "  Line count : $lineCount  (threshold=$Threshold, warn>=$WarnAt)"

# Determine gate state
$gateState = "clean"
$exitCode  = 0
if ($lineCount -ge $Threshold) {
    $gateState = "breached"
    $exitCode  = 2
    Write-Out ""
    Write-Out "  [!] THRESHOLD BREACHED -- $lineCount lines >= $Threshold" Yellow
} elseif ($lineCount -ge $WarnAt) {
    $gateState = "warning"
    $exitCode  = 1
    Write-Out ""
    Write-Out "  [!] WARNING ZONE -- $lineCount lines >= $WarnAt (threshold: $Threshold)" Yellow
} else {
    Write-Out "  [OK] Clean -- $lineCount lines (threshold: $Threshold)" Green
}

# --------------------------------------------------------------------------
# Not breached -- report and exit
# --------------------------------------------------------------------------

if ($gateState -ne "breached") {
    Emit-Json @{
        gate_state = $gateState
        line_count = $lineCount
        threshold  = $Threshold
        warn_at    = $WarnAt
        action     = "none"
    }
    Write-Out "======================================================" Cyan
    exit $exitCode
}

# --------------------------------------------------------------------------
# Breached and CheckOnly
# --------------------------------------------------------------------------

if (-not $Apply) {
    Write-Out ""
    Write-Out "  Run with -Apply to archive terminal tasks automatically." Gray
    Write-Out "  Command: .claude/skills/g-skl-tasks/scripts/gald3r_tasks_archive_gate.ps1 -Apply" Gray
    Emit-Json @{
        gate_state = $gateState
        line_count = $lineCount
        threshold  = $Threshold
        warn_at    = $WarnAt
        action     = "check_only"
    }
    Write-Out "======================================================" Cyan
    exit 2
}

# ==========================================================================
# APPLY MODE -- archive terminal tasks
# ==========================================================================

Write-Out ""
Write-Out "  Applying archive operation..." Yellow

# --------------------------------------------------------------------------
# Identify terminal rows using UTF-32 codepoints for emoji matching
# --------------------------------------------------------------------------

$checkChar  = [char]::ConvertFromUtf32(0x2705)  # [check]
$crossChar  = [char]::ConvertFromUtf32(0x274C)  # [X]

$terminalRows = @()
foreach ($line in $allLines) {
    if ($line.Contains("[" + $checkChar + "]") -or $line.Contains("[" + $crossChar + "]")) {
        $terminalRows += $line
    }
}

$terminalCount = $terminalRows.Count
Write-Out "  Terminal rows found: $terminalCount"

if ($terminalCount -eq 0) {
    Write-Out "  [!] No terminal tasks found to archive. File is large but all tasks are active." Yellow
    Write-Out "  Consider reviewing non-terminal content for cleanup." Gray
    Emit-Json @{
        gate_state     = $gateState
        line_count     = $lineCount
        threshold      = $Threshold
        action         = "no_terminal_tasks"
        terminal_count = 0
    }
    Write-Out "======================================================" Cyan
    exit 0
}

# --------------------------------------------------------------------------
# Extract task metadata from rows
# --------------------------------------------------------------------------
# Supported row formats:
#   Table: | [check] | [123](tasks/task123_slug.md) | Title | type | deps |
#   Bullet: - [check] **Task 123** -- Title
#   Bullet with dash ID: - [check] **Task 123-1** -- Title

$archivedTasks = @()

foreach ($row in $terminalRows) {
    $taskId    = $null
    $taskTitle = $null
    $taskFile  = $null
    $statusVal = if ($row.Contains("[" + $checkChar + "]")) { "completed" } else { "failed" }

    # Table format: | [...] | [ID](tasks/taskFILE.md) | Title | ...
    if ($row -match '\|\s*\[[^\]]+\]\s*\|\s*\[([^\]]+)\]\((tasks/[^\)]+)\)\s*\|\s*([^\|]+)\|') {
        $taskId    = $Matches[1].Trim()
        $taskFile  = $Matches[2].Trim()
        $taskTitle = $Matches[3].Trim()
    }
    # Bullet format: **Task 123** or **Task 123-1**
    elseif ($row -match '\*\*Task\s+([\d][\d\-]*)\*\*\s*[-]+\s*(.+)') {
        $taskId    = "T" + $Matches[1].Trim()
        $taskTitle = $Matches[2].Trim()
        $filePattern = "task" + ($Matches[1] -replace '-', '') + "_*.md"
        $found = Get-ChildItem $tasksDir -Filter $filePattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $taskFile = "tasks/" + $found.Name }
    }

    if ($taskId) {
        $archivedTasks += [PSCustomObject]@{
            RowText   = $row
            TaskId    = $taskId
            TaskTitle = $taskTitle
            TaskFile  = $taskFile
            Status    = $statusVal
        }
    }
}

Write-Out "  Parseable terminal tasks: $($archivedTasks.Count)"

# --------------------------------------------------------------------------
# Determine archive bucket
# --------------------------------------------------------------------------

$archiveTasksDir = Join-Path $archiveRoot "tasks"
if (-not (Test-Path $archiveTasksDir)) { New-Item -ItemType Directory -Path $archiveTasksDir -Force | Out-Null }

# Find existing buckets to determine next ordinal start
$existingBuckets = Get-ChildItem $archiveRoot -Filter "archive_tasks_*.md" -ErrorAction SilentlyContinue
$nextOrdinalStart = 0
foreach ($bucket in $existingBuckets) {
    if ($bucket.Name -match 'archive_tasks_(\d+)_(\d+)\.md') {
        $bucketEnd = [int]$Matches[2]
        $candidateStart = $bucketEnd + 1
        if ($candidateStart -gt $nextOrdinalStart) { $nextOrdinalStart = $candidateStart }
    }
}

$bucketSize      = 1000
$bucketIndex     = [math]::Floor($nextOrdinalStart / $bucketSize)
$bucketStart     = $bucketIndex * $bucketSize
$bucketEnd       = $bucketStart + $bucketSize - 1
$bucketName      = "tasks_{0:D4}_{1:D4}" -f $bucketStart, $bucketEnd
$bucketDir       = Join-Path $archiveTasksDir $bucketName
$bucketStartFmt  = "{0:D4}" -f $bucketStart
$bucketEndFmt    = "{0:D4}" -f $bucketEnd
$bucketFileName  = "archive_tasks_" + $bucketStartFmt + "_" + $bucketEndFmt + ".md"
$bucketIndexFile = Join-Path $archiveRoot $bucketFileName

if (-not (Test-Path $bucketDir)) { New-Item -ItemType Directory -Path $bucketDir -Force | Out-Null }

$today = (Get-Date -Format "yyyy-MM-dd")

# --------------------------------------------------------------------------
# Move task files
# --------------------------------------------------------------------------

$movedFiles = @()
$ordinal    = $nextOrdinalStart

foreach ($task in $archivedTasks) {
    if ($task.TaskFile) {
        $srcFile = Join-Path $gald3rDir $task.TaskFile
        if (Test-Path $srcFile) {
            $dstFile = Join-Path $bucketDir (Split-Path $srcFile -Leaf)
            Move-Item $srcFile $dstFile -Force
            $movedFiles += $srcFile
            Write-Out "    Moved: $($task.TaskId) -> $bucketName/" Gray
        }
    }
    $task | Add-Member -NotePropertyName Ordinal -NotePropertyValue $ordinal -Force
    $ordinal++
}

Write-Out "  Files moved: $($movedFiles.Count)"

# --------------------------------------------------------------------------
# Build archive index rows
# --------------------------------------------------------------------------

$indexRows = $archivedTasks | ForEach-Object {
    "| $($_.Ordinal) | $($_.TaskId) | [$($_.Status)] | $($_.TaskTitle) | $($_.TaskFile) | $today |"
}

# --------------------------------------------------------------------------
# Write / append archive index file
# --------------------------------------------------------------------------

if (Test-Path $bucketIndexFile) {
    $existingIndex = [System.IO.File]::ReadAllText($bucketIndexFile, [System.Text.Encoding]::UTF8)
    $appendBlock   = ($indexRows -join "`n")
    [System.IO.File]::WriteAllText($bucketIndexFile, $existingIndex.TrimEnd() + "`n" + $appendBlock + "`n", [System.Text.Encoding]::UTF8)
    Write-Out "  Archive index updated: $bucketIndexFile" Green
} else {
    $bucketTitleLine = "# Archive: Tasks " + $bucketStartFmt + "-" + $bucketEndFmt
    $headerBlock = $bucketTitleLine + "`n`n" +
        "Archive bucket: $bucketName`n" +
        "Archived: $today`n" +
        "Total entries: $($archivedTasks.Count)`n" +
        "Source: .gald3r/TASKS.md -- <gald3r_source> controller`n" +
        "Authorized by: gald3r_tasks_archive_gate.ps1 -Apply (auto-gate, $today)`n`n" +
        "---`n`n" +
        "## Index`n`n" +
        "| Ordinal | Task ID | Status | Title | Original File | Archived |`n" +
        "|---------|---------|--------|-------|---------------|----------|"

    $footerPointer = "*Archive pointers in TASKS.md reference this file.*"
    $footerFiles   = "*Individual task files preserved in " + $bucketName + "/ bucket.*"
    $fullContent   = $headerBlock + "`n" + ($indexRows -join "`n") + "`n`n---`n`n" + $footerPointer + "`n" + $footerFiles + "`n"
    [System.IO.File]::WriteAllText($bucketIndexFile, $fullContent, [System.Text.Encoding]::UTF8)
    Write-Out "  Archive index created: $bucketIndexFile" Green
}

# --------------------------------------------------------------------------
# Rewrite TASKS.md without terminal rows
# --------------------------------------------------------------------------

$terminalRowSet = [System.Collections.Generic.HashSet[string]]($terminalRows)
$newLines       = [System.Collections.Generic.List[string]]::new()
$skipped        = 0

foreach ($line in $allLines) {
    if ($terminalRowSet.Contains($line)) {
        $skipped++
    } else {
        $newLines.Add($line)
    }
}

# Build archive pointer row for the new bucket
$archivePointerRow = "| [" + $bucketFileName + "](archive/" + $bucketFileName + ") | " + $nextOrdinalStart + "-" + ($ordinal-1) + " | Auto-archived $today | $today | $($archivedTasks.Count) |"

# Find or append Archive Pointers section
$hasArchiveSection = $false
for ($i = 0; $i -lt $newLines.Count; $i++) {
    if ($newLines[$i] -match '^## Archive Pointers') {
        $hasArchiveSection = $true
        # Find the line just before the footer note and insert the new row there
        for ($j = $i + 1; $j -lt $newLines.Count; $j++) {
            if ($newLines[$j] -match '^\*Task files at') {
                $newLines.Insert($j, $archivePointerRow)
                break
            }
        }
        break
    }
}

if (-not $hasArchiveSection) {
    $newLines.Add("")
    $newLines.Add("---")
    $newLines.Add("")
    $newLines.Add("## Archive Pointers")
    $newLines.Add("")
    $newLines.Add("*Completed and cancelled task history has been moved to .gald3r/archive/. Task files are preserved; only active indexes and in-progress tasks remain above.*")
    $newLines.Add("")
    $newLines.Add("| Archive Index | Ordinal Range | Task IDs | Archived | Count |")
    $newLines.Add("|--------------|---------------|----------|----------|-------|")
    $newLines.Add($archivePointerRow)
    $newLines.Add("")
    $newLines.Add("*Task files at: .gald3r/archive/tasks/" + $bucketName + "/*")
}

$newContent = ($newLines -join "`n") + "`n"
[System.IO.File]::WriteAllText($tasksFile, $newContent, [System.Text.Encoding]::UTF8)

# --------------------------------------------------------------------------
# Final report
# --------------------------------------------------------------------------

$newLineCount = ([System.IO.File]::ReadAllLines($tasksFile, [System.Text.Encoding]::UTF8)).Count

Write-Out ""
Write-Out "  [OK] Archive complete!" Green
Write-Out "  Terminal rows removed : $skipped"
Write-Out "  Files moved           : $($movedFiles.Count)"
Write-Out "  TASKS.md before       : $lineCount lines"
Write-Out "  TASKS.md after        : $newLineCount lines"
Write-Out "  Archive index         : $bucketIndexFile"
Write-Out "  Archive files bucket  : $bucketDir"

Emit-Json @{
    gate_state            = "archived"
    line_count_before     = $lineCount
    line_count_after      = $newLineCount
    threshold             = $Threshold
    terminal_rows_removed = $skipped
    files_moved           = $movedFiles.Count
    archive_index         = $bucketIndexFile
    archive_bucket        = $bucketDir
    action                = "archived"
}

Write-Out "======================================================" Cyan
exit 0
