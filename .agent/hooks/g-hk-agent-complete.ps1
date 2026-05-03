# g-hk-agent-complete.ps1 - Cursor hook for agent/stop lifecycle
# Triggered when the agent loop ends ("stop" event in hooks.json).
# Persists a local chat log and writes a reflection hint for the next session.
#
# Cursor sends JSON via stdin. Guard with IsInputRedirected before ReadToEnd()
# to prevent blocking when stdin is a console (not a pipe). Without this guard,
# ReadToEnd() never returns in non-piped contexts (BUG-003 root cause).
#
# stop event payload: {"status": "completed"|"aborted"|"error", "loop_count": N}
# loop_count = number of times THIS hook has already triggered an auto-follow-up
# (starts at 0). It is NOT a conversation turn counter.

$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

# ── Diagnostic log (fires unconditionally — proves hook ran) ─────────────────
try {
    $diagLog = ".gald3r/logs/hook_diag.log"
    if (-not (Test-Path ".gald3r/logs")) { New-Item -ItemType Directory -Path ".gald3r/logs" -Force | Out-Null }
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') agent-complete hook fired, cwd=$(Get-Location)" |
        Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
} catch {}

try {
    $eventData      = $inputJson | ConvertFrom-Json
    $status         = if ($eventData.status) { $eventData.status } else { "unknown" }
    # Official Cursor schema uses snake_case: loop_count, conversation_id, transcript_path
    $loopCount      = if ($null -ne $eventData.loop_count) { $eventData.loop_count } else { 0 }
    $conversationId = if ($eventData.conversation_id) { $eventData.conversation_id } else { "unknown" }
    $transcriptPath = if ($eventData.transcript_path)  { $eventData.transcript_path  } else { $null }
    # Fallback: Cursor also exposes transcript path as env var
    if (-not $transcriptPath -and $env:CURSOR_TRANSCRIPT_PATH) {
        $transcriptPath = $env:CURSOR_TRANSCRIPT_PATH
    }
} catch {
    $status         = "unknown"
    $loopCount      = 0
    $conversationId = "unknown"
    $transcriptPath = $null
}

# Log resolved values to diagnostic (second entry with context)
try {
    $diagLog = ".gald3r/logs/hook_diag.log"
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') event: status=$status loops=$loopCount convId=$conversationId" |
        Add-Content -Path $diagLog -Encoding UTF8 -ErrorAction SilentlyContinue
} catch {}

# Write a local chat transcript synchronously (with timeout to avoid race condition on Cursor exit).
try {
    $projectPath   = (Get-Location).Path
    $loggerScript  = Join-Path $PSScriptRoot "g-hk-cursor-chat-logger.py"

    if (Test-Path $loggerScript) {
        $pythonCmd = $null
        if (Get-Command py -ErrorAction SilentlyContinue) {
            $pythonCmd = "py"
            $pythonArgs = @(
                "-3",
                $loggerScript,
                "--project-path", $projectPath,
                "--loop-count",   $loopCount,
                "--status",       $(if ($status -eq "completed") { "completed" } else { $status }),
                "--platform",     "cursor"
            )
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            $pythonCmd = "python"
            $pythonArgs = @(
                $loggerScript,
                "--project-path", $projectPath,
                "--loop-count",   $loopCount,
                "--status",       $(if ($status -eq "completed") { "completed" } else { $status }),
                "--platform",     "cursor"
            )
        } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
            $pythonCmd = "python3"
            $pythonArgs = @(
                $loggerScript,
                "--project-path", $projectPath,
                "--loop-count",   $loopCount,
                "--status",       $(if ($status -eq "completed") { "completed" } else { $status }),
                "--platform",     "cursor"
            )
        }

        if ($pythonCmd) {
            if ($conversationId -and $conversationId -ne "unknown") {
                $pythonArgs += "--conversation-id"
                $pythonArgs += $conversationId
            }
            if ($transcriptPath) {
                $pythonArgs += "--transcript-path"
                $pythonArgs += $transcriptPath
            }

            # Run synchronously with 30-second timeout so Cursor exit doesn't kill the job.
            # Captures stderr to the diagnostic log so failures are visible.
            $job = Start-Job -ScriptBlock {
                param($exe, $cliArgs, $diagPath)
                $out = & $exe @cliArgs 2>&1
                if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
                    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') logger exited $LASTEXITCODE : $out" |
                        Add-Content -Path $diagPath -Encoding UTF8 -ErrorAction SilentlyContinue
                }
            } -ArgumentList $pythonCmd, $pythonArgs, (Join-Path (Get-Location).Path ".gald3r/logs/hook_diag.log")

            $job | Wait-Job -Timeout 30 | Out-Null
            $job | Remove-Job -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
    try {
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') logger launch error: $_" |
            Add-Content -Path ".gald3r/logs/hook_diag.log" -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {}
}

# Always write a reflection hint so the next session-start hook can prompt
# a brief review of what was accomplished. Includes written_at so the
# session-start hook can ignore stale files (e.g. > 48 hours old).
try {
    $logsDir = ".gald3r/logs"
    if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
    $reflectionData = @{
        conversation_id = $conversationId
        loop_count      = [int]$loopCount
        status          = $status
        written_at      = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
    $reflectionData | ConvertTo-Json -Compress | Set-Content -Path "$logsDir/pending_reflection.json" -Encoding UTF8
} catch {}

@{} | ConvertTo-Json -Compress
exit 0
