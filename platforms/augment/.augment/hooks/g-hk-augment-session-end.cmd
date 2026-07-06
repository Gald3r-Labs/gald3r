@echo off
rem g-hk-augment-session-end.cmd - Augment `SessionEnd` -> canonical `session-end`
rem @subsystems: PLATFORM_INTEGRATION
rem Thin trigger shim ONLY (Augment requires a .ps1/.sh/.cmd/.bat script path, not a
rem bare `python x.py` command). Stdin is inherited by the child process automatically;
rem this shim just forwards to the shared canonical event core. NO business logic here.
python .augment\hooks\g-hk-on-session-end.py
exit /b %ERRORLEVEL%
