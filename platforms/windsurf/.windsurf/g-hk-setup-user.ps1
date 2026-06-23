# gald3r-setup-user.ps1
# @subsystems: PROJECT_IDENTITY_SETUP
# Run this ONCE from a terminal to set your gald3r user identity.
#
# T627: this script no longer writes its own identity file. It delegates to the
# sibling Python hook (g-hk-setup-user.py), which provisions the ONE unified
# identity record managed by the engine (gald3r.user_config / gald3r.home, T530/
# T531) — %LOCALAPPDATA%\gald3r\user_config.json on Windows. The previous
# ~/.gald3r/user_config.json divergent path is retired (the Python hook migrates
# any pre-existing one forward without regenerating ids). Keeping a single
# implementation avoids two competing identity writers.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .cursor/hooks/g-hk-setup-user.ps1

$ErrorActionPreference = "Stop"

# Locate the sibling Python hook (same directory as this script).
$pyHook = Join-Path $PSScriptRoot "g-hk-setup-user.py"
if (-not (Test-Path $pyHook)) {
    Write-Host "ERROR: cannot find the Python setup hook next to this script: $pyHook" -ForegroundColor Red
    Write-Host "Identity setup is delegated to g-hk-setup-user.py (T627). Run it directly:" -ForegroundColor Yellow
    Write-Host "  python `"$pyHook`"" -ForegroundColor Gray
    exit 1
}

# Resolve a Python interpreter (the Python hook needs the gald3r engine).
$py = $null
foreach ($cand in @("python", "python3", "py")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}
if (-not $py) {
    Write-Host "ERROR: no Python interpreter found (python / python3 / py)." -ForegroundColor Red
    Write-Host "Install Python, then run: python `"$pyHook`"" -ForegroundColor Yellow
    exit 1
}

# Delegate — the Python hook drives the interactive prompts and writes the unified
# identity record + setup_meta.json sidecar.
& $py $pyHook
exit $LASTEXITCODE
