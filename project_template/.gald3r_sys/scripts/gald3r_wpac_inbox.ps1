# gald3r_wpac_inbox.ps1 - WPAC inbox message-folder migration + archive (T428)
# @subsystems: WORKSPACE_COORDINATION
#
# Upgrades the WPAC cross-project inbox from a single flat INBOX.md into a
# lightweight index table backed by individual message files, plus an archive
# mechanism that keeps the active index lean.
#
# Layout (anchored on the canonical linking/ directory the hook already reads):
#   .gald3r/linking/INBOX.md                 <- lightweight index table
#   .gald3r/linking/messages/                <- one file per message
#       msg_{id}_{type}_{source}.md
#   .gald3r/linking/messages/archive/        <- archived [DONE] message files
#       archive_index.md                     <- append-only archive index table
#
# Operations:
#   -Migrate   Idempotent: extract inline messages from a legacy flat INBOX.md
#              into individual message files and rewrite INBOX.md as the index.
#              Safe to re-run (second run is a no-op when already migrated).
#   -Archive   Move [DONE] messages older than -ThresholdDays (default 30) from
#              the active index into messages/archive/ and prune their index rows.
#
# Notes:
#   - Pure ASCII source (BUG-127/132). The em-dash (U+2014) that real inbox
#     headings use is referenced via [char]0x2014, never embedded literally.
#   - Backward-compat: if messages/ is absent it is created silently; a legacy
#     flat INBOX.md (inline bodies) is recognized and migrated without data loss.
#   - PS 5.1 and PS 7 compatible.

[CmdletBinding(DefaultParameterSetName = 'Migrate')]
param(
    [string]$ProjectRoot = (Get-Location).Path,

    [Parameter(ParameterSetName = 'Migrate')]
    [switch]$Migrate,

    [Parameter(ParameterSetName = 'Archive')]
    [switch]$Archive,

    [Parameter(ParameterSetName = 'Archive')]
    [int]$ThresholdDays = 30,

    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

# U+2014 EM DASH - kept out of the source bytes for ASCII safety.
$EmDash = [char]0x2014

$linkingDir = Join-Path $ProjectRoot ".gald3r\linking"
$inboxPath  = Join-Path $linkingDir "INBOX.md"
$msgDir     = Join-Path $linkingDir "messages"
$archiveDir = Join-Path $msgDir "archive"
$archiveIdx = Join-Path $archiveDir "archive_index.md"

function Write-Info {
    param([string]$Message)
    if (-not $Quiet) { Write-Output $Message }
}

# Inbox files are DATA: they may legitimately contain Unicode (em-dashes,
# message bodies). Write them as UTF-8 WITHOUT a BOM on both PS 5.1 and PS 7
# (PS 5.1's `-Encoding utf8` emits a BOM, so write bytes directly). This is the
# only correct encoding here; `ascii` would silently mangle Unicode to '?'.
function Set-Utf8NoBom {
    param([string]$Path, [string[]]$Lines)
    $text = ($Lines -join "`n") + "`n"
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $text, $enc)
}

function Add-Utf8NoBom {
    param([string]$Path, [string[]]$Lines)
    $existing = ""
    if (Test-Path $Path) { $existing = [System.IO.File]::ReadAllText($Path) }
    if ($existing.Length -gt 0 -and -not $existing.EndsWith("`n")) { $existing += "`n" }
    $text = $existing + (($Lines -join "`n") + "`n")
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $text, $enc)
}

# Always read inbox/message files as UTF-8 (BOM-tolerant). PS 5.1's default
# Get-Content uses the ANSI code page and would mis-decode em-dashes; .NET's
# UTF8Encoding decodes both BOM and no-BOM correctly on 5.1 and 7.
function Read-Utf8Text {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return "" }
    return [System.IO.File]::ReadAllText($Path, (New-Object System.Text.UTF8Encoding($false)))
}

function Read-Utf8Lines {
    param([string]$Path)
    $text = Read-Utf8Text -Path $Path
    if (-not $text) { return @() }
    return ,($text -split "`r?`n")
}

function Initialize-MessageDirs {
    # Backward-compat: silently create messages/ (+ archive/) when absent.
    if (-not (Test-Path $msgDir))     { New-Item -ItemType Directory -Path $msgDir -Force | Out-Null }
    if (-not (Test-Path $archiveDir)) { New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null }
}

function Get-ProjectName {
    # Best-effort project name from .identity; falls back to the folder name.
    $identityFile = Join-Path $ProjectRoot ".gald3r\.identity"
    if (Test-Path $identityFile) {
        foreach ($line in (Get-Content $identityFile -ErrorAction SilentlyContinue)) {
            if ($line -match "^project_name=(.+)$") { return $Matches[1].Trim() }
        }
    }
    return (Split-Path $ProjectRoot -Leaf)
}

function ConvertTo-Slug {
    param([string]$Text)
    if (-not $Text) { return "unknown" }
    $s = $Text.ToLower() -replace "[^a-z0-9]+", "_"
    $s = $s.Trim("_")
    if (-not $s) { return "unknown" }
    if ($s.Length -gt 40) { $s = $s.Substring(0, 40).Trim("_") }
    return $s
}

# Canonical message file name: msg_{id}_{type}_{source}.md (T428 AC#2).
# The id-slug has any leading "msg" token stripped so a synthetic id like
# "msg-20260416-001" does not produce a "msg_msg_..." double prefix.
function Get-MessageFileName {
    param($Msg)
    $idSlug = ConvertTo-Slug $Msg.Id
    $idSlug = $idSlug -replace "^msg_*", ""
    if (-not $idSlug) { $idSlug = "0" }
    $typeLow = $Msg.Kind.ToLower()
    $srcSlug = ConvertTo-Slug $Msg.Source
    return ("msg_{0}_{1}_{2}.md" -f $idSlug, $typeLow, $srcSlug)
}

function Truncate-Subject {
    param([string]$Text, [int]$Max = 48)
    if (-not $Text) { return "(no subject)" }
    $t = $Text -replace "\s+", " "
    $t = $t.Trim()
    if ($t.Length -le $Max) { return $t }
    return ($t.Substring(0, $Max - 3) + "...")
}

function Format-Age {
    param([datetime]$Then)
    $delta = (Get-Date) - $Then
    if ($delta.TotalHours -lt 24) { return ("{0}h" -f [int]$delta.TotalHours) }
    return ("{0}d" -f [int]$delta.TotalDays)
}

function Test-AlreadyMigrated {
    # The index format carries a stable marker comment on line ~ top.
    if (-not (Test-Path $inboxPath)) { return $false }
    $raw = Read-Utf8Text -Path $inboxPath
    if (-not $raw) { return $false }
    return ($raw -match "<!--\s*WPAC-INDEX-V1\s*-->")
}

# -----------------------------------------------------------------------------
# Parse a legacy flat INBOX.md into message objects.
# Recognizes both heading styles that the existing hook understands:
#   "## [OPEN|DONE|CONFLICT] <id> - from: <proj> - YYYY-MM-DD"  (per-item)
#   "## [STATUS] <free subject> - YYYY-MM-DD"                   (flat-body item)
# Section headers from the linking/INBOX.md template
#   ("## [CONFLICT] - Items..." etc.) are treated as empty section scaffolding
#   and ignored (no body, no date) so a fresh template migrates to an empty index.
# -----------------------------------------------------------------------------
function Get-LegacyMessages {
    param([string[]]$Lines)

    $messages = New-Object System.Collections.Generic.List[Object]
    $current = $null

    $sectionHeaders = @(
        "[CONFLICT] $EmDash Items That Block Work",
        "[REQUEST] $EmDash Incoming Asks From Children",
        "[BROADCAST] $EmDash Orders From Parent",
        "[SYNC] $EmDash Peer Contract Updates From Siblings",
        "[RESOLVED] $EmDash Archive"
    )

    function Close-Current {
        param($Cur, $List)
        if ($null -ne $Cur) { $List.Add($Cur) | Out-Null }
    }

    foreach ($rawLine in $Lines) {
        $line = $rawLine

        # Status heading of any of the recognized kinds.
        if ($line -match "^##\s+\[(OPEN|DONE|CONFLICT|RESOLVED)\]\s*(.*)$") {
            $status = $Matches[1].ToUpper()
            $rest   = $Matches[2].Trim()

            # Skip pure template section scaffolding lines (no real message body).
            $isSection = $false
            foreach ($h in $sectionHeaders) {
                if ("[$status] $rest" -eq $h) { $isSection = $true; break }
            }
            if ($isSection -or $rest -eq "" -or $rest -match "^$EmDash") {
                Close-Current $current $messages; $current = $null
                continue
            }

            Close-Current $current $messages

            # Try the structured per-item form first:
            #   <id> - from:/From: <proj> - YYYY-MM-DD
            $id = ""; $src = ""; $subject = ""; $date = $null
            $dashClass = "[$EmDash\-]"
            if ($rest -match "^(\S+)\s*$dashClass+\s*(?:from|From):\s*(.+?)\s*$dashClass+\s*(\d{4}-\d{2}-\d{2})\s*$") {
                $id = $Matches[1].Trim()
                $src = $Matches[2].Trim()
                $date = [datetime]::ParseExact($Matches[3], "yyyy-MM-dd", $null)
            }
            elseif ($rest -match "^(.*?)\s*$dashClass+\s*(\d{4}-\d{2}-\d{2})\s*$") {
                # Flat-body form: free subject then a trailing date.
                $subject = $Matches[1].Trim()
                $date = [datetime]::ParseExact($Matches[2], "yyyy-MM-dd", $null)
            }
            else {
                $subject = $rest
            }

            $kind = "INFO"
            if     ($rest -match "(?i)\bORDER\b" -or $id -match "(?i)^ORD")   { $kind = "ORDER" }
            elseif ($rest -match "(?i)\bREQUEST\b" -or $id -match "(?i)^REQ") { $kind = "REQUEST" }
            elseif ($rest -match "(?i)\bBROADCAST\b" -or $id -match "(?i)^BCAST") { $kind = "BROADCAST" }
            elseif ($rest -match "(?i)\bSYNC\b" -or $id -match "(?i)^SYNC")   { $kind = "SYNC" }
            elseif ($id -match "(?i)^INFO") { $kind = "INFO" }
            if ($status -eq "CONFLICT") { $kind = "CONFLICT" }

            $current = [PSCustomObject]@{
                Id        = $id
                Status    = $status
                Kind      = $kind
                Source    = $src
                Subject   = $subject
                Date      = $date
                HeaderRaw = $rest
                Body      = New-Object System.Collections.Generic.List[String]
            }
            continue
        }

        if ($null -ne $current) {
            # Pull a Subject/From/Source from the body if not already captured.
            if (-not $current.Subject -and $line -match "^\*\*Subject:\*\*\s*(.+)$") {
                $current.Subject = $Matches[1].Trim()
            }
            if (-not $current.Source -and $line -match "^\*\*(?:Source|From)\*\*:\s*(.+)$") {
                $current.Source = ($Matches[1].Trim() -replace "\s*\(.*$", "").Trim()
            }
            $current.Body.Add($line) | Out-Null
        }
    }
    Close-Current $current $messages

    # Stable synthetic IDs + dates for items that lacked them.
    $seq = 0
    foreach ($m in $messages) {
        $seq++
        if (-not $m.Date) { $m.Date = Get-Date }
        if (-not $m.Source) { $m.Source = "unknown" }
        if (-not $m.Id) {
            $m.Id = ("msg-{0}-{1:000}" -f $m.Date.ToString("yyyyMMdd"), $seq)
        }
    }
    return ,$messages
}

function Write-MessageFile {
    param($Msg)
    $statusLower = $Msg.Status.ToLower()
    $fileName = Get-MessageFileName -Msg $Msg
    $filePath = Join-Path $msgDir $fileName

    # Idempotency: never clobber an already-migrated message file.
    if (Test-Path $filePath) { return $fileName }

    $subj = if ($Msg.Subject) { $Msg.Subject } elseif ($Msg.HeaderRaw) { $Msg.HeaderRaw } else { "(no subject)" }
    $createdAt = $Msg.Date.ToString("yyyy-MM-dd")
    $actionedAt = if ($Msg.Status -in @("DONE", "RESOLVED")) { $createdAt } else { "" }

    $fm = New-Object System.Collections.Generic.List[String]
    $fm.Add("---") | Out-Null
    $fm.Add("id: $($Msg.Id)") | Out-Null
    $fm.Add("type: $($Msg.Kind)") | Out-Null
    $fm.Add("source_project: $($Msg.Source)") | Out-Null
    $fm.Add("subject: '$($subj -replace "'", "''")'") | Out-Null
    $fm.Add("status: $statusLower") | Out-Null
    $fm.Add("created_at: '$createdAt'") | Out-Null
    $fm.Add("actioned_at: '$actionedAt'") | Out-Null
    $fm.Add("---") | Out-Null
    $fm.Add("") | Out-Null
    $fm.Add("# [$($Msg.Kind)] $subj") | Out-Null
    $fm.Add("") | Out-Null
    if ($Msg.Source -and $Msg.Source -ne "unknown") {
        $fm.Add("**Source**: $($Msg.Source)") | Out-Null
        $fm.Add("") | Out-Null
    }
    foreach ($b in $Msg.Body) { $fm.Add($b) | Out-Null }

    Set-Utf8NoBom -Path $filePath -Lines $fm
    return $fileName
}

function New-IndexLines {
    param([string]$ProjectName, $Messages)
    $lines = New-Object System.Collections.Generic.List[String]
    $lines.Add("<!-- WPAC-INDEX-V1 -->") | Out-Null
    $lines.Add("# INBOX $EmDash $ProjectName") | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("> WPAC cross-project coordination inbox (index). Managed by g-skl-wpac-read.") | Out-Null
    $lines.Add("> Message bodies live under messages/. Session-start hook checks this file.") | Out-Null
    $lines.Add("> CONFLICT rows block session work until resolved via @g-wpac-read.") | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("| Status | ID | Type | Source | Subject | Age | File |") | Out-Null
    $lines.Add("|---|---|---|---|---|---|---|") | Out-Null
    foreach ($m in ($Messages | Sort-Object -Property Date)) {
        $statusCell = "[$($m.Status)]"
        $subjSrc = if ($m.Subject) { $m.Subject } else { $m.HeaderRaw }
        $subjCell = Truncate-Subject $subjSrc
        $age = Format-Age -Then $m.Date
        $fileName = Get-MessageFileName -Msg $m
        $link = "[$fileName](messages/$fileName)"
        $lines.Add("| $statusCell | $($m.Id) | $($m.Kind) | $($m.Source) | $subjCell | $age | $link |") | Out-Null
    }
    $lines.Add("") | Out-Null
    return ,$lines
}

# -----------------------------------------------------------------------------
# Read the migrated index table into row objects.
# -----------------------------------------------------------------------------
function Get-IndexRows {
    param([string[]]$Lines)
    $rows = New-Object System.Collections.Generic.List[Object]
    foreach ($line in $Lines) {
        if ($line -notmatch "^\|") { continue }
        if ($line -match "^\|\s*Status\s*\|") { continue }          # header
        if ($line -match "^\|[\s\-:]+\|[\s\-:]+\|") { continue }    # separator
        $cells = ($line.Trim().Trim("|") -split "\|") | ForEach-Object { $_.Trim() }
        if ($cells.Count -lt 7) { continue }
        $statusRaw = $cells[0] -replace "[\[\]]", ""
        $fileCell = $cells[6]
        $fileName = ""
        if ($fileCell -match "\(messages/([^)]+)\)") { $fileName = $Matches[1] }
        elseif ($fileCell -match "\[([^\]]+)\]") { $fileName = $Matches[1] }
        $rows.Add([PSCustomObject]@{
            RawLine  = $line
            Status   = $statusRaw.ToUpper()
            Id       = $cells[1]
            Kind     = $cells[2]
            Source   = $cells[3]
            Subject  = $cells[4]
            Age      = $cells[5]
            FileName = $fileName
        }) | Out-Null
    }
    return ,$rows
}

function Invoke-Migrate {
    Initialize-MessageDirs

    if (-not (Test-Path $inboxPath)) {
        # No inbox yet: write an empty index so the layout is initialized.
        $idx = New-IndexLines -ProjectName (Get-ProjectName) -Messages @()
        Set-Utf8NoBom -Path $inboxPath -Lines $idx
        Write-Info "WPAC inbox: initialized empty index at .gald3r/linking/INBOX.md"
        return
    }

    if (Test-AlreadyMigrated) {
        Write-Info "WPAC inbox: already migrated (index format) - no-op"
        return
    }

    $rawLines = Read-Utf8Lines -Path $inboxPath
    if (-not $rawLines) { $rawLines = @() }

    $messages = Get-LegacyMessages -Lines $rawLines
    $migrated = 0
    foreach ($m in $messages) {
        Write-MessageFile -Msg $m | Out-Null
        $migrated++
    }

    $idx = New-IndexLines -ProjectName (Get-ProjectName) -Messages $messages
    Set-Utf8NoBom -Path $inboxPath -Lines $idx

    Write-Info ("WPAC inbox: migrated {0} message(s) to messages/; INBOX.md rewritten as index" -f $migrated)
}

function Invoke-Archive {
    Initialize-MessageDirs

    if (-not (Test-Path $inboxPath)) {
        Write-Info "WPAC inbox: nothing to archive (no INBOX.md)"
        return
    }
    if (-not (Test-AlreadyMigrated)) {
        # Archive only operates on the new index layout; migrate first.
        Invoke-Migrate
    }

    $rawLines = Read-Utf8Lines -Path $inboxPath
    if (-not $rawLines) { $rawLines = @() }
    $rows = Get-IndexRows -Lines $rawLines

    $cutoff = (Get-Date).Date.AddDays(-1 * $ThresholdDays)
    $toArchive = New-Object System.Collections.Generic.List[Object]

    foreach ($r in $rows) {
        if ($r.Status -ne "DONE" -and $r.Status -ne "RESOLVED") { continue }
        if (-not $r.FileName) { continue }
        $filePath = Join-Path $msgDir $r.FileName
        if (-not (Test-Path $filePath)) { continue }

        # created_at from the message file frontmatter decides eligibility.
        $created = $null
        foreach ($fl in (Read-Utf8Lines -Path $filePath)) {
            if ($fl -match "^created_at:\s*'?(\d{4}-\d{2}-\d{2})'?") {
                $created = [datetime]::ParseExact($Matches[1], "yyyy-MM-dd", $null); break
            }
        }
        if (-not $created) { continue }
        if ($created.Date -le $cutoff) { $toArchive.Add($r) | Out-Null }
    }

    if ($toArchive.Count -eq 0) {
        Write-Info ("WPAC inbox: no [DONE] messages older than {0} day(s) to archive" -f $ThresholdDays)
        return
    }

    # Ensure the archive index has a header.
    if (-not (Test-Path $archiveIdx)) {
        $hdr = @(
            "<!-- WPAC-ARCHIVE-INDEX-V1 -->",
            "# INBOX ARCHIVE",
            "",
            "> Archived [DONE] WPAC messages moved out of the active index.",
            "",
            "| Status | ID | Type | Source | Subject | Archived | File |",
            "|---|---|---|---|---|---|---|"
        )
        Set-Utf8NoBom -Path $archiveIdx -Lines $hdr
    }

    $stamp = (Get-Date).ToString("yyyy-MM-dd")
    $archivedRows = New-Object System.Collections.Generic.List[String]
    foreach ($r in $toArchive) {
        $src = Join-Path $msgDir $r.FileName
        $dst = Join-Path $archiveDir $r.FileName
        if (Test-Path $src) {
            if (Test-Path $dst) { Remove-Item $dst -Force }
            Move-Item -Path $src -Destination $dst -Force
        }
        $link = "[$($r.FileName)]($($r.FileName))"
        $archivedRows.Add("| [$($r.Status)] | $($r.Id) | $($r.Kind) | $($r.Source) | $($r.Subject) | $stamp | $link |") | Out-Null
    }
    Add-Utf8NoBom -Path $archiveIdx -Lines $archivedRows

    # Prune archived rows from the active index (match by message file name).
    $archiveNames = @{}
    foreach ($r in $toArchive) { $archiveNames[$r.FileName] = $true }
    $newLines = New-Object System.Collections.Generic.List[String]
    foreach ($line in $rawLines) {
        $drop = $false
        if ($line -match "^\|") {
            foreach ($name in $archiveNames.Keys) {
                if ($line -match [regex]::Escape("messages/$name")) { $drop = $true; break }
            }
        }
        if (-not $drop) { $newLines.Add($line) | Out-Null }
    }
    Set-Utf8NoBom -Path $inboxPath -Lines $newLines

    Write-Info ("WPAC inbox: archived {0} [DONE] message(s) older than {1} day(s) to messages/archive/" -f $toArchive.Count, $ThresholdDays)
}

# -----------------------------------------------------------------------------
# Dispatch
# -----------------------------------------------------------------------------
if ($Archive) {
    Invoke-Archive
}
else {
    # Default operation is Migrate (also the -Migrate switch path).
    Invoke-Migrate
}

exit 0
