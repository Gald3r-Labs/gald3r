# gald3r-setup-user.ps1
# Run this ONCE from a terminal to set your gald3r user identity.
# Your user ID is stored in ~/.gald3r/user_config.json and used across
# all AI sessions (Cursor, Claude Code, Gemini) on this machine.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .cursor/hooks/g-hk-setup-user.ps1

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "  gald3r User Setup" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your user ID identifies you across all AI memory sessions on this machine."
Write-Host "Use your email, a nickname, initials -- whatever you want." -ForegroundColor Gray
Write-Host ""

# ── Detect suggestions ──────────────────────────────────────────────────────
$suggestions = @()

# Git global email (most universal)
try {
    $gitEmail = (git config --global user.email 2>$null).Trim()
    if ($gitEmail) { $suggestions += $gitEmail }
} catch {}

# Cursor cached email
try {
    $vscDb = "$env:APPDATA\Cursor\User\globalStorage\state.vscdb"
    if (Test-Path $vscDb) {
        Add-Type -AssemblyName System.Data.SQLite 2>$null
        # Use python to query it (sqlite3 is always available via Python)
        $cursorEmail = python -c "
import sqlite3
conn = sqlite3.connect(r'$vscDb')
cur = conn.cursor()
cur.execute(\"SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'\")
row = cur.fetchone()
print(row[0] if row else '')
conn.close()
" 2>$null
        $cursorEmail = $cursorEmail.Trim()
        if ($cursorEmail -and $cursorEmail -notin $suggestions) {
            $suggestions += $cursorEmail
        }
    }
} catch {}

# Windows username as last fallback suggestion
$winUser = $env:USERNAME
if ($winUser) { $suggestions += $winUser }

# ── Show suggestions ─────────────────────────────────────────────────────────
if ($suggestions.Count -gt 0) {
    Write-Host "Detected options:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $suggestions.Count; $i++) {
        Write-Host "  [$($i+1)] $($suggestions[$i])" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "Enter your user ID (or press Enter to use suggestion [1]):" -ForegroundColor Green -NoNewline
Write-Host " " -NoNewline
$userInput = Read-Host

# Resolve choice
$userId = $userInput.Trim()
if (-not $userId) {
    if ($suggestions.Count -gt 0) {
        $userId = $suggestions[0]
        Write-Host "Using: $userId" -ForegroundColor Gray
    } else {
        $userId = "user_$env:USERNAME"
        Write-Host "Using: $userId" -ForegroundColor Gray
    }
} elseif ($userId -match '^\d+$') {
    # User typed a number — pick from suggestions list
    $idx = [int]$userId - 1
    if ($idx -ge 0 -and $idx -lt $suggestions.Count) {
        $userId = $suggestions[$idx]
        Write-Host "Using: $userId" -ForegroundColor Gray
    }
}

# ── Read or create existing user_config.json ────────────────────────────────
$configDir  = Join-Path $env:USERPROFILE ".gald3r"
$configFile = Join-Path $configDir "user_config.json"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$cfg = [ordered]@{}

if (Test-Path $configFile) {
    try {
        $existing = Get-Content $configFile -Raw | ConvertFrom-Json
        # Preserve all existing fields
        $existing.PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value }
    } catch {}
}

# Stable machine ID
$machineId = $cfg["machine_id"]
if (-not $machineId) {
    try {
        $machineId = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" `
                      -Name "MachineGuid" -ErrorAction Stop).MachineGuid
    } catch {
        $machineId = [System.Guid]::NewGuid().ToString()
    }
}

# Update / set fields
$cfg["user_id"]         = $userId
$cfg["machine_id"]      = $machineId
$cfg["mcp_url"]         = if ($cfg["mcp_url"]) { $cfg["mcp_url"] } else { "http://localhost:8082" }
$cfg["platform"]        = "windows"
$cfg["setup_completed"] = $true
$cfg["setup_date"]      = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
$cfg["created_by"]      = "gald3r-setup-user.ps1"

$cfg | ConvertTo-Json | Set-Content -Path $configFile -Encoding UTF8

Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "  User ID  : $userId" -ForegroundColor White
Write-Host "  Config   : $configFile" -ForegroundColor Gray
Write-Host ""
Write-Host "This ID will be used for all gald3r memory sessions on this machine." -ForegroundColor Gray
Write-Host "To change it later, edit: $configFile" -ForegroundColor Gray
Write-Host ""
