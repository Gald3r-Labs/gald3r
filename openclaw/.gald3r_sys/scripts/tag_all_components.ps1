# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    Tag ALL .gald3r_sys component files with subsystem_memberships: (T1457 expansion).

.DESCRIPTION
    Extends add_subsystem_tags.ps1 to cover Commands, Agents, Rules, Hooks (.ps1),
    and Scripts (.ps1) -- not just SKILL.md files.

    Tag mechanisms by file type:
      - Commands (.md, no frontmatter)  -- injects --- frontmatter block at top
      - Agents   (.md, has frontmatter) -- appends subsystem_memberships: to YAML block
      - Rules    (.md, has frontmatter) -- appends subsystem_memberships: to YAML block
      - Hooks    (.ps1)                 -- injects "# @subsystems: GROUP" near top
      - Scripts  (.ps1)                 -- same as hooks

    Assignment is made via slug-based lookup tables. Unrecognized slugs are tagged
    [UNCATEGORIZED] and listed in the report.

.PARAMETER RootPath
    Root of the .gald3r_sys folder to scan (defaults to parent of this script).

.PARAMETER Apply
    Write changes. Without this flag, dry-run only.

.PARAMETER ComponentTypes
    Comma-separated list of component types to process.
    Valid values: commands, agents, rules, hooks, scripts (default: all)

.EXAMPLE
    .\tag_all_components.ps1
    # Dry-run -- shows what would change

.EXAMPLE
    .\tag_all_components.ps1 -Apply
    # Writes subsystem tags to all untagged component files

.NOTES
    Part of T1457 expansion -- full system component map.
    Companion to add_subsystem_tags.ps1 (skills only).
    Source of truth for L1 groups: PRODUCT_SYSTEMS.md defined_groups: frontmatter.
#>
[CmdletBinding()]
param(
    [string]$RootPath = "",
    [switch]$Apply,
    [string]$ComponentTypes = "commands,agents,rules,hooks,scripts"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================
# RESOLVE ROOT
# ============================================================
if ($RootPath -eq "") {
    $RootPath = Split-Path $PSScriptRoot -Parent
}
if (-not [System.IO.Directory]::Exists($RootPath)) {
    Write-Error "Root path not found: $RootPath"; exit 1
}

$typesToRun = $ComponentTypes.Split(",") | ForEach-Object { $_.Trim().ToLower() }

# ============================================================
# L1 GROUP DEFINITIONS (must mirror PRODUCT_SYSTEMS.md)
# ============================================================
$VALID_GROUPS = @(
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

# ============================================================
# LOOKUP TABLES
# ============================================================

# Commands: prefix-based matching (slug -> L1 group)
# Ordered: more specific prefixes first
$CMD_LOOKUP = [ordered]@{
    # BUG_AND_QUALITY
    'g-bug'              = 'BUG_AND_QUALITY'
    'g-qa'               = 'BUG_AND_QUALITY'
    'g-code-review'      = 'BUG_AND_QUALITY'
    'g-compliance'       = 'SECURITY_AND_COMPLIANCE'
    'g-dependency-graph' = 'BUG_AND_QUALITY'
    'g-review'           = 'BUG_AND_QUALITY'
    'g-swot'             = 'BUG_AND_QUALITY'
    'g-doctor'           = 'BUG_AND_QUALITY'
    'g-triage'           = 'BUG_AND_QUALITY'
    'g-hotfix'           = 'BUG_AND_QUALITY'
    'g-skill-review'     = 'BUG_AND_QUALITY'

    # TASK_MANAGEMENT
    'g-task'             = 'TASK_MANAGEMENT'
    'g-go-bugs'          = 'BUG_AND_QUALITY'
    'g-go'               = 'TASK_MANAGEMENT'
    'g-backlog'          = 'TASK_MANAGEMENT'
    'g-sprint'           = 'TASK_MANAGEMENT'
    'g-mission'          = 'TASK_MANAGEMENT'
    'g-grooming'         = 'TASK_MANAGEMENT'
    'g-queue'            = 'TASK_MANAGEMENT'
    'g-juggernaut'       = 'TASK_MANAGEMENT'
    'g-kamikaze'         = 'TASK_MANAGEMENT'
    'g-propose'          = 'TASK_MANAGEMENT'
    'g-steer'            = 'TASK_MANAGEMENT'
    'g-report'           = 'TASK_MANAGEMENT'

    # PLATFORM_INTEGRATION
    'g-cli'              = 'PLATFORM_INTEGRATION'
    'g-create-hook'      = 'PLATFORM_INTEGRATION'
    'g-mcp-new'          = 'PLATFORM_INTEGRATION'
    'g-skill-pack'       = 'PLATFORM_INTEGRATION'
    'g-pers'             = 'PLATFORM_INTEGRATION'
    'g-codeowners'       = 'PLATFORM_INTEGRATION'

    # MEMORY_AND_KNOWLEDGE
    'g-learn'            = 'MEMORY_AND_KNOWLEDGE'
    'g-compress'         = 'MEMORY_AND_KNOWLEDGE'
    'g-keep-it-simple'   = 'MEMORY_AND_KNOWLEDGE'
    'g-vocab'            = 'MEMORY_AND_KNOWLEDGE'

    # VAULT_AND_RESEARCH
    'g-vault'            = 'VAULT_AND_RESEARCH'
    'g-recon'            = 'VAULT_AND_RESEARCH'
    'g-res'              = 'VAULT_AND_RESEARCH'
    'g-knowledge'        = 'VAULT_AND_RESEARCH'
    'g-issue-sync'       = 'VAULT_AND_RESEARCH'

    # WORKSPACE_COORDINATION
    'g-pcac'             = 'WORKSPACE_COORDINATION'
    'g-wpac'             = 'WORKSPACE_COORDINATION'
    'g-wrkspc'           = 'WORKSPACE_COORDINATION'
    'g-workspace'        = 'WORKSPACE_COORDINATION'
    'g-inbox'            = 'WORKSPACE_COORDINATION'

    # PROJECT_IDENTITY_SETUP
    'g-medic'            = 'PROJECT_IDENTITY_SETUP'
    'g-medkit'           = 'PROJECT_IDENTITY_SETUP'
    'g-setup'            = 'PROJECT_IDENTITY_SETUP'
    'g-constraint'       = 'PROJECT_IDENTITY_SETUP'
    'g-goal'             = 'PROJECT_IDENTITY_SETUP'
    'g-subsystem'        = 'PROJECT_IDENTITY_SETUP'
    'g-system'           = 'PROJECT_IDENTITY_SETUP'
    'g-idea'             = 'PROJECT_IDENTITY_SETUP'
    'g-cleanup'          = 'PROJECT_IDENTITY_SETUP'
    'g-status'           = 'PROJECT_IDENTITY_SETUP'
    'g-update'           = 'PROJECT_IDENTITY_SETUP'
    'g-upgrade'          = 'PROJECT_IDENTITY_SETUP'
    'g-migrate'          = 'PROJECT_IDENTITY_SETUP'
    'g-gald3r-optimize'  = 'PROJECT_IDENTITY_SETUP'
    'g-curator'          = 'PROJECT_IDENTITY_SETUP'

    # RELEASE_AND_VERSIONING
    'g-plan'             = 'RELEASE_AND_VERSIONING'
    'g-feat'             = 'RELEASE_AND_VERSIONING'
    'g-prd'              = 'RELEASE_AND_VERSIONING'
    'g-release'          = 'RELEASE_AND_VERSIONING'
    'g-ship'             = 'RELEASE_AND_VERSIONING'
    'g-changelog'        = 'RELEASE_AND_VERSIONING'
    'g-gald3r-export'    = 'RELEASE_AND_VERSIONING'
    'g-template-export'  = 'RELEASE_AND_VERSIONING'
    'g-tier-setup'       = 'RELEASE_AND_VERSIONING'

    # AGENT_ORCHESTRATION
    'g-agent'            = 'AGENT_ORCHESTRATION'
    'g-marketing'        = 'AGENT_ORCHESTRATION'
    'g-test'             = 'BUG_AND_QUALITY'

    # UI_AND_OUTPUT
    'g-theme'            = 'UI_AND_OUTPUT'
    'g-html'             = 'UI_AND_OUTPUT'
    'g-toon'             = 'UI_AND_OUTPUT'
    'g-json'             = 'UI_AND_OUTPUT'
    'g-workflow'         = 'UI_AND_OUTPUT'

    # SECURITY_AND_COMPLIANCE
    'g-security'         = 'SECURITY_AND_COMPLIANCE'
    'g-git-sanity'       = 'SECURITY_AND_COMPLIANCE'
    'g-git-commit'       = 'SECURITY_AND_COMPLIANCE'
    'g-git-push'         = 'SECURITY_AND_COMPLIANCE'
    'g-pr'               = 'RELEASE_AND_VERSIONING'
    'g-crr'              = 'SECURITY_AND_COMPLIANCE'
}

# Agents: explicit slug -> L1 group
$AGENT_LOOKUP = @{
    'g-agnt-code-reviewer'      = 'BUG_AND_QUALITY'
    'g-agnt-ideas-goals'        = 'PROJECT_IDENTITY_SETUP'
    'g-agnt-infrastructure'     = 'PROJECT_IDENTITY_SETUP'
    'g-agnt-marketing'          = 'AGENT_ORCHESTRATION'
    'g-agnt-pcac-coordinator'   = 'WORKSPACE_COORDINATION'
    'g-agnt-project-initializer'= 'PROJECT_IDENTITY_SETUP'
    'g-agnt-project'            = 'PROJECT_IDENTITY_SETUP'
    'g-agnt-qa-engineer'        = 'BUG_AND_QUALITY'
    'g-agnt-task-manager'       = 'TASK_MANAGEMENT'
    'g-agnt-test'               = 'BUG_AND_QUALITY'
    'g-agnt-verifier'           = 'BUG_AND_QUALITY'
    'g-agnt-workspace-manager'  = 'WORKSPACE_COORDINATION'
}

# Rules: explicit slug -> L1 group (filename without extension)
$RULE_LOOKUP = @{
    'g-rl-00-always'                       = 'LOGGING_SYSTEM'
    'g-rl-01-documentation'                = 'PROJECT_IDENTITY_SETUP'
    'g-rl-02-git_workflow'                 = 'SECURITY_AND_COMPLIANCE'
    'g-rl-25-gald3r_session_start'         = 'PROJECT_IDENTITY_SETUP'
    'g-rl-26-readme-changelog'             = 'RELEASE_AND_VERSIONING'
    'g-rl-33-enforcement_catchall'         = 'PROJECT_IDENTITY_SETUP'
    'g-rl-34-todo_completion_gate'         = 'TASK_MANAGEMENT'
    'g-rl-35-bug-discovery-gate'           = 'BUG_AND_QUALITY'
    'g-rl-36-workspace-member-gald3r-guard'= 'WORKSPACE_COORDINATION'
    'silicon_valley_personality'           = 'AGENT_ORCHESTRATION'
    'rally'                                = 'WORKSPACE_COORDINATION'
    'g-rl-04-code_reusability'             = 'BUG_AND_QUALITY'
    'g-rl-08-powershell'                   = 'PLATFORM_INTEGRATION'
    'g-rl-09-python_venv'                  = 'PLATFORM_INTEGRATION'
    'g-rl-37-think-in-code'                = 'AGENT_ORCHESTRATION'
}

# Hooks: explicit slug -> L1 group
$HOOK_LOOKUP = @{
    'g-hk-agent-complete'              = 'LOGGING_SYSTEM'
    'g-hk-encoding-normalize'          = 'PLATFORM_INTEGRATION'
    'g-hk-ggo-stop-detect'             = 'TASK_MANAGEMENT'
    'g-hk-graph-update'                = 'PROJECT_IDENTITY_SETUP'
    'g-hk-nightly-learn'               = 'MEMORY_AND_KNOWLEDGE'
    'g-hk-pcac-inbox-check'            = 'WORKSPACE_COORDINATION'
    'g-hk-post-session-trace'          = 'LOGGING_SYSTEM'
    'g-hk-post-skill-timing'           = 'LOGGING_SYSTEM'
    'g-hk-pre-commit'                  = 'SECURITY_AND_COMPLIANCE'
    'g-hk-pre-push'                    = 'SECURITY_AND_COMPLIANCE'
    'g-hk-pre-session-trace'           = 'LOGGING_SYSTEM'
    'g-hk-pre-skill-timing'            = 'LOGGING_SYSTEM'
    'g-hk-pre-tool-call-gald3r-guard'  = 'PROJECT_IDENTITY_SETUP'
    'g-hk-pre-tool-call-member-gald3r-guard' = 'WORKSPACE_COORDINATION'
    'g-hk-pre-tool-call-prd-freeze'    = 'RELEASE_AND_VERSIONING'
    'g-hk-pre-tool-call'               = 'PROJECT_IDENTITY_SETUP'
    'g-hk-session-end'                 = 'LOGGING_SYSTEM'
    'g-hk-session-start'               = 'LOGGING_SYSTEM'
    'g-hk-setup-user'                  = 'PROJECT_IDENTITY_SETUP'
    'g-hk-validate-shell'              = 'PLATFORM_INTEGRATION'
    'g-hk-vault-migrate'               = 'VAULT_AND_RESEARCH'
    'g-hk-vault-reindex'               = 'VAULT_AND_RESEARCH'
    'g-hk-vault-resolve'               = 'VAULT_AND_RESEARCH'
    'g-hk-wrkspc-manifest-check'       = 'WORKSPACE_COORDINATION'
    'raw-inbox-watcher'                = 'WORKSPACE_COORDINATION'
}

# Scripts: explicit slug -> L1 group
$SCRIPT_LOOKUP = @{
    'add_subsystem_tags'               = 'PROJECT_IDENTITY_SETUP'
    'aggregate_subsystems'             = 'PROJECT_IDENTITY_SETUP'
    'tag_all_components'               = 'PROJECT_IDENTITY_SETUP'
    'gald3r_hook_helpers'              = 'LOGGING_SYSTEM'
    'gald3r_post_write_lint'           = 'BUG_AND_QUALITY'
    'install_git_hooks'                = 'SECURITY_AND_COMPLIANCE'
    'gald3r_optimize'                  = 'PROJECT_IDENTITY_SETUP'
    'gald3r_housekeeping_commit'       = 'SECURITY_AND_COMPLIANCE'
    'gald3r_worktree'                  = 'TASK_MANAGEMENT'
    'migrate_schemas'                  = 'PROJECT_IDENTITY_SETUP'
    'check_member_repo_gald3r_guard'   = 'WORKSPACE_COORDINATION'
    'bootstrap_member_gald3r_marker'   = 'WORKSPACE_COORDINATION'
    'remediate_member_gald3r_marker'   = 'WORKSPACE_COORDINATION'
    'validate_workspace_members_gald3r'= 'WORKSPACE_COORDINATION'
}

# ============================================================
# HELPERS
# ============================================================

function Get-Slug([string]$FilePath) {
    return [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
}

function Get-CommandGroup([string]$Slug) {
    foreach ($key in $CMD_LOOKUP.Keys) {
        if ($Slug -eq $key -or $Slug.StartsWith($key + '-') -or $Slug -eq $key) {
            return $CMD_LOOKUP[$key]
        }
    }
    # Fallback: try each key as prefix
    foreach ($key in $CMD_LOOKUP.Keys) {
        if ($Slug.StartsWith($key)) {
            return $CMD_LOOKUP[$key]
        }
    }
    return 'UNCATEGORIZED'
}

function Get-LookupGroup([string]$Slug, [hashtable]$Table) {
    if ($Table.ContainsKey($Slug)) { return $Table[$Slug] }
    return 'UNCATEGORIZED'
}

# Read first --- frontmatter block from a file
function Test-HasFrontmatter([string]$Content) {
    $lines = $Content -split "`n"
    if ($lines.Count -lt 2) { return $false }
    $first = $lines[0].Trim()
    if ($first -eq "---") { return $true }
    return $false
}

function Test-HasSubsystemTag([string]$Content, [string]$FileType) {
    if ($FileType -eq 'ps1') {
        return $Content -match '(?m)^#\s*@subsystems:'
    }
    return $Content -match '(?m)^subsystem_memberships:'
}

# Inject frontmatter block at top of a markdown file that has NO frontmatter
function Add-FrontmatterToMarkdown([string]$Content, [string]$Group) {
    $tag = if ($Group -eq 'UNCATEGORIZED') { '[UNCATEGORIZED]' } else { "[$Group]" }
    $fm = "---`nsubsystem_memberships: $tag`n---`n"
    return $fm + $Content
}

# Append subsystem_memberships: to an existing frontmatter block
function Add-FieldToFrontmatter([string]$Content, [string]$Group) {
    $tag = if ($Group -eq 'UNCATEGORIZED') { '[UNCATEGORIZED]' } else { "[$Group]" }
    $field = "subsystem_memberships: $tag"
    # Find the closing --- of the first frontmatter block
    $lines = $Content -split "`n"
    $closeIdx = -1
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Trim() -eq "---") { $closeIdx = $i; break }
    }
    if ($closeIdx -lt 0) {
        # Malformed frontmatter -- append before first heading
        return $Content.TrimEnd() + "`n$field`n"
    }
    $before = $lines[0..($closeIdx - 1)] -join "`n"
    $after  = $lines[$closeIdx..($lines.Count - 1)] -join "`n"
    return $before + "`n" + $field + "`n" + $after
}

# Inject @subsystems: comment into a .ps1 file
function Add-CommentTagToScript([string]$Content, [string]$Group) {
    $tag = if ($Group -eq 'UNCATEGORIZED') { 'UNCATEGORIZED' } else { $Group }
    $tagLine = "# @subsystems: $tag"
    $lines = $Content -split "`n"

    # If file has <# ... #> comment block, insert BEFORE the block
    # Otherwise insert after line 0 (first line)
    if ($lines[0].Trim() -eq "<#") {
        # Insert @subsystems tag as comment right before <#
        return $tagLine + "`n" + $Content
    }

    # If first line is a # comment, insert after it
    if ($lines[0].TrimStart().StartsWith("#")) {
        $rest = $lines[1..($lines.Count - 1)] -join "`n"
        return $lines[0] + "`n" + $tagLine + "`n" + $rest
    }

    # Otherwise prepend
    return $tagLine + "`n" + $Content
}

# ============================================================
# COUNTERS
# ============================================================
$results = @{
    commands = @{ tagged = 0; skipped = 0; uncategorized = 0; files = [System.Collections.Generic.List[string]]::new() }
    agents   = @{ tagged = 0; skipped = 0; uncategorized = 0; files = [System.Collections.Generic.List[string]]::new() }
    rules    = @{ tagged = 0; skipped = 0; uncategorized = 0; files = [System.Collections.Generic.List[string]]::new() }
    hooks    = @{ tagged = 0; skipped = 0; uncategorized = 0; files = [System.Collections.Generic.List[string]]::new() }
    scripts  = @{ tagged = 0; skipped = 0; uncategorized = 0; files = [System.Collections.Generic.List[string]]::new() }
}

$mode = if ($Apply) { "APPLY" } else { "DRY-RUN" }
Write-Host "+---------------------------------------------------------+"
Write-Host "|     tag_all_components.ps1 -- $mode                |"
Write-Host "+---------------------------------------------------------+"
Write-Host "  Root: $RootPath"
Write-Host "  Types: $ComponentTypes"
Write-Host ""

# ============================================================
# PROCESS COMMANDS
# ============================================================
if ($typesToRun -contains 'commands') {
    $cmdDir = [System.IO.Path]::Combine($RootPath, "commands")
    if ([System.IO.Directory]::Exists($cmdDir)) {
        Write-Host "[COMMANDS] Scanning $cmdDir ..." -ForegroundColor Cyan
        $cmdFiles = [System.IO.Directory]::GetFiles($cmdDir, "*.md", [System.IO.SearchOption]::TopDirectoryOnly)
        foreach ($f in $cmdFiles) {
            $slug = Get-Slug $f
            $content = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
            if (Test-HasSubsystemTag $content 'md') {
                $results.commands.skipped++
                continue
            }
            $group = Get-CommandGroup $slug
            if ($group -eq 'UNCATEGORIZED') { $results.commands.uncategorized++ }
            $tag = if ($group -eq 'UNCATEGORIZED') { '[UNCATEGORIZED]' } else { "[$group]" }

            if (Test-HasFrontmatter $content) {
                $newContent = Add-FieldToFrontmatter $content $group
            } else {
                $newContent = Add-FrontmatterToMarkdown $content $group
            }

            $results.commands.tagged++
            $results.commands.files.Add("  $slug -> $tag")
            if ($Apply) {
                [System.IO.File]::WriteAllText($f, $newContent, [System.Text.Encoding]::UTF8)
            }
        }
        Write-Host "  Tagged: $($results.commands.tagged)  Skipped: $($results.commands.skipped)  Uncategorized: $($results.commands.uncategorized)" -ForegroundColor White
    } else {
        Write-Host "[COMMANDS] Directory not found: $cmdDir" -ForegroundColor Yellow
    }
}

# ============================================================
# PROCESS AGENTS
# ============================================================
if ($typesToRun -contains 'agents') {
    $agentDir = [System.IO.Path]::Combine($RootPath, "agents")
    if ([System.IO.Directory]::Exists($agentDir)) {
        Write-Host "[AGENTS] Scanning $agentDir ..." -ForegroundColor Cyan
        $agentFiles = [System.IO.Directory]::GetFiles($agentDir, "g-agnt-*.md", [System.IO.SearchOption]::TopDirectoryOnly)
        foreach ($f in $agentFiles) {
            $slug = Get-Slug $f
            $content = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
            if (Test-HasSubsystemTag $content 'md') {
                $results.agents.skipped++
                continue
            }
            $group = Get-LookupGroup $slug $AGENT_LOOKUP
            if ($group -eq 'UNCATEGORIZED') { $results.agents.uncategorized++ }
            $tag = if ($group -eq 'UNCATEGORIZED') { '[UNCATEGORIZED]' } else { "[$group]" }

            if (Test-HasFrontmatter $content) {
                $newContent = Add-FieldToFrontmatter $content $group
            } else {
                $newContent = Add-FrontmatterToMarkdown $content $group
            }

            $results.agents.tagged++
            $results.agents.files.Add("  $slug -> $tag")
            if ($Apply) {
                [System.IO.File]::WriteAllText($f, $newContent, [System.Text.Encoding]::UTF8)
            }
        }
        Write-Host "  Tagged: $($results.agents.tagged)  Skipped: $($results.agents.skipped)  Uncategorized: $($results.agents.uncategorized)" -ForegroundColor White
    }
}

# ============================================================
# PROCESS RULES
# ============================================================
if ($typesToRun -contains 'rules') {
    $rulesDir = [System.IO.Path]::Combine($RootPath, "rules")
    if ([System.IO.Directory]::Exists($rulesDir)) {
        Write-Host "[RULES] Scanning $rulesDir ..." -ForegroundColor Cyan
        $ruleFiles = [System.IO.Directory]::GetFiles($rulesDir, "*.md", [System.IO.SearchOption]::AllDirectories)
        foreach ($f in $ruleFiles) {
            $slug = Get-Slug $f
            $content = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
            if (Test-HasSubsystemTag $content 'md') {
                $results.rules.skipped++
                continue
            }
            $group = Get-LookupGroup $slug $RULE_LOOKUP
            if ($group -eq 'UNCATEGORIZED') { $results.rules.uncategorized++ }
            $tag = if ($group -eq 'UNCATEGORIZED') { '[UNCATEGORIZED]' } else { "[$group]" }

            if (Test-HasFrontmatter $content) {
                $newContent = Add-FieldToFrontmatter $content $group
            } else {
                $newContent = Add-FrontmatterToMarkdown $content $group
            }

            $results.rules.tagged++
            $results.rules.files.Add("  $slug -> $tag")
            if ($Apply) {
                [System.IO.File]::WriteAllText($f, $newContent, [System.Text.Encoding]::UTF8)
            }
        }
        Write-Host "  Tagged: $($results.rules.tagged)  Skipped: $($results.rules.skipped)  Uncategorized: $($results.rules.uncategorized)" -ForegroundColor White
    }
}

# ============================================================
# PROCESS HOOKS
# ============================================================
if ($typesToRun -contains 'hooks') {
    $hookDir = [System.IO.Path]::Combine($RootPath, "hooks")
    if ([System.IO.Directory]::Exists($hookDir)) {
        Write-Host "[HOOKS] Scanning $hookDir ..." -ForegroundColor Cyan
        $hookFiles = [System.IO.Directory]::GetFiles($hookDir, "*.ps1", [System.IO.SearchOption]::AllDirectories)
        foreach ($f in $hookFiles) {
            $slug = Get-Slug $f
            $content = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
            if (Test-HasSubsystemTag $content 'ps1') {
                $results.hooks.skipped++
                continue
            }
            $group = Get-LookupGroup $slug $HOOK_LOOKUP
            if ($group -eq 'UNCATEGORIZED') { $results.hooks.uncategorized++ }
            $tag = if ($group -eq 'UNCATEGORIZED') { 'UNCATEGORIZED' } else { $group }

            $newContent = Add-CommentTagToScript $content $group
            $results.hooks.tagged++
            $results.hooks.files.Add("  $slug -> $tag")
            if ($Apply) {
                [System.IO.File]::WriteAllText($f, $newContent, [System.Text.Encoding]::UTF8)
            }
        }
        Write-Host "  Tagged: $($results.hooks.tagged)  Skipped: $($results.hooks.skipped)  Uncategorized: $($results.hooks.uncategorized)" -ForegroundColor White
    }
}

# ============================================================
# PROCESS SCRIPTS
# ============================================================
if ($typesToRun -contains 'scripts') {
    $scriptDir = [System.IO.Path]::Combine($RootPath, "scripts")
    if ([System.IO.Directory]::Exists($scriptDir)) {
        Write-Host "[SCRIPTS] Scanning $scriptDir ..." -ForegroundColor Cyan
        $scriptFiles = [System.IO.Directory]::GetFiles($scriptDir, "*.ps1", [System.IO.SearchOption]::AllDirectories)
        foreach ($f in $scriptFiles) {
            $slug = Get-Slug $f
            $content = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
            if (Test-HasSubsystemTag $content 'ps1') {
                $results.scripts.skipped++
                continue
            }
            $group = Get-LookupGroup $slug $SCRIPT_LOOKUP
            if ($group -eq 'UNCATEGORIZED') { $results.scripts.uncategorized++ }
            $tag = if ($group -eq 'UNCATEGORIZED') { 'UNCATEGORIZED' } else { $group }

            $newContent = Add-CommentTagToScript $content $group
            $results.scripts.tagged++
            $results.scripts.files.Add("  $slug -> $tag")
            if ($Apply) {
                [System.IO.File]::WriteAllText($f, $newContent, [System.Text.Encoding]::UTF8)
            }
        }
        Write-Host "  Tagged: $($results.scripts.tagged)  Skipped: $($results.scripts.skipped)  Uncategorized: $($results.scripts.uncategorized)" -ForegroundColor White
    }
}

# ============================================================
# SUMMARY REPORT
# ============================================================
Write-Host ""
Write-Host "+---------------------------------------------------------+"
Write-Host "|                    SUMMARY ($mode)                 |"
Write-Host "+---------------------------------------------------------+"

$totalTagged = 0; $totalSkipped = 0; $totalUncat = 0
foreach ($type in @('commands','agents','rules','hooks','scripts')) {
    if ($typesToRun -contains $type) {
        $r = $results[$type]
        $totalTagged  += $r.tagged
        $totalSkipped += $r.skipped
        $totalUncat   += $r.uncategorized
        Write-Host "  $($type.ToUpper().PadRight(10)) : $($r.tagged) tagged, $($r.skipped) skipped, $($r.uncategorized) uncategorized"
    }
}
Write-Host "  -------------------------------------------------------"
Write-Host "  TOTAL      : $totalTagged tagged, $totalSkipped skipped, $totalUncat uncategorized"

if ($totalUncat -gt 0) {
    Write-Host ""
    Write-Host "  UNCATEGORIZED FILES -- assign manually then re-run:" -ForegroundColor Yellow
    foreach ($type in @('commands','agents','rules','hooks','scripts')) {
        if ($typesToRun -contains $type) {
            $r = $results[$type]
            if ($r.uncategorized -gt 0) {
                Write-Host "  [$($type.ToUpper())]" -ForegroundColor Yellow
                $r.files | Where-Object { $_ -match 'UNCATEGORIZED' } | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
            }
        }
    }
}

if (-not $Apply -and $totalTagged -gt 0) {
    Write-Host ""
    Write-Host "  Dry-run complete. Re-run with -Apply to write $totalTagged file(s)." -ForegroundColor Cyan
}
if ($Apply -and $totalTagged -gt 0) {
    Write-Host ""
    Write-Host "  $totalTagged file(s) written." -ForegroundColor Green
    Write-Host "  Re-run aggregate_subsystems.ps1 to update PRODUCT_SYSTEMS.md." -ForegroundColor Cyan
}
