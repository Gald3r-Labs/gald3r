#!/usr/bin/env pwsh
# Provision the bundled gald3r engine: ensure `uv`, then create/verify its environment.
# Cross-platform (Windows PowerShell 5.1, pwsh 7 on Win/macOS/Linux). Idempotent & safe:
# on ANY failure the engine is simply inactive and skills keep working via their SKILL.full.md
# fallbacks — this script never blocks an install.
#
#   pwsh .gald3r_sys/engine/provision_engine.ps1            # ensure uv + provision + verify
#   pwsh .gald3r_sys/engine/provision_engine.ps1 -NoInstall # don't auto-install uv, just check
param([switch]$NoInstall, [switch]$Quiet)

$engineDir = Split-Path -Parent $MyInvocation.MyCommand.Path
function Say($m, $c = 'Gray') { if (-not $Quiet) { Write-Host $m -ForegroundColor $c } }
$isWin = ($env:OS -like '*Windows*') -or ($IsWindows -eq $true)

# 1) ensure uv is available
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    if ($NoInstall) {
        Say "  uv not found (skipped install). Engine inactive; skills use their SKILL.full.md fallback." Yellow
        exit 2
    }
    Say "  Installing uv (one-time, no admin required)..." Cyan
    try {
        if ($isWin) {
            powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
            $bin = Join-Path $env:USERPROFILE ".local\bin"
            if (Test-Path $bin) { $env:PATH = "$bin;$env:PATH" }
        } else {
            sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
            if (Test-Path "$HOME/.local/bin") { $env:PATH = "$HOME/.local/bin:$env:PATH" }
        }
    } catch {
        Say "  uv install failed ($($_.Exception.Message)). Engine inactive; SKILL.full.md fallback is active." Yellow
        exit 2
    }
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Say "  uv installed but not yet on PATH — restart your shell, then re-run this script." Yellow
        Say "  (Skills still work meanwhile via their SKILL.full.md fallback.)" DarkGray
        exit 2
    }
}

# 2) provision + verify (uv auto-fetches Python + deps from the bundled pyproject)
Say "  Provisioning gald3r engine at $engineDir ..." Cyan
try {
    $ver = & uv run --project $engineDir gald3r --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($ver | Out-String) }
    Say "  Engine ready: $ver" Green
    Say "  Skills now call:  uv run --project .gald3r_sys/engine gald3r <verb>" DarkGray
    Say "  (MCP: run 'uv run --project .gald3r_sys/engine gald3r mcp' to expose the tools.)" DarkGray
    exit 0
} catch {
    Say "  Engine provision failed ($($_.Exception.Message))." Red
    Say "  No problem — skills remain fully operable via their SKILL.full.md fallback." Yellow
    exit 2
}
