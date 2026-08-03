@echo off
setlocal EnableExtensions

:: gald3r_clean_commit.bat -- BUG-626 / T804 / C-021 Cursor trailer workaround
:: @subsystems: RELEASE_AND_VERSIONING
::
:: Cursor's IDE agent shell silently rewrites every `git commit ...` command
:: issued from the agent to append a forbidden
:: `Co-authored-by: Cursor <cursoragent@cursor.com>` trailer (CONSTRAINTS.md
:: C-021). The injection happens at the IDE shell layer -- no git hook, no
:: commit template, no git config -- and is NOT bypassed by `--no-verify`,
:: `-F <file>`, `--trailer "..."`, or `git commit --amend`; even a direct
:: `git commit-tree` invocation gets rewritten by the interceptor.
::
:: This helper builds the commit out of `git write-tree` + `git commit-tree`
:: + `git update-ref` run from inside THIS child cmd.exe process. The IDE
:: shell wrapper does not reach inside a child process to rewrite its
:: output, so a commit produced this way carries no injected trailer.
:: Verify with `git cat-file -p HEAD` afterward.
::
:: Usage:
::   gald3r_clean_commit.bat INITIAL  <path-to-commit-message-file>
::   gald3r_clean_commit.bat FOLLOWUP <path-to-commit-message-file>
::
::   INITIAL  -- first commit in a repo with no parent (git commit-tree with
::               no `-p`)
::   FOLLOWUP -- ordinary commit parented at the current HEAD
::               (git commit-tree -p HEAD)
::
:: Exits non-zero with a message on stderr for any bad argument, a missing
:: or empty message file, or a failing git command -- never silently no-ops.

set "GALD3R_CC_MODE=%~1"
set "GALD3R_CC_MSGFILE=%~2"

if "%GALD3R_CC_MODE%"=="" (
    echo gald3r_clean_commit.bat: ERROR - missing MODE argument ^(expected INITIAL or FOLLOWUP^) 1>&2
    exit /b 1
)

if /I "%GALD3R_CC_MODE%"=="INITIAL" goto :gald3r_cc_mode_valid
if /I "%GALD3R_CC_MODE%"=="FOLLOWUP" goto :gald3r_cc_mode_valid
echo gald3r_clean_commit.bat: ERROR - invalid MODE "%GALD3R_CC_MODE%" ^(expected INITIAL or FOLLOWUP^) 1>&2
exit /b 1

:gald3r_cc_mode_valid
if "%GALD3R_CC_MSGFILE%"=="" (
    echo gald3r_clean_commit.bat: ERROR - missing MSGFILE argument ^(path to commit message file^) 1>&2
    exit /b 1
)

if not exist "%GALD3R_CC_MSGFILE%" (
    echo gald3r_clean_commit.bat: ERROR - message file "%GALD3R_CC_MSGFILE%" does not exist 1>&2
    exit /b 1
)

set "GALD3R_CC_MSGSIZE=0"
for %%F in ("%GALD3R_CC_MSGFILE%") do set "GALD3R_CC_MSGSIZE=%%~zF"
if "%GALD3R_CC_MSGSIZE%"=="0" (
    echo gald3r_clean_commit.bat: ERROR - message file "%GALD3R_CC_MSGFILE%" is empty 1>&2
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo gald3r_clean_commit.bat: ERROR - not inside a git working tree 1>&2
    exit /b 1
)

set "GALD3R_CC_TMP=%TEMP%\gald3r_clean_commit_%RANDOM%%RANDOM%.tmp"

git write-tree >"%GALD3R_CC_TMP%" 2>&1
if errorlevel 1 (
    echo gald3r_clean_commit.bat: ERROR - git write-tree failed: 1>&2
    type "%GALD3R_CC_TMP%" 1>&2
    del "%GALD3R_CC_TMP%" >nul 2>&1
    exit /b 1
)
set "GALD3R_CC_TREE="
set /p GALD3R_CC_TREE=<"%GALD3R_CC_TMP%"
del "%GALD3R_CC_TMP%" >nul 2>&1
if "%GALD3R_CC_TREE%"=="" (
    echo gald3r_clean_commit.bat: ERROR - git write-tree produced no output 1>&2
    exit /b 1
)

set "GALD3R_CC_TMP=%TEMP%\gald3r_clean_commit_%RANDOM%%RANDOM%.tmp"

if /I "%GALD3R_CC_MODE%"=="INITIAL" (
    git commit-tree "%GALD3R_CC_TREE%" -F "%GALD3R_CC_MSGFILE%" >"%GALD3R_CC_TMP%" 2>&1
) else (
    git commit-tree "%GALD3R_CC_TREE%" -p HEAD -F "%GALD3R_CC_MSGFILE%" >"%GALD3R_CC_TMP%" 2>&1
)
if errorlevel 1 (
    echo gald3r_clean_commit.bat: ERROR - git commit-tree failed: 1>&2
    type "%GALD3R_CC_TMP%" 1>&2
    del "%GALD3R_CC_TMP%" >nul 2>&1
    exit /b 1
)
set "GALD3R_CC_NEWSHA="
set /p GALD3R_CC_NEWSHA=<"%GALD3R_CC_TMP%"
del "%GALD3R_CC_TMP%" >nul 2>&1
if "%GALD3R_CC_NEWSHA%"=="" (
    echo gald3r_clean_commit.bat: ERROR - git commit-tree produced no output 1>&2
    exit /b 1
)

git update-ref HEAD "%GALD3R_CC_NEWSHA%"
if errorlevel 1 (
    echo gald3r_clean_commit.bat: ERROR - git update-ref HEAD failed for commit %GALD3R_CC_NEWSHA% 1>&2
    exit /b 1
)

echo gald3r_clean_commit.bat: committed %GALD3R_CC_NEWSHA% ^(mode=%GALD3R_CC_MODE%^)
exit /b 0
