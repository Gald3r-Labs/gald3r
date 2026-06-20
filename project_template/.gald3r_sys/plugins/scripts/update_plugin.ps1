# @subsystems: PLATFORM_INTEGRATION
<#
.SYNOPSIS
    Update installed gald3r plugins to their latest registry versions (T427).

.DESCRIPTION
    Implements the @g-plugin-update command per ADR-015 (plugin-system, SS-007).

    For each plugin (or one named via -PluginId) the script:
      1. Compares the installed version (.gald3r_sys/plugins/installed.yaml) with the
         latest version in the registry (registry.json, raw HTTPS).
      2. In -DryRun / --check mode prints an update-availability table and exits 0.
      3. Otherwise, for each plugin with a newer version (or any plugin when -Force):
         show changelog excerpt -> compatibility check -> backup current copy to
         .gald3r_sys/plugins/.backup/<id>-<old>/ -> download new version ->
         validate manifest -> conflict check -> show component diff -> confirm ->
         run new version's upgrade.ps1 (opt-in, confirmed) -> apply (copy new
         components, remove components no longer present) -> rewrite the
         installed.yaml entry -> print summary.

    If any step AFTER the backup is created fails, the plugin is automatically
    restored from backup and installed.yaml is rolled back to the previous version.
    The failure is appended to .gald3r/logs/plugin_update_failures.log.

    ASCII-safe, no BOM, PS 5.1 + PS 7 compatible (BUG-127 / BUG-132 convention,
    mirrors remove_plugin.ps1 / install_plugin.ps1). Status markers are plain ASCII:
    [UPDATE] [OK] [SKIP] [FAIL] [INFO] [WARN].

.PARAMETER PluginId
    Update only this plugin id. When omitted, every installed plugin is considered.

.PARAMETER DryRun
    Check for updates and print the availability table only. No backup, no download,
    no apply. Alias for the documented --check mode.

.PARAMETER Force
    Re-install / re-apply even when the installed version already equals the latest.

.PARAMETER NoBackup
    Skip creating the pre-update backup. NOT recommended -- disables auto-rollback.

.PARAMETER ProjectRoot
    Project root containing .gald3r_sys/ and .gald3r/ (defaults to current directory).

.PARAMETER RegistryUrl
    Override the registry URL. Defaults to the url in .gald3r_sys/config/plugins.yaml,
    then to the ADR-015 default raw GitHub registry.

.PARAMETER KeepBackups
    How many backup versions to retain per plugin after a successful update.
    Defaults to 3 (ADR-015 / T427). Older backups are pruned.

.PARAMETER AssumeYes
    Answer Y to every confirmation prompt (non-interactive / CI). The upgrade.ps1
    lifecycle script still only runs when this is set or the user confirms.

.EXAMPLE
    .\update_plugin.ps1 -DryRun
    Print the update-availability table for all installed plugins.

.EXAMPLE
    .\update_plugin.ps1 -PluginId gald3r-git-toolkit
    Update a single plugin interactively.

.EXAMPLE
    .\update_plugin.ps1 -Force -AssumeYes
    Re-apply every installed plugin from the registry, non-interactively.
#>

[CmdletBinding()]
param(
    [string] $PluginId,

    [Alias('Check')]
    [switch] $DryRun,

    [switch] $Force,

    [switch] $NoBackup,

    [string] $ProjectRoot = (Get-Location).Path,

    [string] $RegistryUrl,

    [int] $KeepBackups = 3,

    [switch] $AssumeYes
)

$ErrorActionPreference = 'Stop'

# ----------------------------------------------------------------------------
# ADR-015 defaults
# ----------------------------------------------------------------------------
$DefaultRegistryUrl = 'https://raw.githubusercontent.com/gald3r/plugin-registry/main/registry.json'

# Plugin subdir -> canonical component target dir + file glob (ADR-015 Component Mapping).
# 'skills' is folder-per-skill; the rest are flat files.
$ComponentMap = @(
    [pscustomobject]@{ Sub = 'skills';   Target = 'skills';   FolderPer = $true  }
    [pscustomobject]@{ Sub = 'commands'; Target = 'commands'; FolderPer = $false }
    [pscustomobject]@{ Sub = 'agents';   Target = 'agents';   FolderPer = $false }
    [pscustomobject]@{ Sub = 'rules';    Target = 'rules';    FolderPer = $false }
    [pscustomobject]@{ Sub = 'hooks';    Target = 'hooks';    FolderPer = $false }
)

# ----------------------------------------------------------------------------
# Output helpers (ASCII-safe markers)
# ----------------------------------------------------------------------------
function Write-Status {
    param(
        [ValidateSet('UPDATE', 'OK', 'SKIP', 'FAIL', 'INFO', 'WARN')]
        [string] $Marker,
        [string] $Message,
        [int]    $Indent = 0
    )
    $color = switch ($Marker) {
        'OK'     { 'Green' }
        'FAIL'   { 'Red' }
        'WARN'   { 'Yellow' }
        'SKIP'   { 'DarkGray' }
        'UPDATE' { 'Cyan' }
        default  { 'Gray' }
    }
    $pad = ' ' * $Indent
    Write-Host ("{0}[{1}] {2}" -f $pad, $Marker, $Message) -ForegroundColor $color
}

# ----------------------------------------------------------------------------
# Minimal YAML read / write for installed.yaml
# ----------------------------------------------------------------------------
# installed.yaml shape (ADR-015 install ledger):
#
#   plugins:
#     gald3r-git-toolkit:
#       version: 1.2.0
#       source: https://github.com/owner/repo
#       installed_at: 2026-05-01T00:00:00Z
#       components:
#         commands: [g-git-sync.md]
#         hooks: [g-git-sync-hook.ps1]
#
# This is a deliberately small, dependency-free reader/writer (no powershell-yaml
# module required, PS5.1 compatible). It supports exactly the nesting installed.yaml
# uses. If a future install_plugin.ps1 ships a shared ledger helper, prefer it.

function Read-InstalledLedger {
    param([string] $Path)

    $result = [ordered]@{}
    if (-not (Test-Path -LiteralPath $Path)) { return $result }

    $lines = Get-Content -LiteralPath $Path -Encoding UTF8
    $curPlugin = $null
    $curComponentType = $null
    $inComponents = $false

    foreach ($raw in $lines) {
        if ($raw -match '^\s*#' -or $raw.Trim() -eq '') { continue }
        # indent depth (2 spaces per level)
        $indent = ($raw.Length - $raw.TrimStart(' ').Length)
        $line = $raw.Trim()

        if ($indent -eq 0) {
            # top-level key (expect 'plugins:')
            $curPlugin = $null
            continue
        }

        if ($indent -eq 2 -and $line.EndsWith(':')) {
            # plugin id
            $curPlugin = $line.TrimEnd(':').Trim()
            $result[$curPlugin] = [ordered]@{
                version      = $null
                source       = $null
                installed_at = $null
                components   = [ordered]@{}
            }
            $inComponents = $false
            $curComponentType = $null
            continue
        }

        if ($null -eq $curPlugin) { continue }

        if ($indent -eq 4) {
            if ($line -eq 'components:') {
                $inComponents = $true
                $curComponentType = $null
                continue
            }
            $inComponents = $false
            if ($line -match '^([A-Za-z0-9_]+):\s*(.*)$') {
                $key = $Matches[1]
                $val = $Matches[2].Trim().Trim('"').Trim("'")
                if ($key -in @('version', 'source', 'installed_at')) {
                    $result[$curPlugin][$key] = $val
                }
            }
            continue
        }

        if ($inComponents -and $indent -eq 6) {
            if ($line -match '^([A-Za-z0-9_]+):\s*\[(.*)\]\s*$') {
                # inline list:  commands: [a.md, b.md]
                $ctype = $Matches[1]
                $items = @()
                if ($Matches[2].Trim() -ne '') {
                    $items = $Matches[2] -split ',' | ForEach-Object { $_.Trim().Trim('"').Trim("'") } | Where-Object { $_ -ne '' }
                }
                $result[$curPlugin].components[$ctype] = @($items)
                $curComponentType = $null
            }
            elseif ($line -match '^([A-Za-z0-9_]+):\s*$') {
                # block list header
                $curComponentType = $Matches[1]
                $result[$curPlugin].components[$curComponentType] = @()
            }
            continue
        }

        if ($inComponents -and $indent -ge 8 -and $line.StartsWith('- ') -and $curComponentType) {
            $item = $line.Substring(2).Trim().Trim('"').Trim("'")
            $result[$curPlugin].components[$curComponentType] += $item
            continue
        }
    }

    return $result
}

function Write-InstalledLedger {
    param(
        [System.Collections.Specialized.OrderedDictionary] $Ledger,
        [string] $Path
    )

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('# gald3r plugin install ledger (installed.yaml) -- ADR-015')
    [void]$sb.AppendLine('plugins:')
    foreach ($id in $Ledger.Keys) {
        $entry = $Ledger[$id]
        [void]$sb.AppendLine(('  {0}:' -f $id))
        if ($null -ne $entry.version)      { [void]$sb.AppendLine(('    version: {0}' -f $entry.version)) }
        if ($null -ne $entry.source)       { [void]$sb.AppendLine(('    source: {0}' -f $entry.source)) }
        if ($null -ne $entry.installed_at) { [void]$sb.AppendLine(('    installed_at: {0}' -f $entry.installed_at)) }
        if ($entry.components -and $entry.components.Keys.Count -gt 0) {
            [void]$sb.AppendLine('    components:')
            foreach ($ctype in $entry.components.Keys) {
                $items = @($entry.components[$ctype])
                $joined = ($items | ForEach-Object { $_ }) -join ', '
                [void]$sb.AppendLine(('      {0}: [{1}]' -f $ctype, $joined))
            }
        }
    }

    # ASCII-safe, no BOM
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $sb.ToString(), $utf8NoBom)
}

# ----------------------------------------------------------------------------
# Registry access
# ----------------------------------------------------------------------------
function Resolve-RegistryUrl {
    param([string] $Override, [string] $ConfigPath)
    if ($Override) { return $Override }
    if (Test-Path -LiteralPath $ConfigPath) {
        foreach ($raw in (Get-Content -LiteralPath $ConfigPath -Encoding UTF8)) {
            if ($raw -match '^\s*registry_url\s*:\s*(.+)$') {
                return $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
    }
    return $DefaultRegistryUrl
}

function Get-Registry {
    param([string] $Url)
    # Local file path support (test fixture) + remote https.
    if (Test-Path -LiteralPath $Url) {
        return (Get-Content -LiteralPath $Url -Raw -Encoding UTF8 | ConvertFrom-Json)
    }
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -ErrorAction Stop
        return ($resp.Content | ConvertFrom-Json)
    }
    catch {
        throw "Failed to fetch registry from '$Url': $($_.Exception.Message)"
    }
}

function Get-RegistryEntry {
    param($Registry, [string] $Id)
    if (-not $Registry) { return $null }
    # registry.json shape: { "plugins": { "<id>": { "version": "...", "source": "...", ... } } }
    $plugins = $null
    if ($Registry.PSObject.Properties.Name -contains 'plugins') { $plugins = $Registry.plugins }
    else { $plugins = $Registry }
    if (-not $plugins) { return $null }
    if ($plugins.PSObject.Properties.Name -contains $Id) { return $plugins.$Id }
    return $null
}

# ----------------------------------------------------------------------------
# SemVer compare ( -1 / 0 / 1 ), tolerant of leading 'v'
# ----------------------------------------------------------------------------
function Compare-SemVer {
    param([string] $A, [string] $B)
    $na = ($A -replace '^v', '') -replace '[-+].*$', ''
    $nb = ($B -replace '^v', '') -replace '[-+].*$', ''
    $pa = @($na -split '\.') + @('0', '0', '0')
    $pb = @($nb -split '\.') + @('0', '0', '0')
    for ($i = 0; $i -lt 3; $i++) {
        $ia = 0; [void][int]::TryParse($pa[$i], [ref]$ia)
        $ib = 0; [void][int]::TryParse($pb[$i], [ref]$ib)
        if ($ia -lt $ib) { return -1 }
        if ($ia -gt $ib) { return 1 }
    }
    return 0
}

# ----------------------------------------------------------------------------
# Manifest validation -- delegate to sibling validate_plugin_manifest.ps1 when
# present (DRY, g-rl-04); fall back to a minimal built-in check otherwise.
# ----------------------------------------------------------------------------
function Test-PluginManifest {
    param([string] $PluginDir, [string] $ScriptsDir)

    $validator = Join-Path $ScriptsDir 'validate_plugin_manifest.ps1'
    $manifest = Join-Path $PluginDir 'gald3r-plugin.yaml'

    if (Test-Path -LiteralPath $validator) {
        & $validator -PluginDir $PluginDir
        return ($LASTEXITCODE -eq 0)
    }

    # Built-in minimal validation (no sibling yet).
    if (-not (Test-Path -LiteralPath $manifest)) {
        Write-Status -Marker WARN -Message "No gald3r-plugin.yaml in $PluginDir" -Indent 2
        return $false
    }
    $hasId = $false; $hasVer = $false
    foreach ($raw in (Get-Content -LiteralPath $manifest -Encoding UTF8)) {
        if ($raw -match '^\s*id\s*:') { $hasId = $true }
        if ($raw -match '^\s*version\s*:') { $hasVer = $true }
    }
    return ($hasId -and $hasVer)
}

# ----------------------------------------------------------------------------
# Changelog excerpt: section(s) between newVer and oldVer headers (limit 20 lines)
# ----------------------------------------------------------------------------
function Get-ChangelogExcerpt {
    param([string] $PluginDir, [string] $OldVer, [string] $NewVer)

    $cl = Join-Path $PluginDir 'CHANGELOG.md'
    if (-not (Test-Path -LiteralPath $cl)) { return $null }

    $lines = Get-Content -LiteralPath $cl -Encoding UTF8
    $collect = @()
    $emitting = $false
    foreach ($line in $lines) {
        if ($line -match '^\s*#{1,3}\s*\[?v?([0-9]+\.[0-9]+\.[0-9]+)') {
            $ver = $Matches[1]
            if ((Compare-SemVer $ver $NewVer) -eq 0) { $emitting = $true }
            elseif ((Compare-SemVer $ver $OldVer) -le 0) { $emitting = $false; break }
        }
        if ($emitting) { $collect += $line }
        if ($collect.Count -ge 20) { break }
    }
    if ($collect.Count -eq 0) { return $null }
    return ($collect -join "`n")
}

# ----------------------------------------------------------------------------
# Confirmation
# ----------------------------------------------------------------------------
function Confirm-Action {
    param([string] $Prompt)
    if ($AssumeYes) { return $true }
    $ans = Read-Host "$Prompt [Y/n]"
    return ($ans -eq '' -or $ans -match '^(y|yes)$')
}

# ----------------------------------------------------------------------------
# Failure logging
# ----------------------------------------------------------------------------
function Write-FailureLog {
    param([string] $LogPath, [string] $Id, [string] $OldVer, [string] $NewVer, [string] $Reason)
    $dir = Split-Path -Parent $LogPath
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $entry = "{0} plugin={1} from={2} to={3} reason={4}" -f $ts, $Id, $OldVer, $NewVer, $Reason
    Add-Content -LiteralPath $LogPath -Value $entry -Encoding UTF8
}

# ----------------------------------------------------------------------------
# Component enumeration / copy / removal
# ----------------------------------------------------------------------------
function Get-ComponentInventory {
    param([string] $PluginDir)
    # Returns ordered map: componentType -> string[] of relative names.
    $inv = [ordered]@{}
    foreach ($map in $ComponentMap) {
        $subDir = Join-Path $PluginDir $map.Sub
        if (-not (Test-Path -LiteralPath $subDir)) { continue }
        if ($map.FolderPer) {
            $names = Get-ChildItem -LiteralPath $subDir -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
        }
        else {
            $names = Get-ChildItem -LiteralPath $subDir -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
        }
        $inv[$map.Sub] = @($names)
    }
    return $inv
}

function Copy-Components {
    param([string] $PluginDir, [string] $GaldSysDir)
    foreach ($map in $ComponentMap) {
        $subDir = Join-Path $PluginDir $map.Sub
        if (-not (Test-Path -LiteralPath $subDir)) { continue }
        $targetRoot = Join-Path $GaldSysDir $map.Target
        if (-not (Test-Path -LiteralPath $targetRoot)) { New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null }
        if ($map.FolderPer) {
            Get-ChildItem -LiteralPath $subDir -Directory | ForEach-Object {
                $dest = Join-Path $targetRoot $_.Name
                if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
                Copy-Item -LiteralPath $_.FullName -Destination $dest -Recurse -Force
            }
        }
        else {
            Get-ChildItem -LiteralPath $subDir -File | ForEach-Object {
                Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetRoot $_.Name) -Force
            }
        }
    }
}

function Remove-Components {
    param(
        [System.Collections.Specialized.OrderedDictionary] $Inventory,
        [string] $GaldSysDir
    )
    foreach ($map in $ComponentMap) {
        if (-not $Inventory.Contains($map.Sub)) { continue }
        $targetRoot = Join-Path $GaldSysDir $map.Target
        foreach ($name in @($Inventory[$map.Sub])) {
            $dest = Join-Path $targetRoot $name
            if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
        }
    }
}

function Get-StaleComponents {
    param(
        [System.Collections.Specialized.OrderedDictionary] $OldInv,
        [System.Collections.Specialized.OrderedDictionary] $NewInv
    )
    # components present in old but not new -> must be removed after apply.
    $stale = [ordered]@{}
    foreach ($map in $ComponentMap) {
        if (-not $OldInv.Contains($map.Sub)) { continue }
        $newNames = @()
        if ($NewInv.Contains($map.Sub)) { $newNames = @($NewInv[$map.Sub]) }
        $gone = @($OldInv[$map.Sub] | Where-Object { $_ -notin $newNames })
        if ($gone.Count -gt 0) { $stale[$map.Sub] = $gone }
    }
    return $stale
}

function Show-ComponentDiff {
    param(
        [System.Collections.Specialized.OrderedDictionary] $OldInv,
        [System.Collections.Specialized.OrderedDictionary] $NewInv
    )
    $added = 0; $removed = 0; $kept = 0
    foreach ($map in $ComponentMap) {
        $o = @(); if ($OldInv.Contains($map.Sub)) { $o = @($OldInv[$map.Sub]) }
        $n = @(); if ($NewInv.Contains($map.Sub)) { $n = @($NewInv[$map.Sub]) }
        foreach ($name in $n) {
            if ($name -in $o) { $kept++ } else { $added++; Write-Status -Marker INFO -Message ("+ {0}/{1}" -f $map.Sub, $name) -Indent 4 }
        }
        foreach ($name in $o) {
            if ($name -notin $n) { $removed++; Write-Status -Marker INFO -Message ("- {0}/{1}" -f $map.Sub, $name) -Indent 4 }
        }
    }
    return [pscustomobject]@{ Added = $added; Removed = $removed; Kept = $kept }
}

# ----------------------------------------------------------------------------
# Backup / rollback / prune
# ----------------------------------------------------------------------------
function New-PluginBackup {
    param([string] $PluginDir, [string] $BackupRoot, [string] $Id, [string] $OldVer)
    if (-not (Test-Path -LiteralPath $BackupRoot)) { New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null }
    $dest = Join-Path $BackupRoot ("{0}-{1}" -f $Id, $OldVer)
    if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
    Copy-Item -LiteralPath $PluginDir -Destination $dest -Recurse -Force
    return $dest
}

function Restore-PluginBackup {
    param([string] $BackupDir, [string] $PluginDir)
    if (Test-Path -LiteralPath $PluginDir) { Remove-Item -LiteralPath $PluginDir -Recurse -Force }
    Copy-Item -LiteralPath $BackupDir -Destination $PluginDir -Recurse -Force
}

function Remove-OldBackups {
    param([string] $BackupRoot, [string] $Id, [int] $Keep)
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return }
    $backups = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like ("{0}-*" -f $Id) } |
        Sort-Object -Property LastWriteTimeUtc -Descending
    if (@($backups).Count -le $Keep) { return }
    @($backups) | Select-Object -Skip $Keep | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
        Write-Status -Marker INFO -Message ("Pruned old backup {0}" -f $_.Name) -Indent 2
    }
}

# ----------------------------------------------------------------------------
# Download a plugin version into a staging dir.
# Local 'source' path => copy (test fixtures). Remote git url => throws if no download helper present.
# ----------------------------------------------------------------------------
function Get-PluginVersion {
    param([string] $Source, [string] $Version, [string] $StagingDir)

    if (Test-Path -LiteralPath $StagingDir) { Remove-Item -LiteralPath $StagingDir -Recurse -Force }
    New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

    if ($Source -and (Test-Path -LiteralPath $Source)) {
        # Local fixture / vendored source: a versioned subdir or the dir itself.
        $verDir = Join-Path $Source $Version
        $src = if (Test-Path -LiteralPath $verDir) { $verDir } else { $Source }
        # -Path (not -LiteralPath) so the trailing wildcard expands to copy contents.
        Copy-Item -Path (Join-Path $src '*') -Destination $StagingDir -Recurse -Force
        return $true
    }

    if ($Source -and ($Source -match '^https?://')) {
        # Remote fetch path. The registry contract (ADR-015) is "single HTTPS GET";
        # the concrete archive/tag fetch is owned by install_plugin.ps1 (not yet
        # present in this absorbed tree). Use it if available to stay DRY.
        $scriptsDir = Split-Path -Parent $PSCommandPath
        $installer = Join-Path $scriptsDir 'install_plugin.ps1'
        if (Test-Path -LiteralPath $installer) {
            & $installer -Source $Source -Version $Version -DownloadOnly -OutDir $StagingDir
            return ($LASTEXITCODE -eq 0)
        }
        throw "Remote download requires install_plugin.ps1 (download helper) which is not present. Source: $Source"
    }

    throw "Unresolvable plugin source: '$Source'"
}

# ============================================================================
# Main
# ============================================================================
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$GaldSysDir  = Join-Path $ProjectRoot '.gald3r_sys'
$PluginsDir  = Join-Path $GaldSysDir 'plugins'
$ScriptsDir  = Join-Path $PluginsDir 'scripts'
$BackupRoot  = Join-Path $PluginsDir '.backup'
$LedgerPath  = Join-Path $PluginsDir 'installed.yaml'
$ConfigPath  = Join-Path $GaldSysDir 'config/plugins.yaml'
$FailLog     = Join-Path $ProjectRoot '.gald3r/logs/plugin_update_failures.log'

if (-not (Test-Path -LiteralPath $PluginsDir)) {
    Write-Status -Marker FAIL -Message "No .gald3r_sys/plugins directory at $PluginsDir"
    exit 1
}

$ledger = Read-InstalledLedger -Path $LedgerPath
if ($ledger.Keys.Count -eq 0) {
    Write-Status -Marker INFO -Message "No plugins installed (installed.yaml empty or missing). Nothing to update."
    exit 0
}

$registryUrl = Resolve-RegistryUrl -Override $RegistryUrl -ConfigPath $ConfigPath
$registry = $null
try {
    $registry = Get-Registry -Url $registryUrl
}
catch {
    Write-Status -Marker FAIL -Message $_.Exception.Message
    exit 1
}

# Select target ids
$targetIds = if ($PluginId) {
    if (-not $ledger.Contains($PluginId)) {
        Write-Status -Marker FAIL -Message "Plugin '$PluginId' is not installed."
        exit 1
    }
    @($PluginId)
}
else {
    @($ledger.Keys)
}

# Build update plan
$plan = @()
foreach ($id in $targetIds) {
    $installedVer = $ledger[$id].version
    $regEntry = Get-RegistryEntry -Registry $registry -Id $id
    if (-not $regEntry) {
        $plan += [pscustomobject]@{ Id = $id; Installed = $installedVer; Latest = '?'; Status = 'not in registry'; Actionable = $false }
        continue
    }
    $latestVer = [string]$regEntry.version
    $cmp = Compare-SemVer $installedVer $latestVer
    if ($cmp -lt 0) {
        $plan += [pscustomobject]@{ Id = $id; Installed = $installedVer; Latest = $latestVer; Status = 'update available'; Actionable = $true; Reg = $regEntry }
    }
    elseif ($Force) {
        $plan += [pscustomobject]@{ Id = $id; Installed = $installedVer; Latest = $latestVer; Status = 'reinstall (force)'; Actionable = $true; Reg = $regEntry }
    }
    else {
        $plan += [pscustomobject]@{ Id = $id; Installed = $installedVer; Latest = $latestVer; Status = 'up to date'; Actionable = $false }
    }
}

# Availability table
Write-Host ''
Write-Status -Marker UPDATE -Message 'Checking plugin updates...'
Write-Host ''
Write-Host ('  {0,-26} {1,-10} {2,-10} {3}' -f 'Plugin', 'Installed', 'Latest', 'Status')
Write-Host ('  {0} {1} {2} {3}' -f ('-' * 26), ('-' * 10), ('-' * 10), ('-' * 18))
foreach ($p in $plan) {
    Write-Host ('  {0,-26} {1,-10} {2,-10} {3}' -f $p.Id, $p.Installed, $p.Latest, $p.Status)
}
Write-Host ''

$actionable = @($plan | Where-Object { $_.Actionable })

if ($DryRun) {
    Write-Status -Marker INFO -Message ("{0} update(s) available (dry-run; nothing applied)." -f $actionable.Count)
    exit 0
}

if ($actionable.Count -eq 0) {
    Write-Status -Marker OK -Message 'All plugins up to date.'
    exit 0
}

if (-not (Confirm-Action ("{0} update(s) available. Apply?" -f $actionable.Count))) {
    Write-Status -Marker SKIP -Message 'Aborted by user.'
    exit 0
}

# Apply loop
$updated = 0
$failed  = 0

foreach ($p in $actionable) {
    $id = $p.Id
    $oldVer = $p.Installed
    $newVer = $p.Latest
    $pluginDir = Join-Path $PluginsDir $id
    $stagingDir = Join-Path $PluginsDir (".staging-{0}" -f $id)
    $backupDir = $null

    Write-Host ''
    Write-Status -Marker UPDATE -Message ("Updating {0} ({1} -> {2})..." -f $id, $oldVer, $newVer)

    try {
        # 2. Changelog excerpt (from currently-installed copy; best-effort)
        $excerpt = Get-ChangelogExcerpt -PluginDir $pluginDir -OldVer $oldVer -NewVer $newVer
        if ($excerpt) {
            Write-Status -Marker INFO -Message 'What changed (CHANGELOG excerpt):' -Indent 2
            foreach ($l in ($excerpt -split "`n")) { Write-Host ("       {0}" -f $l) }
        }

        # 3. Compatibility check (gald3r_min_version host floor, ADR-015)
        if ($p.Reg -and ($p.Reg.PSObject.Properties.Name -contains 'gald3r_min_version')) {
            Write-Status -Marker INFO -Message ("Requires gald3r host >= {0}" -f $p.Reg.gald3r_min_version) -Indent 2
        }

        # 4. Backup current plugin
        if (-not $NoBackup) {
            if (Test-Path -LiteralPath $pluginDir) {
                $backupDir = New-PluginBackup -PluginDir $pluginDir -BackupRoot $BackupRoot -Id $id -OldVer $oldVer
                Write-Status -Marker OK -Message ("Backed up {0} to .gald3r_sys/plugins/.backup/{1}-{2}/" -f $oldVer, $id, $oldVer) -Indent 2
            }
            else {
                Write-Status -Marker WARN -Message "Installed plugin dir missing; cannot back up source (ledger-only update)." -Indent 2
            }
        }
        else {
            Write-Status -Marker WARN -Message 'NoBackup: rollback unavailable for this plugin.' -Indent 2
        }

        # Old inventory (from disk if present, else from ledger)
        $oldInv = if (Test-Path -LiteralPath $pluginDir) {
            Get-ComponentInventory -PluginDir $pluginDir
        }
        else {
            $tmp = [ordered]@{}
            foreach ($k in $ledger[$id].components.Keys) { $tmp[$k] = @($ledger[$id].components[$k]) }
            $tmp
        }

        # 5. Download new version into staging
        $source = if ($p.Reg -and ($p.Reg.PSObject.Properties.Name -contains 'source')) { [string]$p.Reg.source } else { $ledger[$id].source }
        [void](Get-PluginVersion -Source $source -Version $newVer -StagingDir $stagingDir)
        Write-Status -Marker OK -Message ("Downloaded {0}" -f $newVer) -Indent 2

        # 6. Validate manifest of staged new version
        if (-not (Test-PluginManifest -PluginDir $stagingDir -ScriptsDir $ScriptsDir)) {
            throw "Manifest validation failed for staged $id $newVer"
        }
        Write-Status -Marker OK -Message 'Validated manifest' -Indent 2

        # 7/8. Component diff + conflict surface
        $newInv = Get-ComponentInventory -PluginDir $stagingDir
        Write-Status -Marker INFO -Message 'Component changes:' -Indent 2
        $diff = Show-ComponentDiff -OldInv $oldInv -NewInv $newInv

        # 9. Confirm apply
        if (-not (Confirm-Action ("Apply update for {0}?" -f $id))) {
            Write-Status -Marker SKIP -Message "Skipped $id by user." -Indent 2
            Remove-Item -LiteralPath $stagingDir -Recurse -Force -ErrorAction SilentlyContinue
            continue
        }

        # 10. upgrade.ps1 lifecycle (opt-in, confirmed)
        $upgradeScript = Join-Path $stagingDir 'upgrade.ps1'
        if (Test-Path -LiteralPath $upgradeScript) {
            if (Confirm-Action ("Run new version's upgrade.ps1 lifecycle script for {0}?" -f $id)) {
                Write-Status -Marker INFO -Message 'Running upgrade.ps1...' -Indent 2
                & $upgradeScript -ProjectRoot $ProjectRoot -FromVersion $oldVer -ToVersion $newVer
                if ($LASTEXITCODE -ne 0) { throw "upgrade.ps1 exited $LASTEXITCODE" }
            }
            else {
                Write-Status -Marker SKIP -Message 'Skipped upgrade.ps1 (user declined).' -Indent 2
            }
        }

        # 11. Apply: remove components that disappeared, then materialize the new plugin source.
        $stale = Get-StaleComponents -OldInv $oldInv -NewInv $newInv
        if ($stale.Keys.Count -gt 0) { Remove-Components -Inventory $stale -GaldSysDir $GaldSysDir }

        # Replace the versioned plugin source dir
        if (Test-Path -LiteralPath $pluginDir) { Remove-Item -LiteralPath $pluginDir -Recurse -Force }
        Move-Item -LiteralPath $stagingDir -Destination $pluginDir -Force

        # Copy components into canonical dirs
        Copy-Components -PluginDir $pluginDir -GaldSysDir $GaldSysDir

        # 12. Update ledger entry
        $components = [ordered]@{}
        foreach ($k in $newInv.Keys) { if (@($newInv[$k]).Count -gt 0) { $components[$k] = @($newInv[$k]) } }
        $ledger[$id] = [ordered]@{
            version      = $newVer
            source       = $source
            installed_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
            components   = $components
        }
        Write-InstalledLedger -Ledger $ledger -Path $LedgerPath

        # Prune old backups
        if (-not $NoBackup) { Remove-OldBackups -BackupRoot $BackupRoot -Id $id -Keep $KeepBackups }

        # 13. Summary
        Write-Status -Marker OK -Message ("Applied update ({0} updated, {1} added, {2} removed)" -f $diff.Kept, $diff.Added, $diff.Removed) -Indent 2
        Write-Status -Marker OK -Message ("{0} updated to {1}" -f $id, $newVer) -Indent 2
        $updated++
    }
    catch {
        $failed++
        $reason = $_.Exception.Message
        Write-Status -Marker FAIL -Message ("Update failed for {0}: {1}" -f $id, $reason) -Indent 2

        # Auto-rollback if a backup exists
        if ($backupDir -and (Test-Path -LiteralPath $backupDir)) {
            try {
                Restore-PluginBackup -BackupDir $backupDir -PluginDir $pluginDir
                # restore ledger entry to previous version (re-read original components from backup)
                $restInv = Get-ComponentInventory -PluginDir $pluginDir
                $restComponents = [ordered]@{}
                foreach ($k in $restInv.Keys) { if (@($restInv[$k]).Count -gt 0) { $restComponents[$k] = @($restInv[$k]) } }
                $ledger[$id] = [ordered]@{
                    version      = $oldVer
                    source       = $ledger[$id].source
                    installed_at = $ledger[$id].installed_at
                    components   = $restComponents
                }
                Write-InstalledLedger -Ledger $ledger -Path $LedgerPath
                # re-copy restored components into canonical dirs
                Copy-Components -PluginDir $pluginDir -GaldSysDir $GaldSysDir
                Write-Status -Marker OK -Message ("Rolled back {0} to {1}" -f $id, $oldVer) -Indent 2
            }
            catch {
                Write-Status -Marker FAIL -Message ("Rollback ALSO failed for {0}: {1}" -f $id, $_.Exception.Message) -Indent 2
            }
        }
        else {
            Write-Status -Marker WARN -Message 'No backup available; manual recovery may be required.' -Indent 2
        }

        Write-FailureLog -LogPath $FailLog -Id $id -OldVer $oldVer -NewVer $newVer -Reason $reason
    }
    finally {
        if (Test-Path -LiteralPath $stagingDir) { Remove-Item -LiteralPath $stagingDir -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

Write-Host ''
Write-Status -Marker INFO -Message ("Done. {0} updated, {1} failed." -f $updated, $failed)

if ($failed -gt 0) { exit 1 }
exit 0
