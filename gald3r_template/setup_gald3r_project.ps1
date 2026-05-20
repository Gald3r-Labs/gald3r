# setup_gald3r_project.ps1 - gald3r Installer & Updater
# =====================================================
# TWO MODES:
#   INSTALLER mode  : Run from this template folder to install gald3r INTO a target project.
#                     Prompts for target path, detects new/existing/versioned projects,
#                     lets user pick platforms. Run once per project.
#
#   SESSION mode    : Run from an already-installed project to regenerate platform dirs.
#                     Called by session-start hooks: .\setup_gald3r_project.ps1 -Platform auto
#
# Usage (installer / interactive):
#   .\setup_gald3r_project.ps1
#   .\setup_gald3r_project.ps1 -TargetPath "G:\MyProject" -Platforms cursor,claude
#
# Usage (session / non-interactive):
#   .\setup_gald3r_project.ps1 -Platform auto            # auto-detect running IDE
#   .\setup_gald3r_project.ps1 -Platform cursor          # cursor only
#   .\setup_gald3r_project.ps1 -Platform all             # all installed platforms
#   .\setup_gald3r_project.ps1 -Platform all -Clean      # wipe + regenerate
#   .\setup_gald3r_project.ps1 -Platform auto -Quiet     # for hooks

param(
    # ── Installer mode params ─────────────────────────────────────────────────
    [string]$TargetPath  = "",          # target project path (prompted if blank)
    [string[]]$Platforms = @(),         # platform list e.g. cursor,claude (prompted if blank)
    [switch]$DryRun,                    # show plan without writing anything
    [switch]$Force,                     # skip confirmation prompts

    # ── Session mode params (mirrors old setup_dev_env.ps1) ───────────────────
    [string]$Platform = "",             # auto | cursor | claude | agent | codex | opencode | copilot | all
    [switch]$Clean,                     # wipe target dirs before regenerating
    [switch]$Quiet                      # suppress non-essential output
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────────────────────────────────────────
# Detect which mode we are in
# ──────────────────────────────────────────────────────────────────────────────
$templateRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$templatePayload = Join-Path $templateRoot "gald3r_template"
$isInstallerMode = (Test-Path $templatePayload) -and ($Platform -eq "")

if (-not $isInstallerMode -and $Platform -eq "") {
    $Platform = "auto"
}

# ──────────────────────────────────────────────────────────────────────────────
# SHARED: Platform definitions
# ──────────────────────────────────────────────────────────────────────────────
$allPlatforms = [ordered]@{
    cursor   = @{ prefix = ".cursor";   cats = @("skills","agents","commands"); label = "Cursor IDE" }
    claude   = @{ prefix = ".claude";   cats = @("skills","agents","commands"); label = "Claude Code" }
    agent    = @{ prefix = ".agent";    cats = @("skills","agents","commands"); label = "Gemini / Antigravity" }
    codex    = @{ prefix = ".codex";    cats = @("skills","agents","commands"); label = "OpenAI Codex CLI" }
    opencode = @{ prefix = ".opencode"; cats = @("skills","agents","commands"); label = "OpenCode (sst.dev)" }
    copilot  = @{ prefix = ".copilot";  cats = @("commands");                  label = "GitHub Copilot" }
    windsurf = @{ prefix = ".windsurf"; cats = @("skills","agents","commands"); label = "Windsurf" }
    cline    = @{ prefix = ".cline";    cats = @("skills","agents","commands"); label = "Cline" }
    roo      = @{ prefix = ".roo-code"; cats = @("skills","agents","commands"); label = "Roo Code" }
    kiro     = @{ prefix = ".kiro";     cats = @("skills","agents","commands"); label = "Kiro" }
    augment  = @{ prefix = ".augment";  cats = @("skills","agents","commands"); label = "Augment Code" }
    aider    = @{ prefix = ".aider";    cats = @("skills","agents","commands"); label = "Aider" }
    goose    = @{ prefix = ".goose";    cats = @("skills","agents","commands"); label = "Goose (Block)" }
    warp     = @{ prefix = ".warp";     cats = @("skills","agents","commands"); label = "Warp Terminal" }
    openhands= @{ prefix = ".openhands";cats = @("skills","agents","commands"); label = "OpenHands" }
    replit   = @{ prefix = ".replit";   cats = @("skills","agents","commands"); label = "Replit Agent" }
}

# ──────────────────────────────────────────────────────────────────────────────
# SESSION MODE: regenerate platform dirs from .gald3r_sys/ (called by hooks)
# ──────────────────────────────────────────────────────────────────────────────
if (-not $isInstallerMode) {
    $projectRoot = $templateRoot  # when deployed, script lives at project root

    function Get-ActivePlatform {
        param([string]$ProjectRoot)
        if ($env:CURSOR_TRACE -or $env:VSCODE_PID)          { return @("cursor") }
        if ($env:CLAUDE_CODE  -or $env:ANTHROPIC_MODEL)     { return @("claude") }
        if ($env:GEMINI_CLI)                                  { return @("agent") }
        if ($env:OPENAI_CODEX -or $env:CODEX_CLI)           { return @("codex") }
        try {
            $parent = (Get-Process -Id $PID -ErrorAction SilentlyContinue).Parent
            if ($parent -and $parent.ProcessName -match "gemini") { return @("agent") }
        } catch {}
        $detected = @()
        foreach ($key in $allPlatforms.Keys) {
            $prefix = $allPlatforms[$key].prefix
            if (Test-Path (Join-Path $ProjectRoot $prefix)) { $detected += $key }
        }
        if ($detected.Count -gt 0) { return $detected }
        return @("cursor","claude")
    }

    $sysRoot = Join-Path $projectRoot ".gald3r_sys"
    if (-not (Test-Path $sysRoot)) {
        if (-not $Quiet) { Write-Warning ".gald3r_sys/ not found at $projectRoot — run installer first." }
        exit 1
    }

    $targets = switch ($Platform.ToLower()) {
        "auto" { Get-ActivePlatform -ProjectRoot $projectRoot }
        "all"  { $allPlatforms.Keys | Where-Object { Test-Path (Join-Path $projectRoot $allPlatforms[$_].prefix) } }
        default { @($Platform.ToLower()) }
    }

    function Sync-GaldContent {
        param([string]$Src, [string]$Dst, [bool]$CleanFirst)
        if (-not (Test-Path $Src)) { return 0 }
        New-Item -ItemType Directory -Force $Dst | Out-Null
        if ($CleanFirst) {
            Get-ChildItem $Dst -Filter "g-*" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse
        }
        $count = 0
        Get-ChildItem $Src -Recurse -File | ForEach-Object {
            $rel = $_.FullName.Substring($Src.Length + 1)
            $target = Join-Path $Dst $rel
            $targetDir = Split-Path $target
            if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Force $targetDir | Out-Null }
            # g- prefix: always overwrite. non-g-: only if not exists
            if ($rel -match "^g-" -or $rel -match "[/\\]g-" -or -not (Test-Path $target)) {
                Copy-Item $_.FullName $target -Force
                $count++
            }
        }
        return $count
    }

    foreach ($platKey in $targets) {
        if (-not $allPlatforms.ContainsKey($platKey)) { continue }
        $plat = $allPlatforms[$platKey]
        $platDst = Join-Path $projectRoot $plat.prefix

        # Phase 1: scaffold from .gald3r_sys/platforms/{prefix}
        $scaffoldSrc = Join-Path $sysRoot "platforms\$($plat.prefix)"
        if (Test-Path $scaffoldSrc) {
            New-Item -ItemType Directory -Force $platDst | Out-Null
            Get-ChildItem $scaffoldSrc -Recurse -File | ForEach-Object {
                $rel = $_.FullName.Substring($scaffoldSrc.Length + 1)
                $target = Join-Path $platDst $rel
                $targetDir = Split-Path $target
                if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Force $targetDir | Out-Null }
                if (-not (Test-Path $target)) { Copy-Item $_.FullName $target -Force }
            }
        }

        # Phase 2: universal content from .gald3r_sys/{skills,agents,commands,...}
        foreach ($cat in $plat.cats) {
            $catSrc = Join-Path $sysRoot $cat
            $catDst = Join-Path $platDst $cat
            $n = Sync-GaldContent -Src $catSrc -Dst $catDst -CleanFirst:$Clean.IsPresent
            if (-not $Quiet) { Write-Host "  $platKey/$cat: $n files synced" }
        }

        # Rules (with extension translation)
        $rulesSrc = Join-Path $sysRoot "rules"
        if (Test-Path $rulesSrc) {
            $rulesDst = Join-Path $platDst "rules"
            New-Item -ItemType Directory -Force $rulesDst | Out-Null
            Get-ChildItem $rulesSrc -File | ForEach-Object {
                $ext = if ($platKey -eq "cursor") { ".mdc" } else { ".md" }
                $destName = [System.IO.Path]::ChangeExtension($_.Name, $ext)
                $target = Join-Path $rulesDst $destName
                if ($_.Name -match "^g-" -or -not (Test-Path $target)) {
                    Copy-Item $_.FullName $target -Force
                }
            }
        }
    }

    if (-not $Quiet) { Write-Host "gald3r platform dirs regenerated." }
    exit 0
}

# ──────────────────────────────────────────────────────────────────────────────
# INSTALLER MODE
# ──────────────────────────────────────────────────────────────────────────────
function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║        gald3r Project Installer v1.4         ║" -ForegroundColor Cyan
    Write-Host "  ║   AI Development System for Modern IDEs      ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Detect-GaldVersion {
    param([string]$ProjectPath)
    # v1: symlink-based (.platforms/ or .skills/ symlinks)
    if ((Test-Path "$ProjectPath\.platforms") -or (Test-Path "$ProjectPath\.skills")) {
        return "v1-symlink"
    }
    # v3: .gald3r_sys/ present
    if (Test-Path "$ProjectPath\.gald3r_sys") {
        $ver = Get-Content "$ProjectPath\.gald3r_sys\VERSION" -ErrorAction SilentlyContinue
        return "v3-$ver"
    }
    # v2: .gald3r/ exists with phase-based tasks or old structure
    if (Test-Path "$ProjectPath\.gald3r\TASKS.md") {
        $tasks = Get-Content "$ProjectPath\.gald3r\TASKS.md" -ErrorAction SilentlyContinue -Raw
        if ($tasks -match "## Phase") { return "v2-phase" }
        return "v2-sequential"
    }
    # gald3r exists but no version markers
    if (Test-Path "$ProjectPath\.gald3r") { return "v2-unknown" }
    return "none"
}

function Merge-SectionMarker {
    param([string]$TargetFile, [string]$SourceFile, [string]$SectionTag)
    if (-not (Test-Path $SourceFile)) { return }
    $newContent = Get-Content $SourceFile -Raw -ErrorAction SilentlyContinue
    if (-not $newContent) { return }

    if (-not (Test-Path $TargetFile)) {
        Copy-Item $SourceFile $TargetFile -Force
        return
    }

    $existing = Get-Content $TargetFile -Raw
    $startMarker = "# <!-- gald3r $SectionTag START -->"
    $endMarker   = "# <!-- gald3r $SectionTag END -->"

    if ($existing -match [regex]::Escape($startMarker)) {
        # Replace existing section
        $pattern = [regex]::Escape($startMarker) + "[\s\S]*?" + [regex]::Escape($endMarker)
        $replacement = "$startMarker`n$newContent`n$endMarker"
        $updated = $existing -replace $pattern, $replacement
        Set-Content $TargetFile $updated -NoNewline
    } else {
        # Append section
        $append = "`n$startMarker`n$newContent`n$endMarker`n"
        Add-Content $TargetFile $append
    }
}

function Merge-Json {
    param([string]$TargetFile, [string]$SourceFile)
    if (-not (Test-Path $SourceFile)) { return }
    $srcJson = Get-Content $SourceFile -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    if (-not $srcJson) { return }

    if (-not (Test-Path $TargetFile)) {
        Copy-Item $SourceFile $TargetFile -Force
        return
    }

    try {
        $tgtJson = Get-Content $TargetFile -Raw | ConvertFrom-Json
        # Merge: add gald3r keys that don't exist in target
        $srcJson.PSObject.Properties | ForEach-Object {
            if (-not ($tgtJson.PSObject.Properties.Name -contains $_.Name)) {
                $tgtJson | Add-Member -NotePropertyName $_.Name -NotePropertyValue $_.Value
            }
        }
        $tgtJson | ConvertTo-Json -Depth 10 | Set-Content $TargetFile
    } catch {
        Write-Warning "Could not merge $TargetFile — keeping existing."
    }
}

function Deploy-PlatformDirs {
    param([string]$TargetPath, [string[]]$PlatformKeys, [string]$SysRoot)
    foreach ($platKey in $PlatformKeys) {
        if (-not $allPlatforms.ContainsKey($platKey)) {
            Write-Warning "Unknown platform: $platKey"
            continue
        }
        $plat = $allPlatforms[$platKey]
        $platDst = Join-Path $TargetPath $plat.prefix
        New-Item -ItemType Directory -Force $platDst | Out-Null

        # Phase 1: scaffold
        $scaffoldSrc = Join-Path $SysRoot "platforms\$($plat.prefix)"
        if (Test-Path $scaffoldSrc) {
            Get-ChildItem $scaffoldSrc -Recurse -File | ForEach-Object {
                $rel = $_.FullName.Substring($scaffoldSrc.Length + 1)
                $tgt = Join-Path $platDst $rel
                $tgtDir = Split-Path $tgt
                New-Item -ItemType Directory -Force $tgtDir | Out-Null
                if (-not (Test-Path $tgt)) { Copy-Item $_.FullName $tgt -Force }
            }
        }

        # Phase 2: universal content
        foreach ($cat in $plat.cats) {
            $catSrc = Join-Path $SysRoot $cat
            $catDst = Join-Path $platDst $cat
            if (Test-Path $catSrc) {
                New-Item -ItemType Directory -Force $catDst | Out-Null
                Get-ChildItem $catSrc -Recurse -File | ForEach-Object {
                    $rel = $_.FullName.Substring($catSrc.Length + 1)
                    $tgt = Join-Path $catDst $rel
                    $tgtDir = Split-Path $tgt
                    New-Item -ItemType Directory -Force $tgtDir | Out-Null
                    if ($rel -match "^g-" -or $rel -match "[/\\]g-" -or -not (Test-Path $tgt)) {
                        Copy-Item $_.FullName $tgt -Force
                    }
                }
            }
        }

        # Rules
        $rulesSrc = Join-Path $SysRoot "rules"
        if (Test-Path $rulesSrc) {
            $rulesDst = Join-Path $platDst "rules"
            New-Item -ItemType Directory -Force $rulesDst | Out-Null
            Get-ChildItem $rulesSrc -File | ForEach-Object {
                $ext = if ($platKey -eq "cursor") { ".mdc" } else { ".md" }
                $destName = [System.IO.Path]::ChangeExtension($_.Name, $ext)
                $tgt = Join-Path $rulesDst $destName
                if ($_.Name -match "^g-" -or -not (Test-Path $tgt)) {
                    Copy-Item $_.FullName $tgt -Force
                }
            }
        }
        Write-Host "  [OK] $($plat.label) ($($plat.prefix))" -ForegroundColor Green
    }
}

# ── Main installer flow ───────────────────────────────────────────────────────
Write-Banner

# Step 1: Get target path
if (-not $TargetPath) {
    Write-Host "  Where is your project?" -ForegroundColor Yellow
    Write-Host "  (Press Enter to use current directory: $(Get-Location))"
    $input = Read-Host "  Target path"
    $TargetPath = if ($input -eq "") { (Get-Location).Path } else { $input }
}

$TargetPath = $TargetPath.TrimEnd("\", "/")
if (-not (Test-Path $TargetPath)) {
    if (-not $DryRun) {
        $create = Read-Host "  '$TargetPath' does not exist. Create it? [Y/n]"
        if ($create -ne "n" -and $create -ne "N") {
            New-Item -ItemType Directory -Force $TargetPath | Out-Null
            Write-Host "  Created: $TargetPath" -ForegroundColor Green
        } else { exit 0 }
    }
}

Write-Host ""
Write-Host "  Target: $TargetPath" -ForegroundColor Cyan

# Step 2: Detect project state
$galdVersion = Detect-GaldVersion -ProjectPath $TargetPath
$isNew = $galdVersion -eq "none"

Write-Host "  Project state: " -NoNewline
switch -Wildcard ($galdVersion) {
    "none"         { Write-Host "New project (no gald3r found)" -ForegroundColor Green }
    "v1-*"         { Write-Host "LEGACY gald3r v1 (symlink pattern) — will migrate" -ForegroundColor Yellow }
    "v2-phase"     { Write-Host "gald3r v2 (phase-based tasks) — will migrate" -ForegroundColor Yellow }
    "v2-*"         { Write-Host "gald3r v2 — will update" -ForegroundColor Yellow }
    "v3-*"         { Write-Host "gald3r $galdVersion — updating" -ForegroundColor Cyan }
    default        { Write-Host "Unknown / partial install" -ForegroundColor Yellow }
}

if (-not $isNew -and -not $Force -and -not $DryRun) {
    Write-Host ""
    Write-Host "  Existing gald3r detected. This will:" -ForegroundColor Yellow
    Write-Host "    - Update .gald3r_sys/ (framework files — safe overwrite)"
    Write-Host "    - Merge CLAUDE.md, AGENTS.md, .gitignore etc. (section markers)"
    Write-Host "    - Update g- prefixed skills/agents/commands only"
    Write-Host "    - NEVER touch README.md, LICENSE, CHANGELOG.md"
    Write-Host "    - NEVER overwrite your non-gald3r skills/agents/commands"
    Write-Host ""
    $confirm = Read-Host "  Continue? [Y/n]"
    if ($confirm -eq "n" -or $confirm -eq "N") { exit 0 }
}

# Step 3: Platform picker
if ($Platforms.Count -eq 0) {
    Write-Host ""
    Write-Host "  Which platforms will you use?" -ForegroundColor Yellow
    Write-Host "  Available platforms:"
    $idx = 1
    $platformList = @()
    foreach ($key in $allPlatforms.Keys) {
        $label = $allPlatforms[$key].label
        Write-Host "    $idx) $key  — $label"
        $platformList += $key
        $idx++
    }
    Write-Host ""
    Write-Host "  Enter numbers (e.g. 1,2) or names (e.g. cursor,claude) or 'all':"
    $selection = Read-Host "  Platforms"

    if ($selection.ToLower() -eq "all") {
        $Platforms = $platformList
    } else {
        $Platforms = @()
        foreach ($part in ($selection -split "[,\s]+" | Where-Object { $_ })) {
            if ($part -match "^\d+$") {
                $i = [int]$part - 1
                if ($i -ge 0 -and $i -lt $platformList.Count) { $Platforms += $platformList[$i] }
            } elseif ($allPlatforms.ContainsKey($part.ToLower())) {
                $Platforms += $part.ToLower()
            } else {
                Write-Warning "Unknown platform: $part"
            }
        }
    }
}

if ($Platforms.Count -eq 0) {
    Write-Host "  No platforms selected — defaulting to cursor + claude." -ForegroundColor Yellow
    $Platforms = @("cursor", "claude")
}

Write-Host ""
Write-Host "  Installing platforms: $($Platforms -join ', ')" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host ""
    Write-Host "  DRY RUN — no files will be written." -ForegroundColor Yellow
    Write-Host "  Would install to: $TargetPath"
    Write-Host "  Platforms: $($Platforms -join ', ')"
    exit 0
}

# Step 4: Install
Write-Host ""
Write-Host "  [1/5] Deploying .gald3r_sys/ framework files..." -ForegroundColor Cyan
$sysSrc = Join-Path $templatePayload ".gald3r_sys"
$sysDst = Join-Path $TargetPath ".gald3r_sys"
New-Item -ItemType Directory -Force $sysDst | Out-Null
Copy-Item -Path "$sysSrc\*" -Destination $sysDst -Recurse -Force
$sysCount = (Get-ChildItem $sysDst -Recurse -File).Count
Write-Host "  [OK] .gald3r_sys/: $sysCount files" -ForegroundColor Green

Write-Host "  [2/5] Setting up .gald3r/ project state..." -ForegroundColor Cyan
if ($isNew) {
    $galdSrc = Join-Path $templatePayload ".gald3r"
    $galdDst = Join-Path $TargetPath ".gald3r"
    if (Test-Path $galdSrc) {
        Copy-Item -Path $galdSrc -Destination $TargetPath -Recurse -Force
        Write-Host "  [OK] .gald3r/ initialized from template" -ForegroundColor Green
    }
} else {
    Write-Host "  [SKIP] .gald3r/ already exists — preserving your project state" -ForegroundColor DarkGray
}

Write-Host "  [3/5] Merging project root files..." -ForegroundColor Cyan
# Platform-conditional files live in platforms/ subfolder; universal files at payload root
$platformsPayload = Join-Path $templatePayload "platforms"

# Universal files (always installed) — sourced from templatePayload root
$mergeFiles = @{
    ".gitignore"         = "section"
    ".claudeignore"      = "section"
    ".cursorignore"      = "section"
    "GUARDRAILS.md"      = "add-if-missing"
    "GALD3R-MIGRATION.md"= "add-if-missing"
    "GALD3R-PROMPT.md"   = "add-if-missing"
    "scripts"            = "dir-merge"
    "temp_docs"          = "add-if-missing-dir"
    "temp_scripts"       = "add-if-missing-dir"
}

# Platform-conditional files — sourced from platforms/ subfolder
# CLAUDE.md  : Claude Code (primary author), Cursor, Kiro, Windsurf, Roo, Cline, Augment
# AGENTS.md  : Claude, Codex, Gemini, Copilot, OpenCode, Cursor, OpenHands (effectively universal)
# GEMINI.md  : Gemini CLI only (.agent/ folder)
# opencode.json: OpenCode only (.opencode/ folder)
# .github/   : GitHub Copilot only (copilot-instructions.md, workflows, prompts)
$platformFiles = @{
    "CLAUDE.md"          = "section"
    "AGENTS.md"          = "section"
    "GEMINI.md"          = "section"
    "opencode.json"      = "json"
    ".github"            = "copilot-dir"
}

foreach ($file in $mergeFiles.Keys) {
    $strategy = $mergeFiles[$file]
    $srcFile = Join-Path $templatePayload $file
    $dstFile = Join-Path $TargetPath $file

    # Universal files only in this loop — platform-conditional are in $platformFiles loop below
    # Minor gate: skip ignore files if their platform isn't selected
    $shouldInstall = switch ($file) {
        ".claudeignore" { $Platforms -contains "claude" }
        ".cursorignore" { $Platforms -contains "cursor" }
        default         { $true }
    }
    if (-not $shouldInstall) {
        Write-Host "    skip: $file (platform not selected)" -ForegroundColor DarkGray
        continue
    }

    switch ($strategy) {
        "section" {
            Merge-SectionMarker -TargetFile $dstFile -SourceFile $srcFile -SectionTag $file
            Write-Host "    merged: $file" -ForegroundColor DarkGray
        }
        "json" {
            Merge-Json -TargetFile $dstFile -SourceFile $srcFile
            Write-Host "    merged: $file" -ForegroundColor DarkGray
        }
        "add-if-missing" {
            if (-not (Test-Path $dstFile) -and (Test-Path $srcFile)) {
                Copy-Item $srcFile $dstFile -Force
                Write-Host "    added: $file" -ForegroundColor DarkGray
            }
        }
        "add-if-missing-dir" {
            if (-not (Test-Path $dstFile) -and (Test-Path $srcFile)) {
                Copy-Item $srcFile $dstFile -Recurse -Force
                Write-Host "    added: $file/" -ForegroundColor DarkGray
            }
        }
        "dir-merge" {
            if (Test-Path $srcFile) {
                New-Item -ItemType Directory -Force $dstFile | Out-Null
                Get-ChildItem $srcFile -File | ForEach-Object {
                    $tgt = Join-Path $dstFile $_.Name
                    if ($_.Name -match "^g-" -or -not (Test-Path $tgt)) {
                        Copy-Item $_.FullName $tgt -Force
                    }
                }
                Write-Host "    merged: $file/" -ForegroundColor DarkGray
            }
        }
        "copilot-dir" {
            # Full recursive copy of .github/ — only reached when copilot is a selected platform
            if (Test-Path $srcFile) {
                New-Item -ItemType Directory -Force $dstFile | Out-Null
                Copy-Item -Path "$srcFile\*" -Destination $dstFile -Recurse -Force
                Write-Host "    added: .github/ (GitHub Copilot)" -ForegroundColor DarkGray
            }
        }
    }
}

# ── Platform-conditional files (sourced from platforms/ subfolder) ────────────
foreach ($file in $platformFiles.Keys) {
    $strategy = $platformFiles[$file]
    $srcFile = Join-Path $platformsPayload $file
    $dstFile = Join-Path $TargetPath $file

    # Platform gate — skip if platform not selected
    $shouldInstall = switch ($file) {
        "GEMINI.md" {
            $Platforms -contains "agent"
        }
        "opencode.json" {
            $Platforms -contains "opencode"
        }
        "CLAUDE.md" {
            $claudeReaders = @("claude","cursor","kiro","windsurf","roo","cline","augment")
            ($Platforms | Where-Object { $claudeReaders -contains $_ }).Count -gt 0
        }
        "AGENTS.md" {
            # Universal — any platform install gets AGENTS.md
            $Platforms.Count -gt 0
        }
        ".github" {
            $Platforms -contains "copilot"
        }
        default { $true }
    }

    if (-not $shouldInstall) {
        Write-Host "    skip: $file (platform not selected)" -ForegroundColor DarkGray
        continue
    }

    switch ($strategy) {
        "section" {
            Merge-SectionMarker -TargetFile $dstFile -SourceFile $srcFile -SectionTag $file
            Write-Host "    merged: $file" -ForegroundColor DarkGray
        }
        "json" {
            Merge-Json -TargetFile $dstFile -SourceFile $srcFile
            Write-Host "    merged: $file" -ForegroundColor DarkGray
        }
        "copilot-dir" {
            if (Test-Path $srcFile) {
                New-Item -ItemType Directory -Force $dstFile | Out-Null
                Copy-Item -Path "$srcFile\*" -Destination $dstFile -Recurse -Force
                Write-Host "    added: .github/ (GitHub Copilot)" -ForegroundColor DarkGray
            }
        }
    }
}
Write-Host "  [OK] Root files merged" -ForegroundColor Green

Write-Host "  [4/5] Deploying platform dirs..." -ForegroundColor Cyan
Deploy-PlatformDirs -TargetPath $TargetPath -PlatformKeys $Platforms -SysRoot $sysDst

Write-Host "  [5/5] Deploying session script to target project..." -ForegroundColor Cyan
$selfScript = Join-Path $templatePayload "setup_gald3r_project.ps1"
if (-not (Test-Path $selfScript)) { $selfScript = $MyInvocation.MyCommand.Path }
Copy-Item $selfScript (Join-Path $TargetPath "setup_gald3r_project.ps1") -Force
Write-Host "  [OK] setup_gald3r_project.ps1 deployed" -ForegroundColor Green

# ── Done ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║            gald3r setup complete!            ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open your project in your preferred IDE:"
foreach ($p in $Platforms) {
    if ($allPlatforms.ContainsKey($p)) {
        Write-Host "       $($allPlatforms[$p].label)"
    }
}
Write-Host "  2. START A NEW SESSION so gald3r rules + skills load into context"
Write-Host "  3. Type '@g-setup' (Cursor) or '/g-setup' (Claude) to initialize"
Write-Host "     your .gald3r/ project state (TASKS.md, PROJECT.md, etc.)"
Write-Host ""
Write-Host "  Session-start hooks will auto-regenerate platform dirs on each launch."
Write-Host "  To manually regenerate: .\setup_gald3r_project.ps1 -Platform auto"
Write-Host ""
