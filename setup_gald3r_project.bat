@echo off
:: setup_gald3r_project.bat - gald3r Installer launcher (T1586: Python port)
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%setup_gald3r_project.py" %*
if errorlevel 1 (
    echo.
    echo Script failed with error code %errorlevel%
    pause
)
