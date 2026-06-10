@echo off
:: setup_gald3r_project.bat - gald3r Installer launcher
set SCRIPT_DIR=%~dp0
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%setup_gald3r_project.ps1" %*
if errorlevel 1 (
    echo.
    echo Script failed with error code %errorlevel%
    pause
)
