<#
.SYNOPSIS
    check_platform_status.ps1 - Read and report the gald3r cross-platform capability index.
    Entry point for @g-platform-check; CHECK delegate for g-skl-platform-monitor.

.DESCRIPTION
    Reads .gald3r/PLATFORM_STATUS.md and reports the current capability state for one platform
    (-Platform <name>) or every registry platform (default; roster from PLATFORM_REGISTRY.yaml,
    T516). This is the T1460 SKELETON: it parses and reports the
    status table today; deep per-platform gap analysis and doc-diff are placeholder calls to the
    future g-skl-platform-monitor operations (CHECK / SCAN_DOCS), completed by T1461-T1483.

.PARAMETER Platform
    The platform name (e.g. cursor, claude, windsurf). Default "all" reports every platform.

.PARAMETER GenerateMatrix
    T1543: Instead of the status report, read each registry platform's canonical PLATFORM_SPEC.md file
    (.gald3r_sys/platforms/.<platform>/PLATFORM_SPEC.md), derive each capability cell
    (Hooks / Rules / Skills / Commands / MCP / Docs Fresh), and (re)write
    .gald3r/PLATFORM_CAPABILITY_MATRIX.md with the populated cells. Reads PLATFORM_STATUS.md
    read-only to cross-check (warns on disagreement; NEVER overwrites PLATFORM_STATUS.md).

.PARAMETER CrawlMaxAgeDays
    T1543: Docs-freshness threshold (days) used to compute the "Docs Fresh" column when a spec's
    frontmatter does not supply its own crawl_max_age_days. Default 7.

.EXAMPLE
    .\custom_scripts\check_platform_status.ps1
    .\custom_scripts\check_platform_status.ps1 -Platform windsurf
    .\custom_scripts\check_platform_status.ps1 -GenerateMatrix

.NOTES
    Task: T1460 (Platform Maintenance Infrastructure); T1543 (-GenerateMatrix wiring)
#>
# @subsystems: PLATFORM_INTEGRATION

param(
    [string]$Platform = "all",
    [switch]$GenerateMatrix,
    [int]$CrawlMaxAgeDays = 7
)

$ErrorActionPreference = "Stop"

# Resolve the project root via an anchored walk-up (BUG-161 fix). The script moved from the
# legacy custom_scripts/ (one level under the repo root) into the skill tree, so the old
# (Get-Item $PSScriptRoot).Parent resolved to the skill folder and every probe missed.
function Get-ProjectRoot {
    param([string]$Start)
    # Prefer the ancestor that actually holds .gald3r/PLATFORM_STATUS.md (the file this reads).
    $dir = Get-Item $Start
    while ($null -ne $dir) {
        if (Test-Path (Join-Path $dir.FullName ".gald3r\PLATFORM_STATUS.md")) { return $dir.FullName }
        $dir = $dir.Parent
    }
    # Then any .gald3r project marker.
    $dir = Get-Item $Start
    while ($null -ne $dir) {
        if (Test-Path (Join-Path $dir.FullName ".gald3r")) { return $dir.FullName }
        $dir = $dir.Parent
    }
    # Legacy fallback — identical to the pre-BUG-161 behavior.
    return (Get-Item $Start).Parent.FullName
}
$repoRoot   = Get-ProjectRoot $PSScriptRoot
$statusPath = Join-Path $repoRoot ".gald3r\PLATFORM_STATUS.md"

# The supported platforms — derived from the single source of truth,
# PLATFORM_REGISTRY.yaml (T516), via the shared platform_registry.py reader. No hardcoded
# roster lives here anymore; the .ps1 shells out to the Python reader so YAML parsing is
# not duplicated. If Python or the registry is unavailable, fall back to the original
# 23-platform list so this script still runs (AC2 safe fallback).
function Get-KnownPlatforms {
    $fallback = @(
        "cursor","claude","copilot","codex","antigravity","windsurf","gemini","cline","roo",
        "opencode","openhands","kiro","aider","augment","goose","junie","kiro-cli","mistral",
        "openclaw","qwen","replit","subq","warp"
    )
    $readerPath = Join-Path $PSScriptRoot "platform_registry.py"
    if (-not (Test-Path $readerPath)) { return $fallback }
    try {
        $out = & python $readerPath --list 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) {
            $names = @($out | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
            if ($names.Count -gt 0) { return $names }
        }
    } catch {
        # Python not on PATH or reader failed — fall through to the baked-in fallback.
    }
    return $fallback
}

$KNOWN_PLATFORMS = Get-KnownPlatforms

# Platform name -> legacy override-tree PLATFORM_SPEC.md folder (leading-dot). Most are
# ".<name>"; the only exception is replit -> ".replit-gald3r".
function Get-SpecFolderName {
    param([string]$PlatformName)
    if ($PlatformName -eq "replit") { return ".replit-gald3r" }
    return ".$PlatformName"
}

# Walk up from a start dir to find the repo root that contains PLATFORM_REGISTRY.yaml
# (or a .gald3r/). Used so the registry-driven spec resolution can reach the skill trees,
# since $repoRoot above is the skill folder (pre-existing path quirk).
function Get-RegistryRepoRoot {
    param([string]$Start)
    $dir = Get-Item $Start
    while ($dir -ne $null) {
        foreach ($rel in @(
            "gald3r_templates\gald3r_core\platforms\PLATFORM_REGISTRY.yaml",
            "gald3r_core\platforms\PLATFORM_REGISTRY.yaml",
            ".gald3r_sys\platforms\PLATFORM_REGISTRY.yaml",
            "platforms\PLATFORM_REGISTRY.yaml")) {
            if (Test-Path (Join-Path $dir.FullName $rel)) { return $dir.FullName }
        }
        $dir = $dir.Parent
    }
    return $null
}

# Resolve a platform's PLATFORM_SPEC.md (T516). Prefer the legacy override tree
# (.gald3r_sys/platforms/.<x>/) when present; else resolve from the registry skill trees
# (absorbed layout). Returns the path or $null.
function Resolve-SpecPath {
    param([string]$Platform, [string]$SpecsRoot, [string]$RegistryRoot)
    $legacy = Join-Path $SpecsRoot (Join-Path (Get-SpecFolderName $Platform) 'PLATFORM_SPEC.md')
    if (Test-Path $legacy) { return $legacy }
    if (-not $RegistryRoot) { return $null }
    # Candidate skill-folder suffixes: the name, plus the -code-stripped short name.
    $suffixes = @($Platform)
    if ($Platform.EndsWith('-code')) { $suffixes += $Platform.Substring(0, $Platform.Length - 5) }
    $trees = @(
        "gald3r_templates\gald3r_core\project_template\.claude\skills",
        "gald3r_templates\gald3r_core\project_template\.cursor\skills",
        ".claude\skills", ".cursor\skills")
    foreach ($s in $suffixes) {
        foreach ($t in $trees) {
            $cand = Join-Path $RegistryRoot (Join-Path $t (Join-Path "g-skl-platform-$s" 'PLATFORM_SPEC.md'))
            if (Test-Path $cand) { return $cand }
        }
    }
    return $null
}

# ============================================================================
# T1543: -GenerateMatrix — read canonical PLATFORM_SPEC.md files, compute the 6
# capability cells per platform, and (re)write .gald3r/PLATFORM_CAPABILITY_MATRIX.md.
# Self-contained early-exit; the default status-report path below is untouched.
# ============================================================================
if ($GenerateMatrix) {
    $specsRoot  = Join-Path $repoRoot ".gald3r_sys\platforms"
    $matrixPath = Join-Path $repoRoot ".gald3r\PLATFORM_CAPABILITY_MATRIX.md"

    Write-Host "`n=== check_platform_status -GenerateMatrix (T1543) ===" -ForegroundColor Cyan
    Write-Host "  specs : $specsRoot"  -ForegroundColor DarkGray
    Write-Host "  output: $matrixPath" -ForegroundColor DarkGray
    Write-Host ""

    # The row set is registry-driven (KNOWN_PLATFORMS, T516). Spec files resolve per platform
    # via Resolve-SpecPath: legacy override tree first, then the registry skill trees.
    $registryRoot = Get-RegistryRepoRoot $PSScriptRoot
    if (-not (Test-Path $specsRoot)) {
        $anySpec = $false
        foreach ($p in $KNOWN_PLATFORMS) {
            if (Resolve-SpecPath -Platform $p -SpecsRoot $specsRoot -RegistryRoot $registryRoot) { $anySpec = $true; break }
        }
        if (-not $anySpec) {
            Write-Host "  ERROR: no PLATFORM_SPEC.md found via legacy $specsRoot or the registry skill trees." -ForegroundColor Red
            exit 1
        }
        Write-Host "  NOTE: legacy $specsRoot absent — resolving specs from PLATFORM_REGISTRY.yaml against the skill trees." -ForegroundColor DarkYellow
    }

    $validCells = @('✅','⚠️','❌','❓')

    # ---- Cross-check source: PLATFORM_STATUS.md (READ ONLY; never overwritten). ----
    # Parse the hand-set row per platform so we can warn (AC5) when our computed cell disagrees.
    # PS 5.1's Get-Content defaults to the ANSI codepage and mangles UTF-8 emoji; always
    # read these files as UTF-8 explicitly so cell comparisons work on both PS 5.1 and PS 7.
    $utf8 = New-Object System.Text.UTF8Encoding($false)

    $statusByPlatform = @{}
    if (Test-Path $statusPath) {
        $statusLines = [System.IO.File]::ReadAllLines($statusPath, $utf8)
        foreach ($line in $statusLines) {
            if ($line -notmatch '^\s*\|') { continue }
            $cells = ($line -replace '^\s*\|','' -replace '\|\s*$','') -split '\|' | ForEach-Object { $_.Trim() }
            if ($cells.Count -lt 9) { continue }
            if ($cells[0] -eq 'Platform' -or $cells[0] -match '^[-: ]+$') { continue }
            if ($KNOWN_PLATFORMS -notcontains $cells[0]) { continue }
            # Columns: Platform|Status|Last Doc Scan|Hooks|Rules|Skills|Commands|MCP|Notes
            $statusByPlatform[$cells[0]] = [pscustomobject]@{
                LastDocScan = $cells[2]
                Hooks       = $cells[3]
                Rules       = $cells[4]
                Skills      = $cells[5]
                Commands    = $cells[6]
                MCP         = $cells[7]
            }
        }
    } else {
        Write-Host "  WARN: PLATFORM_STATUS.md not found — skipping cross-check (AC5)." -ForegroundColor Yellow
    }

    # ---- Helpers -------------------------------------------------------------
    # Read a single scalar frontmatter field (between the first two '---' fences).
    function Get-FrontmatterField {
        param([string]$Content, [string]$Field)
        $fmMatch = [regex]::Match($Content, '(?s)^\s*---\s*\r?\n(.*?)\r?\n---\s*\r?\n')
        if (-not $fmMatch.Success) { return $null }
        $fm = $fmMatch.Groups[1].Value
        foreach ($l in ($fm -split "`n")) {
            if ($l -match "^\s*$([regex]::Escape($Field))\s*:\s*(.+?)\s*(#.*)?$") {
                $val = $matches[1].Trim()
                $val = $val.Trim([char]34)   # strip surrounding double quotes
                $val = $val.Trim([char]39)   # strip surrounding single quotes
                return $val
            }
        }
        return $null
    }

    # Extract the single data row from the "## Capability Summary" table.
    # Returns an ordered hashtable of the 6 columns, or $null if not parseable.
    function Get-CapabilitySummaryRow {
        param([string]$Content)
        $hMatch = [regex]::Match($Content, '(?m)^##\s+Capability Summary.*$')
        if (-not $hMatch.Success) { return $null }
        $section = $Content.Substring($hMatch.Index)
        $next = [regex]::Match($section.Substring($hMatch.Length), '(?m)^##\s')
        if ($next.Success) { $section = $section.Substring(0, $hMatch.Length + $next.Index) }
        # Find table rows; skip the header row (contains 'Hooks') and the separator row.
        $dataRow = $null
        foreach ($l in ($section -split "`n")) {
            if ($l -notmatch '^\s*\|') { continue }
            $c = ($l -replace '^\s*\|','' -replace '\|\s*$','') -split '\|' | ForEach-Object { $_.Trim() }
            if ($c.Count -lt 6) { continue }
            if ($c[0] -match '^[Hh]ooks$') { continue }      # header
            if ($c[0] -match '^[-: ]+$')   { continue }      # separator
            $dataRow = $c
            break
        }
        if (-not $dataRow) { return $null }
        return [ordered]@{
            Hooks    = $dataRow[0]
            Rules    = $dataRow[1]
            Skills   = $dataRow[2]
            Commands = $dataRow[3]
            MCP      = $dataRow[4]
        }
    }

    # AC2 Hooks cross-read: scan the narrative "## N. Hooks ..." section for an explicit
    # "no hooks" statement. Returns '❌' when the prose clearly says no hook system, else $null.
    function Get-HooksFromNarrative {
        param([string]$Content)
        $hMatch = [regex]::Match($Content, '(?m)^##\s+(?:\d+\.\s+)?Hooks?\s+(?:System|Support).*$')
        if (-not $hMatch.Success) { return $null }
        $section = $Content.Substring($hMatch.Index)
        $next = [regex]::Match($section.Substring($hMatch.Length), '(?m)^##\s')
        if ($next.Success) { $section = $section.Substring(0, $hMatch.Length + $next.Index) }
        if ($section -match '(?i)no\s+(?:native\s+)?hook' -or
            $section -match '(?i)no\s+hook\s*/\s*lifecycle' -or
            $section -match '(?i)❌\s*none') {
            return '❌'
        }
        return $null
    }

    # Compute the "Docs Fresh" cell from last_doc_scan vs the threshold (AC2).
    function Get-DocsFreshCell {
        param([string]$LastDocScan, [int]$Threshold)
        if ([string]::IsNullOrWhiteSpace($LastDocScan)) { return '❓' }
        $v = $LastDocScan.Trim().ToLower()
        if ($v -eq 'never' -or $v -eq '') { return '❓' }
        $parsed = [datetime]::MinValue
        if (-not [datetime]::TryParseExact($LastDocScan.Trim(), 'yyyy-MM-dd',
                [System.Globalization.CultureInfo]::InvariantCulture,
                [System.Globalization.DateTimeStyles]::None, [ref]$parsed)) {
            return '❓'
        }
        $ageDays = ([datetime]::UtcNow.Date - $parsed.Date).TotalDays
        if ($ageDays -le $Threshold) { return '✅' } else { return '⚠️' }
    }

    # ---- Per-platform extraction --------------------------------------------
    $matrixRows = @()
    $missingSpecFolders = @()
    $tally = @{ '✅' = 0; '⚠️' = 0; '❌' = 0; '❓' = 0 }

    foreach ($p in $KNOWN_PLATFORMS) {
        $specPath = Resolve-SpecPath -Platform $p -SpecsRoot $specsRoot -RegistryRoot $registryRoot

        if (-not $specPath -or -not (Test-Path $specPath)) {
            $missingSpecFolders += $p
            $row = [ordered]@{ Platform = $p; Hooks='❓'; Rules='❓'; Skills='❓'; Commands='❓'; MCP='❓'; DocsFresh='❓' }
            $matrixRows += [pscustomobject]$row
            5 | ForEach-Object { $tally['❓']++ }   # 5 capability cells (DocsFresh counted below)
            $tally['❓']++                          # DocsFresh
            continue
        }

        $content = [System.IO.File]::ReadAllText($specPath, $utf8)

        $summary = Get-CapabilitySummaryRow -Content $content
        if (-not $summary) {
            # No structured capability table -> honest all-❓ for the 5 capability cells.
            $summary = [ordered]@{ Hooks='❓'; Rules='❓'; Skills='❓'; Commands='❓'; MCP='❓' }
        }

        # Hooks: prefer the structured Capability Summary cell; if it is non-committal (❓)
        # and the narrative clearly says "no hooks", honor the explicit ❌ (AC2 intent).
        $hooks = $summary.Hooks
        if (($hooks -eq '❓' -or [string]::IsNullOrWhiteSpace($hooks)) ) {
            $narr = Get-HooksFromNarrative -Content $content
            if ($narr) { $hooks = $narr }
        }

        # Normalize any unexpected token to ❓ (honest default).
        $cellHooks    = if ($validCells -contains $hooks)          { $hooks }          else { '❓' }
        $cellRules    = if ($validCells -contains $summary.Rules)    { $summary.Rules }    else { '❓' }
        $cellSkills   = if ($validCells -contains $summary.Skills)   { $summary.Skills }   else { '❓' }
        $cellCommands = if ($validCells -contains $summary.Commands) { $summary.Commands } else { '❓' }
        $cellMCP      = if ($validCells -contains $summary.MCP)      { $summary.MCP }      else { '❓' }

        # Docs Fresh (AC2): last_doc_scan vs per-spec crawl_max_age_days (fallback to -CrawlMaxAgeDays).
        $lastScanFM = Get-FrontmatterField -Content $content -Field 'last_doc_scan'
        $thrFM      = Get-FrontmatterField -Content $content -Field 'crawl_max_age_days'
        $threshold  = $CrawlMaxAgeDays
        if ($thrFM -and ($thrFM -match '^\d+$')) { $threshold = [int]$thrFM }
        # Prefer the PLATFORM_STATUS.md row's Last Doc Scan when the spec frontmatter is "never"
        # but STATUS records a real date (STATUS is the operationally-maintained scan ledger).
        $lastScan = $lastScanFM
        if (($null -eq $lastScan -or $lastScan.Trim().ToLower() -eq 'never') -and $statusByPlatform.ContainsKey($p)) {
            $statusScan = $statusByPlatform[$p].LastDocScan
            if ($statusScan -and $statusScan.Trim().ToLower() -ne 'never') { $lastScan = $statusScan }
        }
        $cellDocsFresh = Get-DocsFreshCell -LastDocScan $lastScan -Threshold $threshold

        $row = [ordered]@{
            Platform  = $p
            Hooks     = $cellHooks
            Rules     = $cellRules
            Skills    = $cellSkills
            Commands  = $cellCommands
            MCP       = $cellMCP
            DocsFresh = $cellDocsFresh
        }
        $matrixRows += [pscustomobject]$row

        foreach ($cv in @($cellHooks,$cellRules,$cellSkills,$cellCommands,$cellMCP,$cellDocsFresh)) {
            if ($tally.ContainsKey($cv)) { $tally[$cv]++ } else { $tally['❓']++ }
        }

        # ---- AC5 cross-check vs PLATFORM_STATUS.md (warn only; never write STATUS) ----
        if ($statusByPlatform.ContainsKey($p)) {
            $s = $statusByPlatform[$p]
            $pairs = @(
                @{ Cap='Hooks';    Mine=$cellHooks;    Theirs=$s.Hooks },
                @{ Cap='Rules';    Mine=$cellRules;    Theirs=$s.Rules },
                @{ Cap='Skills';   Mine=$cellSkills;   Theirs=$s.Skills },
                @{ Cap='Commands'; Mine=$cellCommands; Theirs=$s.Commands },
                @{ Cap='MCP';      Mine=$cellMCP;      Theirs=$s.MCP }
            )
            $emdash = [char]0x2014
            foreach ($pr in $pairs) {
                if (($validCells -contains $pr.Theirs) -and $pr.Mine -ne $pr.Theirs) {
                    Write-Host ("  Matrix says {0} but STATUS says {1} for {2} {3} {4} verify PLATFORM_SPEC.md or PLATFORM_STATUS.md" -f `
                        $pr.Mine, $pr.Theirs, $p, $pr.Cap, $emdash) -ForegroundColor Yellow
                }
            }
        }
    }

    if ($missingSpecFolders.Count -gt 0) {
        Write-Host ("  NOTE: {0} platform(s) had no canonical PLATFORM_SPEC.md (cells left ❓): {1}" -f `
            $missingSpecFolders.Count, ($missingSpecFolders -join ', ')) -ForegroundColor DarkYellow
    }

    # ---- Write the matrix file, preserving the existing column layout/order. ----
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine('# PLATFORM_CAPABILITY_MATRIX.md — Feature Comparison Across Platforms')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('**Generated by** `check_platform_status.ps1 -GenerateMatrix` (T1543). Owned by `g-agnt-platformer`.')
    [void]$sb.AppendLine(("Registry-driven: {0} platforms × 6 capability columns (row set from ``PLATFORM_REGISTRY.yaml``, T516). Cells sourced from each platform's canonical ``PLATFORM_SPEC.md``" -f $matrixRows.Count))
    [void]$sb.AppendLine('(`## Capability Summary` table + frontmatter `last_doc_scan`). Cross-checked against `PLATFORM_STATUS.md`.')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('| Platform | Hooks | Rules | Skills | Commands | MCP | Docs Fresh |')
    [void]$sb.AppendLine('|---|---|---|---|---|---|---|')
    foreach ($r in $matrixRows) {
        [void]$sb.AppendLine(('| {0} | {1} | {2} | {3} | {4} | {5} | {6} |' -f `
            $r.Platform, $r.Hooks, $r.Rules, $r.Skills, $r.Commands, $r.MCP, $r.DocsFresh))
    }
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('---')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('**Capability columns**')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('| Column | Meaning |')
    [void]$sb.AppendLine('|---|---|')
    [void]$sb.AppendLine('| Hooks | Native lifecycle hook system + gald3r hook wiring |')
    [void]$sb.AppendLine('| Rules | Persistent always-apply rules / memory injection |')
    [void]$sb.AppendLine('| Skills | `g-skl-*/SKILL.md` discovery + invocation |')
    [void]$sb.AppendLine('| Commands | `@g-*` slash commands / workflow equivalents |')
    [void]$sb.AppendLine('| MCP | Model Context Protocol server support |')
    [void]$sb.AppendLine('| Docs Fresh | Last doc scan within `crawl_max_age_days` |')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine(('Cells are derived from each platform''s `## Capability Summary` table in its canonical ' +
        '`PLATFORM_SPEC.md`; `Docs Fresh` is computed from frontmatter `last_doc_scan` vs `crawl_max_age_days` ' +
        '(default {0}). Regenerate with `check_platform_status.ps1 -GenerateMatrix`.' -f $CrawlMaxAgeDays))

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($matrixPath, $sb.ToString(), $utf8NoBom)

    $totalCells = $matrixRows.Count * 6
    Write-Host ""
    Write-Host ("  Updated {0} cells ({1} ✅, {2} ⚠️, {3} ❌, {4} ❓)" -f `
        $totalCells, $tally['✅'], $tally['⚠️'], $tally['❌'], $tally['❓']) -ForegroundColor Green
    exit 0
}

Write-Host "`n=== check_platform_status (T1460 skeleton) ===" -ForegroundColor Cyan

if (-not (Test-Path $statusPath)) {
    Write-Host "  ERROR: PLATFORM_STATUS.md not found at $statusPath" -ForegroundColor Red
    Write-Host "  Run T1460 setup or @g-platform-check to (re)generate it." -ForegroundColor DarkGray
    exit 1
}

# Parse the markdown capability table into row objects.
# Row format: | platform | status | last_doc_scan | hooks | rules | skills | commands | mcp | notes |
$rows = @()
foreach ($line in (Get-Content -LiteralPath $statusPath)) {
    if ($line -notmatch '^\s*\|') { continue }
    $cells = ($line -replace '^\s*\|','' -replace '\|\s*$','') -split '\|' | ForEach-Object { $_.Trim() }
    if ($cells.Count -lt 9) { continue }
    # Skip the header and separator rows.
    if ($cells[0] -eq 'Platform' -or $cells[0] -match '^[-: ]+$') { continue }
    if ($KNOWN_PLATFORMS -notcontains $cells[0]) { continue }
    $rows += [pscustomobject]@{
        Platform     = $cells[0]
        Status       = $cells[1]
        LastDocScan  = $cells[2]
        Hooks        = $cells[3]
        Rules        = $cells[4]
        Skills       = $cells[5]
        Commands     = $cells[6]
        MCP          = $cells[7]
        Notes        = $cells[8]
    }
}

if ($Platform -ne "all") {
    $target = $Platform.ToLower()
    if ($KNOWN_PLATFORMS -notcontains $target) {
        Write-Host "  ERROR: unknown platform '$Platform'. Known: $($KNOWN_PLATFORMS -join ', ')" -ForegroundColor Red
        exit 1
    }
    $rows = $rows | Where-Object { $_.Platform -eq $target }
}

if (-not $rows -or $rows.Count -eq 0) {
    Write-Host "  No matching platform rows found in PLATFORM_STATUS.md." -ForegroundColor Yellow
    exit 1
}

# Report.
$rows | Format-Table Platform, Status, LastDocScan, Hooks, Rules, Skills, Commands, MCP -AutoSize

$healthy   = @($rows | Where-Object { $_.Status -eq '✅' }).Count
$attention = @($rows | Where-Object { $_.Status -eq '⚠️' }).Count
$rework    = @($rows | Where-Object { $_.Status -eq '❌' }).Count
$unknown   = @($rows | Where-Object { $_.Status -eq '❓' }).Count

Write-Host ("  Summary: {0} healthy, {1} need attention, {2} need rework, {3} unknown (of {4})" -f `
    $healthy, $attention, $rework, $unknown, @($rows).Count) -ForegroundColor Green

# SCAN_DOCS -> spec proposals and STATUS regeneration are now implemented (T513 freshness
# loop): spec_refresh.py/.ps1 (T514, crawl docs -> PLATFORM_SPEC.md proposals) and
# generate_status.py/.ps1 (T515, specs + crawl ledger -> PLATFORM_STATUS.md). The T1460
# skeleton's "wire SCAN_DOCS diff + STATUS auto-refresh here" is resolved by those host-side
# consumers; deep per-platform CHECK gap-analysis remains T1461-T1483.
Write-Host "  (spec-refresh: spec_refresh.ps1 [T514] · STATUS regen: generate_status.ps1 [T515] · deep CHECK gap-analysis: g-skl-platform-monitor -- T1461-T1483)" -ForegroundColor DarkGray

exit 0
