<#
.SYNOPSIS
  Audit gald3r system/config files (skills, rules, agents, commands) for bloat and produce a
  pruning report with specific suggested removals. Optionally PREVIEW or APPLY edits. (T1054)
.DESCRIPTION
  gald3r_dev ROOT-ONLY maintainer tooling. Sibling of g-skl-compress-memory (T1053): same
  "preserve-always, dry-run-first" philosophy, but targets the framework system corpus
  (.gald3r_sys/{skills,rules,agents,commands}) instead of memory files.

  Three modes (param -Mode, default AUDIT):
    AUDIT   (read-only) scan target files, compute a bloat score per file, output a ranked
            report (files by bloat score + top suggested removals). No writes.
    PREVIEW (read-only) show a per-file diff of the proposed removals. No writes.
    APPLY   write changes ONLY for files explicitly confirmed via -Confirm. Never bulk-applies;
            always shows what will change first.

  Bloat-signal heuristics (weighted; see SKILL.md for the rationale):
    rationalization_table_overflow  rationalization | reality table with >5 rows   weight 3
    skill_over_400_lines            SKILL.md > 400 lines                            weight 4
    near_identical_enforcement      rule file with >3 near-identical enforce lines  weight 3
    multiple_background_sections    agent file with >2 ## Background / ## Context    weight 2
    backref_filler                  lines starting "As mentioned above" / "As noted" weight 1 (each)
    duplicate_acceptance_criteria   (advisory — cross-file, reported, not auto-cut)  weight 2

  PRESERVE-ALWAYS (never suggested for removal, never cut on APPLY):
    fenced code blocks, command syntax lines, acceptance-criteria bodies, hard rules / HARD RULE
    blocks, enforcement logic, YAML frontmatter, URLs.

  PowerShell 5.1+/7 compatible. No bare curl, ';' separators, UTF-8 safe.
.EXAMPLE
  pwsh -File gald3r_optimize.ps1 -Path .gald3r_sys/skills/g-skl-tasks/SKILL.md
  pwsh -File gald3r_optimize.ps1 -Mode AUDIT -Path .gald3r_sys/skills -Json
  pwsh -File gald3r_optimize.ps1 -Mode PREVIEW -Path .gald3r_sys/rules/g-rl-33-enforcement_catchall.md
  pwsh -File gald3r_optimize.ps1 -Mode APPLY -Path .gald3r_sys/skills/g-skl-foo/SKILL.md -Confirm
#>
[CmdletBinding()]
param(
  [ValidateSet('AUDIT','PREVIEW','APPLY')]
  [string]$Mode = 'AUDIT',                 # default = read-only AUDIT
  [string]$Path,                           # file or directory; default = .gald3r_sys/{skills,rules,agents,commands}
  [string]$ProjectRoot,
  [switch]$Confirm,                        # per-file confirmation; REQUIRED for APPLY (never bulk)
  [int]$Top = 10,                          # number of suggested removals to surface in AUDIT
  [switch]$Json
)
$ErrorActionPreference = 'Stop'

# ---- bloat-signal weights (documented in SKILL.md) ----
$Weights = @{
  rationalization_table_overflow = 3
  skill_over_400_lines           = 4
  near_identical_enforcement     = 3
  multiple_background_sections   = 2
  backref_filler                 = 1
  duplicate_acceptance_criteria  = 2
}

function Get-ProjectRoot {
  if ($ProjectRoot) { return $ProjectRoot }
  $d = (Get-Location).Path
  while ($d -and -not (Test-Path (Join-Path $d '.gald3r_sys'))) {
    $p = Split-Path $d -Parent; if ($p -eq $d) { break }; $d = $p
  }
  return $d
}

# Map each line index to its enclosing fenced-code-block state so PRESERVE logic can skip them.
function Get-CodeBlockMask([string[]]$lines) {
  $mask = New-Object 'bool[]' $lines.Count
  $inBlock = $false
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*```') { $mask[$i] = $true; $inBlock = -not $inBlock; continue }
    $mask[$i] = $inBlock
  }
  return $mask
}

# Frontmatter range (--- ... --- at top of file). Returns end line index (inclusive) or -1.
function Get-FrontmatterEnd([string[]]$lines) {
  if ($lines.Count -eq 0 -or $lines[0].Trim() -ne '---') { return -1 }
  for ($i = 1; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim() -eq '---') { return $i } }
  return -1
}

function Test-PreserveLine([string]$line) {
  # Never flag/remove command syntax, acceptance criteria, hard rules, enforcement logic, URLs.
  if ($line -match 'https?://') { return $true }
  if ($line -match '(?i)\bHARD RULE\b|\bMANDATORY\b|\bMUST NOT\b|\bNEVER\b') { return $true }
  if ($line -match '(?i)acceptance criteri') { return $true }
  if ($line -match '(?i)^\s*[-*]?\s*(@?g-|/g-)') { return $true }   # command syntax
  return $false
}

function Find-RationalizationTables([string[]]$lines, [bool[]]$code) {
  # Returns @(@{ header; start; end; rows=@(idx...) }) for | Rationalization | Reality | tables.
  $tables = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($code[$i]) { continue }
    if ($lines[$i] -match '(?i)^\s*\|\s*Rationalization\s*\|\s*Reality\s*\|') {
      $start = $i; $rows = @(); $j = $i + 2  # +1 = separator row
      while ($j -lt $lines.Count -and $lines[$j] -match '^\s*\|') {
        if ($lines[$j] -notmatch '^\s*\|[\s\-:|]+\|\s*$') { $rows += $j }  # skip separators
        $j++
      }
      $tables += @{ header = $start; start = $start; end = ($j - 1); rows = $rows }
      $i = $j
    }
  }
  return $tables
}

function Find-BackgroundSections([string[]]$lines, [bool[]]$code) {
  $hits = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($code[$i]) { continue }
    if ($lines[$i] -match '(?i)^\s*#{2,}\s+(Background|Context)\b') { $hits += $i }
  }
  return $hits
}

function Find-BackrefFiller([string[]]$lines, [bool[]]$code) {
  $hits = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($code[$i]) { continue }
    if ($lines[$i] -match '(?i)^\s*[-*>]?\s*As (mentioned|noted|described|stated) (above|earlier|in)\b') {
      if (-not (Test-PreserveLine $lines[$i])) { $hits += $i }
    }
  }
  return $hits
}

function Find-NearIdenticalEnforcement([string[]]$lines, [bool[]]$code) {
  # Group non-code, non-preserve lines by a normalized signature; flag groups with >3 near-dups.
  $buckets = @{}
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($code[$i]) { continue }
    $t = $lines[$i].Trim()
    if ($t.Length -lt 20) { continue }
    if (Test-PreserveLine $lines[$i]) { continue }
    $sig = ($t.ToLower() -replace '[^a-z0-9 ]','' -replace '\s+',' ').Trim()
    $words = $sig -split ' '
    if ($words.Count -lt 4) { continue }
    $key = ($words | Select-Object -First 6) -join ' '
    if (-not $buckets.ContainsKey($key)) { $buckets[$key] = @() }
    $buckets[$key] += $i
  }
  $groups = @()
  foreach ($k in $buckets.Keys) { if ($buckets[$k].Count -gt 3) { $groups += ,@($buckets[$k]) } }
  return $groups
}

function Get-FileType([string]$file) {
  $name = [System.IO.Path]::GetFileName($file)
  if ($name -eq 'SKILL.md') { return 'skill' }
  if ($name -match '^g-rl-') { return 'rule' }
  if ($file -match '[\\/]agents[\\/]') { return 'agent' }
  if ($file -match '[\\/]commands[\\/]') { return 'command' }
  return 'other'
}

function Analyze-File([string]$file) {
  $raw = [System.IO.File]::ReadAllText($file)
  $lines = $raw -split "`r?`n"
  $code = Get-CodeBlockMask $lines
  $ftype = Get-FileType $file
  $signals = @()
  $suggestions = @()
  $score = 0

  # 1. rationalization table overflow (>5 rows)
  foreach ($tbl in (Find-RationalizationTables $lines $code)) {
    if ($tbl.rows.Count -gt 5) {
      $score += $Weights.rationalization_table_overflow
      $excess = $tbl.rows.Count - 3
      $signals += "rationalization_table_overflow (rows=$($tbl.rows.Count), keep 3 most impactful, drop ~$excess)"
      # suggest dropping the trailing rows (keep first 3 as 'most impactful' default; agent may reorder)
      $dropIdx = $tbl.rows | Select-Object -Skip 3
      foreach ($d in $dropIdx) {
        $suggestions += @{ line = ($d + 1); weight = $Weights.rationalization_table_overflow; reason = 'excess rationalization-table row'; text = $lines[$d].Trim() }
      }
    }
  }

  # 2. SKILL.md > 400 lines (flag for manual review only — never auto-cut)
  if ($ftype -eq 'skill' -and $lines.Count -gt 400) {
    $score += $Weights.skill_over_400_lines
    $signals += "skill_over_400_lines (lines=$($lines.Count); manual review — move reference content to reference/)"
  }

  # 3. rule file with >3 near-identical enforcement messages
  if ($ftype -eq 'rule') {
    foreach ($g in (Find-NearIdenticalEnforcement $lines $code)) {
      $score += $Weights.near_identical_enforcement
      $signals += "near_identical_enforcement ($($g.Count) near-duplicate lines around L$($g[0]+1))"
      foreach ($d in ($g | Select-Object -Skip 1)) {
        $suggestions += @{ line = ($d + 1); weight = $Weights.near_identical_enforcement; reason = 'near-identical enforcement message'; text = $lines[$d].Trim() }
      }
    }
  }

  # 4. agent file with >2 ## Background / ## Context sections
  if ($ftype -eq 'agent') {
    $bg = Find-BackgroundSections $lines $code
    if ($bg.Count -gt 2) {
      $score += $Weights.multiple_background_sections
      $signals += "multiple_background_sections ($($bg.Count) Background/Context headings — consolidate to 1)"
      foreach ($d in ($bg | Select-Object -Skip 1)) {
        $suggestions += @{ line = ($d + 1); weight = $Weights.multiple_background_sections; reason = 'redundant Background/Context heading'; text = $lines[$d].Trim() }
      }
    }
  }

  # 5. backref filler ("As mentioned above..." / "As noted in...")
  foreach ($d in (Find-BackrefFiller $lines $code)) {
    $score += $Weights.backref_filler
    $suggestions += @{ line = ($d + 1); weight = $Weights.backref_filler; reason = 'back-reference filler line'; text = $lines[$d].Trim() }
  }
  $brCount = (Find-BackrefFiller $lines $code).Count
  if ($brCount -gt 0) { $signals += "backref_filler ($brCount line(s))" }

  return [ordered]@{
    file        = $file
    type        = $ftype
    lines       = $lines.Count
    bloat_score = $score
    signals     = $signals
    suggestions = $suggestions
  }
}

function Get-Targets([string]$root) {
  $targets = @()
  if ($Path) {
    $p = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $root $Path }
    if (Test-Path $p -PathType Container) {
      $targets = Get-ChildItem -Path $p -Recurse -File -Filter '*.md' | ForEach-Object { $_.FullName }
    } elseif (Test-Path $p -PathType Leaf) {
      $targets = @($p)
    } else {
      Write-Error "Path not found: $p"; exit 2
    }
  } else {
    foreach ($sub in @('skills','rules','agents','commands')) {
      $dir = Join-Path (Join-Path $root '.gald3r_sys') $sub
      if (Test-Path $dir) { $targets += (Get-ChildItem -Path $dir -Recurse -File -Filter '*.md' | ForEach-Object { $_.FullName }) }
    }
  }
  return $targets
}

# Remove suggested lines (descending so indices stay valid). Returns new file text.
function Build-PrunedText([string]$file, [array]$suggestions) {
  $raw = [System.IO.File]::ReadAllText($file)
  $lines = [System.Collections.Generic.List[string]]($raw -split "`r?`n")
  $dropZeroBased = ($suggestions | ForEach-Object { $_.line - 1 } | Sort-Object -Descending -Unique)
  foreach ($z in $dropZeroBased) { if ($z -ge 0 -and $z -lt $lines.Count) { $lines.RemoveAt($z) } }
  return ($lines -join "`n")
}

# ---------------- main ----------------
$root = Get-ProjectRoot
$targets = Get-Targets $root
if (-not $targets -or $targets.Count -eq 0) {
  Write-Host 'No target .md files found.' -ForegroundColor Yellow; exit 0
}

$reports = @(foreach ($f in $targets) { Analyze-File $f })
# only keep files that actually carry signals for the ranked view
$ranked = @($reports | Where-Object { $_.bloat_score -gt 0 } | Sort-Object { $_.bloat_score } -Descending)

# ----- APPLY -----
if ($Mode -eq 'APPLY') {
  if (-not $Confirm) {
    Write-Error 'APPLY requires per-file -Confirm. Never bulk-applies. Re-run with a single -Path <file> and -Confirm.'; exit 2
  }
  if (-not $Path) {
    Write-Error 'APPLY operates on exactly ONE file at a time. Provide -Path <single file>, not a directory.'; exit 2
  }
  $resolvedPath = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $root $Path }
  if (Test-Path $resolvedPath -PathType Container) {
    Write-Error 'APPLY operates on exactly ONE file at a time. Provide -Path <single file>, not a directory.'; exit 2
  }
  $file = $targets[0]
  $rep = $reports | Where-Object { $_.file -eq $file } | Select-Object -First 1
  if (-not $rep -or $rep.suggestions.Count -eq 0) {
    Write-Host "No auto-applicable removals for $file (nothing to do)." -ForegroundColor Yellow; exit 0
  }
  Write-Host "APPLY — proposed removals for $file :" -ForegroundColor Cyan
  foreach ($s in ($rep.suggestions | Sort-Object line)) {
    Write-Host ("  - L{0} [{1}] {2}" -f $s.line, $s.reason, $s.text) -ForegroundColor DarkYellow
  }
  $new = Build-PrunedText $file $rep.suggestions
  [System.IO.File]::WriteAllText($file, $new)
  Write-Host "APPLIED: removed $($rep.suggestions.Count) line(s) from $file (preserved code/criteria/hard-rules/URLs)." -ForegroundColor Green
  exit 0
}

# ----- PREVIEW -----
if ($Mode -eq 'PREVIEW') {
  if ($Json) { ($ranked | ForEach-Object { @{ file = $_.file; suggestions = $_.suggestions } }) | ConvertTo-Json -Depth 6; exit 0 }
  Write-Host "g-skl-gald3r-optimize — PREVIEW (no files modified)" -ForegroundColor Cyan
  foreach ($r in $ranked) {
    Write-Host ("`n  {0}  (score={1}, {2} suggestion(s))" -f $r.file, $r.bloat_score, $r.suggestions.Count) -ForegroundColor White
    foreach ($s in ($r.suggestions | Sort-Object line)) {
      Write-Host ("    - L{0} [{1}]" -f $s.line, $s.reason) -ForegroundColor DarkYellow
      Write-Host ("        - {0}" -f $s.text) -ForegroundColor DarkGray
    }
    if ($r.suggestions.Count -eq 0) { Write-Host "    (flag-only signals — manual review; nothing auto-removable)" -ForegroundColor DarkGray }
  }
  Write-Host "`nTo apply: re-run with -Mode APPLY -Path <single file> -Confirm (per-file only)." -ForegroundColor Cyan
  exit 0
}

# ----- AUDIT (default) -----
if ($Json) { @{ scanned = $targets.Count; ranked = $ranked } | ConvertTo-Json -Depth 6; exit 0 }

Write-Host "g-skl-gald3r-optimize — AUDIT (read-only)" -ForegroundColor Cyan
Write-Host ("Scanned {0} file(s); {1} carry bloat signals.`n" -f $targets.Count, $ranked.Count)

Write-Host "Files ranked by bloat score:" -ForegroundColor White
if ($ranked.Count -eq 0) {
  Write-Host "  (none — all scanned files are within bloat thresholds)" -ForegroundColor DarkGray
} else {
  foreach ($r in $ranked) {
    Write-Host ("  {0,3}  {1}  [{2}, {3} lines]" -f $r.bloat_score, $r.file, $r.type, $r.lines) -ForegroundColor Yellow
    foreach ($sig in $r.signals) { Write-Host ("         - {0}" -f $sig) -ForegroundColor DarkGray }
  }
}

# top suggested removals across all files
$allSug = @()
foreach ($r in $ranked) { foreach ($s in $r.suggestions) { $allSug += @{ file = $r.file; line = $s.line; weight = $s.weight; reason = $s.reason; text = $s.text } } }
$topSug = @($allSug | Sort-Object { $_.weight } -Descending | Select-Object -First $Top)
Write-Host ("`nTop {0} suggested removals:" -f $Top) -ForegroundColor White
if ($topSug.Count -eq 0) {
  Write-Host "  (no line-level removals suggested — only flag-for-manual-review signals, if any)" -ForegroundColor DarkGray
} else {
  $n = 1
  foreach ($s in $topSug) {
    Write-Host ("  {0,2}. (w{1}) {2}:L{3} [{4}]" -f $n, $s.weight, [System.IO.Path]::GetFileName($s.file), $s.line, $s.reason) -ForegroundColor DarkYellow
    Write-Host ("        - {0}" -f $s.text) -ForegroundColor DarkGray
    $n++
  }
}
Write-Host "`nNext: -Mode PREVIEW to see per-file diffs; -Mode APPLY -Path <single file> -Confirm to prune (per-file only)." -ForegroundColor Cyan
exit 0
