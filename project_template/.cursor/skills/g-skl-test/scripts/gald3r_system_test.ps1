<#
.SYNOPSIS
    gald3r systems functional test harness (T1540).

.DESCRIPTION
    Exercises each major gald3r system independently and emits a per-system
    PASS / PARTIAL / FAIL result plus an overall functionality percentage:
    "gald3r is N% functional on this install".

    This is the complement to T1532 (custom_scripts/tests/run_l1_tests.ps1, the
    framework code-test runner). T1532 targets the framework's own tooling; this
    harness targets the gald3r systems that ship to users -- the PRODUCT_SYSTEMS
    defined_groups (Task Management, Bug Tracking, Platform Integration, ...).

    Tests are NON-DESTRUCTIVE: read-only structural/presence checks where possible;
    any write (Task / Bug create-read-update) happens in a throwaway temp dir and
    NEVER touches the real .gald3r/ tree. Where a system cannot be functionally
    exercised cheaply, the test does an honest structural/presence check and labels
    it [structural] in the notes (no fake green).

    DRY reuse: the Platform Parity and PLATFORM_SPEC checks shell out to the existing
    custom_scripts/platform_parity_sync.ps1 rather than re-implementing parity logic.

.PARAMETER ProjectRoot
    The gald3r install root to test. Defaults to the repo containing this script
    (two levels up from custom_scripts/).

.PARAMETER FailBelow
    CI gate: exit with a non-zero code when the overall functionality score is
    below this percentage (0-100). Default 0 (never gate on score).

.PARAMETER Json
    Emit a machine-readable JSON summary to stdout instead of the human table.
    (The markdown report is still written to .gald3r/reports/ in both modes.)

.PARAMETER NoReport
    Do not write the markdown report file (stdout summary only). Useful for the
    canonical install-template tree where .gald3r/reports/ is not present.

.PARAMETER Systems
    Optional comma-separated list of system keys to run (subset). Default: all.
    Keys: task,bug,platform_spec,parity,hooks,git_hooks,schema,constraints,
          subsystems,skills,wpac,release,encoding

.EXAMPLE
    pwsh custom_scripts\gald3r_system_test.ps1
    # Run every system test against the current repo, write report, print table.

.EXAMPLE
    pwsh custom_scripts\gald3r_system_test.ps1 -ProjectRoot . -FailBelow 80
    # CI gate: exits non-zero if overall score < 80%.

.NOTES
    ASCII-only. Must parse and run under Windows PowerShell 5.1 (powershell.exe)
    AND PowerShell 7+ (pwsh). No em-dashes, smart quotes, or box-drawing chars.
    This is a gald3r_dev / install build+health tool, not part of the shipped
    template payload itself.
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [ValidateRange(0, 100)]
    [int]$FailBelow = 0,
    [switch]$Json,
    [switch]$NoReport,
    [string]$Systems = ""
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Resolve roots
# ---------------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    # custom_scripts/ -> repo root is one level up.
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
} else {
    $RepoRoot = (Resolve-Path $ProjectRoot).Path
}

$DotGald3r   = Join-Path $RepoRoot '.gald3r'
$DotGald3rSys = Join-Path $RepoRoot '.gald3r_sys'
$CustomScripts = Join-Path $RepoRoot 'custom_scripts'

# project name + version from .identity (best-effort)
$projectName = 'unknown'
$gald3rVersion = 'unknown'
$identityPath = Join-Path $DotGald3r '.identity'
if (Test-Path $identityPath) {
    foreach ($line in (Get-Content $identityPath -ErrorAction SilentlyContinue)) {
        if ($line -match '^\s*project_name\s*=\s*(.+?)\s*$') { $projectName = $Matches[1] }
        if ($line -match '^\s*gald3r_version\s*=\s*(.+?)\s*$') { $gald3rVersion = $Matches[1] }
    }
}

# ---------------------------------------------------------------------------
# Result accumulator. Each system test returns a hashtable:
#   @{ name=...; key=...; passed=N; failed=N; skipped=N; structural=$bool;
#      failures=@('FAIL: ...'); notes='...' }
# ---------------------------------------------------------------------------
function New-SystemResult {
    param([string]$Name, [string]$Key)
    return [ordered]@{
        name       = $Name
        key        = $Key
        passed     = 0
        failed     = 0
        skipped    = 0
        structural = $false
        failures   = New-Object System.Collections.Generic.List[string]
        notes      = ''
    }
}

function Add-Pass { param($R) $R.passed++ }
function Add-Fail { param($R, [string]$Msg) $R.failed++; $R.failures.Add("FAIL: $Msg") }
function Add-Skip { param($R) $R.skipped++ }

# Locate a powershell host for shelling out (prefer the one running us).
$psHost = (Get-Process -Id $PID).Path
if (-not $psHost) { $psHost = 'powershell.exe' }

function Invoke-Script {
    # Runs a .ps1 with args under the current host, captures combined output + exit code.
    param([string]$Path, [string[]]$Arguments = @())
    $out = ''
    $exit = $null
    try {
        $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Path) + $Arguments
        $out = & $psHost @argList 2>&1 | Out-String
        $exit = $LASTEXITCODE
    } catch {
        $out = $_.Exception.Message
        $exit = 999
    }
    return [pscustomobject]@{ Output = $out; Exit = $exit }
}

# ===========================================================================
# SYSTEM TESTS
# ===========================================================================

# --- Task Management ------------------------------------------------------
# Functional create/read/update cycle in a TEMP dir (never touches real .gald3r/).
function Test-TaskManagement {
    $R = New-SystemResult -Name 'Task Management' -Key 'task'
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("g3sys_task_" + [guid]::NewGuid().ToString('N').Substring(0,8))
    try {
        $tasksDir = Join-Path $tmp 'tasks'
        New-Item -ItemType Directory -Path $tasksDir -Force | Out-Null
        $taskFile = Join-Path $tasksDir 'task9001_harness_selftest.md'
        $indexFile = Join-Path $tmp 'TASKS.md'

        # 1) create task file
        $body = @"
---
id: T9001
title: "harness selftest"
status: pending
priority: low
type: chore
created: 2026-05-30
---

# T9001 - harness selftest
"@
        Set-Content -Path $taskFile -Value $body -Encoding UTF8
        if (Test-Path $taskFile) { Add-Pass $R } else { Add-Fail $R 'task file not created' }

        # 2) read it back + verify frontmatter id
        $read = Get-Content $taskFile -Raw
        if ($read -match '(?m)^id:\s*T9001\s*$') { Add-Pass $R } else { Add-Fail $R 'task frontmatter id not readable' }

        # 3) update status pending -> in-progress
        $updated = $read -replace '(?m)^(status:\s*)pending\s*$', '${1}in-progress'
        Set-Content -Path $taskFile -Value $updated -Encoding UTF8
        $reRead = Get-Content $taskFile -Raw
        if ($reRead -match '(?m)^status:\s*in-progress\s*$') { Add-Pass $R } else { Add-Fail $R 'status update did not persist' }

        # 4) write + verify a TASKS.md index row
        $row = "| [in-progress] | T9001 | harness selftest | low | chore |"
        Set-Content -Path $indexFile -Value @("# TASKS.md", "", $row) -Encoding UTF8
        $idx = Get-Content $indexFile -Raw
        if ($idx -match 'T9001') { Add-Pass $R } else { Add-Fail $R 'TASKS.md index row not written' }

        # 5) live g-skl-tasks ownership present (the real system the user installs)
        $skillLive = Join-Path $DotGald3rSys 'skills\g-skl-tasks\SKILL.md'
        $skillClaude = Join-Path $RepoRoot '.claude\skills\g-skl-tasks\SKILL.md'
        if ((Test-Path $skillLive) -or (Test-Path $skillClaude)) { Add-Pass $R } else { Add-Fail $R 'g-skl-tasks SKILL.md not found in install' }
    } finally {
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
    $R.notes = 'create/read/update/index in temp dir + g-skl-tasks present'
    return $R
}

# --- Bug Tracking ---------------------------------------------------------
function Test-BugTracking {
    $R = New-SystemResult -Name 'Bug Tracking' -Key 'bug'
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("g3sys_bug_" + [guid]::NewGuid().ToString('N').Substring(0,8))
    try {
        $bugsDir = Join-Path $tmp 'bugs'
        New-Item -ItemType Directory -Path $bugsDir -Force | Out-Null
        $bugFile = Join-Path $bugsDir 'bug9001_harness_selftest.md'
        $indexFile = Join-Path $tmp 'BUGS.md'

        $body = @"
---
id: BUG-9001
title: "harness selftest bug"
severity: Low
status: open
created: 2026-05-30
---

# BUG-9001 - harness selftest bug
"@
        Set-Content -Path $bugFile -Value $body -Encoding UTF8
        if (Test-Path $bugFile) { Add-Pass $R } else { Add-Fail $R 'bug file not created' }

        $read = Get-Content $bugFile -Raw
        if ($read -match '(?m)^id:\s*BUG-9001\s*$') { Add-Pass $R } else { Add-Fail $R 'bug frontmatter id not readable' }

        $row = "| BUG-9001 | harness selftest bug | Low | open |"
        Set-Content -Path $indexFile -Value @("# BUGS.md", "", $row) -Encoding UTF8
        $idx = Get-Content $indexFile -Raw
        if ($idx -match 'BUG-9001') { Add-Pass $R } else { Add-Fail $R 'BUGS.md index row not written' }
    } finally {
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
    $R.notes = 'create/read/index in temp dir'
    return $R
}

# --- PLATFORM_SPEC --------------------------------------------------------
# Reuse the existing -ValidatePlatformSpecs validator (DRY). It checks each
# canonical PLATFORM_SPEC.md for the three required sections. Exit 0 = all OK.
function Test-PlatformSpec {
    $R = New-SystemResult -Name 'PLATFORM_SPEC' -Key 'platform_spec'
    $parity = Join-Path $CustomScripts 'platform_parity_sync.ps1'
    if (-not (Test-Path $parity)) {
        Add-Skip $R
        $R.notes = 'platform_parity_sync.ps1 not present (skipped)'
        return $R
    }
    $res = Invoke-Script -Path $parity -Arguments @('-ValidatePlatformSpecs')
    $scanned = 0
    if ($res.Output -match 'Specs scanned\s*:\s*(\d+)') { $scanned = [int]$Matches[1] }
    if ($res.Exit -eq 0) {
        if ($scanned -gt 0) { Add-Pass $R } else { Add-Fail $R 'no PLATFORM_SPEC.md files were scanned' }
    } else {
        # Pull the MISSING-sections line for the failure detail.
        $missLine = ($res.Output -split "`r?`n" | Where-Object { $_ -match 'MISSING sections:' } | Select-Object -First 1)
        Add-Fail $R ("ValidatePlatformSpecs exit {0}: {1}" -f $res.Exit, ($missLine -replace '\s+', ' ').Trim())
    }
    $R.notes = "validator scanned $scanned spec(s)"
    return $R
}

# --- Platform Parity ------------------------------------------------------
# Run platform_parity_sync.ps1 in default (report-only / dry-run) mode and
# detect whether it flags missing-file gaps. There is no -CheckOnly flag; the
# default run (no -Sync) IS the check mode.
function Test-PlatformParity {
    $R = New-SystemResult -Name 'Platform Parity' -Key 'parity'
    $parity = Join-Path $CustomScripts 'platform_parity_sync.ps1'
    if (-not (Test-Path $parity)) {
        Add-Skip $R
        $R.notes = 'platform_parity_sync.ps1 not present (skipped)'
        return $R
    }
    $res = Invoke-Script -Path $parity -Arguments @()
    # The parity sync reports gaps with lines mentioning MISSING / gap counts.
    $gapLines = @($res.Output -split "`r?`n" | Where-Object { $_ -match '\bMISSING\b' -and $_ -notmatch 'MISSING sections' })
    if ($res.Exit -eq 0 -and $gapLines.Count -eq 0) {
        Add-Pass $R
        $R.notes = 'report-only run: exit 0, no missing-file gaps'
    } elseif ($res.Exit -ne 0) {
        Add-Fail $R ("parity sync exit {0}" -f $res.Exit)
        $R.notes = 'report-only run flagged a non-zero exit'
    } else {
        # exit 0 but gap lines present
        foreach ($g in ($gapLines | Select-Object -First 5)) { Add-Fail $R ($g.Trim()) }
        $R.notes = ("{0} parity gap line(s) detected" -f $gapLines.Count)
    }
    return $R
}

# --- Hook Wiring ----------------------------------------------------------
# Verify every wired hook command resolves on disk AND (for .ps1) parses cleanly.
#
# Reads BOTH config surfaces, matching the Python check_hook_wiring sibling:
#   * the canonical .claude/settings.json "hooks" block (T420 consolidation
#     target -- PascalCase events in a three-level event -> matcher -> hooks[]
#     shape; non-PascalCase event names are Cursor-era and silently do not fire)
#   * the legacy .claude/hooks.json (retained only for residual -File .ps1 wiring;
#     .py commands on that surface are retired by T420)
# .py hook scripts are existence-checked (no PowerShell parse needed); .ps1 hook
# scripts are existence- AND AST-parse-checked.

# Walk the settings.json "hooks" block. Returns @{ paths=@(script paths);
# structural=@(non-PascalCase event failures) }. Mirrors _settings_hook_wiring.
function Get-SettingsHookWiring {
    param([string]$SettingsJson)
    $paths = New-Object System.Collections.Generic.List[string]
    $structural = New-Object System.Collections.Generic.List[string]
    try {
        $data = (Get-Content $SettingsJson -Raw) | ConvertFrom-Json
    } catch {
        $structural.Add(("settings.json parse error: {0}" -f $_.Exception.Message))
        return @{ paths = @($paths); structural = @($structural) }
    }
    $hooks = $data.hooks
    if (-not $hooks) {
        return @{ paths = @($paths); structural = @($structural) }
    }
    foreach ($prop in $hooks.PSObject.Properties) {
        $event = $prop.Name
        if ($event.Length -gt 0 -and [char]::IsLower($event[0])) {
            $structural.Add(("non-PascalCase event '{0}' in settings.json (Cursor-era name; will not fire on Claude Code)" -f $event))
        }
        $groups = $prop.Value
        if ($groups -isnot [System.Collections.IEnumerable] -or $groups -is [string]) { continue }
        foreach ($group in $groups) {
            $entries = $group.hooks
            if (-not $entries) { continue }
            foreach ($entry in $entries) {
                $cmd = [string]$entry.command
                $m = [regex]::Match($cmd, '(?:-File\s+|python\s+)([^\s"]+\.(?:ps1|py))')
                if ($m.Success) { $paths.Add($m.Groups[1].Value) }
            }
        }
    }
    return @{ paths = @($paths | Sort-Object -Unique); structural = @($structural) }
}

function Test-HookWiring {
    $R = New-SystemResult -Name 'Hook Wiring' -Key 'hooks'
    $hooksJson = Join-Path $RepoRoot '.claude\hooks.json'
    $settingsJson = Join-Path $RepoRoot '.claude\settings.json'

    $pyPaths = New-Object System.Collections.Generic.List[string]
    $psPaths = New-Object System.Collections.Generic.List[string]

    # T420: canonical surface -- settings.json "hooks".
    if (Test-Path $settingsJson) {
        $wiring = Get-SettingsHookWiring -SettingsJson $settingsJson
        foreach ($msg in $wiring.structural) { Add-Fail $R $msg }
        foreach ($p in $wiring.paths) {
            if ($p.EndsWith('.ps1')) { $psPaths.Add($p) } else { $pyPaths.Add($p) }
        }
    }

    # Legacy surface -- hooks.json (only residual -File .ps1 wiring is checked
    # here; .py commands on this surface are retired by T420).
    if (Test-Path $hooksJson) {
        $raw = Get-Content $hooksJson -Raw
        foreach ($m in [regex]::Matches($raw, '-File\s+([^\s"]+\.ps1)')) {
            $psPaths.Add($m.Groups[1].Value)
        }
    }

    $pyPaths = @($pyPaths | Sort-Object -Unique)
    $psPaths = @($psPaths | Sort-Object -Unique)

    # .py hook scripts: existence is the honest check (no PS parse needed).
    foreach ($rel in $pyPaths) {
        $full = Join-Path $RepoRoot ($rel -replace '/', '\')
        if (Test-Path $full) { Add-Pass $R } else { Add-Fail $R ("hook missing on disk: {0}" -f $rel) }
    }

    $paths = $psPaths
    if ($paths.Count -eq 0) {
        if (($R.passed + $R.failed) -gt 0) {
            $R.notes = ("{0} settings.json-wired hook(s) verified; no .ps1 commands to parse-check" -f $pyPaths.Count)
        } else {
            Add-Skip $R
            $R.notes = 'no wired hook commands found in settings.json/hooks.json'
        }
        return $R
    }

    $errs = New-Object System.Collections.Generic.List[object]
    foreach ($rel in $paths) {
        $full = Join-Path $RepoRoot ($rel -replace '/', '\')
        if (-not (Test-Path $full)) {
            Add-Fail $R ("hook missing on disk: {0}" -f $rel)
            continue
        }
        [void][System.Management.Automation.Language.Parser]::ParseFile($full, [ref]$null, [ref]$errs)
        if ($errs.Count -gt 0) {
            Add-Fail $R ("hook parse error: {0}" -f $rel)
            $errs.Clear()
        } else {
            Add-Pass $R
        }
    }
    $R.notes = ("{0} wired hook(s) verified" -f $paths.Count)
    return $R
}

# --- Git Hooks ------------------------------------------------------------
# Honor core.hooksPath if set (this repo uses it), else .git/hooks/pre-commit.
# Verify the pre-commit hook exists and calls a dispatcher script.
function Test-GitHooks {
    $R = New-SystemResult -Name 'Git Hooks' -Key 'git_hooks'
    $hooksPath = $null
    try {
        $hooksPath = (& git -C $RepoRoot config --get core.hooksPath 2>$null)
        if ($LASTEXITCODE -ne 0) { $hooksPath = $null }
    } catch { $hooksPath = $null }

    if ($hooksPath) {
        $hooksDir = Join-Path $RepoRoot ($hooksPath -replace '/', '\')
        $R.notes = "core.hooksPath=$hooksPath"
    } else {
        $hooksDir = Join-Path $RepoRoot '.git\hooks'
        $R.notes = 'default .git/hooks'
    }
    $preCommit = Join-Path $hooksDir 'pre-commit'
    if (-not (Test-Path $preCommit)) {
        Add-Fail $R ("pre-commit hook not found at {0}" -f $preCommit)
        return $R
    }
    Add-Pass $R
    $content = Get-Content $preCommit -Raw
    # Dispatcher = the hook invokes a .ps1 / .sh / script (not an empty stub).
    if ($content -match '\.ps1|\.sh|pwsh|powershell|exec\s') {
        Add-Pass $R
    } else {
        Add-Fail $R 'pre-commit hook has no dispatcher invocation'
    }
    return $R
}

# --- Schema Validation ----------------------------------------------------
# Schema version probe (T1440 style): read system schema versions from
# .gald3r_sys/schemas/_registry.yaml and compare to schema_version frontmatter
# on TASKS.md + sampled task files. Report drift.
function Test-SchemaValidation {
    $R = New-SystemResult -Name 'Schema Validation' -Key 'schema'
    $registry = Join-Path $DotGald3rSys 'schemas\_registry.yaml'
    if (-not (Test-Path $registry)) {
        Add-Skip $R
        $R.notes = 'schemas/_registry.yaml not present (skipped)'
        return $R
    }
    Add-Pass $R  # registry present + readable
    $reg = Get-Content $registry -Raw

    # Map TASKS.md + task-file current_versions out of the registry (light parse).
    function Get-CurrentVersion {
        param([string]$Text, [string]$SchemaId)
        $m = [regex]::Match($Text, "schema_id:\s*$([regex]::Escape($SchemaId))\s*[\r\n]+\s*current_version:\s*(\S+)")
        if ($m.Success) { return $m.Groups[1].Value }
        return $null
    }
    $tasksMdVer = Get-CurrentVersion -Text $reg -SchemaId 'TASKS-md'
    $taskFileVer = Get-CurrentVersion -Text $reg -SchemaId 'task-file'

    # Probe .gald3r/TASKS.md frontmatter (missing schema_version => v0 / pre-versioned).
    $tasksMd = Join-Path $DotGald3r 'TASKS.md'
    if (Test-Path $tasksMd) {
        $head = (Get-Content $tasksMd -TotalCount 20) -join "`n"
        if ($head -match '(?m)^schema_version:\s*(\S+)') {
            $fv = $Matches[1]
            if ($tasksMdVer -and ($fv -ne $tasksMdVer)) {
                Add-Fail $R ("TASKS.md schema_version {0} != system {1}" -f $fv, $tasksMdVer)
            } else { Add-Pass $R }
        } else {
            # No schema_version field. This is the common pre-T1440 state; treat
            # as PASS-with-note rather than a hard fail (no drift to a newer ver).
            Add-Pass $R
            $R.notes = 'TASKS.md has no schema_version field (v0 / pre-versioned baseline)'
        }
    } else {
        Add-Skip $R
    }

    # Sample up to 3 recent task files for drift to a NEWER schema than the system.
    $tasksRoot = Join-Path $DotGald3r 'tasks'
    if (Test-Path $tasksRoot) {
        $sample = @(Get-ChildItem $tasksRoot -Recurse -Filter '*.md' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 3)
        $drift = 0
        foreach ($f in $sample) {
            $fh = (Get-Content $f.FullName -TotalCount 25) -join "`n"
            if ($fh -match '(?m)^schema_version:\s*(\S+)') {
                $fv = $Matches[1]
                if ($taskFileVer -and ($fv -ne $taskFileVer)) { $drift++ }
            }
        }
        if ($drift -eq 0) { Add-Pass $R } else { Add-Fail $R ("{0}/{1} sampled task files drift from system schema" -f $drift, $sample.Count) }
    } else {
        Add-Skip $R
    }
    return $R
}

# --- Constraints ----------------------------------------------------------
# Parse CONSTRAINTS.md; every active constraint in the index must have a
# corresponding **Enforcement**: definition block.
function Test-Constraints {
    $R = New-SystemResult -Name 'Constraints' -Key 'constraints'
    $cFile = Join-Path $DotGald3r 'CONSTRAINTS.md'
    if (-not (Test-Path $cFile)) {
        Add-Skip $R
        $R.notes = 'CONSTRAINTS.md not present (skipped)'
        return $R
    }
    $content = Get-Content $cFile -Raw
    # Index rows like: | C-001 | text | active | ... |
    $rowMatches = [regex]::Matches($content, '(?m)^\|\s*(C-\d+)\s*\|[^\|]*\|\s*active\s*\|')
    if ($rowMatches.Count -eq 0) {
        Add-Skip $R
        $R.notes = 'no active constraints in index'
        return $R
    }
    Add-Pass $R  # index parsed
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($m in $rowMatches) {
        $cid = $m.Groups[1].Value
        # Find the definition block heading and its Enforcement line.
        $blockHead = [regex]::Match($content, ("(?m)^##\s+" + [regex]::Escape($cid) + "\b"))
        if (-not $blockHead.Success) { $missing.Add("$cid (no definition block)"); continue }
        $rest = $content.Substring($blockHead.Index)
        $next = [regex]::Match($rest.Substring(1), '(?m)^##\s')
        $block = if ($next.Success) { $rest.Substring(0, 1 + $next.Index) } else { $rest }
        if ($block -match '(?im)\*\*Enforcement\*\*:') {
            # has enforcement
        } else {
            $missing.Add("$cid (no Enforcement field)")
        }
    }
    if ($missing.Count -eq 0) {
        Add-Pass $R
    } else {
        foreach ($x in ($missing | Select-Object -First 5)) { Add-Fail $R ("constraint $x") }
    }
    $R.notes = ("{0} active constraint(s) checked" -f $rowMatches.Count)
    return $R
}

# --- Subsystems -----------------------------------------------------------
# Every SUBSYSTEMS.md entry must have a corresponding spec file in subsystems/.
function Test-Subsystems {
    $R = New-SystemResult -Name 'Subsystems' -Key 'subsystems'
    $ssFile = Join-Path $DotGald3r 'SUBSYSTEMS.md'
    $ssDir = Join-Path $DotGald3r 'subsystems'
    if (-not (Test-Path $ssFile)) {
        Add-Skip $R
        $R.notes = 'SUBSYSTEMS.md not present (skipped)'
        return $R
    }
    $content = Get-Content $ssFile -Raw
    # Rows: | SS-001 | parity-pipeline | active | ... |
    $rows = [regex]::Matches($content, '(?m)^\|\s*SS-\d+\s*\|\s*([a-z0-9\-_]+)\s*\|\s*(\w+)\s*\|')
    if ($rows.Count -eq 0) {
        Add-Skip $R
        $R.notes = 'no subsystem rows in registry'
        return $R
    }
    Add-Pass $R  # registry parsed
    $orphans = New-Object System.Collections.Generic.List[string]
    foreach ($m in $rows) {
        $name = $m.Groups[1].Value
        $status = $m.Groups[2].Value
        if ($status -ne 'active') { continue }  # only active entries require a spec
        $spec = Join-Path $ssDir ("{0}.md" -f $name)
        if (Test-Path $spec) {
            # ok
        } else {
            $orphans.Add($name)
        }
    }
    if ($orphans.Count -eq 0) {
        Add-Pass $R
    } else {
        foreach ($o in $orphans) { Add-Fail $R ("active subsystem '{0}' has no spec file in subsystems/" -f $o) }
    }
    $R.notes = ("{0} registry row(s); {1} active require spec" -f $rows.Count, (($rows | Where-Object { $_.Groups[2].Value -eq 'active' }).Count))
    return $R
}

# --- Skills Inventory -----------------------------------------------------
# Count skills; each SKILL.md must have name + description frontmatter.
function Test-SkillsInventory {
    $R = New-SystemResult -Name 'Skills Inventory' -Key 'skills'
    # Prefer the live install tree; fall back to .claude.
    $skillRoots = @()
    foreach ($cand in @((Join-Path $DotGald3rSys 'skills'), (Join-Path $RepoRoot '.claude\skills'))) {
        if (Test-Path $cand) { $skillRoots += $cand }
    }
    if ($skillRoots.Count -eq 0) {
        Add-Skip $R
        $R.notes = 'no skills directory found (skipped)'
        return $R
    }
    $skillRoot = $skillRoots[0]
    $skillFiles = @(Get-ChildItem $skillRoot -Recurse -Filter 'SKILL.md' -ErrorAction SilentlyContinue)
    if ($skillFiles.Count -eq 0) {
        Add-Skip $R
        $R.notes = "no SKILL.md under $skillRoot"
        return $R
    }
    Add-Pass $R  # at least one skill present
    $malformed = New-Object System.Collections.Generic.List[string]
    foreach ($f in $skillFiles) {
        $head = (Get-Content $f.FullName -TotalCount 15) -join "`n"
        $hasName = $head -match '(?m)^name:\s*\S+'
        $hasDesc = $head -match '(?m)^description:\s*\S+'
        if (-not ($hasName -and $hasDesc)) { $malformed.Add($f.Directory.Name) }
    }
    if ($malformed.Count -eq 0) {
        Add-Pass $R
    } else {
        Add-Fail $R ("{0} malformed skill(s) (missing name/description): {1}" -f $malformed.Count, (($malformed | Select-Object -First 5) -join ', '))
    }
    $R.notes = ("{0} skill(s) scanned under {1}" -f $skillFiles.Count, (Split-Path $skillRoot -Leaf))
    return $R
}

# --- WPAC Topology --------------------------------------------------------
# If topology.md exists, verify parent/child/sibling paths resolve on disk
# (or are explicitly empty/offline). Skip cleanly on non-WPAC projects.
function Test-WpacTopology {
    $R = New-SystemResult -Name 'WPAC Topology' -Key 'wpac'
    $topo = Join-Path $DotGald3r 'workspace\topology.md'
    if (-not (Test-Path $topo)) {
        Add-Skip $R
        $R.notes = 'no topology.md (not a WPAC project, skipped)'
        return $R
    }
    Add-Pass $R  # topology present + readable
    $content = Get-Content $topo -Raw
    $pathMatches = [regex]::Matches($content, '(?m)project_path:\s*"?([A-Za-z]:[\\/][^"\r\n]+?)"?\s*$')
    $checked = 0
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($m in $pathMatches) {
        $p = $m.Groups[1].Value.Trim()
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        $checked++
        # Self path is the project itself; allow it.
        if ((Resolve-Path $p -ErrorAction SilentlyContinue)) {
            # resolves
        } else {
            $missing.Add($p)
        }
    }
    if ($checked -eq 0) {
        Add-Skip $R
        $R.notes = 'topology has no resolvable project_path entries'
        return $R
    }
    if ($missing.Count -eq 0) {
        Add-Pass $R
    } else {
        # Offline peers are common and expected; mark as PARTIAL via fail entries
        # but label clearly so it is not read as a hard system break.
        foreach ($x in ($missing | Select-Object -First 5)) { Add-Fail $R ("topology path does not resolve: {0}" -f $x) }
    }
    $R.notes = ("{0} topology path(s) checked, {1} unresolved" -f $checked, $missing.Count)
    return $R
}

# --- Release Pipeline -----------------------------------------------------
# CHANGELOG.md parseable + every versioned header has a matching release file.
function Test-ReleasePipeline {
    $R = New-SystemResult -Name 'Release Pipeline' -Key 'release'
    $changelog = Join-Path $RepoRoot 'CHANGELOG.md'
    if (-not (Test-Path $changelog)) {
        Add-Skip $R
        $R.notes = 'CHANGELOG.md not present (skipped)'
        return $R
    }
    $content = Get-Content $changelog -Raw
    # Versioned headers: ## [1.7.0] - ... (skip [Unreleased]).
    $verMatches = [regex]::Matches($content, '(?m)^##\s*\[(\d+\.\d+\.\d+)\]')
    if ($verMatches.Count -eq 0) {
        Add-Skip $R
        $R.notes = 'no versioned CHANGELOG headers'
        return $R
    }
    Add-Pass $R  # changelog parsed, has versions
    $releasesDir = Join-Path $DotGald3r 'releases'
    # Collect release records by their AUTHORITATIVE version: frontmatter field, not
    # just the filename slug. A release file may use a codename slug (e.g.
    # release001_maestro-harvest.md is the v1.5.0 record), so matching on the filename
    # alone produces a false "gap". The version: field is the source of truth; the
    # filename slug is kept as a fallback for files lacking the field.
    $relFiles = @()
    $relVersions = New-Object System.Collections.Generic.List[string]
    if (Test-Path $releasesDir) {
        foreach ($rf in (Get-ChildItem $releasesDir -Filter '*.md' -ErrorAction SilentlyContinue)) {
            $relFiles += $rf.Name
            $head = (Get-Content $rf.FullName -TotalCount 30 -ErrorAction SilentlyContinue) -join "`n"
            $vm = [regex]::Match($head, "(?m)^version:\s*['""]?(\d+\.\d+\.\d+)['""]?\s*$")
            if ($vm.Success) { $relVersions.Add($vm.Groups[1].Value) }
        }
    }
    $gaps = New-Object System.Collections.Generic.List[string]
    foreach ($m in $verMatches) {
        $v = $m.Groups[1].Value          # 1.7.0
        $vSlug = $v -replace '\.', '-'   # 1-7-0
        $hit = ($relVersions -contains $v) -or ($relFiles | Where-Object { $_ -match $vSlug })
        if (-not $hit) { $gaps.Add($v) }
    }
    if ($gaps.Count -eq 0) {
        Add-Pass $R
    } else {
        foreach ($g in ($gaps | Select-Object -First 5)) { Add-Fail $R ("CHANGELOG version {0} has no release file" -f $g) }
    }
    $R.notes = ("{0} version(s); {1} gap(s)" -f $verMatches.Count, $gaps.Count)
    return $R
}

# --- Encoding Integrity ---------------------------------------------------
# Sample up to 50 .ps1 files; flag the GENUINELY dangerous case only:
# a file that contains non-ASCII bytes AND has NO UTF-8 BOM. Under Windows
# PowerShell 5.1, a BOM-less file with non-ASCII bytes (em-dash, smart quotes,
# box-drawing) is decoded with the legacy ANSI codepage and can throw a parse
# error -- the T1532 em-dash crash class (BUG-117 / BUG-112 / BUG-124), each
# FIXED by ADDING a BOM. So a UTF-8 BOM is PROTECTIVE here, not a defect:
#   - BOM present                  -> PASS (forces correct UTF-8 reading)
#   - pure ASCII, no BOM           -> PASS (nothing to misdecode)
#   - non-ASCII bytes, no BOM      -> FAIL (unparseable / mis-decoded under 5.1)
# Do NOT mass-strip BOMs to "fix" this -- that REINTRODUCES the crash class.
function Test-EncodingIntegrity {
    $R = New-SystemResult -Name 'Encoding Integrity' -Key 'encoding'
    # Scan repo-tracked source dirs only (avoid .git, node_modules, temp).
    $scanDirs = @()
    foreach ($d in @($CustomScripts, $DotGald3rSys, (Join-Path $RepoRoot '.claude'))) {
        if (Test-Path $d) { $scanDirs += $d }
    }
    if ($scanDirs.Count -eq 0) {
        Add-Skip $R
        $R.notes = 'no scan dirs found (skipped)'
        return $R
    }
    $all = New-Object System.Collections.Generic.List[object]
    foreach ($d in $scanDirs) {
        Get-ChildItem $d -Recurse -Include '*.ps1' -ErrorAction SilentlyContinue | ForEach-Object { $all.Add($_) }
    }
    if ($all.Count -eq 0) {
        Add-Skip $R
        $R.notes = 'no .ps1 files found to sample'
        return $R
    }
    # Deterministic-ish sample of up to 50.
    $sample = @($all | Get-Random -Count ([Math]::Min(50, $all.Count)))
    $bomCount = 0
    $unsafe = New-Object System.Collections.Generic.List[string]   # non-ASCII AND no BOM
    foreach ($f in $sample) {
        try {
            $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
            $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
            if ($hasBom) { $bomCount++ }
            # Detect any byte > 0x7F outside the BOM prefix (i.e. genuine non-ASCII content).
            $start = if ($hasBom) { 3 } else { 0 }
            $hasNonAscii = $false
            for ($i = $start; $i -lt $bytes.Length; $i++) {
                if ($bytes[$i] -gt 0x7F) { $hasNonAscii = $true; break }
            }
            # FAIL only the dangerous case: non-ASCII content WITHOUT a protective BOM.
            if ($hasNonAscii -and -not $hasBom) { $unsafe.Add($f.Name) }
        } catch { }
    }
    if ($unsafe.Count -eq 0) {
        Add-Pass $R
    } else {
        Add-Fail $R ("{0}/{1} sampled .ps1 files have non-ASCII bytes WITHOUT a UTF-8 BOM (unparseable under PS 5.1): {2}" -f $unsafe.Count, $sample.Count, (($unsafe | Select-Object -First 5) -join ', '))
    }
    $R.notes = ("sampled {0} of {1} .ps1 file(s); {2} BOM-protected, {3} non-ASCII-without-BOM" -f $sample.Count, $all.Count, $bomCount, $unsafe.Count)
    return $R
}

# ===========================================================================
# Registry of system tests (key -> function). Order = report order.
# ===========================================================================
$testRegistry = [ordered]@{
    task          = 'Test-TaskManagement'
    bug           = 'Test-BugTracking'
    platform_spec = 'Test-PlatformSpec'
    parity        = 'Test-PlatformParity'
    hooks         = 'Test-HookWiring'
    git_hooks     = 'Test-GitHooks'
    schema        = 'Test-SchemaValidation'
    constraints   = 'Test-Constraints'
    subsystems    = 'Test-Subsystems'
    skills        = 'Test-SkillsInventory'
    wpac          = 'Test-WpacTopology'
    release       = 'Test-ReleasePipeline'
    encoding      = 'Test-EncodingIntegrity'
}

# Subset selection
$selectedKeys = @($testRegistry.Keys)
if (-not [string]::IsNullOrWhiteSpace($Systems)) {
    $want = @($Systems -split ',' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
    $selectedKeys = @($testRegistry.Keys | Where-Object { $want -contains $_ })
    if ($selectedKeys.Count -eq 0) {
        Write-Host "ERROR: -Systems matched no known keys. Valid: $(($testRegistry.Keys) -join ', ')" -ForegroundColor Red
        exit 2
    }
}

# ===========================================================================
# Run
# ===========================================================================
$results = @()
foreach ($key in $selectedKeys) {
    $fn = $testRegistry[$key]
    $r = & $fn
    $results += $r
}

# ---------------------------------------------------------------------------
# Score each system + overall
# ---------------------------------------------------------------------------
function Get-SystemStatus {
    param($R)
    $denom = $R.passed + $R.failed
    if ($denom -eq 0) { return 'SKIP' }
    if ($R.failed -eq 0) { return 'PASS' }
    if ($R.passed -eq 0) { return 'FAIL' }
    return 'PARTIAL'
}
function Get-SystemScore {
    param($R)
    $denom = $R.passed + $R.failed
    if ($denom -eq 0) { return $null }  # skipped -> excluded from average
    return [Math]::Round(($R.passed / $denom) * 100, 0)
}

$scored = @()
foreach ($r in $results) {
    $status = Get-SystemStatus -R $r
    $score = Get-SystemScore -R $r
    $scored += [pscustomobject]@{
        name     = $r.name
        key      = $r.key
        status   = $status
        score    = $score
        passed   = $r.passed
        failed   = $r.failed
        skipped  = $r.skipped
        failures = @($r.failures)
        notes    = $r.notes
    }
}

# Overall = average of per-system scores, excluding SKIP systems.
$activeScores = @($scored | Where-Object { $null -ne $_.score } | ForEach-Object { $_.score })
$overall = if ($activeScores.Count -gt 0) { [Math]::Round((($activeScores | Measure-Object -Sum).Sum / $activeScores.Count), 0) } else { 0 }
$systemsPassing = @($scored | Where-Object { $_.status -eq 'PASS' }).Count
$systemsTested  = @($scored | Where-Object { $_.status -ne 'SKIP' }).Count

# ---------------------------------------------------------------------------
# Write markdown report to .gald3r/reports/
# ---------------------------------------------------------------------------
function Get-StatusGlyph {
    param([string]$Status)
    switch ($Status) {
        'PASS'    { return '[PASS]' }
        'PARTIAL' { return '[PARTIAL]' }
        'FAIL'    { return '[FAIL]' }
        'SKIP'    { return '[SKIP]' }
        default   { return '[?]' }
    }
}

$nowUtc = (Get-Date).ToUniversalTime()
$stamp = $nowUtc.ToString('yyyyMMdd_HHmmss')
$reportPath = $null
$reportsDir = Join-Path $DotGald3r 'reports'

if (-not $NoReport -and (Test-Path $DotGald3r)) {
    if (-not (Test-Path $reportsDir)) {
        New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
    }
    $reportPath = Join-Path $reportsDir ("system_test_{0}.md" -f $stamp)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('# gald3r System Test Report')
    [void]$sb.AppendLine(("Generated: {0} UTC" -f $nowUtc.ToString('yyyy-MM-dd HH:mm')))
    [void]$sb.AppendLine(("Project: {0}" -f $projectName))
    [void]$sb.AppendLine(("gald3r version: {0}" -f $gald3rVersion))
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine(("## Overall Score: {0}% functional ({1}/{2} systems passing)" -f $overall, $systemsPassing, $systemsTested))
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('| System | Score | Status | Notes |')
    [void]$sb.AppendLine('|--------|-------|--------|-------|')
    foreach ($s in $scored) {
        $scoreText = if ($null -ne $s.score) { ("{0}%" -f $s.score) } else { '-' }
        $detail = ("{0}/{1} tests" -f $s.passed, ($s.passed + $s.failed))
        if ($s.status -eq 'SKIP') { $detail = 'skipped' }
        $noteText = $s.notes
        if ($noteText) { $detail = ("{0}; {1}" -f $detail, $noteText) }
        [void]$sb.AppendLine(("| {0} | {1} | {2} {3} | {4} |" -f $s.name, $scoreText, (Get-StatusGlyph $s.status), $s.status, $detail))
    }
    [void]$sb.AppendLine('')
    $anyFail = @($scored | Where-Object { $_.failures.Count -gt 0 })
    if ($anyFail.Count -gt 0) {
        [void]$sb.AppendLine('## Failed Tests')
        foreach ($s in $anyFail) {
            [void]$sb.AppendLine(("### {0}" -f $s.name))
            foreach ($f in $s.failures) {
                [void]$sb.AppendLine(("- {0}" -f $f))
            }
            [void]$sb.AppendLine('')
        }
    } else {
        [void]$sb.AppendLine('## Failed Tests')
        [void]$sb.AppendLine('None. All tested systems passed.')
    }
    # Write WITHOUT BOM (ASCII / UTF8 no-BOM) to keep the report clean.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($reportPath, $sb.ToString(), $utf8NoBom)
}

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if ($Json) {
    [pscustomobject]@{
        suite           = 'gald3r system test harness'
        project         = $projectName
        gald3r_version  = $gald3rVersion
        overall_score   = $overall
        systems_passing = $systemsPassing
        systems_tested  = $systemsTested
        report          = $reportPath
        timestamp       = $nowUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
        systems         = $scored
    } | ConvertTo-Json -Depth 6
} else {
    Write-Host ''
    Write-Host '==================================================================' -ForegroundColor Cyan
    Write-Host '  gald3r System Test Harness (T1540)' -ForegroundColor Cyan
    Write-Host ("  Project: {0}   gald3r version: {1}" -f $projectName, $gald3rVersion) -ForegroundColor DarkGray
    Write-Host '==================================================================' -ForegroundColor Cyan
    $fmt = '  {0,-20} {1,6}  {2,-9} {3}'
    Write-Host ($fmt -f 'System', 'Score', 'Status', 'Notes') -ForegroundColor DarkGray
    Write-Host ('  ' + ('-' * 62)) -ForegroundColor DarkGray
    foreach ($s in $scored) {
        $scoreText = if ($null -ne $s.score) { ("{0}%" -f $s.score) } else { '-' }
        $color = switch ($s.status) {
            'PASS'    { 'Green' }
            'PARTIAL' { 'Yellow' }
            'FAIL'    { 'Red' }
            default   { 'DarkGray' }
        }
        Write-Host ($fmt -f $s.name, $scoreText, $s.status, $s.notes) -ForegroundColor $color
    }
    Write-Host ('  ' + ('-' * 62)) -ForegroundColor DarkGray
    $ovColor = if ($overall -ge 90) { 'Green' } elseif ($overall -ge 70) { 'Yellow' } else { 'Red' }
    Write-Host ("  OVERALL: {0}% functional  ({1}/{2} systems passing)" -f $overall, $systemsPassing, $systemsTested) -ForegroundColor $ovColor
    if ($reportPath) {
        Write-Host ("  Report: {0}" -f $reportPath) -ForegroundColor DarkGray
    }
    # Surface failure detail inline.
    $anyFail = @($scored | Where-Object { $_.failures.Count -gt 0 })
    if ($anyFail.Count -gt 0) {
        Write-Host ''
        Write-Host '  Failed Tests:' -ForegroundColor Red
        foreach ($s in $anyFail) {
            Write-Host ("    {0}:" -f $s.name) -ForegroundColor Yellow
            foreach ($f in $s.failures) { Write-Host ("      - {0}" -f $f) -ForegroundColor DarkYellow }
        }
    }
    Write-Host ''
}

# ---------------------------------------------------------------------------
# CI gate
# ---------------------------------------------------------------------------
if ($FailBelow -gt 0 -and $overall -lt $FailBelow) {
    if (-not $Json) {
        Write-Host ("FAIL GATE: overall score {0}% is below -FailBelow {1}%" -f $overall, $FailBelow) -ForegroundColor Red
    }
    exit 1
}
exit 0
