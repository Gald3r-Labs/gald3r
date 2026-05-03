# g-hk-pcac-inbox-check.ps1
# Cross-project INBOX scanner. Safe to call at session start, before command work, during swarm heartbeats, and at final summaries.
# Read-only by default; never modifies INBOX.md.
# With -BlockOnConflict, exits with ConflictExitCode when open CONFLICT items exist.

param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$BlockOnConflict,
    [switch]$Quiet,
    [int]$ConflictExitCode = 2
)

$inboxPath = Join-Path $ProjectRoot ".gald3r\linking\INBOX.md"

function Emit-Line {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Output $Message
    }
}

# Graceful: linking/ not configured
if (-not (Test-Path $inboxPath)) {
    Emit-Line "INBOX: not configured"
    exit 0
}

$lines = Get-Content $inboxPath -ErrorAction SilentlyContinue

if (-not $lines) {
    Emit-Line "INBOX: clear"
    exit 0
}

# Count open items by type.
$conflicts  = 0  # CONFLICT gating is section-scoped; advisory items may mention the word without blocking.
$requests   = @($lines | Where-Object { $_ -match "REQ-\d+" -and $_ -match "\[OPEN\]" }).Count
$broadcasts = @($lines | Where-Object { $_ -match "BCAST-\d+" -and $_ -match "\[OPEN\]" }).Count
$syncs      = @($lines | Where-Object { $_ -match "SYNC-\d+" -and $_ -match "\[OPEN\]" }).Count

# Also count CONFLICT section headers with checkbox content.
$inConflictSection = $false
$conflictItems = 0
foreach ($line in $lines) {
    if ($line -match "^## \[CONFLICT\]") { $inConflictSection = $true; continue }
    if ($line -match "^## \[" -and $line -notmatch "^## \[CONFLICT\]") { $inConflictSection = $false }
    if ($inConflictSection -and $line -match "^\s*-\s*\[\s*\]") { $conflictItems++ }
}

$totalConflicts = [Math]::Max($conflicts, $conflictItems)
$total = $totalConflicts + $requests + $broadcasts + $syncs

if ($total -eq 0) {
    Emit-Line "INBOX: clear"
    exit 0
}

if ($totalConflicts -gt 0) {
    Emit-Line ""
    Emit-Line ("INBOX CONFLICT GATE - " + $totalConflicts + " CONFLICT item(s) detected")
    Emit-Line "   Conflicts MUST be resolved via @g-pcac-read before task claiming, implementation, verification, or planning continues."
    Emit-Line "   File: .gald3r/linking/INBOX.md"
    Emit-Line ""
    if ($BlockOnConflict) {
        exit $ConflictExitCode
    }
    exit 0
}

$parts = @()
if ($requests -gt 0)   { $parts += ("$requests request(s)") }
if ($broadcasts -gt 0) { $parts += ("$broadcasts broadcast(s)") }
if ($syncs -gt 0)      { $parts += ("$syncs sync(s)") }
$detail = ""
if ($parts.Count -gt 0) { $detail = " (" + ($parts -join ", ") + ")" }
Emit-Line ("INBOX: " + $total + " open" + $detail)
exit 0
