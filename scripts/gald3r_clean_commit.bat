@echo off
REM gald3r_clean_commit.bat
REM
REM Workaround for Cursor IDE (and similar AI agents) injecting a
REM `Co-authored-by: Cursor <cursoragent@cursor.com>` trailer into every
REM `git commit` invocation made from the AI agent shell. Per CONSTRAINTS.md
REM C-021 (no-co-author-commit-footer) such trailers are forbidden because
REM they create co-owned IP / co-author records that complicate future
REM commercial licensing or acquisition.
REM
REM This helper bypasses the IDE-level intercept by invoking git via a
REM child cmd.exe process that the IDE shell wrapper does not rewrite.
REM
REM Two modes:
REM   1) INITIAL  : create the very first commit on a fresh repo
REM                 (no parent). Caller has already run `git add .`
REM                 to stage the working tree.
REM
REM   2) FOLLOWUP : create a follow-up commit, parented at current HEAD.
REM                 Caller has already run `git add` for the changes.
REM
REM Usage:
REM   gald3r_clean_commit.bat <mode> <message_file>
REM     <mode>          : INITIAL | FOLLOWUP
REM     <message_file>  : absolute path to UTF-8 file containing the commit
REM                       message (already free of any AI co-author trailer)
REM
REM Exit codes:
REM   0  success
REM   1  bad args
REM   2  git command failed
REM
REM Run from the repository root.
setlocal
set MODE=%~1
set MSGFILE=%~2
if "%MODE%"=="" goto :usage
if "%MSGFILE%"=="" goto :usage
if not exist "%MSGFILE%" (
  echo ERROR: message file not found: %MSGFILE%
  exit /b 1
)
REM Build the new tree from the staged index.
for /f "delims=" %%T in ('git write-tree') do set TREE=%%T
if "%TREE%"=="" (
  echo ERROR: git write-tree returned empty
  exit /b 2
)
echo TREE=%TREE%
if /i "%MODE%"=="INITIAL" (
  for /f "delims=" %%S in ('git commit-tree %TREE% -F "%MSGFILE%"') do set NEWSHA=%%S
) else if /i "%MODE%"=="FOLLOWUP" (
  for /f "delims=" %%P in ('git rev-parse HEAD') do set PARENT=%%P
  for /f "delims=" %%S in ('git commit-tree %TREE% -p %PARENT% -F "%MSGFILE%"') do set NEWSHA=%%S
) else (
  goto :usage
)
if "%NEWSHA%"=="" (
  echo ERROR: git commit-tree returned empty
  exit /b 2
)
echo NEWSHA=%NEWSHA%
REM In a fresh repository, `git rev-parse --abbrev-ref HEAD` can fail because
REM HEAD has no commit yet. `symbolic-ref --short HEAD` reads the branch name
REM from the symbolic ref itself and works before the first commit exists.
for /f "delims=" %%B in ('git symbolic-ref --short HEAD') do set BRANCH=%%B
if "%BRANCH%"=="" set BRANCH=main
git update-ref refs/heads/%BRANCH% %NEWSHA%
if errorlevel 1 (
  echo ERROR: git update-ref failed
  exit /b 2
)
echo === HEAD object after rewrite ===
git cat-file -p HEAD
endlocal
exit /b 0
:usage
echo usage: gald3r_clean_commit.bat ^<INITIAL^|FOLLOWUP^> ^<message_file^>
exit /b 1
