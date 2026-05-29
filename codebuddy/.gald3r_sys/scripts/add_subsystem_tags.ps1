# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    Bulk-tag SKILL.md files with subsystem_memberships: frontmatter.

.DESCRIPTION
    T1457 Phase 1b -- Bulk Tagging Strategy implementation.

    Scans all SKILL.md files under the given root path and adds
    subsystem_memberships: to any file whose frontmatter does not already
    have it. Assignment is made via a pattern-match lookup table (skill slug
    -> L1 group list). Unrecognized slugs receive [UNCATEGORIZED].

    After running, review the UNCATEGORIZED report and re-run with corrected
    overrides in the -Override hashtable.

.PARAMETER RootPath
    Path to the .gald3r_sys/skills directory (or any parent). All SKILL.md
    files found recursively are processed.

.PARAMETER Apply
    Actually write changes. Without this flag, runs dry-run only.

.PARAMETER ShowAll
    Show all files in the report, not just changed/uncategorized ones.

.PARAMETER Override
    Hashtable of { "skill-slug" = @("GROUP1","GROUP2") } to override the
    built-in lookup table for specific skills.

.EXAMPLE
    .\add_subsystem_tags.ps1 -RootPath ".\gald3r_template\.gald3r_sys\skills"
    (dry-run -- shows what would be changed)

.EXAMPLE
    .\add_subsystem_tags.ps1 -RootPath ".\gald3r_template\.gald3r_sys\skills" -Apply
    (writes subsystem_memberships: to all untagged SKILL.md files)

.NOTES
    T1457 | gald3r_templates | 2026-05-26
    Source of truth for L1 groups: PRODUCT_SYSTEMS.md (defined_groups: frontmatter)
    This script is the bootstrapper -- it runs before PRODUCT_SYSTEMS.md exists.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RootPath = ".",

    [switch]$Apply,
    [switch]$ShowAll,

    [hashtable]$Override = @{}
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------
# L1 Group Definitions (authoritative list -- mirrors PRODUCT_SYSTEMS.md defined_groups:)
# ---------------------------------------------------------
$DEFINED_GROUPS = @(
    'LOGGING_SYSTEM',
    'MEMORY_AND_KNOWLEDGE',
    'TASK_MANAGEMENT',
    'BUG_AND_QUALITY',
    'WORKSPACE_COORDINATION',
    'PROJECT_IDENTITY_SETUP',
    'PLATFORM_INTEGRATION',
    'AGENT_ORCHESTRATION',
    'RELEASE_AND_VERSIONING',
    'VAULT_AND_RESEARCH',
    'UI_AND_OUTPUT',
    'SECURITY_AND_COMPLIANCE'
)

# ---------------------------------------------------------
# Pattern Lookup Table -- skill-slug -> L1 groups
# Order: most specific first. Slug = parent directory name of SKILL.md.
# ---------------------------------------------------------
$SKILL_GROUPS = [ordered]@{
    # PLATFORM_INTEGRATION -- all platform-specific and CLI skills
    'g-skl-platform-aider'      = @('PLATFORM_INTEGRATION')
    'g-skl-platform-augment'    = @('PLATFORM_INTEGRATION')
    'g-skl-platform-claude'     = @('PLATFORM_INTEGRATION')
    'g-skl-platform-cline'      = @('PLATFORM_INTEGRATION')
    'g-skl-platform-codex'      = @('PLATFORM_INTEGRATION')
    'g-skl-platform-copilot'    = @('PLATFORM_INTEGRATION')
    'g-skl-platform-crawl'      = @('PLATFORM_INTEGRATION')
    'g-skl-platform-cursor'     = @('PLATFORM_INTEGRATION')
    'g-skl-platform-gemini'     = @('PLATFORM_INTEGRATION')
    'g-skl-platform-goose'      = @('PLATFORM_INTEGRATION')
    'g-skl-platform-junie'      = @('PLATFORM_INTEGRATION')
    'g-skl-platform-kiro'       = @('PLATFORM_INTEGRATION')
    'g-skl-platform-kiro-cli'   = @('PLATFORM_INTEGRATION')
    'g-skl-platform-mistral'    = @('PLATFORM_INTEGRATION')
    'g-skl-platform-openclaw'   = @('PLATFORM_INTEGRATION')
    'g-skl-platform-opencode'   = @('PLATFORM_INTEGRATION')
    'g-skl-platform-openhands'  = @('PLATFORM_INTEGRATION')
    'g-skl-platform-qwen'       = @('PLATFORM_INTEGRATION')
    'g-skl-platform-replit'     = @('PLATFORM_INTEGRATION')
    'g-skl-platform-roo'        = @('PLATFORM_INTEGRATION')
    'g-skl-platform-subq'       = @('PLATFORM_INTEGRATION')
    'g-skl-platform-warp'       = @('PLATFORM_INTEGRATION')
    'g-skl-platform-windsurf'   = @('PLATFORM_INTEGRATION')
    'g-skl-cli-claude'          = @('PLATFORM_INTEGRATION')
    'g-skl-cli-codex'           = @('PLATFORM_INTEGRATION')
    'g-skl-cli-copilot'         = @('PLATFORM_INTEGRATION')
    'g-skl-cli-cursor'          = @('PLATFORM_INTEGRATION')
    'g-skl-cli-gemini'          = @('PLATFORM_INTEGRATION')
    'g-skl-cli-jcode'           = @('PLATFORM_INTEGRATION')
    'g-skl-cli-opencode'        = @('PLATFORM_INTEGRATION')

    # WORKSPACE_COORDINATION -- all wpac-* and workspace skills
    'g-skl-workspace'           = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-adopt'          = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-ask'            = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-claim'          = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-move'           = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-notify'         = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-order'          = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-read'           = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-send-to'        = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-spawn'          = @('WORKSPACE_COORDINATION')
    'g-skl-wpac-sync'           = @('WORKSPACE_COORDINATION')

    # MEMORY_AND_KNOWLEDGE
    'g-skl-memory'              = @('MEMORY_AND_KNOWLEDGE')
    'g-skl-learn'               = @('MEMORY_AND_KNOWLEDGE')
    'g-skl-vault'               = @('MEMORY_AND_KNOWLEDGE', 'VAULT_AND_RESEARCH')
    'g-skl-muninn'              = @('MEMORY_AND_KNOWLEDGE')
    'g-skl-graphify'            = @('MEMORY_AND_KNOWLEDGE')
    'g-skl-compress-memory'     = @('MEMORY_AND_KNOWLEDGE')
    'g-skl-knowledge-refresh'   = @('MEMORY_AND_KNOWLEDGE', 'VAULT_AND_RESEARCH')
    'g-skl-context-builder'     = @('MEMORY_AND_KNOWLEDGE', 'TASK_MANAGEMENT')

    # TASK_MANAGEMENT
    'g-skl-tasks'               = @('TASK_MANAGEMENT')
    'g-skl-dependency-graph'    = @('TASK_MANAGEMENT')
    'g-skl-status'              = @('TASK_MANAGEMENT')

    # BUG_AND_QUALITY
    'g-skl-bugs'                = @('BUG_AND_QUALITY')
    'g-skl-qa'                  = @('BUG_AND_QUALITY')
    'g-skl-code-review'         = @('BUG_AND_QUALITY')
    'g-skl-review'              = @('BUG_AND_QUALITY')
    'g-skl-swot-review'         = @('BUG_AND_QUALITY')
    'g-skl-verify-ladder'       = @('BUG_AND_QUALITY')
    'g-skl-test'                = @('BUG_AND_QUALITY')
    'g-skl-auto-triage'         = @('BUG_AND_QUALITY', 'AGENT_ORCHESTRATION')
    'g-skl-api-doc-gen'         = @('BUG_AND_QUALITY', 'PLATFORM_INTEGRATION')
    'g-skl-security-scan'       = @('BUG_AND_QUALITY', 'SECURITY_AND_COMPLIANCE')

    # SECURITY_AND_COMPLIANCE
    'g-skl-compliance'          = @('SECURITY_AND_COMPLIANCE')
    'g-skl-dependency-audit'    = @('SECURITY_AND_COMPLIANCE', 'BUG_AND_QUALITY')

    # PROJECT_IDENTITY_SETUP
    'g-skl-setup'               = @('PROJECT_IDENTITY_SETUP')
    'g-skl-project'             = @('PROJECT_IDENTITY_SETUP')
    'g-skl-constraints'         = @('PROJECT_IDENTITY_SETUP')
    'g-skl-tier-setup'          = @('PROJECT_IDENTITY_SETUP')
    'g-skl-plan'                = @('PROJECT_IDENTITY_SETUP')
    'g-skl-features'            = @('PROJECT_IDENTITY_SETUP')
    'g-skl-prds'                = @('PROJECT_IDENTITY_SETUP')
    'g-skl-subsystems'          = @('PROJECT_IDENTITY_SETUP')
    'g-skl-subsystem-graph'     = @('PROJECT_IDENTITY_SETUP')
    'g-skl-ideas'               = @('PROJECT_IDENTITY_SETUP', 'VAULT_AND_RESEARCH')
    'g-skl-res-apply'           = @('PROJECT_IDENTITY_SETUP', 'VAULT_AND_RESEARCH')
    'g-skl-medic'               = @('PROJECT_IDENTITY_SETUP', 'AGENT_ORCHESTRATION')
    'g-skl-medkit'              = @('PROJECT_IDENTITY_SETUP', 'AGENT_ORCHESTRATION')
    'g-skl-gald3r-optimize'     = @('PROJECT_IDENTITY_SETUP', 'AGENT_ORCHESTRATION')

    # RELEASE_AND_VERSIONING
    'g-skl-git-commit'          = @('RELEASE_AND_VERSIONING')
    'g-skl-github-pr'           = @('RELEASE_AND_VERSIONING')
    'g-skl-ship'                = @('RELEASE_AND_VERSIONING')
    'g-skl-release'             = @('RELEASE_AND_VERSIONING')
    'g-skl-template-export'     = @('RELEASE_AND_VERSIONING')

    # VAULT_AND_RESEARCH
    'g-skl-recon-docs'          = @('VAULT_AND_RESEARCH')
    'g-skl-recon-file'          = @('VAULT_AND_RESEARCH')
    'g-skl-recon-repo'          = @('VAULT_AND_RESEARCH')
    'g-skl-recon-url'           = @('VAULT_AND_RESEARCH')
    'g-skl-recon-yt'            = @('VAULT_AND_RESEARCH')
    'g-skl-res-deep'            = @('VAULT_AND_RESEARCH')
    'g-skl-res-review'          = @('VAULT_AND_RESEARCH')
    'g-skl-crawl'               = @('VAULT_AND_RESEARCH')
    'g-skl-yt-video-analysis'   = @('VAULT_AND_RESEARCH')
    'g-skl-monitor'             = @('VAULT_AND_RESEARCH')
    'g-skl-crr'                 = @('VAULT_AND_RESEARCH', 'AGENT_ORCHESTRATION')

    # UI_AND_OUTPUT
    'g-skl-html-output'         = @('UI_AND_OUTPUT')
    'g-skl-json-output'         = @('UI_AND_OUTPUT')
    'g-skl-toon-output'         = @('UI_AND_OUTPUT')
    'g-skl-theme-editor'        = @('UI_AND_OUTPUT')
    'g-skl-comfyui'             = @('UI_AND_OUTPUT')
    'g-skl-design'              = @('UI_AND_OUTPUT')

    # AGENT_ORCHESTRATION
    'g-skl-browser-use'         = @('AGENT_ORCHESTRATION')
    'g-skl-delegate'            = @('AGENT_ORCHESTRATION')
    'g-skl-curator'             = @('AGENT_ORCHESTRATION')
    'g-skl-keep-it-simple'      = @('AGENT_ORCHESTRATION')
    'g-skl-oracle'              = @('AGENT_ORCHESTRATION')
    'g-skl-marketing'           = @('AGENT_ORCHESTRATION')
}

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

function Get-SkillSlug([string]$SkillPath) {
    # Prefer the parent directory name over anything else
    return (Split-Path (Split-Path $SkillPath -Parent) -Leaf)
}

function Get-AssignedGroups([string]$Slug) {
    if ($Override.ContainsKey($Slug)) { return $Override[$Slug] }
    if ($SKILL_GROUPS.Contains($Slug)) { return $SKILL_GROUPS[$Slug] }

    # Pattern fallback for slugs not in table
    if ($Slug -match '^g-skl-platform-' -or $Slug -match '^g-skl-cli-') {
        return @('PLATFORM_INTEGRATION')
    }
    if ($Slug -match '^g-skl-wpac-') {
        return @('WORKSPACE_COORDINATION')
    }
    if ($Slug -match '^g-skl-recon-') {
        return @('VAULT_AND_RESEARCH')
    }
    if ($Slug -match '^g-skl-res-') {
        return @('VAULT_AND_RESEARCH')
    }

    return @('UNCATEGORIZED')
}

function Test-HasFrontmatter([string]$Content) {
    return $Content -match '(?ms)^---\r?\n.*?\r?\n---'
}

function Get-FrontmatterField([string]$Content, [string]$Field) {
    if ($Content -match "(?m)^${Field}:\s*(.+)$") {
        return $Matches[1].Trim()
    }
    return $null
}

function Test-HasField([string]$Content, [string]$Field) {
    return $Content -match "(?m)^${Field}:"
}

function Format-YamlList([string[]]$Items) {
    if ($Items.Count -eq 1) {
        return "[$($Items[0])]"
    }
    $inner = ($Items | ForEach-Object { $_ }) -join ', '
    return "[$inner]"
}

function Add-FrontmatterField([string]$Content, [string]$Field, [string]$Value) {
    # Insert field just before the closing --- of the frontmatter
    $pattern = '(?ms)(^---\r?\n.*?)(^---)'
    if ($Content -match $pattern) {
        $header = $Matches[1]
        $rest = $Content.Substring($Matches[0].Length)
        return "${header}${Field}: ${Value}`n---${rest}"
    }
    return $Content
}

function Add-FrontmatterBlock([string]$Content, [string]$Field, [string]$Value) {
    # Prepend a minimal frontmatter block if none exists
    return "---`n${Field}: ${Value}`n---`n`n${Content}"
}

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

$skillFiles = Get-ChildItem -Path $RootPath -Recurse -Filter "SKILL.md" -File |
    Where-Object { $_.FullName -notmatch '\\node_modules\\' }

$report = [System.Collections.Generic.List[psobject]]::new()
$changedCount = 0
$skippedCount = 0
$uncategorizedCount = 0

foreach ($file in $skillFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $slug = Get-SkillSlug $file.FullName
    $groups = Get-AssignedGroups $slug
    $isUncategorized = $groups -contains 'UNCATEGORIZED'

    $hasGroups = Test-HasField $content 'subsystem_memberships'

    $status = if ($hasGroups) { 'ALREADY_TAGGED' }
              elseif ($isUncategorized) { 'UNCATEGORIZED' }
              else { 'WILL_TAG' }

    if ($isUncategorized) { $uncategorizedCount++ }

    $entry = [pscustomobject]@{
        Slug    = $slug
        Status  = $status
        Groups  = ($groups -join ', ')
        File    = $file.FullName
    }
    $report.Add($entry)

    if ($hasGroups) {
        $skippedCount++
        continue
    }

    $yamlValue = Format-YamlList $groups
    $newContent = if (Test-HasFrontmatter $content) {
        Add-FrontmatterField $content 'subsystem_memberships' $yamlValue
    } else {
        Add-FrontmatterBlock $content 'subsystem_memberships' $yamlValue
    }

    if ($Apply) {
        Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8 -NoNewline
        $changedCount++
    } else {
        $changedCount++
    }
}

# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

$displayMode = if ($Apply) { "APPLIED" } else { "DRY-RUN" }
Write-Host ""
Write-Host "+==============================================================+" -ForegroundColor Cyan
Write-Host "|  add_subsystem_tags.ps1 -- Subsystem Membership Tagger       |" -ForegroundColor Cyan
Write-Host "|  Mode: $($displayMode.PadRight(55))|" -ForegroundColor Cyan
Write-Host "+==============================================================+" -ForegroundColor Cyan
Write-Host ""

if ($ShowAll -or $uncategorizedCount -gt 0) {
    $showItems = if ($ShowAll) { $report } else {
        $report | Where-Object { $_.Status -ne 'ALREADY_TAGGED' }
    }
    foreach ($item in $showItems) {
        $color = switch ($item.Status) {
            'ALREADY_TAGGED' { 'DarkGray' }
            'UNCATEGORIZED'  { 'Yellow' }
            'WILL_TAG'       { 'Green' }
            default          { 'White' }
        }
        Write-Host ("  [{0,-15}]  {1,-35}  {2}" -f $item.Status, $item.Slug, $item.Groups) -ForegroundColor $color
    }
    Write-Host ""
}

Write-Host "  Total skills found:   $($skillFiles.Count)" -ForegroundColor White
Write-Host "  Already tagged:       $skippedCount" -ForegroundColor DarkGray
Write-Host "  $(if ($Apply) {'Tagged:'} else {'Would tag:'})          $changedCount" -ForegroundColor Green
Write-Host "  UNCATEGORIZED:        $uncategorizedCount" -ForegroundColor Yellow
Write-Host ""

if ($uncategorizedCount -gt 0) {
    Write-Host "  ? UNCATEGORIZED SKILLS require manual group assignment." -ForegroundColor Yellow
    Write-Host "    Re-run with -Override @{'slug'=@('GROUP')} to fix them." -ForegroundColor Yellow
    Write-Host ""
}

if (-not $Apply) {
    Write-Host "  ? Add -Apply to write changes." -ForegroundColor Cyan
}

# Output machine-readable summary for verification gate
$summary = [pscustomobject]@{
    Mode              = $displayMode
    TotalSkills       = $skillFiles.Count
    AlreadyTagged     = $skippedCount
    Tagged            = $changedCount
    Uncategorized     = $uncategorizedCount
    UncategorizedList = @($report | Where-Object { $_.Status -eq 'UNCATEGORIZED' } | Select-Object -ExpandProperty Slug)
}
$reportPath = Join-Path (Split-Path (Resolve-Path $RootPath).Path -Parent) "add_subsystem_tags_report.json"
$summary | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportPath -Encoding UTF8
