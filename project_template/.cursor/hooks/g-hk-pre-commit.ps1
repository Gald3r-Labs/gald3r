#!/usr/bin/env pwsh
# @subsystems: SECURITY_AND_COMPLIANCE
<#
.SYNOPSIS
    gald3r pre-commit sanity hook (opt-in).

.DESCRIPTION
    Checks staged changes for: secrets, large files (>5 MB), and gald3r task sync drift.

    BLOCK items exit 1 (commit is halted).
    WARN items exit 0 with a warning (commit proceeds).

    INSTALLATION (opt-in only):
        git config core.hooksPath .cursor/hooks

    REMOVAL:
        git config --unset core.hooksPath

    This script is safe to run manually: .\cursor\hooks\g-hk-pre-commit.ps1

.NOTES
    T600 hook contract acknowledgement (B-4 — block_on_failure):

    This hook already speaks the BLOCK/WARN dialect that the T600 design
    contract describes:
        exit 1   = BLOCK   (the commit is aborted)
        exit 0   = ALLOW or WARN (the commit proceeds; warnings logged to stdout)

    A `-BlockOnFailure` flag is accepted but is a no-op here because the
    exit-code semantics already match the contract — there is no softer
    "warn-only" mode to flip into. Future hooks that have both warn and
    block modes (e.g., a generic linter wrapper) should branch on the flag.

    See: docs/20260506_000000_Cursor_T600_HOOK_SYSTEM_EXTENSIONS.md §3.
#>

[CmdletBinding()]
param(
    [switch]$BlockOnFailure
)

# Bypass switch: mirrors the T600 §3.3 user override path. Honored even
# though this specific hook is always-block; surfacing it keeps semantics
# uniform across the hook family.
if ($env:GALD3R_HOOK_BYPASS -eq '1') {
    Write-Host "gald3r pre-commit: BYPASS active (GALD3R_HOOK_BYPASS=1) — treating BLOCK as WARN." -ForegroundColor Yellow
    $script:Gald3rBypass = $true
} else {
    $script:Gald3rBypass = $false
}

$ErrorActionPreference = "SilentlyContinue"

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../../")).Path
}
$commonPath = Join-Path $repoRoot ".cursor/skills/g-skl-git-commit/scripts/gald3r_git_sanity_common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
}

$block = $false
$warns = @()

Write-Host ""
Write-Host "gald3r pre-commit sanity check" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# --- 1. SECRETS CHECK (BLOCK) ---
$secretPatterns = @()
if (Get-Command Get-Gald3rSecretPatterns -ErrorAction SilentlyContinue) {
    $secretPatterns = @(Get-Gald3rSecretPatterns)
}
if ($secretPatterns.Count -eq 0) {
    $secretPatterns = @(
        "sk-[a-zA-Z0-9]{20,}",
        "Bearer\s+[a-zA-Z0-9._\-]{20,}",
        "AKIA[A-Z0-9]{16}",
        "password\s*=\s*\S+",
        "api_key\s*=\s*\S+",
        "secret_key\s*=\s*\S+",
        "private_key\s*=\s*\S+",
        "-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
}

$diff = git diff --cached 2>$null
$secretHits = @()
foreach ($pat in $secretPatterns) {
    $hits = $diff | Select-String -Pattern $pat
    if ($hits) {
        $secretHits += $hits | ForEach-Object { "  $($_.Line.Trim())" } | Select-Object -First 3
    }
}

# Also check for staged .env files
$stagedFiles = git diff --cached --name-only 2>$null
$envFiles = $stagedFiles | Where-Object { $_ -match "^\.env(\..*)?$" }
if ($envFiles) {
    $secretHits += $envFiles | ForEach-Object { "  [.env file staged: $_]" }
}

if ($secretHits.Count -gt 0) {
    Write-Host "BLOCK: Secrets detected in staged changes:" -ForegroundColor Red
    $secretHits | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    Write-Host "  -> Remove secrets before committing. Use environment variables or a vault." -ForegroundColor Red
    $block = $true
} else {
    Write-Host "Secrets:     PASS" -ForegroundColor Green
}

# --- 2. LARGE FILE CHECK (WARN) ---
$largeFiles = $stagedFiles | Where-Object {
    (Test-Path $_) -and ((Get-Item $_ -ErrorAction SilentlyContinue).Length -gt 5MB)
}

if ($largeFiles) {
    $sizeWarn = "WARN: Staged files > 5 MB detected:`n" + ($largeFiles | ForEach-Object {
        $sizeKb = [math]::Round((Get-Item $_).Length / 1KB, 0)
        "  $_ ($sizeKb KB)"
    } | Out-String)
    $warns += $sizeWarn
    Write-Host "Large files: WARN — $($largeFiles.Count) file(s) > 5 MB" -ForegroundColor Yellow
} else {
    Write-Host "Large files: PASS" -ForegroundColor Green
}

# --- 3. C-026 WORKTREE TASKS.MD GUARD (BLOCK) ---
# Bucket agents in worktrees must never write TASKS.md directly (C-026).
# Only the coordinator in the primary worktree is allowed to write the index.
$tasksMdStagedCheck = $stagedFiles | Where-Object { $_ -match "\.gald3r[/\\]TASKS\.md$|^\.gald3r/TASKS\.md$" }
if ($tasksMdStagedCheck) {
    # Detect if we are in a non-primary worktree
    $worktreeList = git worktree list 2>$null
    $primaryWorktree = ($worktreeList | Select-String -Pattern "\[HEAD\]|\[main\]|\[dev\]" | Select-Object -First 1)?.Line
    $cwdNorm = (Resolve-Path .).Path.TrimEnd('\/')
    $primaryNorm = if ($primaryWorktree) { ($primaryWorktree -split '\s+')[0].TrimEnd('\/') } else { $cwdNorm }

    $inNonPrimaryWorktree = ($worktreeList.Count -gt 1) -and ($cwdNorm -ne $primaryNorm) -and
                            -not ($worktreeList | Where-Object { $_ -match [regex]::Escape($cwdNorm) -and $_ -match "\[" })

    if ($inNonPrimaryWorktree) {
        Write-Host ""
        Write-Host "BLOCK: C-026 — TASKS.md is coordinator-owned." -ForegroundColor Red
        Write-Host "  Bucket agents in worktrees must NOT write .gald3r/TASKS.md." -ForegroundColor Red
        Write-Host "  Write your individual task file only (tasks/open/task{id}_*.md)." -ForegroundColor Red
        Write-Host "  The coordinator writes TASKS.md at reconciliation time." -ForegroundColor Red
        Write-Host "  See .gald3r/CONSTRAINTS.md C-026 for details." -ForegroundColor Red
        if ($script:Gald3rBypass) {
            $warns += "C-026 BYPASS: TASKS.md written from worktree — coordinator must reconcile."
            Write-Host "  BYPASS active — proceeding with warning." -ForegroundColor Yellow
        } else {
            $block = $true
        }
    }
}

# --- 3. gald3r SYNC DRIFT CHECK (WARN) ---
if (Test-Path ".gald3r") {
    $tasksMdStaged = $stagedFiles | Where-Object { $_ -match "TASKS\.md" }
    $taskFilesStaged = $stagedFiles | Where-Object { $_ -match "\.gald3r[/\\]tasks[/\\]" }

    if ($tasksMdStaged -and -not $taskFilesStaged) {
        $warns += "WARN: .gald3r/TASKS.md is staged but no tasks/ files are staged. Run @g-task-sync-check."
        Write-Host "gald3r sync: WARN — TASKS.md staged without tasks/ files" -ForegroundColor Yellow
    } elseif ($taskFilesStaged -and -not $tasksMdStaged) {
        $warns += "WARN: tasks/ files staged but .gald3r/TASKS.md is not. Run @g-task-sync-check."
        Write-Host "gald3r sync: WARN — tasks/ files staged without TASKS.md" -ForegroundColor Yellow
    } else {
        Write-Host "gald3r sync: PASS" -ForegroundColor Green
    }
} else {
    Write-Host "gald3r sync: SKIP (no .gald3r/ in this repo)" -ForegroundColor DarkGray
}

# --- 4. PROTECTED FILES ALLOWLIST (BLOCK) ---
# Enforces g-rl-02 § "Protected Files" — never commit these even by mistake.
# Each pattern matches against the staged file path (any depth). Bypass via
# $env:GALD3R_HOOK_BYPASS = '1' (rare; mainly for emergency parity fixes).
$protectedPatterns = @(
    '^\.agent/'
    '^\.claude/'
    '^\.codex/'
    '^\.cursor/'
    '^\.opencode/'
    '^\.copilot/'
    '^\.gald3r/'
    '^\.project_template/'
    '^temp_docs/'
    '^temp_scripts/'
    '^AGENTS\.md$'
    '^CLAUDE\.md$'
    '^GEMINI\.md$'
    '^GUARDRAILS\.md$'
    '^\.env(\..*)?$'
    '^\.mcp\.json$'
)
$protectedHits = @()
foreach ($f in $stagedFiles) {
    $rel = ($f -replace '\\', '/')
    foreach ($pat in $protectedPatterns) {
        if ($rel -match $pat) {
            $protectedHits += "  $rel  (matches /$pat/)"
            break
        }
    }
}
if ($protectedHits.Count -gt 0) {
    Write-Host "Protected files: BLOCK — $($protectedHits.Count) staged path(s) match the Protected Files allowlist:" -ForegroundColor Red
    $protectedHits | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    Write-Host "  -> Unstage with: git reset HEAD <file>. See .claude/rules/g-rl-02-git_workflow.md § 'Protected Files'." -ForegroundColor Red
    $block = $true
} else {
    Write-Host "Protected files: PASS" -ForegroundColor Green
}

# --- 5. STUB / TODO ANNOTATION (BLOCK) ---
# Enforces g-rl-34 — bare # TODO / pass / raise NotImplementedError in staged
# diff added lines must carry the `TODO[TASK-X->TASK-Y]` annotation form, OR
# the surrounding context already carries the marker on a nearby line. WARN
# severity for `pass` (very noisy across legit ABC methods). BLOCK for bare
# TODO/FIXME/NotImplementedError.
$stubBlockPatterns = @(
    '^\+\s*(#|//|--)\s*(TODO|FIXME)\b'
    '^\+\s*raise\s+NotImplementedError'
    '^\+\s*throw\s+new\s+Error\(\s*[\"`'']?not\s+implemented'
)
$annotationRegex = 'TODO\s*\[\s*TASK[-_]\d+\s*[-→>]+\s*TASK[-_]\d+\s*\]'
$stubHits = @()
if ($diff) {
    $diffLines = $diff -split "`r?`n"
    $currentFile = ""
    for ($i = 0; $i -lt $diffLines.Count; $i++) {
        $line = $diffLines[$i]
        if ($line -match '^\+\+\+\s+b/(.+)$') {
            $currentFile = $matches[1]
            continue
        }
        if ($line -match '^\+' -and $line -notmatch '^\+\+\+') {
            foreach ($pat in $stubBlockPatterns) {
                if ($line -match $pat) {
                    # Check if THIS line already carries the annotation.
                    if ($line -match $annotationRegex) { continue }
                    # Look at +/- 2 lines for the annotation on the same hunk.
                    $hasAnnotation = $false
                    for ($j = [Math]::Max(0, $i - 2); $j -le [Math]::Min($diffLines.Count - 1, $i + 2); $j++) {
                        if ($j -eq $i) { continue }
                        if ($diffLines[$j] -match $annotationRegex) { $hasAnnotation = $true; break }
                    }
                    if (-not $hasAnnotation) {
                        $trimmed = $line.Substring(1).TrimEnd()
                        if ($trimmed.Length -gt 100) { $trimmed = $trimmed.Substring(0, 100) + '…' }
                        $stubHits += "  ${currentFile}: $trimmed"
                    }
                    break
                }
            }
        }
    }
}
if ($stubHits.Count -gt 0) {
    Write-Host "Stub annotation: BLOCK — $($stubHits.Count) bare TODO/NotImplementedError without TODO[TASK-X->TASK-Y] form:" -ForegroundColor Red
    $stubHits | Select-Object -First 10 | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    if ($stubHits.Count -gt 10) {
        Write-Host "  ... and $($stubHits.Count - 10) more" -ForegroundColor Red
    }
    Write-Host "  -> Annotate each stub: TODO[TASK-<current>->TASK-<followup>]: <description>" -ForegroundColor Red
    Write-Host "     See .claude/rules/g-rl-34-todo_completion_gate.md." -ForegroundColor Red
    $block = $true
} else {
    Write-Host "Stub annotation: PASS" -ForegroundColor Green
}

Write-Host ""

# --- RESULT ---
if ($block) {
    if ($script:Gald3rBypass) {
        Write-Host "Pre-commit check: BLOCK conditions found, but BYPASS is active — commit will proceed." -ForegroundColor Yellow
        Write-Host ""
        exit 0
    }
    Write-Host "Pre-commit check: BLOCKED — fix issues above before committing." -ForegroundColor Red
    Write-Host ""
    exit 1
}

if ($warns.Count -gt 0) {
    Write-Host "Pre-commit check: WARNINGS (commit will proceed)" -ForegroundColor Yellow
    $warns | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    Write-Host ""
    exit 0
}

Write-Host "Pre-commit check: ALL PASS" -ForegroundColor Green
Write-Host ""
exit 0
