<#
.SYNOPSIS
  Edge-case round-trip tests for the TOON encoder/decoder (T1384).
.DESCRIPTION
  Dot-sources toon_output.ps1 -AsLibrary to exercise the REAL Encode-Node /
  Decode-Block / Coerce functions (no duplicated logic, per g-rl-04), then asserts
  ENCODE -> DECODE is lossless for nine edge cases that the in-line VALIDATE
  smoke-test does not cover. Standalone: `pwsh -File toon_test.ps1`.
  Exit 0 = all pass, 1 = one or more failures.
#>
[CmdletBinding()]
param([switch]$ShowToon)
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'toon_output.ps1') -AsLibrary

$script:pass = 0; $script:fail = 0

# Round-trip an arbitrary object through ENCODE then DECODE, compare canonical JSON.
function Roundtrip($obj) {
  $sb = [System.Text.StringBuilder]::new()
  # wrap in an envelope-like node so top level is always an object
  $node = [pscustomobject][ordered]@{ data = $obj }
  Encode-Node $node 0 $sb
  $toon = $sb.ToString().TrimEnd()
  $idx = [ref]0
  $decoded = [pscustomobject](Decode-Block ($toon -split "`r?`n") $idx 0)
  return @{
    Toon = $toon
    SrcJson = ($node.data | ConvertTo-Json -Depth 24 -Compress)
    RtJson  = ($decoded.data | ConvertTo-Json -Depth 24 -Compress)
  }
}

function Test-Case([string]$name, $obj) {
  $r = Roundtrip $obj
  if ($r.SrcJson -eq $r.RtJson) {
    $script:pass++; Write-Host "  PASS  $name" -ForegroundColor Green
  } else {
    $script:fail++
    Write-Host "  FAIL  $name" -ForegroundColor Red
    Write-Host "        src: $($r.SrcJson)" -ForegroundColor DarkGray
    Write-Host "        got: $($r.RtJson)"  -ForegroundColor DarkGray
  }
  if ($ShowToon) { Write-Host "----TOON----`n$($r.Toon)`n------------" -ForegroundColor DarkCyan }
}

Write-Host "TOON edge-case round-trip tests" -ForegroundColor Cyan

# 1. Object nested 3+ levels deep
Test-Case 'nested 3+ levels deep' ([pscustomobject]@{
  a = [pscustomobject]@{ b = [pscustomobject]@{ c = [pscustomobject]@{ d = 42; label = 'deep' } } }
})

# 2. Empty object array  -> [] (not null)
Test-Case 'empty array' ([pscustomobject]@{ items = @() })

# 3. Single-element object array -> 1-element array (not scalar)
Test-Case 'single-element object array' ([pscustomobject]@{
  rows = @([pscustomobject]@{ id = 1; name = 'only' })
})

# 4. null cell in a tabular row -> $null
Test-Case 'null cell in tabular row' ([pscustomobject]@{
  rows = @(
    [pscustomobject]@{ id = 1; note = 'has' }
    [pscustomobject]@{ id = 2; note = $null }
  )
})

# 5. Pipe-escaped cell -> literal | preserved
Test-Case 'pipe inside tabular cell' ([pscustomobject]@{
  rows = @([pscustomobject]@{ id = 1; expr = 'a | b'; cmd = 'x|y' })
})

# 6. Empty string value round-trips as "" (scalar AND tabular cell)
Test-Case 'empty string scalar' ([pscustomobject]@{ blank = '' })
Test-Case 'empty string in tabular cell' ([pscustomobject]@{
  rows = @([pscustomobject]@{ id = 1; note = '' })
})

# 7. Numeric-looking string preserved as string, not coerced to int
Test-Case 'numeric-looking string scalar' ([pscustomobject]@{ code = '012' })
Test-Case 'numeric-looking string in tabular cell' ([pscustomobject]@{
  rows = @([pscustomobject]@{ id = 1; code = '007'; ver = '1.2' })
})
# bool-looking string must stay a string too
Test-Case 'bool-looking string scalar' ([pscustomobject]@{ flag = 'true' })

# 8. Real boolean in a tabular cell coerced correctly
Test-Case 'boolean in tabular cell' ([pscustomobject]@{
  rows = @([pscustomobject]@{ id = 1; active = $true; locked = $false })
})

# 9. Scalar array with 0 elements -> empty array
Test-Case 'empty scalar array' ([pscustomobject]@{ labels = @() })

# 9b. Non-empty scalar arrays must stay scalar (NOT become tabular {Length}) — the
#     bug that the broken Is-Obj hid (a string is -is [pscustomobject] in PowerShell).
Test-Case 'non-empty string scalar array' ([pscustomobject]@{ labels = @('feature','bug','chore') })
Test-Case 'numeric scalar array'          ([pscustomobject]@{ nums = @(1,2,3) })
Test-Case 'single-element scalar array'   ([pscustomobject]@{ one = @('solo') })

# Bonus: special characters are SAFE and round-trip bare (T1383)
Test-Case 'special chars % # ! @ * \ stay bare' ([pscustomobject]@{
  pct = '87%'; hash = '#tag'; bang = 'no!'; at = '@user'; star = 'a*b'; back = 'a\b'
})

Write-Host ""
Write-Host "Results: $script:pass passed, $script:fail failed" -ForegroundColor ($(if ($script:fail -eq 0) { 'Green' } else { 'Red' }))
exit ([int]($script:fail -gt 0))
