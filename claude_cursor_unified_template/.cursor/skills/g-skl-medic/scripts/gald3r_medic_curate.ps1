<#
.SYNOPSIS
  g-medic curation: dry-run fragmentation report, optional apply from prior proposal JSON.

.DESCRIPTION
  Default: analyze .gald3r/features and .gald3r/subsystems, run hierarchy sync helpers (-WarnOnly),
  optionally write markdown + machine-readable proposal under .gald3r/reports/. Never deletes feature/subsystem files.

  Apply: requires -ProposalJson pointing to JSON produced by a prior dry-run (same schema).
  Backs up each source file, executes git mv moves, replaces path strings in FEATURES.md, SUBSYSTEMS.md,
  and task markdown under .gald3r/tasks/** (status subfolders: open/, in-progress/, awaiting/, done/YYYY/MM/, closed/)
  when those files reference moved paths, then refreshes architecture diagrams.
  Refuses apply if git working tree has unexpected dirty paths under .gald3r/.

.PARAMETER NoReportFiles
  Dry-run only: do not write medic_curate_*.md / proposal JSON / medic_curate_latest.json (CI or no-disk mode).

.PARAMETER ProjectRoot
.PARAMETER Apply
.PARAMETER ProposalJson
  Path to medic_curate_proposal.json from a previous dry-run.

.PARAMETER ForceSameRun
  Reserved for future use — apply still requires ProposalJson today.
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$Apply,
    [string]$ProposalJson = '',
    [switch]$ForceSameRun,
    [switch]$NoReportFiles
)

$ErrorActionPreference = 'Stop'
$reports = Join-Path (Join-Path $ProjectRoot '.gald3r') 'reports'
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$proposalPath = Join-Path $reports "medic_curate_proposal_$stamp.json"
$reportMd = Join-Path $reports "medic_curate_$stamp.md"

function Get-GitStatusShort([string]$root) {
    Push-Location $root
    try { return (git status --porcelain=v1 -uall 2>$null) } finally { Pop-Location }
}

function Normalize-RepoPath([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return '' }
    return ($p.Trim() -replace '\\', '/')
}

function Update-TextFilePaths([string]$filePath, [array]$movePairs) {
    if (-not (Test-Path -LiteralPath $filePath)) { return $false }
    $t = Get-Content -LiteralPath $filePath -Raw -Encoding utf8
    $orig = $t
    foreach ($pair in $movePairs) {
        $from = $pair.from
        $to = $pair.to
        if ($from -and $to -and $t.Contains($from)) {
            $t = $t.Replace($from, $to)
        }
    }
    if ($t -eq $orig) { return $false }
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($filePath, $t, $utf8NoBom)
    return $true
}

function New-CurationSuggestion(
    [string]$kind,
    [string]$from,
    [string]$to,
    [string]$risk,
    [string]$confidence,
    [string]$rationale,
    [string]$action = 'move'
) {
    [ordered]@{
        kind       = $kind
        action     = $action
        from       = $from
        to         = $to
        risk       = $risk
        confidence = $confidence
        rationale  = $rationale
    }
}

function Get-FeatureArea([string]$fileName) {
    $n = $fileName.ToLowerInvariant()
    if ($n -match 'agent|gateway|trace|eval|inference|loop|sdk') { return 'gald3r-agent' }
    if ($n -match 'backend|api|mcp|oracle|docker|server|websocket|auth') { return 'gald3r-backend' }
    if ($n -match 'vault|knowledge|recon|harvest|ingest|crawl|memory') { return 'knowledge-vault' }
    if ($n -match 'workspace|pcac|link|member|template|parity') { return 'workspace-control' }
    if ($n -match 'skill|command|platform|cursor|claude|codex|opencode|gemini|copilot') { return 'platform-surfaces' }
    if ($n -match 'medic|health|status|task|bug|feature|prd|release|plan|constraint|subsystem') { return 'gald3r-control-plane' }
    if ($n -match 'desktop|tauri|electron|frontend|react|web|ui|theme|voice|3d|level') { return 'app-surfaces' }
    if ($n -match 'personality|fandom|fan|silicon|trek|firefly|bsg|hackers') { return 'personality-packs' }
    return 'needs-human-review'
}

function Get-SubsystemDomain([string]$fileName) {
    $n = $fileName.ToLowerInvariant()
    if ($n -match '^adopted_gald3r_web_') { return 'adopted/gald3r_web' }
    if ($n -match '^adopted_gald3r_discord_') { return 'adopted/gald3r_discord' }
    if ($n -match '^gald3r-agent-') { return 'gald3r-agent' }
    if ($n -match 'vault|knowledge|recon|harvest|ingest|crawl|memory') { return 'knowledge-vault' }
    if ($n -match 'backend|api|oracle|websocket|auth|streaming|status') { return 'backend' }
    if ($n -match 'frontend|web-ui|tauri|electron|theme|voice|3d|level|communications') { return 'apps' }
    if ($n -match 'ai-agent|ai-skill|command|behavioral|platform|parity|skill') { return 'platform-surfaces' }
    if ($n -match 'task|bug|feature|project|idea|release|planning|constraint|medic|health|subsystem') { return 'gald3r-control-plane' }
    if ($n -match 'workspace|pcac|link|member') { return 'workspace-control' }
    return 'core'
}

if ($Apply) {
    if ([string]::IsNullOrWhiteSpace($ProposalJson) -or -not (Test-Path -LiteralPath $ProposalJson)) {
        Write-Error "Apply requires -ProposalJson path to a dry-run proposal JSON (from .gald3r/reports/medic_curate_proposal_*.json)."
    }
    $dirty = @(Get-GitStatusShort $ProjectRoot)
    $unexpected = $dirty | Where-Object {
        $_ -match '^\?\?|^.. .gald3r/' -and
        $_ -notmatch 'reports[/\\]medic_curate' -and
        $_ -notmatch 'reports[/\\]medic_curate_backup'
    }
    if ($unexpected.Count -gt 0) {
        Write-Error "Refusing apply: working tree has unrelated changes:`n$($unexpected -join "`n")"
    }
    $prop = Get-Content -LiteralPath $ProposalJson -Raw -Encoding utf8 | ConvertFrom-Json
    if ($null -eq $prop.moves) { Write-Error 'Proposal has no moves array - run dry-run first.' }
    $movesArr = @($prop.moves)
    if ($movesArr.Count -eq 0) { Write-Error 'Proposal moves is empty. Add approved git mv entries to the JSON, then re-run -Apply.' }

    $normMoves = [System.Collections.Generic.List[hashtable]]::new()
    $tos = @{}
    $froms = @{}
    foreach ($m in $movesArr) {
        $f = Normalize-RepoPath ([string]$m.from)
        $t = Normalize-RepoPath ([string]$m.to)
        if (-not $f -or -not $t) { Write-Error "Move entry missing from/to: $($m | ConvertTo-Json -Compress)" }
        if ($f -eq $t) { Write-Error "Move from and to are identical: $f" }
        if ($f -notmatch '(?i)^\.gald3r/(features|subsystems)/') { Write-Error "Refusing apply: from path must be under .gald3r/features or .gald3r/subsystems: $f" }
        if ($t -notmatch '(?i)^\.gald3r/(features|subsystems)/') { Write-Error "Refusing apply: to path must be under .gald3r/features or .gald3r/subsystems: $t" }
        if ($tos.ContainsKey($t)) { Write-Error "Refusing apply: duplicate move target: $t" }
        if ($froms.ContainsKey($f)) { Write-Error "Refusing apply: duplicate move source: $f" }
        $tos[$t] = $true
        $froms[$f] = $true
        $normMoves.Add(@{ from = $f; to = $t })
    }

    $backupRoot = Join-Path $reports "medic_curate_backup_$stamp"
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

    foreach ($mv in $normMoves) {
        $fromFs = Join-Path $ProjectRoot ($mv.from -replace '/', [IO.Path]::DirectorySeparatorChar)
        $toFs = Join-Path $ProjectRoot ($mv.to -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $fromFs)) { Write-Warning "Skip missing: $fromFs"; continue }
        $relBackup = $mv.from.TrimStart('.').TrimStart('/')
        $destBackup = Join-Path $backupRoot ($relBackup -replace '/', [IO.Path]::DirectorySeparatorChar)
        $destDir = Split-Path $destBackup -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
        Copy-Item -LiteralPath $fromFs -Destination $destBackup -Force
        $toDir = Split-Path $toFs -Parent
        if (-not (Test-Path $toDir)) { New-Item -ItemType Directory -Force -Path $toDir | Out-Null }
        git -C $ProjectRoot mv -- "$($mv.from)" "$($mv.to)" 2>&1 | Write-Host
    }

    $gald3r = Join-Path $ProjectRoot '.gald3r'
    $patchFiles = @(
        (Join-Path $gald3r 'FEATURES.md'),
        (Join-Path $gald3r 'SUBSYSTEMS.md')
    )
    # T1025: tasks now live in status subfolders — use -Recurse to find all
    foreach ($tf in (Get-ChildItem -Path (Join-Path $gald3r 'tasks') -File -Filter '*.md' -Recurse -ErrorAction SilentlyContinue)) {
        $patchFiles += $tf.FullName
    }
    $updated = [System.Collections.Generic.List[string]]::new()
    foreach ($pf in $patchFiles) {
        if (Update-TextFilePaths $pf $normMoves) { $updated.Add($pf) }
    }

    $manifest = Join-Path $reports "medic_curate_manifest_$stamp.json"
    @{
        applied          = $stamp
        source_proposal  = $ProposalJson
        moves            = $normMoves
        backup_directory = $backupRoot
        patched_files    = @($updated)
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifest -Encoding utf8

    & (Join-Path (Join-Path $ProjectRoot 'scripts') 'gald3r_subsystem_diagrams_generate.ps1') -ProjectRoot $ProjectRoot
    Write-Host "Apply complete. Manifest: $manifest Backup: $backupRoot"
    exit 0
}

# --- Dry-run ---
$featSync = Join-Path (Join-Path $ProjectRoot 'scripts') 'gald3r_feature_hierarchy_sync.ps1'
$subSync = Join-Path (Join-Path $ProjectRoot 'scripts') 'gald3r_subsystem_hierarchy_sync.ps1'
$featOut = (& powershell -NoProfile -ExecutionPolicy Bypass -File $featSync -ProjectRoot $ProjectRoot -WarnOnly -Json 2>$null) | Select-Object -Last 1
$subOut = (& powershell -NoProfile -ExecutionPolicy Bypass -File $subSync -ProjectRoot $ProjectRoot -WarnOnly -Json 2>$null) | Select-Object -Last 1

$featRoot = Join-Path (Join-Path $ProjectRoot '.gald3r') 'features'
$subRoot = Join-Path (Join-Path $ProjectRoot '.gald3r') 'subsystems'
$featureFileItems = @(Get-ChildItem $featRoot -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '(?i)feat[-_]?\d+' })
$subsystemFileItems = @(Get-ChildItem $subRoot -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -notmatch '^(SYSTEM_|SUBSYSTEM_TREE|DEPENDENCY_GRAPH)'
    })
$featFiles = $featureFileItems.Count
$subFiles = $subsystemFileItems.Count
$nestedFeat = (Get-ChildItem $featRoot -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue | Where-Object {
        $_.DirectoryName -ne $featRoot
    }).Count

$areas = @{}
$featureFileItems | ForEach-Object {
    $rel = $_.FullName.Substring($featRoot.Length).TrimStart('\')
    $seg = ($rel -split '\\')[0]
    if ($seg -match '(?i)^feat[-_]?\d+') { $key = '_flat_root' } else { $key = $seg }
    if (-not $areas.ContainsKey($key)) { $areas[$key] = 0 }
    $areas[$key]++
}

$suggestedMoves = [System.Collections.Generic.List[object]]::new()
$indexCandidates = [System.Collections.Generic.List[object]]::new()

foreach ($ff in ($featureFileItems | Sort-Object FullName)) {
    if ($ff.DirectoryName -ne $featRoot) { continue }
    $rel = '.gald3r/features/' + $ff.Name
    $area = Get-FeatureArea $ff.Name
    $risk = if ($area -eq 'needs-human-review') { 'medium' } else { 'low' }
    $confidence = if ($area -eq 'needs-human-review') { 'low' } else { 'medium' }
    $targetArea = $area
    $suggestedMoves.Add((New-CurationSuggestion `
                -kind 'feature' `
                -from $rel `
                -to ".gald3r/features/$targetArea/$($ff.Name)" `
                -risk $risk `
                -confidence $confidence `
                -rationale "Flat root feature file; filename tokens map to the '$targetArea' feature area. Review before copying into apply moves."))
}

foreach ($sf in ($subsystemFileItems | Sort-Object FullName)) {
    if ($sf.DirectoryName -ne $subRoot) { continue }
    $rel = '.gald3r/subsystems/' + $sf.Name
    $domain = Get-SubsystemDomain $sf.Name
    $risk = if ($domain -eq 'core') { 'medium' } else { 'low' }
    $confidence = if ($domain -eq 'core') { 'low' } else { 'medium' }
    $suggestedMoves.Add((New-CurationSuggestion `
                -kind 'subsystem' `
                -from $rel `
                -to ".gald3r/subsystems/$domain/$($sf.Name)" `
                -risk $risk `
                -confidence $confidence `
                -rationale "Flat subsystem spec; filename tokens map to the '$domain' domain. Moving requires index/path patch review."))
}

# FEATURES.md: duplicate feat-NNN id lines (same id appears more than once in index table)
$featDupes = @()
$featuresMd = Join-Path (Join-Path $ProjectRoot '.gald3r') 'FEATURES.md'
if (Test-Path -LiteralPath $featuresMd) {
    $fm = Get-Content -LiteralPath $featuresMd -Raw -Encoding utf8
    # Count feat-NNN only on markdown table rows (| ... |) to skip narrative mentions
    $idHits = @{}
    foreach ($line in ($fm -split "`r?`n")) {
        if ($line -notmatch '^\|') { continue }
        foreach ($m in [regex]::Matches($line, '(?i)feat-(\d+)')) {
            $id = $m.Groups[1].Value
            if (-not $idHits.ContainsKey($id)) { $idHits[$id] = 0 }
            $idHits[$id]++
        }
    }
    foreach ($k in $idHits.Keys) {
        if ($idHits[$k] -gt 1) { $featDupes += "feat-$k appears $($idHits[$k]) times in FEATURES.md table rows" }
    }
}

$subJsonObj = $null
try { $subJsonObj = $subOut | ConvertFrom-Json } catch { $subJsonObj = $null }
$diskNotIndexed = @()
if ($null -ne $subJsonObj -and $null -ne $subJsonObj.disk_not_indexed) {
    $diskNotIndexed = @($subJsonObj.disk_not_indexed)
}
foreach ($p in $diskNotIndexed) {
    $confidence = if ($p -match 'nested-path-demo') { 'low' } else { 'high' }
    $risk = if ($p -match 'nested-path-demo') { 'low' } else { 'low' }
    $rationale = if ($p -match 'nested-path-demo') {
        'Fixture/demo path detected. Keep unindexed unless you want fixture specs surfaced in SUBSYSTEMS.md.'
    }
    else {
        'Spec exists on disk but is absent from SUBSYSTEMS.md index; likely should be registered before broader tree moves.'
    }
    $indexCandidates.Add((New-CurationSuggestion `
                -kind 'subsystem-index' `
                -action 'index' `
                -from ".gald3r/$p" `
                -to '.gald3r/SUBSYSTEMS.md' `
                -risk $risk `
                -confidence $confidence `
                -rationale $rationale))
}

$sb = [System.Text.StringBuilder]::new()
[void]$sb.AppendLine('# medic_curate dry-run ' + $stamp + ' UTC')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Executive summary')
[void]$sb.AppendLine('')
[void]$sb.AppendLine("This is a **recommendation report**, not an apply plan. It found $featFiles feature files, $subFiles subsystem specs, and $($diskNotIndexed.Count) subsystem specs that exist on disk but are not indexed.")
[void]$sb.AppendLine('')
[void]$sb.AppendLine('**Recommended next step:** review the `suggested_moves` and `index_candidates` sections in the JSON, copy only approved entries into the top-level `moves` array, then run `-Apply -ProposalJson`. The top-level `moves` array remains empty by design so dry-run suggestions cannot migrate files accidentally.')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('### Suggested first batch')
[void]$sb.AppendLine('')
if ($indexCandidates.Count -gt 0) {
    [void]$sb.AppendLine('1. Register real `disk_not_indexed` subsystem specs in `SUBSYSTEMS.md`; keep fixtures/demo files unindexed unless they are meant to become real subsystems.')
}
else {
    [void]$sb.AppendLine('1. No unindexed subsystem specs detected.')
}
if (($areas.ContainsKey('_flat_root')) -and $areas['_flat_root'] -gt 0) {
    [void]$sb.AppendLine("2. Move flat root feature files into reviewed area folders. Candidate count: $($areas['_flat_root']).")
}
else {
    [void]$sb.AppendLine('2. Feature files already appear to live under area folders; focus on index cleanup first.')
}
[void]$sb.AppendLine('3. Move flat subsystem specs into domain folders only after reviewing `SUBSYSTEMS.md` link updates in the resulting diff.')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Summary')
[void]$sb.AppendLine('| Metric | Value |')
[void]$sb.AppendLine('|--------|-------|')
[void]$sb.AppendLine("| Feature markdown files (featNNN / feat-NNN) | $featFiles |")
[void]$sb.AppendLine("| Subsystem spec files (recursive) | $subFiles |")
[void]$sb.AppendLine("| Nested-under-area feature paths (heuristic) | $nestedFeat |")
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Fragmentation heuristics')
if ($featDupes.Count -gt 0) {
    [void]$sb.AppendLine('### Possible duplicate feature IDs in FEATURES.md')
    foreach ($d in ($featDupes | Select-Object -First 20)) { [void]$sb.AppendLine("- $d") }
    if ($featDupes.Count -gt 20) {
        [void]$sb.AppendLine("- _(truncated - see proposal JSON feature_dupes for all $($featDupes.Count) entries)_")
    }
    [void]$sb.AppendLine('')
}
else {
    [void]$sb.AppendLine('- No duplicate `feat-NNN` token counts detected in FEATURES.md table rows.')
    [void]$sb.AppendLine('')
}
if ($diskNotIndexed.Count -gt 0) {
    [void]$sb.AppendLine("### Subsystem specs on disk not matched in SUBSYSTEMS.md index ($($diskNotIndexed.Count))")
    $diskNotIndexed | Select-Object -First 25 | ForEach-Object { [void]$sb.AppendLine("- ``$_``") }
    if ($diskNotIndexed.Count -gt 25) { [void]$sb.AppendLine('- _(truncated — see proposal JSON `subsystem_sync.disk_not_indexed`)_') }
    [void]$sb.AppendLine('')
}

[void]$sb.AppendLine('## Feature area counts (folder segment under features/)')
foreach ($k in ($areas.Keys | Sort-Object)) {
    [void]$sb.AppendLine("- **$k**: $($areas[$k]) file(s)")
}
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Recommended candidate actions')
[void]$sb.AppendLine('')
if ($indexCandidates.Count -gt 0) {
    [void]$sb.AppendLine('### Index registration candidates')
    [void]$sb.AppendLine('| Action | Source | Target | Confidence | Rationale |')
    [void]$sb.AppendLine('|--------|--------|--------|------------|-----------|')
    foreach ($c in ($indexCandidates | Select-Object -First 20)) {
        $action = $c['action']
        $from = $c['from']
        $to = $c['to']
        $confidence = $c['confidence']
        $rationale = $c['rationale']
        [void]$sb.AppendLine("| $action | ``$from`` | ``$to`` | $confidence | $rationale |")
    }
    if ($indexCandidates.Count -gt 20) { [void]$sb.AppendLine('| note | _(truncated)_ | proposal JSON | - | See `index_candidates` for all candidates. |') }
    [void]$sb.AppendLine('')
}
if ($suggestedMoves.Count -gt 0) {
    [void]$sb.AppendLine('### Candidate file moves')
    [void]$sb.AppendLine('| Kind | From | To | Risk | Confidence | Rationale |')
    [void]$sb.AppendLine('|------|------|----|------|------------|-----------|')
    foreach ($c in ($suggestedMoves | Sort-Object kind, risk, from | Select-Object -First 40)) {
        $kind = $c['kind']
        $from = $c['from']
        $to = $c['to']
        $risk = $c['risk']
        $confidence = $c['confidence']
        $rationale = $c['rationale']
        [void]$sb.AppendLine("| $kind | ``$from`` | ``$to`` | $risk | $confidence | $rationale |")
    }
    if ($suggestedMoves.Count -gt 40) { [void]$sb.AppendLine('| note | _(truncated)_ | proposal JSON | - | - | See `suggested_moves` for all candidates. |') }
    [void]$sb.AppendLine('')
}
else {
    [void]$sb.AppendLine('- No candidate moves generated by the current heuristics.')
    [void]$sb.AppendLine('')
}
[void]$sb.AppendLine('## Hierarchy sync (machine JSON)')
[void]$sb.AppendLine('```json')
[void]$sb.AppendLine($featOut)
[void]$sb.AppendLine($subOut)
[void]$sb.AppendLine('```')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Proposed moves')
[void]$sb.AppendLine('_Conservative default: no automatic apply moves in dry-run._ Review `suggested_moves`, copy approved `{ from, to }` entries into the JSON top-level `moves` array, then run `-Apply -ProposalJson`. Apply copies each source into `reports/medic_curate_backup_<stamp>/`, runs `git mv`, then replaces path strings in FEATURES.md, SUBSYSTEMS.md, and `.gald3r/tasks/**/*.md` (status subfolders — T1025) when they reference old paths.')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Risk')
[void]$sb.AppendLine('- **Low** for read-only dry-run (use `-NoReportFiles` to avoid writing report/proposal files).')
[void]$sb.AppendLine('- **Medium** when applying moves: review git diff; path replace is literal substring — avoid ambiguous partial paths.')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('## Workspace-Control')
[void]$sb.AppendLine('This script only targets the controller `.gald3r/` tree passed as `-ProjectRoot`. Do not point at member repos with marker-only `.gald3r/`.')

$proposal = @{
    schemaVersion    = 1
    generated_utc    = $stamp
    moves            = @()
    suggested_moves  = @($suggestedMoves)
    index_candidates = @($indexCandidates)
    notes            = 'moves is intentionally empty. Review suggested_moves and copy approved { from, to } entries into moves before -Apply. index_candidates are SUBSYSTEMS.md registration suggestions, not git mv entries.'
    feature_sync     = ($featOut | ConvertFrom-Json)
    subsystem_sync   = ($subOut | ConvertFrom-Json)
    feature_dupes    = @($featDupes)
    disk_not_indexed = $diskNotIndexed
}

if (-not $NoReportFiles) {
    Set-Content -LiteralPath $reportMd -Value $sb.ToString() -Encoding utf8
    $proposal | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $proposalPath -Encoding utf8
    Copy-Item -LiteralPath $proposalPath -Destination (Join-Path $reports 'medic_curate_latest.json') -Force
    Write-Host "Dry-run report: $reportMd"
    Write-Host "Proposal JSON: $proposalPath"
    Write-Host "(also copied to reports/medic_curate_latest.json)"
}
else {
    Write-Host ($sb.ToString())
    Write-Host '--- proposal (stdout, not written) ---'
    Write-Host ($proposal | ConvertTo-Json -Depth 10)
}
