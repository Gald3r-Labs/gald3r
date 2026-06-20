# g-hk-session-start.ps1 - Cursor hook for session initialization
# @subsystems: LOGGING_SYSTEM
# Triggered when a new composer conversation is created.
# Injects gald3r context and handles first-time user setup.

# ── Ensure platform dirs are populated from canonical root ────────────────────
try {
    $setupScript = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "setup_gald3r_project.ps1"
    if (Test-Path $setupScript) {
        & $setupScript -Platform cursor -Quiet
    }
} catch {}

# ── Idempotency guard ─────────────────────────────────────────────────────────
if ($env:GALD3R_HK_SESSION_START_APPLIED -eq "1") {
    @{ continue = $true; additional_context = "[SKIP] g-hk-session-start already applied this session" } | ConvertTo-Json -Compress
    exit 0
}
$env:GALD3R_HK_SESSION_START_APPLIED = "1"

$inputJson = $input | Out-String

# ── Read .identity file ───────────────────────────────────────────────────────
$identityFile = ".gald3r\.identity"
$identity = @{ project_id=""; project_name=""; user_id=""; user_name=""; gald3r_version=""; vault_location="" }
$setupNeeded = $false

if (Test-Path $identityFile) {
    Get-Content $identityFile | ForEach-Object {
        if ($_ -match "^(\w+)=(.*)$") { $identity[$Matches[1]] = $Matches[2].Trim() }
    }
}

# ── User identity resolution ──────────────────────────────────────────────────
$userId = $identity.user_id
if (-not $userId -or $userId -eq "{SETUP_NEEDED}" -or $userId -eq "") {
    # Fallback to appdata config
    $appDataConfig = if ($env:APPDATA) {
        Join-Path $env:APPDATA "gald3r\user_config.json"
    } else {
        Join-Path $env:HOME ".config/gald3r/user_config.json"
    }
    if (Test-Path $appDataConfig) {
        try {
            $appCfg = Get-Content $appDataConfig -Raw | ConvertFrom-Json
            if ($appCfg.user_id -and $appCfg.user_id -ne "SETUP_NEEDED") {
                $userId = $appCfg.user_id
                # Write back to .identity
                try {
                    $content = Get-Content $identityFile -Raw
                    $content = $content -replace "user_id=.*", "user_id=$userId"
                    Set-Content $identityFile $content -NoNewline
                } catch {}
            }
        } catch {}
    }
    if (-not $userId -or $userId -eq "SETUP_NEEDED") { $setupNeeded = $true }
}

# ── .project_id auto-heal ─────────────────────────────────────────────────────
$projectId = $identity.project_id
$uuidPattern = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
if (-not ($projectId -match $uuidPattern)) {
    $projectId = [guid]::NewGuid().ToString()
    try {
        $content = Get-Content $identityFile -Raw
        $content = $content -replace "project_id=.*", "project_id=$projectId"
        Set-Content $identityFile $content -NoNewline
    } catch {}
}

# ── Build context message ─────────────────────────────────────────────────────
$setupBanner = ""
if ($setupNeeded) {
    $setupBanner = @'
## GALD3R FIRST-TIME SETUP NEEDED
Your gald3r user ID has not been configured yet.

**Quick setup:** Edit `.gald3r/.identity` and set `user_id` and `user_name` to your values.

---
'@
}

$reflectionBanner = ""
$reflectionFile   = ".gald3r/logs/pending_reflection.json"
if (Test-Path $reflectionFile) {
    try {
        $reflData    = Get-Content $reflectionFile -Raw | ConvertFrom-Json
        $sessionSize = 0
        if ($reflData.loop_count) { $sessionSize = [int]$reflData.loop_count }

        if ($sessionSize -ge 5) {
            $reflectionBanner = @"
## Previous Session Reminder
Your last session had $sessionSize turns. Consider running **``@g-status``** to review where things stand.

---
"@
        }
        Remove-Item $reflectionFile -ErrorAction SilentlyContinue
    } catch {
        Remove-Item $reflectionFile -ErrorAction SilentlyContinue
    }
}

. "$PSScriptRoot\g-hk-vault-resolve.ps1"

$vaultNoteCount = @(
    Get-ChildItem -Path $VaultPath -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\.obsidian($|\\)" }
).Count

$recentVaultActivity = "none yet"
$vaultLogPath = Join-Path $VaultPath "log.md"
if (Test-Path $vaultLogPath) {
    $recentLogLine = Get-Content $vaultLogPath | Where-Object { $_ -match "^## " } | Select-Object -Last 1
    if ($recentLogLine) {
        $recentVaultActivity = $recentLogLine -replace "^##\s*", ""
    }
}

$vaultBanner = @"
## Vault Context
- Vault path: $VaultPath
- Repos path: $ReposPath
- Notes: $vaultNoteCount
- Recent activity: $recentVaultActivity
"@

# ── Vault existence / structure verification (T1456) ───────────────────────
# Warning-only: surfaces NOT FOUND / PARTIAL when a configured shared vault is
# missing or lacks its research/ subdirs. Never blocks session start.
try {
    . "$PSScriptRoot\g-hk-vault-verify.ps1"
    $vaultStatusLine = Get-Gald3rVaultStatusBanner -ProjectRoot (Get-Location).Path
    if ($vaultStatusLine) { $vaultBanner += "$vaultStatusLine`n" }
} catch {}

# ── Stale documentation check ──────────────────────────────────────────────
$staleDocBanner = ""
try {
    $indexPath = Join-Path $VaultPath "research/platforms/_index.yaml"
    if (Test-Path $indexPath) {
        $today = Get-Date
        $staleCount = 0
        $lines = Get-Content $indexPath -ErrorAction SilentlyContinue
        foreach ($line in $lines) {
            if ($line -match 'next_refresh:\s*(\d{4}-\d{2}-\d{2})') {
                $refreshDate = [DateTime]::ParseExact($Matches[1], "yyyy-MM-dd", $null)
                if ($refreshDate -lt $today) { $staleCount++ }
            }
        }
        if ($staleCount -gt 0) {
            $staleDocBanner = "- 📚 $staleCount documentation note(s) overdue for refresh — run ``@g-ingest-docs REFRESH_STALE```n"
        }
    }
} catch {}

if ($staleDocBanner) { $vaultBanner += $staleDocBanner }

if ($VaultMessages.Count -gt 0) {
    $vaultBanner += "`n"
    foreach ($message in $VaultMessages) {
        $vaultBanner += "- Notice: $message`n"
    }
}

$vaultBanner += "`n---`n"

# ── Vault raw inbox check ─────────────────────────────────────────────────────
$rawInboxBanner = ""
try {
    $rawPath = Join-Path $VaultPath "raw"
    if (Test-Path $rawPath) {
        $rawFiles = @(
            Get-ChildItem -Path $rawPath -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ne "README.md" }
        )
        if ($rawFiles.Count -gt 0) {
            $rawInboxBanner = "- 📥 $($rawFiles.Count) file(s) in vault raw/ inbox — drop processed via ``@g-vault-process-inbox`` (planned) or route manually via ``g-skl-ingest-*```n"
            $vaultBanner += $rawInboxBanner
        }
    }
} catch {}

# ── TASKS.md archive gate ─────────────────────────────────────────────────────
$archiveGateBanner = ""
try {
    $gateScript = Join-Path (Split-Path $PSScriptRoot -Parent) "scripts\gald3r_tasks_archive_gate.ps1"
    if (Test-Path $gateScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $gateScript -CheckOnly -ProjectRoot (Get-Location).Path 2>$null | Out-Null
        $gateExit = $LASTEXITCODE
        if ($gateExit -eq 2) {
            $archiveGateBanner = "WARNING: TASKS.md ARCHIVE GATE: file exceeds 1200 lines. Run: .cursor/skills/g-skl-tasks/scripts/gald3r_tasks_archive_gate.ps1 -Apply to archive terminal tasks.`n---`n"
        } elseif ($gateExit -eq 1) {
            $archiveGateBanner = "WARNING: TASKS.md approaching archive threshold (>=900 lines). Consider: .cursor/skills/g-skl-tasks/scripts/gald3r_tasks_archive_gate.ps1 -Apply`n---`n"
        }
    }
} catch {}

# ── HEARTBEAT no_agent watchdog (T968) ────────────────────────────────────────
# Cron entries in `.gald3r/config/HEARTBEAT.md` flagged `no_agent: true` run their
# script DIRECTLY (no agent invocation) and deliver output only when stdout is
# non-empty — a cheap "watchdog" for health checks. Entries without the flag
# (the default, `no_agent: false`) are left untouched for the normal agent path.
#
# Entry format (fenced ```yaml block per cron entry inside HEARTBEAT.md):
#   - id: disk-space-check
#     schedule: "0 * * * *"
#     no_agent: true            # run script directly, no agent
#     script: scripts/health/check_disk.ps1
#     output: log               # `log` (→ .gald3r/logs/) or `terminal` (default)
#
# Silent contract: empty stdout = no banner, no agent call, no message.
$watchdogBanner = ""
try {
    $heartbeatFile = Join-Path (Join-Path (Join-Path (Get-Location).Path '.gald3r') 'config') 'HEARTBEAT.md'
    if (Test-Path $heartbeatFile) {
        $hbRaw = Get-Content $heartbeatFile -Raw -ErrorAction Stop

        # Split into per-entry blocks on the leading `- id:` marker. Each entry is a
        # YAML-ish list item; we parse line-by-line rather than pulling a YAML module
        # so the hook stays dependency-free.
        $entryBlocks = [regex]::Split($hbRaw, '(?m)^\s*-\s+id:\s*') | Select-Object -Skip 1
        foreach ($block in $entryBlocks) {
            $blockText = $block

            # no_agent flag — only true entries are watchdogs. Default/false is skipped.
            if ($blockText -notmatch '(?m)^\s*no_agent:\s*true\s*$') { continue }

            # Required: a script path to execute directly.
            $scriptRel = $null
            if ($blockText -match '(?m)^\s*script:\s*["'']?([^"''\r\n]+?)["'']?\s*$') {
                $scriptRel = $Matches[1].Trim()
            }
            if (-not $scriptRel) { continue }

            # Optional output channel: `log` writes to .gald3r/logs/; default is terminal
            # (surfaced in the session-start additional_context banner).
            $outputChannel = 'terminal'
            if ($blockText -match '(?m)^\s*output:\s*["'']?(\w+)["'']?\s*$') {
                $outputChannel = $Matches[1].Trim().ToLower()
            }

            # Entry id (already consumed by the split) — recover the first token for labels.
            $entryId = ($blockText -split "`n", 2)[0].Trim().Trim('"', "'")
            if (-not $entryId) { $entryId = $scriptRel }

            # Resolve script path relative to the project root.
            $scriptPath = if ([System.IO.Path]::IsPathRooted($scriptRel)) {
                $scriptRel
            } else {
                Join-Path (Get-Location).Path $scriptRel
            }
            if (-not (Test-Path $scriptPath)) { continue }

            # Run the script directly and capture stdout only. Failures are swallowed
            # so a broken watchdog never blocks session start.
            $stdout = ""
            try {
                if ($scriptPath -match '\.ps1$') {
                    $stdout = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>$null | Out-String
                } else {
                    $stdout = & $scriptPath 2>$null | Out-String
                }
            } catch {
                $stdout = ""
            }

            # Silent on empty stdout — the whole point of watchdog mode.
            if (-not $stdout -or $stdout.Trim() -eq "") { continue }

            $stdout = $stdout.TrimEnd()
            if ($outputChannel -eq 'log') {
                # Deliver verbatim to a per-entry log file under .gald3r/logs/.
                try {
                    $wdLogDir = Join-Path (Join-Path (Get-Location).Path '.gald3r') 'logs'
                    if (-not (Test-Path $wdLogDir)) { New-Item -ItemType Directory -Path $wdLogDir -Force | Out-Null }
                    $stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
                    $wdLogFile = Join-Path $wdLogDir "watchdog_$entryId.log"
                    Add-Content -Path $wdLogFile -Value "## $stamp`n$stdout`n" -ErrorAction SilentlyContinue
                } catch {}
            } else {
                # Deliver verbatim to the terminal (session-start banner).
                $watchdogBanner += "## Watchdog: $entryId`n$stdout`n`n"
            }
        }
        if ($watchdogBanner) { $watchdogBanner += "---`n" }
    }
} catch {}

# ── Cross-project INBOX check ─────────────────────────────────────────────────
$inboxBanner = ""
try {
    $inboxOutput = & "$PSScriptRoot\g-hk-pcac-inbox-check.ps1" -ProjectRoot (Get-Location).Path 2>$null
    if ($inboxOutput -and $inboxOutput.Trim() -ne "") {
        $inboxBanner = "$inboxOutput`n---`n"
    }
} catch {}

$additionalContext = "${setupBanner}${reflectionBanner}${vaultBanner}${archiveGateBanner}${watchdogBanner}${inboxBanner}gald3r task management system is active. Check .gald3r/TASKS.md for current tasks."

# ── Append GUARDRAILS if present ──────────────────────────────────────────────
$guardrailsFile = "GUARDRAILS.md"
if (Test-Path $guardrailsFile) {
    try {
        $guardrails = Get-Content $guardrailsFile -Raw
        $additionalContext = "${additionalContext}`n`n---`n`n${guardrails}"
    } catch {}
}

# ── Response ──────────────────────────────────────────────────────────────────
$response = @{
    continue           = $true
    additional_context = $additionalContext
}

$response | ConvertTo-Json -Compress
exit 0
