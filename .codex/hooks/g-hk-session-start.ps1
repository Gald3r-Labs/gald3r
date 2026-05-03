# g-hk-session-start.ps1 - Cursor hook for session initialization
# Triggered when a new composer conversation is created.
# Injects gald3r context and handles first-time user setup.

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
    $setupBanner = @"
## GALD3R FIRST-TIME SETUP NEEDED
Your gald3r user ID has not been configured yet.

**Quick setup:** Edit `.gald3r/.identity` and set `user_id` and `user_name` to your values.

---
"@
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
    Where-Object { $_.FullName -notmatch "\\.obsidian(\|\\)" }
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
- Vault path: `$VaultPath`
- Repos path: `$ReposPath`
- Notes: $vaultNoteCount
- Recent activity: $recentVaultActivity
"@

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

# ── Cross-project INBOX check ─────────────────────────────────────────────────
$inboxBanner = ""
try {
    $inboxOutput = & "$PSScriptRoot\g-hk-pcac-inbox-check.ps1" -ProjectRoot (Get-Location).Path 2>$null
    if ($inboxOutput -and $inboxOutput.Trim() -ne "") {
        $inboxBanner = "$inboxOutput`n---`n"
    }
} catch {}

$additionalContext = "${setupBanner}${reflectionBanner}${vaultBanner}${inboxBanner}gald3r task management system is active. Check .gald3r/TASKS.md for current tasks."

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
