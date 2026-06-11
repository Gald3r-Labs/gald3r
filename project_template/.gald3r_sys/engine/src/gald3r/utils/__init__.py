"""Cross-platform utility layer — the Python replacement for the common
PowerShell patterns used across gald3r scripts (T1583).

Sub-modules:
    console — colored terminal output (replaces Write-Host -ForegroundColor)
    fs      — filesystem ops (replaces robocopy / Remove-Item / Set-VersionInTree)
    process — subprocess + git wrappers (replaces & git ... / $LASTEXITCODE)
    paths   — temp files and gald3r root resolution (replaces $env:TEMP walks)

Usage:
    from gald3r.utils import console, fs, paths, process
"""
# @subsystems: PLATFORM_INTEGRATION
from gald3r.utils import console, fs, paths, process

__all__ = ["console", "fs", "paths", "process"]
