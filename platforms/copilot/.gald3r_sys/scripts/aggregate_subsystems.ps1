# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    Generate PRODUCT_SYSTEMS.md from distributed subsystem_memberships: and parent_system: tags.

.DESCRIPTION
    T1459 -- aggregate_subsystems.ps1

    Scans one or more project repos for tagged files (SKILL.md files with
    subsystem_memberships: and subsystem spec .md files with parent_system:),
    builds a group map, detects issues, and writes PRODUCT_SYSTEMS.md with
    machine-readable frontmatter (defined_groups:) preserved.

    Invoke via: @g-system-rebuild

.PARAMETER ProjectPath
    Root path of the project to scan (default: current directory).

.PARAMETER WorkspaceOnly
    Scan only the current project. When omitted and a workspace manifest exists,
    also scans all registered member repos.

.PARAMETER Apply
    Write PRODUCT_SYSTEMS.md. Without this flag, runs dry-run only (reports plan).

.PARAMETER OutputPath
    Override the output path for PRODUCT_SYSTEMS.md.
    Default: resolves from workspace topology (controller .gald3r/ or local .gald3r/).

.PARAMETER Verbose
    Show per-file scan details.

.EXAMPLE
    .\aggregate_subsystems.ps1 -ProjectPath . -Apply
    (Scan current project + workspace members, write PRODUCT_SYSTEMS.md)

.EXAMPLE
    .\aggregate_subsystems.ps1 -ProjectPath . -WorkspaceOnly
    (Dry-run for current project only)

.NOTES
    T1459 | gald3r_templates | 2026-05-26
    Reads defined_groups: from existing PRODUCT_SYSTEMS.md stub (T1457 output).
    Falls back to hardcoded defaults if stub missing.
    T1458 reads defined_groups: from the OUTPUT of this script.
#>
[CmdletBinding()]
param(
    [string]$ProjectPath = ".",
    [switch]$WorkspaceOnly,
    [switch]$Apply,
    [string]$OutputPath = "",
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path $ProjectPath).Path

# ---------------------------------------------------------------------------
# Default L1 groups (bootstrapping -- before PRODUCT_SYSTEMS.md exists)
# ---------------------------------------------------------------------------
$DEFAULT_GROUPS = @(
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Read-YamlFrontmatter([string]$FilePath) {
    $content = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)
    if ($content -notmatch '(?s)^---\r?\n(.+?)\r?\n---') { return @{} }
    $fm = $Matches[1]
    $result = @{}
    $lines = $fm -split '\r?\n'
    $currentKey = $null

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]

        # Block list item under current key (e.g. "  - VALUE")
        if ($currentKey -and $line -match '^\s+-\s+(.+)$') {
            $item = $Matches[1].Trim().Trim("'").Trim('"')
            if ($result[$currentKey] -is [System.Collections.Generic.List[string]]) {
                $result[$currentKey].Add($item) | Out-Null
            } else {
                $list = [System.Collections.Generic.List[string]]::new()
                $list.Add($item) | Out-Null
                $result[$currentKey] = $list
            }
            continue
        }

        # Key: value line
        if ($line -match '^(\w[\w_-]*):\s*(.*)$') {
            $currentKey = $Matches[1]
            $val = $Matches[2].Trim()
            if ($val -match '^\[(.+)\]$') {
                # Inline list: [A, B, C]
                $result[$currentKey] = @($Matches[1] -split '\s*,\s*' |
                    ForEach-Object { $_.Trim().Trim("'").Trim('"') })
            } elseif ([string]::IsNullOrEmpty($val)) {
                # Empty value -- might start a block list on next lines
                $result[$currentKey] = [System.Collections.Generic.List[string]]::new()
            } else {
                $result[$currentKey] = $val.Trim("'").Trim('"')
                $currentKey = $null  # scalar -- no block continuation
            }
            continue
        }

        # Non-matching line breaks block list continuations
        if ($line -notmatch '^\s') { $currentKey = $null }
    }

    # Convert List[string] to plain arrays for uniform access
    $keys = @($result.Keys)
    foreach ($k in $keys) {
        if ($result[$k] -is [System.Collections.Generic.List[string]]) {
            $result[$k] = @($result[$k])
        }
    }

    return $result
}

function Get-DefinedGroups([string]$ProductSystemsPath) {
    if (Test-Path $ProductSystemsPath) {
        $fm = Read-YamlFrontmatter $ProductSystemsPath
        $dg = @($fm['defined_groups'])
        if ($fm.ContainsKey('defined_groups') -and $dg.Count -gt 0) {
            return $dg
        }
    }
    return $DEFAULT_GROUPS
}

function Find-ProjectRoots([string]$Root, [bool]$WorkspaceOnly) {
    $roots = @($Root)
    if ($WorkspaceOnly) { return $roots }

    # Check for workspace manifest
    $manifestPath = Join-Path $Root ".gald3r\linking\workspace_manifest.yaml"
    if (-not (Test-Path $manifestPath)) {
        $manifestPath = Join-Path $Root ".gald3r\workspace\workspace_manifest.yaml"
    }
    if (Test-Path $manifestPath) {
        $manifest = [System.IO.File]::ReadAllText($manifestPath)
        $localPaths = [regex]::Matches($manifest, 'local_path:\s*["'']?([^"''\r\n]+)["'']?')
        foreach ($m in $localPaths) {
            $p = $m.Groups[1].Value.Trim()
            if ($p -and $p -ne $Root -and (Test-Path $p)) {
                $roots += $p
            }
        }
    }
    return $roots | Select-Object -Unique
}

function Resolve-OutputPath([string]$Root) {
    # Prefer controller .gald3r/ when WPAC is configured
    $topologyPath = Join-Path $Root ".gald3r\workspace\topology.md"
    if (Test-Path $topologyPath) {
        $topo = [System.IO.File]::ReadAllText($topologyPath)
        if ($topo -match 'role:\s*controller') {
            return Join-Path $Root ".gald3r\PRODUCT_SYSTEMS.md"
        }
    }
    return Join-Path $Root ".gald3r\PRODUCT_SYSTEMS.md"
}

# ---------------------------------------------------------------------------
# Step 1: Determine output path and load defined groups
# ---------------------------------------------------------------------------

$effectiveOutputPath = if ($OutputPath) { $OutputPath } else { Resolve-OutputPath $projectRoot }
$definedGroups = Get-DefinedGroups $effectiveOutputPath

Write-Host ""
Write-Host "+--------------------------------------------------------------+"
Write-Host "|  aggregate_subsystems.ps1 -- PRODUCT_SYSTEMS.md Generator   |"
Write-Host "|  Mode: $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })$(if ($WorkspaceOnly) { ' (this project only)' } else { ' (workspace-wide)' })$((' ' * 55).Substring(0, [Math]::Max(0, 55 - "$(if ($Apply) {'APPLY'} else {'DRY-RUN'})$(if ($WorkspaceOnly) {' (this project only)'} else {' (workspace-wide)'})".Length)))|"
Write-Host "+--------------------------------------------------------------+"
Write-Host ""
Write-Host "  Output: $effectiveOutputPath"
Write-Host "  Groups: $($definedGroups.Count) defined"
Write-Host ""

# ---------------------------------------------------------------------------
# Step 2: Discover repos to scan
# ---------------------------------------------------------------------------

$reposToScan = @(Find-ProjectRoots $projectRoot $WorkspaceOnly.IsPresent)

Write-Host "  Repos to scan: $($reposToScan.Count)"
foreach ($r in $reposToScan) { Write-Host "    - $r" }
Write-Host ""

# ---------------------------------------------------------------------------
# Step 3: Scan files
# ---------------------------------------------------------------------------

# groupMap: { "GROUP_NAME" => @{ skills=@(..); subsystems=@(..); commands=@(..); agents=@(..); rules=@(..); hooks=@(..); scripts=@(..) } }
$groupMap = @{}
foreach ($g in $definedGroups) {
    $groupMap[$g] = @{
        skills    = [System.Collections.Generic.List[string]]::new()
        subsystems= [System.Collections.Generic.List[string]]::new()
        commands  = [System.Collections.Generic.List[string]]::new()
        agents    = [System.Collections.Generic.List[string]]::new()
        rules     = [System.Collections.Generic.List[string]]::new()
        hooks     = [System.Collections.Generic.List[string]]::new()
        scripts   = [System.Collections.Generic.List[string]]::new()
    }
}

$ungroupedSkills    = [System.Collections.Generic.List[string]]::new()
$ungroupedSubsystems= [System.Collections.Generic.List[string]]::new()
$unknownGroupRefs   = [System.Collections.Generic.List[psobject]]::new()
$totalSkills = 0; $totalSubsystems = 0
$totalCommands = 0; $totalAgents = 0; $totalRules = 0; $totalHooks = 0; $totalScripts = 0

# Helper: parse subsystem_memberships from markdown frontmatter
# Returns @() (empty) when field not present; always returns an array
function Get-FrontmatterMemberships([string]$FilePath) {
    $fm = Read-YamlFrontmatter $FilePath
    if (-not $fm.ContainsKey('subsystem_memberships')) { return @() }
    $raw = $fm['subsystem_memberships']
    if ($raw -is [string]) { $raw = $raw.Trim('[',']') }
    return @($raw -split ',' | ForEach-Object { $_.Trim().Trim('[',']') } | Where-Object { $_ -ne '' })
}

# Helper: parse # @subsystems: from .ps1 comment
# Returns @() (empty) when tag not present; always returns an array
function Get-CommentMemberships([string]$FilePath) {
    $content = [System.IO.File]::ReadAllText($FilePath)
    if ($content -match '(?m)^#\s*@subsystems:\s*(.+)$') {
        return @($Matches[1] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
    }
    return @()
}

# Helper: add slug to groupMap bucket
function Add-ToGroupMap([string]$Grp, [string]$Bucket, [string]$Slug) {
    if ($groupMap.ContainsKey($Grp)) {
        $groupMap[$Grp][$Bucket].Add($Slug) | Out-Null
        return $true
    }
    return $false
}

foreach ($repoRoot in $reposToScan) {
    # -- Scan SKILL.md files (canonical .gald3r_sys/skills/ only -- excludes platform copies) --
    $canonicalSkillsDir = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys\skills")
    $skillFiles = @()
    if ([System.IO.Directory]::Exists($canonicalSkillsDir)) {
        $skillFiles = Get-ChildItem -Path $canonicalSkillsDir -Recurse -Filter "SKILL.md" -File -ErrorAction SilentlyContinue
    }

    foreach ($sf in $skillFiles) {
        $totalSkills++
        $slug = Split-Path (Split-Path $sf.FullName -Parent) -Leaf
        $memberships = @(Get-FrontmatterMemberships $sf.FullName)

        if ($memberships.Count -eq 0) {
            $ungroupedSkills.Add("$slug ($repoRoot)"); continue
        }
        if ($memberships.Count -eq 1 -and $memberships[0] -eq 'UNCATEGORIZED') {
            $ungroupedSkills.Add("$slug (UNCATEGORIZED)"); continue
        }

        foreach ($grp in $memberships) {
            if (-not (Add-ToGroupMap $grp 'skills' $slug)) {
                $unknownGroupRefs.Add([pscustomobject]@{ File = $sf.FullName; Field = 'subsystem_memberships'; Value = $grp })
            }
        }
        if ($VerboseOutput) { Write-Host "    [SKL] $slug -> $($memberships -join ', ')" }
    }

    # -- Scan subsystem spec files --
    $subsystemDir = Join-Path $repoRoot ".gald3r\subsystems"
    if (Test-Path $subsystemDir) {
        $specFiles = Get-ChildItem -Path $subsystemDir -Recurse -Filter "*.md" -File -ErrorAction SilentlyContinue
        foreach ($sf in $specFiles) {
            $totalSubsystems++
            $fm = Read-YamlFrontmatter $sf.FullName
            $name = if ($fm.ContainsKey('name')) { $fm['name'] } else { [System.IO.Path]::GetFileNameWithoutExtension($sf.Name) }

            if (-not $fm.ContainsKey('parent_system') -or [string]::IsNullOrWhiteSpace($fm['parent_system'])) {
                $ungroupedSubsystems.Add("$name ($repoRoot)"); continue
            }
            $parentSystem = $fm['parent_system']
            if (-not (Add-ToGroupMap $parentSystem 'subsystems' $name)) {
                $unknownGroupRefs.Add([pscustomobject]@{ File = $sf.FullName; Field = 'parent_system'; Value = $parentSystem })
            }
            if ($VerboseOutput) { Write-Host "    [SUB] $name -> $parentSystem" }
        }
    }

    # -- Scan command files (.md with subsystem_memberships:) --
    $cmdDir = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys\commands")
    if ([System.IO.Directory]::Exists($cmdDir)) {
        $cmdFiles = [System.IO.Directory]::GetFiles($cmdDir, "*.md", [System.IO.SearchOption]::TopDirectoryOnly)
        foreach ($cf in $cmdFiles) {
            $totalCommands++
            $slug = [System.IO.Path]::GetFileNameWithoutExtension($cf)
            $memberships = @(Get-FrontmatterMemberships $cf)
            if ($memberships.Count -eq 0) { continue }
            foreach ($grp in $memberships) {
                if ($grp -ne 'UNCATEGORIZED') { Add-ToGroupMap $grp 'commands' $slug | Out-Null }
            }
            if ($VerboseOutput) { Write-Host "    [CMD] $slug -> $($memberships -join ', ')" }
        }
    }

    # -- Scan agent files (.md with subsystem_memberships:) --
    $agentDir = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys\agents")
    if ([System.IO.Directory]::Exists($agentDir)) {
        $agentFiles = [System.IO.Directory]::GetFiles($agentDir, "g-agnt-*.md", [System.IO.SearchOption]::TopDirectoryOnly)
        foreach ($af in $agentFiles) {
            $totalAgents++
            $slug = [System.IO.Path]::GetFileNameWithoutExtension($af)
            $memberships = @(Get-FrontmatterMemberships $af)
            if ($memberships.Count -eq 0) { continue }
            foreach ($grp in $memberships) {
                if ($grp -ne 'UNCATEGORIZED') { Add-ToGroupMap $grp 'agents' $slug | Out-Null }
            }
            if ($VerboseOutput) { Write-Host "    [AGT] $slug -> $($memberships -join ', ')" }
        }
    }

    # -- Scan rule files (.md with subsystem_memberships:) --
    $rulesDir = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys\rules")
    if ([System.IO.Directory]::Exists($rulesDir)) {
        $ruleFiles = [System.IO.Directory]::GetFiles($rulesDir, "*.md", [System.IO.SearchOption]::AllDirectories)
        foreach ($rf in $ruleFiles) {
            $totalRules++
            $slug = [System.IO.Path]::GetFileNameWithoutExtension($rf)
            $memberships = @(Get-FrontmatterMemberships $rf)
            if ($memberships.Count -eq 0) { continue }
            foreach ($grp in $memberships) {
                if ($grp -ne 'UNCATEGORIZED') { Add-ToGroupMap $grp 'rules' $slug | Out-Null }
            }
            if ($VerboseOutput) { Write-Host "    [RUL] $slug -> $($memberships -join ', ')" }
        }
    }

    # -- Scan hook files (.ps1 with # @subsystems:) --
    $hookDir = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys\hooks")
    if ([System.IO.Directory]::Exists($hookDir)) {
        $hookFiles = [System.IO.Directory]::GetFiles($hookDir, "*.ps1", [System.IO.SearchOption]::AllDirectories)
        foreach ($hf in $hookFiles) {
            $totalHooks++
            $slug = [System.IO.Path]::GetFileNameWithoutExtension($hf)
            $memberships = @(Get-CommentMemberships $hf)
            if ($memberships.Count -eq 0) { continue }
            foreach ($grp in $memberships) {
                if ($grp -ne 'UNCATEGORIZED') { Add-ToGroupMap $grp 'hooks' $slug | Out-Null }
            }
            if ($VerboseOutput) { Write-Host "    [HKS] $slug -> $($memberships -join ', ')" }
        }
    }

    # -- Scan script files (.ps1 with # @subsystems:) --
    $scriptDir = [System.IO.Path]::Combine($repoRoot, ".gald3r_sys\scripts")
    if ([System.IO.Directory]::Exists($scriptDir)) {
        $scriptFiles = [System.IO.Directory]::GetFiles($scriptDir, "*.ps1", [System.IO.SearchOption]::AllDirectories)
        foreach ($scf in $scriptFiles) {
            $totalScripts++
            $slug = [System.IO.Path]::GetFileNameWithoutExtension($scf)
            $memberships = @(Get-CommentMemberships $scf)
            if ($memberships.Count -eq 0) { continue }
            foreach ($grp in $memberships) {
                if ($grp -ne 'UNCATEGORIZED') { Add-ToGroupMap $grp 'scripts' $slug | Out-Null }
            }
            if ($VerboseOutput) { Write-Host "    [SCR] $slug -> $($memberships -join ', ')" }
        }
    }
}

# ---------------------------------------------------------------------------
# Step 4: Issue detection
# ---------------------------------------------------------------------------

$emptyGroups = @($definedGroups | Where-Object {
    $g = $groupMap[$_]
    $g.skills.Count -eq 0 -and $g.subsystems.Count -eq 0 -and $g.commands.Count -eq 0 -and
    $g.agents.Count -eq 0 -and $g.rules.Count -eq 0 -and $g.hooks.Count -eq 0 -and $g.scripts.Count -eq 0
})

Write-Host "  Scan Results:"
Write-Host "    Skills scanned:        $totalSkills"
Write-Host "    Subsystems scanned:    $totalSubsystems"
Write-Host "    Commands scanned:      $totalCommands"
Write-Host "    Agents scanned:        $totalAgents"
Write-Host "    Rules scanned:         $totalRules"
Write-Host "    Hooks scanned:         $totalHooks"
Write-Host "    Scripts scanned:       $totalScripts"
Write-Host "    Ungrouped skills:      $($ungroupedSkills.Count)"
Write-Host "    Ungrouped subsystems:  $($ungroupedSubsystems.Count)"
Write-Host "    Unknown group refs:    $($unknownGroupRefs.Count)"
Write-Host "    Empty groups:          $($emptyGroups.Count)"
Write-Host ""

if ($unknownGroupRefs.Count -gt 0) {
    Write-Host "  UNKNOWN GROUP REFERENCES (typos -- fix these before applying):"
    foreach ($ref in $unknownGroupRefs) {
        Write-Host "    $($ref.Field): $($ref.Value) in $($ref.File)"
    }
    Write-Host ""
}

if ($ungroupedSubsystems.Count -gt 0) {
    Write-Host "  UNGROUPED SUBSYSTEMS (missing parent_system: in frontmatter):"
    foreach ($s in $ungroupedSubsystems) { Write-Host "    - $s" }
    Write-Host ""
}

if (-not $Apply) {
    Write-Host "  DRY-RUN complete. Add -Apply to write PRODUCT_SYSTEMS.md."
    Write-Host ""
    return
}

# ---------------------------------------------------------------------------
# Step 5: Generate PRODUCT_SYSTEMS.md
# ---------------------------------------------------------------------------

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$reposScanned = ($reposToScan | ForEach-Object { Split-Path $_ -Leaf }) -join ', '

$sb = [System.Text.StringBuilder]::new()

# Frontmatter -- machine-readable; preserves defined_groups: for T1458 enforcement
[void]$sb.AppendLine("---")
[void]$sb.AppendLine("generated_by: aggregate_subsystems.ps1")
[void]$sb.AppendLine("generated_at: $timestamp")
[void]$sb.AppendLine("workspace_repos_scanned: [$reposScanned]")
[void]$sb.AppendLine("defined_groups:")
foreach ($g in $definedGroups) { [void]$sb.AppendLine("  - $g") }
[void]$sb.AppendLine("---")
[void]$sb.AppendLine("")

# Header
[void]$sb.AppendLine("# PRODUCT SYSTEMS MAP")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("> **Auto-generated** by ``aggregate_subsystems.ps1`` at $timestamp")
[void]$sb.AppendLine("> Repos scanned: $reposScanned")
[void]$sb.AppendLine("> Run ``@g-system-rebuild`` to regenerate. Do not hand-edit.")
[void]$sb.AppendLine("> Source of truth for L1 group names: ``defined_groups:`` in this file's frontmatter.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("---")
[void]$sb.AppendLine("")

# Group sections
foreach ($grp in $definedGroups) {
    $entry = $groupMap[$grp]
    $hasAny = $entry.skills.Count -gt 0 -or $entry.subsystems.Count -gt 0 -or $entry.commands.Count -gt 0 -or
              $entry.agents.Count -gt 0 -or $entry.rules.Count -gt 0 -or $entry.hooks.Count -gt 0 -or $entry.scripts.Count -gt 0

    [void]$sb.AppendLine("## $grp")
    [void]$sb.AppendLine("")

    $buckets = [ordered]@{
        'Skills'    = $entry.skills
        'Subsystems'= $entry.subsystems
        'Commands'  = $entry.commands
        'Agents'    = $entry.agents
        'Rules'     = $entry.rules
        'Hooks'     = $entry.hooks
        'Scripts'   = $entry.scripts
    }
    foreach ($bName in $buckets.Keys) {
        $bList = $buckets[$bName]
        if ($bList.Count -gt 0) {
            [void]$sb.AppendLine("**$bName** ($($bList.Count)):")
            foreach ($s in ($bList | Sort-Object)) { [void]$sb.AppendLine("- $s") }
            [void]$sb.AppendLine("")
        }
    }

    if (-not $hasAny) {
        [void]$sb.AppendLine("*No members yet. Add ``parent_system: $grp`` to subsystem specs or ``subsystem_memberships: [$grp]`` to component files.*")
        [void]$sb.AppendLine("")
    }

    [void]$sb.AppendLine("---")
    [void]$sb.AppendLine("")
}

# Ungrouped section
if ($ungroupedSkills.Count -gt 0 -or $ungroupedSubsystems.Count -gt 0) {
    [void]$sb.AppendLine("## UNGROUPED")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("> Run ``@g-subsystem-audit`` for details and fix guidance.")
    [void]$sb.AppendLine("")
    if ($ungroupedSkills.Count -gt 0) {
        [void]$sb.AppendLine("**Untagged Skills** ($($ungroupedSkills.Count)):")
        foreach ($s in $ungroupedSkills) { [void]$sb.AppendLine("- $s") }
        [void]$sb.AppendLine("")
    }
    if ($ungroupedSubsystems.Count -gt 0) {
        [void]$sb.AppendLine("**Ungrouped Subsystems** ($($ungroupedSubsystems.Count)):")
        foreach ($s in $ungroupedSubsystems) { [void]$sb.AppendLine("- $s") }
        [void]$sb.AppendLine("")
    }
} else {
    [void]$sb.AppendLine("## UNGROUPED")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("*None -- all components are assigned to a group.*")
    [void]$sb.AppendLine("")
}

# Write the file
$outputDir = Split-Path $effectiveOutputPath -Parent
if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }
[System.IO.File]::WriteAllText($effectiveOutputPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding $false))

Write-Host "  Written: $effectiveOutputPath"
$populated = ($definedGroups | Where-Object {
    $g = $groupMap[$_]
    $g.skills.Count -gt 0 -or $g.subsystems.Count -gt 0 -or $g.commands.Count -gt 0 -or
    $g.agents.Count -gt 0 -or $g.rules.Count -gt 0 -or $g.hooks.Count -gt 0 -or $g.scripts.Count -gt 0
}).Count
Write-Host "  Groups populated: $populated/$($definedGroups.Count)"
Write-Host ""
Write-Host "  Done."
