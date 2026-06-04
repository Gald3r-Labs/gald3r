<#
.SYNOPSIS
    Load a gald3r Workflow Profile YAML and emit a JSON snapshot for agents.
    T1281 (Project Types epic); hybrid activation + freeform fallback added by
    T1335 (BUG-092 reconciliation). Phase 1 loader stub — informational only;
    commands still use their hardcoded status lists until Phase 2.

.DESCRIPTION
    Resolves the active workflow profile via the hybrid activation chain, reads
    the matching profile under .gald3r/config/workflow_profiles/, and prints a
    JSON snapshot to stdout.

    Hybrid activation chain (highest priority first, T1335 decision #3):
      1. -ProjectType parameter (explicit override, e.g. for testing)
      2. Task frontmatter `workflow_profile:` (when -TaskFile is supplied)
      3. PROJECT.md `workflow_profile:` field
      4. .gald3r/.identity `project_type=` (or .gald3r/.project_type dotfile)
      5. freeform (final safe-default fallback)

    Filenames are canonical: <profile>.yaml. The five canonical profiles are
    software_development, content_creation, 3d_modeling, research_analysis,
    freeform. If a resolved profile file is missing, the loader warns and loads
    freeform.yaml.

.PARAMETER ProjectType
    Override the resolved profile (e.g. -ProjectType freeform).

.PARAMETER TaskFile
    Optional path to a task .md file; its `workflow_profile:` frontmatter field
    (if present) wins over PROJECT.md and .identity.

.PARAMETER ProjectRoot
    Repo root containing .gald3r/. Defaults to walking up from the script.

.EXAMPLE
    pwsh -File load_profile.ps1
    pwsh -File load_profile.ps1 -ProjectType content_creation
    pwsh -File load_profile.ps1 -TaskFile .gald3r/tasks/open/task1300_foo.md
#>
[CmdletBinding()]
param(
    [string]$ProjectType,
    [string]$TaskFile,
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$FALLBACK = 'freeform'   # T1335 decision #3: freeform is the safe default

function Find-ProjectRoot {
    param([string]$Start)
    $dir = if ($Start) { $Start } else { $PSScriptRoot }
    for ($i = 0; $i -lt 12 -and $dir; $i++) {
        if (Test-Path (Join-Path $dir '.gald3r')) { return $dir }
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    return (Get-Location).Path
}

# Read a `workflow_profile:` value from a markdown file's YAML frontmatter.
function Get-WorkflowProfileField {
    param([string]$Path)
    if (-not $Path -or -not (Test-Path $Path)) { return $null }
    $line = Select-String -Path $Path -Pattern '^\s*workflow_profile\s*:\s*(.+?)\s*$' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($line) {
        $val = $line.Matches[0].Groups[1].Value.Trim().Trim('"').Trim("'").ToLower()
        if ($val -and $val -ne 'null') { return $val }
    }
    return $null
}

# Hybrid activation chain — returns the resolved profile id (string).
function Resolve-Profile {
    param([string]$Root, [string]$TaskFilePath)

    # 2. Task frontmatter workflow_profile: (highest after explicit param)
    if ($TaskFilePath) {
        $taskProfile = Get-WorkflowProfileField -Path $TaskFilePath
        if ($taskProfile) { return $taskProfile }
    }

    # 3. PROJECT.md workflow_profile:
    $projectMd = Join-Path $Root '.gald3r/PROJECT.md'
    $projProfile = Get-WorkflowProfileField -Path $projectMd
    if ($projProfile) { return $projProfile }

    # 4a. .identity combined file: project_type=...
    $identity = Join-Path $Root '.gald3r/.identity'
    if (Test-Path $identity) {
        $line = Select-String -Path $identity -Pattern '^\s*project_type\s*=\s*(.+)\s*$' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($line) {
            $v = $line.Matches[0].Groups[1].Value.Trim().ToLower()
            if ($v) { return $v }
        }
    }
    # 4b. .project_type dotfile (gald3r_install idiom)
    $dotfile = Join-Path $Root '.gald3r/.project_type'
    if (Test-Path $dotfile) {
        $v = (Get-Content $dotfile -Raw -ErrorAction SilentlyContinue).Trim().ToLower()
        if ($v) { return $v }
    }

    # 5. final fallback
    return $FALLBACK
}

# T1239: normalize legacy project_type / project-types-epic ids onto the
# canonical T1238 workflow-profile filenames actually shipped under
# .gald3r/config/workflow_profiles/. Keeps the .identity project_type= switch
# (e.g. software_development) resolving to the real software_dev.yaml file.
$PROFILE_ALIASES = @{
    'software_development' = 'software_dev'
    'software'             = 'software_dev'
    'research_analysis'    = 'research'
    'research_science'     = 'research'
    'content'              = 'content_creation'
}

$root = Find-ProjectRoot -Start $ProjectRoot
if (-not $ProjectType) { $ProjectType = Resolve-Profile -Root $root -TaskFilePath $TaskFile }
$ProjectType = $ProjectType.ToLower()
if ($PROFILE_ALIASES.ContainsKey($ProjectType)) { $ProjectType = $PROFILE_ALIASES[$ProjectType] }

$profileDir = Join-Path $root '.gald3r/config/workflow_profiles'
$profilePath = Join-Path $profileDir "$ProjectType.yaml"

if (-not (Test-Path $profilePath)) {
    # T1239: prefer freeform.yaml; if absent, fall back to the T1238 default
    # profile (software_dev) before the builtin minimal snapshot below.
    $freeformPath = Join-Path $profileDir "$FALLBACK.yaml"
    $defaultPath  = Join-Path $profileDir 'software_dev.yaml'
    if (Test-Path $freeformPath) {
        Write-Warning "Profile '$ProjectType' not found; falling back to '$FALLBACK'."
        $ProjectType = $FALLBACK
        $profilePath = $freeformPath
    } elseif (Test-Path $defaultPath) {
        Write-Warning "Profile '$ProjectType' not found and no '$FALLBACK.yaml'; falling back to 'software_dev'."
        $ProjectType = 'software_dev'
        $profilePath = $defaultPath
    } else {
        $profilePath = $freeformPath
    }
}

if (-not (Test-Path $profilePath)) {
    # Last-resort minimal snapshot so callers never hard-fail (freeform shape).
    [pscustomobject]@{
        id                = $FALLBACK
        name              = 'Freeform'
        source            = 'builtin-fallback'
        task_statuses     = @('open','in-progress','done','paused','cancelled')
        task_types        = @('task','note','chore')
        default_task_type = 'task'
        review_gate       = @{ required = $false; self_verify_allowed = $true }
    } | ConvertTo-Json -Depth 6
    exit 0
}

# Prefer the powershell-yaml module; degrade gracefully if absent.
$parsed = $null
if (Get-Module -ListAvailable -Name 'powershell-yaml' -ErrorAction SilentlyContinue) {
    try {
        Import-Module powershell-yaml -ErrorAction Stop
        $parsed = (Get-Content $profilePath -Raw) | ConvertFrom-Yaml
    } catch { $parsed = $null }
}

if ($parsed) {
    $parsed['source'] = $profilePath
    $parsed | ConvertTo-Json -Depth 12
} else {
    # No YAML parser available — emit a structured pointer rather than failing.
    Write-Warning "powershell-yaml not installed; emitting raw-pointer snapshot. Install with: Install-Module powershell-yaml -Scope CurrentUser"
    [pscustomobject]@{
        id           = $ProjectType
        source       = $profilePath
        parsed       = $false
        note         = 'Install powershell-yaml for a structured snapshot; raw YAML available at source path.'
        raw_yaml     = (Get-Content $profilePath -Raw)
    } | ConvertTo-Json -Depth 6
}
