# g-hk-component-tag-check.ps1 - Git pre-commit hook: enforce subsystem tagging on .gald3r_sys components
# @subsystems: PROJECT_IDENTITY_SETUP
#
# Blocks commits that add new component files to .gald3r_sys/ without subsystem tagging.
# Run modes:
#   - git pre-commit hook (via core.hooksPath): called with no arguments, no stdin
#   - Direct check:  pwsh g-hk-component-tag-check.ps1 [-WarnOnly] [-Staged]
#
# Exit codes: 0 = pass (allow commit), 1 = fail (block commit)

param(
    [switch]$WarnOnly,    # Print findings but do not block (exit 0 always)
    [switch]$Staged       # Explicit staged mode (default when called from git)
)

$ErrorActionPreference = "Stop"

# Determine repo root
$repoRoot = & git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Host "[tag-check] Not inside a git repo — skipping." -ForegroundColor Yellow
    exit 0
}

# Directories in .gald3r_sys that require tagging
$markdownDirs = @("skills", "commands", "agents", "rules")
$scriptDirs   = @("hooks", "scripts")
$galdSys      = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys")

# Get staged files (ACM: Added, Copied, Modified)
$stagedFiles = & git diff --cached --name-only --diff-filter=ACM 2>$null
if (-not $stagedFiles) {
    exit 0
}

$violations = [System.Collections.Generic.List[string]]::new()

foreach ($relPath in $stagedFiles) {
    $fullPath = [System.IO.Path]::Combine($repoRoot, $relPath.Replace("/", "\"))
    if (-not [System.IO.File]::Exists($fullPath)) { continue }

    # Only check files under .gald3r_sys
    if (-not $relPath.StartsWith(".gald3r_sys/") -and -not $relPath.StartsWith(".gald3r_sys\")) { continue }

    $ext = [System.IO.Path]::GetExtension($fullPath).ToLower()

    if ($ext -eq ".md") {
        # Determine if it belongs to a taggable directory
        $inTaggableDir = $false
        foreach ($d in $markdownDirs) {
            if ($relPath -match [regex]::Escape(".gald3r_sys/$d/") -or $relPath -match [regex]::Escape(".gald3r_sys\$d\")) {
                $inTaggableDir = $true
                break
            }
        }
        if (-not $inTaggableDir) { continue }

        $content = [System.IO.File]::ReadAllText($fullPath)
        if ($content -notmatch "subsystem_memberships\s*:") {
            $violations.Add("MISSING subsystem_memberships: in $relPath")
        }
    }
    elseif ($ext -eq ".ps1") {
        $inTaggableDir = $false
        foreach ($d in $scriptDirs) {
            if ($relPath -match [regex]::Escape(".gald3r_sys/$d/") -or $relPath -match [regex]::Escape(".gald3r_sys\$d\")) {
                $inTaggableDir = $true
                break
            }
        }
        if (-not $inTaggableDir) { continue }

        # Check first 15 lines for @subsystems comment
        $lines = [System.IO.File]::ReadAllLines($fullPath) | Select-Object -First 15
        $hasTag = $lines | Where-Object { $_ -match "^#\s*@subsystems\s*:" }
        if (-not $hasTag) {
            $violations.Add("MISSING '# @subsystems:' comment in first 15 lines: $relPath")
        }
    }
}

if ($violations.Count -eq 0) {
    exit 0
}

# Report violations
Write-Host "" -ForegroundColor Red
Write-Host "=== [g-hk-component-tag-check] SUBSYSTEM TAGGING VIOLATIONS ===" -ForegroundColor Red
Write-Host ""
foreach ($v in $violations) {
    Write-Host "  !! $v" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Each .gald3r_sys component needs:" -ForegroundColor Cyan
Write-Host "  Markdown (.md):  'subsystem_memberships: [GROUP]' in YAML frontmatter" -ForegroundColor Cyan
Write-Host "  PowerShell (.ps1): '# @subsystems: GROUP' in first 15 lines" -ForegroundColor Cyan
Write-Host ""
Write-Host "Valid groups: LOGGING_SYSTEM | MEMORY_AND_KNOWLEDGE | TASK_MANAGEMENT |" -ForegroundColor Cyan
Write-Host "  BUG_AND_QUALITY | WORKSPACE_COORDINATION | PROJECT_IDENTITY_SETUP |" -ForegroundColor Cyan
Write-Host "  PLATFORM_INTEGRATION | AGENT_ORCHESTRATION | RELEASE_AND_VERSIONING |" -ForegroundColor Cyan
Write-Host "  VAULT_AND_RESEARCH | UI_AND_OUTPUT | SECURITY_AND_COMPLIANCE | UNGROUPED" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run @g-skill-new / @g-command-new / @g-rule-new to scaffold with tags pre-filled." -ForegroundColor Green
Write-Host "Or add tags manually and re-stage the files." -ForegroundColor Green
Write-Host ""

if ($WarnOnly) {
    exit 0
}
exit 1
