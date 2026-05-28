<#
.SYNOPSIS
  Analyze (and optionally apply) compression of the NON-gald3r sections of memory files
  (AGENTS.md / CLAUDE.md / *memory*.md) while strictly preserving gald3r-managed ranges. (T1053)
.DESCRIPTION
  DRY-RUN by default. Detects `<!-- gald3r SECTION START -->`..`<!-- gald3r SECTION END -->`
  marker pairs (and single-line `<!-- gald3r ... SECTION -->` markers) and treats everything
  INSIDE them as off-limits. Reports per-file token budgets (char/4 proxy) for the protected vs
  compressible regions so an agent (via the g-skl-compress-memory skill) can rewrite only the
  compressible prose. Apply mode splices an agent-produced compressed body back in, preserving
  protected ranges byte-for-byte, and only after explicit confirmation.

  Safety: in a gald3r SOURCE repo (this very repo — `.gald3r_sys/` present and no markers in the
  file) the ENTIRE memory file is gald3r-managed, so the script SKIPS it (nothing to compress).
.EXAMPLE
  pwsh -File gald3r_compress_memory.ps1                      # dry-run scan of AGENTS.md + CLAUDE.md
  pwsh -File gald3r_compress_memory.ps1 -Path AGENTS.md
  pwsh -File gald3r_compress_memory.ps1 -Path AGENTS.md -Apply -CompressedFile compressed_body.txt -Confirm
#>
[CmdletBinding()]
param(
  [string]$Path,                       # specific file; omitted = scan AGENTS.md + CLAUDE.md in -ProjectRoot
  [string]$ProjectRoot,
  [switch]$Apply,                      # default off = dry-run
  [string]$CompressedFile,             # apply mode: agent-produced compressed compressible-body
  [switch]$Confirm,                    # required for -Apply (no silent file writes)
  [switch]$Force,                      # consumer project with no markers: allow whole-file compress
  [switch]$Json
)
$ErrorActionPreference = 'Stop'

function Get-ProjectRoot {
  if ($ProjectRoot) { return $ProjectRoot }
  $d = (Get-Location).Path
  while ($d -and -not (Test-Path (Join-Path $d '.gald3r'))) {
    $p = Split-Path $d -Parent; if ($p -eq $d) { break }; $d = $p
  }
  return $d
}
function Est-Tokens([string]$s) { if (-not $s) { return 0 }; return [math]::Ceiling($s.Length / 4.0) }
function Is-SourceRepo([string]$root) { return (Test-Path (Join-Path $root '.gald3r_sys')) }

# Returns @{ protected=@(@{start;end}); hasMarkers=$bool } over 0-based line indices.
function Find-ProtectedRanges([string[]]$lines) {
  $ranges = @(); $open = $null; $had = $false
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i]
    if ($l -match '(?i)<!--.*gald3r.*(section\s+start|begin)') { $open = $i; $had = $true; continue }
    if ($l -match '(?i)<!--.*gald3r.*(section\s+end|^.*end\s*-->)' -and $null -ne $open) {
      $ranges += @{ start = $open; end = $i }; $open = $null; $had = $true; continue
    }
  }
  if ($null -ne $open) { $ranges += @{ start = $open; end = ($lines.Count - 1) } }  # unterminated → protect to EOF
  return @{ protected = $ranges; hasMarkers = $had }
}

function Analyze-File([string]$file, [string]$root) {
  $raw = [System.IO.File]::ReadAllText($file)
  $lines = $raw -split "`r?`n"
  $info = Find-ProtectedRanges $lines
  $totalTok = Est-Tokens $raw
  $result = [ordered]@{
    file = $file; total_tokens = $totalTok; has_markers = $info.hasMarkers
    protected_tokens = 0; compressible_tokens = 0; status = ''; note = ''
  }
  if (-not $info.hasMarkers) {
    if (Is-SourceRepo $root) {
      $result.status = 'skip'
      $result.note = 'gald3r SOURCE repo + no SECTION markers: entire file is gald3r-managed — nothing safely compressible.'
      $result.protected_tokens = $totalTok
      return $result
    } elseif (-not $Force) {
      $result.status = 'warn'
      $result.note = 'No gald3r SECTION markers found. In a consumer project this usually means an old install. Re-run with -Force to treat the whole file as user-compressible.'
      return $result
    } else {
      $result.status = 'compressible'
      $result.compressible_tokens = $totalTok
      $result.note = 'No markers; -Force: entire file treated as compressible (still dry-run unless -Apply).'
      return $result
    }
  }
  # markers present: compressible = lines outside protected ranges
  $protectedLineSet = New-Object System.Collections.Generic.HashSet[int]
  foreach ($r in $info.protected) { for ($k = $r.start; $k -le $r.end; $k++) { [void]$protectedLineSet.Add($k) } }
  $protText = ($lines | Where-Object { $protectedLineSet.Contains([array]::IndexOf($lines, $_)) }) -join "`n"
  $protTok = 0; $compTok = 0
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $t = Est-Tokens ($lines[$i] + "`n")
    if ($protectedLineSet.Contains($i)) { $protTok += $t } else { $compTok += $t }
  }
  $result.protected_tokens = $protTok
  $result.compressible_tokens = $compTok
  $result.status = 'compressible'
  $result.note = "$($info.protected.Count) protected gald3r range(s). Compress only the compressible region; preserve code blocks + URLs verbatim. Target >=30% reduction on the compressible tokens."
  return $result
}

# ---------- main ----------
$root = Get-ProjectRoot
$targets = @()
if ($Path) { $targets = @($Path | ForEach-Object { if ([System.IO.Path]::IsPathRooted($_)) { $_ } else { Join-Path $root $_ } }) }
else { foreach ($n in @('AGENTS.md','CLAUDE.md')) { $p = Join-Path $root $n; if (Test-Path $p) { $targets += $p } } }

if ($targets.Count -eq 0) { Write-Host 'No memory files found (AGENTS.md/CLAUDE.md).' -ForegroundColor Yellow; exit 0 }

# APPLY mode (single file + compressed body) -----------------------------------
if ($Apply) {
  if (-not $Confirm) { Write-Error 'Apply mode requires -Confirm (no silent writes to tracked memory files).'; exit 2 }
  if (-not $Path -or -not $CompressedFile) { Write-Error 'Apply mode requires -Path <file> and -CompressedFile <agent-compressed-body>.'; exit 2 }
  $file = $targets[0]
  $lines = ([System.IO.File]::ReadAllText($file)) -split "`r?`n"
  $info = Find-ProtectedRanges $lines
  if (-not $info.hasMarkers) { Write-Error 'Refusing to apply: no gald3r SECTION markers — cannot guarantee protected-range preservation.'; exit 2 }
  # Rebuild: replace each compressible gap between protected ranges is non-trivial to map automatically;
  # for safety the apply path requires the agent to supply the FULL new file with protected ranges intact,
  # and we verify the protected ranges are byte-identical before writing.
  $newRaw = [System.IO.File]::ReadAllText($CompressedFile)
  $newLines = $newRaw -split "`r?`n"
  $newInfo = Find-ProtectedRanges $newLines
  $origProt = foreach ($r in $info.protected) { ($lines[$r.start..$r.end] -join "`n") }
  $newProt  = foreach ($r in $newInfo.protected) { ($newLines[$r.start..$r.end] -join "`n") }
  if (($origProt -join "`n--`n") -ne ($newProt -join "`n--`n")) {
    Write-Error 'Refusing to apply: protected gald3r range(s) differ between original and compressed file. No write performed.'; exit 3
  }
  [System.IO.File]::WriteAllText($file, $newRaw)
  Write-Host "APPLIED: $file (protected gald3r ranges verified byte-identical)" -ForegroundColor Green
  exit 0
}

# DRY-RUN report ----------------------------------------------------------------
$reports = foreach ($f in $targets) { Analyze-File $f $root }
if ($Json) { $reports | ConvertTo-Json -Depth 5; exit 0 }

Write-Host "g-skl-compress-memory — DRY RUN (no files modified)" -ForegroundColor Cyan
foreach ($r in $reports) {
  $pct = if ($r.compressible_tokens -gt 0) { [math]::Round(100.0 * 0.30, 0) } else { 0 }
  Write-Host ("`n  {0}" -f $r.file) -ForegroundColor White
  Write-Host ("    status={0}  total~{1} tok  protected~{2}  compressible~{3}" -f $r.status, $r.total_tokens, $r.protected_tokens, $r.compressible_tokens)
  if ($r.compressible_tokens -gt 0) {
    Write-Host ("    target: >=30% of {0} compressible tokens (~{1} tok saved)" -f $r.compressible_tokens, [math]::Ceiling($r.compressible_tokens*0.30)) -ForegroundColor DarkCyan
  }
  Write-Host ("    {0}" -f $r.note) -ForegroundColor DarkGray
}
Write-Host "`nTo compress: run the g-skl-compress-memory skill on the compressible region, then apply with -Apply -CompressedFile <new-full-file> -Confirm." -ForegroundColor Cyan
