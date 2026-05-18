# g-hk-pcac-inbox-check.ps1 (T168 rewrite)
# Cross-project INBOX scanner. Safe to call at session start, before command work, during swarm heartbeats, and at final summaries.
# Reads INBOX.md, surfaces a per-item one-line summary grouped by type, and auto-actions LOW-RISK item types only.
# With -BlockOnConflict, exits with ConflictExitCode when open CONFLICT items exist.
#
# Auto-action policy (T168):
#   [INFO]      -> auto-mark-read (low risk, no action required).
#   [SYNC]      -> auto-mark-read (peer snapshot copy is left to @g-pcac-read).
#   [BROADCAST] -> surface only; user must @g-pcac-read --ack <id>.
#   [REQUEST]   -> surface only; user must @g-pcac-read --accept|--decline <id>.
#   [ORDER]     -> surface only; user must @g-pcac-read --accept <id>; treated as blocking.
#   [CONFLICT]  -> preserve existing g-rl-25 behavior (warning + session gate).
#
# Idempotency: re-running on an already-actioned inbox is a no-op (auto-actioned items have status [DONE]).
# Audit: every auto-action writes to .gald3r/logs/pcac_auto_actions.log with timestamp, item id, action.

param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$BlockOnConflict,
    [switch]$Quiet,
    [int]$ConflictExitCode = 2,
    [switch]$NoAutoAction
)

$inboxPath = Join-Path $ProjectRoot ".gald3r\linking\INBOX.md"
$logsDir   = Join-Path $ProjectRoot ".gald3r\logs"
$autoLog   = Join-Path $logsDir "pcac_auto_actions.log"

function Emit-Line {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Output $Message
    }
}

function Format-Age {
    param([datetime]$Then)
    $delta = (Get-Date) - $Then
    if ($delta.TotalHours -lt 24) {
        return ("{0}h ago" -f [int]$delta.TotalHours)
    }
    return ("{0}d ago" -f [int]$delta.TotalDays)
}

function Write-AutoLog {
    param([string]$ItemId, [string]$Action)
    if (-not (Test-Path $logsDir)) {
        New-Item -Path $logsDir -ItemType Directory -Force | Out-Null
    }
    $stamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -Path $autoLog -Value ("{0} | {1} | {2}" -f $stamp, $ItemId, $Action) -Encoding UTF8
}

# Graceful: linking/ not configured.
if (-not (Test-Path $inboxPath)) {
    Emit-Line "INBOX: not configured"
    exit 0
}

$rawLines = Get-Content $inboxPath -ErrorAction SilentlyContinue

if (-not $rawLines) {
    Emit-Line "INBOX: clear"
    exit 0
}

# --- Parse INBOX.md into items ---
# Items use one of two heading styles:
#   "## [OPEN] REQ-NNN — from: <proj> — YYYY-MM-DD"  (per-item, all kinds)
#   "## [CONFLICT]"                                    (section header — checkbox items follow)

$items = New-Object System.Collections.Generic.List[Object]
$current = $null
$inConflictSection = $false

function Add-Current {
    param([System.Collections.Generic.List[Object]]$List, $Cur)
    if ($null -ne $Cur) { $List.Add($Cur) | Out-Null }
}

for ($i = 0; $i -lt $rawLines.Count; $i++) {
    $line = $rawLines[$i]

    # Section-style CONFLICT header.
    if ($line -match "^## \[CONFLICT\]\s*$") {
        Add-Current $items $current; $current = $null
        $inConflictSection = $true
        continue
    }

    # Per-item heading (any kind).
    if ($line -match "^## \[(OPEN|DONE|CONFLICT)\]\s+(\S+)\s*[—\-]+\s*from:\s*([^—\-]+?)\s*[—\-]+\s*(\d{4}-\d{2}-\d{2})") {
        Add-Current $items $current
        $status = $matches[1]
        $id     = $matches[2].Trim()
        $src    = $matches[3].Trim()
        $dateOk = [datetime]::TryParseExact($matches[4], "yyyy-MM-dd", $null, [System.Globalization.DateTimeStyles]::None, [ref]([datetime]::MinValue))
        $date   = if ($dateOk) { [datetime]::ParseExact($matches[4], "yyyy-MM-dd", $null) } else { Get-Date }

        $kind = "INFO"
        if     ($id -match "^REQ")   { $kind = "REQUEST" }
        elseif ($id -match "^BCAST") { $kind = "BROADCAST" }
        elseif ($id -match "^SYNC")  { $kind = "SYNC" }
        elseif ($id -match "^ORD")   { $kind = "ORDER" }
        elseif ($id -match "^INFO")  { $kind = "INFO" }
        if ($status -eq "CONFLICT") { $kind = "CONFLICT" }

        $current = [PSCustomObject]@{
            Status  = $status
            Id      = $id
            Source  = $src
            Date    = $date
            Kind    = $kind
            Subject = ""
            Body    = New-Object System.Collections.Generic.List[String]
        }
        $inConflictSection = $false
        continue
    }

    # CONFLICT-section checkbox items: "- [ ] subject"
    if ($inConflictSection -and $line -match "^\s*-\s*\[\s*\]\s*(.+)$") {
        $items.Add([PSCustomObject]@{
            Status  = "CONFLICT"
            Id      = ("CFL-" + ($items.Count + 1).ToString("000"))
            Source  = "(section)"
            Date    = (Get-Date)
            Kind    = "CONFLICT"
            Subject = $matches[1].Trim()
            Body    = New-Object System.Collections.Generic.List[String]
        }) | Out-Null
        continue
    }

    if ($null -ne $current) {
        if ($line -match "^\*\*Subject:\*\*\s*(.+)$" -and -not $current.Subject) {
            $current.Subject = $matches[1].Trim()
        }
        $current.Body.Add($line) | Out-Null
    }
}
Add-Current $items $current

# --- Counts ---
$openConflicts  = @($items | Where-Object { $_.Kind -eq "CONFLICT" -and $_.Status -ne "DONE" })
$openRequests   = @($items | Where-Object { $_.Kind -eq "REQUEST"   -and $_.Status -eq "OPEN" })
$openBroadcasts = @($items | Where-Object { $_.Kind -eq "BROADCAST" -and $_.Status -eq "OPEN" })
$openOrders     = @($items | Where-Object { $_.Kind -eq "ORDER"     -and $_.Status -eq "OPEN" })
$openSyncs      = @($items | Where-Object { $_.Kind -eq "SYNC"      -and $_.Status -eq "OPEN" })
$openInfos     = @($items | Where-Object { $_.Kind -eq "INFO"      -and $_.Status -eq "OPEN" })

$totalConflicts = $openConflicts.Count
$total = $totalConflicts + $openRequests.Count + $openBroadcasts.Count + $openOrders.Count + $openSyncs.Count + $openInfos.Count

if ($total -eq 0) {
    Emit-Line "INBOX: clear"
    exit 0
}

# --- Conflict gate (preserves existing g-rl-25 Step 6 behavior) ---
if ($totalConflicts -gt 0) {
    Emit-Line ""
    Emit-Line ("INBOX CONFLICT GATE - " + $totalConflicts + " CONFLICT item(s) detected")
    Emit-Line "   Conflicts MUST be resolved via @g-pcac-read before task claiming, implementation, verification, or planning continues."
    Emit-Line "   File: .gald3r/linking/INBOX.md"
    $sortedConflicts = $openConflicts | Sort-Object -Property Date
    $shown = 0
    foreach ($c in $sortedConflicts) {
        if ($shown -ge 10) { break }
        $age = Format-Age -Then $c.Date
        $subj = if ($c.Subject) { $c.Subject } else { "(no subject)" }
        Emit-Line ("   - " + $c.Id + " from " + $c.Source + ": " + $subj + " (" + $age + ")")
        $shown++
    }
    if ($openConflicts.Count -gt 10) {
        Emit-Line ("   +" + ($openConflicts.Count - 10) + " more")
    }
    Emit-Line ""
    if ($BlockOnConflict) {
        exit $ConflictExitCode
    }
    exit 0
}

# --- Per-item summary (T168) ---
function Emit-Group {
    param([string]$Label, [string]$Emoji, $List)
    if ($List.Count -eq 0) { return }
    Emit-Line ""
    Emit-Line ("{0} {1} ({2})" -f $Emoji, $Label, $List.Count)
    $sorted = $List | Sort-Object -Property Date  # oldest first
    $shown = 0
    foreach ($it in $sorted) {
        if ($shown -ge 10) { break }
        $age = Format-Age -Then $it.Date
        $subj = if ($it.Subject) { $it.Subject } else { "(no subject)" }
        Emit-Line ("   - " + $it.Id + " from " + $it.Source + ": " + $subj + " (" + $age + ")")
        $shown++
    }
    if ($List.Count -gt 10) {
        Emit-Line ("   +" + ($List.Count - 10) + " more - run @g-pcac-read --all to see them all")
    }
}

Emit-Line ("INBOX: " + $total + " open")
Emit-Group "ORDERS (parent - explicit acceptance required)"     "ORD" $openOrders
Emit-Group "REQUESTS (child - explicit decision required)"      "REQ" $openRequests
Emit-Group "BROADCASTS (parent - explicit ack required)"        "BCT" $openBroadcasts
Emit-Group "SYNCS (sibling - auto-marked-read)"                 "SYN" $openSyncs
Emit-Group "INFO (auto-marked-read)"                            "INF" $openInfos

# --- Auto-action policy (T168) ---
# INFO + SYNC items are auto-marked-read. ORDERS / REQUESTS / BROADCASTS / CONFLICTS are surface-only.

if ($NoAutoAction) {
    Emit-Line ""
    Emit-Line ("Auto-action: skipped (-NoAutoAction); ORDERS/REQUESTS/BROADCASTS still need @g-pcac-read.")
    exit 0
}

$autoIds = New-Object System.Collections.Generic.HashSet[String]
foreach ($it in $openInfos) { $autoIds.Add($it.Id) | Out-Null }
foreach ($it in $openSyncs) { $autoIds.Add($it.Id) | Out-Null }

$autoActioned = 0

if ($autoIds.Count -gt 0) {
    # Rewrite [OPEN] -> [DONE] for auto-actioned items and stamp them with an Auto-actioned line.
    $newLines = New-Object System.Collections.Generic.List[String]
    $hasRecentlyActioned = $false
    $stamp = (Get-Date).ToString("yyyy-MM-dd")
    $i = 0
    while ($i -lt $rawLines.Count) {
        $line = $rawLines[$i]
        if ($line -match "^## \[OPEN\]\s+(\S+)\s*(.*)$") {
            $hdrId = $matches[1].Trim()
            if ($autoIds.Contains($hdrId)) {
                $newLines.Add(($line -replace "^## \[OPEN\]", "## [DONE]")) | Out-Null
                $i++
                $newLines.Add("**Auto-actioned:** $stamp by g-hk-pcac-inbox-check") | Out-Null
                Write-AutoLog -ItemId $hdrId -Action "auto-mark-read"
                $autoActioned++
                continue
            }
        }
        if ($line -match "^## Recently Actioned") { $hasRecentlyActioned = $true }
        $newLines.Add($line) | Out-Null
        $i++
    }

    if (-not $hasRecentlyActioned -and $autoActioned -gt 0) {
        $newLines.Add("") | Out-Null
        $newLines.Add("## Recently Actioned") | Out-Null
        $newLines.Add("") | Out-Null
        $newLines.Add("Auto-actioned items (INFO + SYNC) are stamped above with **Auto-actioned:** YYYY-MM-DD. Audit log: .gald3r/logs/pcac_auto_actions.log") | Out-Null
    }

    if ($autoActioned -gt 0) {
        Set-Content -Path $inboxPath -Value $newLines -Encoding UTF8
    }
}

if ($autoActioned -gt 0) {
    Emit-Line ""
    Emit-Line ("Auto-actioned: " + $autoActioned + " item(s) (INFO + SYNC); audit log: .gald3r/logs/pcac_auto_actions.log")
}

exit 0
