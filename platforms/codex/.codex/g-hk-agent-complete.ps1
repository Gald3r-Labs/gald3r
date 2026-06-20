# g-hk-agent-complete.ps1 - Cursor hook for agent/stop lifecycle
# @subsystems: LOGGING_SYSTEM
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

# ── T1232: Fallback transcript discovery via agent-transcripts/ folder ────────
# Cursor stopped sending conversation_id/transcript_path in the stop event
# payload around April 2026. When those are missing, scan the agent-transcripts
# folder directly and use the most recently modified non-subagent JSONL file.
if (-not $transcriptPath -or -not (Test-Path $transcriptPath)) {
    try {
        $projectPath = (Get-Location).Path
        $rawSlug     = $projectPath -replace ':', '' -replace '[^A-Za-z0-9]', '-'
        $rawSlug     = $rawSlug.ToLower().Trim('-')
        $transcriptRoot = Join-Path $env:USERPROFILE ".cursor\projects\$rawSlug\agent-transcripts"
        if (-not (Test-Path $transcriptRoot)) {
            # Alternative: try appdata cursor projects
            $appDataRoot = Join-Path $env:APPDATA "Cursor\User\workspaceStorage"
            # Fall through — keep transcriptPath null
        } else {
            $latestJsonl = Get-ChildItem -Path $transcriptRoot -Recurse -Filter "*.jsonl" |
                Where-Object { $_.FullName -notmatch '\\subagents\\' -and $_.Name -notmatch 'subagent' } |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($latestJsonl) {
                $transcriptPath = $latestJsonl.FullName
                if ($conversationId -eq "unknown") {
                    $conversationId = $latestJsonl.BaseName
                }
                "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') T1232 fallback transcript: $($latestJsonl.Name)" |
                    Add-Content -Path ".gald3r/logs/hook_diag.log" -Encoding UTF8 -ErrorAction SilentlyContinue
            }
        }
    } catch {
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') T1232 transcript discovery error: $_" |
            Add-Content -Path ".gald3r/logs/hook_diag.log" -Encoding UTF8 -ErrorAction SilentlyContinue
    }
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
    # BUG-133 fix: probe for whichever chat logger actually ships in this
    # hook directory. g-hk-cursor-chat-logger.py does not ship in every
    # deployment (the .claude install ships g-hk-claude-chat-logger.py); the
    # previous hardcoded name was a silent no-op there.
    $loggerScript = $null
    foreach ($loggerName in @("g-hk-cursor-chat-logger.py", "g-hk-claude-chat-logger.py")) {
        $candidate = Join-Path $PSScriptRoot $loggerName
        if (Test-Path $candidate) { $loggerScript = $candidate; break }
    }
    if (-not $loggerScript) {
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') logger skipped: no chat logger ships in this deployment" |
            Add-Content -Path ".gald3r/logs/hook_diag.log" -Encoding UTF8 -ErrorAction SilentlyContinue
    }

    if ($loggerScript) {
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
                    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') logger FAILED exit=$LASTEXITCODE : $out" |
                        Add-Content -Path $diagPath -Encoding UTF8 -ErrorAction SilentlyContinue
                } else {
                    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') logger OK: chat log written" |
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

# ── T1174: Skill-Capture Stub (opt-in) ───────────────────────────────────────
# When AGENT_CONFIG.md has `skill_capture_hook: true`, stage a stub file in
# .gald3r/reports/skill_candidates/ inviting the next agent session to capture
# any reusable patterns discovered during this task as a SKILL.md candidate.
#
# The hook is fire-and-stage only — PowerShell hooks cannot literally prompt
# an LLM. The stub is filled by the agent at next session-start (the session
# start hook surfaces pending stubs) or by `@g-idea-farm`, which scans the
# candidate folder and surfaces filled stubs to IDEA_BOARD.md.
#
# Default: disabled. Opt in by setting `skill_capture_hook: true` in
# .gald3r/config/AGENT_CONFIG.md.
try {
    $agentConfigPath = ".gald3r/config/AGENT_CONFIG.md"
    $skillCaptureEnabled = $false
    if (Test-Path $agentConfigPath) {
        $configContent = Get-Content -Path $agentConfigPath -Raw -ErrorAction SilentlyContinue
        if ($configContent -and $configContent -match '(?m)^\s*skill_capture_hook\s*:\s*true\b') {
            $skillCaptureEnabled = $true
        }
    }

    if ($skillCaptureEnabled -and $status -eq "completed") {
        $candidatesDir = ".gald3r/reports/skill_candidates"
        if (-not (Test-Path $candidatesDir)) {
            New-Item -ItemType Directory -Path $candidatesDir -Force | Out-Null
        }

        $stampDate = Get-Date -Format "yyyyMMdd"
        $stampTime = Get-Date -Format "HHmmss"
        # Short, filesystem-safe conv id slice (or fallback to time stamp)
        $convShort = if ($conversationId -and $conversationId -ne "unknown") {
            ($conversationId -replace '[^A-Za-z0-9]', '').Substring(0, [Math]::Min(8, ($conversationId -replace '[^A-Za-z0-9]','').Length))
        } else { $stampTime }
        if (-not $convShort) { $convShort = $stampTime }
        $stubName = "${stampDate}_${stampTime}_session${convShort}.md"
        $stubPath = Join-Path $candidatesDir $stubName

        if (-not (Test-Path $stubPath)) {
            $stubBody = @"
---
status: pending
captured_at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
session_id: $conversationId
loop_count: $loopCount
session_status: $status
task_id: ""        # fill in if this session worked on a specific task (e.g., 1174)
---

# SKILL Candidate Stub (pending agent input)

Did this session reveal a reusable pattern? If yes, describe it in 3-5 lines
matching the SKILL.md structure below. If no, set `status: discarded` in the
frontmatter above and leave the body empty.

## name
<short kebab-case skill name, e.g., parallel-status-sweep>

## when_to_use
<one sentence — the trigger condition or user phrasing that activates it>

## how_it_works
<3-5 lines describing the procedure / steps / tool sequence>

## example
<minimal concrete example, code block, or invocation>

---

**Filled by**: agent / human
**Next step**: ``@g-idea-farm`` scans this folder and promotes filled stubs to ``IDEA_BOARD.md``.
"@
            Set-Content -Path $stubPath -Value $stubBody -Encoding UTF8
            try {
                "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') skill_capture stub written: $stubPath" |
                    Add-Content -Path ".gald3r/logs/hook_diag.log" -Encoding UTF8 -ErrorAction SilentlyContinue
            } catch {}
        }
    }
} catch {
    try {
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') skill_capture error: $_" |
            Add-Content -Path ".gald3r/logs/hook_diag.log" -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {}
}

@{} | ConvertTo-Json -Compress
exit 0
