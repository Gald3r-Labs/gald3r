<#
.SYNOPSIS
    check_platform_status.ps1 - Read and report the gald3r cross-platform capability index.
    Entry point for @g-platform-check; CHECK delegate for g-skl-platform-monitor.

.DESCRIPTION
    Reads .gald3r/PLATFORM_STATUS.md and reports the current capability state for one platform
    (-Platform <name>) or all 23 (default). This is the T1460 SKELETON: it parses and reports the
    status table today; deep per-platform gap analysis and doc-diff are placeholder calls to the
    future g-skl-platform-monitor operations (CHECK / SCAN_DOCS), completed by T1461-T1483.

.PARAMETER Platform
    The platform name (e.g. cursor, claude, windsurf). Default "all" reports every platform.

.PARAMETER GenerateMatrix
    T1543: Instead of the status report, read all 23 canonical PLATFORM_SPEC.md files
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

# Resolve the project root (parent of custom_scripts/) and the status file.
$repoRoot   = (Get-Item $PSScriptRoot).Parent.FullName
$statusPath = Join-Path $repoRoot ".gald3r\PLATFORM_STATUS.md"

# The 23 supported platforms (matches PLATFORM_STATUS.md rows and T1461-T1483).
$KNOWN_PLATFORMS = @(
    "cursor","claude","copilot","codex","antigravity","windsurf","gemini","cline","roo",
    "opencode","openhands","kiro","aider","augment","goose","junie","kiro-cli","mistral",
    "openclaw","qwen","replit","subq","warp"
)

# Platform name -> canonical PLATFORM_SPEC.md folder (leading-dot). Most are ".<name>";
# the only exception is replit -> ".replit-gald3r".
function Get-SpecFolderName {
    param([string]$PlatformName)
    if ($PlatformName -eq "replit") { return ".replit-gald3r" }
    return ".$PlatformName"
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

    if (-not (Test-Path $specsRoot)) {
        Write-Host "  ERROR: canonical platforms spec root not found at $specsRoot" -ForegroundColor Red
        exit 1
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
        $folder   = Get-SpecFolderName $p
        $specPath = Join-Path $specsRoot (Join-Path $folder 'PLATFORM_SPEC.md')

        if (-not (Test-Path $specPath)) {
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
    [void]$sb.AppendLine('23 platforms × 6 capability columns. Cells sourced from each platform''s canonical `PLATFORM_SPEC.md`')
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

# Placeholder delegation to future g-skl-platform-monitor operations (T1461-T1483).
# TODO[TASK-1460->T1461-T1483]: wire CHECK gap-analysis + SCAN_DOCS diff here once the per-platform
# monitor operations are implemented. Scaffolding by design per T1460 spec.
Write-Host "  (deep gap analysis / doc-scan: g-skl-platform-monitor CHECK|SCAN_DOCS -- T1461-T1483)" -ForegroundColor DarkGray

exit 0
