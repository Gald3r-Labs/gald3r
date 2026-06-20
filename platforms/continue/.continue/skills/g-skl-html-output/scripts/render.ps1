<#
.SYNOPSIS
  Render a gald3r human-facing report as themed HTML (T1316).
.DESCRIPTION
  Implements CHOOSE_THEME + RENDER + VALIDATE + EXPORT for the g-skl-html-output
  skill. Composes docs/templates/html-base.html with an already-rendered body
  fragment, links the active theme (docs/themes/_active.css), and writes a
  timestamped file under the output dir per g-rl-01 naming.

  Coordination files (TASKS.md, BUGS.md, task specs) are NEVER rendered here.
.EXAMPLE
  pwsh -File render.ps1 -Template report -Title "Project Status" `
       -SessionLabel "g-status - <gald3r_source>" -BodyHtml $html -OutDir docs -Topic STATUS
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('base','report','review','backlog')][string]$Template,
  [Parameter(Mandatory)][string]$Title,
  [string]$SessionLabel = '',
  [Parameter(Mandatory)][string]$BodyHtml,
  [string]$Topic,
  [string]$OutDir = 'docs',
  [string]$ProjectRoot,
  [string]$IDE = 'Claude',
  [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'

# --- Resolve project root (walk up for .gald3r/) ---
if (-not $ProjectRoot) {
  $d = (Get-Location).Path
  while ($d -and -not (Test-Path (Join-Path $d '.gald3r'))) {
    $p = Split-Path $d -Parent; if ($p -eq $d) { break }; $d = $p
  }
  $ProjectRoot = $d
}
$themesDir = Join-Path $ProjectRoot 'docs/themes'
$tplDir    = Join-Path $ProjectRoot 'docs/templates'

# --- CHOOSE_THEME ---
$theme = 'gald3r-dark'
$cfg = Join-Path $ProjectRoot '.gald3r/config/AGENT_CONFIG.md'
if (Test-Path $cfg) {
  $m = Select-String -Path $cfg -Pattern '^\s*html_theme:\s*([\w-]+)' | Select-Object -First 1
  if ($m) { $theme = $m.Matches[0].Groups[1].Value }
}
if (-not (Test-Path (Join-Path $themesDir "$theme.css"))) {
  Write-Warning "Theme '$theme' not found; falling back to gald3r-dark."
  $theme = 'gald3r-dark'
}
# Rewrite _active.css redirect (T1328)
$activePath = Join-Path $themesDir '_active.css'
@"
/*! _active.css - active-theme resolution redirect (T1328). Rewritten by g-skl-html-output. */
@import url('$theme.css');
"@ | Set-Content -Path $activePath -Encoding UTF8

# --- Load templates ---
$base = Get-Content (Join-Path $tplDir 'html-base.html') -Raw
# Strip the leading template-documentation comment so its literal {{ }} tokens
# are not substituted into the output (keeps html-base.html self-documenting).
$base = [regex]::new('<!--.*?-->\s*', 'Singleline').Replace($base, '', 1)
if ($Template -ne 'base') {
  # Body fragment templates document structure; the caller supplies fully
  # rendered $BodyHtml, so we inject it directly into the base shell.
}

# --- Compute substitutions ---
$outAbs = Join-Path $ProjectRoot $OutDir
$themeHref = 'themes/_active.css'
try {
  $rel = [IO.Path]::GetRelativePath($outAbs, (Join-Path $themesDir '_active.css'))
  if ($rel) { $themeHref = $rel -replace '\\','/' }
} catch { }
$mermaidTheme = if ($theme -eq 'gald3r-light') { 'default' } else { 'dark' }
$genDate = (Get-Date).ToString('yyyy-MM-dd')

$html = $base.
  Replace('{{ title }}', $Title).
  Replace('{{ generated_date }}', $genDate).
  Replace('{{ session_label }}', $SessionLabel).
  Replace('{{ theme_href }}', $themeHref).
  Replace('{{ mermaid_theme }}', $mermaidTheme).
  Replace('{{ body }}', $BodyHtml)

# --- VALIDATE ---
$errors = @()
if ($html -match '\{\{\s*\w+\s*\}\}') { $errors += "Unsubstituted placeholder(s) remain." }
if ($html -match '<style[ >]')        { $errors += "Inline <style> present; styling must be external." }
if (-not (Test-Path (Join-Path $themesDir "$theme.css"))) { $errors += "Active theme CSS missing." }
$mer = [regex]::Matches($html, '<div class="mermaid">(.*?)</div>', 'Singleline')
foreach ($x in $mer) {
  $b = $x.Groups[1].Value.Trim()
  if ($b -and $b -notmatch '^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|journey)') {
    $errors += "Mermaid block does not start with a known diagram keyword."
  }
}
if ($errors.Count) {
  Write-Host "VALIDATE: FAIL" -ForegroundColor Red
  $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
  exit 1
}
Write-Host "VALIDATE: PASS (theme=$theme, mermaid=$mermaidTheme)" -ForegroundColor Green
if ($ValidateOnly) { return }

# --- EXPORT (g-rl-01 naming) ---
if (-not $Topic) { $Topic = ($Title -replace '[^A-Za-z0-9]+','_').Trim('_').ToUpper() }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$fname = "{0}_{1}_{2}.html" -f $stamp, $IDE, $Topic.ToUpper()
if (-not (Test-Path $outAbs)) { New-Item -ItemType Directory -Path $outAbs -Force | Out-Null }
$outFile = Join-Path $outAbs $fname
$html | Set-Content -Path $outFile -Encoding UTF8
Write-Host "EXPORT: $outFile" -ForegroundColor Cyan
$outFile
