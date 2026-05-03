<#
.SYNOPSIS
    Non-interactive helper for g-skl-tier-setup SETUP and ENABLE operations.

.DESCRIPTION
    Produces the same file outputs as the in-chat SETUP flow but from a script, for CI or unattended
    installs. Not the primary entry point — prefer the in-chat agent flow for interactive use. This
    script is per the D015 convention: canonical scripts live in gald3r_template_full/.cursor/skills/{skill}/scripts/.

    SETUP mode:
      - Reads a tiers definition from a JSON file (-DefinitionPath) or accepts repeated -Tier blocks
      - Writes .gald3r/release_profiles/{name}.yaml for each tier
      - Scaffolds template_{name}/ directories with .gitkeep
      - Appends tier_system=enabled and tier_names=[...] to .gald3r/.identity

    ENABLE mode (partial — inference only):
      - Reads .gald3r/release_profiles/*.yaml to learn tier names
      - Scans .gald3r/subsystems/*.md and reports inferred min_tier: for each
      - Writes annotations when -Apply is passed; dry-run otherwise

.PARAMETER Operation
    SETUP | ENABLE

.PARAMETER DefinitionPath
    Path to a JSON file describing tiers (SETUP only). Schema:
      [
        {"name":"free","operational_requirement":"none","tier_prefix":"FREE","remote":"","destination":"{LOCAL}"},
        {"name":"pro","operational_requirement":"api-keys","tier_prefix":"PRO","remote":"","destination":"{LOCAL}"}
      ]

.PARAMETER Apply
    ENABLE only — actually write min_tier: to subsystem files. Without this flag the script reports what it would do.

.PARAMETER ProjectRoot
    Optional project root path. Defaults to the script's grandparent-of-grandparent (skill is under gald3r_template_full/.cursor/skills/ so root is ../../..).

.EXAMPLE
    .\scripts\tier_setup.ps1 -Operation SETUP -DefinitionPath .\tiers.json

.EXAMPLE
    .\scripts\tier_setup.ps1 -Operation ENABLE        # dry run
    .\scripts\tier_setup.ps1 -Operation ENABLE -Apply # write annotations
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('SETUP', 'ENABLE')]
    [string]$Operation,

    [string]$DefinitionPath,

    [switch]$Apply,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

# Resolve project root. When invoked from .../gald3r_template_full/.cursor/skills/g-skl-tier-setup/scripts/,
# the project root is four directories up. The -ProjectRoot override is for testing.
if (-not $ProjectRoot) {
    $here = Split-Path -Parent $PSCommandPath
    $ProjectRoot = (Get-Item (Join-Path $here '..\..\..\..\..')).FullName
}

if (-not (Test-Path (Join-Path $ProjectRoot '.gald3r'))) {
    Write-Host "ERROR: .gald3r/ not found at $ProjectRoot — run @g-setup first." -ForegroundColor Red
    exit 1
}

$profilesDir = Join-Path $ProjectRoot '.gald3r\release_profiles'
$identityFile = Join-Path $ProjectRoot '.gald3r\.identity'
$subsystemsDir = Join-Path $ProjectRoot '.gald3r\subsystems'

# ─── Tier name validator ────────────────────────────────────────────────────

function Test-TierName {
    param([string]$Name)
    if ($Name.Length -lt 2 -or $Name.Length -gt 20) { return $false }
    if ($Name -notmatch '^[a-z][a-z0-9-]*$') { return $false }
    $reserved = @('readme', 'all', 'none', 'default')
    if ($reserved -contains $Name.ToLower()) { return $false }
    return $true
}

# ─── SETUP ──────────────────────────────────────────────────────────────────

function Invoke-Setup {
    if (-not $DefinitionPath) {
        Write-Host "ERROR: -DefinitionPath required for SETUP mode." -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path $DefinitionPath)) {
        Write-Host "ERROR: Definition file not found: $DefinitionPath" -ForegroundColor Red
        exit 1
    }

    $tiers = Get-Content $DefinitionPath -Raw | ConvertFrom-Json
    if ($tiers.Count -lt 1) {
        Write-Host "ERROR: Definition must contain at least one tier." -ForegroundColor Red
        exit 1
    }

    foreach ($tier in $tiers) {
        if (-not (Test-TierName $tier.name)) {
            Write-Host "ERROR: Invalid tier name '$($tier.name)' — must be lowercase letters/digits/hyphens, 2–20 chars, not reserved." -ForegroundColor Red
            exit 1
        }
    }

    if (-not (Test-Path $profilesDir)) {
        New-Item -ItemType Directory -Path $profilesDir | Out-Null
    }

    # Build included_tiers cumulatively (tier N includes tiers 1..N)
    $names = $tiers | ForEach-Object { $_.name }

    for ($i = 0; $i -lt $tiers.Count; $i++) {
        $tier = $tiers[$i]
        $includedTiers = $names[0..$i] -join ', '

        $opReq = if ($tier.operational_requirement) { $tier.operational_requirement } else { 'none' }
        $prefix = if ($tier.tier_prefix) { $tier.tier_prefix } else { $tier.name.Substring(0, 1).ToUpper() }
        $remote = if ($tier.remote) { $tier.remote } else { '' }
        $destination = if ($tier.destination) { $tier.destination } else { '{LOCAL}' }
        $description = if ($tier.description) { $tier.description } else { "$($tier.name) tier" }

        $yaml = @"
name: $($tier.name)
tier_prefix: $prefix
template_dir: template_$($tier.name)/
destination: $destination
remote: $remote
included_tiers: [$includedTiers]
operational_requirement: $opReq
description: "$description"
"@

        $outPath = Join-Path $profilesDir "$($tier.name).yaml"
        Set-Content -Path $outPath -Value $yaml -Encoding UTF8
        Write-Host "  wrote $outPath"

        # Scaffold template directory
        $tplDir = Join-Path $ProjectRoot "template_$($tier.name)"
        if (-not (Test-Path $tplDir)) {
            New-Item -ItemType Directory -Path $tplDir | Out-Null
            Set-Content -Path (Join-Path $tplDir '.gitkeep') -Value '' -Encoding UTF8
            Write-Host "  scaffolded $tplDir (with .gitkeep)"
        } else {
            Write-Host "  template_$($tier.name)/ already exists — left untouched"
        }
    }

    # Update .gald3r/.identity
    if (Test-Path $identityFile) {
        $lines = Get-Content $identityFile
        $lines = $lines | Where-Object { $_ -notmatch '^tier_system=' -and $_ -notmatch '^tier_names=' }
        $lines += "tier_system=enabled"
        $lines += "tier_names=[$($names -join ',')]"
        Set-Content -Path $identityFile -Value $lines -Encoding UTF8
        Write-Host "  updated $identityFile"
    } else {
        Write-Host "WARN: .gald3r/.identity not found — create it manually with tier_system=enabled and tier_names=[...]" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "SETUP complete. Next: run this script with -Operation ENABLE to annotate subsystems."
}

# ─── ENABLE ─────────────────────────────────────────────────────────────────

function Invoke-Enable {
    if (-not (Test-Path $profilesDir)) {
        Write-Host "ERROR: .gald3r/release_profiles/ not found — run SETUP first." -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path $subsystemsDir)) {
        Write-Host "ERROR: .gald3r/subsystems/ not found — no subsystems to annotate." -ForegroundColor Red
        exit 1
    }

    # Parse tiers
    $tierList = @()
    foreach ($f in (Get-ChildItem $profilesDir -Filter '*.yaml')) {
        $content = Get-Content $f.FullName -Raw
        $name = if ($content -match '(?m)^name:\s*(.+)$') { $Matches[1].Trim() } else { $f.BaseName }
        $opReq = if ($content -match '(?m)^operational_requirement:\s*(.+)$') { $Matches[1].Trim() } else { 'none' }
        $includedCount = 0
        if ($content -match '(?m)^included_tiers:\s*\[([^\]]+)\]') {
            $includedCount = ($Matches[1] -split ',').Count
        }
        $tierList += [PSCustomObject]@{
            Name = $name
            OpReq = $opReq
            IncludedCount = $includedCount
        }
    }

    # Sort ascending by included_tiers count (lowest tier first)
    $tierList = $tierList | Sort-Object IncludedCount
    $defaultTier = $tierList[0].Name
    $apiKeysTier = ($tierList | Where-Object OpReq -eq 'api-keys' | Select-Object -First 1).Name
    $dockerTier = ($tierList | Where-Object OpReq -eq 'docker' | Select-Object -First 1).Name

    if (-not $apiKeysTier) { $apiKeysTier = ($tierList | Select-Object -Last 1).Name }
    if (-not $dockerTier) { $dockerTier = ($tierList | Select-Object -Last 1).Name }

    Write-Host "Tier list (lowest -> highest): $($tierList.Name -join ' -> ')"
    Write-Host "Default tier (no signals):     $defaultTier"
    Write-Host "API-keys tier:                 $apiKeysTier"
    Write-Host "Docker tier:                   $dockerTier"
    Write-Host ""

    $results = @()

    foreach ($f in (Get-ChildItem $subsystemsDir -Filter '*.md')) {
        $content = Get-Content $f.FullName -Raw
        $inferred = $defaultTier
        $signals = @()

        if ($content -match '(?im)docker|docker-compose|container|OKE|kubernetes|localhost:543[23]') {
            $inferred = $dockerTier
            $signals += 'docker'
        } elseif ($content -match '(?im)\bMCP\b|mcp server|mcp_tool|mcp__') {
            $inferred = $dockerTier
            $signals += 'MCP'
        } elseif ($content -match '(?im)postgres|pgvector|oracle thick|mysql') {
            $inferred = $dockerTier
            $signals += 'managed-db'
        } elseif ($content -match '(?im)api[_\-]?key|API Key|OPENAI_KEY|ANTHROPIC_|PERPLEXITY_') {
            $inferred = $apiKeysTier
            $signals += 'api-keys'
        } elseif ($content -match '(?im)openai|anthropic|perplexity') {
            $inferred = $apiKeysTier
            $signals += 'cloud-ai'
        } elseif ($content -match '(?im)vault_location|research/platforms|research/github|ingest[_-]doc|crawl4ai|playwright|firecrawl') {
            $inferred = $apiKeysTier
            $signals += 'vault-network'
        }

        # Check existing min_tier
        $existing = $null
        if ($content -match '(?m)^min_tier:\s*(\S+)') {
            $existing = $Matches[1].Trim()
        }

        $results += [PSCustomObject]@{
            File = $f.Name
            Existing = $existing
            Inferred = $inferred
            Signals = ($signals -join ',')
            WillChange = ($existing -ne $inferred)
        }
    }

    Write-Host "Inference results:"
    $results | ForEach-Object {
        $status = if ($null -eq $_.Existing) { 'NEW' } elseif ($_.WillChange) { "CHANGE $($_.Existing)->$($_.Inferred)" } else { "OK ($($_.Existing))" }
        $sig = if ($_.Signals) { "[$($_.Signals)]" } else { '' }
        Write-Host "  $($_.File.PadRight(48)) $status $sig"
    }

    if (-not $Apply) {
        Write-Host ""
        Write-Host "Dry run. Pass -Apply to write min_tier: annotations."
        return
    }

    # Apply annotations
    $written = 0
    foreach ($r in $results) {
        if (-not $r.WillChange -and $r.Existing) { continue }
        $path = Join-Path $subsystemsDir $r.File
        $content = Get-Content $path -Raw

        if ($content -match '(?m)^min_tier:\s*\S+') {
            $content = $content -replace '(?m)^min_tier:\s*\S+', "min_tier: $($r.Inferred)"
        } else {
            # Insert after 'name:' line
            $content = $content -replace '(?m)(^name:\s*.+$)', "`$1`r`nmin_tier: $($r.Inferred)"
        }

        Set-Content -Path $path -Value $content -Encoding UTF8 -NoNewline
        $written++
    }

    Write-Host ""
    Write-Host "Wrote $written subsystem annotations."

    # Run tier sync if available
    $syncScript = Join-Path $ProjectRoot 'scripts\platform_parity_sync.ps1'
    if (Test-Path $syncScript) {
        Write-Host "Running platform_parity_sync.ps1 -TierSync..."
        & $syncScript -TierSync
    } else {
        Write-Host "WARN: scripts/platform_parity_sync.ps1 not found — tier sync skipped." -ForegroundColor Yellow
    }
}

# ─── Main ───────────────────────────────────────────────────────────────────

switch ($Operation) {
    'SETUP'  { Invoke-Setup }
    'ENABLE' { Invoke-Enable }
}
