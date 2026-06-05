@{
    # gald3r_templates framework test-plan manifest (T1532).
    #
    # Single source of truth for which restored tests belong to which verification
    # level (L1 = fast / daily, L2 = integration, L3 = release). run_l1_tests.ps1
    # reads this file, filters by -Level, and dispatches each test by Runner.
    #
    # Paths are repo-root-relative (forward slashes). Runner is 'pwsh' or 'python'.
    #
    # Levels:
    #   L1 - fast, runs on every verify-gate / daily. Must be hermetic + quick.
    #   L2 - integration; may spin up disposable git repos in TEMP.
    #   L3 - release-time; broader / slower checks.
    Tests = @(
        @{
            Name   = 'g_go_workspace_mode_fixtures'
            Level  = 'L1'
            Runner = 'pwsh'
            Path   = 'custom_scripts/tests/test_g_go_workspace_mode_fixtures.ps1'
            Desc   = 'g-go --workspace policy/contract fixtures (D015-parity, discovered IDE roots)'
        },
        @{
            Name   = 'g_go_go_autopilot_fixtures'
            Level  = 'L1'
            Runner = 'pwsh'
            Path   = 'custom_scripts/tests/test_g_go_go_autopilot_fixtures.ps1'
            Desc   = 'g-go-go autopilot policy/contract fixtures (D015-parity, discovered IDE roots)'
        },
        @{
            Name   = 'workspace_template_export'
            Level  = 'L1'
            Runner = 'python'
            Path   = 'custom_scripts/tests/test_workspace_template_export.py'
            Desc   = 'paths_overlap / case-sensitivity regression (BUG-030); also runs at L3 release'
            AlsoLevels = @('L3')
        },
        @{
            Name   = 'queue_compute_functions'
            Level  = 'L1'
            Runner = 'pwsh'
            Path   = 'custom_scripts/tests/test_queue_compute_functions.ps1'
            Desc   = 'Resolve-WorkspaceQueue + Get-RunnableTaskQueue extracted queue-compute units (T1553, T1532 AC4)'
        },
        @{
            Name   = 'gald3r_housekeeping_commit'
            Level  = 'L2'
            Runner = 'pwsh'
            Path   = 'gald3r_template/.gald3r_sys/skills/g-skl-git-commit/scripts/tests/test_gald3r_housekeeping_commit.ps1'
            Desc   = 'gald3r_housekeeping_commit.ps1 integration smoke (disposable git repos in TEMP)'
        }
    )
}
