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
            Runner = 'python'
            Path   = '.gald3r_sys/skills/g-skl-test/scripts/tests/test_g_go_workspace_mode_fixtures.py'
            Desc   = 'g-go --workspace policy/contract fixtures (D015-parity, discovered IDE roots)'
        },
        @{
            Name   = 'g_go_go_autopilot_fixtures'
            Level  = 'L1'
            Runner = 'python'
            Path   = '.gald3r_sys/skills/g-skl-test/scripts/tests/test_g_go_go_autopilot_fixtures.py'
            Desc   = 'g-go-go autopilot policy/contract fixtures (D015-parity, discovered IDE roots)'
        }
        # RETIRED (BUG-192, 2026-07-12): 'workspace_template_export' entry removed.
        # test_workspace_template_export.py (and its manifest entry) imported a
        # workspace_template_export helper module (paths_overlap, IS_CASE_INSENSITIVE_FS)
        # that never existed anywhere in this tree -- ImportError at collection time,
        # independent of and pre-existing before the BUG-130 manifest-path fix. The
        # test's own docstring confirms the helper belongs to a DIFFERENT repo's layout
        # (gald3r_dev/gald3r_templates 'custom_scripts/_delete_when_sure/'), not this
        # neutral_source 'skills/g-skl-test/scripts/tests/' tree -- same genuinely-dead
        # class as the two retirements below, not a relocate/misname case. Test file
        # deleted; re-add a real manifest entry only if paths_overlap/IS_CASE_INSENSITIVE_FS
        # and their BUG-030 test coverage are ever actually ported into this tree.
        #
        # RETIRED (T435, 2026-06-16): 'queue_compute_functions' entry removed.
        # The functions under test (Resolve-WorkspaceQueue, Get-RunnableTaskQueue)
        # were extracted from the unrecoverable legacy g_go_go_queue_compute.ps1 temp
        # script (T1553) into queue_compute.ps1 modules that were NEVER restored to the
        # shipped tree -- no .gald3r_sys/skills/g-skl-{workspace,tasks}/scripts/queue_compute.ps1
        # exists anywhere in the canonical template. The test dot-sources those absent
        # modules and dies at load with "Resolve-WorkspaceQueue is not recognized" (exit 1).
        # Genuinely dead source -> retire rather than port a test for code that does not exist
        # (T1582 audit dead-code flag was right in OUTCOME, wrong in REASON: it was a live
        # manifest entry, but for a non-existent function). See task435_*.md for full rationale.
        #
        # RETIRED (BUG-130, 2026-07-12): 'gald3r_housekeeping_commit' entry removed.
        # Path pointed at gald3r_template/.gald3r_sys/skills/g-skl-git-commit/scripts/tests/
        # test_gald3r_housekeeping_commit.py -- stale, carried over unchanged from the frozen
        # donor manifest. Neither that test file NOR the script it was meant to exercise
        # (gald3r_housekeeping_commit.ps1, documented only in rules/g-rl-33-enforcement_catchall.md
        # under .gald3r_sys/skills/g-skl-git-commit/scripts/) exist anywhere in this tree --
        # genuinely never restored, not just relocated/misnamed like the two L1 fixtures above.
        # Re-add a real manifest entry (Runner 'python' or 'pwsh' to match whatever ships) if
        # gald3r_housekeeping_commit.ps1 and its test are ever actually ported in.
    )
}
