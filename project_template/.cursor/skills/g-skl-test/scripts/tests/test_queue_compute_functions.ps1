<#
.SYNOPSIS
    Unit tests for the extracted autopilot queue-compute functions (T1553).

.DESCRIPTION
    Exercises the two pure functions extracted from the (unrecoverable) legacy
    g_go_go_queue_compute.ps1 temp script, per T1532 AC4 / T1553:

      - Resolve-WorkspaceQueue  (.gald3r_sys/skills/g-skl-workspace/scripts/queue_compute.ps1)
      - Get-RunnableTaskQueue   (.gald3r_sys/skills/g-skl-tasks/scripts/queue_compute.ps1)

    Both functions are pure (no filesystem dependency for their core logic), so the
    tests feed them representative in-memory manifest/task records and assert the
    exact runnable set + ordering. The workspace-queue cases mirror what fixtures
    F4 (member resolves with existing path) and F8 (controlled members are the
    runnable/deferred source) in test_g_go_workspace_mode_fixtures.ps1 exercise.

    ASCII-only source (BUG-073 discipline). Runs green under pwsh 7 and
    powershell.exe 5.1. Exit 0 == all assertions passed, non-zero == failure.

.PARAMETER Json
    Emit a machine-readable JSON summary instead of human-readable lines.

.EXAMPLE
    pwsh -NoProfile -File custom_scripts/tests/test_queue_compute_functions.ps1
#>

[CmdletBinding()]
param(
    [switch]$Json
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$wsScript = Join-Path $RepoRoot '.gald3r_sys\skills\g-skl-workspace\scripts\queue_compute.ps1'
$taskScript = Join-Path $RepoRoot '.gald3r_sys\skills\g-skl-tasks\scripts\queue_compute.ps1'

$results = @()
function Add-Check {
    param([string]$Name, [bool]$Pass, [string]$Detail)
    $script:results += [PSCustomObject]@{ name = $Name; pass = $Pass; detail = $Detail }
}

# --- Load the functions under test (dot-source, must define + not run anything) ---
if (-not (Test-Path $wsScript)) {
    Add-Check 'workspace queue_compute.ps1 present' $false "missing: $wsScript"
} else {
    . $wsScript
    Add-Check 'workspace queue_compute.ps1 present' $true $wsScript
}
if (-not (Test-Path $taskScript)) {
    Add-Check 'tasks queue_compute.ps1 present' $false "missing: $taskScript"
} else {
    . $taskScript
    Add-Check 'tasks queue_compute.ps1 present' $true $taskScript
}

Add-Check 'Resolve-WorkspaceQueue defined' ([bool](Get-Command Resolve-WorkspaceQueue -ErrorAction SilentlyContinue)) ''
Add-Check 'Get-RunnableTaskQueue defined'  ([bool](Get-Command Get-RunnableTaskQueue  -ErrorAction SilentlyContinue)) ''

# ----------------------------------------------------------------------------
# Resolve-WorkspaceQueue
# ----------------------------------------------------------------------------
# Representative manifest slice modeled on the real workspace_manifest.yaml:
#   - owner control_project (gald3r_dev)            -> excluded (owner + role)
#   - public_distribution_repo (gald3r)             -> excluded (role)
#   - two controlled_member with existing paths      -> RUNNABLE
#   - one controlled_member with a missing path      -> dropped under -RequireExistingPath
#   - one deregistered controlled_member (gald3r_forge) -> excluded (lifecycle)
#   - one reference_archive (maestro2)               -> excluded (lifecycle + role)
#   - one autonomous_child                           -> RUNNABLE
$existA = $RepoRoot                      # a path guaranteed to exist
$existB = $PSScriptRoot                  # another guaranteed-existing path
$missing = Join-Path $RepoRoot '__nonexistent_member_path_t1553__'

$repos = @(
    @{ id = 'gald3r_dev';        local_path = $existA;  workspace_role = 'control_project';          lifecycle_status = 'active' },
    @{ id = 'gald3r';            local_path = $existA;  workspace_role = 'public_distribution_repo'; lifecycle_status = 'active' },
    @{ id = 'gald3r_throne';     local_path = $existA;  workspace_role = 'controlled_member';        lifecycle_status = 'adopted' },
    @{ id = 'gald3r_valhalla';   local_path = $existB;  workspace_role = 'controlled_member';        lifecycle_status = 'adopted' },
    @{ id = 'gald3r_pathless';   local_path = $missing; workspace_role = 'controlled_member';        lifecycle_status = 'active_member' },
    @{ id = 'gald3r_forge';      local_path = $existA;  workspace_role = 'controlled_member';        lifecycle_status = 'deregistered'; deregistered_at = '2026-05-04' },
    @{ id = 'maestro2';          local_path = $existA;  workspace_role = 'reference_archive';        lifecycle_status = 'reference_archive' },
    @{ id = 'gald3r_child';      local_path = $existB;  workspace_role = 'autonomous_child';         lifecycle_status = 'active' }
)

# WQ1: default run -- excludes owner/public/deregistered/reference; keeps members+child.
# (path existence NOT required here, so gald3r_pathless survives.)
$wq1 = @(Resolve-WorkspaceQueue -Repositories $repos -OwnerId 'gald3r_dev')
$wq1Ids = @($wq1 | ForEach-Object { $_.id })
$wq1Expected = @('gald3r_child', 'gald3r_pathless', 'gald3r_throne', 'gald3r_valhalla')  # sorted by id
$wq1Pass = (($wq1Ids -join ',') -eq ($wq1Expected -join ','))
Add-Check 'WQ1 default filter (role+owner+lifecycle, sorted)' $wq1Pass "got [$($wq1Ids -join ',')] want [$($wq1Expected -join ',')]"

# WQ2 (F4): -RequireExistingPath drops the missing-path member -> >= 1 resolves.
$wq2 = @(Resolve-WorkspaceQueue -Repositories $repos -OwnerId 'gald3r_dev' -RequireExistingPath)
$wq2Ids = @($wq2 | ForEach-Object { $_.id })
$wq2Expected = @('gald3r_child', 'gald3r_throne', 'gald3r_valhalla')
$wq2Pass = ((($wq2Ids -join ',') -eq ($wq2Expected -join ',')) -and ($wq2.Count -ge 1))
Add-Check 'WQ2 (F4) RequireExistingPath drops missing-path member' $wq2Pass "got [$($wq2Ids -join ',')] want [$($wq2Expected -join ',')]"

# WQ3 (F8): controlled_member is the deferred/runnable source -- restrict role to it.
$wq3 = @(Resolve-WorkspaceQueue -Repositories $repos -OwnerId 'gald3r_dev' -RunnableRoles @('controlled_member') -RequireExistingPath)
$wq3Ids = @($wq3 | ForEach-Object { $_.id })
$wq3Expected = @('gald3r_throne', 'gald3r_valhalla')   # child excluded (not controlled_member), forge excluded (deregistered)
$wq3Pass = (($wq3Ids -join ',') -eq ($wq3Expected -join ','))
Add-Check 'WQ3 (F8) controlled_member-only role filter' $wq3Pass "got [$($wq3Ids -join ',')] want [$($wq3Expected -join ',')]"

# WQ4: -Filter (workspace_repos routing) narrows to a named subset.
$wq4 = @(Resolve-WorkspaceQueue -Repositories $repos -OwnerId 'gald3r_dev' -Filter @('gald3r_valhalla', 'gald3r_dev'))
$wq4Ids = @($wq4 | ForEach-Object { $_.id })
$wq4Pass = (($wq4Ids -join ',') -eq 'gald3r_valhalla')   # gald3r_dev filtered out as owner
Add-Check 'WQ4 Filter (workspace_repos) + owner exclusion' $wq4Pass "got [$($wq4Ids -join ',')] want [gald3r_valhalla]"

# WQ5: empty input -> empty array (no throw under StrictMode).
$wq5 = @(Resolve-WorkspaceQueue -Repositories @() -OwnerId 'gald3r_dev')
Add-Check 'WQ5 empty manifest -> empty queue' ($wq5.Count -eq 0) "count=$($wq5.Count)"

# ----------------------------------------------------------------------------
# Get-RunnableTaskQueue
# ----------------------------------------------------------------------------
# Representative task slice:
#   T100 done          -> excluded (status)
#   T200 pending low                          repos: [gald3r_templates]
#   T150 pending critical                     repos: [gald3r_templates]
#   T300 pending high                         repos: [] (current repo)
#   T400 pending high  repos: [gald3r_other]  -> excluded (not in runnable set)
#   T250 pending medium policy=source_only
#   T260 pending medium policy=docs_only      -> excluded when touch-policy gate set
#   T050 open    critical                     -> 'open' counts as pending
$tasks = @(
    @{ id = 'T100'; status = 'done';    priority = 'critical'; workspace_repos = @('gald3r_templates') },
    @{ id = 'T200'; status = 'pending'; priority = 'low';      workspace_repos = @('gald3r_templates') },
    @{ id = 'T150'; status = 'pending'; priority = 'critical'; workspace_repos = @('gald3r_templates') },
    @{ id = 'T300'; status = 'pending'; priority = 'high';     workspace_repos = @() },
    @{ id = 'T400'; status = 'pending'; priority = 'high';     workspace_repos = @('gald3r_other') },
    @{ id = 'T250'; status = 'pending'; priority = 'medium';   workspace_repos = @('gald3r_templates'); workspace_touch_policy = 'source_only' },
    @{ id = 'T260'; status = 'pending'; priority = 'medium';   workspace_repos = @('gald3r_templates'); workspace_touch_policy = 'docs_only' },
    @{ id = 'T050'; status = 'open';    priority = 'critical';  workspace_repos = @('gald3r_templates') }
)
$runnableRepos = @('gald3r_templates')

# TQ1: full order -- critical-first then lowest-id; T400 dropped (routing), T100 dropped (done).
$tq1 = @(Get-RunnableTaskQueue -Tasks $tasks -RunnableRepoIds $runnableRepos)
$tq1Ids = @($tq1 | ForEach-Object { $_.id })
# critical: T050, T150 ; high: T300 ; medium: T250, T260 ; low: T200
$tq1Expected = @(50, 150, 300, 250, 260, 200)
$tq1Pass = (($tq1Ids -join ',') -eq ($tq1Expected -join ','))
Add-Check 'TQ1 critical-first then lowest-id ordering + routing gate' $tq1Pass "got [$($tq1Ids -join ',')] want [$($tq1Expected -join ',')]"

# TQ2: run-budget caps the result (top 3 by order).
$tq2 = @(Get-RunnableTaskQueue -Tasks $tasks -RunnableRepoIds $runnableRepos -Budget 3)
$tq2Ids = @($tq2 | ForEach-Object { $_.id })
$tq2Pass = (($tq2Ids -join ',') -eq '50,150,300')
Add-Check 'TQ2 run budget caps to top-N in order' $tq2Pass "got [$($tq2Ids -join ',')] want [50,150,300]"

# TQ3: workspace_touch_policy gate drops docs_only when only source_only allowed.
$tq3 = @(Get-RunnableTaskQueue -Tasks $tasks -RunnableRepoIds $runnableRepos -AllowedTouchPolicies @('source_only'))
$tq3Ids = @($tq3 | ForEach-Object { $_.id })
# T260 (docs_only) dropped; T300 (no policy) still passes the policy gate.
$tq3Expected = @(50, 150, 300, 250, 200)
$tq3Pass = (($tq3Ids -join ',') -eq ($tq3Expected -join ','))
Add-Check 'TQ3 touch-policy gate drops disallowed policy, keeps policyless' $tq3Pass "got [$($tq3Ids -join ',')] want [$($tq3Expected -join ',')]"

# TQ4: omitted workspace_repos == current repo only -> still runnable with empty RunnableRepoIds.
$tq4 = @(Get-RunnableTaskQueue -Tasks @(@{ id = 'T900'; status = 'pending'; priority = 'high'; workspace_repos = @() }) -RunnableRepoIds @())
Add-Check 'TQ4 empty workspace_repos == current repo (runnable)' (($tq4.Count -eq 1) -and ($tq4[0].id -eq 900)) "count=$($tq4.Count)"

# TQ5: scalar/comma workspace_repos string is normalized like an array.
$tq5 = @(Get-RunnableTaskQueue -Tasks @(@{ id = 'T901'; status = 'pending'; priority = 'low'; workspace_repos = 'gald3r_templates, gald3r_other' }) -RunnableRepoIds @('gald3r_templates'))
Add-Check 'TQ5 comma-string workspace_repos normalized' (($tq5.Count -eq 1) -and ($tq5[0].id -eq 901)) "count=$($tq5.Count)"

# TQ6: empty task list -> empty queue (no throw).
$tq6 = @(Get-RunnableTaskQueue -Tasks @() -RunnableRepoIds $runnableRepos)
Add-Check 'TQ6 empty task list -> empty queue' ($tq6.Count -eq 0) "count=$($tq6.Count)"

# ----------------------------------------------------------------------------
# Integration: workspace queue feeds the task routing gate.
# ----------------------------------------------------------------------------
$wsRunnable = @(Resolve-WorkspaceQueue -Repositories $repos -OwnerId 'gald3r_dev' -RunnableRoles @('controlled_member') -RequireExistingPath)
$wsRunnableIds = @($wsRunnable | ForEach-Object { $_.id })
$memberTasks = @(
    @{ id = 'T700'; status = 'pending'; priority = 'high';     workspace_repos = @('gald3r_throne') },
    @{ id = 'T710'; status = 'pending'; priority = 'critical'; workspace_repos = @('gald3r_valhalla') },
    @{ id = 'T720'; status = 'pending'; priority = 'high';     workspace_repos = @('gald3r_forge') }   # deregistered -> not runnable
)
$intQueue = @(Get-RunnableTaskQueue -Tasks $memberTasks -RunnableRepoIds $wsRunnableIds)
$intIds = @($intQueue | ForEach-Object { $_.id })
$intPass = (($intIds -join ',') -eq '710,700')   # critical first, forge task gated out
Add-Check 'INT workspace queue gates member task routing' $intPass "runnable=[$($wsRunnableIds -join ',')] queue=[$($intIds -join ',')] want [710,700]"

# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------
$total = $results.Count
$passed = @($results | Where-Object { $_.pass }).Count
$failed = $total - $passed

if ($Json) {
    [PSCustomObject]@{
        suite     = 'T1553 queue-compute function unit tests'
        repo_root = $RepoRoot
        total     = $total
        passed    = $passed
        failed    = $failed
        results   = $results
        timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    } | ConvertTo-Json -Depth 5
} else {
    Write-Host ''
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host '  queue-compute function unit tests (T1553) ' -ForegroundColor Cyan
    Write-Host '============================================' -ForegroundColor Cyan
    foreach ($r in $results) {
        $icon = if ($r.pass) { 'PASS' } else { 'FAIL' }
        $color = if ($r.pass) { 'Green' } else { 'Red' }
        Write-Host ("  [{0}] {1}" -f $icon, $r.name) -ForegroundColor $color
        if ($r.detail -and -not $r.pass) { Write-Host ("        {0}" -f $r.detail) -ForegroundColor DarkGray }
    }
    Write-Host ''
    $summaryColor = if ($failed -eq 0) { 'Green' } else { 'Red' }
    Write-Host ("Summary: {0}/{1} checks passed, {2} failed" -f $passed, $total, $failed) -ForegroundColor $summaryColor
    Write-Host ''
}

if ($failed -eq 0) { exit 0 } else { exit 1 }
