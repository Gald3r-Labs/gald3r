@echo off
rem g-hk-augment-tool-start.cmd - Augment `PreToolUse` -> canonical `tool-start`
rem @subsystems: PLATFORM_INTEGRATION
rem Thin trigger shim ONLY (Augment requires a .ps1/.sh/.cmd/.bat script path, not a
rem bare `python x.py` command). Stdin is inherited by the child process automatically;
rem this shim just forwards to the shared canonical event core. Exit code 2 from the
rem core blocks the tool call (Augment PreToolUse semantics). NO business logic here.
python .augment\hooks\g-hk-on-tool-start.py
exit /b %ERRORLEVEL%
