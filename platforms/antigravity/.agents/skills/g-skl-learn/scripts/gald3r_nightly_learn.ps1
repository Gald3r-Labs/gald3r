<#
.SYNOPSIS
    Nightly session summary extraction into learned-facts.md (T928).

.DESCRIPTION
    Reads recent session summaries from the vault (or local fallback), identifies
    facts not yet captured in learned-facts.md, and outputs an extraction prompt
    for the next agent session. Closes the gald3r learning loop:
    session ends -> memory_capture_session -> nightly extraction -> learned-facts.md

    Usage:
      .\gald3r_nightly_learn.ps1                    # Check and prepare extraction
      .\gald3r_nightly_learn.ps1 -Apply             # Apply extracted facts (agent-mode)
      .\gald3r_nightly_learn.ps1 -DryRun            # Show what would be extracted
      .\gald3r_nightly_learn.ps1 -LookbackDays 7   # Sessions from last 7 days

.PARAMETER ProjectRoot
    Root directory of the gald3r-managed project.

.PARAMETER LookbackDays
    How many days of sessions to include (default: 3).

.PARAMETER Apply
    If set, the agent has already performed extraction and is writing the results.
    Expects -ExtractedFacts param with newline-separated bullet points.

.PARAMETER ExtractedFacts
    String containing extracted facts (used with -Apply).

.PARAMETER DryRun
    Show what would be done without writing anything.

.PARAMETER Json
    Output structured JSON.
#>

[CmdletBinding()]
param(
    [string] $ProjectRoot = (Get-Location).Path,
    [int]    $LookbackDays = 3,
    [switch] $Apply,
    [string] $ExtractedFacts = '',
    [switch] $DryRun,
    [switch] $Json
)

$ErrorActionPreference = 'Stop'

# ── Helpers ──────────────────────────────────────────────────────────────────

function Log {
    param([string]$Msg, [string]$Color = 'White')
    if (-not $Json) { Write-Host $Msg -ForegroundColor $Color }
}

function Out-Json {
    param([hashtable]$Data)
    Write-Output (ConvertTo-Json $Data -Compress -Depth 6)
}

# PS5.1-compatible multi-segment path join.
# PS7 Join-Path accepts 3+ positional args; PS5.1 only accepts 2.
function Join-Paths {
    $result = $args[0]
    for ($i = 1; $i -lt $args.Count; $i++) { $result = Join-Path $result $args[$i] }
    return $result
}

# ── Load .identity ────────────────────────────────────────────────────────────

$identityPath = Join-Paths $ProjectRoot '.gald3r' '.identity'
$projectName  = 'unknown'
$vaultLocation = ''

if (Test-Path $identityPath) {
    Get-Content $identityPath | ForEach-Object {
        if ($_ -match '^project_name=(.+)$') { $projectName  = $Matches[1].Trim() }
        if ($_ -match '^vault_location=(.+)$') { $vaultLocation = $Matches[1].Trim() }
    }
}

# ── Locate learned-facts.md ──────────────────────────────────────────────────

$learnedFactsPath = Join-Paths $ProjectRoot '.gald3r' 'learned-facts.md'
$existingFacts = ''
if (Test-Path $learnedFactsPath) {
    $existingFacts = Get-Content $learnedFactsPath -Raw
}

# ── APPLY MODE: write extracted facts ────────────────────────────────────────

if ($Apply) {
    if (-not $ExtractedFacts) {
        Log "ERROR: -Apply requires -ExtractedFacts" 'Red'
        exit 1
    }

    $lines = $ExtractedFacts -split "`n" | Where-Object { $_ -match '^\s*-\s+' }
    if (-not $lines) {
        Log "No fact lines found in -ExtractedFacts" 'Yellow'
        exit 0
    }

    $date = (Get-Date).ToString('yyyy-MM-dd')
    $newFacts = @()

    foreach ($line in $lines) {
        $fact = $line.Trim()
        # Simple string dedup: skip if any existing line contains this fact's keywords
        $keywords = ($fact -replace '^\s*-\s+\[[\w-]+\]\s*', '') -split '\s+' | Where-Object { $_.Length -gt 4 } | Select-Object -First 3
        $isDup = $false
        foreach ($kw in $keywords) {
            if ($existingFacts -match [regex]::Escape($kw)) { $isDup = $true; break }
        }
        if (-not $isDup) { $newFacts += $fact }
    }

    if (-not $newFacts) {
        Log "All extracted facts already present in learned-facts.md — nothing to add." 'Cyan'
        if ($Json) { Out-Json @{ ok = $true; added = 0; skipped = $lines.Count } }
        exit 0
    }

    if ($DryRun) {
        Log "DRY-RUN: would append $($newFacts.Count) fact(s):" 'Cyan'
        $newFacts | ForEach-Object { Log "  $_" 'Gray' }
        if ($Json) { Out-Json @{ ok = $true; dryRun = $true; wouldAdd = $newFacts } }
        exit 0
    }

    # Ensure the file has an Architecture section
    if (-not (Test-Path $learnedFactsPath)) {
        $scaffold = @"
# learned-facts.md

## Architecture & Conventions

## Recurring Preferences

## Watch-Outs & Gotchas

## Superseded Facts
"@
        [System.IO.File]::WriteAllText($learnedFactsPath, $scaffold, [System.Text.UTF8Encoding]::new($false))
        $existingFacts = Get-Content $learnedFactsPath -Raw
    }

    $appendBlock = "`n" + ($newFacts -join "`n") + "`n"

    if ($existingFacts -match '## Architecture & Conventions') {
        # Insert after the Architecture header
        $existingFacts = $existingFacts -replace '(## Architecture & Conventions\n)', "`$1$appendBlock"
    } else {
        $existingFacts += $appendBlock
    }

    [System.IO.File]::WriteAllText($learnedFactsPath, $existingFacts, [System.Text.UTF8Encoding]::new($false))
    Log "Appended $($newFacts.Count) new fact(s) to learned-facts.md" 'Green'
    if ($Json) { Out-Json @{ ok = $true; added = $newFacts.Count; facts = $newFacts } }
    exit 0
}

# ── GATHER MODE: collect recent session summaries ─────────────────────────────

$cutoff = (Get-Date).AddDays(-$LookbackDays)
$sessionFiles = @()

# 1. Vault sessions path
if ($vaultLocation -and $vaultLocation -ne '{LOCAL}' -and (Test-Path $vaultLocation)) {
    $vaultSessions = Join-Paths $vaultLocation "projects" $projectName "sessions"
    if (Test-Path $vaultSessions) {
        $sessionFiles += Get-ChildItem $vaultSessions -Filter "*.md" -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $cutoff }
    }
}

# 2. Local fallback: .gald3r/logs/ or .gald3r/reports/
$localLogs = Join-Paths $ProjectRoot '.gald3r' 'logs'
if (Test-Path $localLogs) {
    $sessionFiles += Get-ChildItem $localLogs -Filter "*session*" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $cutoff }
}

# 3. Check last-extracted timestamp
$lastExtractedPath = Join-Paths $ProjectRoot '.gald3r' 'logs' 'nightly_learn_last_run.txt'
$lastExtracted = $null
if (Test-Path $lastExtractedPath) {
    $lastExtracted = [datetime]::Parse((Get-Content $lastExtractedPath -Raw).Trim())
    # Only include sessions newer than last extraction
    $sessionFiles = $sessionFiles | Where-Object { $_.LastWriteTime -gt $lastExtracted }
}

if (-not $sessionFiles) {
    $sinceDate = if ($null -ne $lastExtracted) { $lastExtracted } else { $cutoff }
    Log "No new session files found since $sinceDate - nothing to extract." 'Cyan'
    if ($Json) { Out-Json @{ ok = $true; sessionsFound = 0; action = 'none' } }
    exit 0
}

Log "Found $($sessionFiles.Count) session file(s) to process:" 'Cyan'
$sessionFiles | ForEach-Object { Log "  $($_.Name)" 'Gray' }

# ── Build extraction prompt ──────────────────────────────────────────────────

$summaries = $sessionFiles | ForEach-Object {
    $name = $_.Name
    $body = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    if ($body) {
        "### $name`n$($body.Substring(0, [Math]::Min(2000, $body.Length)))"
    }
}

$existingFactsSnippet = if ($existingFacts.Length -gt 3000) {
    $existingFacts.Substring(0, 3000) + "`n...(truncated)"
} else {
    $existingFacts
}

$prompt = @"
You are reviewing recent agent session summaries for the gald3r project ("$projectName").
Your job is to extract durable architectural facts, patterns, and gotchas that should be
preserved in learned-facts.md for the next agent session.

## Existing facts (do NOT repeat these):

$existingFactsSnippet

## Recent session summaries:

$($summaries -join "`n`n---`n`n")

## Instructions:

List any NEW architectural decisions, patterns, conventions, gotchas, or preferences
that are NOT already captured above. Format each as a single bullet:

  - [YYYY-MM-DD] {fact} (context: {brief context})

Focus on:
- Architecture decisions and rationale
- File locations and naming patterns
- Gotchas and workarounds discovered
- User/project preferences observed

Emit ONLY the bullet list. If nothing new, emit: (none)
"@

# Write extraction prompt to a temp file for the agent to use
$promptPath = Join-Paths $ProjectRoot '.gald3r' 'logs' 'nightly_learn_pending.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $promptPath) | Out-Null
[System.IO.File]::WriteAllText($promptPath, $prompt, [System.Text.UTF8Encoding]::new($false))

# Update last-run timestamp
[System.IO.File]::WriteAllText($lastExtractedPath, (Get-Date).ToString('o'), [System.Text.UTF8Encoding]::new($false))

Log "" 
Log "Extraction prompt written to: $promptPath" 'Green'
Log ""
Log "To complete the learning loop, run in your next agent session:" 'Yellow'
Log "  @g-learn extract" 'Yellow'
Log ""
Log "Or run the agent directly with the prompt content." 'Gray'

if ($Json) {
    Out-Json @{
        ok            = $true
        sessionsFound = $sessionFiles.Count
        promptPath    = $promptPath
        action        = 'prompt-ready'
        nextStep      = '@g-learn extract'
    }
}
