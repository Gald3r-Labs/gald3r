# generate_copilot_instructions.ps1
# Generates .github/copilot-instructions.md from gald3r always-apply rules.
# Idempotent — safe to rerun; output is deterministic given the same input files.
#
# Usage:
#   .\scripts\generate_copilot_instructions.ps1
#   .\scripts\generate_copilot_instructions.ps1 -Verbose

[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [switch]$DryRun
)

# Locate project root (walk up from script location looking for AGENTS.md)
if (-not $ProjectRoot) {
    $dir = $PSScriptRoot
    while ($dir -and -not (Test-Path (Join-Path $dir "AGENTS.md"))) {
        $dir = Split-Path $dir -Parent
    }
    $ProjectRoot = if ($dir) { $dir } else { $PSScriptRoot }
}

Write-Verbose "Project root: $ProjectRoot"
$EcosystemRoot = Split-Path $ProjectRoot -Parent
$TemplateFullRoot = Join-Path $EcosystemRoot "gald3r_template_full"

# Source: all g-rl-*.mdc files in .cursor/rules/, sorted numerically
$rulesDir = Join-Path $ProjectRoot ".cursor\rules"
$ruleFiles = Get-ChildItem -Path $rulesDir -Filter "g-rl-*.mdc" -ErrorAction SilentlyContinue |
    Sort-Object Name

if ($ruleFiles.Count -eq 0) {
    Write-Warning "No g-rl-*.mdc files found in $rulesDir"
    exit 1
}

Write-Verbose "Found $($ruleFiles.Count) rule files"

# Header banner
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm UTC"
$banner = @"
<!--
  .github/copilot-instructions.md — AUTO-GENERATED, DO NOT EDIT MANUALLY
  
  Generated from: .cursor/rules/g-rl-*.mdc
  Generator:      .gald3r_sys/skills/g-skl-platform-copilot/scripts/generate_copilot_instructions.ps1
  Generated at:   $timestamp

  This file carries gald3r always-apply rules into GitHub Copilot sessions.
  Regenerate after modifying rules: .\scripts\generate_copilot_instructions.ps1

  gald3r — AI Development System for Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot
  Supported IDEs: Cursor (.cursor/), Claude Code (.claude/), Gemini (.agent/),
                  Codex (.codex/), OpenCode (.opencode/), GitHub Copilot (.copilot/)
-->

# gald3r System Instructions for GitHub Copilot

The following rules apply to every Copilot session in this repository.
They are automatically concatenated from gald3r's always-apply rule files.

---

"@

# Build content blocks — strip Cursor-specific frontmatter from each file
$blocks = @()
foreach ($file in $ruleFiles) {
    Write-Verbose "Processing: $($file.Name)"
    $raw = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Strip YAML frontmatter block (--- ... ---)
    $content = $raw
    if ($content -match "(?s)^---\r?\n.*?\r?\n---\r?\n") {
        $content = $content -replace "(?s)^---\r?\n.*?\r?\n---\r?\n", ""
    }
    
    # Remove alwaysApply: lines (Cursor-specific config)
    $content = $content -replace "(?m)^alwaysApply:.*$\r?\n", ""
    
    # Remove empty leading/trailing lines from each block
    $content = $content.Trim()
    
    if ($content.Length -gt 0) {
        $blocks += "<!-- Rule: $($file.Name) -->`n$content`n"
    }
}

# Assemble output
$output = $banner + ($blocks -join "`n---`n`n") + "`n"

# Destination paths
$destinations = @(
    (Join-Path $ProjectRoot ".github\copilot-instructions.md"),
    (Join-Path $TemplateFullRoot ".github\copilot-instructions.md")
)

foreach ($dest in $destinations) {
    $destDir = Split-Path $dest -Parent
    if (-not (Test-Path $destDir)) {
        if ($DryRun) {
            Write-Host "[DRY-RUN] Would create: $destDir"
        } else {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
    }
    
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would write $($output.Length) chars to: $dest"
    } else {
        [System.IO.File]::WriteAllText($dest, $output, [System.Text.UTF8Encoding]::new($false))
        Write-Host "Written: $dest ($($output.Length) chars)"
    }
}

if (-not $DryRun) {
    Write-Host ""
    Write-Host "copilot-instructions.md generated successfully."
    Write-Host "Rule files processed: $($ruleFiles.Count)"
    Write-Host "Rule files: $($ruleFiles.Name -join ', ')"
}

# -----------------------------------------------------------------------
# Step 2: Generate .github/agents/ from .claude/agents/g-agnt-*.md
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "--- Generating .github/agents/ ---" -ForegroundColor Cyan

$agentSrc = Join-Path $ProjectRoot ".claude\agents"
$agentTargets = @(
    (Join-Path $ProjectRoot ".github\agents"),
    (Join-Path $TemplateFullRoot ".github\agents")
)

foreach ($agentDst in $agentTargets) {
    if (-not (Test-Path $agentDst)) {
        if ($DryRun) { Write-Host "[DRY-RUN] Would create: $agentDst" }
        else { New-Item -ItemType Directory -Force $agentDst | Out-Null }
    }
    $agentFiles = Get-ChildItem $agentSrc -Filter "g-agnt-*.md" -File -ErrorAction SilentlyContinue
    foreach ($f in $agentFiles) {
        if ($DryRun) { Write-Host "[DRY-RUN] Would copy $($f.Name) -> $agentDst" }
        else { Copy-Item $f.FullName "$agentDst\$($f.Name)" -Force }
    }
    if (-not $DryRun) { Write-Host "Agents: $($agentFiles.Count) files -> $agentDst" }
}

# -----------------------------------------------------------------------
# Step 3: Generate .github/hooks/gald3r-hooks.json
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "--- Generating .github/hooks/ ---" -ForegroundColor Cyan

$hooksContent = @'
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-session-start.sh",
        "powershell": ".claude/hooks/g-hk-session-start.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ],
    "agentStop": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-agent-complete.sh",
        "powershell": ".claude/hooks/g-hk-agent-complete.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ],
    "preToolUse": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-validate-shell.sh",
        "powershell": ".claude/hooks/g-hk-validate-shell.ps1",
        "cwd": ".",
        "timeoutSec": 15
      }
    ],
    "sessionEnd": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-agent-complete.sh",
        "powershell": ".claude/hooks/g-hk-agent-complete.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ]
  }
}
'@

$hooksTargets = @(
    (Join-Path $ProjectRoot ".github\hooks\gald3r-hooks.json"),
    (Join-Path $TemplateFullRoot ".github\hooks\gald3r-hooks.json")
)

foreach ($hDst in $hooksTargets) {
    $hDir = Split-Path $hDst -Parent
    if (-not (Test-Path $hDir)) {
        if ($DryRun) { Write-Host "[DRY-RUN] Would create: $hDir" }
        else { New-Item -ItemType Directory -Force $hDir | Out-Null }
    }
    if ($DryRun) { Write-Host "[DRY-RUN] Would write gald3r-hooks.json -> $hDst" }
    else {
        [System.IO.File]::WriteAllText($hDst, $hooksContent, [System.Text.UTF8Encoding]::new($false))
        Write-Host "Hooks written: $hDst"
    }
}

# -----------------------------------------------------------------------
# Step 4: Generate .github/prompts/ from .cursor/commands/ (rename *.md -> *.prompt.md)
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "--- Generating .github/prompts/ ---" -ForegroundColor Cyan

$promptTargetPairs = @(
    @{ Src = (Join-Path $ProjectRoot ".cursor\commands"); Dst = (Join-Path $ProjectRoot ".github\prompts") },
    @{ Src = (Join-Path $TemplateFullRoot ".cursor\commands"); Dst = (Join-Path $TemplateFullRoot ".github\prompts") }
)

foreach ($pair in $promptTargetPairs) {
    if (-not (Test-Path $pair.Dst)) {
        if ($DryRun) { Write-Host "[DRY-RUN] Would create: $($pair.Dst)" }
        else { New-Item -ItemType Directory -Force $pair.Dst | Out-Null }
    }
    $cmdFiles = Get-ChildItem $pair.Src -Filter "*.md" -File -ErrorAction SilentlyContinue
    foreach ($f in $cmdFiles) {
        $promptName = "$($f.BaseName).prompt.md"
        if ($DryRun) { Write-Host "[DRY-RUN] Would copy $($f.Name) -> $promptName" }
        else { Copy-Item $f.FullName "$($pair.Dst)\$promptName" -Force }
    }
    if (-not $DryRun) { Write-Host "Prompts: $($cmdFiles.Count) files -> $($pair.Dst)" }
}

Write-Host ""
Write-Host "All Copilot .github/ targets generated." -ForegroundColor Green
Write-Host "  copilot-instructions.md : rules source"
Write-Host "  .github/agents/         : agent definitions (from .claude/agents/)"
Write-Host "  .github/hooks/          : lifecycle hooks (gald3r-hooks.json)"
Write-Host "  .github/prompts/        : prompt templates (from .cursor/commands/)"
Write-Host "  Skills                  : auto-discovered from .claude/skills/ (no copy needed)"

