<#
.SYNOPSIS
  Encode gald3r report JSON as TOON (Token-Oriented Object Notation) and export (T1382).
.DESCRIPTION
  ENCODE + DECODE + VALIDATE(lossless round-trip) + EXPORT for g-skl-toon-output.
  Wraps the standard envelope (version/timestamp/command/schema/data) around the
  supplied JSON `data` payload, encodes to TOON, validates round-trip, and writes a
  timestamped .toon under the output dir (g-rl-01).
.EXAMPLE
  pwsh -File toon_output.ps1 -Command g-status -Schema status -DataJson '{...}' -OutDir docs -Topic STATUS -Compare
#>
[CmdletBinding()]
param(
  [string]$Command,
  [string]$Schema,
  [string]$DataJson,
  [string]$Topic,
  [string]$OutDir = 'docs',
  [string]$ProjectRoot,
  [string]$IDE = 'Claude',
  [switch]$Compare,
  [switch]$Stdout,
  [switch]$AsLibrary   # define functions then return — for toon_test.ps1 (dot-source, no CLI run)
)
$ErrorActionPreference = 'Stop'

# ---------- helpers ----------
# A bare token that Coerce() would reinterpret on DECODE (number/bool/null lookalikes).
# A STRING value matching this MUST be quoted so it round-trips as a string, not an int
# /bool/null (e.g. "012" -> 012, "true" -> $true would be lossy). (T1384)
function Looks-Coercible([string]$s) {
  return ($s -eq 'null' -or $s -eq 'true' -or $s -eq 'false' -or $s -match '^-?\d+$' -or $s -match '^-?\d+\.\d+$')
}
# Quote a scalar string only when required: grammar/whitespace ambiguity (Need-Quote) or
# coercion ambiguity (Looks-Coercible). Characters %, #, !, @, *, and a lone \ are SAFE —
# none are part of the TOON grammar, so they never trigger quoting and round-trip bare. (T1383)
function Need-Quote([string]$s) { return ($s -match '[:|]' -or $s -match "`n" -or $s -ne $s.Trim() -or $s -eq '') }
function Enc-Scalar($v) {
  if ($null -eq $v) { return 'null' }
  if ($v -is [bool]) { return ($v.ToString().ToLower()) }
  if ($v -is [int] -or $v -is [long] -or $v -is [double] -or $v -is [decimal]) { return "$v" }
  $s = "$v"
  if ((Need-Quote $s) -or (Looks-Coercible $s)) { return '"' + ($s -replace '\\','\\' -replace '"','\"') + '"' }
  return $s
}
# Encode one TABULAR cell. null -> empty cell; "" -> quoted "" (disambiguates "" from null);
# number/bool-looking strings quoted (preserve type); literal pipes escaped \|. (T1384)
function Enc-Cell($cv) {
  if ($null -eq $cv) { return '' }
  if ($cv -is [bool]) { return $cv.ToString().ToLower() }
  if ($cv -is [int] -or $cv -is [long] -or $cv -is [double] -or $cv -is [decimal]) { return "$cv" }
  $s = "$cv"
  if ($s -eq '' -or (Looks-Coercible $s)) { return '"' + ($s -replace '\\','\\' -replace '"','\"') + '"' }
  return ($s -replace '\|','\|')
}
# Use the concrete runtime type, NOT [pscustomobject]: in PowerShell `-is [pscustomobject]`
# is the PSObject accelerator and is TRUE for nearly every value (strings, ints, ...),
# which made scalar arrays (e.g. ["feature","bug"]) wrongly encode as tabular. (T1384)
function Is-Obj($v) { return ($v -is [System.Management.Automation.PSCustomObject]) }
function Obj-Keys($o) { return $o.PSObject.Properties.Name }

function Encode-Node($node, [int]$indent, [System.Text.StringBuilder]$sb) {
  $pad = ' ' * $indent
  foreach ($p in $node.PSObject.Properties) {
    $k = $p.Name; $v = $p.Value
    if ($v -is [System.Collections.IEnumerable] -and $v -isnot [string]) {
      $arr = @($v)
      $allObj = ($arr.Count -gt 0) -and (($arr | Where-Object { -not (Is-Obj $_) }).Count -eq 0)
      if ($allObj) {
        $fields = Obj-Keys $arr[0]
        [void]$sb.AppendLine("$pad$k[$($arr.Count)]{$([string]::Join(',', $fields))}:")
        foreach ($rec in $arr) {
          $cells = foreach ($f in $fields) { Enc-Cell $rec.$f }
          [void]$sb.AppendLine("$pad  $([string]::Join(' | ', $cells))")
        }
      } else {
        # scalar array (also the empty-array case: yields "$k[0]: ")
        $items = @(foreach ($e in $arr) { Enc-Scalar $e })
        [void]$sb.AppendLine("$pad$k[$($arr.Count)]: $([string]::Join(', ', $items))")
      }
    } elseif (Is-Obj $v) {
      [void]$sb.AppendLine("$pad${k}:")
      Encode-Node $v ($indent + 2) $sb
    } else {
      [void]$sb.AppendLine("$pad${k}: $(Enc-Scalar $v)")
    }
  }
}

function Coerce([string]$s) {
  if ($s -eq 'null') { return $null }
  if ($s -eq 'true') { return $true }
  if ($s -eq 'false') { return $false }
  if ($s -match '^-?\d+$') { return [long]$s }
  if ($s -match '^-?\d+\.\d+$') { return [double]$s }
  if ($s.StartsWith('"') -and $s.EndsWith('"')) { return ($s.Substring(1,$s.Length-2) -replace '\\"','"' -replace '\\\\','\') }
  return $s
}

# Recursive-descent decode over an array of lines, by indentation.
function Decode-Block([object[]]$lines, [ref]$i, [int]$indent) {
  $obj = [ordered]@{}
  while ($i.Value -lt $lines.Count) {
    $line = $lines[$i.Value]
    if ($line.Trim() -eq '') { $i.Value++; continue }
    $curIndent = ($line.Length - $line.TrimStart(' ').Length)
    if ($curIndent -lt $indent) { break }
    if ($curIndent -gt $indent) { break }
    $t = $line.Trim()
    $m = [regex]::Match($t, '^([\w-]+)\[(\d+)\]\{([^}]*)\}:$')   # tabular array
    if ($m.Success) {
      $key=$m.Groups[1].Value; $n=[int]$m.Groups[2].Value; $fields=$m.Groups[3].Value.Split(',')
      $i.Value++
      $rows=@()
      for ($r=0; $r -lt $n -and $i.Value -lt $lines.Count; $r++) {
        # Split on UNESCAPED pipes only (escaped content pipes are \|). This is robust
        # to trailing-space loss — a trailing null/empty cell no longer needs a trailing
        # space to be detected (the document-level TrimEnd() would strip it). (T1384)
        $cells = $lines[$i.Value].TrimStart() -split '(?<!\\)\|'
        $rec=[ordered]@{}
        for ($c=0; $c -lt $fields.Count; $c++) {
          $cell = if ($c -lt $cells.Count) { ($cells[$c].Trim() -replace '\\\|','|') } else { '' }
          $rec[$fields[$c].Trim()] = if ($cell -eq '') { $null } else { Coerce $cell }
        }
        $rows += [pscustomobject]$rec; $i.Value++
      }
      $obj[$key]=$rows; continue
    }
    $m = [regex]::Match($t, '^([\w-]+)\[(\d+)\]:\s*(.*)$')        # scalar array
    if ($m.Success) {
      $vals = if ($m.Groups[3].Value.Trim()) { $m.Groups[3].Value.Split(',') | ForEach-Object { Coerce ($_.Trim()) } } else { @() }
      $obj[$m.Groups[1].Value]=@($vals); $i.Value++; continue
    }
    $m = [regex]::Match($t, '^([\w-]+):\s*(.*)$')                 # key: value | nested
    if ($m.Success) {
      $key=$m.Groups[1].Value; $val=$m.Groups[2].Value
      if ($val -eq '') { $i.Value++; $obj[$key]=[pscustomobject](Decode-Block $lines $i ($indent+2)) }
      else { $obj[$key]=Coerce $val; $i.Value++ }
      continue
    }
    $i.Value++  # unrecognized; skip
  }
  return $obj
}

if ($AsLibrary) { return }   # dot-sourced for tests: functions are defined, skip CLI run

# ---------- main ----------
if (-not $Command -or -not $Schema -or -not $DataJson) {
  Write-Error "toon_output.ps1 requires -Command, -Schema, and -DataJson (omit them only with -AsLibrary)."; exit 2
}
if ($Schema -notin @('status','review','backlog')) {
  Write-Error "Invalid -Schema '$Schema' (expected: status|review|backlog)."; exit 2
}
if (-not $ProjectRoot) {
  $d=(Get-Location).Path; while ($d -and -not (Test-Path (Join-Path $d '.gald3r'))) { $p=Split-Path $d -Parent; if($p -eq $d){break}; $d=$p }; $ProjectRoot=$d
}
$ver='unknown'; $idf=Join-Path $ProjectRoot '.gald3r/.identity'
if (Test-Path $idf) { $mm=Select-String -Path $idf -Pattern '^\s*gald3r_version=(.+)$' | Select-Object -First 1; if($mm){$ver=$mm.Matches[0].Groups[1].Value.Trim()} }

try { $data = $DataJson | ConvertFrom-Json } catch { Write-Host "VALIDATE: FAIL — data is not valid JSON: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }
$envelope=[pscustomobject][ordered]@{
  gald3r_version=$ver
  generated_at=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  command=$Command; schema=$Schema; data=$data
}

$sb=[System.Text.StringBuilder]::new()
Encode-Node $envelope 0 $sb
$toon=$sb.ToString().TrimEnd()

# VALIDATE: lossless round-trip (compare data payloads as canonical JSON)
$idx=[ref]0
$decoded=[pscustomobject](Decode-Block ($toon -split "`r?`n") $idx 0)
$srcJson=($envelope.data | ConvertTo-Json -Depth 24 -Compress)
$rtJson =($decoded.data | ConvertTo-Json -Depth 24 -Compress)
if ($srcJson -ne $rtJson) {
  Write-Host "VALIDATE: WARN — round-trip differs (lossy on this payload)." -ForegroundColor Yellow
} else {
  Write-Host "VALIDATE: PASS — lossless round-trip (schema=$Schema, version=$ver)" -ForegroundColor Green
}

if ($Compare) {
  $jsonChars=($envelope | ConvertTo-Json -Depth 24).Length
  $toonChars=$toon.Length
  $pct=[math]::Round(100*($jsonChars-$toonChars)/$jsonChars,1)
  Write-Host "COMPARE: JSON=$jsonChars chars  TOON=$toonChars chars  ($pct% smaller than JSON)" -ForegroundColor Cyan
}

if ($Stdout) { $toon; return }
if (-not $Topic) { $Topic=$Command -replace '[^A-Za-z0-9]+','_' }
$outAbs=Join-Path $ProjectRoot $OutDir
if (-not (Test-Path $outAbs)) { New-Item -ItemType Directory -Path $outAbs -Force | Out-Null }
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$outFile=Join-Path $outAbs ("{0}_{1}_{2}.toon" -f $stamp,$IDE,$Topic.ToUpper())
$toon | Set-Content -Path $outFile -Encoding UTF8
Write-Host "EXPORT: $outFile" -ForegroundColor Cyan
$outFile
