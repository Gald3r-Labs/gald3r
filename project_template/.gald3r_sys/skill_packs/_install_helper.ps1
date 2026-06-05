#Requires -Version 5.1
# _install_helper.ps1 — shared platform installer logic for personality and skill packs
# Sourced by pack install.ps1 scripts via: . "$PSScriptRoot\..\_install_helper.ps1"
#
# Platform discovery: reads .gald3r_sys/platforms/ to enumerate all supported platforms,
# then loads capabilities from .gald3r_sys/_platform_capabilities.json.
# Only installs to platforms whose folders actually exist in the target project.

param(
    [string]$ProjectRoot = (Get-Location).Path
)

# Locate .gald3r_sys from this helper's own path
$galdSysRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (!(Test-Path "$galdSysRoot\_platform_capabilities.json")) {
    # Fallback: walk up to find it
    $search = $PSScriptRoot
    for ($i = 0; $i -lt 6; $i++) {
        $search = Split-Path $search -Parent
        if (Test-Path "$search\.gald3r_sys\_platform_capabilities.json") {
            $galdSysRoot = $search
            break
        }
    }
}

# Load capabilities map
$capabilitiesPath = "$galdSysRoot\.gald3r_sys\_platform_capabilities.json"
if (Test-Path $capabilitiesPath) {
    $CAPABILITIES = Get-Content $capabilitiesPath -Raw | ConvertFrom-Json
} else {
    Write-Warning "Could not find _platform_capabilities.json at $capabilitiesPath — using minimal defaults"
    $CAPABILITIES = @{
        ".cursor" = @{ hasRules = $true;  rulesExt = ".mdc"; hasSkills = $true;  rulesDir = "rules"; skillsDir = "skills" }
        ".claude" = @{ hasRules = $true;  rulesExt = ".md";  hasSkills = $true;  rulesDir = "rules"; skillsDir = "skills" }
    }
}

# Discover all supported platform names from .gald3r_sys/platforms/
$platformsDir = "$galdSysRoot\.gald3r_sys\platforms"
if (Test-Path $platformsDir) {
    $KNOWN_PLATFORMS = (Get-ChildItem $platformsDir -Directory).Name
} else {
    $KNOWN_PLATFORMS = @(".cursor", ".claude", ".agent", ".codex", ".opencode", ".copilot")
}

function Get-ActivePlatforms([string]$ProjectRoot) {
    # Return only platforms that both exist in the project AND are in the capabilities map
    $active = @()
    foreach ($p in $KNOWN_PLATFORMS) {
        if (Test-Path (Join-Path $ProjectRoot $p)) {
            $active += $p
        }
    }
    return $active
}

function Get-PlatformCap([string]$platform) {
    # Get capability object for a platform, with safe defaults
    $cap = $CAPABILITIES.$platform
    if ($null -eq $cap) {
        return @{ hasRules = $false; rulesExt = ".md"; hasSkills = $false; rulesDir = "rules"; skillsDir = "skills"; copilotInstructions = $null }
    }
    # Normalize PSCustomObject to hashtable
    return @{
        hasRules           = [bool]$cap.hasRules
        rulesExt           = [string]$cap.rulesExt
        hasSkills          = [bool]$cap.hasSkills
        rulesDir           = [string]$cap.rulesDir
        skillsDir          = [string]$cap.skillsDir
        copilotInstructions = $cap.copilotInstructions
    }
}

function Install-Rules([string]$sourceDir, [string]$ProjectRoot, [string[]]$platforms) {
    if (!(Test-Path $sourceDir)) { return }
    $mdFiles = Get-ChildItem "$sourceDir\*.md" -ErrorAction SilentlyContinue
    if (!$mdFiles) { return }

    foreach ($p in $platforms) {
        $cfg = Get-PlatformCap $p

        # Copilot: append to copilot-instructions.md instead of a rules dir
        if ($cfg.copilotInstructions) {
            $ciPath = Join-Path $ProjectRoot $cfg.copilotInstructions
            New-Item -ItemType Directory -Force -Path (Split-Path $ciPath) | Out-Null
            foreach ($f in $mdFiles) {
                "`n---`n" + (Get-Content $f.FullName -Raw) | Add-Content $ciPath -Encoding UTF8
                Write-Host "  → $($cfg.copilotInstructions) (appended $($f.Name))"
            }
            continue
        }

        if (!$cfg.hasRules -or !$cfg.rulesDir) { continue }
        $destDir = Join-Path $ProjectRoot "$p\$($cfg.rulesDir)"
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        foreach ($f in $mdFiles) {
            $destName = $f.BaseName + $cfg.rulesExt
            Copy-Item $f.FullName (Join-Path $destDir $destName) -Force
            Write-Host "  → $p/$($cfg.rulesDir)/$destName"
        }
    }
}

function Remove-Rules([string[]]$fileBasenames, [string]$ProjectRoot, [string[]]$platforms) {
    foreach ($p in $platforms) {
        $cfg = Get-PlatformCap $p
        if ($cfg.copilotInstructions) { continue }  # copilot append is not reversible per-file safely
        if (!$cfg.hasRules -or !$cfg.rulesDir) { continue }
        $rulesDir = Join-Path $ProjectRoot "$p\$($cfg.rulesDir)"
        foreach ($base in $fileBasenames) {
            $target = Join-Path $rulesDir ($base + $cfg.rulesExt)
            if (Test-Path $target) {
                Remove-Item $target -Force
                Write-Host "  ✗ removed $p/$($cfg.rulesDir)/$($base + $cfg.rulesExt)"
            }
        }
    }
}

function Install-Skills([string]$sourceSkillsDir, [string]$ProjectRoot, [string[]]$platforms) {
    if (!(Test-Path $sourceSkillsDir)) { return }
    foreach ($p in $platforms) {
        $cfg = Get-PlatformCap $p
        if (!$cfg.hasSkills -or !$cfg.skillsDir) { continue }
        $destBase = Join-Path $ProjectRoot "$p\$($cfg.skillsDir)"
        foreach ($skillDir in Get-ChildItem $sourceSkillsDir -Directory) {
            $dest = Join-Path $destBase $skillDir.Name
            New-Item -ItemType Directory -Force -Path $dest | Out-Null
            Get-ChildItem $skillDir.FullName -Recurse | Where-Object { !$_.PSIsContainer } | ForEach-Object {
                $rel = $_.FullName.Substring($skillDir.FullName.Length)
                $target = "$dest$rel"
                New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
                Copy-Item $_.FullName $target -Force
            }
            Write-Host "  → $p/$($cfg.skillsDir)/$($skillDir.Name)/"
        }
    }
}

function Remove-Skills([string[]]$skillNames, [string]$ProjectRoot, [string[]]$platforms) {
    foreach ($p in $platforms) {
        $cfg = Get-PlatformCap $p
        if (!$cfg.hasSkills -or !$cfg.skillsDir) { continue }
        $skillsDir = Join-Path $ProjectRoot "$p\$($cfg.skillsDir)"
        foreach ($name in $skillNames) {
            # Never silently remove _evolved variants
            $evolved = Join-Path $skillsDir "${name}_evolved"
            if (Test-Path $evolved) {
                Write-Host "  ⚠ Skipping ${name}_evolved in $p (user-evolved — use --force to remove)"
                continue
            }
            $target = Join-Path $skillsDir $name
            if (Test-Path $target) {
                Remove-Item $target -Recurse -Force
                Write-Host "  ✗ removed $p/$($cfg.skillsDir)/$name/"
            }
        }
    }
}
