#Requires -Version 5.1
# @subsystems: SECURITY_AND_COMPLIANCE
<#
.SYNOPSIS
    Install gald3r git hooks (T1428) into the target repository.

.DESCRIPTION
    Points the repo's git hooks at the tracked .githooks/ directory by setting
    `core.hooksPath`. This makes the pre-commit encoding-normalization hook
    (.githooks/pre-commit) active on every clone without writing into the
    untracked .git/hooks/ directory.

    Why core.hooksPath instead of copying into .git/hooks/?
      - .git/hooks/ is never tracked by git, so a fresh clone gets no hook.
      - The .githooks/ directory IS tracked (shipped by the install scaffold),
        so a single `core.hooksPath .githooks` makes the hook portable.

    Idempotent: re-running just re-sets the config value.

.PARAMETER RepoRoot
    Repository root. Defaults to the current directory.

.PARAMETER Uninstall
    Remove the gald3r hooks path (git config --unset core.hooksPath).
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

Push-Location $RepoRoot
try {
    & git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "install_git_hooks: '$RepoRoot' is not a git repository. Skipping."
        return
    }

    if ($Uninstall) {
        & git config --unset core.hooksPath 2>$null
        Write-Host "gald3r git hooks: uninstalled (core.hooksPath unset)" -ForegroundColor DarkYellow
        return
    }

    $hooksDir = Join-Path $RepoRoot '.githooks'
    if (-not (Test-Path $hooksDir)) {
        Write-Warning "install_git_hooks: '.githooks/' not found at $RepoRoot. Run gald3r setup first."
        return
    }

    & git config core.hooksPath .githooks
    Write-Host "gald3r git hooks: installed (core.hooksPath -> .githooks)" -ForegroundColor Green
    Write-Host "  pre-commit will normalize encodings (UTF-8 BOM for .ps1, no-BOM + LF otherwise)." -ForegroundColor DarkGray
    Write-Host "  Disable with: install_git_hooks.ps1 -Uninstall" -ForegroundColor DarkGray
}
finally {
    Pop-Location
}
