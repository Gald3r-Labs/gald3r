#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Autonomous g-mission overnight runner — no human intervention needed.
    Loops @g-mission resume automatically on CONTEXT_GATE / BUDGET_EXHAUSTED.
    Only stops on real blocking exit codes.

.DESCRIPTION
    Runs the claude CLI in a tight loop, parsing EXIT_REASON from each
    session's output. CONTEXT_GATE and BUDGET_EXHAUSTED are transparent
    auto-resumes. All other exit codes surface to the user and stop the loop.

    Designed for overnight runs, AFK afternoons, or any unattended period.
    A 12-hour run at 20-30 min per session = up to 36 sessions with no human
    intervention needed.

.PARAMETER Condition
    The mission condition string. Omit to resume an existing ACTIVE_MISSION.md.
    Example: "drain all ai_safe tasks"

.PARAMETER UntilEmpty
    Run in --until-empty drain mode (default: true for overnight runs).

.PARAMETER Budget
    Per-session turn budget passed to @g-mission resume.
    Default: 999 (effectively no cap per session).

.PARAMETER MaxSessions
    Safety cap on total loop iterations. Default: 200 (~4-100 hours of work).

.PARAMETER ProjectPath
    Path to the gald3r_dev root. Defaults to current directory.

.PARAMETER ClaudeArgs
    Extra args forwarded to the claude CLI (e.g. "--model claude-opus-4-7").

.EXAMPLE
    # Resume an existing mission overnight
    .\scripts\mission-overnight.ps1

.EXAMPLE
    # Start a new mission and run overnight
    .\scripts\mission-overnight.ps1 -Condition "drain all ai_safe tasks" -UntilEmpty

.EXAMPLE
    # Run with a specific claude model
    .\scripts\mission-overnight.ps1 -ClaudeArgs "--model claude-opus-4-7"
#>

param(
    [string]$Condition = "",
    [switch]$UntilEmpty = $true,
    [int]$Budget = 999,
    [int]$MaxSessions = 200,
    [string]$ProjectPath = (Get-Location).Path,
    [string[]]$ClaudeArgs = @()
)

Set-Location $ProjectPath

$logFile   = Join-Path $ProjectPath ".gald3r\logs\mission_overnight_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$stateFile = Join-Path $ProjectPath ".gald3r\config\ACTIVE_MISSION.md"

# Codes that auto-resume — no human needed
$AUTO_RESUME_CODES = @("CONTEXT_GATE", "BUDGET_EXHAUSTED")

# Codes that stop the loop — something real happened
$STOP_CODES = @(
    "QUEUE_EMPTY",           # success — drain complete
    "CONDITION_MET",         # success — mission achieved
    "AI_SAFE_BLOCKED",       # needs human approval
    "BLAST_RADIUS_HIGH",     # needs human approval
    "PCAC_CONFLICT",         # needs inbox resolution
    "CLEAN_GATE_BLOCKED",    # dirty paths — needs human
    "DEPENDENCY_BLOCKED",    # all tasks blocked — needs human
    "HUMAN_DECISION_REQUIRED",
    "SAFETY_GATE"
)

function Write-Log {
    param([string]$msg, [string]$level = "INFO")
    $ts   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts][$level] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -Encoding UTF8 -ErrorAction SilentlyContinue
}

function Get-ExitReason {
    param([string]$output)
    if ($output -match "EXIT_REASON:\s*(\w+)") {
        return $Matches[1].Trim()
    }
    return $null
}

function Get-MissionStatus {
    if (-not (Test-Path $stateFile)) { return $null }
    $content = Get-Content $stateFile -Raw
    if ($content -match "status:\s*(\w[\w-]*)") { return $Matches[1].Trim() }
    return $null
}

# Ensure log dir exists
$null = New-Item -ItemType Directory -Force -Path (Split-Path $logFile)

Write-Log "=== mission-overnight.ps1 starting ===" "START"
Write-Log "ProjectPath : $ProjectPath"
Write-Log "Budget      : $Budget"
Write-Log "UntilEmpty  : $UntilEmpty"
Write-Log "MaxSessions : $MaxSessions"
Write-Log "LogFile     : $logFile"

$session   = 0
$totalTasks = 0
$startTime = Get-Date

# Build the initial prompt
if ($Condition) {
    $emptyFlag = if ($UntilEmpty) { " --until-empty" } else { "" }
    $initialPrompt = "@g-mission $Condition$emptyFlag --budget $Budget"
    Write-Log "Starting new mission: $initialPrompt"
} else {
    $budgetFlag = "--budget $Budget"
    $initialPrompt = "@g-mission resume --until-empty $budgetFlag"
    Write-Log "Resuming existing mission"
}

$prompt = $initialPrompt

while ($session -lt $MaxSessions) {
    $session++
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalHours, 1)
    Write-Log "--- Session $session / $MaxSessions  (${elapsed}h elapsed) ---"
    Write-Log "Prompt: $prompt"

    # Build claude CLI invocation
    $claudeInvocation = @(
        "--dangerously-skip-permissions",
        "-p", $prompt
    ) + $ClaudeArgs

    # Run claude and capture output
    $sessionOutput = ""
    try {
        $sessionOutput = & claude @claudeInvocation 2>&1 | Tee-Object -Variable rawLines | Out-String
        $exitCode = $LASTEXITCODE
    } catch {
        Write-Log "claude CLI invocation failed: $_" "ERROR"
        break
    }

    Write-Log "Session $session completed (exit=$exitCode, output length=$($sessionOutput.Length))"

    # Parse EXIT_REASON from output
    $exitReason = Get-ExitReason -output $sessionOutput

    if (-not $exitReason) {
        # No EXIT_REASON found — old format or crash — check mission status file
        $missionStatus = Get-MissionStatus
        Write-Log "No EXIT_REASON in output. ACTIVE_MISSION status: $missionStatus" "WARN"

        if ($missionStatus -eq "achieved") {
            Write-Log "Mission achieved (from state file). Stopping." "SUCCESS"
            break
        } elseif ($missionStatus -eq "paused") {
            Write-Log "Mission paused (from state file). Stopping — human review needed." "STOP"
            break
        } else {
            # Assume context gate / ambiguous — try one auto-resume
            Write-Log "Ambiguous exit — attempting one auto-resume" "WARN"
        }
    } else {
        Write-Log "EXIT_REASON: $exitReason"
    }

    # Count tasks from output (rough — looks for "N tasks shipped")
    if ($sessionOutput -match "(\d+) tasks? shipped") {
        $shipped = [int]$Matches[1]
        $totalTasks += $shipped
        Write-Log "This session shipped $shipped tasks (total so far: $totalTasks)"
    }

    # Decide what to do next
    if ($exitReason -in $STOP_CODES) {
        Write-Log "EXIT_REASON=$exitReason is a BLOCKING stop. Loop ending. Human review required." "STOP"
        Write-Host ""
        Write-Host "======================================================"
        Write-Host " MISSION OVERNIGHT STOPPED"
        Write-Host " Reason  : $exitReason"
        Write-Host " Sessions: $session"
        Write-Host " Tasks   : $totalTasks"
        Write-Host " Elapsed : ${elapsed}h"
        Write-Host " Log     : $logFile"
        Write-Host "======================================================"
        break
    }

    if ($exitReason -in $AUTO_RESUME_CODES -or -not $exitReason) {
        Write-Log "EXIT_REASON=$exitReason — auto-resuming next session"
        $prompt = "@g-mission resume --until-empty --budget $Budget"
        # Small breathing room between sessions — lets git settle, hooks finish
        Start-Sleep -Seconds 5
        continue
    }

    # Unknown code — treat as stop
    Write-Log "Unknown EXIT_REASON: $exitReason — treating as blocking stop" "WARN"
    break
}

if ($session -ge $MaxSessions) {
    Write-Log "MaxSessions ($MaxSessions) reached. Stopping loop." "STOP"
}

$totalElapsed = [math]::Round(((Get-Date) - $startTime).TotalHours, 2)
Write-Log "=== mission-overnight.ps1 complete === sessions=$session tasks=$totalTasks elapsed=${totalElapsed}h" "DONE"
