<#
.SYNOPSIS
    Manage the gald3r user settings profile (T1036).

.DESCRIPTION
    CLI helper for the two-layer gald3r user profile system:
      Layer 1 (global):       %APPDATA%\gald3r\user_profile.yaml  (Windows)
      Layer 2 (per-project):  <project>\.gald3r\.user_prefs.yaml  (gitignored)

    SECURITY: The profile never stores plaintext API key values.
    api_keys entries hold only environment variable names and optional keychain IDs.

.PARAMETER Action
    get             — Show the current effective profile (merges global + project prefs)
    set             — Update a single field (dot-path) in the global profile
    validate-keys   — Check whether each API key env var is set and non-empty
    migrate         — Migrate from legacy %APPDATA%\gald3r\user_config.json to user_profile.yaml

.PARAMETER Field
    Dot-path field to update for the 'set' action. Examples:
      personality.theme
      display_name
      updates.auto_upgrade
      api_keys.openai   (provide Value as a hashtable: @{env_var='OPENAI_API_KEY'})

.PARAMETER Value
    New value for the 'set' action (string, bool, hashtable depending on field).

.PARAMETER ProjectPath
    Optional. Path to a project directory. When provided:
      - 'get' merges project .user_prefs.yaml on top of global profile
      - 'set' writes to project .user_prefs.yaml instead of global profile

.PARAMETER Apply
    For 'set' and 'migrate': actually write changes. Default is dry-run.

.EXAMPLE
    # Show effective profile for a project
    .\manage_user_profile.ps1 -Action get -ProjectPath G:\MyProject

    # Set personality theme globally (dry-run)
    .\manage_user_profile.ps1 -Action set -Field personality.theme -Value norse

    # Apply globally
    .\manage_user_profile.ps1 -Action set -Field personality.theme -Value norse -Apply

    # Set personality theme for a specific project only
    .\manage_user_profile.ps1 -Action set -Field personality.theme -Value professional -ProjectPath G:\WorkProject -Apply

    # Validate API keys
    .\manage_user_profile.ps1 -Action validate-keys

    # Migrate from legacy user_config.json (dry-run)
    .\manage_user_profile.ps1 -Action migrate

    # Migrate and apply
    .\manage_user_profile.ps1 -Action migrate -Apply
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('get', 'set', 'validate-keys', 'migrate')]
    [string]$Action,

    [string]$Field,
    [object]$Value,
    [string]$ProjectPath,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Get-GlobalProfilePath {
    $appData = $env:APPDATA
    if (-not $appData) {
        $appData = Join-Path $HOME 'AppData\Roaming'
    }
    return Join-Path $appData 'gald3r\user_profile.yaml'
}

function Get-ProjectPrefsPath {
    param([string]$ProjectRoot)
    return Join-Path $ProjectRoot '.gald3r\.user_prefs.yaml'
}

function Read-YamlFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    # Use PowerShell-Yaml if available; else warn and return $null
    try {
        $content = Get-Content -Path $Path -Raw -Encoding UTF8
        if (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
            return ConvertFrom-Yaml $content
        } else {
            Write-Warning "PowerShell-Yaml module not installed. Install with: Install-Module powershell-yaml"
            Write-Host $content
            return $null
        }
    } catch {
        Write-Warning "Could not read YAML at ${Path}: $_"
        return $null
    }
}

function Write-YamlFile {
    param([string]$Path, [object]$Data)
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (Get-Command ConvertTo-Yaml -ErrorAction SilentlyContinue) {
        ConvertTo-Yaml $Data | Set-Content -Path $Path -Encoding UTF8
    } else {
        Write-Warning "PowerShell-Yaml not installed. Cannot write YAML. Install with: Install-Module powershell-yaml"
    }
}

function Get-NowIso {
    return (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
}

function New-DefaultProfile {
    return [ordered]@{
        schema_version = 2
        user_id        = [System.Guid]::NewGuid().ToString()
        display_name   = ''
        email          = ''
        created_at     = Get-NowIso
        updated_at     = Get-NowIso
        api_keys       = [ordered]@{}
        mcp_servers    = [ordered]@{}
        personality    = [ordered]@{
            theme             = 'silicon_valley'
            primary_character = 'random'
            animation_enabled = $true
            emoji_density     = 'normal'
        }
        skill_packs = @()
        plugins     = @()
        updates     = [ordered]@{
            check_frequency  = '24h'
            auto_upgrade     = $false
            notify_in_agent  = $true
            notify_in_throne = $true
            skip_versions    = @()
        }
    }
}

function Set-DotPath {
    param([hashtable]$Data, [string]$Path, [object]$NewValue)
    $parts = $Path -split '\.'
    $obj = $Data
    for ($i = 0; $i -lt ($parts.Count - 1); $i++) {
        $key = $parts[$i]
        if (-not $obj.ContainsKey($key)) {
            $obj[$key] = [ordered]@{}
        }
        $obj = $obj[$key]
    }
    $obj[$parts[-1]] = $NewValue
}

# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

function Invoke-Get {
    $globalPath = Get-GlobalProfilePath
    Write-Host "Global profile: $globalPath"

    $global = Read-YamlFile $globalPath
    if ($null -eq $global) {
        Write-Warning "Global profile not found at $globalPath"
        Write-Host "Run with -Action migrate to create from legacy config, or:"
        Write-Host "  .\manage_user_profile.ps1 -Action set -Field display_name -Value YourName -Apply"
        return
    }

    if ($ProjectPath) {
        $prefsPath = Get-ProjectPrefsPath $ProjectPath
        Write-Host "Project prefs: $prefsPath"
        $prefs = Read-YamlFile $prefsPath
        if ($prefs) {
            Write-Host "(Project prefs loaded — overrides apply)"
        }
    }

    Write-Host ""
    Write-Host "=== Effective Profile ===" -ForegroundColor Cyan

    Write-Host "Identity:"
    Write-Host "  user_id:      $($global.user_id)"
    Write-Host "  display_name: $($global.display_name)"
    Write-Host "  email:        $($global.email)"

    Write-Host ""
    Write-Host "Personality:"
    $personality = $global.personality
    if ($ProjectPath -and $prefs -and $prefs.personality) {
        $personality = $prefs.personality
        Write-Host "  (project override active)"
    }
    Write-Host "  theme:             $($personality.theme)"
    Write-Host "  primary_character: $($personality.primary_character)"
    Write-Host "  animation_enabled: $($personality.animation_enabled)"
    Write-Host "  emoji_density:     $($personality.emoji_density)"

    Write-Host ""
    Write-Host "API Keys (env-var references — never values):"
    if ($global.api_keys -and $global.api_keys.Count -gt 0) {
        foreach ($name in $global.api_keys.Keys) {
            $ref = $global.api_keys[$name]
            $envVar = if ($ref -is [hashtable]) { $ref.env_var } else { $ref }
            $isSet = [bool]([System.Environment]::GetEnvironmentVariable($envVar))
            $status = if ($isSet) { "[OK]" } else { "[MISSING]" }
            $color  = if ($isSet) { 'Green' } else { 'Red' }
            Write-Host "  $name → $envVar $status" -ForegroundColor $color
        }
    } else {
        Write-Host "  (none configured)"
    }

    Write-Host ""
    Write-Host "MCP Servers:"
    $mcpServers = $global.mcp_servers
    if ($ProjectPath -and $prefs -and $prefs.mcp_servers -and $prefs.mcp_servers.Count -gt 0) {
        foreach ($key in $prefs.mcp_servers.Keys) {
            $mcpServers[$key] = $prefs.mcp_servers[$key]
        }
        Write-Host "  (project MCP overrides active)"
    }
    if ($mcpServers -and $mcpServers.Count -gt 0) {
        foreach ($name in $mcpServers.Keys) {
            $entry = $mcpServers[$name]
            $url = if ($entry -is [hashtable]) { $entry.url } else { $entry }
            Write-Host "  $name → $url"
        }
    } else {
        Write-Host "  (none configured)"
    }

    Write-Host ""
    Write-Host "Skill Packs ($($global.skill_packs.Count)):"
    foreach ($sp in $global.skill_packs) {
        $state = if ($sp.enabled) { "enabled" } else { "disabled" }
        Write-Host "  $($sp.id) [$state]"
    }

    Write-Host ""
    Write-Host "Updates:"
    Write-Host "  check_frequency: $($global.updates.check_frequency)"
    Write-Host "  auto_upgrade:    $($global.updates.auto_upgrade)"
    Write-Host "  notify_in_agent: $($global.updates.notify_in_agent)"
}

function Invoke-Set {
    if (-not $Field) {
        Write-Error "-Field is required for the 'set' action."
        return
    }
    if ($null -eq $Value) {
        Write-Error "-Value is required for the 'set' action."
        return
    }

    if ($ProjectPath) {
        $path = Get-ProjectPrefsPath $ProjectPath
        Write-Host "Scope: project prefs → $path"
        $data = Read-YamlFile $path
        if ($null -eq $data) {
            # Bootstrap minimal project prefs
            $identityPath = Join-Path $ProjectPath '.gald3r\.identity'
            $projectId = ''
            if (Test-Path $identityPath) {
                foreach ($line in Get-Content $identityPath) {
                    if ($line -match '^project_id=(.+)$') { $projectId = $Matches[1].Trim(); break }
                }
            }
            $data = [ordered]@{ schema_version = 1; project_id = $projectId }
        }
        Set-DotPath -Data $data -Path $Field -NewValue $Value
        if ($Apply) {
            Write-YamlFile $path $data
            Write-Host "Written: $path" -ForegroundColor Green
        } else {
            Write-Host "(Dry-run) Would write to: $path" -ForegroundColor Yellow
            Write-Host "  Field: $Field = $Value"
        }
    } else {
        $path = Get-GlobalProfilePath
        Write-Host "Scope: global profile → $path"
        $data = Read-YamlFile $path
        if ($null -eq $data) {
            $data = New-DefaultProfile
            Write-Host "Global profile not found — creating with defaults."
        }
        Set-DotPath -Data $data -Path $Field -NewValue $Value
        $data.updated_at = Get-NowIso
        if ($Apply) {
            Write-YamlFile $path $data
            Write-Host "Written: $path" -ForegroundColor Green
        } else {
            Write-Host "(Dry-run) Would write to: $path" -ForegroundColor Yellow
            Write-Host "  Field: $Field = $Value"
            Write-Host "Pass -Apply to write."
        }
    }
}

function Invoke-ValidateKeys {
    $globalPath = Get-GlobalProfilePath
    $global = Read-YamlFile $globalPath
    if ($null -eq $global) {
        Write-Warning "No global profile at $globalPath"
        return
    }
    if (-not $global.api_keys -or $global.api_keys.Count -eq 0) {
        Write-Host "No API keys configured in profile."
        return
    }
    Write-Host "API Key Validation:" -ForegroundColor Cyan
    $ok = 0; $missing = 0
    foreach ($name in $global.api_keys.Keys) {
        $ref = $global.api_keys[$name]
        $envVar = if ($ref -is [hashtable]) { $ref.env_var } else { $ref }
        $val = [System.Environment]::GetEnvironmentVariable($envVar)
        if ($val) {
            Write-Host "  [OK]      $name → $envVar" -ForegroundColor Green
            $ok++
        } else {
            Write-Host "  [MISSING] $name → $envVar" -ForegroundColor Red
            $missing++
        }
    }
    Write-Host ""
    Write-Host "$ok/$($ok + $missing) keys present."
}

function Invoke-Migrate {
    $legacyPath = Join-Path $env:APPDATA 'gald3r\user_config.json'
    $targetPath = Get-GlobalProfilePath

    if (-not (Test-Path $legacyPath)) {
        Write-Warning "Legacy config not found at: $legacyPath"
        Write-Host "Nothing to migrate."
        return
    }

    $legacy = Get-Content $legacyPath -Raw -Encoding UTF8 | ConvertFrom-Json

    $now = Get-NowIso
    $profile = [ordered]@{
        schema_version = 2
        user_id        = if ($legacy.user_id) { $legacy.user_id } else { [System.Guid]::NewGuid().ToString() }
        display_name   = if ($legacy.user_name) { $legacy.user_name } else { '' }
        email          = if ($legacy.email) { $legacy.email } else { '' }
        created_at     = if ($legacy.created_at) { $legacy.created_at } else { $now }
        updated_at     = $now
        api_keys       = [ordered]@{}
        mcp_servers    = [ordered]@{}
        personality    = [ordered]@{
            theme             = 'silicon_valley'
            primary_character = 'random'
            animation_enabled = $true
            emoji_density     = 'normal'
        }
        skill_packs = @()
        plugins     = @()
        updates     = [ordered]@{
            check_frequency  = '24h'
            auto_upgrade     = $false
            notify_in_agent  = $true
            notify_in_throne = $true
            skip_versions    = @()
        }
    }

    Write-Host "Migration plan:" -ForegroundColor Cyan
    Write-Host "  Source: $legacyPath"
    Write-Host "  Target: $targetPath"
    Write-Host "  user_id:      $($profile.user_id)"
    Write-Host "  display_name: $($profile.display_name)"
    Write-Host "  email:        $($profile.email)"

    if ($Apply) {
        if (Test-Path $targetPath) {
            Write-Warning "Target already exists: $targetPath"
            Write-Warning "Overwrite? Press Ctrl+C to cancel, or wait 5 seconds to continue..."
            Start-Sleep -Seconds 5
        }
        Write-YamlFile $targetPath $profile
        Write-Host "Migration complete: $targetPath" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "(Dry-run) Would write to: $targetPath" -ForegroundColor Yellow
        Write-Host "Pass -Apply to execute migration."
    }
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

switch ($Action) {
    'get'           { Invoke-Get }
    'set'           { Invoke-Set }
    'validate-keys' { Invoke-ValidateKeys }
    'migrate'       { Invoke-Migrate }
}
