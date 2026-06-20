#Requires -Version 5.1
# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    Register a global `gald3r` command on the Windows user PATH (T471).

.DESCRIPTION
    Writes a small `gald3r.cmd` launcher into a launcher directory (default:
    the gald3r install home's bin/ -- %LOCALAPPDATA%\gald3r\bin) and adds that
    directory to the persisted user PATH (HKCU\Environment) so that
    `gald3r --version` works from any directory in a new terminal.

    The launcher prefers `uv run` against the bundled engine and falls back to
    `python -m gald3r`. The PATH edit is idempotent (the entry is added only when
    absent). This is the Windows twin of install_global_cli.py; the .py script is
    the cross-OS path (POSIX shim into ~/.local/bin on mac/Linux).

    See ..\docs\adr\ADR-016-install-home-and-global-cli.md.

.PARAMETER BinDir
    Override the launcher directory (default: %LOCALAPPDATA%\gald3r\bin).

.PARAMETER DryRun
    Preview only -- print planned operations and write nothing.

.PARAMETER Uninstall
    Remove the launcher and the user PATH entry.
#>

[CmdletBinding()]
param(
    [string]$BinDir = '',
    [switch]$DryRun,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

function Get-DefaultBinDir {
    $base = $env:LOCALAPPDATA
    if ([string]::IsNullOrWhiteSpace($base)) {
        $base = Join-Path $env:USERPROFILE 'AppData\Local'
    }
    return (Join-Path (Join-Path $base 'gald3r') 'bin')
}

function Get-EngineDir {
    # Resolve the bundled engine dir (the one holding pyproject.toml).
    $scriptDir = Split-Path -Parent $PSCommandPath
    $candidates = @(
        (Join-Path (Split-Path -Parent $scriptDir) 'engine'),
        (Join-Path (Get-Location).Path '.gald3r_sys\engine')
    )
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c 'pyproject.toml')) { return $c }
    }
    return $null
}

function Test-PathEntry {
    param([string]$PathValue, [string]$Target)
    $want = $Target.TrimEnd('\', '/').ToLowerInvariant()
    foreach ($e in ($PathValue -split ';')) {
        if (-not [string]::IsNullOrWhiteSpace($e)) {
            if ($e.TrimEnd('\', '/').ToLowerInvariant() -eq $want) { return $true }
        }
    }
    return $false
}

if ([string]::IsNullOrWhiteSpace($BinDir)) { $BinDir = Get-DefaultBinDir }
$engineDir = Get-EngineDir
$launcher = Join-Path $BinDir 'gald3r.cmd'

$action = if ($Uninstall) { 'uninstall' } else { 'install' }
$tag = if ($DryRun) { ' (DRY RUN)' } else { '' }
Write-Host "  gald3r global CLI $action$tag"
Write-Host "  launcher dir : $BinDir"
$engineLabel = if ($engineDir) { $engineDir } else { '(not found -- launcher uses python -m gald3r)' }
Write-Host "  engine dir   : $engineLabel"

# -- Build launcher body (CRLF, ASCII) ------------------------------------------
if ($engineDir) {
    $body = @"
@echo off
REM gald3r global launcher (T471) -- prefers uv, falls back to python -m
set "GALD3R_ENGINE_DIR=$engineDir"
where uv >nul 2>nul && (
  uv run --project "%GALD3R_ENGINE_DIR%" gald3r %*
) || (
  python -m gald3r %*
)
"@
} else {
    $body = @"
@echo off
REM gald3r global launcher (T471)
python -m gald3r %*
"@
}

# -- Uninstall ------------------------------------------------------------------
if ($Uninstall) {
    if ($DryRun) {
        Write-Host "[DRY] would remove launcher: $launcher"
        Write-Host "[DRY] would remove '$BinDir' from user PATH (HKCU\Environment)"
        return
    }
    if (Test-Path $launcher) { Remove-Item $launcher -Force; Write-Host "  removed launcher: $launcher" }
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($null -ne $userPath -and (Test-PathEntry -PathValue $userPath -Target $BinDir)) {
        $want = $BinDir.TrimEnd('\', '/').ToLowerInvariant()
        $kept = @($userPath -split ';' | Where-Object {
            -not [string]::IsNullOrWhiteSpace($_) -and $_.TrimEnd('\', '/').ToLowerInvariant() -ne $want
        })
        [Environment]::SetEnvironmentVariable('Path', ($kept -join ';'), 'User')
        Write-Host "  removed from user PATH: $BinDir"
    }
    return
}

# -- Install --------------------------------------------------------------------
if ($DryRun) {
    Write-Host "[DRY] would create dir: $BinDir"
    Write-Host "[DRY] would write launcher: $launcher"
    Write-Host "[DRY] would add '$BinDir' to user PATH (HKCU\Environment) if absent"
    return
}

if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }
# ASCII, CRLF .cmd
[System.IO.File]::WriteAllText($launcher, ($body -replace "`r?`n", "`r`n"), [System.Text.Encoding]::ASCII)
Write-Host "  wrote launcher: $launcher"

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($null -eq $userPath) { $userPath = '' }
if (Test-PathEntry -PathValue $userPath -Target $BinDir) {
    Write-Host "  user PATH already contains: $BinDir"
} else {
    $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $BinDir } else { "$userPath;$BinDir" }
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    Write-Host "  added to user PATH: $BinDir"
}
Write-Host "  Done. Open a NEW terminal, then: gald3r --version"
